# Contract: `apply-demo-results` command

**Layer**: infrastructure (outer edge). It only wires adapters to the `ApplyDemoResults` use case and reports the outcome.

## Invocation

Run from `backend/` with `DATABASE_URL` set:

```text
uv run apply-demo-results <results.csv> [--rules-dir <schema3 dir>]
uv run python -m app.infrastructure.apply_demo_results <results.csv> [--rules-dir <schema3 dir>]
```

| Argument | Required | Default |
| --- | --- | --- |
| `results_csv` | yes | none |
| `--rules-dir` | no | `<repo>/docs/procedures/schema3`, the same default as `load_calls` |

## Input file

The file is UTF-8 CSV with a header row. These columns are required: `demo_id`, `hvb_call_id`, `call_type`, `date`, `time`, `missed_steps`, `wrong_steps`. Extra columns are ignored.

## Output and exit code

| Case | stdout | Exit | Database |
| --- | --- | --- | --- |
| All rows valid | `{'updated': 48, 'problems': [], 'saved': True}` | 0 | All listed calls updated in one transaction, owned by the command |
| Any bad row | `{'updated': 0, 'problems': ['HVB-DEMO-07: unknown step foo', ...], 'saved': False}` | 1 | Unchanged |
| Missing column or unreadable file | error message naming the file or columns | 1 | Unchanged |

Problem messages are `"<demo_id>: <problem>"`, where `<problem>` is one of:
- `call not loaded`
- `call has no rubric steps (load with --demo-results)`
- `call <external_id> listed more than once`
- `call_type <csv>, loaded call is <stored>`
- `unknown step <key>`
- `step <key> is both missed and wrong`
- `bad date/time <date> <time>`
