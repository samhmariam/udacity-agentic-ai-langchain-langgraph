# ADR-004: Citations Are Mandatory for Factual Claims

## Status
Proposed

## Context
Prompts ask for citing sources in [module-01-langchain-fundamentals/doc_assistant_project/src/prompts.py](../../src/prompts.py), but runtime does not hard-enforce citation completeness.

## Decision
Introduce mandatory citation attachment and verification node. If evidence is insufficient, response must explicitly declare insufficient evidence.

## Consequences
- Pros: trustworthiness and auditability.
- Cons: possible increase in refusal rate when retrieval is weak.

## Alternatives Considered
- Best-effort citations only.
- Confidence-only without citations.

## How to Revisit This Decision
Revisit only if downstream system supplies independently verifiable provenance.
