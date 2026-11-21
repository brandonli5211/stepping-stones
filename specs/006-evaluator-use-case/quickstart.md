# Quickstart: Evaluate Ordered Call Steps

1. Start PostgreSQL 18 and load a supported stored call with its procedure and transcript.
2. Set `OPENAI_API_KEY` for a live adapter run. Unit and integration tests use a fake decision model and do not require a key.
3. Run the command for a single supported call:

   ```text
   cd backend
   uv run analyze --call-id <id>
   ```

4. Verify the command reports a saved result.
5. Fetch `GET /calls/<id>` and confirm that its steps, evidence, flags, score, and provisional status match the saved evaluator result without starting a model call.
6. Run the evaluator tests, including confidence-boundary, invalid-quote, terminal-finalization, logged-action comparison, and transaction-rollback cases.

## Verified review regression

On 2026-11-21, a live Docker run of `uv run analyze --call-id 1 --force` against local demo call `a2f086d27b3a4f96` saved six completed steps and one wrong step, with zero review points. The submit step cites turn 9. Its logged-values check loses 35 points, and its source and destination read-back checks each lose 5. Task type and amount pass, giving a score of 55. This differs from the curated CSV's whole-step penalty.

`GET /calls/1` returned the same 45 lost points, populated sub-check descriptions and results, and fresh comparison rows showing both accounts reversed. Caller-request source and destination confidences were 0.98 and 1.00. The serial backend suite passed 202 tests in Docker with the existing `sample/` directory mounted read-only at `/sample`. Other call types were covered by automated tests.
