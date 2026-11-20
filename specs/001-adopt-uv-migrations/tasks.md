---

description: "Task list for locked backend setup and starting schema"
---

# Tasks: Locked Backend Setup and Starting Schema

**Input**: Design documents from `/specs/001-adopt-uv-migrations/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md, constitution.md

**Tests**: Required. The spec (FR-012, SC-006) and constitution principle VI require a unit test that calls every new or changed function. Tests do not use SQLite or any database other than the PostgreSQL 18 quickstart check.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested on its own.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Setup, Foundational, and Polish tasks have no story label

## Path Conventions

- Backend: `backend/`
- Clean Architecture packages under `backend/app/`:
  - Domain: `backend/app/domain/`
  - Application (use cases + ports): `backend/app/application/`
  - Adapters: `backend/app/adapters/persistence/`, `backend/app/adapters/http/`
  - Infrastructure: `backend/app/infrastructure/`, plus `backend/alembic/`
  - Composition root: `backend/app/main.py`
- Compose: `docker-compose.yml` at the repository root
- Docs: `README.md`, `docs/SETUP.md`
- Frontend package install stays on npm. Do not add a uv command for `frontend/`

## Scope notes from the approved design

- uv commands are `uv run serve`, `uv run migrate`, and `uv run test`, linked as `[project.scripts]` in `backend/pyproject.toml`. There is no format or lint command in this feature.
- `uv run migrate` is its own command in the documented startup sequence. `uv run serve` does not call Alembic. Compose starts the API with `uv run serve` only.
- The initial table is `app_meta`. It is not a coaching table (no calls, templates, scores, or agents).
- Clean Architecture is mandatory (constitution VII, FR-013). Domain and application modules MUST NOT import FastAPI, SQLAlchemy, or Alembic. Phases 1–5 delivered the locked install and schema; Phase 6 aligns that code with the layered layout in `plan.md`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: One uv project and one lockfile replace `backend/requirements.txt`

- [X] T001 Create `backend/pyproject.toml` and an empty `backend/app/__init__.py`. Name the project `stepping-stones-backend`, require Python `>=3.12`, and set the build backend to hatchling with wheel packages `["app"]`. Copy these runtime pins from `backend/requirements.txt` exactly: `fastapi==0.115.6`, `uvicorn[standard]==0.34.0`, `sqlalchemy==2.0.36`, `psycopg[binary]==3.2.3`. Add `alembic` and a dev dependency on `pytest` without inventing versions for those two. Declare `[project.scripts]` `serve = "app.commands:serve"`, `migrate = "app.commands:migrate"`, and `test = "app.commands:test"`.
- [X] T002 Generate `backend/uv.lock` by running `uv lock` in `backend/` after T001, and commit that lock as the only Python dependency record
- [X] T003 [P] Delete `backend/requirements.txt` so install cannot fall back to a second dependency list
- [X] T004 [P] Rewrite `backend/Dockerfile` to start from `python:3.12-slim`, copy uv `0.11.32` from `ghcr.io/astral-sh/uv:0.11.32` (`/uv` and `/uvx` onto `/bin/`), copy `backend/pyproject.toml` and `backend/uv.lock`, run `uv sync --frozen`, and set `CMD` to `uv run serve`. Do not run `pip install` and do not copy `requirements.txt`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Async database access, the test command, and PostgreSQL 18. No user story work starts until this phase is complete.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Write failing unit tests in `backend/tests/test_db.py` that call `get_engine` and `get_session` from `backend/app/db.py` with a fake `DATABASE_URL`. Assert the engine URL uses scheme `postgresql+psycopg://` and that no connection is opened. Assert `get_session` yields an async session.
- [X] T006 [P] Write a failing unit test in `backend/tests/test_commands.py` that calls `test` from `backend/app/commands.py` with a fake process runner and asserts the launched command is pytest. Assert it does not start the API and does not require Docker Compose.
- [X] T007 Implement `get_engine` and `get_session` in `backend/app/db.py` so T005 passes. Use SQLAlchemy's async engine and async sessions only. Read `DATABASE_URL`. Do not call `create_engine` or open a synchronous session.
- [X] T008 Implement `test` in `backend/app/commands.py` so T006 passes. Default the process runner to a real subprocess launch, and run pytest for `backend/tests`. `uv run test` must exit 0 when the suite passes and non-zero when a test fails.
- [X] T009 Point the `db` service in `docker-compose.yml` at `postgres:18`. Mount a new named volume at `/var/lib/postgresql` (the PostgreSQL 18 image path; data lives in `/var/lib/postgresql/18/docker`). Do not mount that volume at `/var/lib/postgresql/data` and do not attach the existing `pgdata` volume. Do not delete the old volume. Leave the frontend service on `npm run dev`.

