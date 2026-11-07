# Contract: Backend uv commands

All commands run from `backend/` unless noted. They use the lockfile.
They do not read `requirements.txt`.

## `uv sync`

Installs the locked backend dependencies into the project environment.

- Success: the command exits 0 and the environment matches `uv.lock`.
- Missing lock, or a lock that does not match `pyproject.toml`: the
  command exits non-zero and does not install a different set.

### `uv sync --frozen`

Same as `uv sync`, and it will not update the lock. This is what the
image runs.

## `uv run serve`

Starts the API process and keeps running.

- Binds `0.0.0.0` port `8000`.
- Reloads when backend source changes.
- Process is the one Compose starts. Compose does not call uvicorn except
  through this command.
- A second Compose port mapping may publish a different host port. The
  process inside the container still listens on `8000`.

Success for this contract is a running process, not an exit code.

## `uv run migrate`

Applies the schema history through head.

- Empty database: exits 0. `app_meta` exists. The Alembic version row
  points at the single revision in this feature.
- Database already at head: exits 0. `app_meta` is unchanged. No data is
  deleted.
- `app_meta` already exists with a different shape: exits non-zero. Rows
  that were already there are still there.
- Does not start the API.

## `uv run test`

Runs the backend test suite in the project environment.

- Exits 0 when every test passes.
- Exits non-zero when a test fails.
- Does not start the API and does not require the Compose stack.
- Does not create a database of another product. The migration test checks
  generated SQL, as described in the plan's research.

## Compose

The backend service command is `uv run serve`. The database service image
is PostgreSQL 18. The frontend service is unchanged and still installs
with npm.
