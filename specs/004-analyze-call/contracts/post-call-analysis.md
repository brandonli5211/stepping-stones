# Contract: `POST /calls/{call_id}` and analysis settings

**Layer**: interface adapter, in `backend/app/adapters/http/analyze.py`. The handler is `async def`; it delegates to `AnalyzeCall` and maps errors to HTTP status codes.

The contract is **unchanged** from `backend/app/calls_api.py` (now removed).

## Request

- **Path**: `call_id` (int), our own call ID, which is the `id` that `GET /calls` returns.
- **Body**: optional, `{"model": str | null = null, "dry_run": bool = false}`.

## Responses

The status codes and bodies are listed in [data-model.md](../data-model.md) under Response mapping. The detail texts are exactly:
- 404: `no call with id <id>`
- 422: `call <id> has no transcript stored`
- 503: `missing rules file: <path> (set RULES_DIR)`
- 503: `could not get an answer from Ollama: <reason>`

## Settings (read once when `app.main` starts)

| Variable | Default | Used for |
| --- | --- | --- |
| `RULES_DIR` | `<repo>/docs/procedures/schema3` | Folder of `_common.json`. The file is read per request, so a missing file gives 503 at request time. |
| `OLLAMA_HOST` | `http://localhost:11434` | Model address. `http://` is added if the scheme is missing. |
| `OLLAMA_MODEL` | `deepseek-r1:8b` | Default model when the body names none |
| `OLLAMA_TIMEOUT` | `600` | Seconds. A non-numeric value stops the API from starting. |

## Model request (to Ollama)

`POST <host>/api/generate` with `{"model", "prompt", "stream": false, "format": "json", "options": {"temperature": 0, "seed": 42}}` and the header `Content-Type: application/json`. The reply's `response` field is the answer text.
