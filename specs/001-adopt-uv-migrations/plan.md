# Implementation Plan: Locked Backend Setup and Starting Schema

**Branch**: `001-adopt-uv-migrations` | **Date**: 2026-10-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-adopt-uv-migrations/spec.md`

Planning input applied on top of that spec: uv commands start the server,
run Alembic, and run tests. Docker Compose starts the server with uv. The
first Alembic revision creates an initial table.

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Replace the backend's unlocked dependency list with one uv project and a
committed lock. Teammates and the running app install from that lock.
Three uv commands cover the work: `uv run serve`, `uv run migrate`, and
`uv run test`. Compose starts the API with `uv run serve` and runs
PostgreSQL 18. `uv run migrate` applies one Alembic revision that creates
the `app_meta` table. The health check stays the same for the screen and
becomes asynchronous, because this change edits that file.

Source for this feature MUST follow Clean Architecture (constitution
Principle VII). Domain rules and the health use case sit inside the
dependency circle. FastAPI, SQLAlchemy, Alembic, and the `uv run`
command wrappers stay at the outer edge and depend inward.

## Technical Context

**Language/Version**: Python 3.12 (the version the backend image already uses)

**Primary Dependencies**: uv 0.11.32, FastAPI, uvicorn, SQLAlchemy 2 async
engine, psycopg 3, Alembic, hatchling (build backend for `uv run` scripts),
pytest (dev)

**Storage**: PostgreSQL 18. One application table, `app_meta`, plus
Alembic's version table. See [data-model.md](data-model.md).

**Testing**: pytest via `uv run test`. Unit tests call each new function.
The migration is checked by the SQL it generates, not by another database
product.

**Target Platform**: Local Docker Compose for the app. Host uv for install,
migrate, and test outside Compose.

**Project Type**: Web application. This feature changes the backend and
Compose only. The frontend package install stays on npm.

**Performance Goals**: A clean backend install plus a reachable health
check completes in under 10 minutes, not counting the first download of
the base image. The schema command is safe to run twice.

**Constraints**: PostgreSQL 18 only. uv is the only Python installer.
Async SQLAlchemy on the request path. Alembic is the only schema change.
One initial table, and it is not a coaching record. A schema command must
not drop existing data. Frontend stays on npm. Every new or changed
function has a unit test that calls it. Clean Architecture layering is
mandatory: domain and application code MUST NOT import FastAPI,
SQLAlchemy, or Alembic.

**Scale/Scope**: One local stack, one lockfile, one Alembic revision, one
application table. No coaching screens.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Before research | After design |
| --- | --- | --- |
| I. Server owns the judgment | Pass. No scoring or step checks move to the screen. | Pass. Health still only reports that the API and database are up. |
| II. Asynchronous API | Pass, with a required edit. The health handler is synchronous today. This change edits that file, so the handler becomes `async def` and uses an async session. | Pass. [contracts/health.md](contracts/health.md) keeps the same response and requires an async handler that delegates to a use case. |
| III. Asynchronous persistence | Pass. PostgreSQL 18, async SQLAlchemy, one Alembic revision for `app_meta`. Migration `run_sync` stays off the request path. | Pass. [data-model.md](data-model.md) and [research.md](research.md) record the driver, the revision, and the refusal to reuse a PostgreSQL 16 data directory. Persistence adapters live outside the domain. |
| IV. Typed component UI | Pass. No frontend source is added. | Pass. The frontend is out of the source layout below. |
| V. One stack | Pass. uv for Python, npm for JavaScript, PostgreSQL 18, Compose. No second package manager. | Pass. [contracts/uv-commands.md](contracts/uv-commands.md) is the only Python install and start path. hatchling is the build backend uv needs for scripts, not a second installer. |
| VI. Unit test every new function | Pass. `serve`, `migrate`, `test`, the health use case, the async health route, and the migration entry points each get a test that calls them. | Pass. [quickstart.md](quickstart.md) step 2 runs that suite with `uv run test`. |
| VII. Clean Architecture | Pass. This feature introduces `app_meta` and a health check; both are designed with inward dependencies. | Pass. Source layout below names domain, application, adapters, and infrastructure. Domain and use cases do not import FastAPI, SQLAlchemy, or Alembic. The FastAPI health route only delegates. SQLAlchemy maps `app_meta`; the domain entity holds the key/value rules. |

No gate failed. Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/001-adopt-uv-migrations/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── uv-commands.md
│   └── health.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
backend/
├── pyproject.toml              # dependencies and serve / migrate / test scripts
├── uv.lock                     # the only Python dependency record
├── alembic.ini
├── alembic/                    # infrastructure: schema driver
│   ├── env.py                  # async engine, run_sync for migrations only
│   └── versions/
│       └── <revision>_create_app_meta.py
├── app/
│   ├── domain/                 # entities and pure rules (no FastAPI/SQLAlchemy)
│   │   └── app_meta.py         # AppMeta entity: key/value required and unique
│   ├── application/            # use cases + ports
│   │   ├── ports.py            # DatabaseProbe (and similar) protocols
│   │   └── check_health.py     # CheckHealth use case
│   ├── adapters/               # interface adapters
│   │   ├── persistence/
│   │   │   ├── models.py       # SQLAlchemy mapping for app_meta
│   │   │   ├── engine.py       # async engine and session factory
│   │   │   └── database_probe.py
│   │   └── http/
│   │       └── health.py       # FastAPI route; delegates to CheckHealth
│   ├── infrastructure/         # frameworks and drivers at the edge
│   │   └── commands.py         # serve, migrate, test wrappers
│   └── main.py                 # wires FastAPI app and includes routers
├── tests/
│   ├── test_domain_app_meta.py
│   ├── test_check_health.py
│   ├── test_commands.py
│   ├── test_health_route.py
│   ├── test_engine.py
│   └── test_migration_sql.py
└── Dockerfile                  # uv sync --frozen, no pip install

docker-compose.yml              # postgres:18; backend command is `uv run serve`
```

`backend/requirements.txt` is removed so the image and developers cannot
install from a second list.

**Structure Decision**: Keep the top-level `backend/` and `frontend/`
split. Inside `backend/app/`, source is layered by Clean Architecture:
`domain/` → `application/` ← `adapters/` ← `infrastructure/` and
`main.py`. Alembic stays under `backend/alembic/` as an outer driver.
Tests live in `backend/tests/` and target each layer. The frontend tree
is unchanged. Flat modules such as `app/models.py`, `app/db.py`, and an
inline health handler in `app/main.py` are non-compliant for this feature
and MUST be moved into the layout above.

## Complexity Tracking

No constitution violations require justification.

## Phase 0 and Phase 1 outputs

Research is in [research.md](research.md). The design artifacts are
[data-model.md](data-model.md), [contracts/uv-commands.md](contracts/uv-commands.md),
[contracts/health.md](contracts/health.md), and [quickstart.md](quickstart.md).

Post-design constitution check: all seven gates still pass. Nothing in the
contracts or the data model puts judgment in the frontend, a synchronous
session on the request path, a database other than PostgreSQL 18, a Python
install that bypasses uv, a new frontend file, a function without a test,
domain or use-case code that imports FastAPI/SQLAlchemy/Alembic, or
business rules left inside routers or ORM models.
