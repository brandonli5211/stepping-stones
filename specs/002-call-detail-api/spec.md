# Feature Specification: Call Detail API

**Feature Branch**: `feat/34-call-detail-api` (spec folder `002-call-detail-api`)

**Created**: 2026-11-08

**Status**: Implemented (converged 2026-11-11)

**Ticket**: #34 · Sprint 1 · Size M · Depends on #29

**Input**: User description: "`GET /calls/{id}` returns everything the call detail screen (Figma frame 'Transfer money, call detail') needs, read straight from the database. Nothing is analyzed while the page loads. It returns the header (call type, call ID, one-sentence summary), the score (points out of 100, '6 of 7 steps done right', points lost, number of critical problems), the transcript (speaker, time, text, notes such as 'Evidence for Greet and open' or 'Wrong: read back reversed'), the required steps with status and points, each step's details (sub-checks with points, the proving quote and its time, a coaching phrase), the flags, and an extra block that depends on the call type, with a field naming the type (for Transfer money: the 'Caller asked / Logged / Result' table for amount, from and to; an unknown type returns an empty block). An unknown call returns 'not found' (404). An example response is added to `docs/api-contract.md`. The stored data holds each step's result (Completed, Missed or Wrong) and the points it is worth; the API works out the score (100 minus points lost) and the counts itself. Step results are written by hand for now (#33) and by the analyzer later (#38); this endpoint only reads them."

## Clarifications

### Session 2026-11-08

- Q: What counts as a flag? → A: One flag per step that was missed or done
  wrong, with its severity and points lost. Steps under review, steps out of
  order, and calls sent to review do not raise flags.
- Q: Which ID identifies the call in the request? → A: The call's numeric ID,
  the same `id` the call list returns and the analyze request takes. The
  dataset's external ID is returned in the header as the call's reference.
- Q: What score is returned while some steps are under review? → A: A
  provisional score: 100 minus the points already lost on missed and wrong
  steps, returned with the points still under review so the screen can show it
  as "so far".

### Session 2026-11-11 (after `/speckit-analyze`)

- Q: Should the response carry the Figma values no requirement covered (step
  description, "Reversed", flag sentence)? → A: Yes (Option A). The step
  description comes from the call's procedure rules as stored; "reversed" and
  the flag sentence are worked out by the backend from the stored field table.
  Hiding noise turns stays a display choice for the page.

## User Scenarios & Testing *(mandatory)*

