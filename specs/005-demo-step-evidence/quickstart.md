# Quickstart: Demo Step Evidence

## 1. Unit tests (no database)

```bash
cd backend
uv run test
```

All tests pass, including the evidence cases in `test_bad_file_saves_nothing` and `test_demo_48_evidence`, which checks `HVB-DEMO-06`'s quote against `sample/demo_48/transcript/a2f086d27b3a4f96.json`.

## 2. Against PostgreSQL 18

```bash
docker compose up -d db
cd backend
export DATABASE_URL=postgresql+psycopg://stepping:stepping@localhost:5432/stepping_stones
uv run migrate
uv run python -m app.load_calls ../sample/demo_48 --demo-results
uv run apply-demo-results ../sample/demo_48/results.csv
```

Expected output: `{'updated': 48, 'problems': [], 'saved': True}`.

```sql
SELECT c.external_id, s.step_key, s.status, s.severity, s.points_lost,
       s.evidence_turn_idx, s.evidence_quote, t.start_seconds, c.score
FROM call_steps s
JOIN calls c ON c.id = s.call_id
LEFT JOIN call_turns t ON t.call_id = s.call_id AND t.idx = s.evidence_turn_idx
WHERE s.evidence_turn_idx IS NOT NULL;
```

Expected: exactly one row, `a2f086d27b3a4f96 | submit_and_confirm_transfer | wrong | critical | 55 | 9 | okay and that was from your savings to your checking account | 33.53 | 45`.

`SELECT comparison FROM call_steps …` for that step still shows the three caller-asked vs logged rows (source and destination do not match).

## 3. Bad evidence saves nothing

Copy `results.csv`, change one word of the `HVB-DEMO-06` quote, and apply the copy:

```text
{'updated': 0, 'problems': ['HVB-DEMO-06: quote not in turn 9'], 'saved': False}
```

The exit code is 1, and the query above still returns the row from step 2.

## 4. Nothing else moved

With `DEMO_TODAY=2026-10-09T23:59:59+00:00 uv run serve`, `GET /calls?limit=100&weeks=8` gives the same body as before this feature: this week 53 of 59 (90%), and call `a2f086d27b3a4f96` labelled "Wrong: Submit and confirm transfer".
