---

description: "Task list for GetProgress (issue #37, backend half)"
---

# Tasks: Get Progress

**Input**: Design documents from `/specs/006-get-progress/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/get-progress.md, quickstart.md, constitution.md (1.5.0)

**Tests**: cut on 2026-11-19 to two tests plus the shared layer guard, at the product owner's request; a third, `test_progress_small_dataset`, was added on 2026-11-20. This does not meet constitution VI; the deviation is recorded in plan.md Complexity Tracking. The tests need no database. The real queries are checked in T006 through quickstart.md.

**Organization**: ONE Clean Architecture use case, `GetProgress` (plan.md Summary), as a single vertical slice of 6 tasks. Spec stories US1–US4 are all served by this one slice.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: `[US1]` = the single use-case slice
- Paths are relative to the repository root

## Use Case: GetProgress (from plan.md Summary)

**Goal**: `GET /progress` returns the 8 weekly percents, this week against the first week, the percent per call type, the step rows and the demo-data flag, all worked out on the server.

**Independent Test** (full commands in quickstart.md):
1. `uv run test` is green.
2. With demo_48 loaded and `DEMO_TODAY=2026-10-09T23:59:59+00:00`: weekly percents 64, 70, 68, 75, 80, 79, 86, 90; by call type 88, 86, 85, 80, 79, 77, 73, 69; 26 step rows, the first 13 as in spec User Story 3.
3. `this_week` and `first_week_percent` equal `GET /calls?weeks=8`.

- [X] T001 [US1] **Domain.** Create `backend/app/domain/progress.py` (standard library plus `app.domain.call_list`), exactly per data-model.md "Domain".
  - **Constants**: `WEEKS = 8`, `TYPE_WINDOW = 5`, `SHARED_WINDOW = 10`, `RESOLVED = ("completed", "missed", "wrong")`, `MISSES = ("missed", "wrong")`.
  - **Types**: `ProgressWindow`, `ProgressWeek`, `CallTypeTotals`, `CallTypeProgress`, `StepResult`, `StepRow` with the fields in data-model.md.
  - **`progress_window(now, agent_id)`**: "`since` = 00:00 UTC on `monday − 7 weeks`. `until` = 00:00 UTC on `monday + 1 week`. `agent_id or None`."
  - **`eight_weeks(totals, now)`**: "Exactly 8 weeks, oldest first … A week with no totals has 0, 0 and `percent None` … Only the last is `is_current`. Totals for other weeks are ignored."
  - **`call_type_progress(totals)`**: "Ordered by percent, highest first, with `None` last; ties by `name`."
  - **`step_rows(results, shared_keys)`**: the five steps in data-model.md (keep resolved, order by `(started_at, call_id)`, group shared by `(None, step_key)` and others by `(call_type, step_key)`, keep the last 10 or 5, order by misses then shared-first then `call_type_name` then position then `step_key`).
  - **Tests**: no unit test of its own (2026-11-19 test cut). The rules run on a small fixed dataset in `test_progress_small_dataset` and on the demo data in `test_progress_demo_48` (T006), and the shared layer guard covers the module.
- [X] T002 [US1] **Application.** Create `backend/app/application/get_progress/` with `__init__.py`, `input_data.py` (`GetProgressInputData`), `input_boundary.py` (`GetProgressInputBoundary`), `output_data.py` (`GetProgressOutputData`), `output_boundary.py` (`GetProgressOutputBoundary`), `data_access.py` (`ProgressDataAccess`) and `interactor.py` (`GetProgressInteractor`), one class per file, per data-model.md "Application". Add `SharedStepsSource` to `backend/app/application/ports.py` ("`async load(self) -> frozenset[str]`. Raises `RulesUnavailable`."). The interactor follows the four steps in data-model.md and reuses `call_list.this_week` and `call_list.first_week_percent`. No unit test of its own (2026-11-19 test cut): the interactor runs in `test_progress_demo_48` (success) and `test_progress_503_without_rules` (`RulesUnavailable` → `prepare_fail_view`). The shared layer guard covers the package and `ports.py`.
- [X] T003 [P] [US1] **Data adapters.** Create `backend/app/adapters/persistence/progress_data_access.py` per data-model.md "Other adapters": `DEMO_MODEL`, `window_clauses`, `week_totals_query`, `call_type_totals_query`, `step_results_query`, `demo_calls_query` and `SqlAlchemyProgressDataAccess` with the four async port methods mapping rows to `WeekTotals`, `CallTypeTotals` and `StepResult`. Import `WEEK` from `call_list_reader.py`. Create `backend/app/adapters/files/shared_steps.py` with `JsonSharedSteps(rules_dir)` ("`FileNotFoundError` becomes `RulesUnavailable`"). No unit test of the SQL adapter (2026-11-19 test cut); T006's database run checks it. `JsonSharedSteps` runs in both kept tests (real rules folder, and a missing folder).
- [X] T004 [P] [US1] **Controller, presenter, view model.** Create `backend/app/adapters/http/progress/__init__.py`, `view_model.py` (`ProgressViewModel` with `body()`), `presenter.py` (`GetProgressPresenter` with `prepare_success_view`, `prepare_fail_view`, `label`, `summary`) and `controller.py` (`GetProgressController`), per data-model.md and contracts/get-progress.md. Summary lines follow research.md R8. No unit test of its own (2026-11-19 test cut): the presenter's labels, summary lines and comparison line are asserted on the demo data in `test_progress_demo_48`; `prepare_fail_view` and the controller run in `test_progress_503_without_rules`.
- [X] T005 [US1] **Route and wiring.** Create `backend/app/adapters/http/progress/router.py`: `get_progress_parts(request, session)` and `async def progress(...)` for `GET /progress`, which raises `HTTPException(503, …)` when the view model has an error. Edit `backend/app/infrastructure/analysis_settings.py` (`shared_steps_from_env`) and `backend/app/main.py` (`configure_progress`, include the router). Test: `backend/tests/test_progress_route.py`: `test_progress_503_without_rules`: `get_progress_parts` with a missing rules folder and a session that is never used, then `progress(...)` raises 503 with the missing path. Wiring in `main.py` has no unit test (2026-11-19 test cut).
- [X] T006 [US1] **Demo numbers and verification.** Create `backend/tests/test_progress_demo_48.py`: seed the 48 calls with `parse_call` + `seed_steps`, apply the real `results.csv` through `ApplyDemoResults` with an in-memory store, build an in-memory `ProgressDataAccess` from the result, and run `GetProgressInteractor` with `FixedClock(2026-10-09T23:59:59Z)`, the real `JsonSharedSteps` and the real presenter. Assert:
  - SC-001 (weekly 64, 70, 68, 75, 80, 79, 86, 90, with the steps of spec US1/AC1);
  - SC-002 (the eight call types of spec US2/AC1, in order);
  - SC-003 (26 rows; the 13 rows of spec US3/AC2 in order, with their results and summary lines);
  - SC-004 (this week 53 of 59, 90; first week 64).

  Create `backend/tests/test_progress_small_dataset.py` (added 2026-11-20): six fixed calls over three weeks in two call types, one wrong step and one step under review, run through `GetProgressInteractor` and the real presenter with a fake data access. Assert the weekly percents (five empty weeks, then 83, 80, 83), this week 5 of 6 and "Same as 83% in week 1", Pay bill 83 and Replace card 82, the top row "Confirm replacement" with results missed, wrong, completed and "Missed on 2 of your last 3 replace-card calls", and that no row contains `under_review` (SC-006).

  Run `uv run test`. Run quickstart.md steps 2–6 against PostgreSQL 18 in a throwaway database and record the results here, including SC-005 (dot rows against `GET /calls`) and SC-007 (`GET /calls` unchanged).

  **Results (2026-11-16)**:
  - `uv run test`: 64 passed (53 before this feature), as rebuilt on 2026-11-20. The comparison line (FR-017) is checked by `test_progress_demo_48`, not by a second database run.
  - PostgreSQL 18 run in the throwaway database `stepping_stones_verify_006` (dropped afterwards; the main database was not touched), with `DEMO_TODAY=2026-10-09T23:59:59+00:00`:
    - SC-001: weekly 16/25 = 64, 16/23 = 70, 17/25 = 68, 24/32 = 75, 45/56 = 80, 31/39 = 79, 19/22 = 86, 53/59 = 90; only the last week is current.
    - SC-002: Check balance 88, Get branch hours 86, Order checks 85, Reset password 80, Pay bill 79, Schedule appointment 77, Replace card 73, Transfer money 69.
    - SC-003: 26 rows, 13 with misses, in the order of spec US3/AC2, with the expected results and summary lines.
    - SC-004: `this_week` (53 of 59, 90) and `first_week_percent` (64) equal `GET /calls?weeks=8`. `demo_data` is true.
    - SC-005: all 7 Replace card and Transfer money rows equal the step statuses of that call type's last 5 calls in `GET /calls`.
    - SC-007: `GET /calls?limit=100&weeks=8` is byte-identical to the body recorded before this feature.
    - Unknown agent: 200 with 8 empty weeks and nothing else. `agent_id=x`: 422. `RULES_DIR=/nonexistent`: `GET /progress` 503 with the missing-file message, `GET /calls` 200.

## Dependencies & Execution Order

1. T001 (domain) comes first.
2. T002 depends on T001.
3. T003 and T004 depend on T001 and T002 and can run in parallel with each other.
4. T005 depends on T002, T003 and T004.
5. T006 depends on all of the above.

## Implementation Strategy

1. Implement T001→T006 in order. `uv run test` must be green before the next task.
2. Stop when the independent test above passes.
3. The Progress screen is feature 007, with its own spec, plan and tasks.

## Notes

- 6 tasks, one use case. Hard ceiling reached; convergence findings must be folded into an existing task.
- No schema change, so no migration. No new dependency.
- Do not commit until asked.
- **Test cut (2026-11-19)**: at the product owner's request the tests were cut to `test_progress_demo_48`, `test_progress_503_without_rules` and the shared layer guard. `test_progress_small_dataset` was added back on 2026-11-20, so FR-012 and SC-006 are met. Principle VI remains a recorded deviation (plan.md Complexity Tracking).
