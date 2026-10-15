# Tech stack: what we use, why, and how to read the code

**Stack:** Python · FastAPI · PostgreSQL · React (Vite)

```
 data/sample_calls.json
        │  backend/scripts/seed.py  (Python reads JSON, writes rows)
        ▼
 ┌──────────────┐   SQL    ┌──────────────────┐   JSON over HTTP   ┌─────────────────┐
 │  PostgreSQL  │ ◄──────► │  FastAPI backend │ ◄────────────────► │  React frontend │
 │  port 5432   │          │  port 8000       │                    │  port 5173      │
 └──────────────┘          └──────────────────┘                    └─────────────────┘
   stores calls,             reads/writes the DB,                    what agents see
   turns, (later)            runs template checks                    in the browser
   templates + scores        + scoring, serves /api/*
```

## What each piece does

| Layer | Tech | Job in Stepping Stones | Where it lives |
|-------|------|------------------------|----------------|
| Data loading | Python script | Read HarperValleyBank (HVB) call JSON and save it into the database | `backend/scripts/seed.py`, `data/` |
| Database | PostgreSQL | Store calls, turns, and later templates, step results and scores | runs in Docker (`docker-compose.yml`) or installed locally |
| Backend / API | Python + FastAPI | Answer requests like "give me call HVB-0001"; later: check a call against its template and score it | `backend/app/` |
| Frontend | React + Vite | The agent dashboard: call list, post-call summary, progress | `frontend/src/` |

## Why this stack (replacing MongoDB + Java Spring Boot)

Our proof of concept used Python → MongoDB → Spring Boot → React. That proved data could move end to end. For the real product we're switching. Edit these if the team's reasons differ:

1. **One backend language instead of two.** The old setup used Python for loading data and Java for the API. Now loading, step detection and the API are all Python, so everyone can read the whole backend.
2. **Step detection is text processing, and Python is good at that.** Our MVP rules (keywords, patterns, checking `captured_by_agent`) are a few lines of Python. If we try smarter detection later, the libraries are in Python too.
3. **Our data is now relational.** Agents have many calls, calls have many turns, calls have one result per template step, and progress means "completion rate per agent per week". Those are joins and `GROUP BY` queries, which is what SQL is built for. Postgres still has `JSONB` columns for loose data like `captured_by_agent`, so we keep the flexibility we had with MongoDB.
4. **FastAPI is quick to learn and documents itself.** Open <http://localhost:8000/docs> and you get a page listing every endpoint that you can try from the browser. Type hints + Pydantic check the data going in and out for us.
5. **React stays.** Same frontend as the proof of concept, now started with Vite (Create React App is no longer maintained).

**Trade-off to be honest about:** Spring Boot was picked for CSC207's Java OOP. We can keep the same OOP design in Python. The planned classes (`Template`, `Step`, `StepDetector`, `CallScorer`, `ProgressTracker`) work the same way as Python classes.

## How one request flows (read the code in this order)

Example: you open <http://localhost:5173/calls/HVB-0001>.

1. **`frontend/src/App.jsx`** sees the URL `/calls/HVB-0001` and shows `CallDetailPage`.
2. **`frontend/src/pages/CallDetailPage.jsx`** calls `getCall("HVB-0001")`.
3. **`frontend/src/api/client.js`** sends `GET http://localhost:8000/api/conversations/HVB-0001`.
4. **`backend/app/main.py`** receives it and hands it to the conversations router.
5. **`backend/app/routers/conversations.py`** → `get_conversation()` asks the database for that call and its turns.
6. **`backend/app/models.py`** describes the `conversations` and `turns` tables, so SQLAlchemy can turn rows into Python objects.
7. **`backend/app/schemas.py`** decides which fields go back as JSON.
8. Back in React, **`components/Transcript.jsx`** draws each turn.

## Backend files

| File | Read it to learn… |
|------|-------------------|
| `app/main.py` | How the app starts, CORS, which routers are plugged in |
| `app/config.py` | Settings from `.env` (database URL, frontend address) |
| `app/database.py` | How we connect to Postgres; `get_db` gives each request a session |
| `app/models.py` | The database tables |
| `app/schemas.py` | The JSON shapes the API returns |
| `app/routers/conversations.py` | The actual endpoints |
| `scripts/seed.py` | How JSON calls become database rows |
| `tests/test_health.py` | A minimal test to copy |

**Key words:** *ORM* (SQLAlchemy) = write Python classes instead of raw SQL. *Model* = a table. *Schema* = an API response shape. *Router* = a group of endpoints. *Session* = one conversation with the database.

## Frontend files

| File | Read it to learn… |
|------|-------------------|
| `src/main.jsx` | Where React starts |
| `src/App.jsx` | Layout + routes (one route per page) |
| `src/pages/` | One file per page |
| `src/components/` | Reusable pieces used by pages |
| `src/api/client.js` | Every backend call, in one place |
| `src/hooks/useApi.js` | Loading / error / data handling for API calls |
| `src/index.css` | Colour tokens (`--color-completed`, `--color-missed`, …) and base styles |

## Database tables (so far)

```
conversations                         turns
─────────────                         ─────
id            text  PK  "HVB-0001"    id               serial PK
agent_id      text      "hvb-speaker-17"   conversation_id  text FK → conversations.id
task_type     text      "replace card"     turn_number      int
captured_by_agent jsonb {"replacement card type": "credit"}
                                       speaker          text  "agent" | "customer"
                                       text             text
                                       dialog_acts      text[]
```

Look at it yourself: `docker compose exec db psql -U stepping stepping_stones`, then `\dt` and `select * from conversations;`.

## Where new code goes

| Feature | Backend | Frontend |
|---------|---------|----------|
| Templates (required steps per task type) | `app/models.py` (`Template`, `Step` tables) or a `templates/*.json` file to start; `app/routers/templates.py` | a templates page (if we show them) |
| Step detection + scoring | `app/services/scoring.py` (`StepDetector`, `CallScorer`); save results in a `call_results` table | step checklist + score on `CallDetailPage` |
| Progress over time | `app/services/progress.py`; `GET /api/agents/{id}/progress` | progress page with a chart |
| Full HVB ingest | `scripts/load_hvb.py` | — |

Rule of thumb: **routers stay thin** (read the request, call a service, return the result); **logic goes in `services/`** so it can be tested without the web server.
