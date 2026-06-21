# ADR-001: LangGraph as Orchestration Backbone

## Status
Proposed

## Context
The project currently routes intents through a small state graph in [module-01-langchain-fundamentals/doc_assistant_project/src/agent.py](../../src/agent.py). The domain requires traceability, safety checks, deterministic boundaries, and possible human escalation.

## Decision
Use LangGraph as the orchestration backbone for request lifecycle management, while keeping deterministic pipelines for retrieval verification, calculations, and safety checks.

## Consequences
- Pros: explicit state transitions, checkpointing, auditability.
- Cons: added architecture complexity versus a single chain.

## Alternatives Considered
- Single chain with prompt routing.
- Multi-agent swarm architecture.

## How to Revisit This Decision
Revisit if requirements simplify to single-task FAQ behavior with low-risk domain data.
