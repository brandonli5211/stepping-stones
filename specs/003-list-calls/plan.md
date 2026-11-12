# Implementation Plan: List Calls with a Demo Clock

**Branch**: `feat/33-load-demo-48` (issue #33) | **Date**: 2026-11-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-list-calls/spec.md`

This plan replaces the rejected `DEMO_TODAY` edit inside `list_calls` (PR #45). It moves the calls list out of `backend/app/calls_api.py` into Clean Architecture layers.

## Summary

**Primary use case**: `ListCalls`. It returns the recent calls with their step outcomes and result labels, plus the header numbers (calls reviewed, this week, first week), measured from a reference instant supplied by a `Clock` port.

The rules move unchanged from the `list_calls` handler into the domain: the window, the UTC Monday of "this week", the percent and the result label. Data access moves into a read adapter that issues the same three queries. A thin `async` route delegates to the use case.

`DEMO_TODAY` is parsed once in the composition root:
- when it is set, a fixed clock serves that instant;
- when it is not, the system clock serves the real time and responses match today's byte for byte;
- when it is malformed, the API refuses to start.

**Inward dependency path**:

| Layer | Module | What it holds |
| --- | --- | --- |
| Domain | `app/domain/call_list.py` | Pure types and rules. Standard library only. |
| Application | `app/application/list_calls.py` | The use case. Depends on the domain and on the `CallListReader` and `Clock` ports in `app/application/ports.py`. |
| Adapters | `app/adapters/persistence/call_list_reader.py` | Async SQLAlchemy reads. |
| Adapters | `app/adapters/http/calls.py` | The FastAPI route and presenter. |
| Infrastructure | `app/infrastructure/clock.py` + `app/main.py` | `DEMO_TODAY` parsing and composition. |

Nothing inner imports anything outer. The HTTP adapter gets the clock from `app.state`, not by importing infrastructure.

## Use Cases

*Accurate after Phase 0 (research) and after Phase 1 (design).*

| Use case | Responsibility | Module |
| --- | --- | --- |
| `ListCalls` (primary) | Builds the calls list and its header from a reference instant given by the `Clock` port and data read through the `CallListReader` port, applying the window, this-week, percent and result-label rules. It never reads the environment, parses HTTP or touches SQL. | `backend/app/application/list_calls.py` |

**Out of scope for this plan**:
- `AnalyzeCall`: `POST /calls/{call_id}`, which stays in `calls_api.py` unchanged. It comes as Feature C, before the PR opens.
- `ApplyDemoResults`: done, in feature 002.

## Technical Context

**Language/Version**: Python ≥ 3.12. The host runs 3.13 via uv.

**Primary Dependencies**: FastAPI and async SQLAlchemy 2 (existing), plus the standard library `datetime`. There are no new dependencies. `httpx` is not installed, so route tests call the handler directly.

**Storage**: PostgreSQL 18. Reads only from `calls`, `call_steps` and `procedures`. No schema change.

**Testing**: pytest (`uv run test`) with no database: domain functions, the use case with fakes, the reader with a fake session, the clock parsing, and the handler and presenter. The real database and the API are checked by [quickstart.md](quickstart.md), including the before/after JSON comparison.

**Target Platform**: The local API (`uv run serve`) and the Compose stack.

**Project Type**: Web application backend. No frontend change.

**Performance Goals**: The same three queries as today, so there is no change in latency.

**Constraints**:
- The response is byte-identical without `DEMO_TODAY` (SC-004).
- The label wording is exact.
- Weeks are UTC Monday-start.
- `DEMO_TODAY` is read only in the composition root.
- Route handlers are async and delegate.

**Scale/Scope**: one use case, about 5 new modules, an edited `main.py` and `ports.py`, a trimmed `calls_api.py`, 6 tasks or fewer.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Before research | After design |
| --- | --- | --- |
| I. Server owns the judgment | Pass. Labels and percents are still computed in the backend, and the screen is unchanged. | Pass. The rules are in `domain/call_list.py`. |
| II. Asynchronous API | Pass. `GET /calls` stays `async def`. | Pass. [contracts/get-calls.md](contracts/get-calls.md): the handler builds the query, delegates, and presents. |
| III. Asynchronous persistence | Pass. Reads stay on `AsyncSession`. No schema change. | Pass. `SqlAlchemyCallListReader` uses `AsyncSession` only. |
| IV. Typed component UI | Pass. No frontend change. | Pass. |
| V. One stack | Pass. No new packages. | Pass. `httpx` is deliberately not added (research R6). |
| VI. Unit test every new function | Pass (planned). | Pass. Every function in [data-model.md](data-model.md), plus the reader, the clock, the handler, the presenter and the `main.py` wiring, gets a calling test. |
| VII. Clean Architecture | Pass. One use case, two ports (read and clock). The rules move out of the router. | Pass. The domain is standard library only. The use case imports only the domain and ports. The HTTP adapter does not import infrastructure. An import-guard test covers `fastapi`, `sqlalchemy`, `alembic`, `psycopg` and `os`. |
| Workflow | Pass. Same branch and issue (#33). One primary use case is in the Summary and in Use Cases. | Pass. Planned as one slice of 6 tasks or fewer. |
| Governance: touched non-compliant files | **Conditional.** `calls_api.py` is edited, by removing `list_calls`, `_percent` and `snake`. Its remaining `analyze_call` still breaks Principle VII. `main.py` and `ports.py` are edited and compliant. | **Conditional**, see Complexity Tracking. |

The only conditional gate is the governance one. It is justified below and closed by Feature C before the PR opens.

## Project Structure

### Documentation (this feature)

```text
specs/003-list-calls/
├── spec.md
├── plan.md              # this file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/get-calls.md
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code

```text
backend/
├── app/
│   ├── domain/call_list.py                      # NEW  types + pure rules
│   ├── application/
│   │   ├── ports.py                             # EDIT add Clock, CallListReader
│   │   └── list_calls.py                        # NEW  ListCalls + ListCallsQuery
│   ├── adapters/
│   │   ├── persistence/call_list_reader.py      # NEW  SqlAlchemyCallListReader
│   │   └── http/calls.py                        # NEW  GET /calls router + present_call_list
│   ├── infrastructure/clock.py                  # NEW  SystemClock, FixedClock, parse_demo_today, clock_from_env
│   ├── main.py                                  # EDIT app.state.clock, include calls router
│   └── calls_api.py                             # EDIT remove list_calls, _percent, snake, unused imports
└── tests/
    ├── test_domain_call_list.py                 # NEW
    ├── test_list_calls.py                       # NEW
    ├── test_call_list_reader.py                 # NEW
    ├── test_clock.py                            # NEW  (+ main wiring)
    └── test_calls_route.py                      # NEW  handler + presenter
```

**Structure Decision**: this is the same layering as features 001 and 002. The HTTP adapter sits beside `adapters/http/health.py`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| `calls_api.py` is edited, but `analyze_call` in it stays non-compliant (Principle VII) inside this feature | One use case per plan (workflow rule). Bringing `analyze_call` into compliance is a second use case (`AnalyzeCall`). The user chose to do it as Feature C, before the PR for #33 opens. | Doing both here would put two use cases in one plan, which is a constitution break. Leaving it with no follow-up would break the governance rule at PR time. |

## Phase 0 and Phase 1 outputs

- **Phase 0**: [research.md](research.md), decisions R1–R8.
- **Phase 1**:
  - [data-model.md](data-model.md)
  - [contracts/get-calls.md](contracts/get-calls.md)
  - [quickstart.md](quickstart.md)

**Post-design constitution check**: Principles I–VII and the workflow rules pass, and the Use Cases section lists exactly one primary use case after both phases. The governance gate stays conditional on Feature C, as recorded in Complexity Tracking.
