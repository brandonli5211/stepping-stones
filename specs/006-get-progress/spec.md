# Feature Specification: Get Progress

**Feature Branch**: `feat/37-progress`

**Created**: 2026-11-16

**Status**: Draft

**Input**: User description: "Feature 006 GetProgress (issue #37, backend half). GET /progress returns, for one agent over the last 8 weeks: the completion percent for each of the 8 weeks, this week compared with week 1, the percent per call type, the 'steps you skip most' rows (step, call type or 'All call types', recent results oldest to newest, summary line), and whether the data is demo data. One use case, GetProgress, with every CSC207 Clean Architecture part in its own class. Reuse the week/percent rules of the calls list. The by-type acceptance values are the real demo_48 values 88, 86, 85, 80, 79, 77, 73, 69, not Figma's 97..78. The Progress screen is a separate later feature (007)."

**Primary use case**: GetProgress (one use case for this feature).

## How issue #37 is split

Issue #37 asks for an API and a screen. That is two use cases, so it is two features, done in order:

| Feature | Use case | Covers |
|---|---|---|
| **006 (this spec)** | GetProgress | The progress numbers, worked out on the server and served to the screen. |
| 007 (later) | ViewProgress | The Progress screen: bar chart, by-call-type bars, dot rows, legend, "Demo data" badge. |

## Known mismatch with issue #37

The issue's done-when says the by-call-type values match Figma: 97, 95, 92, 90, 88, 86, 82, 78. Those values cannot be reached with the real step lists (schema3) and the 48 demo calls. For example, a call type with 4 calls of 5 steps can only show multiples of 5%.

This spec uses the values the demo data really gives: **88, 86, 85, 80, 79, 77, 73, 69**. The weekly values do match Figma: week 1 is 64% and week 8 is 90%. The Figma by-type bars need updating; this was already noted on issue #33.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See how my required steps change over 8 weeks (Priority: P1)

An agent opens Progress. The screen asks the server for the agent's progress and gets back one percent for each of the last 8 weeks (steps completed out of steps required), plus this week's numbers and the first week's percent to compare against.

**Why this priority**: The 8-week trend is the main thing the Progress screen shows, and the "64% to 90%" story is the centre of the demo.

**Independent Test**: With the demo data loaded and "today" fixed at 2026-10-09, ask for progress. The eight weekly percents are 64, 70, 68, 75, 80, 79, 86, 90. This week is 53 of 59 (90%) and the first week is 64%.

**Acceptance Scenarios**:

1. **Given** the 48 demo calls and today fixed at 2026-10-09, **When** progress is requested, **Then** there are exactly 8 weeks, oldest first, each with its Monday date, steps completed, steps required and percent: 16/25 = 64, 16/23 = 70, 17/25 = 68, 24/32 = 75, 45/56 = 80, 31/39 = 79, 19/22 = 86, 53/59 = 90.
2. **Given** the same data, **When** progress is requested, **Then** the last week is marked as the current week, this week is 53 of 59 (90%), the first-week percent is 64, and the comparison line is "Up from 64% in week 1". The numbers agree with the My calls card.
3. **Given** a week inside the 8 with no scored calls, **When** progress is requested, **Then** that week is still listed, with 0 steps and no percent.
4. **Given** an agent with no scored calls in the 8 weeks, **When** progress is requested, **Then** the answer has 8 empty weeks, no this-week numbers, no first-week percent, no comparison line, no call types and no step rows. It is not an error.
5. **Given** this week's percent is lower than the first week's, **When** progress is requested, **Then** the comparison line reads "Down from 64% in week 1". When they are equal it reads "Same as 64% in week 1". When either percent is unknown there is no comparison line.

---

### User Story 2 - See which call types I do well and badly (Priority: P2)

The same answer has one percent per call type, over the same 8 weeks, best first.

**Why this priority**: It tells the agent where to focus, but it is secondary to the trend.

