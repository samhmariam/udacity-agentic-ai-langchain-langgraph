# IMPLEMENTATION ROADMAP

## Strategy
Prioritize architectural learning, correctness, and safety before feature expansion.

| Priority | Work Item | Why It Matters | Files Impacted | Effort | Risk Reduced | Acceptance Criteria |
|---|---|---|---|---|---|---|
| P0 | Align dependency management | Prevent setup drift and install failures | [module-01-langchain-fundamentals/doc_assistant_project/requirements.txt](../requirements.txt), [module-01-langchain-fundamentals/doc_assistant_project/pyproject.toml](../pyproject.toml) | Low | Medium | Clean install path documented and verified |
| P0 | Add test scaffold | Baseline reliability and regression safety | new tests folder, [module-01-langchain-fundamentals/doc_assistant_project/src](../src) | Medium | High | Unit and integration tests run in CI |
| P0 | Add citation verifier node | Prevent unsupported factual outputs | [module-01-langchain-fundamentals/doc_assistant_project/src/agent.py](../src/agent.py), [module-01-langchain-fundamentals/doc_assistant_project/src/schemas.py](../src/schemas.py) | Medium | High | Responses fail closed when citation coverage missing |
| P0 | Enforce deterministic calculation policy | Avoid arithmetic hallucinations | [module-01-langchain-fundamentals/doc_assistant_project/src/agent.py](../src/agent.py), [module-01-langchain-fundamentals/doc_assistant_project/src/tools.py](../src/tools.py) | Medium | High | All calculation answers have tool execution evidence |
| P1 | Safety and privacy policy checks | Reduce healthcare and finance harm risk | [module-01-langchain-fundamentals/doc_assistant_project/src/agent.py](../src/agent.py), new safety module | Medium | Critical | High-risk prompts blocked or escalated |
| P1 | Retrieval quality upgrades | Improve grounding and reduce hallucination | [module-01-langchain-fundamentals/doc_assistant_project/src/retrieval.py](../src/retrieval.py) | High | High | Benchmark lift in retrieval hit quality |
| P1 | Structured audit event pipeline | Ensure traceability and debugging | [module-01-langchain-fundamentals/doc_assistant_project/src/assistant.py](../src/assistant.py), [module-01-langchain-fundamentals/doc_assistant_project/src/tools.py](../src/tools.py) | Medium | High | End-to-end request trace available |
| P2 | Human review workflow | Governance for high-risk responses | [module-01-langchain-fundamentals/doc_assistant_project/src/agent.py](../src/agent.py), UI/API layer | Medium | High | Review-required cases pause and resume safely |
| P2 | Real ingestion pipeline | Move beyond simulated docs | [module-01-langchain-fundamentals/doc_assistant_project/src/retrieval.py](../src/retrieval.py), new ingestion modules | High | Medium | Upload -> parse -> index works for sample file types |
| P2 | Evaluation suite and golden datasets | Quantify quality and safety over time | new eval and test assets | High | High | CI gate with quality thresholds |

## Milestones

### Milestone 1: Foundation Hardening
- Dependency alignment
- Test scaffolding
- Basic unit tests for retrieval and calculator
- Definition of done:
  - Local and CI test command passes
  - At least one failing-to-passing regression captured

### Milestone 2: Grounded Response Guarantees
- Citation verifier node
- Deterministic calc enforcement checks
- Structured response validation tests
- Definition of done:
  - 100 percent factual outputs include citations or no-evidence response
  - Calculation benchmark meets threshold

### Milestone 3: Safety and Governance
- Safety and privacy policy module
- Human escalation branch
- Audit event coverage
- Definition of done:
  - High-risk prompts reliably blocked/escalated
  - Audit records complete for all requests

### Milestone 4: Retrieval and Ingestion Evolution
- Real document ingestion and chunk lineage
- Retrieval quality improvements
- Domain evaluation datasets
- Definition of done:
  - Ingestion supports agreed formats
  - Retrieval and answer quality metrics exceed baseline targets

## Immediate Fixes
1. Resolve requirements.txt placeholder inconsistency.
2. Correct schema and state mismatches noted in current behavior doc.
3. Add minimal smoke tests for process_message and graph routing.
