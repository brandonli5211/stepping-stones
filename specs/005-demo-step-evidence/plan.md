# Implementation Plan: Demo Step Evidence

**Branch**: `feat/33-load-demo-48` (issue #33) | **Date**: 2026-11-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-demo-step-evidence/spec.md`

## Summary

**Primary use case**: `ApplyDemoResults` (extended from feature 002). Besides validating and scoring each results row, it now validates the row's optional hand-labelled evidence against the call's stored turns and saves the evidence turn and quote on the named step. As before, it saves all calls together or none.

The presenter runs the same command as before (`uv run apply-demo-results ../sample/demo_48/results.csv`). The CSV gains three optional columns: `evidence_step`, `evidence_turn` and `evidence_quote`. For a row with evidence, the use case asks the store for that call's turns. The domain checks the evidence:
- the step is one the row marks missed or wrong;
- the turn exists;
- the quote appears word for word in the turn.

The scored step then carries the evidence, and the store writes it to the existing `call_steps.evidence_turn_idx` / `evidence_quote`. Nothing else changes: no migration, no route, no change to scores.

**Inward dependency path** (same modules as feature 002):

| Layer | Module | Change |
| --- | --- | --- |
| Domain | `app/domain/demo_results.py` | `ResultsRow` evidence fields, `StepEvidence`, `has_evidence`, `evidence_problems`, `evidence_for`. `ScoredStep` evidence fields, set by `score_call`. Standard library only. |
| Application | `app/application/ports.py`, `app/application/apply_demo_results.py` | `DemoCallStore.find_turns` port method. The use case loads turns only for rows with evidence and adds evidence problems. |
| Adapters | `app/adapters/files/demo_results_files.py` | Reads the three optional columns. |
| Adapters | `app/adapters/persistence/demo_call_store.py` | `FIND_TURNS` and `find_turns`. `UPDATE_STEP` also writes the two evidence fields. |
| Infrastructure | `app/infrastructure/apply_demo_results.py` | No change. |

Nothing inner imports anything outer.

## Use Cases

*Accurate after Phase 0 (research) and after Phase 1 (design).*

| Use case | Responsibility | Module |
| --- | --- | --- |
| `ApplyDemoResults` (primary, extended) | Validates every results row, including its optional step evidence, against its stored call and turns. It scores the valid rows with domain rules and saves all calls, with their evidence, through the `DemoCallStore` port only when no row has a problem. | `backend/app/application/apply_demo_results.py` |

**Out of scope for this plan**:
- The call detail API and screen (#34, #35), which will read the evidence.
- Any "flag" field: the flag is the stored Wrong status with critical severity (spec, Assumptions).
- `load_calls.py` / `call_parse.py` (not edited; still a separate follow-up).
- The stale read-back `sub_checks` left by the seed on step 5 (not touched by apply today; FR-008).

## Technical Context

**Language/Version**: Python ≥ 3.12 (uv; 3.13 on the host, 3.12 in the image).

**Primary Dependencies**: the existing SQLAlchemy 2 async stack with psycopg 3, and the standard library `csv`. No new dependency.

**Storage**: PostgreSQL 18. Writes go to the existing `call_steps.evidence_turn_idx` and `call_steps.evidence_quote` (migration 002). The table's foreign key `(call_id, evidence_turn_idx) → call_turns` guarantees the turn exists. No schema change and no migration.

**Testing**: pytest via `uv run test`, with no database needed. Two tests cover this feature: `test_bad_file_saves_nothing` gains 5 evidence cases (each unverifiable evidence saves nothing), and `test_demo_48_evidence` checks that the evidence in `sample/demo_48/results.csv` matches the transcript file of the call it names. `test_demo_48_numbers` also checks that the evidence is saved on the one step. Not every function has its own test (see Complexity Tracking). The real database is checked by [quickstart.md](quickstart.md).

**Target Platform**: developer and presenter machine. The command runs from `backend/`.

**Project Type**: web application backend, CLI command only.

**Performance Goals**: at most one extra query, and only when the file has evidence. 48 rows in a few seconds.

**Constraints**:
- **Clean Architecture**: domain and application import no FastAPI, SQLAlchemy, Alembic or psycopg.
- **All or nothing**: any bad row saves nothing.
- **Backward compatible**: a CSV without the evidence columns applies exactly as before.
- **FR-008**: no change to scores, statuses, severity, notes, sub-checks, comparison, or either endpoint.

**Scale/Scope**: one use case extended, five source modules edited, one data file edited, about 5 tasks.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Before research | After design |
| --- | --- | --- |
| I. Server owns the judgment | Pass. Whether a quote supports a step is checked in the backend domain. | Pass. `evidence_problems` is in `app/domain`. |
| II. Asynchronous API | Pass. No route added or changed. | Pass. |
| III. Asynchronous persistence | Pass. Existing columns only, so no migration is needed. | Pass. `find_turns` and the extended `UPDATE_STEP` run on the `AsyncSession` inside the command's single transaction. |
| IV. Typed component UI | Pass. No frontend change. | Pass. |
| V. One stack | Pass. No new package. | Pass. |
| VI. Unit test every new function | Pass (planned). | **Deviation, accepted 2026-11-19.** The tests were cut; see Complexity Tracking. |
| VII. Clean Architecture | Pass. Rules in the domain, one new port method, wiring unchanged. | Pass. The domain stays standard library only. The use case imports only the domain and ports. The existing import-guard tests still cover `fastapi`, `sqlalchemy`, `alembic` and `psycopg`. |
| Workflow | Pass. Branch `feat/33-load-demo-48`, issue #33, one primary use case named in the Summary and in Use Cases. | Pass. The tasks are planned as one vertical slice of 6 or fewer. |
| Governance: touched non-compliant files | Pass. All edited files are already compliant. `app/models.py` is only imported by the persistence adapter, as in feature 002. | Pass. |

Principle VI is not met after the 2026-11-19 test cut; the deviation is recorded in Complexity Tracking. No other gate failed.

## Project Structure

### Documentation (this feature)

```text
specs/005-demo-step-evidence/
├── spec.md
├── plan.md              # this file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   └── apply-demo-results-command.md   # input-file and problem-message changes
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── domain/demo_results.py                      # EDIT evidence types and rules; ScoredStep evidence
│   ├── application/
│   │   ├── ports.py                                # EDIT DemoCallStore.find_turns
│   │   └── apply_demo_results.py                   # EDIT load turns, evidence problems
│   └── adapters/
│       ├── files/demo_results_files.py             # EDIT optional evidence columns
│       └── persistence/demo_call_store.py          # EDIT FIND_TURNS, find_turns, UPDATE_STEP evidence
└── tests/
    ├── test_apply_demo_results.py                  # EDIT +5 evidence cases in test_bad_file_saves_nothing
    ├── test_demo_results_files.py                  # NEW  the demo_48 evidence quote is in its turn
    ├── demo_48_data.py                             # EDIT the in-memory store serves stored turns
    └── test_demo_48.py                             # EDIT the evidence lands on the one step
sample/demo_48/results.csv                          # EDIT three columns; HVB-DEMO-06 evidence
```

**Structure Decision**: extend feature 002's modules in place. No new module is needed, because the evidence belongs to the same results row, use case, port and transaction.

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
| --- | --- | --- |
| Principle VI (unit test every new function) is not met. | On 2026-11-19 the product owner cut this feature's tests to 5 evidence cases in `test_bad_file_saves_nothing` and `test_demo_48_evidence`, plus an evidence check in `test_demo_48_numbers`. The domain rules and `read_results_csv` are covered only through those tests. No test calls `find_turns`, `to_turn_texts`, `FIND_TURNS` or the extended `UPDATE_STEP` and `step_params`; the real database run in quickstart.md is their only check. | One unit test per function was the original plan and was cut on purpose. Reviewers must accept this deviation explicitly. |

## Phase 0 and Phase 1 outputs

- **Phase 0**: [research.md](research.md), decisions R1–R7. No NEEDS CLARIFICATION remained.
- **Phase 1**: [data-model.md](data-model.md), [contracts/apply-demo-results-command.md](contracts/apply-demo-results-command.md), [quickstart.md](quickstart.md).

**Post-design constitution check**: all gates passed at design time (Principle VI is a recorded deviation since the 2026-11-19 test cut). The evidence rules are pure domain code. The port is the only path to the turns. The command remains the transaction owner. No business rule sits in a router, ORM model or UI. The Use Cases section lists exactly one primary use case after both phases.
