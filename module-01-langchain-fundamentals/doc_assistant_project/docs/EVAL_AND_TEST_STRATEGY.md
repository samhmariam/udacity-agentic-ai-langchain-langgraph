# EVAL AND TEST STRATEGY

## Objective
Define a rigorous evaluation and testing framework for correctness, safety, and stability.

## 1) Unit Tests
- Retrieval logic by keyword, type, amount range, approximate amount.
- Calculator tool input validation and correctness.
- Prompt selector behavior per intent.
- Schema validation and serialization.

Current code under test:
- [module-01-langchain-fundamentals/doc_assistant_project/src/retrieval.py](../src/retrieval.py)
- [module-01-langchain-fundamentals/doc_assistant_project/src/tools.py](../src/tools.py)
- [module-01-langchain-fundamentals/doc_assistant_project/src/prompts.py](../src/prompts.py)
- [module-01-langchain-fundamentals/doc_assistant_project/src/schemas.py](../src/schemas.py)

## 2) Integration Tests
- End-to-end process_message flows for each intent.
- Session save and reload behavior.

## 3) Graph Tests
- Routing from classify_intent to correct task node.
- Node-to-node transitions and end conditions.
- Actions_taken accumulation.

Current graph location:
- [module-01-langchain-fundamentals/doc_assistant_project/src/agent.py](../src/agent.py)

## 4) Retrieval Tests
- Ranking and top_k expectations.
- Amount query parsing for over/under/between/exact/approximate.
- Retrieval miss behavior.

## 5) Citation Tests
- Every response includes citations or explicit insufficient evidence.
- Citation references existing document ids.

## 6) Calculation Accuracy Tests
- Expression planning and deterministic execution.
- Numeric precision and formatting.
- Negative tests for unsafe expression input.

## 7) Summarization Quality Tests
- Coverage of key points.
- Hallucination checks against source documents.
- Structure compliance.

## 8) Financial Document Tests
- Amount extraction consistency.
- Cross-document total calculations.
- Contract value and invoice total verification.

## 9) Healthcare Document Tests
- Claim amount computation and retrieval.
- Refusal behavior for diagnosis-like prompts.
- PHI redaction checks in logs.

## 10) Refusal and Safety Tests
- Prompt injection attempts from document text.
- Requests for prohibited financial/clinical advice.
- Missing evidence must trigger safe fallback.

## 11) Regression Tests
- Golden outputs for key scenarios.
- Intent routing consistency snapshots.
- Tool-use policy regression checks.

## 12) Golden Datasets
- Curated sets for qa, summarization, calculation.
- Separate corpora for finance and healthcare.
- Include adversarial and ambiguous examples.

## 13) Human Review Rubric
- Factual correctness.
- Citation quality.
- Numeric correctness.
- Safety compliance.
- Clarity and completeness.

## 14) LLM-as-judge Rubric
Use cautiously for style and coherence only, not final factual authority.
- Check answer relevance and completeness.
- Pair with deterministic citation and numeric validators.

## 15) CI and CD Gate Recommendations
- Block merge on unit and integration test failures.
- Block merge if citation coverage below threshold.
- Block release if high-severity safety regressions detected.
- Track benchmark trend dashboards.

## Test Matrix

| Test Type | Purpose | Example Case | Pass Criteria | Current Support | Gap |
|---|---|---|---|---|---|
| Unit retrieval | Validate retrieval correctness | Query invoices over 50000 | Expected docs returned | Missing | Add tests for retrieval module |
| Unit calculator | Validate deterministic arithmetic | Expression 1200+800+150+300 | Exact numeric result | Missing | Add calculator tests |
| Unit prompt selection | Correct system prompt route | intent calculation | correct prompt selected | Missing | Add prompt selector tests |
| Graph routing | Correct node transitions | Intent summarization | route to summarization node | Missing | Add graph tests with mocks |
| Integration end-to-end | Validate orchestration | process_message with qa query | success and structured output | Missing | Add integration harness |
| Citation test | Enforce grounding | factual answer query | citations present and valid | Missing | Implement citation validator |
| Calculation accuracy | Numeric correctness | sum invoice totals | deterministic expected result | Missing | Add numeric benchmark set |
| Safety refusal | Policy compliance | diagnosis request | refusal or escalation | Missing | Add safety policy node and tests |
| Regression suite | Stability over changes | golden set replay | no metric regressions | Missing | Add CI baseline evaluation |

## Current State Summary
- No test files were found in [module-01-langchain-fundamentals/doc_assistant_project](../).
- Immediate priority is test scaffolding before feature expansion.
