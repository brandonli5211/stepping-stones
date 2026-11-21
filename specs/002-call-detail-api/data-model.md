# Phase 1 Data Model: Call Detail API

**Feature**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md) · **Date**: 2026-11-08

No schema change. This feature reads the #29 tables and adds no columns or
tables, so no Alembic migration is needed (constitution Principle III).

## 1. Stored data read (outer layer, existing)

| Table | Columns used | Notes |
| --- | --- | --- |
| `calls` | `id`, `external_id`, `call_type`, `procedure_id`, `summary` | `score`, `points_lost` and `steps_*` are **not** read (R3). |
| `procedures` | `name`, `rules` | Display name of the call type, and each step's `description` from `rules.steps`, joined on `procedure_id`. |
| `call_turns` | `idx`, `speaker`, `start_seconds`, `text` | Ordered by `idx`. `start_seconds` may be null. |
| `call_steps` | `step_key`, `position`, `name`, `points`, `status`, `severity`, `points_lost`, `points_under_review`, `detail`, `evidence_turn_idx`, `evidence_quote`, `coaching`, `sub_checks`, `comparison` | Ordered by `position`. |

## 2. Domain records (inner layer, new: `app/domain/call_detail.py`)

Frozen dataclasses. No FastAPI, SQLAlchemy or Pydantic imports.

### Input records (what the reader port returns)

- **CallRecord**: `id: int`, `external_id: str`, `call_type: str`,
  `call_type_name: str`, `summary: str | None`, `turns: tuple[TurnRecord, ...]`,
  `steps: tuple[StepRecord, ...]`.
- **TurnRecord**: `idx: int`, `speaker: "agent" | "caller"`,
  `start_seconds: float | None`, `text: str`.
- **StepRecord**: `key: str`, `position: int`, `name: str`, `points: int`,
  `status: "completed" | "missed" | "wrong" | "under_review"`,
  `severity: "none" | "slip" | "inaccuracy" | "mistake" | "critical"`,
  `points_lost: int`, `points_under_review: int`, `detail: str | None`,
  `evidence_turn_idx: int | None`, `evidence_quote: str | None`,
  `coaching: str | None`, `sub_checks: tuple[SubCheck, ...]`,
  `comparison: tuple[ComparisonRow, ...]`, `description: str | None` (from the
  procedure rules).
- **SubCheck**: `key: str`, `description: str`, `points: int`,
  `result: "passed" | "failed" | "under_review"` (stored as `status`).
- **ComparisonRow**: `field: str`, `caller_asked: str | None`,
  `logged: str | None`, `match: bool`.

Validation: records raise `InvalidCallRecord` (a `ValueError`) naming the step,
for an unknown step status, severity, sub-check result or turn speaker, or for
`points_lost` outside 0 to `points` (same rule as the database check). The
reader adds the call id to the message.

### Derived records (what the domain rules produce)

- **ScoreSummary**: `score: int | None`, `out_of: 100`,
  `steps_done_right: int`, `steps_total: int`, `points_lost: int`,
  `critical_count: int`, `points_under_review: int`, `provisional: bool`.
  - `points_lost = Σ step.points_lost`
  - `score = max(0, 100 - points_lost)`; `None` when there are no steps
  - `steps_done_right = #steps with status completed`
  - `critical_count = #steps with severity critical`
  - `points_under_review = Σ step.points_under_review`;
    `provisional = points_under_review > 0`
- **Note**: `kind: "evidence" | "wrong"`, `step_key: str`, `text: str`.
  - completed step with evidence turn → `evidence`, "Evidence for {name}"
  - wrong step with evidence turn → `wrong`, "Wrong: {detail}" (or
    "Wrong: {name}" when `detail` is empty)
  - missed / under review / no evidence turn → no note
- **Flag**: `step_key`, `step_name`, `status: "missed" | "wrong"`, `severity`,
  `points_lost`, `message: str | None`. One per missed or wrong step, in
  position order. Message: the call type's builder when it gives one (Transfer
  money: "Moved {amount} {from} → {to}. The caller asked for {from} → {to}.",
  with the asked amount added only when it differs; "Nothing was logged. The
  caller asked for …" when nothing was logged; "Logged amount …, from …, to ….
  The caller asked for …" when only part was logged), else the step's `detail`.
- **StepDetail** also carries `coaching`: the stored coaching for missed and
  wrong steps, none for completed and under-review steps (`coaching_for`).
- **Evidence**: `quote: str`, `turn_idx: int`, `start_seconds: float | None`.
  Present when the step has both an evidence turn and a quote; else `None`.
- **TypeDetails**: `type: str` plus content.
  - **TransferMoneyDetails**: `type: "transfer_money"`,
    `fields: tuple[FieldRow, ...]` where **FieldRow** is `field` (key),
    `label` ("Amount" / "From" / "To"), `caller_asked`, `logged`,
    `result: "match" | "mismatch" | "reversed"`. Rows come from the stored
    `comparison` rows in the order amount, source, destination. From and To
    are both `reversed` when logged From = asked To and logged To = asked From
    (and they differ).
  - **EmptyDetails**: `type: <call_type>`, no content. Used for every type
    without a builder.
- **CallDetail**: `header` (`call_id`, `external_id`, `call_type`,
  `call_type_name`, `summary`), `score: ScoreSummary`,
  `transcript: tuple[(TurnRecord, notes), ...]`, `steps` (each StepRecord with
  its `Evidence`), `flags: tuple[Flag, ...]`, `type_details: TypeDetails`.

### Errors

- **CallNotFound(call_id)**: raised by the use case when the reader returns
  `None`. The HTTP adapter maps it to 404.

## 3. Response schema (outer layer, new: `app/adapters/http/call_detail_schema.py`)

Pydantic models mirroring `CallDetail` one to one, used as the route's
`response_model`. `type_details` is a union tagged by `type`:
`TransferMoneyDetailsOut | EmptyDetailsOut`, where an empty block may not use a
type that has its own block. Full shape and example:
[contracts/get-call-detail.md](contracts/get-call-detail.md).

## 4. State and lifecycle

Read only. The detail reflects whatever step results are stored at the time of
the request: a `pending` call (no steps) returns a null score, no flags and an
empty step list; a call whose steps are later rewritten by #38 returns the new
values on the next read. Nothing is cached.
