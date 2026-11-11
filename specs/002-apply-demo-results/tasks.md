---

description: "Task list for ApplyDemoResults (issue #33)"
---

# Tasks: Apply Demo Results

**Input**: Design documents from `/specs/002-apply-demo-results/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/apply-demo-results-command.md, quickstart.md, constitution.md (1.5.0)

**Tests**: cut on 2026-11-19 to two broad tests plus the shared layer guard, at the product owner's request. This does not meet constitution VI; the deviation is recorded in plan.md Complexity Tracking. The tests need no database. The real database is checked in T006 through quickstart.md.

**Organization**: ONE Clean Architecture use case, `ApplyDemoResults` (plan.md Summary), as a single vertical slice of 6 tasks. Spec stories US1 (apply the file) and US2 (a bad file changes nothing) are both served by this one slice.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: `[US1]` = the single use-case slice
- Paths are relative to the repository root

## Use Case: ApplyDemoResults (from plan.md Summary)

**Goal**: the presenter runs `uv run apply-demo-results ../sample/demo_48/results.csv`, which validates every row, rescores each listed call from the rubric, and saves all calls in one transaction or none.

**Independent Test**: run the steps below; quickstart.md steps 2–5 give the full commands.
1. `uv run test` is green.
2. After load and apply, call `a2f086d27b3a4f96` has:
   - score 45 and points_lost 55
   - 7 steps: 6 completed, 0 missed, 1 wrong
   - `submit_and_confirm_transfer` wrong, severity critical, 55 lost
   - a start time of 2026-10-07 16:48 Toronto
3. A file with an unknown key and a call_type mismatch exits 1, lists both problems, and changes nothing.

- [X] T001 [P] [US1] **Domain.** Create `backend/app/domain/demo_results.py` (standard library only) and `backend/tests/test_domain_demo_results.py`.
  - **Types**: frozen dataclasses `SeverityBand(name, min_lost, max_lost: int | None)`, `ResultsRow(demo_id, external_id, call_type, date, time, missed: frozenset[str], wrong: frozenset[str])`, `StoredStep(key, name, points, status, detail)`, `StoredCall(external_id, call_type, steps)`, `ScoredStep(key, status, severity, points_lost, detail)`, `ScoredCall(external_id, started_at, score, points_lost, steps_total, steps_completed, steps_missed, steps_wrong, steps)`.
  - **`parse_step_keys(cell)`**: "Splits on `;`, trims, drops empty items".
  - **`toronto_start(date, time)`**: "Reads the date and time as America/Toronto local time. A malformed value raises `ValueError`". It returns an aware UTC datetime via `zoneinfo`.
  - **`severity_for(bands, lost)`**: "`lost ≤ 0` gives `none`. Otherwise the first band with `min ≤ lost ≤ max`, where a `None` max is open. Above all bands gives the last band".
  - **`row_problems(row, stored)`**: returns problems prefixed `"<demo_id>: "`, in this order:
    1. `call not loaded` (and nothing else when stored is None);
    2. `call has no rubric steps (load with --demo-results)` (when `stored.steps` is empty; no unknown-key check follows);
    3. `call_type <csv>, loaded call is <stored>`;
    4. `unknown step <key>` (one per key not in the call's stored steps, sorted);
    5. `step <key> is both missed and wrong` (sorted);
    6. `bad date/time <date> <time>`.
  - **`duplicate_problems(rows)`**: for every row after the first one with the same `external_id`, returns `"<demo_id>: call <external_id> listed more than once"`, in file order.
  - **`score_call(row, stored, bands)`**: missed if in `missed`, wrong if in `wrong`, else completed. A missed or wrong step loses its full `points`, otherwise 0. Severity comes from `severity_for`. `detail` is kept only if the status is unchanged, else `None`. Score is `max(0, 100 - lost)`. Counts come from the steps.
  - **Tests** (`backend/tests/test_domain_demo_results.py`): `test_severity_matches_seed`: `severity_for` equals `app.call_parse._band(common, n)` for n in 0..100, with bands read from the real `docs/procedures/schema3/_common.json`. The module is also covered by the shared layer guard `backend/tests/test_layering.py` (`test_no_framework_imports`, every domain and application module).

- [X] T002 [US1] **Application.** Add the `DemoCallStore` Protocol to `backend/app/application/ports.py` with `async find_calls(external_ids: Collection[str]) -> Mapping[str, StoredCall]` and `async save_results(calls: Sequence[ScoredCall]) -> None` (all or nothing). Create `backend/app/application/apply_demo_results.py` with:
  - frozen `ApplyOutcome(updated: int, problems: tuple[str, ...], saved: bool)`;
  - frozen `ApplyDemoResults(store: DemoCallStore, bands: tuple[SeverityBand, ...])`;
  - `async execute(rows: Sequence[ResultsRow]) -> ApplyOutcome`, which:
    1. calls `find_calls` once with all distinct external ids;
    2. collects `duplicate_problems(rows)` plus `row_problems` for every row;
    3. if there are any problems, returns `ApplyOutcome(0, problems, False)` **without calling `save_results`**;
    4. otherwise calls `save_results([score_call(...) for each row])` once and returns `ApplyOutcome(len(rows), (), True)`.

  The module imports only the domain and ports. Add `backend/tests/test_apply_demo_results.py` with a fake store and one parametrized test, `test_bad_file_saves_nothing`: a missing call, a call with no stored steps, a duplicated call, an unknown key, a both-listed key, a call_type mismatch and a bad date each give `saved=False` with the expected message, and save is never called, not even for the valid row in the same file.

- [X] T003 [US1] **File adapter.** Create `backend/app/adapters/files/__init__.py` and `backend/app/adapters/files/demo_results_files.py` with:
  - **`read_results_csv(path) -> list[ResultsRow]`**: uses `csv.DictReader` with UTF-8. The required columns are `demo_id, hvb_call_id, call_type, date, time, missed_steps, wrong_steps`, and a missing one raises `ValueError` naming it. Extra columns are ignored. Keys go through `parse_step_keys`.
  - **`read_severity_bands(rules_dir) -> tuple[SeverityBand, ...]`**: reads `_common.json` → `severity.bands`.

  No unit test (2026-11-19 test cut). Feature 003's `test_demo_48_numbers` reads the real CSV and bands through these functions.

- [X] T004 [US1] **Persistence adapter.** Create `backend/app/adapters/persistence/demo_call_store.py` with `SqlAlchemyDemoCallStore(session: AsyncSession)`, which implements `DemoCallStore` using the existing mapped `Call` and `CallStep` from `app.models` (import only; do not edit `app/models.py`).
  - **`find_calls`**: selects the calls by `external_id` with their steps ordered by `position` and maps them to `StoredCall`/`StoredStep`.
  - **`save_results`**: issues the updates within the caller's transaction. It MUST NOT call `begin()`, `commit()` or `rollback()`; the command owns the unit of work (research R3). It updates:
    - `calls`: `started_at, status='scored', score, points_lost, steps_total, steps_completed, steps_missed, steps_wrong, steps_under_review=0`;
    - each `call_steps` row: `status, severity, points_lost, points_under_review=0, detail`, keyed by `(call_id, step_key)`.

  It touches no other columns. No unit test (2026-11-19 test cut); checked only by the real database run in T006.

- [X] T005 [US1] **Outer command.** Create `backend/app/infrastructure/apply_demo_results.py` with `main(argv: Sequence[str] | None = None) -> int`.
  - **Arguments**: `results_csv`, and `--rules-dir` defaulting to `<repo>/docs/procedures/schema3`.
  - **Steps**:
    1. read the rows and bands through the T003 adapters;
    2. open a session from `app.adapters.persistence.engine`;
    3. run `apply_with_session(session, rows, bands)` with `asyncio.run`;
    4. print `{'updated': n, 'problems': [...], 'saved': bool}`.
  - **`async apply_with_session(session, rows, bands) -> ApplyOutcome`**: inside one `async with session.begin():`, build `ApplyDemoResults(SqlAlchemyDemoCallStore(session), bands)` and run `execute(rows)`. This is the single unit of work: it commits on success and rolls back on any exception.
  - **Exit code**: return 0 if saved, else 1. A file or column error prints the message and returns 1.
  - **Seam**: an optional `run_use_case` parameter, an async callable taking `(rows, bands)`, so the command can run without a database.
  - Add an `if __name__ == "__main__"` guard: `raise SystemExit(main())`.
  - Add `apply-demo-results = "app.infrastructure.apply_demo_results:main"` to `[project.scripts]` in `backend/pyproject.toml`.
  - No unit test (2026-11-19 test cut); checked only by the real database run in T006.
  - **Convergence 1**: the default database runner `_apply_with_database(rows, bands, session_source=get_session)` MUST get its session from `app.adapters.persistence.engine.get_session`, the async generator that yields one session and then disposes the engine. Do not build `async_sessionmaker` by hand.

- [X] T006 [US1] **Validate and clean up.**
  1. Confirm `backend/app/apply_results.py` does not exist, and that `backend/app/calls_api.py`, `backend/app/call_parse.py`, `backend/app/load_calls.py` and `backend/app/models.py` are unchanged against `origin/feat/get_calls`.
  2. Confirm that `sample/demo_48` is identical to `feat/load-demo-48` and that `sample/calls_sample_56` is still present.
  3. Run `uv run test` from `backend/`.
  4. Against local Postgres, run [quickstart.md](quickstart.md) steps 2–5:
     - load, then apply, gives `updated: 48`;
     - the SC-002 SQL gives score 45, the step values and 16:48 Toronto;
     - a bad scratch CSV exits 1 with both problems and an unchanged snapshot;
     - a second apply gives the same values.
  5. Record any mismatch instead of changing the expected numbers.

**Checkpoint**: `ApplyDemoResults` works through the domain → application/port → adapters → command layers. The domain and application import no FastAPI, SQLAlchemy, Alembic or psycopg. Not every new function has a unit test (see plan.md Complexity Tracking).

---

## Dependencies & Execution Order

1. T001 (domain) comes first. T003 imports the domain types, so it follows T001.
2. T002 (use case and port) depends on T001.
3. T004 (persistence adapter) depends on T001 and T002.
4. T005 (command) depends on T002, T003 and T004.
5. T006 depends on all of the above.

## Implementation Strategy

1. Implement T001→T006 in order. `uv run test` must be green before the next task.
2. Stop when the independent test above passes.
3. ListCalls (demo clock, week window, percent, label) is a separate feature with its own spec, plan and tasks. It is not added here.

## Notes

- 6 tasks, one use case. Hard ceiling respected.
- No schema change, so no migration.
- No new dependencies.
- Do not commit unless asked.
- **Convergence pass 1 (2026-11-11)**: converge found that `_apply_with_database` should take its session from `engine.get_session`. Appending it as T007 would break the 6-task ceiling, so it was folded into T005, which was reopened. See the T005 "Convergence 1" bullet.
- **Test cut (2026-11-19)**: at the product owner's request the tests were cut to `test_bad_file_saves_nothing`, `test_severity_matches_seed` and the shared layer guard. This is a recorded deviation from constitution VI (plan.md Complexity Tracking).
