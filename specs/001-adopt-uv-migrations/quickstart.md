# Quickstart: Locked Backend Setup and Starting Schema

Validation for this feature. Commands assume the repo root unless a step
says `backend/`. Details of the commands are in
[contracts/uv-commands.md](contracts/uv-commands.md). The table shape is in
[data-model.md](data-model.md).

## Prerequisites

- Docker Desktop (or Docker Engine with Compose v2)
- uv 0.11.32 available on the host for the non-Docker checks
- No application data that must survive a PostgreSQL 18 move. A volume
  created by PostgreSQL 16 cannot be opened by PostgreSQL 18. Leave that
  volume in place. Point this stack at a new volume. Do not delete the old
  one as part of these steps.

## 1. Locked install

From `backend/`:

```bash
uv sync
```

Expected: the command exits 0 and uses `uv.lock`. Deleting `uv.lock` and
running `uv sync --frozen` exits non-zero.

Repeat `uv sync` in a second empty environment from the same revision.
Expected: the installed versions match. Zero version differences.

## 2. Tests without the stack

From `backend/`:

```bash
uv run test
```

Expected: the suite exits 0. The migration check reports that the revision
creates `app_meta`. Domain and `CheckHealth` tests pass without FastAPI or
SQLAlchemy imports. No Compose services are required.

## 3. Schema on an empty database

Start only the database (PostgreSQL 18), then apply the history from
`backend/` with `DATABASE_URL` aimed at that database:

```bash
docker compose up -d db
uv run migrate
uv run migrate
```

Expected:

- The first `uv run migrate` exits 0 and creates `app_meta`.
- The second exits 0 and does not change the table.
- The table's columns match [data-model.md](data-model.md).
- Existing rows, if a later check inserts any, are still present after the
  second run.

## 4. Compose starts the API through uv

```bash
docker compose up --build
```

Expected:

- The backend process was started by `uv run serve`, not by a bare
  uvicorn command.
- The database image is PostgreSQL 18.
- The site at http://localhost:5173 shows that the backend is up and the
  database is connected.
- `GET /api/health` returns `200` with `status` `ok` and `database`
  `connected`. See [contracts/health.md](contracts/health.md).

If the API port or the database port is already taken, use the existing
`.env` overrides. Those overrides do not change the uv command or the
PostgreSQL major version.

## 5. Frontend packages were not retargeted

The frontend still installs and starts with npm. This quickstart does not
add a uv command for it.
