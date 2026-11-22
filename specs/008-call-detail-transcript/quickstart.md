# Quickstart: Call detail page (transcript, score, flags)

How to check the page works. What it must show is in [contracts/call-detail-view.md](./contracts/call-detail-view.md); the state shapes are in [data-model.md](./data-model.md).

## Prerequisites

- Docker running, the repo cloned, `frontend/` installed with `npm ci`, `backend/` synced with `uv sync`.

## 1. Unit tests, types and build

```bash
cd frontend && npm test -- --run && npm run lint && npm run build
```

Expected: every test passes, including `src/callDetail/layering.test.ts`; `tsc --noEmit` and the build are clean.

## 2. Sample mode (no backend)

```bash
cd frontend && VITE_SAMPLE_DATA=true npm run dev
```

Open `http://localhost:5173/calls/1`. Expected: "Transfer money", the ring at 45 in "Focus here", "6 of 7 steps done right", "1 critical, 55 points lost", 9 turns with the labels from the Figma frame (0:33 wrong, 0:44 wrong and also evidence for Offer further help), one flag card. Choosing the flag scrolls to 0:33 and highlights 0:33 and 0:44.

Open `http://localhost:5173/calls/abc`. Expected: the not-found state.

## 3. Against the real API

```bash
docker compose up -d db
cd backend && export DATABASE_URL=postgresql+psycopg://stepping:stepping@localhost:5432/stepping_stones
uv run migrate && uv run python -m app.load_calls ../sample/demo_48 --demo-results && uv run apply-demo-results ../sample/demo_48/results.csv && uv run serve
```

In another terminal: `cd frontend && npm run dev`, then open `/calls/{id}` for the Transfer money demo call (`external_id` `a2f086d27b3a4f96`; its `id` is the one `GET /calls` returns).

Expected: the same page as in sample mode, with the stored values. `/calls/999999` shows the not-found state; stopping the backend and reloading shows the error state with a retry.

## 4. Edge checks

- Greyscale the page in the browser's rendering tools: evidence, wrong and plain turns are still told apart by label and icon (SC-004).
- A call with no flags shows "Nothing to fix on this call".
- The PR includes a screenshot next to the Figma frame "Call review".
