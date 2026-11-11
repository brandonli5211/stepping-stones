---

description: "Task list for ListCalls (issue #33)"
---

# Tasks: List Calls with a Demo Clock

**Input**: Design documents from `/specs/003-list-calls/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/get-calls.md, quickstart.md, constitution.md (1.5.0)

**Tests**: cut on 2026-11-19 to two broad tests plus the shared layer guard, at the product owner's request. This does not meet constitution VI; the deviation is recorded in plan.md Complexity Tracking. The tests need no database. The real database and the API are checked in T006.

**Organization**: ONE Clean Architecture use case, `ListCalls` (plan.md Summary), as a single vertical slice of 6 tasks. Spec stories US1 (the demo clock) and US2 (normal use unchanged) are both served by this one slice.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: `[US1]` = the single use-case slice
- Paths are relative to the repository root

## Use Case: ListCalls (from plan.md Summary)

**Goal**: `GET /calls` is served by a thin async route, then the `ListCalls` use case, then the domain rules and the read port. The reference instant comes from a `Clock` built from `DEMO_TODAY` at startup.

**Independent Test**: [quickstart.md](quickstart.md) steps 1–5:
1. `uv run test` is green.
2. With `DEMO_TODAY=2026-10-09T23:59:59+00:00` and `weeks=8`, the response gives:
   - calls_reviewed 48;
   - this_week `{53, 59, 90}`;
   - first_week_percent 64;
   - `a2f086d27b3a4f96` labelled "Wrong: Submit and confirm transfer".
3. The SQL check gives the weekly percents 64, 70, 68, 75, 80, 79, 86, 90.
4. Without `DEMO_TODAY`, the JSON is byte-identical to the baseline from T001.
5. An offset-less `DEMO_TODAY` stops `app.main` from importing.

- [X] T001 [US1] **Baseline and domain.**
  - **Baseline first, before any code change** (research R8): with a one-off script in the session scratchpad, call the *current* `app.calls_api.list_calls` against the main database (`DATABASE_URL=…/stepping_stones`, no `DEMO_TODAY`). Pass an `AsyncSession` from `app.adapters.persistence.engine.get_session` and explicit keyword arguments for every parameter. Request these sets:
    - `{}`;
    - `weeks=8`;
    - `has_missed=True`;
    - `call_type="transfer_money"`;
    - `limit=100`;
    - `agent_id=<min agents.id>`.

    Save each response as JSON (`json.dumps(…, default=str, sort_keys=False)`) under the scratchpad's `baseline/` directory. Also start the current API with `uv run uvicorn app.main:app --port 8001` (no `DEMO_TODAY`), save the raw bodies of `GET /calls` and `GET /calls?weeks=8` with `curl` to `baseline/http_*.json`, then stop that server.
  - Then create `backend/app/domain/call_list.py` (standard library only) with:
    - **Frozen dataclasses**: `StepOutcome(key, name, status)`, `CallResult(label, status)`, `CallRecord(id, external_id, call_type, call_type_name, started_at, status, score, steps_completed, steps_total, steps)`, `CallSummary` (the `CallRecord` fields + `result`), `CallWindow(since, agent_id)`, `ListFilter(call_type, has_missed)`, `WeekTotals(week: date, done, total)`, `WeekNumbers(steps_completed, steps_total, percent)`, `ListHeader(calls_reviewed, weeks, this_week, first_week_percent)`, `CallList(summary, calls)`.
    - **`normalize_call_type(text)`**: `"_".join(str(text).strip().lower().split())`.
    - **`result_for(steps)`**: "The first `missed`/`wrong` step in order gives `Missed <name>` or `Wrong: <name>`; otherwise `None`". Use exactly `f"Missed {name}"` with no colon and `f"Wrong: {name}"`.
    - **`percent(done, total)`**: "`round(100 * done / total)`, or `None` if `total` is 0".
    - **`window_for(reference, weeks, agent_id)`**: `CallWindow(reference - timedelta(weeks=weeks) if weeks else None, agent_id or None)`.
    - **`week_monday(reference)`**: convert to UTC, then `(r - timedelta(days=r.weekday())).date()`.
    - **`this_week(weeks, reference)`**: the matching `WeekTotals` turned into `WeekNumbers(int(done), int(total), percent(done, total))`, else `None`.
    - **`first_week_percent(weeks)`**.
  - **Tests**: no unit test of its own (2026-11-19 test cut). `test_demo_48_numbers` (`backend/tests/test_demo_48.py`) runs these rules on the 48 demo calls, and the shared layer guard covers the module.

- [X] T002 [US1] **Application.**
  - Add to `backend/app/application/ports.py`:
    - `Clock` Protocol: `now() -> datetime`;
    - `CallListReader` Protocol: `async recent_calls(window: CallWindow, filters: ListFilter, limit: int) -> Sequence[CallRecord]`, `async count_calls(window: CallWindow) -> int`, `async week_totals(window: CallWindow) -> Sequence[WeekTotals]`.
  - Create `backend/app/application/list_calls.py` with frozen `ListCallsQuery(agent_id=None, call_type=None, has_missed=False, limit=10, weeks=None)` and frozen `ListCalls(reader, clock)`. Its `async execute(query) -> CallList`:
    1. read `clock.now()` **once**;
    2. `window_for(...)`;
    3. `ListFilter(normalize_call_type(call_type) if call_type else None, has_missed)`;
    4. `recent_calls`, `count_calls`, `week_totals`, in that order;
    5. build a `CallSummary` with `result_for` for each record;
    6. build `ListHeader(count, query.weeks, this_week(totals, now), first_week_percent(totals))`.
  - **Tests**: `test_demo_48_numbers` in `backend/tests/test_demo_48.py` (with the helper `backend/tests/demo_48_data.py`): the 48 demo calls are seeded as `load_calls --demo-results` would, scored by `ApplyDemoResults` from the real `results.csv`, and listed through `ListCalls` with an in-memory reader and `FixedClock(2026-10-09T23:59:59Z)`, `weeks=8`, `limit=100`. It asserts 48 calls reviewed, this week 53/59/90, first week 64, and `a2f086d27b3a4f96` labelled "Wrong: Submit and confirm transfer". `list_calls.py` and `ports.py` are covered by the shared layer guard.

- [X] T003 [US1] **Persistence adapter.** Create `backend/app/adapters/persistence/call_list_reader.py` with `SqlAlchemyCallListReader(session: AsyncSession)`, moving today's three queries from `calls_api.list_calls` unchanged in meaning:
  - **`window_clauses(window)`**: `[Call.started_at >= since]` if `since`, plus `[Call.agent_id == agent_id]` if `agent_id`.
  - **`recent_calls`**:
    - selects `Call.id, external_id, call_type, Procedure.name, started_at, status, score, steps_completed, steps_total`, joined to `Procedure`;
    - filters by the window clauses, plus `Call.call_type == filters.call_type` if set, plus `Call.steps_missed + Call.steps_wrong > 0` if `has_missed`;
    - orders by `started_at desc, id desc` and applies `.limit(limit)`;
    - then, only if there are rows, selects `CallStep.call_id, step_key, name, status` for those ids, ordered by `call_id, position`;
    - maps everything to `CallRecord`/`StepOutcome`.
  - **`count_calls`**: `select(func.count()).select_from(Call).where(*window)` via `session.scalar`.
  - **`week_totals`**: `func.date_trunc('week', Call.started_at.op("AT TIME ZONE")("UTC"))`, which groups by the UTC week whatever time zone the session uses (research R3), with the sums of `steps_completed` and `steps_total`, grouped and ordered by week, mapped to `WeekTotals(week.date(), int(done), int(total))`.
  - **Tests**: none (2026-11-19 test cut). Checked only by the real database run in T006.

- [X] T004 [US1] **Clock and composition.** Create `backend/app/infrastructure/clock.py` with:
  - `SystemClock.now()`: `datetime.now(timezone.utc)`;
  - `FixedClock(instant).now()`;
  - `parse_demo_today(value)`: ISO 8601 via `datetime.fromisoformat`; it requires `tzinfo` and returns the value in UTC. Otherwise it raises `ValueError(f"DEMO_TODAY={value} is not an ISO 8601 date-time with a UTC offset")`;
  - `clock_from_env(environ)`: `FixedClock(parse_demo_today(v))` when `environ.get("DEMO_TODAY")` is non-empty after stripping, else `SystemClock()`.

  Edit `backend/app/main.py`: add `configure_clock(app: FastAPI, environ: Mapping[str, str]) -> None`, which sets `app.state.clock = clock_from_env(environ)`, and call `configure_clock(app, os.environ)` at import. This is the only place `DEMO_TODAY` is read.

  **Tests**: `test_calls_body_without_demo_today` checks that `clock_from_env` gives `SystemClock` when `DEMO_TODAY` is unset or blank. Parsing and `configure_clock` have no unit test (2026-11-19 test cut); T006 checks a bad value stops `import app.main`.

- [X] T005 [US1] **HTTP adapter and calls_api.py cleanup.**
  - Create `backend/app/adapters/http/calls.py` with `router = APIRouter()` and:
    - **`present_call_list(result) -> dict`**: produces exactly today's keys, order and types (see data-model.md, Response mapping). `started_at` stays a datetime; `steps` is a list of `{"key","name","status"}`; `result` is `None` or `{"label","status"}`.
    - **`async get_list_calls(request: Request, session = Depends(get_session)) -> ListCalls`**: builds `ListCalls(reader=SqlAlchemyCallListReader(session), clock=request.app.state.clock)`.
    - **`@router.get("/calls") async def list_calls(agent_id: int | None = None, call_type: str | None = None, has_missed: bool = False, limit: int = Query(10, ge=1, le=100), weeks: int | None = Query(None, ge=1, le=520), use_case: ListCalls = Depends(get_list_calls)) -> dict`**: builds `ListCallsQuery`, awaits `execute`, and returns `present_call_list`. It holds no SQL and no rules.
  - In `backend/app/calls_api.py`, remove `list_calls`, `_percent`, `snake` and the imports only they used (`datetime`, `timedelta`, `timezone`, `func`, `Query`, `CallStep`). `analyze_call`, `build_prompt`, `ask_ollama`, `load_common` and `AnalyzeRequest` stay byte-for-byte unchanged.
  - In `backend/app/main.py`, include `app.adapters.http.calls.router`.
  - **Tests** in `backend/tests/test_calls_route.py`: `test_calls_body_without_demo_today`: `present_call_list` on a sample `CallList` equals the exact expected dict, including key order (`list(d)`, `list(d["summary"])` and `list(d["calls"][0])`). The handler and `get_list_calls` have no unit test (2026-11-19 test cut).

- [X] T006 [US1] **Validate.**
  1. `uv run test` is green.
  2. Against the main database (demo_48 loaded and applied), run [quickstart.md](quickstart.md) steps 2–5:
     - **Demo clock:** `DEMO_TODAY=2026-10-09T23:59:59+00:00 uv run serve` and `GET /calls?weeks=8&limit=100` give `calls_reviewed` 48, `this_week` 53/59/90, `first_week_percent` 64, and `a2f086d27b3a4f96` with label "Wrong: Submit and confirm transfer".
     - **Weekly percents:** the SQL query gives 64, 70, 68, 75, 80, 79, 86, 90.
     - **Unchanged without the demo clock:** run the same six T001 request sets through the new handler and compare them byte for byte with the baseline JSON. Also start the new API on port 8001 and compare the `GET /calls` and `GET /calls?weeks=8` bodies byte for byte with `baseline/http_*.json`.
     - **Bad value:** an offset-less `DEMO_TODAY` stops `import app.main`.
  3. Confirm that `git diff` for `calls_api.py` only removes code, and that `analyze_call` is unchanged.
  4. Record any mismatch rather than changing the expected numbers.

**Checkpoint**: `ListCalls` works through the domain, application and port, adapter, and composition layers. The `GET /calls` handler only delegates. `DEMO_TODAY` is read only in `main.py`. Not every new or changed function has a unit test (see plan.md Complexity Tracking).

---

## Dependencies & Execution Order

1. T001: baseline first, then the domain.
2. T002 depends on T001.
3. T003 depends on T001 and T002.
4. T004 depends on T002 (the `Clock` port). It can be written alongside T003, but it edits `main.py`, which T005 also edits, so finish T004 before T005.
5. T005 depends on T002, T003 and T004.
6. T006 depends on all of the above.

## Implementation Strategy

1. Implement T001→T006 in order. `uv run test` must be green after each.
2. Stop when the independent test passes.
3. AnalyzeCall (`POST /calls/{call_id}`) is Feature C, with its own spec, plan and tasks.

## Notes

- 6 tasks, one use case. Hard ceiling respected.
- No schema change. No new dependencies.
- Do not commit unless asked.
- **Test cut (2026-11-19)**: at the product owner's request the tests were cut to `test_demo_48_numbers`, `test_calls_body_without_demo_today` and the shared layer guard. This is a recorded deviation from constitution VI (plan.md Complexity Tracking).
