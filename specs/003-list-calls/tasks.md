---

description: "Task list for ListCalls (issue #33)"
---

# Tasks: List Calls with a Demo Clock

**Input**: Design documents from `/specs/003-list-calls/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/get-calls.md, quickstart.md, constitution.md (1.5.0)

**Tests**: Required by constitution VI and by spec FR-011 and SC-005. Each task ships unit tests for the functions it adds or changes, and each test calls the function and asserts its result or its specified failure. The tests need no database. The real database and the API are checked in T006.

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
  - **Tests** in `backend/tests/test_domain_call_list.py`:
    - each label case (missed first, wrong first, a later problem after an earlier completed step, under_review ignored, no problem gives `None`);
    - percent rounding: 53/59 is 90, 16/23 is 70, 0/0 is `None`, and half to even (1/8 is 12, 3/8 is 38);
    - the window with and without weeks, and `agent_id` 0 or `None` giving no filter;
    - the Monday for a Sunday 23:59:59Z, for a Monday 00:00Z, and for `2026-10-09T19:59:59-04:00` (Monday 2026-10-05);
    - this week found and missing; first week empty and non-empty;
    - `normalize_call_type(" Transfer  Money ")` gives `transfer_money`;
    - an import guard (no `fastapi`, `sqlalchemy`, `alembic`, `psycopg`, `os`, `app`).

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
  - **Tests** in `backend/tests/test_list_calls.py`, with a fake reader that records its arguments and a fixed clock:
    - the window uses the clock's instant: with weeks=8 and the clock at 2026-10-09T23:59:59Z, `since` is 2026-08-14T23:59:59Z;
    - `call_type` is normalized, and an empty one gives `None`;
    - the header comes out as 53/59/90 and first week 64 from fake week totals;
    - labels are attached in record order;
    - the clock is called exactly once;
    - an import guard for `list_calls.py` and `ports.py`: no `fastapi`, `sqlalchemy`, `alembic`, `psycopg` or `os`, and nothing from `app.adapters` or `app.infrastructure`.

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
  - **Tests** in `backend/tests/test_call_list_reader.py`, with a fake `AsyncSession` that returns canned rows and records statements:
    - row-to-record mapping, with steps grouped and ordered;
    - no step query when there are no calls;
    - the compiled SQL (postgresql dialect) holds the window, `call_type`, `has_missed`, order and limit clauses for each combination;
    - `count_calls` uses the window only;
    - `week_totals` maps datetimes to dates and sums to ints;
    - its compiled SQL groups on `date_trunc('week', calls.started_at AT TIME ZONE 'UTC')`, via a bound parameter.

- [X] T004 [US1] **Clock and composition.** Create `backend/app/infrastructure/clock.py` with:
  - `SystemClock.now()`: `datetime.now(timezone.utc)`;
  - `FixedClock(instant).now()`;
  - `parse_demo_today(value)`: ISO 8601 via `datetime.fromisoformat`; it requires `tzinfo` and returns the value in UTC. Otherwise it raises `ValueError(f"DEMO_TODAY={value} is not an ISO 8601 date-time with a UTC offset")`;
  - `clock_from_env(environ)`: `FixedClock(parse_demo_today(v))` when `environ.get("DEMO_TODAY")` is non-empty after stripping, else `SystemClock()`.

  Edit `backend/app/main.py`: add `configure_clock(app: FastAPI, environ: Mapping[str, str]) -> None`, which sets `app.state.clock = clock_from_env(environ)`, and call `configure_clock(app, os.environ)` at import. This is the only place `DEMO_TODAY` is read.

  **Tests** in `backend/tests/test_clock.py`:
  - each parse case: `+00:00`, `Z`, and `-04:00` converted to UTC; offset-less, garbage and empty-string inputs raise with the value named;
  - both clocks;
  - `clock_from_env` for unset, blank and set values;
  - `configure_clock` on a fresh `FastAPI()`, with no module reload: `SystemClock` without the variable, `FixedClock` at the instant with it, and `ValueError` with a bad value;
  - `app.main.app.state.clock` exists after a normal import;
  - one subprocess test: `python -c "import app.main"` with an offset-less `DEMO_TODAY` exits non-zero and prints the value.

- [X] T005 [US1] **HTTP adapter and calls_api.py cleanup.**
  - Create `backend/app/adapters/http/calls.py` with `router = APIRouter()` and:
    - **`present_call_list(result) -> dict`**: produces exactly today's keys, order and types (see data-model.md, Response mapping). `started_at` stays a datetime; `steps` is a list of `{"key","name","status"}`; `result` is `None` or `{"label","status"}`.
    - **`async get_list_calls(request: Request, session = Depends(get_session)) -> ListCalls`**: builds `ListCalls(reader=SqlAlchemyCallListReader(session), clock=request.app.state.clock)`.
    - **`@router.get("/calls") async def list_calls(agent_id: int | None = None, call_type: str | None = None, has_missed: bool = False, limit: int = Query(10, ge=1, le=100), weeks: int | None = Query(None, ge=1, le=520), use_case: ListCalls = Depends(get_list_calls)) -> dict`**: builds `ListCallsQuery`, awaits `execute`, and returns `present_call_list`. It holds no SQL and no rules.
  - In `backend/app/calls_api.py`, remove `list_calls`, `_percent`, `snake` and the imports only they used (`datetime`, `timedelta`, `timezone`, `func`, `Query`, `CallStep`). `analyze_call`, `build_prompt`, `ask_ollama`, `load_common` and `AnalyzeRequest` stay byte-for-byte unchanged.
  - In `backend/app/main.py`, include `app.adapters.http.calls.router`.
  - **Tests** in `backend/tests/test_calls_route.py`:
    - `present_call_list` on a sample `CallList` equals the exact expected dict, including key order (compare `list(d)` and `list(d["calls"][0])`);
    - the handler passes every parameter into `ListCallsQuery` and returns the presented dict, using a fake use case;
    - the handler source holds no `select`, `execute(` or `os.environ`;
    - `get_list_calls` wires the reader and the clock from a fake request with `app.state.clock`;
    - `app.main.app` has exactly one `GET /calls` route and still has `POST /calls/{call_id}`.

- [X] T006 [US1] **Validate.**
  1. `uv run test` is green.
  2. Against the main database (demo_48 loaded and applied), run [quickstart.md](quickstart.md) steps 2–5:
     - **Demo clock:** `DEMO_TODAY=2026-10-09T23:59:59+00:00 uv run serve` and `GET /calls?weeks=8&limit=100` give `calls_reviewed` 48, `this_week` 53/59/90, `first_week_percent` 64, and `a2f086d27b3a4f96` with label "Wrong: Submit and confirm transfer".
     - **Weekly percents:** the SQL query gives 64, 70, 68, 75, 80, 79, 86, 90.
     - **Unchanged without the demo clock:** run the same six T001 request sets through the new handler and compare them byte for byte with the baseline JSON. Also start the new API on port 8001 and compare the `GET /calls` and `GET /calls?weeks=8` bodies byte for byte with `baseline/http_*.json`.
     - **Bad value:** an offset-less `DEMO_TODAY` stops `import app.main`.
  3. Confirm that `git diff` for `calls_api.py` only removes code, and that `analyze_call` is unchanged.
  4. Record any mismatch rather than changing the expected numbers.

**Checkpoint**: `ListCalls` works through the domain, application and port, adapter, and composition layers. The `GET /calls` handler only delegates. `DEMO_TODAY` is read only in `main.py`. Every new or changed function has a calling unit test.

---

## Dependencies & Execution Order

1. T001: baseline first, then the domain.
2. T002 depends on T001.
3. T003 depends on T001 and T002.
4. T004 depends on T002 (the `Clock` port). It can be written alongside T003, but it edits `main.py`, which T005 also edits, so finish T004 before T005.
5. T005 depends on T002, T003 and T004.
6. T006 depends on all of the above.

## Implementation Strategy

1. Implement T001→T006 in order. Each task includes its own tests, and `uv run test` must be green after each.
2. Stop when the independent test passes.
3. AnalyzeCall (`POST /calls/{call_id}`) is Feature C, with its own spec, plan and tasks.

## Notes

- 6 tasks, one use case. Hard ceiling respected.
- No schema change. No new dependencies.
- Do not commit unless asked.
