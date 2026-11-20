# Contract: Health check

This feature does not add an endpoint. The existing health check stays the
screen's signal that the API is up and the database accepts a connection.

## Request

`GET /api/health`

No request body. No authentication.

## Response

Status `200` and a JSON object:

| Field | Value when healthy |
| --- | --- |
| `status` | `ok` |
| `database` | `connected` |

The body does not include coaching results, scores, or the contents of
`app_meta`.

## Failure

If the database cannot be reached, the request does not return the healthy
body above. The screen then cannot show a connected database.

## What changed inside the handler

The HTTP adapter is asynchronous. It does not embed the connectivity
check. It depends on the `CheckHealth` use case, which depends on a
`DatabaseProbe` port. The SQLAlchemy probe is the persistence adapter
behind that port. Callers still see the same path, the same status, and
the same fields.
