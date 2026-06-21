# AGENTIC DESIGN REVIEW

## Executive Position
This system benefits from selective agentic behavior, not full autonomy everywhere. Use deterministic pipelines for retrieval, calculation execution, citation verification, and safety checks. Use LLM reasoning where interpretation and language generation are required.

## 1) Which Parts Should Be Deterministic Pipelines?
- Document ingestion and indexing.
- Retrieval filters and ranking post-processing.
- Calculation execution.
- Citation attachment validation.
- Safety policy checks and rule-based blocks.

Evidence in current code:
- Deterministic retrieval and amount filters in [module-01-langchain-fundamentals/doc_assistant_project/src/retrieval.py](../src/retrieval.py).
- Deterministic calculator tool in [module-01-langchain-fundamentals/doc_assistant_project/src/tools.py](../src/tools.py).

## 2) Which Parts Need LLM Reasoning?
- Intent classification.
- Question answering over retrieved context.
- Summarization and explanation generation.
- Formula planning from natural language before deterministic execution.

Current evidence:
- Intent and task nodes in [module-01-langchain-fundamentals/doc_assistant_project/src/agent.py](../src/agent.py).

## 3) Which Parts Need LangGraph State?
- Session-aware routing and conversation memory.
- Tracking actions_taken, active_documents, and summary.
- Maintaining deterministic checkpoints between nodes.

Current evidence:
- AgentState and InMemorySaver use in [module-01-langchain-fundamentals/doc_assistant_project/src/agent.py](../src/agent.py).
- Session JSON persistence in [module-01-langchain-fundamentals/doc_assistant_project/src/assistant.py](../src/assistant.py).

## 4) Which Parts Need Tools?
- Calculator for all arithmetic.
- Document search and document reader.
- Collection statistics and diagnostics.

Current evidence:
- Tools in [module-01-langchain-fundamentals/doc_assistant_project/src/tools.py](../src/tools.py).

## 5) Which Parts Should Not Be Agentic?
- Security policy checks.
- PHI/PII redaction.
- Calculation execution.
- Citation required checks.
- Access control decisions.

## 6) Where Should Routing Happen?
- First routing at intent classification.
- Secondary routing after verification and safety check.
- Safety route can divert to human review.

## 7) Where Should Human Approval Happen?
- Healthcare interpretations with potential harm.
- High-impact financial calculations.
- Cases with low confidence or missing citations.

## 8) Failure Modes of Agent Use Here
- Tool hallucination or skipped tool usage.
- Wrong intent routing.
- Confident hallucinations from sparse retrieval.
- Prompt injection from document content.
- Citation omission.

## 9) Over-engineered Architecture to Avoid
- Multi-agent swarms for simple three-intent routing.
- Autonomous planning loops without deterministic constraints.
- Complex memory agents before robust retrieval and safety base.

## 10) Simplest Production-grade Version
- Single orchestrator graph.
- Deterministic retrieval and calc tools.
- Mandatory citation verifier node.
- Safety checker node with human escalation.
- Golden dataset evaluation gates in CI.

## Capability Classification Table

| Capability | Pipeline, Chain, Tool, or Agent? | Why | Risk | Recommendation |
|---|---|---|---|---|
| Intent classification | Agent or Chain | Language interpretation | Misroute | Keep as small structured LLM call |
| Document retrieval | Pipeline plus Tool | Deterministic filtering and ranking | Missed evidence | Keep deterministic with testable scoring |
| Reading document by id | Tool | Simple deterministic operation | Access misuse | Add authorization checks |
| Arithmetic execution | Tool | Deterministic correctness | Wrong expression input | Keep tool-only execution, never freeform arithmetic |
| Summarization | Agent | Requires abstraction and language | Hallucination | Restrict to retrieved context and verify citations |
| Question answering | Agent | Natural language generation | Fabricated facts | Enforce citation and no-evidence fallback |
| Citation verification | Pipeline | Rule-based coverage checks | False trust | Add hard fail on missing citations |
| Safety policy | Pipeline | Should be deterministic and auditable | Harmful output | Implement explicit policy rules |
| Session persistence | Pipeline | Data management concern | Data corruption | Version schema and validate writes |
| Human escalation | Pipeline node | Governance and accountability | Latency | Trigger by strict risk thresholds |