**Independent Test**: With the demo data, the by-call-type list is Check balance 88, Get branch hours 86, Order checks 85, Reset password 80, Pay bill 79, Schedule appointment 77, Replace card 73, Transfer money 69.

**Acceptance Scenarios**:

1. **Given** the demo data, **When** progress is requested, **Then** the call types and their numbers are, in this order: Check balance 42/48 = 88 (8 calls), Get branch hours 24/28 = 86 (7), Order checks 17/20 = 85 (4), Reset password 20/25 = 80 (5), Pay bill 22/28 = 79 (4), Schedule appointment 27/35 = 77 (5), Replace card 35/48 = 73 (8), Transfer money 34/49 = 69 (7).
2. **Given** a call type with no scored calls in the 8 weeks, **When** progress is requested, **Then** that call type is not listed.

---

### User Story 3 - See the steps I skip most (Priority: P3)

The answer has one row per required step. A step that every call type has (greet, offer further help, close) gets one row labelled "All call types" over the agent's last 10 calls. Every other step gets a row for its call type over the agent's last 5 calls of that type. Each row shows the result of each of those calls, oldest to newest, and a summary line. Rows with the most misses come first, then the steps that were always done.

**Why this priority**: It is the most specific coaching on the screen, and it needs the first two stories' data rules to be in place.

**Independent Test**: With the demo data, the first rows are "Confirm replacement" (Replace card: completed, missed, completed, missed, missed; "Missed on 3 of your last 5 replace-card calls") and "Confirm appointment" (Schedule appointment: missed, missed, completed, completed, missed). The Transfer money row "Submit and confirm transfer" ends with a wrong result, which is the call the My calls table labels "Wrong: Submit and confirm transfer".

**Acceptance Scenarios**:

1. **Given** the demo data, **When** progress is requested, **Then** there are 26 rows: 13 with at least one miss, then 13 that were always done.
2. **Given** the demo data, **When** progress is requested, **Then** the rows with misses are, in order:

   | # | Step | Label | Results, oldest to newest | Misses |
   |---|---|---|---|---|
   | 1 | Confirm replacement | Replace card | done, missed, done, missed, missed | 3 of 5 |
   | 2 | Confirm appointment | Schedule appointment | missed, missed, done, done, missed | 3 of 5 |
   | 3 | Offer further help | All call types | six done, missed, done, done, missed | 2 of 10 |
   | 4 | State account balance | Check balance | done, done, missed, missed, done | 2 of 5 |
   | 5 | Collect company address | Pay bill | missed, missed, done, done | 2 of 4 |
   | 6 | Collect time | Schedule appointment | done, missed, done, done, missed | 2 of 5 |
   | 7 | Collect source account | Transfer money | missed, done, done, missed, done | 2 of 5 |
   | 8 | Submit and confirm transfer | Transfer money | done, missed, done, done, wrong | 2 of 5 |
   | 9 | Collect home address | Order checks | missed, done, done, done | 1 of 4 |
   | 10 | Collect payment amount | Pay bill | missed, done, done, done | 1 of 4 |
   | 11 | Collect phone number | Reset password | done, done, missed, done, done | 1 of 5 |
   | 12 | Collect transfer amount | Transfer money | done, done, done, missed, done | 1 of 5 |
   | 13 | Collect destination account | Transfer money | done, done, done, missed, done | 1 of 5 |

3. **Given** the demo data, **When** progress is requested, **Then** each result in the Replace card and Transfer money rows equals that step's status on the same call in the My calls list.
4. **Given** a row with misses, **When** its summary line is read, **Then** it is "Missed on 3 of your last 5 replace-card calls" for a single call type and "Missed on 2 of your last 10 calls" for an "All call types" row. A row with no misses reads "Done on all of your last 5 replace-card calls" or "Done on all of your last 10 calls". With one call, the line says "call".
5. **Given** a step that is wrong on a call, **When** the row is built, **Then** that result is shown as wrong and it counts as a miss.
6. **Given** a step that is under review on a call, **When** the row is built, **Then** that call is left out of the row and the window reaches one call further back.

