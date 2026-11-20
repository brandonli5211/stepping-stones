# Quickstart: View Progress

## 1. Unit tests and type check

```bash
cd frontend
npm install
npm test
npm run lint
```

All tests pass (including `progress shows what the api sends`, `progress error state` and `imports point inward`) and the type check is clean.

## 2. In the browser, against a throwaway database

Never use the main `stepping_stones` database for this.

```bash
docker compose up -d --wait db
docker compose exec -T db psql -U stepping -d postgres -c "CREATE DATABASE stepping_stones_verify_007"
cd backend
export DATABASE_URL=postgresql+psycopg://stepping:stepping@localhost:5432/stepping_stones_verify_007
uv run migrate
uv run python -m app.load_calls ../sample/demo_48 --demo-results
uv run apply-demo-results ../sample/demo_48/results.csv
DEMO_TODAY=2026-10-09T23:59:59+00:00 CORS_ORIGINS=http://localhost:5174 uv run uvicorn app.main:app --port 8765
```

In a second terminal:

```bash
cd frontend
VITE_API_URL=http://localhost:8765 npm run dev -- --port 5174
```

Open `http://localhost:5174/progress`. Expected:

- The title "Your progress" with a "Demo data" badge.
- 8 bars labelled Aug 17 to Oct 5 reading 64%, 70%, 68%, 75%, 80%, 79%, 86%, 90%. Only the last is highlighted and says "This week".
- "53 of 59 required steps completed" and "Up from 64% in week 1".
- By call type: 88, 86, 85, 80, 79, 77, 73, 69, in the order of the spec.
- Steps you skip most: 5 rows, starting with Confirm replacement (completed, missed, completed, missed, missed; "Missed on 3 of your last 5 replace-card calls"). "Show all 26 steps" shows 26 rows; "Show fewer" goes back to 5.
- The legend under the rows.

Then check:

- **My calls agrees**: on `http://localhost:5174/`, the last five Replace card and Transfer money calls have the same stones for those steps.
- **Failure**: stop the API and reload Progress. It shows "Couldn't load your progress" and no chart.
- **Sample mode**: start the frontend with `VITE_SAMPLE_DATA=true` and no API. Progress shows the sample answer.
- **Other pages**: My calls, a call detail address and Procedures look as before.

Take a screenshot of the Progress page with the demo data for the pull request.

## 3. Clean up

```bash
docker compose exec -T db psql -U stepping -d postgres -c "DROP DATABASE stepping_stones_verify_007"
```
