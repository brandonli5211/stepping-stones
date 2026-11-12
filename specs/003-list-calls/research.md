# Research: List Calls with a Demo Clock

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

**Primary use case**: `ListCalls`

No Technical Context item was left as NEEDS CLARIFICATION. The two scope questions (what happens to `analyze_call`, and how the weekly percents are checked) were answered by the user before the spec was written.

## R1. How "now" reaches the use case

- **Decision**:
  - A `Clock` port (`now() -> datetime`, aware UTC) lives in `app/application/ports.py`.
  - `app/infrastructure/clock.py` provides `SystemClock`, `FixedClock(instant)` and `clock_from_env(environ) -> Clock`.
  - The composition root `app/main.py` defines `configure_clock(app, environ)`, which sets `app.state.clock = clock_from_env(environ)`. It calls `configure_clock(app, os.environ)` once at import. Tests call `configure_clock` directly instead of reloading the module (analyze finding T1).
  - The HTTP adapter reads `request.app.state.clock`; it never imports infrastructure.
- **Rationale**:
  - FR-008 and FR-009 require the variable to be read at the outer edge only.
  - Reading it at import makes a malformed value fail startup: uvicorn cannot import `app.main`, which satisfies story 1, scenario 4.
  - The use case stays deterministic in tests, because a fixed clock is injected.
- **Alternatives considered**:
  - Reading `os.environ` inside the handler on every request (the rejected PR): config sits in the router, and a malformed value fails every request with a 500 instead of failing at startup.
  - Passing `today` as a query parameter: changes the API (FR-010).

## R2. Parsing DEMO_TODAY

- **Decision**: `parse_demo_today(value)` uses `datetime.fromisoformat` and requires `tzinfo`, then converts to UTC. A value with no offset, or that cannot be parsed, raises `ValueError("DEMO_TODAY=<value> is not an ISO 8601 date-time with a UTC offset")`. An empty or unset value gives `SystemClock`.
- **Rationale**: an offset-less value is ambiguous (spec edge case). Converting to UTC means the Monday of "this week" is the UTC Monday (FR-006), even for a value such as `2026-10-09T19:59:59-04:00`. The rejected edit took the weekday in whatever offset was given.

## R3. Week rules stay identical

- **Decision**: these domain functions in `app/domain/call_list.py` reproduce today's expressions exactly:
  - **`window_start(reference, weeks)`**: `reference - timedelta(weeks=weeks)` when `weeks` is set, else `None`.
  - **`week_monday(reference)`**: `(reference_utc - timedelta(days=weekday)).date()`.
  - **`percent(done, total)`**: `round(100 * done / total)` when `total` is non-zero, else `None`. Python's `round` keeps round-half-to-even.
  - **`this_week(weeks, reference)`**: the row whose week is the Monday of the reference week.
  - **`first_week_percent(weeks)`**: the percent of the first row.

  The SQL grouping, now in the persistence adapter, becomes `date_trunc('week', started_at AT TIME ZONE 'UTC')`. That pins the grouping to UTC whatever time zone the database session uses, so FR-006 holds and the grouping always agrees with `week_monday`. On the local session, which is UTC, it produces the same groups and dates as today's `date_trunc('week', started_at)`, so SC-004 still holds. (Analyze finding U1.)
- **Rationale**: SC-004 requires identical responses. A query against the main database with the current grouping already returns 64, 70, 68, 75, 80, 79, 86, 90 and 53/59 for this week, so the logic only needs to move, not change.
- **Alternative considered**: grouping by Toronto week. It would change the numbers and the behavior, so it was rejected.

## R4. Result label

- **Decision**: `result_for(steps)` takes the first step, in step order, with status `missed` or `wrong`:
  - a missed step gives `CallResult(label=f"Missed {name}", status="missed")`, with no colon;
  - a wrong step gives `CallResult(label=f"Wrong: {name}", status="wrong")`, with a colon;
  - otherwise it returns `None`.
- **Rationale**: the user asked for exactly this wording, as it is today at `calls_api.py:169`.

## R5. Read port and adapter

- **Decision**: the port `CallListReader` (in `ports.py`) has three methods, mirroring today's three queries:
  - `recent_calls(window, filters, limit) -> list[CallRecord]`: calls joined to their procedure name, newest first then id descending; then each call's steps in position order.
  - `count_calls(window) -> int`
  - `week_totals(window) -> list[WeekTotals]`: Monday date, the sum of `steps_completed`, the sum of `steps_total`, ordered by week.

  `SqlAlchemyCallListReader` in `app/adapters/persistence/call_list_reader.py` builds the same SQLAlchemy statements as the current handler.
  - `CallWindow(since, agent_id)` gives the WHERE clauses shared by all three queries.
  - `ListFilter(call_type, has_missed)` adds the list-only clauses.
  - Truthiness is the same as today: `if agent_id`, `if weeks`, `if call_type`.
- **Rationale**: identical SQL is what makes the responses identical. The rules (labels, this week, percent) move to the domain, and only data access stays in the adapter.
- **Testing**:
  - A recording fake `AsyncSession` checks the parameters passed, and that the mapping from rows to domain records is right.
  - The compiled SQL is checked for the window, filter and order clauses.
  - The real database is covered by the quickstart.

## R6. HTTP adapter and presenter

- **Decision**: the new module `app/adapters/http/calls.py` holds the `GET /calls` router.
  - It is `async def` with the same query parameters and validation: `limit` 1–100 (default 10) and `weeks` 1–520.
  - It builds `ListCallsQuery`, calls `ListCalls.execute`, and returns `present_call_list(result)`.
  - `present_call_list` produces the same dict keys, order and value types as today, with `started_at` left as a datetime for FastAPI to serialize.
  - The dependency `get_list_calls(request, session)` builds `ListCalls(reader=SqlAlchemyCallListReader(session), clock=request.app.state.clock)`.
  - `main.py` includes the router.
- **Testing**: `httpx` is not installed, so there is no `TestClient`. The handler is tested by calling it directly with a fake use case, the way `test_health_route.py` does. The presenter gets its own test.

## R7. What happens to calls_api.py

- **Decision**: remove `list_calls`, `_percent`, `snake` (used only by `list_calls`) and the imports they alone used (`timedelta`, `datetime`, `timezone`, `func`, `Query`, `CallStep`). `analyze_call` and its helpers stay unchanged.
- **Rationale**: the user chose to split it this way. Feature C (AnalyzeCall) brings the rest of the file into compliance before the PR opens. Until then, the governance rule is satisfied by that plan; the gap is recorded in plan.md under Complexity Tracking.

## R8. Proving "unchanged" (SC-004)

- **Decision**: before any code changes, the first task records the current `GET /calls` responses as JSON in the scratchpad. It calls the existing handler in process, against the main database, without `DEMO_TODAY`, for the five parameter sets in SC-004 plus `agent_id=<first agent>`. After the change, the same requests through the new handler must give byte-identical JSON.
  It also starts the *current* API on port 8001 and saves the HTTP bodies of `GET /calls` and `GET /calls?weeks=8` with `curl`. After the change, the same two requests to the new API must return byte-identical bodies, which covers serialization as well (analyze finding C1).
- **Rationale**: this is the only direct proof of FR-010 and SC-004. It is read-only against the main database.
