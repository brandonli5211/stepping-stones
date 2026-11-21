# Contract: `uv run analyze`

Runs the ordered evaluator against completed stored calls and saves results before the UI reads them.

## Invocation

```text
uv run analyze [--call-id ID | --call-type TYPE | --all]
```

Exactly one selector is required. `--all` evaluates all eligible calls. The command performs no analysis at page-load time.

## Success output

The presenter reports each call's identifier and final completed, wrong, missed, and under-review counts, followed by a total number saved.

## Failure output

Unknown selections, missing procedure/turn data, model failures, malformed decisions, or invalid evidence are named. A failing call saves no partial result. Other selected calls may be processed in their own transactions and reported independently.

## Persisted behavior

- Completed and wrong results include verified evidence and applicable logged-action comparisons.
- Under-review results have no missed flag.
- Ended calls account for every required step.
- Existing `GET /calls` and `GET /calls/{id}` responses expose the saved result without invoking the model.
