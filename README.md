# Stepping Stones

Post-call coaching for contact-centre agents. After a templated call, it shows which required steps the agent completed, which ones they missed, and a score.

**TOo BAD** · UofT FTL Cohort 9 × Genesys

The app runs as **React → FastAPI → PostgreSQL**. That replaces the first proof of concept (Python → MongoDB → Java Spring Boot → React).

---

## Tech stack

| Piece | What it is | Why it is here |
| --- | --- | --- |
| React + Vite | The agent screen, at http://localhost:5173 | The UI stays a client. It shows the result. It does not decide if a step was completed. |
| FastAPI | The API, at http://localhost:8000/docs | Loading calls, checking steps, scoring, and the API are all Python. `/docs` lists every endpoint. |
| PostgreSQL 18 | The database | A transcript is one nested document. Progress questions are filters: this agent, this task type, this step. SQL does both. Postgres can still store loose JSON. |
| uv | The only Python installer | Backend dependencies install from `backend/uv.lock`. The frontend still installs with npm. |
| Docker Compose | Starts all three | One command for local development. The API process is `uv run serve`. |

Python was chosen over a second Java service because the product is a checker. The rubric and the service that explains it should be the same code.

## Setup and run

### Prerequisites

| Tool | Needed for | Install |
| --- | --- | --- |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose v2) | Running the full stack | Required |
| [uv](https://docs.astral.sh/uv/) 0.11.32 | Backend install, migrate, and tests on the host | Optional if you only use Compose |
| Node.js 20+ / npm | Frontend install outside Compose | Optional if you only use Compose |

### Run the stack (recommended)

```bash
git clone https://github.com/brandonli5211/stepping-stones.git
cd stepping-stones
docker compose up --build
```

The first build takes a few minutes. Compose brings up PostgreSQL 18, starts the API with `uv run serve`, and starts the React app with npm.

| Service | URL |
| --- | --- |
| App | http://localhost:5173 |
| API docs | http://localhost:8000/docs |
| Postgres | `localhost:5432` |

Open the app. You should see the **Your calls** page. Check the API and database at http://localhost:8000/api/health, which should return `{"status":"ok","database":"connected"}`.

Handy Compose commands:

```bash
docker compose up -d --build     # background
docker compose logs -f backend   # follow API logs
docker compose down              # stop
```

If port 8000 or 5432 is already taken, copy `.env.example` to `.env` and set `BACKEND_PORT` or `POSTGRES_PORT`. Details are in [docs/SETUP.md](docs/SETUP.md).

### Backend on the host (optional)

Use this when you want to install, migrate, or test the API without going through the frontend container. From `backend/`:

```bash
uv sync                  # install from backend/uv.lock
uv run migrate           # apply starting schema (creates app_meta)
uv run serve             # API on http://localhost:8000
uv run test              # backend tests
```

`uv sync` installs the locked set in `backend/uv.lock`. `uv sync --frozen` exits non-zero when that lock is missing or no longer matches `backend/pyproject.toml`.

Point `DATABASE_URL` at PostgreSQL 18 before `uv run migrate`. The first migrate creates `app_meta`; a second run exits 0 and does not change the schema. Migrate does not drop data and does not start the API.

A quick path that starts only the database in Docker, then migrates from the host:

```bash
docker compose up -d db
cd backend
export DATABASE_URL=postgresql+psycopg://stepping:stepping@localhost:5432/stepping_stones
uv sync
uv run migrate
uv run serve
```

### Frontend on the host (optional)

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL` to the API base URL if it is not `http://localhost:8000`. The frontend stays on npm; there is no uv command for `frontend/`.

Set `VITE_SAMPLE_DATA=true` (in `.env` for Compose, or in your shell) to have every screen use the example responses in `frontend/src/api/sampleData.js` instead of the API. Use it to build a screen before its endpoint exists.

## Project structure

```
backend/             FastAPI app (health check today)
frontend/            React app (health check today)
docs/SETUP.md        How to run it, and port conflicts
docker-compose.yml   Postgres + API + UI
```

Templates, the step checker, and the real coaching screens are not in this starter yet.

## How to fill in your section

Four sections below are blank on purpose. Each one has a suggested owner. Claim yours, edit only that section, and open a pull request.

1. On GitHub, open `README.md`, click the pencil, and choose **Create a new branch**.
2. Name the branch `docs/readme-<section>` (for example `docs/readme-features`).
3. Replace the suggestion under your section with a few short sentences. Put your name on the owner line.
4. Open a pull request titled `README: <section>` and ask one teammate to review it.

---

## What it is

**Suggested owner:** Anton 

Stepping Stones is a post-call coaching tool for contact-centre agents. Feedback today usually comes late, is vague, and is based on only a small sample of calls, so agents rarely learn exactly what to change. A polite call, even one the customer rates 10/10, can still skip required steps, so customer scores alone don’t show whether an agent followed the process. Stepping Stones checks each call’s transcript against a template for its task type and shows which required steps the agent completed, which they missed, and an overall score. It helps new hires learn the process, current agents see their progress over time, and coaches focus on specific gaps. It runs after the transcript exists and before the agent’s next shift, not live during the call.

## Features

**Owner:** Diego

**First version**

- **Templates:** an ordered list of required steps for 1–3 HarperValleyBank task types, starting with Transfer money and Replace card.
- **Post-call review:** for one call, which required steps the agent completed, which they missed, a flag for each missed step, and a score.
- **Procedures:** the steps each task type expects, so agents can check them before their next call.
- **Progress:** an agent's step-completion rate week over week, and the steps they skip most.
- **Calls:** loaded from the HarperValleyBank transcripts.

**Later**

- A peer example for a missed step, taken from another call where the step was done.
- Weighted steps, so missing a key step costs more than missing a courtesy step.
- Branching calls, where the required steps depend on what the caller asks for.
- Better detection of whether a step was done.

**Worked score.** The score is the number of required steps completed divided by the number of required steps. In the replace-card example, the agent greets the caller, collects the card type and closes the call, but never says the new card was ordered. That is 3 of 4 steps, so the score is 75%, in the Getting there band (60–84).

## Dataset

**Suggested owner:** [Someone write this] 

**How to fill this in:** what HarperValleyBank already gives us, and what we add.

- It gives task type, agent id, separate agent and customer turns, and what the agent logged.
- We add the template, the checker, the score, and the screen.
- Say that the calls are role-play, and cite Wu et al. 2020, arXiv:2010.13929, CC BY 4.0.
- Dataset: https://github.com/cricketclub/gridspace-stanford-harper-valley

_Replace this list with your version._

## How we work

**Owner:** Ozan

- **Branches:** `type/issue-number-short-name`, for example `feat/22-app-shell` or `docs/readme-dataset`. Types: `feat`, `fix`, `docs`, `chore`.
- **Pull requests:** one issue per PR. Put `Closes #<issue number>` in the description so the issue closes when the PR merges. For a page, add a screenshot next to its Figma frame.
- **Reviews:** at least one teammate approves every PR before it merges. Nobody merges their own PR without a review.
- **Board:** a ticket moves Backlog → Ready → In progress → In review → Done. Move it to In progress when you start, In review when the PR is open, and Done when it merges.
- **Questions:** ask in the team group chat. If it's about a specific ticket, comment on the issue so the answer stays with the work.

---

## Contributors

Add your focus on the same pull request as your section.

| Name | Focus | GitHub |
| --- | --- | --- |
| Brandon | TBA| [@brandonli5211](https://github.com/brandonli5211) |
| Diego | Frontend: Procedures | [@DiegoFigarella](https://github.com/DiegoFigarella) |
| Ozan | TBA | [@ozantimur](https://github.com/ozantimur) |
| Anton | TBA | [@thlasagna](https://github.com/thlasagna) |
| Tugra | TBA | [@TroubleVaser](https://github.com/TroubleVaser) |

## Links

- Team repo: https://github.com/brandonli5211/stepping-stones
- Figma: [Stepping Stones — UI Mockup](https://www.figma.com/design/tgQYPY631Tg5njDsoBYGNJ/Stepping-Stones-%E2%80%94-UI-Mockup?node-id=12-99)
- Dataset: https://github.com/cricketclub/gridspace-stanford-harper-valley
