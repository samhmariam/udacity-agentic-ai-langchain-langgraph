# ADR-002: Hybrid Retrieval Architecture

## Status
Proposed

## Context
Current retrieval is in-memory and deterministic in [module-01-langchain-fundamentals/doc_assistant_project/src/retrieval.py](../../src/retrieval.py). Production settings need better recall and semantic matching.

## Decision
Adopt hybrid retrieval: lexical filtering plus vector retrieval plus metadata constraints, followed by reranking and citation span extraction.

## Consequences
- Pros: improved grounding and recall.
- Cons: additional infra and indexing complexity.

## Alternatives Considered
- Keep keyword-only retrieval.
- Pure vector retrieval without lexical constraints.

## How to Revisit This Decision
Reevaluate after retrieval benchmark data and latency budgets are collected.
