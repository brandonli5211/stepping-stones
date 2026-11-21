# Phase 0 Research: Call Detail API

**Feature**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md) · **Date**: 2026-11-08

Each item: the question, the decision, why, and what was rejected.

## R1. Where does the mock call's data come from?

**Finding**: The Figma values (45, 6 of 7, 55 lost, 0:33, field table) belong
to demo call `HVB-DEMO-06` (HarperValley call `a2f086d27b3a4f96`) in
`backend/seed/demo_calls.json` on the unmerged branch
`origin/feat/33-demo-dataset`. That file uses its own format (`step_id` such as
`submit`, stored `notes`, `flags`, `type_details`). It is not loaded into the
#29 tables (`calls`, `call_turns`, `call_steps`) that this endpoint reads, and
its step ids differ from the schema3 keys (`submit` vs
`submit_and_confirm_transfer`).

**Decision**: This feature reads the #29 tables only. The tests build the
`HVB-DEMO-06` call as a fixture in the shape those tables hold (seven steps,
the submit step wrong with 55 points lost and its evidence turn at 33.53 s,
the comparison rows on the submit step), and assert every mock value from it.
Loading the #33 seed file into the #29 tables is left to #33 (or a follow-up),
which owns the demo data.

**Rationale**: The ticket says this endpoint "only reads" step results and
that #33 produces them. Building a loader here would add a second use case
(constitution: one use case per plan) and duplicate #33's work.

**Rejected**: (a) Reading `demo_calls.json` directly: breaks "read straight
from the database". (b) Writing a seed-to-table loader in this feature: second
use case, more than 6 tasks.

## R2. Transcript notes: derived or stored?

**Finding**: #29 has no notes table. Each `call_steps` row has one
`evidence_turn_idx`, an `evidence_quote`, a `status` and a one-sentence
`detail`. The #33 seed stores notes as free rows, sometimes two per step
(submit has "Wrong" notes at 0:33 and 0:44).

**Decision**: Derive notes from step results in the domain layer: for each step
with an evidence turn, add "Evidence for <step name>" to that turn when the
step is completed, or "Wrong: <detail>" when it is wrong. Missed and
under-review steps add no note. One note per step.

**Rationale**: No migration, matches FR-007, and covers the "Done when" (the
0:33 evidence). A call with no wrong steps cannot produce a "Wrong" note.

