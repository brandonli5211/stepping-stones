# Implementation Plan: Evaluate Ordered Call Steps

**Branch**: `feat/evaluator-use-case` | **Date**: 2026-11-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/006-evaluator-use-case/spec.md`

## Summary

<!--
  REQUIRED for this project (constitution 1.5+):
  - Name exactly ONE primary application use case (Clean Architecture).
  - One short paragraph: primary requirement + technical approach.
  - One short paragraph: which layers that use case touches and that
    dependencies point inward (domain ← application/ports ← adapters ←
    infrastructure/UI). Do not plan a second use case here.
  - Also fill the Use Cases section below; keep it accurate after Phase 0
    and again after Phase 1.
-->

**Primary use case**: `EvaluateOrderedCall` — evaluates every required step in one stored, completed call and atomically saves the resulting coaching state.

The command selects stored calls and passes one numeric call ID to the use case. The use case loads the procedure, transcript turns, and logged-action data through a port; it asks the configured OpenAI Decisions model to choose an evidence turn and, when a step has recorded actions, whether those actions match the caller's transcript. Pure Python validates the selected evidence, applies the confidence threshold, derives status/severity/score, and saves the UI-facing totals in one transaction.

Dependencies point inward: pure ordered-evaluation entities and rules → the interactor with input/output and persistence/model ports → async SQLAlchemy, OpenAI Decisions, command controller, and presenter adapters → command and settings composition. Existing call-detail/list/progress views remain read-only consumers of the saved results.

## Use Cases

<!--
  REQUIRED (constitution 1.5+): List application use cases after each
  /speckit-plan phase. Exactly ONE primary use case per feature.
-->

| Use case | Responsibility | Module |
| --- | --- | --- |
| `EvaluateOrderedCall` (primary) | Evaluates one complete stored call in procedure order, resolves evidence and result states, and delegates all reads/writes/model requests through ports. It must not parse CLI arguments, use SQLAlchemy, or perform HTTP. | `backend/app/application/evaluate_ordered_call/interactor.py` |

**Out of scope for this plan**: human review resolution, live/in-progress turn streaming, frontend screen changes, and a second model provider.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python >= 3.12.

**Primary Dependencies**: FastAPI, SQLAlchemy async, psycopg, OpenAI Decisions HTTP API, and standard library only; no new dependency.

**Storage**: PostgreSQL 18 through async SQLAlchemy. Existing `calls`, `call_turns`, `call_steps`, and `procedures` store the final result. No schema change is planned because the command evaluates a complete call in one transaction rather than persisting an in-progress cursor.

**Testing**: pytest through `uv run test`; fakes for ports; a stub async session for persistence mapping; no live model requirement.

**Target Platform**: local backend command and Docker Compose PostgreSQL 18.

**Project Type**: backend web service with an offline command.

**Performance Goals**: one transaction per call; no model call while an API consumer opens a page.

**Constraints**: Python owns status, comparison, score, severity, and flags; model evidence quotes must match a stored turn word-for-word; confidence threshold is a named domain rule; uncertain/contradictory decisions remain under review; the normal stack remains usable without an OpenAI key except for opt-in live adapter checks.

**Scale/Scope**: all calls, one call type, or one call ID; starts with Transfer money, Replace card, and Check balance.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Before research | After design |
| --- | --- | --- |
| I. Server owns judgment | Pass: Python, not the UI or model, decides statuses and scores. | Pass. |
| II. Asynchronous API | N/A: this feature adds an offline command, not a route. | Pass. |
| III. Asynchronous persistence | Pass: one async session transaction per call. | Pass. |
| IV. Typed component UI | N/A: no frontend change. | N/A. |
| V. One stack | Pass: standard-library HTTP adapter and uv only. | Pass. |
| VI. Unit tests | Pass: every new function is planned with a direct unit test. | Pass. |
| VII. Clean Architecture | Pass: one primary use case, inward-only dependencies. | Pass. |
| Workflow | Pass: one feature, one use case, no more than six implementation tasks. | Pass. |

No gate failed.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
backend/
├── app/
│   ├── domain/ordered_evaluation.py
│   ├── application/
│   │   ├── ports.py
│   │   └── evaluate_ordered_call/
│   │       ├── input_boundary.py
│   │       ├── input_data.py
│   │       ├── output_boundary.py
│   │       ├── output_data.py
│   │       └── interactor.py
│   ├── adapters/
│   │   ├── llm/openai_decision.py
│   │   ├── persistence/ordered_call_store.py
│   │   └── command/analyze.py
│   └── infrastructure/analyze_command.py
└── tests/
    └── test_*ordered*_evaluation.py
```

**Structure Decision**: follow existing `domain/`, `application/`, and `adapters/` conventions. This feature adds explicit boundary and presenter classes inside its application/command slice without refactoring existing use cases.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | — | — |
