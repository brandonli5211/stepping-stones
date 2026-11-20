# Data Model: Get Progress

No table changes. Types are frozen dataclasses unless noted.

## Domain: `app/domain/progress.py`

Standard library plus `app.domain.call_list` (`WeekTotals`, `WeekNumbers`, `week_monday`, `percent`).

### Constants

| Name | Value |
| --- | --- |
| `WEEKS` | `8` |
| `TYPE_WINDOW` | `5` (a step of one call type) |
| `SHARED_WINDOW` | `10` (a step shared by all call types) |
| `RESOLVED` | `("completed", "missed", "wrong")` |
| `MISSES` | `("missed", "wrong")` |

### Types

| Type | Fields |
| --- | --- |
| `ProgressWindow` | `since: datetime`, `until: datetime` (exclusive), `agent_id: int \| None` |
| `ProgressWeek` | `week_start: date` (the Monday), `steps_completed: int`, `steps_total: int`, `percent: int \| None`, `is_current: bool` |
| `CallTypeTotals` | `call_type: str`, `name: str`, `done: int`, `total: int`, `calls: int` (what the data access returns) |
| `CallTypeProgress` | `call_type: str`, `name: str`, `steps_completed: int`, `steps_total: int`, `percent: int \| None`, `calls: int` |
| `StepResult` | `call_id: int`, `started_at: datetime`, `call_type: str`, `call_type_name: str`, `step_key: str`, `step_name: str`, `position: int`, `status: str` |
| `StepRow` | `step_key: str`, `step_name: str`, `call_type: str \| None`, `call_type_name: str \| None` (both `None` for a shared step), `results: tuple[str, ...]` (oldest first), `misses: int`, `window: int` (= `len(results)`) |

### Functions

| Function | Rule |
| --- | --- |
| `progress_window(now, agent_id) -> ProgressWindow` | `monday = week_monday(now)`. `since` = 00:00 UTC on `monday − 7 weeks`. `until` = 00:00 UTC on `monday + 1 week`. `agent_id or None`. |
| `eight_weeks(totals: Sequence[WeekTotals], now) -> tuple[ProgressWeek, ...]` | Exactly 8 weeks, oldest first, for the Mondays `monday − 7 weeks … monday`. A week with no totals has 0, 0 and `percent None`. `percent` comes from `call_list.percent`. Only the last is `is_current`. Totals for other weeks are ignored. |
| `call_type_progress(totals: Sequence[CallTypeTotals]) -> tuple[CallTypeProgress, ...]` | One per input, with `percent(done, total)`. Ordered by percent, highest first, with `None` last; ties by `name`. |
| `step_rows(results: Sequence[StepResult], shared_keys: Collection[str]) -> tuple[StepRow, ...]` | See below. |

**`step_rows`**:

1. Keep results whose status is in `RESOLVED`. Order them by `(started_at, call_id)`.
2. Group them: a result whose `step_key` is in `shared_keys` goes to the group `(None, step_key)`. Any other goes to `(call_type, step_key)`.
3. For each group, keep the last `SHARED_WINDOW` results for a shared group and the last `TYPE_WINDOW` for the others.
4. Build a `StepRow`: `results` are the kept statuses, oldest first. `misses` counts statuses in `MISSES`. `step_name` is the newest kept result's name. `call_type` and `call_type_name` are the group's, or `None` for a shared group.
5. Order rows by: misses, highest first; shared rows before call-type rows; `call_type_name`; the newest kept result's `position`; `step_key`.

## Application: `app/application/get_progress/`

| Module | Class | Definition |
| --- | --- | --- |
| `input_data.py` | `GetProgressInputData` | `agent_id: int \| None = None` |
| `input_boundary.py` | `GetProgressInputBoundary` (Protocol) | `async execute(self, input_data: GetProgressInputData) -> None` |
| `output_data.py` | `GetProgressOutputData` | `weeks: tuple[ProgressWeek, ...]`, `this_week: WeekNumbers \| None`, `first_week_percent: int \| None`, `call_types: tuple[CallTypeProgress, ...]`, `step_rows: tuple[StepRow, ...]`, `demo_data: bool` |
| `output_boundary.py` | `GetProgressOutputBoundary` (Protocol) | `prepare_success_view(self, output_data: GetProgressOutputData) -> None`; `prepare_fail_view(self, message: str) -> None` |
| `data_access.py` | `ProgressDataAccess` (Protocol) | see below |
| `interactor.py` | `GetProgressInteractor` | fields `data: ProgressDataAccess`, `shared_steps: SharedStepsSource`, `clock: Clock`, `presenter: GetProgressOutputBoundary`; `async execute(input_data) -> None` |