**Checkpoint**: `uv sync` works from `backend/`, `uv run test` runs pytest, and Compose can start PostgreSQL 18 on a new volume.

---

## Phase 3: User Story 1 - One locked backend setup (Priority: P1) 🎯 MVP

**Goal**: A clean checkout installs one locked backend set, and Compose starts that same set with `uv run serve`. The health screen still reports the API is up and the database is reachable.

**Independent Test**: From a clean checkout, run `uv sync` in `backend/`, start the stack, and confirm the screen reports the database is reachable. Installed versions match `backend/uv.lock`. A second clean install of the same revision has zero version differences. `uv sync --frozen` exits non-zero when `backend/uv.lock` is missing or disagrees with `backend/pyproject.toml`.

### Tests for User Story 1

> Write these tests first and confirm they fail before the implementation tasks.

- [X] T010 [P] [US1] Add a failing unit test in `backend/tests/test_commands.py` that calls `serve` from `backend/app/commands.py` with a fake process runner. Assert the command is uvicorn for `app.main:app` bound to `0.0.0.0` port `8000` with reload. Assert `serve` does not launch Alembic.
- [X] T011 [P] [US1] Add a failing unit test in `backend/tests/test_health.py` that calls the health handler in `backend/app/main.py` with a fake async session. When `SELECT 1` succeeds, assert the return value is `{"status": "ok", "database": "connected"}`. When the session raises, assert that healthy body is not returned.

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `serve` in `backend/app/commands.py` so T010 passes. Launch uvicorn for `app.main:app` on `0.0.0.0` port `8000` with reload. Do not call Alembic from `serve`.
- [X] T013 [P] [US1] Rewrite the health handler in `backend/app/main.py` as `async def` using `get_session` from `backend/app/db.py`, so T011 passes. Keep `GET /api/health`, status `200`, and the fields `status` and `database`. Remove `create_engine`. Do not read `app_meta` and do not add coaching fields. Leave CORS as it is.
- [X] T014 [P] [US1] Set the backend service command in `docker-compose.yml` to `uv run serve`. Add an anonymous volume at `/app/.venv` beside the `./backend:/app` mount so the bind mount does not hide the environment. Do not start the API with a bare uvicorn command.
- [X] T015 [P] [US1] Document the locked install in `README.md` and `docs/SETUP.md`: from `backend/`, `uv sync` installs `backend/uv.lock`, and `uv sync --frozen` exits non-zero when the lock is missing or stale. State that Compose starts the API with `uv run serve`. State that the frontend still installs with npm. Do not document Alembic in this task.

**Checkpoint**: User Story 1 is independently testable. The health check reports `ok` / `connected` without `app_meta`.

---

## Phase 4: User Story 2 - A fresh database gets its starting schema (Priority: P2)

**Goal**: `uv run migrate` applies one Alembic revision that creates `app_meta`. A second run exits 0 and does not change the schema or drop data. This command is the schema step in the documented startup sequence. It is not folded into `uv run serve`.

**Independent Test**: Point `uv run migrate` at an empty PostgreSQL 18 database. Confirm `app_meta` exists with the columns in `data-model.md`. Run `uv run migrate` again and confirm it exits 0 and the schema is unchanged. A second empty database from the same revision ends with the same starting schema.

### Tests for User Story 2

> Write these tests first and confirm they fail before the implementation tasks.

- [X] T016 [P] [US2] Add a failing unit test in `backend/tests/test_commands.py` that calls `migrate` from `backend/app/commands.py` with a fake process runner. Assert the command is `alembic upgrade head`. Assert it does not start the API and does not drop data.
- [X] T017 [P] [US2] Add a failing test in `backend/tests/test_migration_sql.py` that runs the revision in Alembic offline SQL mode (`upgrade head --sql`) through `backend/alembic/env.py`. Assert the SQL contains `CREATE TABLE app_meta` and does not contain `DROP`. Assert columns `id`, `key`, and `value` are present. Do not open SQLite or another database product.

### Implementation for User Story 2

- [X] T018 [P] [US2] Create the `app_meta` model in `backend/app/models.py`. Columns, quoted from `data-model.md`: `id` integer, primary key, generated by the database; `key` text, required, unique; `value` text, required. A row without `key` or `value` is rejected. Two rows with the same `key` are rejected. No foreign keys. The table may contain zero rows. Do not seed coaching data. Do not model calls, templates, scores, or agents.
- [X] T019 [P] [US2] Add `backend/alembic.ini` and `backend/alembic/env.py`. `env.py` reads `DATABASE_URL`, builds an async engine, and calls `run_sync` only inside the migration connection. The request path must not use that synchronous bridge. Include offline SQL mode so T017 can call it.
- [X] T020 [US2] Add the first revision at `backend/alembic/versions/<revision_id>_create_app_meta.py` so T017 passes. `down_revision` is empty. Upgrade creates only `app_meta` as specified in T018. Upgrade does not drop an existing table. Do not seed rows.
- [X] T021 [US2] Implement `migrate` in `backend/app/commands.py` so T016 passes. Run `alembic upgrade head`. On an empty database, exit 0 after creating `app_meta` and the Alembic version row. On a database already at head, exit 0 without changing `app_meta` or deleting rows. If `app_meta` already exists with a different shape, exit non-zero and leave existing rows in place. Do not start the API.
- [X] T022 [P] [US2] Document `uv run migrate` in `README.md` and `docs/SETUP.md`. From `backend/`, with `DATABASE_URL` aimed at PostgreSQL 18: the first run creates `app_meta`, the second run exits 0 and does not change the schema, and the command does not drop existing data or start the API.

