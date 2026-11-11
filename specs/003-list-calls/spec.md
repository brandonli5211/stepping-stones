# Feature Specification: List Calls with a Demo Clock

**Feature Branch**: `feat/33-load-demo-48`

**Created**: 2026-11-11

**Status**: Draft

**Input**: User description: "Feature B — ListCalls (issue #33). Move the week window, the 'this week' choice, the percent, and the missed/wrong result label out of the calls list handler into a ListCalls use case, behind a thin handler. Keep the exact label wording. An optional DEMO_TODAY instant is read only at the outer edge. Without it, the use case uses the real current time and the response matches today's behavior exactly. With it, 'this week' and the weeks filter use that instant. Response shape unchanged. Acceptance with demo_48 loaded and applied, DEMO_TODAY=2026-10-09T23:59:59+00:00, weeks=8: this week 53 of 59, 90%; first week 64%; weekly percents 64, 70, 68, 75, 80, 79, 86, 90; call a2f086d27b3a4f96 labelled 'Wrong: Submit and confirm transfer'. Exactly one use case: ListCalls. Analyze-call stays untouched and moves in a following Feature C."

**Primary use case**: ListCalls (one use case for this feature). Analyzing a single call is a separate, later feature, AnalyzeCall (Feature C).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Present the 8-week demo as if it were the demo day (Priority: P1)

A presenter shows the coaching screen using the demo calls. Those calls are dated 2026-08-18 to 2026-10-09. The presenter starts the service with a demo "today" set to the end of 2026-10-09. The header then shows the week that contains that instant as "this week", and the "last N weeks" filter counts back from that instant, so the 8-week progress story appears exactly as curated.

**Why this priority**: without it the demo calls fall outside "this week" and outside any recent-weeks window on the real calendar. The demo then shows empty or wrong progress numbers.

**Independent Test**:
1. Load and apply the demo_48 results (feature ApplyDemoResults).
2. Start the service with the demo "today" set to 2026-10-09T23:59:59Z.
3. Request the list for the last 8 weeks.

The header shows this week as 53 of 59 required steps, 90%, and the first week as 64%.

**Acceptance Scenarios**:

1. **Given** demo_48 loaded and applied and the demo "today" 2026-10-09T23:59:59Z, **When** the list is requested for the last 8 weeks, **Then**:
   - calls reviewed is 48;
   - this week shows 53 steps completed of 59, percent 90;
   - the first-week percent is 64.
2. **Given** the same setup, **When** the eight Monday-start weeks in the window are grouped the same way the list groups them, **Then** their percents are, in order: 64, 70, 68, 75, 80, 79, 86, 90.
3. **Given** the same setup, **When** the list shows call `a2f086d27b3a4f96`, **Then** its result label is exactly "Wrong: Submit and confirm transfer".
4. **Given** a demo "today" that is not a valid date-time with an offset, **When** the service starts, **Then** it refuses to start and names the bad value. It does not quietly fall back to the real time.

---

### User Story 2 - Normal use is unchanged (Priority: P1)

A coach uses the screen with no demo "today" set. Everything behaves exactly as before this change: the same calls in the same order, the same steps, labels, header numbers and filters. The response has the same fields.

**Why this priority**: the restructuring must not change what coaches see. A regression here breaks the main screen.

**Independent Test**: with no demo "today", compare the list response before and after the change for the same data and the same query parameters, including no parameters, `weeks`, `agent_id`, `call_type` and `has_missed`. Every response is identical. The only difference allowed is in timestamps produced by the clock itself, and the response contains none.

**Acceptance Scenarios**:

1. **Given** no demo "today", **When** the list is requested with any combination of the existing filters, **Then** the response is identical to the response before this change.
2. **Given** no demo "today", **When** "this week" is computed, **Then** it is the Monday-start week (UTC) containing the real current time.
3. **Given** a call whose first missed-or-wrong step, in step order, is missed, **When** it is listed, **Then** its label is "Missed <step name>", with no colon. **Given** the first such step is wrong, **Then** the label is "Wrong: <step name>", with a colon. **Given** no step is missed or wrong, **Then** the call has no result.

---

### Edge Cases