The consumers of this feature are the two call detail page tickets (#35
transcript, score, flags; #36 step panel and coaching) and, through them, the
agent reviewing one of their calls. The stories are one vertical slice: read
one stored call and present it whole.

### User Story 1 - See one whole call in a single read (Priority: P1)

An agent opens one of their calls. The page asks for that call once and gets
back everything it shows: who called about what, the score, the transcript
with its notes, every required step and its details, and the flags. Nothing
is analyzed while the page waits.

**Why this priority**: This is the whole point of the ticket. Without it the
call detail page has nothing to show.

**Independent Test**: Build the HVB-DEMO-06 call as a test fixture in the #29
table shape, request its detail, and compare every value required by FR-003 to
FR-019 with the Figma frame. End-to-end on the running stack once #33's data is
loaded into the #29 tables.

**Acceptance Scenarios**:

1. **Given** the HVB-DEMO-06 Transfer money call (fixture), **When** its
   detail is requested, **Then** the response shows a score of 45 out of 100,
   "6 of 7" steps done right, 55 points lost, and the number of critical
   problems.
2. **Given** the same call, **When** its detail is requested, **Then** the
   header carries the call type, the call ID and the one-sentence summary.
3. **Given** the same call, **When** its detail is requested, **Then** the
   transcript lists every turn in order with speaker, time, and text; the
   wrong step's proving quote is at 0:33, and that turn carries its
   "Wrong: ..." note.
4. **Given** the same call, **When** its detail is requested, **Then** each
   required step appears in procedure order with its status and points, and
   its details give the sub-checks with their points, the proving quote with
   its time, and a coaching phrase.
5. **Given** a call where a step was done wrong, **When** its detail is
   requested, **Then** the turn that proves it carries a "Wrong: ..." note
   and the step appears among the flags.

---

### User Story 2 - See the details that belong to this call type (Priority: P2)

Some call types have details only they need. For Transfer money the agent sees
a table comparing what the caller asked for, what was logged, and whether
they match, for the amount, the source ("from") account and the destination
("to") account.

**Why this priority**: The mock shows this table, but the rest of the page
works without it, and other call types may have nothing here.

**Independent Test**: Request the Transfer money call and check the extra
block names its type and holds the three rows; request a call of another type
and check its block names that type and holds only what that type defines (or
nothing).

**Acceptance Scenarios**:

1. **Given** the Transfer money call, **When** its detail is requested,
   **Then** the extra block says it is the Transfer money type and holds rows
   for amount, from and to, each with "Caller asked", "Logged", and "Result".
2. **Given** a call of a type with no extra block defined, **When** its detail
   is requested, **Then** the extra block names that type and is empty, and
   the rest of the response is complete.

---

### User Story 3 - Clear answer for a call that does not exist (Priority: P2)

A link points to a call that is not stored (mistyped, removed, or another
environment). The page gets a clear "not found" answer instead of a broken or
partial result.

**Why this priority**: The page needs a defined state to show; it is small
but required by the ticket.

**Independent Test**: Request an ID that is not stored and check for a
not-found response (404) with a short message.

**Acceptance Scenarios**:

1. **Given** no call with the requested ID, **When** its detail is requested,
   **Then** the response is "not found" (404) and contains no call data.

---

### Edge Cases

- **A call with no mistakes**: every step completed; the response has no
  flags, no "Wrong" notes, 0 points lost, a score of 100, and zero critical
  problems.
- **A step missed entirely**: it has no proving quote or time; its evidence is
  present but empty (null) rather than left out, and it appears among the
  flags.
- **A step under review**: counted in the step total but not as done right; its
  points are not taken off the score. It is shown with its "under review"
  status, raises no flag, and its points are added to the call's points still
  under review, which marks the score as provisional.
- **A turn with no timing**: the turn is still listed; its time is empty.
- **A turn that is evidence for more than one step**: it carries one note per
  step.
- **A call that is stored but has no step results yet** (still pending): the
  response is returned with its header and transcript, an empty step list, no
  flags, and an empty score rather than a made-up one.
- **A stored "score" that disagrees with the step results**: the response uses
  the value worked out from the step results.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The service MUST return the detail of one call when asked for it
  by the call's numeric ID, the same `id` the call list returns and the analyze
  request takes. The dataset's external ID MUST NOT be accepted in its place.
- **FR-002**: The detail MUST be read from stored data only. Requesting it MUST
  NOT run any analysis or change any stored data.
- **FR-003**: The header MUST include the call type (key and display name), the
  call ID, the external ID as the call's reference, and the stored one-sentence
  summary.
- **FR-004**: The score section MUST include the score out of 100, the number of
  steps done right and the step total (for example "6 of 7"), the points lost,
  the number of critical problems, and the points still under review (0 when
  no step is under review).
- **FR-004a**: When any step is under review, the score MUST still be returned
  as 100 minus the points lost so far, and the points still under review MUST
  be greater than 0, so the screen can mark the score as provisional.
- **FR-005**: The service MUST work out the score as 100 minus the points lost
  on the call's step results, and MUST work out the step counts and the
  critical-problem count from those results. It MUST NOT take these from a
  value the screen sends, and the screen MUST NOT have to compute them.
- **FR-006**: The transcript MUST list every turn in order, each with its
  speaker (agent or caller), its start time, its text, and its notes.
- **FR-007**: A turn MUST carry an "Evidence for <step name>" note for each
  completed step it proves, and a "Wrong: <reason>" note for each step done
  wrong that it proves. A call with no wrong steps MUST have no "Wrong" notes.
- **FR-008**: The response MUST list every required step of the call in
  procedure order, each with its name, its status (completed, missed, wrong, or
  under review), the points it is worth, and the points lost on it.
- **FR-009**: Each step's details MUST include its sub-checks (each with
  description, points, and result), the quote that proves the step and the
  time of the turn it comes from, and a coaching phrase for missed and wrong
  steps (empty for completed and under-review steps, and whenever none is
  stored).
- **FR-010**: The response MUST include the flags: one per step that was missed
  or done wrong, in procedure order, each naming the step, its status, its
  severity, and its points lost. Steps that are completed or under review MUST
  NOT raise a flag, so a call with no mistakes has none.
- **FR-011**: The response MUST include an extra block whose content depends on
  the call type, with a field naming that type.
- **FR-012**: For Transfer money, the extra block MUST hold a table with one row
  each for amount, from (source account), and to (destination account), and
  for each row what the caller asked, what was logged, and the result: `match`,
  `mismatch`, or `reversed`. Both the from and to rows are `reversed` when the
  logged from is what the caller asked as to, and the logged to is what the
  caller asked as from. The backend decides this; the page only shows it.
- **FR-013**: Adding the extra block for another call type MUST NOT require
  changing the rest of the response. A call type with no block defined MUST
  return an empty block that still names the type.
