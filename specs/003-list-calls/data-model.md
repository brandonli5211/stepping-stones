# Data Model: List Calls with a Demo Clock

**Primary use case**: `ListCalls`

**No schema change**: the feature reads the existing `calls`, `call_steps` and `procedures` tables. No migration is needed.

## Domain types (`backend/app/domain/call_list.py`, standard library only)

| Type | Fields | Notes |
| --- | --- | --- |
| `StepOutcome` | `key`, `name`, `status` | Statuses: completed / missed / wrong / under_review. |
| `CallResult` | `label`, `status` | Built only by `result_for`. |
| `CallRecord` | `id`, `external_id`, `call_type`, `call_type_name`, `started_at`, `status`, `score`, `steps_completed`, `steps_total`, `steps: tuple[StepOutcome, ...]` | One call as read. `score` may be None. |
| `CallSummary` | `record: CallRecord`, `result: CallResult \| None` | One listed call. The presenter flattens it into the call fields + `result`. |
| `CallWindow` | `since: datetime \| None`, `agent_id: int \| None` | Applies to the list and the header (FR-004). |
| `ListFilter` | `call_type: str \| None`, `has_missed: bool` | Applies to the list only. `call_type` is already normalized. |
| `WeekTotals` | `week: date`, `done: int`, `total: int` | One Monday-start week. |
| `WeekNumbers` | `steps_completed`, `steps_total`, `percent` | This week's numbers in the header. |
| `ListHeader` | `calls_reviewed`, `weeks`, `this_week: WeekNumbers \| None`, `first_week_percent: int \| None` | The header (FR-005). |
| `CallList` | `summary: ListHeader`, `calls: tuple[CallSummary, ...]` | The use case output. |

## Domain functions (pure, each unit-tested)

| Function | Rule | Spec |
| --- | --- | --- |
| `normalize_call_type(text)` | `"_".join(text.strip().lower().split())`, the same as the current `snake` | FR-004 |
| `result_for(steps)` | The first `missed`/`wrong` step in order gives `Missed <name>` or `Wrong: <name>`; otherwise `None` | FR-003 |
| `percent(done, total)` | `round(100 * done / total)`, or `None` if `total` is 0 | FR-007 |
| `window_for(reference, weeks, agent_id)` | `CallWindow(reference - weeks if weeks else None, agent_id or None)` | FR-004, FR-008 |
| `week_monday(reference)` | The UTC Monday date of the reference instant | FR-006 |
| `this_week(weeks, reference)` | The `WeekTotals` whose week is `week_monday(reference)` turned into `WeekNumbers` (int sums, `percent`), or `None` | FR-005 |
| `first_week_percent(weeks)` | `percent` of the first week row, or `None` | FR-005 |

## Application (`backend/app/application/list_calls.py`, `ports.py`)

| Type | Shape |
| --- | --- |
| `Clock` port | `now() -> datetime` (aware) |
| `CallListReader` port | `async recent_calls(window, filters, limit) -> Sequence[CallRecord]`, `async count_calls(window) -> int`, `async week_totals(window) -> Sequence[WeekTotals]` |
| `ListCallsQuery` | `agent_id: int \| None`, `call_type: str \| None`, `has_missed: bool`, `limit: int`, `weeks: int \| None` |
| `ListCalls` | `reader`, `clock`. `async execute(query) -> CallList`. It reads the clock once, builds the window and filter, runs the three reads, and assembles the result with the domain functions. |

## Infrastructure (`backend/app/infrastructure/clock.py`)

| Item | Rule |
| --- | --- |
| `SystemClock.now()` | `datetime.now(timezone.utc)` |
| `FixedClock(instant).now()` | Returns `instant` |
| `parse_demo_today(value)` | ISO 8601 with an offset, converted to UTC. No offset, or unparseable, raises `ValueError` naming the value. |
| `clock_from_env(environ)` | `FixedClock(parse_demo_today(v))` if `DEMO_TODAY` is non-empty, else `SystemClock()` |

## Response mapping (`backend/app/adapters/http/calls.py`, `present_call_list`)

The shape is exactly as today: same keys, same order, same types.

```text
{"summary": {"calls_reviewed", "weeks", "this_week": null | {"steps_completed", "steps_total", "percent"}, "first_week_percent"},
 "calls": [{"id", "external_id", "call_type", "call_type_name", "started_at", "status", "score",
            "steps_completed", "steps_total", "steps": [{"key", "name", "status"}],
            "result": null | {"label", "status"}}]}
```
