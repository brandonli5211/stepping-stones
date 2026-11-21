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
