"""Semantic retrieval over UDA-Hub knowledge articles."""

from __future__ import annotations

import math
from pathlib import Path
from threading import Lock
from typing import Any, Protocol

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from data.models import udahub
from agentic.tools.database import DEFAULT_CORE_DB


class KnowledgeRetriever(Protocol):
    def search(self, account_id: str, query: str, limit: int = 3) -> list[dict[str, Any]]: ...


class SemanticKnowledgeBase:
    """Lazily index knowledge articles once and perform account-scoped search."""

    def __init__(
        self,
        db_path: str | Path = DEFAULT_CORE_DB,
        embeddings: Embeddings | None = None,
    ) -> None:
        self.db_path = Path(db_path)
        if not self.db_path.is_file():
            raise FileNotFoundError(f"Database does not exist: {self.db_path}")
        self.embeddings = embeddings or OpenAIEmbeddings(model="text-embedding-3-small")
        self._index: list[tuple[Document, list[float]]] | None = None
        self._lock = Lock()

    def _build_index(self) -> list[tuple[Document, list[float]]]:
        if self._index is not None:
            return self._index
        with self._lock:
            if self._index is not None:
                return self._index

            engine = create_engine(f"sqlite:///{self.db_path}", echo=False)
            sessions = sessionmaker(
                bind=engine,
                expire_on_commit=False,
            )
            try:
                with sessions() as session:
                    articles = list(session.scalars(select(udahub.Knowledge)))
            finally:
                engine.dispose()
            if not articles:
                raise LookupError("The UDA-Hub knowledge base is empty")

            documents = [
                Document(
                    id=article.article_id,
                    page_content=f"{article.title}\n\n{article.content}",
                    metadata={
                        "article_id": article.article_id,
                        "account_id": article.account_id,
                        "title": article.title,
                        "tags": article.tags,
                    },
                )
                for article in articles
            ]
            vectors = self.embeddings.embed_documents(
                [document.page_content for document in documents]
            )
            self._index = list(zip(documents, vectors, strict=True))
            return self._index

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        if len(left) != len(right):
            raise ValueError("Embedding dimensions do not match")
        denominator = math.sqrt(sum(value * value for value in left)) * math.sqrt(
            sum(value * value for value in right)
        )
        if denominator == 0:
            return 0.0
        return sum(a * b for a, b in zip(left, right, strict=True)) / denominator

    def search(
        self,
        account_id: str,
        query: str,
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        if not query.strip():
            raise ValueError("Knowledge search query cannot be empty")
        if not 1 <= limit <= 5:
            raise ValueError("Knowledge search limit must be between 1 and 5")

        query_vector = self.embeddings.embed_query(query)
        results = [
            (document, self._cosine_similarity(query_vector, vector))
            for document, vector in self._build_index()
            if document.metadata.get("account_id") == account_id
        ]
        results.sort(key=lambda item: item[1], reverse=True)
        return [
            {
                **document.metadata,
                "content": document.page_content,
                "score": round(score, 4),
            }
            for document, score in results[:limit]
        ]
