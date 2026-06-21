# RISK REVIEW

## Scope
Risk analysis for document assistants operating on financial and healthcare data.

## Risk Register

| Risk | Severity | Example Failure | Mitigation | Required Test |
|---|---|---|---|---|
| Hallucinated answers | High | Assistant invents contract clause | Mandatory citation verifier and no-evidence fallback | Citation coverage and hallucination challenge set |
| Missing citations | High | Correct-sounding answer with no source ids | Hard fail gate before final response | Citation validator unit and integration tests |
| Wrong calculations | High | Incorrect claim total due to malformed expression | Deterministic calc tool, operand provenance checks | Calculation accuracy golden tests |
| Misread tables | High | Wrong amount extracted from table-like content | Structured parsers and extraction validation | Table extraction benchmark tests |
| PHI or PII leakage | Critical | Claimant details leaked in logs | Redaction, encryption, least-data logging | Red-team privacy leakage tests |
| Prompt injection in documents | High | Document instructs model to ignore policy | Context isolation and tool permission boundaries | Injection resilience tests |
| Tool misuse | Medium | Wrong tool called or skipped | Tool policy constraints and post-checks | Tool invocation policy tests |
| Over-trusting retrieved context | High | Low relevance chunk used as source | Reranking and evidence threshold | Retrieval relevance tests |
| Unsafe healthcare interpretation | Critical | Medical advice generated from claims data | Safety policy and human escalation | Healthcare refusal and escalation tests |
| Financial advice risk | High | Investment recommendation provided | Domain refusal rules and disclaimer policy | Financial advisory refusal tests |
| Data retention risk | High | Sensitive sessions stored indefinitely | Retention policy and purge workflows | Retention policy tests |
| Access control gaps | High | User reads unauthorized docs | AuthZ checks before retrieval and read | Access control tests |
| Audit trail gaps | Medium | Cannot reconstruct decision path | Node-level audit events and request ids | Audit completeness tests |
| Model or version drift | Medium | Quality drops after model update | Version pinning and canary evaluations | Drift detection regression tests |
| Evaluation blind spots | High | Passing tests miss safety failures | Diverse datasets and adversarial cases | Coverage audit and red-team suite |

## Current Baseline Evidence
- Current implementation files:
  - [module-01-langchain-fundamentals/doc_assistant_project/src/agent.py](../src/agent.py)
  - [module-01-langchain-fundamentals/doc_assistant_project/src/tools.py](../src/tools.py)
  - [module-01-langchain-fundamentals/doc_assistant_project/src/retrieval.py](../src/retrieval.py)
  - [module-01-langchain-fundamentals/doc_assistant_project/src/assistant.py](../src/assistant.py)
- No explicit risk controls beyond prompt instructions and basic exception handling are currently implemented.

## Priority Mitigation Order
1. Citation enforcement and deterministic calculation verification.
2. Safety and privacy policy node with escalation path.
3. Test and evaluation harness with red-team coverage.
4. Access control and retention controls for session and logs.
