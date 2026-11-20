# Quickstart: Get Progress

## 1. Unit tests (no database)

```bash
cd backend
uv run test
```

All tests pass. `tests/test_progress_demo_48.py` runs the whole use case over `sample/demo_48` and asserts the spec's weekly, by-call-type and step-row numbers. `tests/test_progress_route.py` checks the 503 for a missing rules file.

## 2. Against PostgreSQL 18, in a throwaway database

Never use the main `stepping_stones` database for this.

```bash
docker compose up -d --wait db
docker compose exec -T db psql -U stepping -d postgres -c "CREATE DATABASE stepping_stones_verify_006"
cd backend
export DATABASE_URL=postgresql+psycopg://stepping:stepping@localhost:5432/stepping_stones_verify_006
uv run migrate
uv run python -m app.load_calls ../sample/demo_48 --demo-results
uv run apply-demo-results ../sample/demo_48/results.csv
DEMO_TODAY=2026-10-09T23:59:59+00:00 uv run uvicorn app.main:app --port 8765
```

In a second terminal:

```bash
curl -s localhost:8765/progress | python3 -m json.tool
```

Expected:

- `demo_data` is `true`.
- `weeks`: 8 items from `2026-08-17` to `2026-10-05` with percents 64, 70, 68, 75, 80, 79, 86, 90. Only the last is current.
- `this_week` is `{"steps_completed": 53, "steps_total": 59, "percent": 90}` `first_week_percent` is 64 and `comparison` is `"Up from 64% in week 1"`. The first two equal `summary` on `curl -s 'localhost:8765/calls?weeks=8'`.
- `call_types`: Check balance 88, Get branch hours 86, Order checks 85, Reset password 80, Pay bill 79, Schedule appointment 77, Replace card 73, Transfer money 69.
- `steps`: 26 rows. The first 13 are the rows in spec User Story 3, in that order. The first is Confirm replacement, "Missed on 3 of your last 5 replace-card calls".

## 3. The dot rows agree with My calls

For the Replace card and Transfer money rows, each result equals that step's status on the same call in `GET /calls?limit=100&weeks=8`, taking that call type's last 5 calls, oldest first.

## 4. Other cases

- `curl -s 'localhost:8765/progress?agent_id=999999'`: 200, 8 empty weeks, `this_week` null, empty `call_types` and `steps`, `demo_data` false.
- `curl -s -o /dev/null -w '%{http_code}' 'localhost:8765/progress?agent_id=x'`: 422.
- Start the API with `RULES_DIR=/nonexistent`: `GET /progress` answers 503, and `GET /calls` still answers 200.

## 5. Nothing else moved

`GET /calls?limit=100&weeks=8` returns the same body as before this feature.

## 6. Clean up

```bash
docker compose exec -T db psql -U stepping -d postgres -c "DROP DATABASE stepping_stones_verify_006"
```
