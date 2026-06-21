# DATA MODEL

## Goal
Define reusable data contracts for document assistants in high-risk domains.

## 1) Uploaded Document
### Pydantic Sketch
```python
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class UploadedDocument(BaseModel):
    document_id: str
    source_uri: Optional[str]
    filename: str
    mime_type: str
    uploaded_at: datetime
    uploaded_by: str
    checksum_sha256: str
    metadata: Dict[str, Any] = {}
```

### JSON Example
```json
{
  "document_id": "INV-2026-001",
  "source_uri": "s3://bucket/invoices/inv-2026-001.pdf",
  "filename": "inv-2026-001.pdf",
  "mime_type": "application/pdf",
  "uploaded_at": "2026-06-20T10:15:00Z",
  "uploaded_by": "user_123",
  "checksum_sha256": "abc123...",
  "metadata": {
    "doc_type": "invoice",
    "region": "US"
  }
}
```

## 2) Document Metadata
- document_id
- doc_type
- title
- entity_names
- dates
- currency
- amount_fields
- contains_phi
- sensitivity_level

Current metadata usage baseline:
- [module-01-langchain-fundamentals/doc_assistant_project/src/retrieval.py](../src/retrieval.py)

## 3) Chunk
Current baseline model exists as DocumentChunk in [module-01-langchain-fundamentals/doc_assistant_project/src/schemas.py](../src/schemas.py).

Recommended extension fields:
- chunk_id
- start_offset
- end_offset
- section_title
- token_count
- embedding_id

## 4) Source Citation
```python
class SourceCitation(BaseModel):
    citation_id: str
    document_id: str
    chunk_id: str
    quote: str
    start_offset: int
    end_offset: int
    relevance_score: float
```

## 5) User Query
```python
class UserQuery(BaseModel):
    request_id: str
    user_id: str
    session_id: str
    text: str
    created_at: datetime
    domain_hint: str | None = None
```

## 6) Conversation and Session
Current baseline model: SessionState in [module-01-langchain-fundamentals/doc_assistant_project/src/schemas.py](../src/schemas.py).

Recommended additions:
- policy_profile
- retention_class
- last_intent
- safety_events

## 7) Retrieval Result
```python
class RetrievalResult(BaseModel):
    query: str
    hits: list[SourceCitation]
    retrieval_mode: str
    total_hits: int
```

## 8) Calculation Result
Current baseline model: CalculationResponse in [module-01-langchain-fundamentals/doc_assistant_project/src/schemas.py](../src/schemas.py).

Recommended extension:
- operands with provenance
- precision and rounding metadata
- validation status

## 9) Generated Answer
Current baseline model: AnswerResponse in [module-01-langchain-fundamentals/doc_assistant_project/src/schemas.py](../src/schemas.py).

Recommended extension:
- citations list as structured objects
- safety_disclaimer
- verification_status

## 10) Evaluation Case
```python
class EvaluationCase(BaseModel):
    case_id: str
    input_query: str
    expected_intent: str
    expected_sources: list[str]
    expected_numeric_result: float | None = None
    rubric: dict
```

## 11) Audit Event
```python
class AuditEvent(BaseModel):
    event_id: str
    timestamp: datetime
    request_id: str
    session_id: str
    node_name: str
    action: str
    payload: dict
    model_version: str | None = None
```

## Data Lifecycle
1. Document ingestion and metadata extraction.
2. Chunking and indexing.
3. Query-time retrieval and task processing.
4. Response verification and citation binding.
5. Session and audit persistence.
6. Evaluation and monitoring feedback loops.

## Privacy Considerations
- Do not store raw PHI/PII in tool logs unless required and encrypted.
- Apply data minimization for conversation history.
- Define retention by sensitivity class.

Current logging baseline to harden:
- [module-01-langchain-fundamentals/doc_assistant_project/src/tools.py](../src/tools.py)
- [module-01-langchain-fundamentals/doc_assistant_project/src/assistant.py](../src/assistant.py)

## Retention Assumptions
- Session history retention should be configurable by policy.
- Audit logs retained longer than conversation text but redacted.

## Financial and Healthcare Risks in Data Model
- Ambiguous amount fields can produce wrong calculations.
- Missing provenance fields reduce auditability.
- Lack of sensitivity labels risks PHI leakage.
- No schema versioning can break backward compatibility in persisted sessions.
