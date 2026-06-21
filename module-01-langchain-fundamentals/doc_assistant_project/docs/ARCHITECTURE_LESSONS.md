# ARCHITECTURE LESSONS

## Why This Artifact Matters
This document extracts reusable architecture principles from this repository so you can design future agentic systems with confidence.

## 1) Moving from Vague Brief to Specification
- Start with strict inventory of what exists versus what is intended.
- Convert aspirations into requirement IDs and acceptance criteria.
- Separate facts from assumptions in every review deliverable.

Use this pattern in any project:
1. Repo audit
2. Current behavior mapping
3. Product and technical spec
4. Architecture proposal
5. Risk and evaluation design

## 2) Deterministic vs Agentic Components
- Deterministic where correctness is mandatory:
  - retrieval filters
  - calculations
  - policy checks
  - citation validation
- Agentic where interpretation is required:
  - intent classification
  - synthesis and explanation

Rule of thumb:
- If an error can cause material harm, keep that step deterministic or strongly verified.

## 3) Designing LangGraph State
- Keep state explicit, typed, and auditable.
- Include both working state and governance state:
  - evidence
  - citations
  - safety flags
  - actions taken
- Avoid stuffing raw unbounded history into every node; keep summaries and references.

Current baseline state reference:
- [module-01-langchain-fundamentals/doc_assistant_project/src/agent.py](../src/agent.py)

## 4) Defining Tools Safely
- Every tool should be:
  - deterministic if possible
  - schema-bounded
  - side-effect aware
  - logged with minimal sensitive data
- Tool outputs should be machine-readable first, human-readable second.

Current baseline tools:
- [module-01-langchain-fundamentals/doc_assistant_project/src/tools.py](../src/tools.py)

## 5) Retrieval with Citations
- Retrieval without citation validation is insufficient in high-risk domains.
- Build citation as a data product, not formatting sugar.
- Add claim-to-evidence checks as a hard gate.

## 6) High-risk Domain Handling
- Prompt guidance alone is not a safety strategy.
- For healthcare and financial contexts, enforce:
  - refusal policies
  - human escalation
  - audit logging
  - deterministic numeric verification

## 7) Evaluations as Architecture
- Evaluation must be built into design from day one.
- Use golden sets, risk-focused tests, and regression gates.
- Measure what matters:
  - citation validity
  - numeric correctness
  - safety compliance

## 8) Avoiding Over-engineering
- Do not start with many agents.
- Start with one orchestrator graph plus deterministic tools.
- Add complexity only where empirical failure data justifies it.

## 9) Writing Reusable Architecture Documents
Reusable package for future projects:
- REPO_AUDIT
- CURRENT_BEHAVIOR
- SPEC
- ARCHITECTURE
- LANGGRAPH_DESIGN
- DATA_MODEL
- EVAL_AND_TEST_STRATEGY
- RISK_REVIEW
- ADR set
- IMPLEMENTATION_ROADMAP

## 10) Applying This Pattern to Future Systems
When building any new agentic system:
1. Inventory reality.
2. Define requirements with MUST/SHOULD/COULD/WON’T.
3. Isolate deterministic boundaries.
4. Design graph around verifiable checkpoints.
5. Build evaluation and risk controls before feature scaling.

## Agentic System Architecture Checklist

### Problem and Scope
- [ ] Have I written a concrete problem statement?
- [ ] Are target users and non-goals explicit?
- [ ] Are high-risk domains identified?

### Current State
- [ ] Do I know exactly what the code does today?
- [ ] Did I separate observed facts from assumptions?
- [ ] Do I have a gap list tied to file evidence?

### Requirements
- [ ] Are requirements prioritized with MUST/SHOULD/COULD/WON’T?
- [ ] Are acceptance criteria measurable?
- [ ] Is there a traceability table from requirement to code?

### Architecture
- [ ] Which steps are deterministic?
- [ ] Which steps truly need LLM reasoning?
- [ ] Is LangGraph state explicit and minimal?
- [ ] Are tool boundaries strict and testable?

### Safety and Governance
- [ ] Are citations mandatory and verified?
- [ ] Are calculations deterministic and provenance-backed?
- [ ] Are privacy and retention policies enforced?
- [ ] Is there a human review path for high-risk outputs?

### Evaluation and Delivery
- [ ] Do tests cover unit, integration, graph, safety, and regressions?
- [ ] Are golden datasets in place for each major capability?
- [ ] Are CI gates tied to quality and safety metrics?
- [ ] Is there a roadmap with milestone definitions of done?

## Final Learning Summary
This repository is a strong teaching base for stateful orchestration and tool integration. The main lesson is that real production confidence in agentic systems comes from deterministic boundaries, explicit state design, citation and calculation verification, and evaluation-first engineering discipline.
