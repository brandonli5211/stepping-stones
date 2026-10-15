# Setup: run Stepping Stones on your laptop

Goal: database, API and frontend all running, and you can see two sample calls in the browser. Takes about 20 minutes the first time.

You will have **3 things running** at the end, each in its own terminal:

| Terminal | Runs | Address |
|----------|------|---------|
| 1 | Postgres (database) | `localhost:5432` |
| 2 | FastAPI (backend) | <http://localhost:8000> |
| 3 | Vite (frontend) | <http://localhost:5173> |

## 0. Install these once

| Tool | Version | Check with |
|------|---------|-----------|
| Git | any | `git --version` |
| Python | 3.11 or newer | `python --version` (Mac: `python3 --version`) |
| Node.js | 20 or newer (LTS) | `node --version` |
| Docker Desktop | any | `docker --version` |

No Docker? See [Postgres without Docker](#postgres-without-docker) below.

```sh
git clone https://github.com/brandonli5211/stepping-stones.git
cd stepping-stones
```

## 1. Start the database

```sh
docker compose up -d
```

This downloads Postgres 16 and starts it in the background with user `stepping`, password `stepping`, database `stepping_stones`. Data survives restarts. To stop it: `docker compose down`.

## 2. Start the backend

```sh
cd backend
python -m venv .venv
```

Activate the virtual environment (you'll do this every time you open a new terminal for the backend):

- **Mac / Linux:** `source .venv/bin/activate`
- **Windows PowerShell:** `.venv\Scripts\Activate.ps1`
- **Windows cmd:** `.venv\Scripts\activate.bat`

Your prompt should now start with `(.venv)`. Then:

```sh
pip install -r requirements.txt
cp .env.example .env            # Windows: copy .env.example .env
python -m scripts.seed          # creates the tables and loads 2 sample calls
uvicorn app.main:app --reload
```

You should see `Loaded 2 calls…` and then `Uvicorn running on http://127.0.0.1:8000`.

**Check:** open <http://localhost:8000/docs>. Click `GET /api/conversations` → **Try it out** → **Execute**. You should see `HVB-0001` and `DEMO-0002`.

`--reload` restarts the server every time you save a Python file.

## 3. Start the frontend (new terminal)

```sh
cd frontend
npm install
npm run dev
```

**Check:** open <http://localhost:5173>. You should see a table with 2 calls; click one to see its transcript.

## 4. Run the tests

```sh
cd backend      # with .venv activated
pytest
```

## Daily routine

```sh
git pull
docker compose up -d
# terminal 2
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload
# terminal 3
cd frontend && npm run dev
```

If someone changed `requirements.txt` or `package.json`, re-run `pip install -r requirements.txt` / `npm install`.

## Changing the database

`seed.py` creates tables that don't exist yet, but it does **not** change tables that already exist. While we're early, if you change `models.py`, reset the database:

```sh
docker compose down -v      # deletes all data
docker compose up -d
cd backend && python -m scripts.seed
```

(When this gets annoying we'll add Alembic for migrations.)

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `connection refused` on port 5432 | Database isn't running: `docker compose up -d`. Check with `docker compose ps`. |
| `port 5432 is already allocated` | You already have Postgres installed and running. Either stop it, or use it (see below). |
| `ModuleNotFoundError: No module named 'app'` | Run commands from inside `backend/`. |
| `ModuleNotFoundError: fastapi` | Your venv isn't activated (no `(.venv)` in the prompt). |
| Windows: `running scripts is disabled` when activating | Run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Frontend says "Could not load calls" | The backend isn't running on port 8000, or `FRONTEND_ORIGIN` in `backend/.env` doesn't match the frontend address. |
| Frontend shows "No calls yet" | Run `python -m scripts.seed` in `backend/`. |

## Postgres without Docker

1. Install Postgres 16: Mac `brew install postgresql@16 && brew services start postgresql@16`; Windows: installer from <https://www.postgresql.org/download/windows/>.
2. Create the user and database (`psql -U postgres` on Windows, `psql postgres` on Mac):

   ```sql
   CREATE USER stepping WITH PASSWORD 'stepping';
   CREATE DATABASE stepping_stones OWNER stepping;
   ```

3. Continue from step 2. The default `DATABASE_URL` in `.env` already points at `localhost:5432`.

## Useful database commands

```sh
docker compose exec db psql -U stepping stepping_stones
```

```sql
\dt                                  -- list tables
select * from conversations;
select speaker, text from turns where conversation_id = 'HVB-0001' order by turn_number;
\q                                   -- quit
```
