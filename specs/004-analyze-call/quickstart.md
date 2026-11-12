# Quickstart: Analyze a Call

This guide validates feature AnalyzeCall. The API is described in [contracts/post-call-analysis.md](contracts/post-call-analysis.md).

## Prerequisites

- The main database is loaded (48 demo calls). Ollama is **not** required.
- Run commands from `backend/` with:

  ```bash
  export DATABASE_URL=postgresql+psycopg://stepping:stepping@localhost:5432/stepping_stones
  ```

## 0. Baseline, before any code change (research R7)

Start the current API with `uv run uvicorn app.main:app --port 8001`.

1. For call IDs 1, 2, 3, 4, 6, 8, 14 and 15 (one per call type), run the request below and save each body and status code:

   ```bash
   curl -s -w '\n%{http_code}' -X POST localhost:8001/calls/<id> \
     -H 'Content-Type: application/json' -d '{"dry_run": true}'
   ```

2. Save the body and status for `POST /calls/999999` with `{"dry_run": true}`.
3. Restart the API with `RULES_DIR=<empty scratch folder>` and save the body and status for `POST /calls/1` with `{"dry_run": true}`.

## 1. Unit tests

```bash
uv run test
```

**Expected**: all tests pass. They include the stand-in model tests and the 422 tests, and need no database and no model.

## 2. Same requests after the change

Repeat step 0 against the new code.

**Expected**: every body and status code is byte-identical: 8 × 200, then 404, then 503.

## 3. Old module gone

```bash
test ! -e app/calls_api.py && ! grep -rn "calls_api" app ../docs
```

**Expected**: no output and exit code 0.

## 4. Other features still work

- Feature 003: `GET /calls` with no parameters is byte-identical to its baseline.
- Feature 002: the unit tests pass.
