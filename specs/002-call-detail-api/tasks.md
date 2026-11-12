---

description: "Tasks for the Call Detail API (GET /calls/{id})"
---

# Tasks: Call Detail API

**Input**: Design documents from `specs/002-call-detail-api/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/get-call-detail.md](contracts/get-call-detail.md)

**Tests**: Each task ships the unit tests for the functions it adds
(constitution Principle VI). There is no separate test phase.

**Organization**: One Clean Architecture use case, `GetCallDetail`, as one
vertical slice of 6 tasks.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[US1]**: the single use-case slice

## Use Case: `GetCallDetail` (from plan.md Summary)

**Goal**: `GET /calls/{id}` returns the whole call detail (header, score,
transcript with notes, steps with details, flags, type block) read from the
#29 tables, or 404 for an unknown call.

**Independent Test**: `cd backend && uv run test` passes, including the
`HVB-DEMO-06` fixture asserting 45, 6 of 7, 55 points lost, 1 critical, the
evidence at 33.53 s (0:33), the three-row field table with From and To
reversed, the step description and the flag message; the check-balance
fixture asserting no flags and no "Wrong" notes; and the 404.

- [X] T001 [P] [US1] **Domain** (innermost layer): in
  `backend/app/domain/call_detail.py`, add the frozen records `CallRecord`,
  `TurnRecord`, `StepRecord`, `SubCheck`, `ComparisonRow`, the derived
  `ScoreSummary`, `Note`, `Flag`, `Evidence`, `FieldRow`,
  `TransferMoneyDetails`, `EmptyDetails`, `CallDetail`, the `CallNotFound`
  error, and the pure functions `summarize_score`, `notes_by_turn`, `flags`,
  `evidence_for`, `transfer_money_details`, `type_details` (registry:
  `transfer_money` → field table, any other type → empty block) and
  `build_call_detail`. Rules exactly as [data-model.md](data-model.md) §2.
  Tests in `backend/tests/test_domain_call_detail.py` call every function with:
  the `HVB-DEMO-06` fixture (all mock values, FR-004, FR-007, FR-010, FR-012,
  SC-001); a check-balance call with no mistakes (score 100, `flags == ()`, no
  `wrong` notes, `EmptyDetails("check_balance")`, SC-002); a step under review
  (provisional score, no flag, FR-004a); a pending call with no steps (score
  `None`); a missed step (no note, no evidence, one flag); a turn with no time;
  and records raising `InvalidCallRecord` for an unknown status, severity,
  sub-check result or speaker, or `points_lost > points`. No FastAPI,
  SQLAlchemy or Pydantic import.
  **Option A (2026-11-11)**: `StepRecord.description`; `FieldRow.result` gains
  `reversed` (From and To swapped, FR-012); `Flag.message` from a per-type
  builder `transfer_flag_message` with the step's `detail` as fallback
  (FR-019); `flags` takes the call type. Direct tests for every function,
  private helpers `_require` and `_in_order` included (analyze D1).
  **Converge F1 (2026-11-11, folded in to keep the 6-task limit)**: when
  nothing was logged, `transfer_flag_message` says so from the table ("Nothing
  was logged. The caller asked for $78 checking → savings.") and, when only
  part was logged, lists what was ("Logged amount $114, from not logged, to
  checking. …") instead of falling back to the stored reason (FR-019, partial). **Converge F2**: a `coaching_for`
  rule returns no coaching for completed and under-review steps, carried on
  `StepDetail.coaching` (FR-009, partial). Direct tests for both.

- [X] T002 [US1] **Application** (use case + port): add the
  `CallDetailReader` Protocol (`async def get(call_id: int) -> CallRecord |
  None`) to `backend/app/application/ports.py`, and the `GetCallDetail` use
  case in `backend/app/application/get_call_detail.py`
  (`async def execute(call_id) -> CallDetail`: read through the port, raise
  `CallNotFound` when `None`, else return `build_call_detail(record)`).
  Tests in `backend/tests/test_get_call_detail.py` with a fake reader: found
  call returns the built detail and calls the reader once with that id; absent
  call raises `CallNotFound`; the reader is only read (fake has no write
  methods, FR-002); and an AST import check that `call_detail.py`,
  `get_call_detail.py` and `ports.py` import no `fastapi`, `sqlalchemy`,
  `alembic` or `pydantic` (Principle VII). Depends on T001.

- [X] T003 [US1] **Persistence adapter**: in
  `backend/app/adapters/persistence/call_detail_reader.py`, add
  `SqlAlchemyCallDetailReader(session: AsyncSession)` implementing
  `CallDetailReader` with three async read queries (call joined to
  `procedures.name`; `call_turns` by `idx`; `call_steps` by `position`) and no
  commit, plus pure mappers `to_turn_record`, `to_step_record` (JSON
  `sub_checks.status` → `SubCheck.result`, `comparison` → `ComparisonRow`s,
  `Decimal` seconds → `float`) and `to_call_record`. Tests in
  `backend/tests/test_call_detail_repository.py`: each mapper with plain row
  objects (null time, empty `sub_checks`, null `comparison`); `get` with a stub
  async session returning canned rows (found) and no row (returns `None`).
  **Option A**: the call query also reads `procedures.rules`; each step gets
  the `description` for its key from `rules.steps` (FR-018), via a pure
  `step_descriptions(rules)` mapper. Direct test for `_text` (analyze D1).
  Depends on T002.

- [X] T004 [US1] **HTTP adapter** (outer edge): in
  `backend/app/adapters/http/call_detail_schema.py`, add Pydantic response
  models matching [contracts/get-call-detail.md](contracts/get-call-detail.md),
  with `type_details` as a union tagged by `type`
  (`TransferMoneyDetailsOut | EmptyDetailsOut`; an empty block may not use a
  type that has its own block) (FR-015). In
  `backend/app/adapters/http/call_detail.py`, add `present(detail) ->
  CallDetailOut`, the dependency `get_get_call_detail(session=Depends(get_session))`,
  and `@router.get("/calls/{call_id}", response_model=CallDetailOut)` as an
  `async def` that only calls the use case and maps `CallNotFound` to
  `HTTPException(404, "no call with id {id}")` (FR-001, FR-014, Principles II,
  VII). Tests in `backend/tests/test_call_detail_route.py`: `present` on the
  `HVB-DEMO-06` detail validates and matches the contract example's values;
  the route called directly with a fake use case returns that body; a fake
  raising `CallNotFound` gives a 404; the route handler is `async def`.
  **Option A**: `StepDetailsOut.description`, `FlagOut.message`, field result
  `reversed`. Direct tests for `_step` and `_type_details` (analyze D1), and a
  test that the OpenAPI path parameter is an integer (FR-001, analyze C1).
  **Converge F2**: `_step` takes the coaching from `StepDetail.coaching`, not
  the stored step, so the route adds no rule of its own.
  Depends on T003.

- [X] T005 [US1] **Composition and check**: include the call detail router in
  `backend/app/main.py`; fix the `external_id` comment in `backend/app/models.py`
  ("the dataset's call id, shown as the reference; the URL uses `id`"). No
  behavior change, so no test change. Run `cd backend && uv run test` (all
  pass) and the [quickstart.md](quickstart.md) steps 2–3: `GET /calls/{id}`
  returns 200 for a stored call, `GET /calls/999999` returns 404, and `/docs`
  lists the endpoint with its schema (FR-016, SC-005). Depends on T004.

- [X] T006 [P] [US1] **Contract for #35 and #36**: create
  `docs/api-contract.md` with the request, the responses (200, 404, 422), the
  shape and the `HVB-DEMO-06`, check-balance and 404 examples, copied from
  [contracts/get-call-detail.md](contracts/get-call-detail.md) (FR-016,
  SC-006). No code, so it can be done first and pushed early to unblock #35
  and #36. **Option A**: regenerate the examples from `present()` so they show
  the description, `reversed` and the flag message.

**Checkpoint**: `GetCallDetail` works through the domain → application →
adapters → `main.py` layers; domain and application import no FastAPI,
SQLAlchemy or Pydantic; every new function has a unit test.

---

## Requirement coverage

| Requirement | Task |
| --- | --- |
| FR-001 numeric id | T004 |
| FR-002 read only | T002, T003 |
| FR-003 header | T001, T004 |
| FR-004, FR-004a, FR-005 score and counts | T001 |
| FR-006, FR-007 transcript and notes | T001, T003 |
| FR-008, FR-009 steps and details | T001, T003, T004 |
| FR-010 flags | T001 |
| FR-011 to FR-013 type block | T001, T004 |
| FR-014 404 | T002, T004 |
| FR-015 typed schema | T004 |
| FR-016 catalogue and example | T005, T006 |
| FR-017 tests | T001 to T004 |
| FR-018 step description | T001, T003, T004 |
| FR-019 flag message | T001, T004 |

## Dependencies & Execution Order

1. T006 has no dependency; do it first so #35 and #36 can start.
2. T001 → T002 → T003 → T004 → T005, inward to outward.
3. Each task's tests are written and passing before the next task starts.

## Implementation Strategy

1. T006, then T001 to T005 in order.
2. Stop when the Independent Test passes.
3. Out of scope (new features, not more rows here): loading the #33 seed into
   the #29 tables, several notes per step, refactoring `app/calls_api.py`.

## Notes

- 6 tasks, the ceiling. Nothing touches the frontend.
- No migration: no schema change (Principle III).
- No new dependency (Principle V).
