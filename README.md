# Stepping Stones

> **README status: outline.** Each section has an owner and prompts. Replace the prompts (the `> ✏️` lines) with real content, then delete this note.

Post-call coaching for contact-centre agents on templated calls. After each call, Stepping Stones shows which required steps the agent completed, flags the ones they missed, scores step completion, and tracks improvement over time.

Built by **TOo BAD** for UofT FTL Cohort 9 × Genesys.

---

## What it is
**Owner:** ______

> ✏️ 3–5 sentences. The problem (feedback is late, vague and sampled; a polite call can still skip required steps), who it's for (new hires, current agents, coaches/QA), and where it fits (after the call, before the agent's next shift). Source: `PRODUCT_DIRECTION.md` in our Claude project.

## Features
**Owner:** ______

### MVP
> ✏️ One line each on what it does and why it matters to an agent. Starting list:
> - Templates: required steps per task type (starting with 1–3 of: replace card, transfer money, pay bill)
> - Post-call summary: steps completed vs missed, with flags
> - Step-completion score (completed ÷ required)
> - Progress over time per agent
> - Load agent calls from HarperValleyBank JSON

### Later
> ✏️ Peer Model Answer, weighted/critical steps, conversation branches, better detection.

### How scoring works
> ✏️ Short worked example (the replace-card 3/4 = 75% table).

## Tech stack
**Owner:** ______

| Layer | Tech |
|-------|------|
| Data loading | Python |
| Database | PostgreSQL 16 |
| Backend | FastAPI (Python), SQLAlchemy |
| Frontend | React + Vite |

Why we chose it and how the pieces connect: [docs/TECH_STACK.md](docs/TECH_STACK.md).

> ✏️ Optional: one-paragraph summary of the "why" in your own words.

## Getting started

Full guide: [docs/SETUP.md](docs/SETUP.md). Short version:

```sh
docker compose up -d                                   # database
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && cp .env.example .env
python -m scripts.seed && uvicorn app.main:app --reload   # API → http://localhost:8000/docs
cd ../frontend && npm install && npm run dev           # app → http://localhost:5173
```

## Project structure

```
stepping-stones/
├── backend/            FastAPI app (Python)
│   ├── app/            main.py, models, schemas, routers/ (later: services/)
│   ├── scripts/        seed.py — loads calls into Postgres
│   └── tests/
├── frontend/           React app (Vite)
│   └── src/            pages/, components/, api/
├── data/               sample calls (HVB format)
├── docs/               TECH_STACK, SETUP, UI_OUTLINE
└── docker-compose.yml  Postgres for local dev
```

## Dataset
**Owner:** ______

> ✏️ HarperValleyBank: what it gives us (task types, agent/customer turns, agent IDs, `captured_by_agent`, dialog acts) and what we add (templates, checker, score, UI). Note it's role-play data. Cite: Wu et al. 2020, arXiv:2010.13929, CC BY 4.0.

## How we work
**Owner:** ______

> ✏️ Branch naming (e.g. `feature/score-card`), PR rules (1 reviewer?), how tickets on the Kanban board link to branches, where we talk.

## Contributors

| Name | Role / focus | GitHub |
|------|--------------|--------|
| Anton | | |
| Brandon | | @brandonli5211 |
| Diego | | |
| Ozan | | |
| Tugra | | |

## Links
**Owner:** ______

- Kanban board: ______
- Presentation deck ("Filling the Gaps: Fixing Missing Steps in Agent Conversations"): ______
- HarperValleyBank dataset: <https://github.com/cricketclub/gridspace-stanford-harper-valley>
- Genesys partner docs: <https://github.com/marcomarchesanogenesys/uoft-ftli-2026-genesys-docs>
- UI outline: [docs/UI_OUTLINE.md](docs/UI_OUTLINE.md)
