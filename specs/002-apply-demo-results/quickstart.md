# Quickstart: Apply Demo Results

This guide validates feature ApplyDemoResults. Command details are in [contracts/apply-demo-results-command.md](contracts/apply-demo-results-command.md), and the rules are in [data-model.md](data-model.md).

## Prerequisites

- Docker Postgres 18 is running locally.
- Run all commands from `backend/` with:

  ```bash
  export DATABASE_URL=postgresql+psycopg://stepping:stepping@localhost:5432/stepping_stones
  ```

## 1. Unit tests (no database)

```bash
uv run test
```

**Expected**: all tests pass, including the domain, use case, file adapter, store adapter, and command tests.

## 2. Load and apply

```bash
uv run migrate
uv run python -m app.load_calls ../sample/demo_48 --demo-results
uv run apply-demo-results ../sample/demo_48/results.csv
```

**Expected**: `{'updated': 48, 'problems': [], 'saved': True}` and exit code 0.

## 3. Check SC-002

```sql
SELECT c.score, c.points_lost, c.steps_total, c.steps_completed, c.steps_missed, c.steps_wrong,
       c.started_at AT TIME ZONE 'America/Toronto'
FROM calls c WHERE external_id = 'a2f086d27b3a4f96';
SELECT step_key, status, severity, points_lost FROM call_steps s JOIN calls c ON c.id = s.call_id
WHERE c.external_id = 'a2f086d27b3a4f96' ORDER BY position;
```

**Expected**:
- **Call**: `45 | 55 | 7 | 6 | 0 | 1 | 2026-10-07 16:48:00`.
- **Steps**: only `submit_and_confirm_transfer` is `wrong | critical | 55`. All other steps are `completed | none | 0`.

## 4. Bad file changes nothing (SC-003)

1. Copy `results.csv` to a scratch file.
2. Change one `wrong_steps` cell to `not_a_step`.
3. Change another row's `call_type`.
4. Snapshot `SELECT external_id, score, started_at FROM calls ORDER BY 1`.
5. Run `uv run apply-demo-results <scratch.csv>`.

**Expected**:
- Exit code 1.
- Both problems are listed with their demo IDs.
- The snapshot is identical afterwards.

## 5. Re-apply is stable

Run step 2's apply line again.

**Expected**: the same output, and the step 3 queries return the same values.

## 6. End-to-end acceptance (after feature ListCalls)

With `DEMO_TODAY=2026-10-09T23:59:59+00:00 uv run serve`, the screen should show:
- this week: 53 of 59 required steps, 90%
- weekly percents: 64, 70, 68, 75, 80, 79, 86, 90
- call `a2f086d27b3a4f96` labelled "Wrong: Submit and confirm transfer"

Those checks belong to feature ListCalls's quickstart.
