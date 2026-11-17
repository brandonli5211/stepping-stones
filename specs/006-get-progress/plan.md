# Implementation Plan: Get Progress

**Branch**: `feat/37-progress` (issue #37, backend half) | **Date**: 2026-11-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/006-get-progress/spec.md`

## Summary

**Primary use case**: `GetProgress`. For one agent and the 8 calendar weeks ending this week, it works out the weekly completion percents, this week against the first week, the percent per call type, the "steps you skip most" rows and the demo-data flag, and hands them to a presenter.

`GET /progress?agent_id=` is a thin async route. It builds the use case's parts for the request, asks the controller to run it, and returns what the presenter put in the view model.

**Inward dependency path**:

| Layer | Module | What it holds |
| --- | --- | --- |
| Domain | `app/domain/progress.py` | Pure progress rules. Standard library plus `app/domain/call_list.py`, whose week and percent rules it reuses (`week_monday`, `percent`, `this_week`, `first_week_percent`, `WeekTotals`, `WeekNumbers`). |
| Application | `app/application/get_progress/` | Input Data, Input Boundary, Interactor, Output Boundary, Output Data and the Data Access Interface, one class per file. Depends on the domain and on ports only. |
| Interface adapters | `app/adapters/http/progress/` | Controller, Presenter and View Model, one class per file, plus the FastAPI router. |
| Interface adapters | `app/adapters/persistence/progress_data_access.py` | The Data Access Interface over the async SQLAlchemy session. |
| Interface adapters | `app/adapters/files/shared_steps.py` | Reads the shared step keys from the rules file. |
| Frameworks | `app/main.py`, `app/infrastructure/analysis_settings.py` | Read `RULES_DIR` once, put the shared-steps source on the app, register the router. |

Nothing inner imports anything outer.

### The nine CSC207 parts

| Part | Class | Module |
| --- | --- | --- |
| Controller | `GetProgressController` | `backend/app/adapters/http/progress/controller.py` |
| Input Boundary | `GetProgressInputBoundary` | `backend/app/application/get_progress/input_boundary.py` |
| Input Data | `GetProgressInputData` | `backend/app/application/get_progress/input_data.py` |
| Interactor | `GetProgressInteractor` | `backend/app/application/get_progress/interactor.py` |
| Output Boundary | `GetProgressOutputBoundary` | `backend/app/application/get_progress/output_boundary.py` |
| Output Data | `GetProgressOutputData` | `backend/app/application/get_progress/output_data.py` |
| Presenter | `GetProgressPresenter` | `backend/app/adapters/http/progress/presenter.py` |
| View Model | `ProgressViewModel` | `backend/app/adapters/http/progress/view_model.py` |
| Data Access Interface | `ProgressDataAccess` | `backend/app/application/get_progress/data_access.py` |

**How one request flows**:

1. The route builds a `ProgressViewModel`, a `GetProgressPresenter` holding it, a `GetProgressInteractor` holding the presenter and the data access, and a `GetProgressController` holding the interactor (typed as the Input Boundary).
2. The controller turns the request's `agent_id` into `GetProgressInputData` and calls the Input Boundary.
3. The interactor reads the clock, loads the shared step keys and the stored numbers through its ports, applies the domain rules, and calls the Output Boundary with `GetProgressOutputData`.
4. The presenter fills the view model with response-ready values, including each row's label and summary line.
5. The route returns the view model's body, or a 503 when the presenter recorded a failure.

## Use Cases

*Accurate after Phase 0 (research) and after Phase 1 (design).*

| Use case | Responsibility | Module |
| --- | --- | --- |
| `GetProgress` (primary) | Works out one agent's 8-week progress (weeks, this week against the first week, call types, step rows, demo-data flag) from stored calls through the `ProgressDataAccess` port and the domain rules, and passes it to the Output Boundary. It never touches HTTP, SQL or files. | `backend/app/application/get_progress/interactor.py` |

**Out of scope for this plan**:
- `ViewProgress`, the Progress screen: feature 007, planned after this one, on top of `feat/31-app-shell-ts`.
- Changing `ListCalls` or `AnalyzeCall`. `call_list.py` is imported, not edited.
- Moving `app/models.py`, `load_calls.py` or `call_parse.py` into the layers.

## Technical Context

**Language/Version**: Python ≥ 3.12 (uv; 3.13 on the host, 3.12 in the image).

**Primary Dependencies**: FastAPI and SQLAlchemy 2 async with psycopg 3, all existing. No new dependency.

**Storage**: PostgreSQL 18, read only. It reads `calls`, `call_steps` and `procedures`. No schema change and no migration.

**Testing**: pytest via `uv run test`, with no database. Three tests cover this feature: `test_progress_small_dataset` runs the use case on six fixed calls over three weeks (one wrong step, one step under review) and checks the weekly and by-type percents, the top step row and its summary line, and that under review is left out of the step rows; `test_progress_demo_48` runs the whole use case (real interactor, rules-file reader and presenter) over `sample/demo_48` with an in-memory data access and asserts the spec's weekly, by-call-type and step-row numbers, and `test_progress_503_without_rules` runs the route with a missing rules file. The shared layer guard checks the new domain and application modules. Not every function has its own test (see Complexity Tracking). The real queries are checked against a throwaway PostgreSQL 18 database ([quickstart.md](quickstart.md)).

**Target Platform**: the API container and the developer's host.

**Project Type**: web application backend. One new route, no frontend change.

**Performance Goals**: four small queries per request. The largest reads one row per resolved step of the agent's scored calls in 8 weeks (281 rows for the demo data).

**Constraints**:
- **Clean Architecture**: domain and application import no FastAPI, SQLAlchemy, Alembic or psycopg.
- **Async**: the route is `async def`, and persistence uses the async session.
- **Reuse**: no copy of the week or percent rules.
- **Read only**: `GET /calls` and `POST /calls/{id}` answer as before.

**Scale/Scope**: one use case, 15 small new modules (9 of them one class each), 2 edited modules, 6 tasks.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Before research | After design |
| --- | --- | --- |
| I. Server owns the judgment | Pass. Every percent, count, order and summary line is produced by the backend. | Pass. Rules are in `app/domain/progress.py`; the presenter writes the summary line on the server. |
| II. Asynchronous API | Pass (planned). | Pass. `GET /progress` is `async def`. |
| III. Asynchronous persistence | Pass. Read only; no schema change, so no migration. | Pass. `SqlAlchemyProgressDataAccess` uses the `AsyncSession` from `get_session`. |
| IV. Typed component UI | Pass. No frontend change in this feature. | Pass. |
| V. One stack | Pass. No new package. | Pass. |
| VI. Unit test every new function | Pass (planned). | **Deviation, accepted 2026-11-19.** The tests were cut to three; see Complexity Tracking. |
| VII. Clean Architecture | Pass. One use case, with ports for persistence and the rules file. | Pass. All nine parts are separate classes. The interactor depends on boundaries and ports only. The route delegates. An import-guard test covers the domain and application modules. |
| Technology constraint: progress questions stay SQL filters | Pass. | Pass. Agent, time window and status are SQL filters over relational columns, and the weekly and by-type sums are SQL. No JSON column is read. Choosing the last 5 or 10 results per step is a domain rule so that it can be tested without a database ([research.md](research.md) R4). |
| Workflow | Pass. Branch `feat/37-progress`, issue #37, one primary use case in the Summary and in Use Cases. | Pass. The tasks are planned as one vertical slice of 6. |
| Governance: touched non-compliant files | Pass. `main.py` and `analysis_settings.py` are edited and are compliant. `app/models.py` and `call_list_reader.py` are only imported. | Pass. |

Principle VI is not met after the 2026-11-19 test cut; the deviation is recorded in Complexity Tracking. No other gate failed.

## Project Structure

### Documentation (this feature)

```text
specs/006-get-progress/
├── spec.md
├── plan.md              # this file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   └── get-progress.md  # GET /progress
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── domain/
│   │   └── progress.py                      # NEW  types and pure rules; imports call_list
│   ├── application/
│   │   ├── ports.py                         # EDIT add SharedStepsSource
│   │   └── get_progress/
│   │       ├── __init__.py                  # NEW
│   │       ├── input_data.py                # NEW  GetProgressInputData
│   │       ├── input_boundary.py            # NEW  GetProgressInputBoundary
│   │       ├── output_data.py               # NEW  GetProgressOutputData
│   │       ├── output_boundary.py           # NEW  GetProgressOutputBoundary
│   │       ├── data_access.py               # NEW  ProgressDataAccess
│   │       └── interactor.py                # NEW  GetProgressInteractor
│   ├── adapters/
│   │   ├── http/progress/
│   │   │   ├── __init__.py                  # NEW
│   │   │   ├── controller.py                # NEW  GetProgressController
│   │   │   ├── presenter.py                 # NEW  GetProgressPresenter
│   │   │   ├── view_model.py                # NEW  ProgressViewModel
│   │   │   └── router.py                    # NEW  GET /progress
│   │   ├── persistence/progress_data_access.py   # NEW  SqlAlchemyProgressDataAccess
│   │   └── files/shared_steps.py            # NEW  JsonSharedSteps
│   ├── infrastructure/analysis_settings.py  # EDIT shared_steps_from_env
│   └── main.py                              # EDIT configure_progress, include the router
└── tests/
    ├── test_progress_route.py               # NEW  503 when the rules file is missing
    └── test_progress_demo_48.py             # NEW  the spec's numbers from sample/demo_48
```

**Structure Decision**: the use case gets its own package under `application/` and under `adapters/http/`, with one class per file, so each CSC207 part can be pointed at. Earlier use cases are single modules; they are not restructured here.

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
| --- | --- | --- |
| Principle VI (unit test every new function) is not met. | On 2026-11-19 the product owner cut this feature's tests to `test_progress_demo_48` and `test_progress_503_without_rules`, plus the shared layer guard; `test_progress_small_dataset` was added back on 2026-11-20. The domain rules, the interactor, the presenter and the controller are covered only through those tests. Leaving steps under review out of the weekly and by-type sums happens in SQL; the small-dataset test's fake mirrors that rule, so only the database run checks the real query. These have no test: the empty answer, the agent filter, the SQL adapter (`progress_data_access.py`), `shared_steps_from_env`, `configure_progress` and the route registration. The real database run in quickstart.md is the only check of the SQL and the wiring. | One unit test per function was the original plan and was cut on purpose. Reviewers must accept this deviation explicitly. |

## Phase 0 and Phase 1 outputs

- **Phase 0**: [research.md](research.md), decisions R1–R9. No NEEDS CLARIFICATION remained.
- **Phase 1**: [data-model.md](data-model.md), [contracts/get-progress.md](contracts/get-progress.md), [quickstart.md](quickstart.md).

**One spec change made during planning**: an edge case and FR-016 were added to [spec.md](spec.md). When the shared rules file cannot be read, the request fails as "service unavailable" with no partial answer, the same as call analysis does today ([research.md](research.md) R5).

**Post-design constitution check**: all gates passed at design time (Principle VI is a recorded deviation since the 2026-11-19 test cut). The domain and application packages import no framework or driver. The route only wires and delegates. No rule sits in a router, ORM model or UI. The Use Cases section lists exactly one primary use case after both phases.
