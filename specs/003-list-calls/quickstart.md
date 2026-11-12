# Quickstart: List Calls with a Demo Clock

This guide validates feature ListCalls. The API is described in [contracts/get-calls.md](contracts/get-calls.md), and the rules in [data-model.md](data-model.md).

## Prerequisites

- Docker Postgres 18 is running.
- demo_48 has been loaded and applied (see [feature 002 quickstart](../002-apply-demo-results/quickstart.md)).
- Run commands from `backend/` with:

  ```bash
  export DATABASE_URL=postgresql+psycopg://stepping:stepping@localhost:5432/stepping_stones
  ```

## 0. Baseline, before any code change (research R8)

Record the current handler's JSON for these request sets, with no `DEMO_TODAY`:
- no parameters
- `weeks=8`
- `has_missed=true`
- `call_type=transfer_money`
- `limit=100`
- `agent_id=<first agent id>`

Save it to the session scratchpad. Also start the current API with `uv run uvicorn app.main:app --port 8001` and save the raw response bodies of `GET /calls` and `GET /calls?weeks=8`. Step 4 compares against both.

## 1. Unit tests (no database)

```bash
uv run test
```

**Expected**: all tests pass.

## 2. Demo clock acceptance (SC-001, SC-003)

```bash
DEMO_TODAY=2026-10-09T23:59:59+00:00 uv run serve
curl -s 'localhost:8000/calls?weeks=8&limit=100'
```

**Expected**:
- `summary.calls_reviewed` = 48
- `summary.this_week` = `{"steps_completed": 53, "steps_total": 59, "percent": 90}`
- `summary.first_week_percent` = 64
- the call with `external_id` `a2f086d27b3a4f96` has `result.label` = `"Wrong: Submit and confirm transfer"`

## 3. Weekly percents (SC-002)

```sql
SELECT date_trunc('week', started_at)::date AS week,
       round(100.0 * sum(steps_completed) / sum(steps_total)) AS pct
FROM calls
WHERE started_at >= timestamptz '2026-10-09T23:59:59Z' - interval '8 weeks'
GROUP BY 1 ORDER BY 1;
```

**Expected**: 64, 70, 68, 75, 80, 79, 86, 90. Weeks start Monday 2026-08-17 and end with Monday 2026-10-05.

## 4. Unchanged without the demo clock (SC-004)

Restart without `DEMO_TODAY` and repeat the step 0 requests.

**Expected**: both the handler JSON and the two saved HTTP bodies are byte-identical to the baseline. The weekly window is computed from the real time, so run step 0 and step 4 on the same day.

## 5. Bad demo clock refuses to start (US1 scenario 4)

```bash
DEMO_TODAY=2026-10-09T23:59:59 uv run python -c "import app.main"
```

**Expected**: it exits with a `ValueError` naming the value.
