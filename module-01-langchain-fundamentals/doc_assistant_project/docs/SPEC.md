# SPEC

## Document Status
- Status: Proposed
- Scope: Product and technical specification for a document assistant for financial and healthcare documents.
- Baseline implementation reviewed in:
  - [module-01-langchain-fundamentals/doc_assistant_project/src/assistant.py](../src/assistant.py)
  - [module-01-langchain-fundamentals/doc_assistant_project/src/agent.py](../src/agent.py)
  - [module-01-langchain-fundamentals/doc_assistant_project/src/retrieval.py](../src/retrieval.py)
  - [module-01-langchain-fundamentals/doc_assistant_project/src/tools.py](../src/tools.py)
  - [module-01-langchain-fundamentals/doc_assistant_project/src/prompts.py](../src/prompts.py)

## 1) Problem Statement
Organizations need a document assistant that can answer questions, summarize records, and perform reliable calculations across financial and healthcare documents while preserving traceability, privacy, and auditability.

## 2) Target Users
- MUST: Analysts handling invoices, claims, and contracts.
- MUST: Operations teams reviewing mixed domain documents.
- SHOULD: Compliance reviewers validating source-grounded answers.
- COULD: Product and support teams using the assistant for internal document triage.

## 3) Primary Use Cases
- MUST: Ask document-grounded questions and receive cited answers.
- MUST: Summarize one or multiple documents with key points.
- MUST: Perform deterministic calculations using document values.
- SHOULD: Filter documents by type, amount, and natural language amount constraints.
- SHOULD: Persist session context across turns.

## 4) Non-goals
- WON’T: Provide clinical diagnosis or treatment recommendations.
- WON’T: Provide financial investment advice.
- WON’T: Replace regulatory/compliance sign-off workflows.
- WON’T: Interpret handwritten/poor OCR scans in v1.

## 5) User Journeys
### Journey A: Q and A
1. User asks a question.
2. System classifies intent.
3. System retrieves relevant context.
4. System answers with citations and confidence.

### Journey B: Summarization
1. User requests summary for selected docs or discovered docs.
2. System retrieves target docs and generates structured summary.
3. System returns key points with source references.

### Journey C: Calculation
1. User requests a numerical result (for example total due over invoices above threshold).
2. System identifies needed docs, extracts values, computes deterministically.
3. System returns expression, result, and cited sources.

## 6) Functional Requirements
- FR-001 MUST: Intent classification into qa, summarization, calculation, unknown.
- FR-002 MUST: Route requests to task-specific processing path.
- FR-003 MUST: Support document search by keyword and type.
- FR-004 SHOULD: Support amount/range/approximate retrieval filters.
- FR-005 MUST: Read full document content by id.
- FR-006 MUST: Produce structured output per task.
- FR-007 MUST: Persist conversation session state.
- FR-008 SHOULD: Persist tool usage logs.
- FR-009 MUST: Attach citations to every factual answer.
- FR-010 MUST: Use deterministic tool execution for arithmetic.
- FR-011 SHOULD: Keep conversation summary and active document memory.
- FR-012 SHOULD: Provide user-visible failure explanations.

## 7) Non-functional Requirements
- NFR-001 MUST: Response traceability (source ids + tool logs).
- NFR-002 MUST: Domain safety controls for healthcare and finance.
- NFR-003 MUST: Deterministic/reproducible calculation path.
- NFR-004 MUST: Testability at unit, integration, and graph levels.
- NFR-005 SHOULD: Low-latency retrieval and bounded token usage.
- NFR-006 SHOULD: Configurable model/provider without code edits.
- NFR-007 MUST: Secure secret handling and no secret logging.
- NFR-008 MUST: Audit events for critical decisions and failures.

## 8) Financial Domain Requirements
- FIN-001 MUST: Numeric extraction and arithmetic must be deterministic.
- FIN-002 MUST: Sources for every numeric claim.
- FIN-003 SHOULD: Amount normalization with currency and unit handling.
- FIN-004 MUST: Refuse speculative investment recommendation questions.

## 9) Healthcare Domain Requirements
- HC-001 MUST: No diagnosis/treatment recommendations.
- HC-002 MUST: Explicit uncertainty when data insufficient.
- HC-003 MUST: PHI-aware handling and redaction controls.
- HC-004 SHOULD: Trigger human review for high-risk health prompts.

## 10) Accuracy and Citation Requirements
- AC-001 MUST: All factual claims cite source document ids.
- AC-002 MUST: If no evidence found, system must say insufficient evidence.
- AC-003 SHOULD: Citation includes snippet/span and section metadata.
- AC-004 MUST: Confidence is calibrated and not fabricated.

## 11) Calculation Requirements
- CAL-001 MUST: Calculation always executed via calculation tool.
- CAL-002 MUST: Show expression and final numeric result.
- CAL-003 MUST: Include source ids for all operands.
- CAL-004 SHOULD: Validate units and date alignment before compute.

