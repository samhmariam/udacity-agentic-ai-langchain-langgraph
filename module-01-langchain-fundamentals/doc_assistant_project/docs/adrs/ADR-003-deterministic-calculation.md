# ADR-003: Calculations Must Be Tool-based and Deterministic

## Status
Proposed

## Context
Current calculation path includes a calculator tool in [module-01-langchain-fundamentals/doc_assistant_project/src/tools.py](../../src/tools.py), while prompts ask the model to use it in [module-01-langchain-fundamentals/doc_assistant_project/src/prompts.py](../../src/prompts.py).

## Decision
All arithmetic outputs must be produced by deterministic tool execution. LLM may only plan expressions and explain results.

## Consequences
- Pros: reproducibility and auditability.
- Cons: requires strict tool policy checks and expression validation.

## Alternatives Considered
- LLM-only arithmetic in response generation.
- Post-hoc numeric correction pass only.

## How to Revisit This Decision
Revisit only if deterministic compute engine is replaced with stronger typed symbolic math service.