---

### User Story 4 - Know when the numbers are made up (Priority: P4)

The answer says whether any of the calls it counted are demo data, so the screen can show a "Demo data" badge.

**Why this priority**: It is one flag, but it stops made-up results from being mistaken for real analysis.

**Independent Test**: With the demo data loaded, the answer says demo data is true. With only analyser-scored calls, it says false.

**Acceptance Scenarios**:

1. **Given** at least one counted call was scored by the demo seed, **When** progress is requested, **Then** demo data is true.
2. **Given** no counted call was scored by the demo seed, or no call was counted at all, **When** progress is requested, **Then** demo data is false.

---

### Edge Cases

- **Which calls count**: only scored calls of the requested agent that started inside the 8 weeks. Calls that are pending, need review or failed are left out everywhere.
- **The 8 weeks**: the week that contains "today" and the 7 weeks before it. Weeks start on Monday, in UTC, the same as the My calls card. "Today" is the same clock the calls list uses, so a fixed demo date applies here too.
- **Under review**: a step that is under review is neither completed nor required until it is resolved. It is left out of the weekly and by-call-type numbers, and out of the step rows. With the demo data no step is under review.
- **Wrong**: counts as not completed in every number. In a step row it keeps its own "wrong" result.
- **Week 1 in the comparison**: the first-week percent is the first of the 8 weeks that has any scored call, by the same rule as the My calls card. With the demo data that is the first calendar week.
- **Fewer calls than the window**: the row uses the calls there are ("Missed on 2 of your last 4 pay-bill calls").
- **A step with no resolved result in the 8 weeks**: it has no row.
- **Rounding**: percents are whole numbers, rounded the same way as the My calls card.
- **Order of call types**: highest percent first. Call types with the same percent are in name order.
- **Order of step rows**: most misses first. Rows with the same number of misses are in label order with "All call types" first, then in the step's order in its procedure.
- **No agent given**: the numbers cover every agent's calls, as the calls list does today.
- **An agent id that is not a number**: the request is rejected as invalid.
- **The shared rules cannot be read**: the list of steps shared by all call types comes from the rules file. If that file is missing, the request fails as "service unavailable" with no partial answer, the same as call analysis does today. The calls list keeps working.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST offer one read-only request, `GET /progress`, that returns an agent's progress for the last 8 weeks. It takes an optional agent id and changes nothing.
- **FR-002**: The answer MUST list exactly 8 weeks, oldest first. Each week has its Monday date, steps completed, steps required, a percent (none when no steps are required) and whether it is the current week.
- **FR-003**: The answer MUST give this week's steps completed, steps required and percent, and the first-week percent, using the same rules as the My calls card. The two screens MUST agree for the same data.
- **FR-004**: The answer MUST list each call type that has scored calls in the 8 weeks, with its name, steps completed, steps required, percent and number of calls, highest percent first.
- **FR-005**: The answer MUST list step rows as described in User Story 3. The window is the last 10 calls for a step shared by all call types and the last 5 calls of that call type for any other step.
- **FR-006**: Each step row MUST have the step's key and name, its call type and label (the call type's name or "All call types"), the results oldest to newest, the number of misses, the number of calls in the window and the summary line.
- **FR-007**: Step rows MUST be ordered with the most misses first, then the always-done rows, with ties broken as in Edge Cases.
- **FR-008**: A wrong step MUST count as not completed. A step under review MUST be left out of every number and row until it is resolved.
- **FR-009**: The answer MUST say whether any counted call is demo data.
- **FR-010**: Every number MUST be worked out on the server from the stored calls with database queries. No stored procedure is used. The screen MUST NOT have to compute a percent, a count, an order or a summary line.
- **FR-011**: The week and percent rules MUST be the ones the calls list already uses. They MUST NOT be copied into a second place.
- **FR-012**: The progress rules (the 8 weeks, by-call-type numbers, step rows, ordering, summary counts) MUST be computable and testable without a database or web server, and MUST be tested with a small fixed dataset. Met by `test_progress_small_dataset` (six calls over three weeks).
- **FR-013**: The use case MUST be built with every Clean Architecture part named in the course (CSC207), each in its own class: Controller, Input Boundary, Input Data, Interactor, Output Boundary, Output Data, Presenter, View Model and Data Access Interface.
- **FR-014**: The calls list (`GET /calls`) and call analysis (`POST /calls/{id}`) MUST NOT change.
- **FR-015**: No schema change is needed. If one turns out to be needed, it MUST ship as a migration in the same change.
- **FR-017**: The answer MUST include the comparison line for this week against the first week ("Up from", "Down from" or "Same as", then the first-week percent and "in week 1"), written by the server. It is absent when this week or the first week has no percent. *(Added on 2026-11-16 at the product owner's request, so the screen only displays it.)*
- **FR-016**: When the shared rules cannot be read, the request MUST fail as "service unavailable" and MUST NOT return a partial answer. *(Added during planning.)*

### Key Entities

- **Week**: one of the 8 weeks. It has a Monday date, steps completed, steps required, a percent and whether it is the current week.
- **Call type progress**: one call type's name, steps completed, steps required, percent and number of calls over the 8 weeks.
- **Step row**: one step's recent history. It has the step, a label (a call type or "All call types"), the results oldest to newest, the misses, the window size and a summary line.
- **Step result**: completed, missed or wrong for one step on one call.
- **Shared step**: a step that every call type's procedure has. Today these are greet and open, offer further help, and close.
- **Progress**: the whole answer: the 8 weeks, this week, the first-week percent, the call types, the step rows and the demo-data flag.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: With the demo data and today fixed at 2026-10-09, the weekly percents are 64, 70, 68, 75, 80, 79, 86, 90.
- **SC-002**: With the same data, the by-call-type percents are 88, 86, 85, 80, 79, 77, 73, 69, in the order given in User Story 2.
- **SC-003**: With the same data, there are 26 step rows, and the 13 rows with misses are the ones in User Story 3, in that order.
- **SC-004**: This week and the first-week percent are equal to the My calls card's numbers for the same data (53 of 59, 90%, and 64%).
- **SC-005**: Every result in the Replace card and Transfer money rows equals the same step's status in the My calls list.
- **SC-006**: Every progress rule has an automated test that runs with no database. A small fixed dataset (`test_progress_small_dataset`) covers the weekly and by-call-type percents, the top step row and its summary line, wrong counting as a miss, and under review being left out of the step rows. The demo data (`test_progress_demo_48`) covers the two window sizes and the full row order.
- **SC-007**: The My calls list answers exactly as it did before this feature.

## Assumptions

- **Under review is left out of both sides** of every progress percent, as issue #37 asks. The My calls card (issue #30) counts steps under review as required. The two can differ while a step is under review. They are equal for the demo data, where nothing is under review. Changing the My calls card is out of scope.
- **Every step row is returned**, in order. How many rows the screen shows is decided in feature 007.
- **The summary line and the comparison line are written by the server**, so the screen does not build sentences from counts or percents. The call type appears as its key with hyphens ("replace-card"), matching the example in issue #37.
- **"Demo data" means scored by the demo seed.** The loader marks those calls, and the curated results file is applied on top of them.
- **Shared steps** come from the rules the procedures already define. No new list is added.
- **The 8 weeks are calendar weeks**, so the chart always has 8 bars. The calls list uses a rolling 8 × 7 days. For the demo data both cover the same 48 calls.
- **The clock** is the one feature 003 added (`DEMO_TODAY` for demos, the real time otherwise).
- **Signing in** is out of scope. The agent is named by an id in the request, as on the calls list.
- **The Progress screen** (feature 007) and the Figma update are out of scope.
- **Depends on** issue #33's branch (`feat/33-load-demo-48`) for the demo data and the calls-list rules.
