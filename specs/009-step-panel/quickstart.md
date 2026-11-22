# Quickstart: Call detail step panel

## 1. What this change adds

Open `/calls/1` after the demo calls are loaded. The right side lists the seven required steps. "Submit and confirm transfer" is selected, its 0:33 quote and coaching sentence are on the panel, and From / To show as reversed. The score and the transcript were already there.

## 2. Load the screens without a model key

From `backend/`, with Postgres running (`docker compose up -d db` from the repo root) and `DATABASE_URL=postgresql+psycopg://stepping:stepping@localhost:5432/stepping_stones`:

```bash
uv sync
uv run migrate
uv run python -m app.load_calls ../sample/demo_48 --demo-results
uv run apply-demo-results ../sample/demo_48/results.csv
uv run serve
```

Then, from `frontend/`:

```bash
npm install
npm run dev
```

Open `http://127.0.0.1:5173/calls/1`. Sample mode (`npm run dev` with no API) also shows this call, because the sample answer includes the steps.

## 3. Checks

```bash
cd frontend && npm test && npm run lint && npm run build
```

## 4. A live score is a separate command

`uv run analyze` needs `OPENAI_API_KEY` in the shell environment. It is not required for the screens above. The demo calls already have a stored result, so replacing call 1 needs `--force`.