## 12) Privacy and Security Requirements
- SEC-001 MUST: Secrets loaded from environment, never hardcoded.
- SEC-002 MUST: Session storage protected with least privilege.
- SEC-003 MUST: PHI/PII not logged in plain text where avoidable.
- SEC-004 SHOULD: Prompt-injection resistance and tool permission gating.

## 13) Auditability Requirements
- AUD-001 MUST: Record query, selected sources, tools used, model version.
- AUD-002 MUST: Record final answer and safety checks outcome.
- AUD-003 SHOULD: Version prompts and graph definitions.

## 14) Failure Modes
- FM-001 Retrieval miss causing hallucinated answer.
- FM-002 Wrong intent classification.
- FM-003 Incorrect arithmetic expression formulation.
- FM-004 Missing citations.
- FM-005 Prompt injection from document text.
- FM-006 Session corruption or incomplete persistence.

## 15) Human-in-the-loop Requirements
- HITL-001 SHOULD: Escalate healthcare high-risk outputs for human review.
- HITL-002 SHOULD: Escalate financial advisory-like prompts.
- HITL-003 MUST: Allow manual override and correction capture.

## 16) Acceptance Criteria
- A-001 MUST: At least 95 percent deterministic calculation correctness on golden dataset.
- A-002 MUST: 100 percent answers include citations or explicit no-evidence response.
- A-003 MUST: Zero critical PHI leakage in logs under red-team tests.
- A-004 SHOULD: Intent classification macro F1 above target threshold.
- A-005 SHOULD: End-to-end session persistence validated across restarts.

## 17) Open Questions
- OQ-001 Should retrieval remain in-memory for coursework or move to vector DB for realism?
- OQ-002 What PHI policy and data retention window is required in target deployment?
- OQ-003 Should healthcare and financial safety checks be separate policy modules?
- OQ-004 What confidence calibration method is acceptable?

## Requirements Traceability

| Requirement ID | Requirement | Current Support | Gap | Relevant Files |
|---|---|---|---|---|
| FR-001 | Intent classification | Partial | Unknown intent not explicitly routed in workflow mapping except fallback | [module-01-langchain-fundamentals/doc_assistant_project/src/agent.py](../src/agent.py), [module-01-langchain-fundamentals/doc_assistant_project/src/schemas.py](../src/schemas.py) |
| FR-002 | Task routing | Present | No explicit safety routing layer | [module-01-langchain-fundamentals/doc_assistant_project/src/agent.py](../src/agent.py) |
| FR-003 | Keyword/type retrieval | Present | No ranking quality tests | [module-01-langchain-fundamentals/doc_assistant_project/src/retrieval.py](../src/retrieval.py), [module-01-langchain-fundamentals/doc_assistant_project/src/tools.py](../src/tools.py) |
| FR-004 | Amount/range retrieval | Present | No unit/currency normalization | [module-01-langchain-fundamentals/doc_assistant_project/src/retrieval.py](../src/retrieval.py) |
| FR-005 | Read full document by id | Present | No access control | [module-01-langchain-fundamentals/doc_assistant_project/src/tools.py](../src/tools.py) |
| FR-006 | Structured outputs | Present | No response schema validation tests | [module-01-langchain-fundamentals/doc_assistant_project/src/schemas.py](../src/schemas.py), [module-01-langchain-fundamentals/doc_assistant_project/src/agent.py](../src/agent.py) |
| FR-007 | Session persistence | Present | JSON file storage only, no migration/versioning | [module-01-langchain-fundamentals/doc_assistant_project/src/assistant.py](../src/assistant.py) |
| FR-008 | Tool usage logs | Present | No privacy filtering in logs | [module-01-langchain-fundamentals/doc_assistant_project/src/tools.py](../src/tools.py) |
| FR-009 | Mandatory citations | Partial | Not enforced post-generation | [module-01-langchain-fundamentals/doc_assistant_project/src/prompts.py](../src/prompts.py), [module-01-langchain-fundamentals/doc_assistant_project/src/agent.py](../src/agent.py) |
| FR-010 | Deterministic arithmetic tool usage | Partial | Prompt instructs, but no hard runtime enforcement | [module-01-langchain-fundamentals/doc_assistant_project/src/prompts.py](../src/prompts.py), [module-01-langchain-fundamentals/doc_assistant_project/src/tools.py](../src/tools.py) |
| SEC-001 | Secrets handling | Partial | .env template present, no secret scanning policy | [module-01-langchain-fundamentals/doc_assistant_project/.env](../.env), [module-01-langchain-fundamentals/doc_assistant_project/main.py](../main.py) |
| NFR-004 | Testability and automated tests | Missing | No tests found | [module-01-langchain-fundamentals/doc_assistant_project](../) |
