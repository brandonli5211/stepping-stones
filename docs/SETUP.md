# Local setup

You only need [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose v2).

```bash
git clone https://github.com/brandonli5211/stepping-stones.git
cd stepping-stones
docker compose up --build
```

The first build takes a few minutes. When it settles:

| Service  | URL                          | Port |
| -------- | ---------------------------- | ---- |
| Frontend | http://localhost:5173        | 5173 |
| Backend  | http://localhost:8000/docs   | 8000 |
| Postgres | `localhost`                  | 5432 (or `POSTGRES_PORT`) |

The frontend page should show **Backend health: ok (database: connected)**.
If it does, all three services are talking to each other.

Compose starts the API with `uv run serve`. The frontend still installs and starts with npm. There is no uv command for `frontend/`.

To install the locked backend on the host, from `backend/`:

```bash
uv sync
```

That installs the versions in `backend/uv.lock`. `uv sync --frozen` exits non-zero when the lock is missing or does not match `backend/pyproject.toml`.

PostgreSQL 18 uses a new volume, `pg18`, mounted at `/var/lib/postgresql`. The previous `pgdata` volume is left in place and is not attached. `uv run migrate` must not delete that old volume.

From `backend/`, with `DATABASE_URL` aimed at that PostgreSQL 18 database:

```bash
uv run migrate
```

The first run creates `app_meta`. The second run exits 0 and does not change the schema. The command does not drop existing data, and it does not start the API.

Code changes in `backend/` and `frontend/` reload automatically.

## Handy commands

```bash
docker compose up -d --build     # run in the background
docker compose logs -f backend   # follow one service's logs
docker compose down              # stop everything
docker compose down -v           # manual wipe of volumes, not the schema step
```

## Troubleshooting

- **Port 8000 already allocated:** copy `.env.example` to `.env`, set `BACKEND_PORT=8001`, then run `docker compose up --build` again. The frontend follows automatically, and the API is then at http://localhost:8001/docs.
- **Port 5432 already in use:** a local Postgres is often already listening there. Copy `.env.example` to `.env`, set `POSTGRES_PORT=5430`, then run `docker compose up --build` again. Connect from the host at `localhost:5430`. The backend still reaches Postgres inside Docker on port 5432.
- **Port 5173 in use:** stop whatever uses it, or change the left-hand frontend port in `docker-compose.yml`.
- **Different DB credentials:** copy `.env.example` to `.env` and edit it.
