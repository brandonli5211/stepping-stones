# Implementation Plan: Call Detail API

**Branch**: `feat/34-call-detail-api` (spec folder `002-call-detail-api`) | **Date**: 2026-11-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-call-detail-api/spec.md`

## Summary

**Primary use case**: `GetCallDetail`: read one stored call by its numeric ID
and assemble everything the call detail screen shows, or raise `CallNotFound`.

`GET /calls/{id}` returns the header, a score worked out from the stored step
results (100 minus points lost, counts, critical count, provisional when steps
are under review), the transcript with notes derived from each step's evidence
turn, the steps with their details (including the step description from the
procedure rules), one flag per missed or wrong step with a one-sentence
message, and a block tagged by call type (Transfer money: the Amount / From /
To field table built from the stored comparison rows, with `reversed` when From
and To are swapped; every other type: empty). Read only, no
analysis, no schema change. A Pydantic `response_model` types the response; an
example goes into `docs/api-contract.md` for #35 and #36.

Dependencies point inward: pure rules in `app/domain/call_detail.py` ← the
`GetCallDetail` use case and its `CallDetailReader` port in `app/application/`
← the SQLAlchemy reader in `app/adapters/persistence/` and the FastAPI route,
presenter and schema in `app/adapters/http/` ← wiring in `app/main.py`. The
domain and use case import no FastAPI, SQLAlchemy or Pydantic.

## Use Cases

Checked after Phase 0 ([research.md](research.md)) and again after Phase 1
([data-model.md](data-model.md), [contracts/](contracts/get-call-detail.md)).
Unchanged by Phase 1.

| Use case | Responsibility | Module |
| --- | --- | --- |
| `GetCallDetail` (primary) | Load one call through the `CallDetailReader` port, apply the domain rules (score, counts, notes, flags, type block) and return a `CallDetail`; raise `CallNotFound` when the call is absent. It must not analyze, write, or know about HTTP or SQL. | `backend/app/application/get_call_detail.py` |

**Out of scope for this plan**: loading the #33 seed file into the #29 tables
(#33 or a follow-up); storing several notes per step (needs a table and a
writer, #38); moving `GET /calls` and `POST /calls/{id}` out of
`app/calls_api.py` into Clean Architecture layers (separate refactor).

## Technical Context

**Language/Version**: Python ≥ 3.12 (backend `pyproject.toml`)

**Primary Dependencies**: FastAPI 0.115.6 (with its bundled Pydantic for the
response schema), SQLAlchemy 2.0.36 async with psycopg 3.2.3. No new
dependency.

**Storage**: PostgreSQL 18, read only: `calls`, `procedures`, `call_turns`,
`call_steps` from #29. No migration.

**Testing**: pytest through `uv run test`; async code run with `asyncio.run`
and fakes for ports, as in `tests/test_check_health.py`. No test database.

**Target Platform**: Linux container from Docker Compose (API on port 8000).

**Project Type**: Web service (backend only for this ticket; the page is #35 and
#36).

**Performance Goals**: One request per page load; three read queries per call
(call with procedure, turns, steps).

**Constraints**: Read only (FR-002); no analysis on the request path; `async def`
route; response must validate against the typed schema.

**Scale/Scope**: One call per request; a call has tens of turns and at most ~10
steps.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Gate | Before Phase 0 | After Phase 1 |
| --- | --- | --- | --- |
| I. Server owns the judgment | Score, counts, notes and flags worked out in the backend; page only shows them | Pass | Pass: domain rules R3–R5; contract says the page must not recompute |
| II. Asynchronous API | New route is `async def` | Pass | Pass |
| III. Async persistence | Async session only; schema changes need a migration | Pass | Pass: reader uses `AsyncSession`; no schema change, so no migration |
| IV. Typed component UI | No frontend code in this ticket | N/A | N/A |
| V. One stack | No new language, library or tool; uv for Python deps | Pass | Pass: Pydantic already comes with FastAPI; tests use existing pytest |
| VI. Unit test every new function | Each new function has a unit test in the same PR | Pass | Pass: every new function, private helpers included, has a test that calls it directly (fixed after `/speckit-analyze` D1) |
| VII. Clean Architecture | Domain / use case free of frameworks; route delegates; one use case | Pass | Pass: layers in Summary and Project Structure; an import test guards domain and application |
| Workflow: one use case, Use Cases section, ≤ 6 tasks | Exactly one primary use case listed after each phase | Pass | Pass: `GetCallDetail` only |
| Governance: touched non-compliant files | A touched file must be brought into compliance | Pass | Pass: `calls_api.py` is not touched (R9); `models.py` gets a comment fix only, and its classes stay at the outer layer |

No violations, so Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/002-call-detail-api/
├── spec.md
├── plan.md                     # this file
├── research.md                 # Phase 0
├── data-model.md               # Phase 1
├── quickstart.md               # Phase 1
├── contracts/
│   └── get-call-detail.md      # Phase 1: shape + examples for #35, #36
├── checklists/requirements.md
└── tasks.md                    # /speckit-tasks (not created here)
```

### Source Code (repository root)

```text
backend/app/
├── domain/
│   └── call_detail.py              # NEW  records + pure rules: score, notes, flags, evidence, type block, CallNotFound
├── application/
│   ├── ports.py                    # EDIT add CallDetailReader Protocol
│   └── get_call_detail.py          # NEW  GetCallDetail use case (primary)
├── adapters/
│   ├── persistence/
│   │   └── call_detail_reader.py   # NEW  SqlAlchemyCallDetailReader + row → record mapper
│   └── http/
│       ├── call_detail_schema.py   # NEW  Pydantic response models (typed schema)
│       └── call_detail.py          # NEW  GET /calls/{id}: presenter, 404 mapping, DI wiring
├── models.py                       # EDIT fix the external_id comment only
└── main.py                         # EDIT include the call detail router

backend/tests/
├── test_domain_call_detail.py      # NEW  HVB-DEMO-06, check-balance no-mistakes, under review, pending
├── test_get_call_detail.py         # NEW  found / not found / no framework imports
├── test_call_detail_repository.py  # NEW  row mapper, reader with a stub session
└── test_call_detail_route.py       # NEW  200 body validates, 404, async handler

docs/
└── api-contract.md                 # NEW  example response (copied from contracts/)
```

**Structure Decision**: Backend web service, using the Clean Architecture
folders that already exist (`domain/`, `application/`, `adapters/http`,
`adapters/persistence/`). The new route gets its own router module so the
older `app/calls_api.py` stays untouched. Route order: `GET /calls/{id}` has a
typed integer path parameter and does not clash with `GET /calls` or
`POST /calls/{id}`.

## Complexity Tracking

No Constitution Check violations.
