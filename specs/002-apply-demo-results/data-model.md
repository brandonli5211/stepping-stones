# Data Model: Apply Demo Results

**Primary use case**: `ApplyDemoResults`

**No schema change**: the feature updates existing columns of `calls` and `call_steps`. No Alembic migration is needed.

## Domain types (`backend/app/domain/demo_results.py`)

These are pure frozen dataclasses. They import nothing outside the standard library.

| Type | Fields | Rules |
| --- | --- | --- |
| `SeverityBand` | `name: str`, `min_lost: int`, `max_lost: int \| None` | Built from `_common.json` → `severity.bands`. `None` means no upper bound. |
| `ResultsRow` | `demo_id`, `external_id`, `call_type`, `date`, `time` (all `str`), `missed: frozenset[str]`, `wrong: frozenset[str]` | One CSV row. Keys come from `parse_step_keys`. |
| `StoredStep` | `key: str`, `name: str`, `points: int`, `status: str`, `detail: str \| None` | One existing `call_steps` row. |
| `StoredCall` | `external_id: str`, `call_type: str`, `steps: tuple[StoredStep, ...]` | One existing call, with steps in procedure order. |
| `ScoredStep` | `key`, `status` (`completed`/`missed`/`wrong`), `severity`, `points_lost`, `detail` | The new values for one step. `points_under_review` is always 0. |
| `ScoredCall` | `external_id`, `started_at` (aware, UTC), `score`, `points_lost`, `steps_total`, `steps_completed`, `steps_missed`, `steps_wrong`, `steps: tuple[ScoredStep, ...]` | The new values for one call. `status = scored`, `steps_under_review = 0`. |

## Domain functions (pure, each unit-tested)

| Function | Input → output | Rule (spec ref) |
| --- | --- | --- |
| `parse_step_keys(cell)` | `str \| None` → `frozenset[str]` | Splits on `;`, trims, drops empty items (edge case). |
| `toronto_start(date, time)` | `str, str` → UTC `datetime` | Reads the date and time as America/Toronto local time. A malformed value raises `ValueError` (FR-003). |
| `severity_for(bands, lost)` | bands, `int` → `str` | `lost ≤ 0` gives `none`. Otherwise the first band with `min ≤ lost ≤ max`, where a `None` max is open. Above all bands gives the last band (FR-006). It returns the same result as `call_parse._band`. |
| `row_problems(row, stored)` | `ResultsRow, StoredCall \| None` → `list[str]` | Each problem is prefixed with the `demo_id`, in this order:<br>- `call not loaded` (when stored is None, this is the only problem)<br>- `call has no rubric steps (load with --demo-results)` (when `stored.steps` is empty; no unknown-key check follows)<br>- `call_type X, loaded call is Y`<br>- `unknown step K` (one per key not in the call's stored steps, sorted)<br>- `step K is both missed and wrong` (sorted)<br>- `bad date/time D T`<br>Returns `[]` when the row is valid (FR-008). |
| `duplicate_problems(rows)` | `Sequence[ResultsRow]` → `list[str]` | For every row after the first one with the same `external_id`: `"<demo_id>: call <external_id> listed more than once"`, in file order (FR-008). |
| `score_call(row, stored, bands)` | → `ScoredCall` | Requires a valid row. Status follows FR-004. Lost is the step's full points or 0 (FR-005). Detail is kept only if the status is unchanged. Totals, score `max(0, 100 − lost)` and counts follow FR-007. |

### Worked example (SC-002)

| Input | Value |
| --- | --- |
| Row | `HVB-DEMO-06` |
| Call | `a2f086d27b3a4f96`, type `transfer_money` |
| Local start | 2026-10-07 16:48 |
| Wrong steps | `submit_and_confirm_transfer` (55 points) |

| Output | Value |
| --- | --- |
| `started_at` | 2026-10-07T20:48:00Z |
| Wrong step | 55 points lost, severity `critical` |
| Other 6 steps | `completed`, 0 points lost, severity `none` |
| Call | score 45, points_lost 55, total 7, completed 6, missed 0, wrong 1 |

## Application types (`backend/app/application/apply_demo_results.py`, `ports.py`)

| Type | Shape |
| --- | --- |
| `DemoCallStore` (port, in `ports.py`) | `async find_calls(external_ids: Collection[str]) -> Mapping[str, StoredCall]` and `async save_results(calls: Sequence[ScoredCall]) -> None`. Save writes within the caller's unit of work; the command commits or rolls back (research R3). |
| `ApplyOutcome` | `updated: int`, `problems: tuple[str, ...]`, `saved: bool` |
| `ApplyDemoResults` | `store: DemoCallStore`, `bands: tuple[SeverityBand, ...]`. `async execute(rows) -> ApplyOutcome`. |

## Persistence mapping (adapter only)

| Domain | Table.column |
| --- | --- |
| `StoredCall.external_id`, `call_type` | `calls.external_id`, `calls.call_type` |
| `StoredStep.*` | `call_steps.step_key`, `name`, `points`, `status`, `detail` (ordered by `position`) |
| `ScoredCall.*` | `calls.started_at`, `score`, `points_lost`, `steps_total`, `steps_completed`, `steps_missed`, `steps_wrong`. Also sets `status='scored'`, `steps_under_review=0`. |
| `ScoredStep.*` | `call_steps.status`, `severity`, `points_lost`, `detail`. Also sets `points_under_review=0`. |

## State transitions

Each step moves from any status (`completed`/`missed`/`wrong`/`under_review`) to exactly one of `completed`/`missed`/`wrong`. Each call moves from any status to `scored`. Applying the same file a second time leaves the data the same.
