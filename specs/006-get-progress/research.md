# Research: Get Progress

Every Technical Context item was known. These decisions record the choices.

## R1. One use case for the whole answer

- **Decision**: one use case, `GetProgress`, returns the weeks, the comparison, the call types, the step rows and the demo-data flag in one answer.
- **Rationale**: issue #37 asks for one `GET /progress`, and the screen shows all of it at once. The four parts share one window, one agent and one clock.
- **Alternatives considered**: a use case per section (weekly, by type, steps). That is three endpoints or three interactors behind one route for one screen, and three features under the one-use-case rule.

## R2. All nine CSC207 parts, one class per file

- **Decision**: the use case lives in `app/application/get_progress/` (Input Data, Input Boundary, Interactor, Output Boundary, Output Data, Data Access Interface) and `app/adapters/http/progress/` (Controller, Presenter, View Model, router). The interactor returns nothing. It calls the Output Boundary, and the presenter fills the view model.
- **Rationale**: the product owner requires every part as its own class (spec FR-013). One file per class lets each part be found by name.
- **Alternatives considered**:
  - The style of features 002–004 (the use case returns a value, a presenter function sits in the router module). It has no Input Boundary, Output Boundary or View Model.
  - All nine classes in one module: allowed by "its own class", but harder to point at.
- **Boundaries as `typing.Protocol`**: the same style as the existing ports. The interactor satisfies `GetProgressInputBoundary`, and the presenter satisfies `GetProgressOutputBoundary`. A test checks both by calling them through the boundary type.

## R3. Reuse the calls-list rules by import

- **Decision**: `app/domain/progress.py` imports `week_monday`, `percent`, `this_week`, `first_week_percent`, `WeekTotals` and `WeekNumbers` from `app/domain/call_list.py`. The persistence adapter imports the `WEEK` expression from `call_list_reader.py`.
- **Rationale**: spec FR-011 and FR-003. One definition of "week" and "percent" keeps My calls and Progress in agreement.
- **Alternatives considered**: moving the shared rules into a new `domain/weeks.py`. That is cleaner, but it edits feature 003's modules and tests for no behaviour change. It can be done later.

## R4. SQL sums for weeks and call types; the last-N rule in the domain

- **Decision**: the data access runs four queries, each filtered in SQL by agent, window and `status = 'scored'`:
  1. week totals: `sum(steps_completed)`, `sum(steps_total - steps_under_review)` per UTC Monday week;
  2. call type totals: the same sums and `count(*)` per call type, with the procedure name;
  3. step results: one row per resolved step (`completed`, `missed`, `wrong`) with call id, start time, call type, names, position and status, oldest first;
  4. whether any counted call has `model = 'demo-seed'`.

  The domain then picks the last 5 or 10 results per step, counts misses and orders the rows.
- **Rationale**: issue #37 wants the numbers from SQL queries, and the constitution wants progress questions to stay SQL filters. The window and ordering rules must be testable with a small fixed dataset and no database (spec FR-012), so they are domain code.
- **Alternatives considered**:
  - `row_number()` window functions in SQL for the last 5 or 10: correct, but then the rule can only be tested against a database.
  - Loading whole calls and summing everything in Python: moves the sums out of SQL.

## R5. Shared steps come from the rules file, per request

- **Decision**: a new port `SharedStepsSource.load() -> frozenset[str]` in `application/ports.py`, implemented by `JsonSharedSteps` (`adapters/files/shared_steps.py`), which reads `shared_step_keys` from `<RULES_DIR>/_common.json`. A missing file raises the existing `RulesUnavailable`. The interactor then calls `prepare_fail_view`, and the route answers 503.
- **Rationale**: `shared_step_keys` is the rules' own list, so no second list is added. Reading per request with a 503 is what call analysis already does for the same file. A missing file must not stop the API from starting, because `GET /calls` does not need it. Docker Compose already mounts `docs/` and sets `RULES_DIR`.
- **Alternatives considered**:
  - Working it out from the active procedures in the database (keys present in every procedure): reads the JSON rules column and gives a wrong answer when only one procedure is loaded.
  - Reading the file once at startup: a missing file would stop every endpoint.
  - Hard-coding the three keys: a second list.

## R6. The window is 8 calendar weeks with an upper bound

- **Decision**: `ProgressWindow(since, until, agent_id)`. `since` is 00:00 UTC on the Monday 7 weeks before this week's Monday. `until` is 00:00 UTC on the Monday after this week, exclusive.
- **Rationale**: the chart needs exactly 8 bars. The upper bound keeps calls dated after the demo "today" week out of the by-type numbers and step rows. The whole current week counts, as it does on the My calls card.
- **Alternatives considered**: reusing `CallWindow` (`now − 8 × 7 days`, no upper bound). It can reach into a 9th calendar week and lets later calls in.

## R7. Under review

- **Decision**: steps required = `steps_total − steps_under_review`, summed in SQL. Step results with status `under_review` are not read.
- **Rationale**: spec FR-008 and its first assumption, accepted by the product owner.
- **Alternatives considered**: counting under review as required, as My calls does. Issue #37 says to leave it out.

## R8. Where the words are written

- **Decision**: the presenter writes each row's `label` (the call type's name or "All call types") and `summary` line, and the `comparison` line for this week against the first week. The domain gives it the counts, the call type and whether the step is shared, and orders the rows. Ordering uses the call type's name, with shared rows first, so it does not depend on the label text.
- **Rationale**: wording is presentation, and it stays on the server (Principle I). The order is a rule, so it is in the domain.
- **Comparison line**: `Up from {first}% in week 1` when this week's percent is higher than the first week's, `Down from …` when lower, `Same as …` when equal. There is none when this week has no numbers or either percent is unknown.
- **Summary lines**: `slug` is the call type key with `_` replaced by `-`.

  | Case | Line |
  | --- | --- |
  | misses > 0, one call type, window > 1 | `Missed on {m} of your last {w} {slug} calls` |
  | misses > 0, all call types, window > 1 | `Missed on {m} of your last {w} calls` |
  | no misses, one call type, window > 1 | `Done on all of your last {w} {slug} calls` |
  | no misses, all call types, window > 1 | `Done on all of your last {w} calls` |
  | window = 1 | `Missed on your last {slug} call` / `Done on your last {slug} call` (without the slug for all call types) |

## R9. Response field names

- **Decision**: `steps_completed`, `steps_total` and `percent`, the same names `GET /calls` uses for `this_week`. See [contracts/get-progress.md](contracts/get-progress.md).
- **Rationale**: the screen can share types between the two answers. Here `steps_total` means steps required, which is the total minus steps under review.
- **Alternatives considered**: `steps_required`. Clearer on its own, but it gives the same idea two names across the API.