**Checkpoint**: User Stories 1 and 2 both work. Health still reports `ok` / `connected` after the schema step.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Docs that span both stories, and the quickstart check

- [X] T023 [P] Update the tech stack table in `README.md` from PostgreSQL 16 to PostgreSQL 18, and describe uv as the only Python installer. Leave the frontend on npm.
- [X] T024 [P] Update `docs/SETUP.md` so the PostgreSQL 18 volume is the new volume mounted at `/var/lib/postgresql`. State that `uv run migrate` must not delete the old volume, and that `docker compose down -v` is a manual wipe rather than the schema step.
- [X] T025 Run `specs/001-adopt-uv-migrations/quickstart.md` from the repository root and fix any failure in the files the tasks above already name

---

## Phase 6: Clean Architecture Alignment

**Purpose**: Move the feature's health check, `app_meta` rules, persistence, and command wrappers into the layered layout required by constitution Principle VII and FR-013. Phases 1–5 remain the functional baseline; this phase makes the dependency rule hold in source.

**⚠️ CRITICAL**: Domain and application packages MUST NOT import FastAPI, SQLAlchemy, or Alembic. Route handlers MUST NOT embed `SELECT 1` or other connectivity logic.

### Tests for Clean Architecture

> Write these tests first and confirm they fail before the implementation tasks.

- [X] T026 [P] Add a failing unit test in `backend/tests/test_domain_app_meta.py` that constructs the domain `AppMeta` entity from `backend/app/domain/app_meta.py`. Assert a missing or empty `key` or `value` is rejected. Assert a valid entity exposes `key` and `value`. Do not import SQLAlchemy in this test module.
- [X] T027 [P] Add a failing unit test in `backend/tests/test_check_health.py` that calls `CheckHealth` from `backend/app/application/check_health.py` with a fake `DatabaseProbe`. When the probe reports reachable, assert the use case returns the healthy outcome. When the probe reports failure, assert the healthy outcome is not returned. Do not import FastAPI or SQLAlchemy in this test module.
- [X] T028 [P] Add a failing unit test in `backend/tests/test_health_route.py` that calls the FastAPI health route adapter in `backend/app/adapters/http/health.py` with a fake `CheckHealth` (or injected probe wired through the use case). Assert the adapter returns `{"status": "ok", "database": "connected"}` on success and does not execute SQL itself.

### Implementation for Clean Architecture

- [X] T029 [P] Create `backend/app/domain/app_meta.py` with the pure `AppMeta` entity so T026 passes. No FastAPI, SQLAlchemy, or Alembic imports.
- [X] T030 [P] Create `backend/app/application/ports.py` with a `DatabaseProbe` protocol (reachable / not reachable). Create `backend/app/application/check_health.py` so T027 passes. Application modules import domain and ports only.
- [X] T031 [P] Move async engine/session helpers from `backend/app/db.py` to `backend/app/adapters/persistence/engine.py`. Move the SQLAlchemy `AppMeta` mapping for this feature from the flat models module into `backend/app/adapters/persistence/models.py`. Add `backend/app/adapters/persistence/database_probe.py` that implements `DatabaseProbe` with an async session. Update Alembic `env.py` imports to the new model path without changing migration revision ids.
- [X] T032 [P] Create `backend/app/adapters/http/health.py` so T028 passes. The route is `async def`, depends on the use case (or a factory that builds it with the SQLAlchemy probe), and returns the health contract body. Remove inline health SQL from `backend/app/main.py`; `main.py` only wires the app and includes the health router.
- [X] T033 [P] Move `serve`, `migrate`, and `test` from `backend/app/commands.py` to `backend/app/infrastructure/commands.py`. Update `[project.scripts]` in `backend/pyproject.toml` to the new module path. Keep command behavior identical. Update `backend/tests/test_commands.py` imports.
- [X] T034 Remove or shrink the old flat modules (`backend/app/db.py`, and any health/SQL left in `backend/app/main.py` or a flat `commands.py`) so imports resolve only through the layered packages. Do not move coaching/call tables in this task beyond what is required to keep existing imports working; coaching modules outside this feature's layout are later work.
- [X] T035 Run `uv run test` and `specs/001-adopt-uv-migrations/quickstart.md`. Confirm health still returns `ok` / `connected`, migrate is unchanged, and no domain or application module imports FastAPI, SQLAlchemy, or Alembic.