- **FR-014**: A request for an ID with no stored call MUST return "not found"
  (404) with a short message and no call data.
- **FR-015**: The response shape MUST be defined by a typed schema, so a
  response that does not fit it fails rather than being sent.
- **FR-016**: The response shape MUST be listed in the service's endpoint
  catalogue, and an example response for the Transfer money call MUST be added
  to `docs/api-contract.md` so #35 and #36 can start before this merges.
- **FR-017**: Automated tests MUST cover the Transfer money call (every value on
  the mock), a call of one other type, a call with no mistakes, and the
  not-found case.
- **FR-018**: Each step's details MUST include the step's description as stored
  in the call's procedure rules (for example "Log the transfer correctly, then
  read back the amount, source and destination to confirm it is done."), or be
  empty when the rules have no description for that step key.
- **FR-019**: Each flag MUST include a one-sentence message. For Transfer money,
  when the step's field table disagrees with the caller, it is built from that
  table (for example "Moved $114 savings → checking. The caller asked for
  checking → savings."). Otherwise it is the step's stored reason (`detail`),
  or empty when none is stored.

### Key Entities *(include if feature involves data)*

- **Call detail**: everything about one call that the detail screen shows. Made
  of a header, a score summary, a transcript, steps, flags, and a type-specific
  block.
- **Header**: call type (key and display name), call ID, one-sentence summary.
- **Score summary**: score out of 100, steps done right, step total, points
  lost, critical-problem count, points still under review. Worked out from the
  step results.
- **Transcript turn**: position, speaker, start time, text, and zero or more
  notes linking it to steps.
- **Step result**: one required step of the call: name, position, status,
  points worth, points lost, severity, and its details (description, sub-checks,
  proving quote and time, coaching phrase). Stored by #33 now and #38 later; only read
  here.
- **Sub-check**: one scored part of a step: description, points, result.
- **Flag**: a step that was missed or done wrong, called out on the screen:
  step name, status, severity, points lost, message (see FR-010, FR-019).
- **Type-specific block**: a type name plus content defined per call type. For
  Transfer money, a field comparison table (field, caller asked, logged,
  result).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For the HVB-DEMO-06 call, 100% of the values required by FR-003
  to FR-019 match the Figma mock: score 45, "6 of 7", 55 points lost, the
  evidence quote at 0:33, the field table with From and To reversed, the step
  description, and the flag message.
- **SC-002**: For a call with no mistakes, the response has zero flags and zero
  "Wrong" notes, and a score of 100.
- **SC-003**: The call detail page needs exactly one request to render a whole
  call, and does no scoring or counting of its own.
- **SC-004**: Opening a call's detail changes no stored data and starts no
  analysis (verified by tests).
- **SC-005**: An unknown call ID always returns "not found" (404).
- **SC-006**: The example response is published in `docs/api-contract.md`
  before the endpoint merges, and #35 and #36 can build against it without
  asking the backend team for the shape.

## Assumptions

- "Call ID" is the call's own numeric ID (confirmed in Clarifications). The
  stored data's note that the external ID is "the call id in the URL" is out of
  date and should be corrected in this change.
- "Done right" means a step whose status is completed. Missed, wrong, and under
  review steps are not done right.
- Points lost come from the stored per-step points lost. Steps under review lose
  no points until they are judged; their points are reported as still under
  review (confirmed in Clarifications).
- A "critical problem" is a step whose stored severity is critical (21 or more
  points lost, per the shared severity bands).
- The time shown for a quote is the start time of the turn the quote comes from,
  shown as minutes and seconds (for example 0:33).
- The Transfer money field table is built from the comparison rows already
  stored with the step results. Only Transfer money gets a type-specific block
  in this feature; other types return an empty block until a later ticket
  defines theirs.
- Agents only see their own calls, but sign-in and per-agent access are not in
  this ticket's scope; the endpoint returns any stored call by ID.
- Depends on #29 (stored calls, turns, and step results). Loading #33's seed
  into the #29 tables is outside this feature; until then the mock values are
  proven with the HVB-DEMO-06 test fixture.
- The step description is returned as the procedure rules store it. Its
  wording differs from the Figma frame ("Log the transfer correctly…" vs
  "Submit the transfer…"); changing the wording belongs to the procedure files,
  not this endpoint.
- Hiding noise turns ("[noise]") is a display choice for the page; every
  stored turn is returned.
- Clean Architecture (constitution Principle VII) applies: the score, counts,
  notes, and flags are worked out in the backend's application/domain layers,
  not in the route handler, the database models, or the React page
  (Principle I).
