# Research: Locked Backend Setup and Starting Schema

## Decision: One uv project replaces the unlocked list

**Decision**: The backend becomes a uv project at `backend/pyproject.toml`
with `backend/uv.lock` committed. `requirements.txt` is removed. Developers
install with `uv sync`. The image installs with `uv sync --frozen` and
refuses to continue if the lock and the declared dependencies disagree.

**Rationale**: uv is the required Python package manager. A lockfile is the
single recorded set both a teammate and the running app install from.
`--frozen` is the failure mode when the lock is missing or stale: uv exits
non-zero instead of resolving new versions.

**Alternatives considered**: Keep `requirements.txt` and generate it from
the lock. Rejected because that is a second dependency list. pip-tools or
Poetry. Rejected because another Python package manager is forbidden.

## Decision: Three `uv run` commands, not a task runner

**Decision**: Declare console scripts in `[project.scripts]` and run them
with uv:

| Action | Command |
| --- | --- |
| Start the API | `uv run serve` |
| Apply the schema history | `uv run migrate` |
| Run tests | `uv run test` |

`serve` starts uvicorn on `0.0.0.0:8000` with reload, matching today's
Compose command. `migrate` runs `alembic upgrade head`. `test` runs
pytest. Each script is a Python function, and each function has a unit
test that asserts the command it launches.

Docker Compose starts the backend with `uv run serve`. It does not start
the server with a bare `uvicorn` on `PATH`.

**Rationale**: uv runs a project command with `uv run <name>` once the
name is a `[project.scripts]` entry. That needs a build backend
(hatchling) so uv installs the project into the environment. uv does not
ship a shell-script task table. The three actions stay separate: the
server is long-running, the schema step must be repeatable on its own,
and tests must be runnable without starting the server.

**Alternatives considered**: Poe or another task runner. Rejected because
it adds a tool the constitution does not name, while `uv run` already
runs the three actions. One command that migrates, tests, and then serves.
Rejected because a failed test would block the server, and a second
schema apply could not be shown on its own. `uv run alembic` and
`uv run pytest` without wrappers. Rejected because the requested interface
is a uv command per action, and the wrappers are what Compose and
teammates share.

## Decision: Compose installs with uv and keeps the source mount

**Decision**: The backend image copies the uv binaries from
`ghcr.io/astral-sh/uv:0.11.32` onto the current Python 3.12 slim base.
The image runs `uv sync --frozen`. Compose keeps the `./backend:/app`
mount and stores the virtualenv in an anonymous volume at `/app/.venv`
so the mount does not hide it. The service command is `uv run serve`.
`uv run` syncs that environment from the lock before it starts the
process.

**Rationale**: The official uv Docker guide starts the process with
`uv run`, and it copies the uv binary into the application image rather
than installing uv with pip. Pinning `0.11.32` matches the uv already
installed on the developer machine. The anonymous volume is required
because a bind mount of `backend/` would otherwise replace the `.venv`
built into the image.

**Alternatives considered**: `pip install uv` inside the image. Rejected
because pip would still be the installer. Installing dependencies into
the system interpreter and dropping `uv run` at start. Rejected because
Compose must use uv to start the server. `UV_PROJECT_ENVIRONMENT` aimed
at a path outside `/app`. Equivalent in effect to the anonymous volume,
with more custom layout. The volume is the smaller change.

## Decision: PostgreSQL 18, same driver, async engine

**Decision**: The Compose database image changes from PostgreSQL 16 to
`postgres:18`. Application code uses SQLAlchemy's async engine and async
sessions with the existing psycopg driver and the URL scheme
`postgresql+psycopg://`. Alembic uses its async configuration: an async
engine, then `run_sync` only inside that connection while migrations run.
The request path does not use a synchronous engine.

**Rationale**: PostgreSQL 18 is required. psycopg 3 already speaks
asyncio through SQLAlchemy's async engine, so a second driver is
unnecessary. Alembic has no async migration API; the supported bridge is
an async connection plus `run_sync`, and that bridge is not the request
path.

**Alternatives considered**: asyncpg. Rejected because the project
already depends on psycopg and the constitution forbids an extra data
library without an amendment. Leaving the health check on a synchronous
engine. Rejected because this change edits that file, and a file this
change edits has to meet the async rule.

## Decision: One non-coaching table in the first revision

**Decision**: The first Alembic revision creates `app_meta` and nothing
else. Columns are in `data-model.md`. Coaching tables (calls, templates,
scores, agents) are not created. Applying `uv run migrate` on an empty
database creates `app_meta` and Alembic's version table. Running it
again changes nothing and exits successfully. A hand-made table of the
same name with a different shape makes Alembic stop without dropping
data.

**Rationale**: The planning request requires an initial table created by
Alembic. The specification forbids coaching records in this feature.
`app_meta` is the smallest application table that makes "a table was
created" observable, without designing the coaching model.

**Alternatives considered**: An empty revision that only creates
Alembic's version table. Rejected because that is not an application
table. Creating calls, templates, scores, or agents. Rejected by the
specification. Seeding coaching rows in the migration. Rejected for the
same reason.

## Decision: A PostgreSQL 16 data directory is not reused

**Decision**: The schema command never drops data. Moving the image to
PostgreSQL 18 does not attach the existing PostgreSQL 16 data directory.
PostgreSQL refuses to open a 16 cluster as 18. The quickstart tells the
teammate to point Compose at a new volume. Removing the old volume is a
manual choice and is not part of the schema command.

**Rationale**: The specification says a schema step must not wipe data.
A major-version server cannot read the old directory, so the safe
behavior is a new empty volume plus the migration, leaving the old
volume untouched.

**Alternatives considered**: `pg_upgrade` inside this feature. Rejected
because the current database has no application tables and the feature
does not promise an in-place major upgrade. `docker compose down -v` as
a required step. Rejected because that deletes the old volume.

## Decision: Tests call each new function without a second database

**Decision**: pytest is a backend dev dependency, run only through
`uv run test`. Unit tests call `serve`, `migrate`, and `test` and assert
the process each one launches, using a fake process runner. A test calls
the migration in Alembic's offline SQL mode and asserts the output
contains `CREATE TABLE app_meta`. The health function, once it is async,
is called with a fake session and must still report the database as
connected. Tests do not use SQLite or another database product.

**Rationale**: Every new or changed function needs a test that calls it.
Offline SQL proves the revision creates the table without standing up a
second kind of database. Live PostgreSQL remains the quickstart check.

**Alternatives considered**: pytest-alembic against a disposable
PostgreSQL. Useful later, heavier than this feature needs, and not
required to prove the revision's SQL. No tests for the thin command
wrappers. Rejected by the unit-test rule.
