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
| PostgreSQL 16 | The database | A transcript is one nested document. Progress questions are filters: this agent, this task type, this step. SQL does both. Postgres can still store loose JSON. |
| Docker Compose | Starts all three | One command for local development. |

Python was chosen over a second Java service because the product is a checker. The rubric and the service that explains it should be the same code.

## Getting started

You need [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
git clone https://github.com/brandonli5211/stepping-stones.git
cd stepping-stones
docker compose up --build
```

| Service | URL |
| --- | --- |
| App | http://localhost:5173 |
| API docs | http://localhost:8000/docs |
| Postgres | `localhost:5432` |

The page should show **Stepping Stones** and **Backend health: ok (database: connected)**.

If port 8000 or 5432 is already taken, copy `.env.example` to `.env` and set `BACKEND_PORT` or `POSTGRES_PORT`. Details are in [docs/SETUP.md](docs/SETUP.md).

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

**Suggested owner:** [Someone write this]

**How to fill this in:** a short list, one line each, for the first version and for later.

- First version: templates for 1–3 task types, a post-call summary (completed, missed, flags, score), progress over time, and calls loaded from HarperValleyBank.
- Later: a peer example for a missed step, weighted steps, branching calls, and better detection.
- Add one worked score. The replace-card example is 3 of 4 steps = 75%, because the agent never said the card was ordered.

_Replace this list with your version._

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
| Diego | TBA | [@DiegoFigarella](https://github.com/DiegoFigarella) |
| Ozan | TBA | [@ozantimur](https://github.com/ozantimur) |
| Anton | TBA | [@thlasagna](https://github.com/thlasagna) |
| Tugra | TBA | [@TroubleVaser](https://github.com/TroubleVaser) |

## Links

- Team repo: https://github.com/brandonli5211/stepping-stones
- Figma: [Stepping Stones — UI Mockup](https://www.figma.com/design/tgQYPY631Tg5njDsoBYGNJ/Stepping-Stones-%E2%80%94-UI-Mockup?node-id=12-99)
- Dataset: https://github.com/cricketclub/gridspace-stanford-harper-valley