- **No calls in "this week"**: this week is empty (no numbers), as today.
- **Weeks with zero required steps**: the percent is empty rather than a division error, as today.
- **Rounding**: percents round to the nearest whole number the same way as today, with exact halves going to the even neighbour. No current demo week lands on a half.
- **Calls dated after the demo "today"**: they are still listed and counted, because today's behavior has no upper bound. The demo data has none.
- **Demo "today" with no offset**, such as `2026-10-09T23:59:59`: treated as malformed (story 1, scenario 4), so the instant is never ambiguous.
- **Without `weeks`**: there is no date limit. Header numbers cover all calls (for the agent, if one is given), and "this week" still uses the demo "today" when it is set.
- **`agent_id` filter**: limits both the list and the header numbers.
- **`call_type` and `has_missed` filters**: limit only the list, not the header numbers, as today.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The list MUST return the most recent calls, newest first, with ties broken by the newer record first. The default number is 10, and the allowed range is 1–100.
- **FR-002**: Each listed call MUST carry the same fields as today, with each call's steps in step order (key, name, status):
  - id, external id, call type, call type name, start time, status, score
  - steps completed, steps total
  - its steps
  - its result
- **FR-003**: A call's result MUST come from its first step, in step order, whose status is missed or wrong:
  - a missed step gives label `Missed <step name>`, with no colon;
  - a wrong step gives label `Wrong: <step name>`, with a colon;
  - the result also carries that step's status;
  - with no such step, the result is empty.
- **FR-004**: The window MUST consist of the optional "last N weeks" limit (N from 1 to 520, counted back from the reference instant) and the optional agent filter. It applies to both the list and the header numbers. The call type filter (with the same name normalization as today) and the "has a missed or wrong step" filter MUST apply only to the list.
- **FR-005**: The header MUST report:
  - calls reviewed: the number of calls in the window;
  - the requested weeks value;
  - "this week": steps completed, steps total and percent for the Monday-start week containing the reference instant, or empty if that week has no calls;
  - the first-week percent: the earliest Monday-start week in the window.
- **FR-006**: Weeks MUST be Monday-start weeks in UTC, grouped exactly as today.
- **FR-007**: Percent MUST be `round(100 × completed ÷ total)`, or empty when the total is 0.
- **FR-008**: The reference instant MUST be the demo "today" when it is configured, and otherwise the real current time.
- **FR-009**: The demo "today" MUST be read from the `DEMO_TODAY` setting at the outer edge of the system only:
  - it must be an ISO 8601 date-time with a UTC offset;
  - a missing value means "use the real time";
  - a malformed value MUST stop the service from starting, with a message naming the value.
- **FR-010**: The response fields and their meaning MUST stay unchanged. No field is added or removed.
- **FR-011**: The rules for the window, "this week", the percent and the result label MUST be computable and testable without a database or web server.
- **FR-012**: The list request handler MUST only translate the request and response and delegate. It holds none of the rules above.
- **FR-013**: Analyzing a single call MUST keep working exactly as today. It is not changed by this feature.

### Key Entities

- **Reference instant**: the "now" used for the window and for "this week". It is either the demo "today" or the real time.
- **Call summary**: one listed call, with the fields in FR-002.
- **Step outcome**: key, name and status (completed, missed, wrong, under review), in step order.
- **Result**: the label and status taken from the first missed or wrong step.
- **Week totals**: for one Monday-start week, the steps completed and steps total. The percent comes from these.
- **Header**: calls reviewed, the weeks value, this week's totals and percent, and the first-week percent.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: With demo_48 loaded and applied, the demo "today" at 2026-10-09T23:59:59Z and the last 8 weeks requested, the header shows:
  - this week: 53 of 59 steps, 90%;
  - first week: 64%;
  - 48 calls reviewed.
- **SC-002**: With the same setup, the eight weekly percents, grouped as the list groups them, are 64, 70, 68, 75, 80, 79, 86, 90.
- **SC-003**: With the same setup, call `a2f086d27b3a4f96` is labelled exactly "Wrong: Submit and confirm transfer".
- **SC-004**: With no demo "today", list responses for the same data and parameters are identical before and after the change. That holds for 100% of the compared requests, including:
  - no parameters;
  - `weeks=8`;
  - `has_missed=true`;
  - `call_type=transfer_money`;
  - `limit=100`.
- **SC-005**: Every rule in FR-003 to FR-008 has an automated test that runs with no database.

## Assumptions

- The database session reports times in UTC, as the local stack does. Weekly grouping therefore matches the UTC Monday used for "this week", as it does today.
- The demo "today" is a presenter setting for local demos. It is read once when the service starts; changing it means restarting the service.
- 8 of the demo call IDs also exist in `calls_sample_56`, as noted in feature ApplyDemoResults. That doesn't affect this feature.
- Only the screen's current inputs are kept. No new filter or field is added.
- The screen code is not changed by this feature.
- Analyzing a call (`POST /calls/{call_id}`) stays as it is for now. Feature C (AnalyzeCall) brings its file into compliance before the pull request for issue #33 opens.
