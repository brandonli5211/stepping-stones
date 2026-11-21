---

description: "Task list for the persisted ordered evaluator"
---

# Tasks: Evaluate Ordered Call Steps

**Input**: Design documents from `specs/006-evaluator-use-case/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/analyze-command.md

## Use Case: EvaluateOrderedCall

**Goal**: Analyze one complete stored call in procedure order, use OpenAI Decisions only for facts/evidence, and atomically save results that existing call-detail/list/progress readers can present.

**Independent Test**: Run `uv run analyze --call-id <fixture-id>` with a fake decision model and verify every stored step state, evidence, comparison, aggregate count, and terminal result through the existing call-detail reader.

- [X] T001 [US1] Implement ordered-evaluation domain records, named confidence rule, quote validation, logged-action comparison, and terminal state rules in `backend/app/domain/ordered_evaluation.py`; include direct tests in `backend/tests/test_domain_ordered_evaluation.py`.
- [X] T002 [US1] Add `EvaluateOrderedCall` input/output boundaries, data records, interactor, and required source/model/store protocols in `backend/app/application/evaluate_ordered_call/` and `backend/app/application/ports.py`; include direct tests in `backend/tests/test_evaluate_ordered_call.py`.
- [ ] T003 [US1] Implement an async SQLAlchemy source/store that loads procedure/turn/action data and atomically saves `CallStep` and `Call` fields in `backend/app/adapters/persistence/ordered_call_store.py`; test row mapping, rollback, idempotency, and call-detail consistency in `backend/tests/test_ordered_call_store.py`.
- [X] T004 [US1] Implement the OpenAI Decisions adapter, including structured-fact parsing, refusal/malformed handling, and word-for-word evidence preservation, in `backend/app/adapters/llm/openai_decision.py`; test each function in `backend/tests/test_openai_decision.py`.
- [ ] T005 [US1] Implement the `uv run analyze` command controller and output presenter in `backend/app/adapters/command/analyze.py` and compose settings in `backend/app/infrastructure/analyze_command.py`; add the script entry point and test selector/output/error behavior in `backend/tests/test_analyze_command.py`.
- [ ] T006 [US1] Run the quickstart and complete cross-layer validation in `backend/tests/test_ordered_evaluation_integration.py`, including 0.79/0.80/0.81 confidence, contradiction, refusal, invalid quote, ended-call finalization, logged-action mismatch, and existing list/detail/progress aggregate consistency; update `README.md` with the local model, memory requirement, and command instructions.

**Checkpoint**: `EvaluateOrderedCall` works through domain → application ports → OpenAI Decisions/persistence/command adapters; domain and application import no FastAPI or SQLAlchemy.

---

## Dependencies & Execution Order

1. T001 defines the pure state rules.
2. T002 applies those rules through the single use case.
3. T003 and T004 implement the ports and may proceed in parallel after T002.
4. T005 composes the completed ports into the offline command.
5. T006 validates the completed vertical slice.

## Implementation Strategy

1. Complete T001 and T002 with fake ports first.
2. Complete T003 and T004, then use T005 to make the real command runnable.
3. Stop when T006 proves persisted results are visible through existing readers; defer human review resolution and live turn streaming to later features.
