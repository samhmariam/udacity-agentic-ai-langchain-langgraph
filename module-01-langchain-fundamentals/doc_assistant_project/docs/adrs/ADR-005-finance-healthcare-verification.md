# ADR-005: Finance and Healthcare Responses Need Verification Gates

## Status
Proposed

## Context
The project targets financial and healthcare documents, both high-risk domains, but current implementation has no explicit safety gate nodes.

## Decision
Add verification gates for numeric correctness, citation coverage, and policy checks before final response emission.

## Consequences
- Pros: reduced harmful errors.
- Cons: added latency and complexity.

## Alternatives Considered
- Prompt-only safeguards.
- Human review only for all outputs.

## How to Revisit This Decision
Revisit when risk appetite, domain scope, and compliance requirements are formally defined.
