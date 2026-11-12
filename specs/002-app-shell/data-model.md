# Data Model: App Shell and Shared Screen Pieces

Frontend types only. No database change and no Alembic migration: this
feature adds no table and no column.

## Domain (`frontend/src/domain.ts`)

Types and constants only, no functions.

### StepStatus

One of `completed`, `missed`, `wrong`, `under_review` — the values the
`/calls` API sends. `procedure` is a display-only variant for a step as
written in a procedure, not a call result.

| Rule | Source |
| --- | --- |
| Each status has a fixed text label in `STATUS_LABELS`: Completed, Missed, Wrong, Under review, Procedure step | FR-007 |
| A raw value outside the known statuses is drawn and labelled as `under_review` | Spec edge case |
| The status is never computed in the frontend; it is read from the API | FR-009, Principle I |

### Screen (`SCREENS`)

| Field | Type | Notes |
| --- | --- | --- |
| `id` | `"my-calls" \| "call-detail" \| "progress" \| "procedures"` | Exactly four (FR-001) |
| `path` | string | `/`, `/calls/:callId`, `/progress`, `/procedures` |
| `title` | string | Page title |
| `nav` | `"my-calls" \| "progress" \| "procedures"` | Menu item marked on this screen; call detail → `my-calls` (FR-003) |

### MenuItem (`MENU`)

`{ nav, label, path }` for My calls, Progress, Procedures, in that order.

### AgentProfile

`{ name: string; role: string | null }`.

## Application (`frontend/src/application.ts`)

### ShellView — output of `resolveShellView(path, agent)`

| Field | Type | Notes |
| --- | --- | --- |
| `screen` | Screen | Unknown address → My calls (FR-005) |
| `callId` | string \| null | Set on call detail |
| `menu` | `(MenuItem & { current: boolean })[]` | Exactly one `current` (FR-003) |
| `agent` | AgentProfile | Name defaults to "Agent", empty role → null (FR-004) |

### ApiGateway (port)

`{ get<T>(path: string): Promise<T> }` — rejects with an `Error` whose
message names the path and HTTP status. Implemented by `createApiGateway`
in `frontend/src/gateway.ts`.

## Sample responses (`frontend/src/gateway.ts`)

Keyed by API path. `/calls` returns the same shape as
`backend/app/calls_api.py::list_calls`: `summary` (`calls_reviewed`,
`weeks`, `this_week { steps_completed, steps_total, percent }`,
`first_week_percent`) and `calls[]` (`id`, `external_id`, `call_type`,
`call_type_name`, `started_at`, `status`, `score`, `steps_completed`,
`steps_total`, `steps[]`, `result`). Scores, statuses and result labels
are stored as literal values, never calculated.