**Rejected**: A `call_step_notes` table for several notes per step: a schema
change and a writer that does not exist yet (#38). Recorded as a follow-up if
the page needs the second "Wrong" note at 0:44.

## R3. Score, counts, critical count, provisional score

**Decision**: Pure domain functions compute, from the step results only:
`points_lost = sum(points_lost)`, `score = 100 - points_lost` (clamped to
0–100), `steps_done_right = count(status == completed)`,
`steps_total = count(steps)`, `critical_count = count(severity == critical)`,
`points_under_review = sum(points_under_review)`. With no steps, score is
`null` (pending call). The stored `calls.score` and `calls.steps_*` columns are
not read.

**Rationale**: Ticket notes and FR-005 (the API works it out); constitution
Principle I (backend owns the judgment) and Principle VII (domain rule, no
framework).

**Rejected**: Reading `calls.score`: the ticket says it is worked out, and
`calls.score` is null for `needs_review`, which contradicts the clarified
provisional score.

## R4. Flags

**Decision**: Domain function: one flag per step with status `missed` or
`wrong`, in position order: `{step_key, step_name, status, severity,
points_lost}`. (Clarification 2026-11-08.)

## R5. Type-specific block

**Decision**: A small registry in the application layer maps a call type to a
builder function: `transfer_money` → builds the field table from the
`comparison` rows stored on its steps (field key mapped to the labels Amount,
From, To; `match` mapped to `match` / `mismatch`). Any other type → empty
block. The block is a tagged object: `{"type": "<call_type>", ...}`, typed as a union
tagged by `type`: `transfer_money` must carry its table; any other type is an
empty block, and an empty block may not use a type that has its own block. New
types add a variant. (A strict Pydantic discriminated union was not possible
because the empty block accepts any type name.)

**Added 2026-11-11 (Option A)**: From and To are `reversed` when the logged
values are the caller's two accounts swapped. Flags carry a message: for
Transfer money, built from the field table when it disagrees with the caller
("Moved $114 savings → checking. The caller asked for checking → savings.");
otherwise the step's stored `detail`. Step descriptions come from the call's
procedure rules (`procedures.rules.steps[].description`), read with the call.

**Rationale**: FR-011 to FR-013: adding a type adds a builder and a schema
variant without changing the rest of the response.

**Rejected**: Returning the raw `comparison` JSON: leaks storage shape to the
page and gives no typed contract.

## R6. Typed schema and error

**Decision**: Pydantic models (already shipped with FastAPI, so no new
dependency; constitution Principle V) as the route's `response_model`, in the
HTTP adapter layer. The use case returns plain domain dataclasses; a presenter
maps them to the Pydantic models. A domain `CallNotFound` error is raised by
the use case and mapped to HTTP 404 in the route.

**Rationale**: FR-015 (a response that does not fit fails), and `/docs` lists
the shape (Technology Constraints). Keeps FastAPI and Pydantic out of the
domain and use-case modules (Principle VII).

## R7. Persistence access

**Decision**: A `CallDetailReader` port (Protocol) in
`app/application/ports.py` with `async def get(call_id: int) -> CallRecord |
None`. A SQLAlchemy adapter loads the call with its procedure name, turns and
steps through the existing async session (`get_session`) and maps rows to
domain records. Three queries (call + procedure, turns, steps), read only, no
commit.

**Rationale**: Principle III (async session), Principle VII (port in the
application layer, SQLAlchemy at the edge), FR-002 (read only).

## R8. Testing without a database

**Finding**: Existing tests run with `pytest` and `asyncio.run`, using fakes
for ports; there is no test database or HTTP client dependency.

**Decision**: Follow that pattern. Unit tests for every new function:
domain rules (with the `HVB-DEMO-06` fixture, a check-balance call, and a call
with no mistakes), the use case with a fake reader (found and not found), the
presenter, the route handler called directly with a fake use case (200 and
404), and the repository's row mapper with plain row objects. A test also
checks the domain and application modules import no framework (as
`test_check_health.py` does).

**Rejected**: Adding `httpx`/`pytest-asyncio` or a test database: new
dependencies not needed for the required coverage.

## R9. Where the existing calls code fits

**Finding**: `app/calls_api.py` holds `GET /calls` and `POST /calls/{id}` with
SQL inside the route functions; it predates Principle VII.

**Decision**: Leave it in place. The new route lives in a new
`app/adapters/http/call_detail.py` and does not touch `calls_api.py`, so the
Governance "bring a touched file into compliance" rule is not triggered. The
only edit to an existing module is the out-of-date `external_id` comment in
`app/models.py` (a comment fix, no behavior change). Moving `calls_api.py` to
Clean Architecture is a separate refactor.

## R10. Example response for #35 and #36

**Decision**: The contract and a full `HVB-DEMO-06` example live in
[contracts/get-call-detail.md](contracts/get-call-detail.md) now. The
implementation copies that example into `docs/api-contract.md` (new file) so
#35 and #36 can start before the endpoint merges (FR-016, SC-006).

## Use Cases (after Phase 0)

| Use case | Responsibility | Module |
| --- | --- | --- |
| `GetCallDetail` (primary) | Read one stored call by numeric ID and assemble its detail (header, score, transcript notes, steps, flags, type block); raise `CallNotFound` if absent. Never analyzes or writes. | `backend/app/application/get_call_detail.py` |

Out of scope: loading the #33 seed into the #29 tables; multiple notes per
step; refactoring `calls_api.py`.
