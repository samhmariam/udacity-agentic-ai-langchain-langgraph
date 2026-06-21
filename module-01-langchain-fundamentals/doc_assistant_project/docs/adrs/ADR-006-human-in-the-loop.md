# ADR-006: Human-in-the-loop for High-risk Cases

## Status
Proposed

## Context
Some outputs in healthcare and finance can carry high impact. Current flow in [module-01-langchain-fundamentals/doc_assistant_project/src/agent.py](../../src/agent.py) ends without review branch.

## Decision
Introduce conditional human review path for high-risk intent patterns and low-confidence verified outputs.

## Consequences
- Pros: governance and accountability.
- Cons: operational overhead and slower turnaround.

## Alternatives Considered
- Fully automated responses.
- Human review for every response.

## How to Revisit This Decision
Adjust thresholds and review policy based on measured error rates and business criticality.
