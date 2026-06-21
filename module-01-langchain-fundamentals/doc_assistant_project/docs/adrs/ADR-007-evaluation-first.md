# ADR-007: Evaluation Is a Core Architecture Component

## Status
Proposed

## Context
No tests or evaluation suite currently exists in the project root, increasing regression and safety risk.

## Decision
Treat evaluation as first-class architecture: golden datasets, regression gates, safety tests, and domain-specific metrics in CI.

## Consequences
- Pros: measurable quality and safer releases.
- Cons: initial setup effort and data curation overhead.

## Alternatives Considered
- Ad hoc manual testing.
- Post-release monitoring only.

## How to Revisit This Decision
Revisit after stable metrics and process maturity prove lower-cost alternatives sufficient.
