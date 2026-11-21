# Contract: `uv run analyze`

Runs the ordered evaluator against completed stored calls and saves results before the UI reads them.

## Invocation

```text
uv run analyze [--call-id ID | --call-type TYPE | --all] [--force]
```

Exactly one selector is required. By default all selectors evaluate only `pending` calls. `--force` is required to replace
an existing `scored` or `needs_review` result. The command performs no analysis at page-load time.

## Success output

The presenter reports each call's identifier and final completed, wrong, missed, and under-review counts, followed by a total number saved.

## Failure output

Unknown selections, missing procedure/turn data, model failures, malformed decisions, or invalid evidence are named. A failing call saves no partial result. Other selected calls may be processed in their own transactions and reported independently.

## Persisted behavior

- Completed and wrong results include verified evidence and applicable logged-action comparisons.
- Under-review results have no missed flag.
- Ended calls account for every required step.
- Existing `GET /calls` and `GET /calls/{id}` responses expose the saved result without invoking the model.
- Sub-checks retain their procedure descriptions, points, and passed/failed/under-review results. Re-analysis replaces the comparison table with the newly extracted request and logged values.
- A step with failed and unresolved sub-checks is wrong, with separate lost and review points. The call remains `needs_review` while any review points remain.
- The separate experimental `POST /calls/{id}` Ollama preview route does not persist a result; this command is the sole evaluator writer.