**`ProgressDataAccess`** (every method counts only scored calls inside the window, for the agent when one is given):

| Method | Returns |
| --- | --- |
| `async week_totals(window) -> Sequence[WeekTotals]` | Steps completed and steps required (total minus under review) per UTC Monday week, oldest first. Weeks with no call are absent. |
| `async call_type_totals(window) -> Sequence[CallTypeTotals]` | The same sums and the number of calls per call type. |
| `async step_results(window) -> Sequence[StepResult]` | One per resolved step result, oldest call first, then step position. |
| `async has_demo_calls(window) -> bool` | Whether any counted call was scored by the demo seed. |

**`SharedStepsSource`** (new port in `app/application/ports.py`): `async load(self) -> frozenset[str]`. Raises `RulesUnavailable`.

**`GetProgressInteractor.execute`**:

1. `now = clock.now()`; `window = progress_window(now, input_data.agent_id)`.
2. `shared = await shared_steps.load()`. On `RulesUnavailable`: `presenter.prepare_fail_view(str(error))` and return. Nothing else is read.
3. Read `week_totals`, `call_type_totals`, `step_results` and `has_demo_calls`.
4. `presenter.prepare_success_view(GetProgressOutputData(weeks=eight_weeks(totals, now), this_week=call_list.this_week(totals, now), first_week_percent=call_list.first_week_percent(totals), call_types=call_type_progress(...), step_rows=step_rows(results, shared), demo_data=...))`.

## Interface adapters: `app/adapters/http/progress/`

| Module | Class | Definition |
| --- | --- | --- |
| `view_model.py` | `ProgressViewModel` (mutable dataclass) | `demo_data: bool = False`, `weeks: list[dict]`, `this_week: dict \| None = None`, `first_week_percent: int \| None = None`, `comparison: str \| None = None`, `call_types: list[dict]`, `steps: list[dict]`, `error: str \| None = None`. `body() -> dict` returns the seven response fields in the contract's order, without `error`. |
| `presenter.py` | `GetProgressPresenter` | holds a `ProgressViewModel`. `prepare_success_view` fills it per the contract. `prepare_fail_view` sets `error`. Helpers: `comparison(this_week, first_week_percent) -> str \| None`, `label(row) -> str`, `summary(row) -> str` ([research.md](research.md) R8). |
| `controller.py` | `GetProgressController` | holds a `GetProgressInputBoundary`. `async execute(self, agent_id: int \| None) -> None` builds `GetProgressInputData` and calls it. |
| `router.py` | — | `get_progress_parts(request, session) -> tuple[GetProgressController, ProgressViewModel]` wires one request. `async progress(agent_id: int \| None = None, parts = Depends(...)) -> dict` runs the controller, raises `HTTPException(503, view_model.error)` on failure, otherwise returns `view_model.body()`. |

## Other adapters

| Module | Item | Definition |
| --- | --- | --- |
| `adapters/persistence/progress_data_access.py` | `DEMO_MODEL` | `"demo-seed"` (the loader's marker) |
| | `window_clauses(window) -> list` | `Call.status == "scored"`, `Call.started_at >= since`, `Call.started_at < until`, and `Call.agent_id == agent_id` when set |
| | `week_totals_query(window)` | `WEEK` (imported from `call_list_reader`), `sum(Call.steps_completed)`, `sum(Call.steps_total - Call.steps_under_review)`, grouped and ordered by week |
| | `call_type_totals_query(window)` | `Call.call_type`, `max(Procedure.name)`, the two sums and `count()`, joined to `Procedure`, grouped by call type |
| | `step_results_query(window)` | `Call.id`, `Call.started_at`, `Call.call_type`, `Procedure.name`, `CallStep.step_key`, `CallStep.name`, `CallStep.position`, `CallStep.status`; `CallStep.status IN RESOLVED`; ordered by `Call.started_at`, `Call.id`, `CallStep.position` |
| | `demo_calls_query(window)` | `SELECT EXISTS(...)` with the window clauses and `Call.model == DEMO_MODEL` |
| | `SqlAlchemyProgressDataAccess` | the four port methods over an `AsyncSession` |
| `adapters/files/shared_steps.py` | `JsonSharedSteps(rules_dir)` | `async load()` returns `frozenset(common["shared_step_keys"])` from `_common.json`. `FileNotFoundError` becomes `RulesUnavailable`. |
| `infrastructure/analysis_settings.py` | `shared_steps_from_env(environ) -> JsonSharedSteps` | uses `RULES_DIR` or `DEFAULT_RULES_DIR`, like the prompt template |
| `main.py` | `configure_progress(app, environ)` | sets `app.state.shared_steps`; the router is included |