**Checkpoint**: Gate VII holds for this feature's packages. Health and `app_meta` rules are testable without the web framework or ORM.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies. Start here.
- **Foundational (Phase 2)**: Depends on Phase 1. Blocks both user stories.
- **User Story 1 (Phase 3)**: Depends on Phase 2. Does not depend on User Story 2.
- **User Story 2 (Phase 4)**: Depends on Phase 2. Does not depend on User Story 1's health or Compose command. It needs the PostgreSQL 18 service from T009.
- **Polish (Phase 5)**: Depends on the user stories you intend to ship.
- **Clean Architecture (Phase 6)**: Depends on Phases 3 and 4 (health and `app_meta` exist). May follow Phase 5.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Phase 2. No dependency on User Story 2. The health check does not read `app_meta`.
- **User Story 2 (P2)**: Starts after Phase 2. `uv run migrate` does not start the API, so it is testable without User Story 1's `serve` command.

### Within Each User Story

- Tests are written and failing before implementation
- Models before the Alembic revision (T018 before T020)
- Alembic env before the revision and before `migrate` (T019 before T020 and T021)
- `serve` does not wait on the migration, and `migrate` does not wait on `serve`

### Parallel Opportunities

- T003 and T004 can run in parallel with each other. T002 waits on T001.
- T005, T006, and T009 can run in parallel. T007 then follows T005. T008 then follows T006.
- T010 and T011 can run in parallel. After they fail, T012, T013, T014, and T015 can run in parallel.
- T016 and T017 can run in parallel. After they fail, T018, T019, and T022 can run in parallel. T020 and T021 then follow T019 (T020 also follows T018).
- T023 and T024 can run in parallel. T025 follows the stories intended to ship.
- T026, T027, and T028 can run in parallel. After they fail, T029, T030, and T033 can run in parallel. T031 and T032 follow T030. T034 follows T031–T033. T035 is last.

---

## Parallel Example: User Story 1

```bash
# Tests together:
Task: "T010 failing serve test in backend/tests/test_commands.py"
Task: "T011 failing health test in backend/tests/test_health.py"

# Implementation together, after those tests fail:
Task: "T012 serve in backend/app/commands.py"
Task: "T013 async health in backend/app/main.py"
Task: "T014 uv run serve in docker-compose.yml"
Task: "T015 install docs in README.md and docs/SETUP.md"
```

---

## Parallel Example: User Story 2

```bash
# Tests together:
Task: "T016 failing migrate test in backend/tests/test_commands.py"
Task: "T017 failing offline SQL test in backend/tests/test_migration_sql.py"

# Independent implementation after those tests fail:
Task: "T018 app_meta model in backend/app/models.py"
Task: "T019 Alembic env in backend/alembic.ini and backend/alembic/env.py"
Task: "T022 migrate docs in README.md and docs/SETUP.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: `uv sync`, then the health screen against PostgreSQL 18
5. Demo the locked install before adding the schema revision

### Incremental Delivery

1. Setup + Foundational → lockfile, `uv run test`, PostgreSQL 18
2. User Story 1 → locked install and `uv run serve` → validate independently (MVP)
3. User Story 2 → `uv run migrate` creates `app_meta` → validate the second run is a no-op
4. Polish → README, setup notes, and `quickstart.md`
5. Clean Architecture → layered packages for domain, application, adapters, infrastructure → validate gate VII

### Parallel Team Strategy

1. Everyone finishes Setup and Foundational together
2. Then one person takes User Story 1 (`serve`, health, Compose command) and another takes User Story 2 (model, Alembic, `migrate`)
3. They share command modules only in sequence: `test` in T008, `serve` in T012, `migrate` in T021, then the move to `infrastructure/commands.py` in T033
4. They share `docker-compose.yml` only in sequence: database in T009, backend command in T014
5. Clean Architecture (Phase 6) is shared work after both stories land

---

## Notes

- [P] tasks use different files and do not depend on incomplete tasks
- [US1] and [US2] map to the two stories in `spec.md`
- Every new function ships with a test that calls it: domain `AppMeta`, `CheckHealth`, `DatabaseProbe` adapter, `get_engine` / `get_session`, `test`, `serve`, the health route adapter, `migrate`, and the Alembic offline migration path
- `uv run serve` stays a long-running API process. Schema apply stays `uv run migrate`
- Do not add a formatter, a second Python installer, a frontend uv command, or coaching tables
- Do not leave health SQL or `app_meta` validation rules inside FastAPI routers or ORM models once Phase 6 is done
