# Contract: `GET /calls` and `DEMO_TODAY`

**Layer**: interface adapter, in `backend/app/adapters/http/calls.py`. The handler is `async def`; it builds the query, delegates to `ListCalls`, and presents the result.

This contract is **unchanged** from the current handler in `backend/app/calls_api.py`. Only the module the handler lives in changes.

## Request

| Param | Type | Default | Validation | Effect |
| --- | --- | --- | --- | --- |
| `agent_id` | int | none | — | Window: list and header |
| `call_type` | str | none | — | List only. Normalized as `snake`, e.g. `"Transfer Money"` → `transfer_money` |
| `has_missed` | bool | false | — | List only. Keeps calls with `steps_missed + steps_wrong > 0` |
| `limit` | int | 10 | 1–100 (422 otherwise) | List size |
| `weeks` | int | none | 1–520 (422 otherwise) | Window: `started_at >= reference − weeks` |

## Response 200

The shape is as in [data-model.md](../data-model.md) under Response mapping.

`summary.this_week` covers the UTC Monday-start week containing the reference instant. `result.label` is `"Missed <step name>"` or `"Wrong: <step name>"`.

## Configuration: `DEMO_TODAY`

The value is read once, when the API process starts (`app.main`).

| Value | Reference instant |
| --- | --- |
| unset or empty | the real current time (UTC), read on each request |
| ISO 8601 with offset, e.g. `2026-10-09T23:59:59+00:00` | that instant, on every request |
| no offset (`2026-10-09T23:59:59`) or unparseable | the API fails to start: `ValueError: DEMO_TODAY=<value> is not an ISO 8601 date-time with a UTC offset` |
