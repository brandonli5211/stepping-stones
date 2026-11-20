# Feature Specification: View Progress

**Feature Branch**: `feat/37-progress`

**Created**: 2026-11-16

**Status**: Draft

**Input**: User description: "Feature 007 ViewProgress (issue #37, frontend half). The Progress screen in the TypeScript app shell shows GET /progress: the 8-week bar chart with the current week highlighted, this week against week 1, the 'By call type' bars, the 'steps you skip most' rows of stones with their summary lines, the legend, and a 'Demo data' badge while the data is made up. One use case, ViewProgress, with the nine CSC207 parts on the frontend side where they apply; components only render."

**Primary use case**: ViewProgress (one use case for this feature).

## Where this sits

Issue #37 is split into two features. Feature 006 (GetProgress, done) works out the progress numbers on the server. This feature shows them. It builds on the TypeScript app shell from issue #31 (`feat/31-app-shell-ts`, merged into this branch), which already has a Progress entry in the menu and a placeholder page.

The by-call-type values on screen are the real demo values (88, 86, 85, 80, 79, 77, 73, 69), not Figma's 97…78. See the mismatch note in the feature 006 spec.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See my 8-week trend (Priority: P1)

An agent opens Progress from the menu. The page shows a bar for each of the last 8 weeks with its percent, the current week's bar highlighted, and a line that compares this week with the first week.

**Why this priority**: The trend is the main point of the screen and the centre of the demo.

**Independent Test**: With the demo data and today fixed at 2026-10-09, open Progress. There are 8 bars reading 64%, 70%, 68%, 75%, 80%, 79%, 86%, 90%. The last bar is highlighted. The page says "53 of 59 required steps completed" this week and "Up from 64% in week 1".

**Acceptance Scenarios**:

1. **Given** the demo data, **When** the agent opens Progress, **Then** the chart shows 8 bars, oldest on the left, each with its percent and its week's start date ("Aug 17" … "Oct 5"). Each bar's height matches its percent.
2. **Given** the same page, **When** the agent looks at the chart, **Then** only the current week's bar is highlighted, and it is also marked "This week" in words, not by colour alone.
3. **Given** the server sends the comparison line "Up from 64% in week 1", **When** the page is shown, **Then** that line appears word for word. The page does not work out "Up", "Down" or "Same" itself.
4. **Given** a week with no percent, **When** the chart is drawn, **Then** that week has an empty bar and "–" in place of a percent.
5. **Given** the answer has no this-week numbers, **When** the page is shown, **Then** it says "No analysed calls this week".
6. **Given** the answer has no comparison line, **When** the page is shown, **Then** no comparison line is shown.

---

### User Story 2 - See how each call type is going (Priority: P2)

Under "By call type", the page shows one bar per call type with its name and percent, in the order the server sends them.

**Why this priority**: It shows where to focus, after the trend.

**Independent Test**: With the demo data, the list reads Check balance 88%, Get branch hours 86%, Order checks 85%, Reset password 80%, Pay bill 79%, Schedule appointment 77%, Replace card 73%, Transfer money 69%.

**Acceptance Scenarios**:

1. **Given** the demo data, **When** the agent opens Progress, **Then** the eight call types appear in the order above, each with a bar as long as its percent and the text "N of M steps".
2. **Given** a call type with no percent, **When** it is shown, **Then** its bar is empty and it reads "–".

---

### User Story 3 - See the steps I skip most (Priority: P3)

Under "Steps you skip most", the page shows rows. Each row has the step's name, its call type or "All call types", one stone per recent call from oldest to newest, and the summary line the server wrote. A legend explains the stones.

**Why this priority**: It is the most specific coaching on the screen, and it depends on the page already loading.

**Independent Test**: With the demo data, the first row is "Confirm replacement", "Replace card", five stones (completed, missed, completed, missed, missed) and "Missed on 3 of your last 5 replace-card calls".

**Acceptance Scenarios**:

1. **Given** the demo data, **When** the agent opens Progress, **Then** the first 5 rows are shown, in the server's order: Confirm replacement, Confirm appointment, Offer further help, State account balance, Collect company address.
2. **Given** more rows than are shown, **When** the agent chooses "Show all 26 steps", **Then** every row is shown, and the control changes to "Show fewer".
3. **Given** a row, **When** it is drawn, **Then** its stones are in the server's order, each stone's look and hidden text match its result (completed, missed or wrong), and the summary line is shown word for word.
4. **Given** 5 rows or fewer, **When** the page is shown, **Then** there is no "Show all" control.
5. **Given** the page, **When** the agent looks below the rows, **Then** a legend shows the stone for each result.

---

### User Story 4 - Know when the numbers are made up, and when something went wrong (Priority: P4)

The page shows a "Demo data" badge when the server says the data is demo data. While loading, with no data, or after a failure, it says so plainly.

**Why this priority**: It keeps made-up results from being mistaken for real ones and keeps the page honest when there is nothing to show.

**Independent Test**: With the demo data the badge shows. With the server stopped, the page shows "Couldn't load your progress" and the reason.

**Acceptance Scenarios**:

1. **Given** the server says demo data is true, **When** the page is shown, **Then** a "Demo data" badge is next to the title. When it says false, there is no badge.
2. **Given** the request is still running, **When** the page is shown, **Then** it says "Loading your progress…".
3. **Given** the request fails, **When** the page is shown, **Then** an alert says "Couldn't load your progress" with the reason, and no chart is drawn.
4. **Given** the answer has no call types and no step rows, **When** the page is shown, **Then** it says "No analysed calls in the last 8 weeks" in place of the three sections.
5. **Given** the agent leaves Progress and comes back, **When** the page opens again, **Then** it loads fresh numbers.

---

### Edge Cases

- **Which agent**: the page asks for the agent set for the app (the same setting the calls page uses). With no setting, it asks for everyone's calls.
- **Sample mode**: when the app runs with sample data and no server, Progress shows a built-in sample answer, as the shell does for calls.
- **A result the page does not know**: its stone is shown as under review, as the shell's stone already does.
- **Leaving before the answer arrives**: a late answer is ignored. It does not show on another page or cause an error.
- **Long names**: a long step or call type name wraps. It does not push the stones off the row.
- **Narrow window**: the 8 bars stay readable down to a laptop-width window. Phone layout is out of scope.
- **Other pages**: My calls, Call detail and Procedures look and behave as before.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Progress page MUST get its numbers from the server's progress answer (feature 006) each time it is opened.
- **FR-002**: The page MUST show the 8 weeks as a bar chart, oldest first, with each week's percent and start date, and the current week highlighted and marked in words.
- **FR-003**: The page MUST show this week's steps completed and required, and the server's comparison line against the first week, unchanged. When the server sends none, none is shown.
- **FR-004**: The page MUST show one bar per call type with its name, percent and steps, in the server's order.
- **FR-005**: The page MUST show the step rows in the server's order, 5 at first, with a control to show all and to show fewer.
- **FR-006**: Each step row MUST show the step name, the label, one stone per result in the server's order, and the server's summary line unchanged.
- **FR-007**: The page MUST show a legend for the stones.
- **FR-008**: The page MUST show a "Demo data" badge exactly when the server says the data is demo data.
- **FR-009**: The page MUST show a loading message, an error message with the reason, and an empty message, as described in User Story 4.
- **FR-010**: The page MUST NOT compute a percent, a count of misses, an order of rows or call types, a summary line, a comparison line, or whether a step was completed. It only shows what the server sends. Turning a percent into a bar length and a date into a short label are display choices and are allowed.
- **FR-011**: Every result MUST be told apart by more than colour: each stone has its own shape detail and a text label for screen readers.
- **FR-012**: The use case MUST be built with the Clean Architecture parts named in the course (CSC207), each in its own class: Controller, Input Boundary, Input Data, Interactor, Output Boundary, Output Data, Presenter, View Model and Data Access Interface. The page component MUST only render the view model and pass on what the agent does.
- **FR-013**: Reaching the server MUST go through one typed gateway. Shaping the answer for display MUST sit in the presenter and view model, not in components.
- **FR-014**: All new frontend files MUST be TypeScript, styled with the project's utility classes and shared components. No new library is added.
- **FR-015**: The shell's placeholder Progress content MUST be replaced by this page. The other pages MUST NOT change.
- **FR-016**: Every new function MUST have a unit test. The tests MUST cover the view model for a full answer, an empty answer, a failure, and showing all rows. **Partly met since the 2026-11-19 test cut**: a full answer with showing all rows (through the whole app) and a failure are tested; the empty answer and the per-function tests are not.

### Key Entities

- **Progress answer**: what the server sends: the demo-data flag, 8 weeks, this week, the first-week percent, the call types and the step rows.
- **Progress view**: what the page draws: a state (loading, failed, empty or ready), the badge, the week bars, the this-week line, the comparison line, the call type bars, the visible step rows and the "show all" control.
- **Week bar**: a label, a percent text, a bar height and whether it is the current week.
- **Call type bar**: a name, a percent text, a steps text and a bar length.
- **Step row view**: a step name, a label, a list of stones and a summary line.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: With the demo data and today fixed at 2026-10-09, the page shows the eight weekly percents 64, 70, 68, 75, 80, 79, 86, 90, with only the last bar highlighted.
- **SC-002**: The page shows "53 of 59 required steps completed" and "Up from 64% in week 1", the same numbers as the My calls card.
- **SC-003**: The page shows the eight call types with 88, 86, 85, 80, 79, 77, 73, 69, in that order.
- **SC-004**: The first five step rows match the server's first five, and "Show all" reveals all 26.
- **SC-005**: The Replace card and Transfer money stones match those calls' stones on My calls.
- **SC-006**: The "Demo data" badge shows with the demo data.
- **SC-007**: With the server stopped, the page shows an error message within a few seconds and no chart.
- **SC-008**: The full answer with "Show all", the failure state and the layering have automated tests, and the existing frontend tests still pass. *(Narrowed on 2026-11-19, when the tests were cut; see plan.md Complexity Tracking.)*
- **SC-009**: A screenshot of the page with the demo data is ready for the pull request, to sit next to the Figma frame.

## Assumptions

- **Five rows first.** The server returns all 26 rows. The page shows the first 5 and lets the agent show all. The number is one named setting in the view model, so it can change without touching the server or the components. *(5 was confirmed by the product owner on 2026-11-16.)*
- **Week labels are start dates** ("Aug 17"), in English, taken from the server's week start.
- **The comparison line comes from the server** (feature 006, FR-017). The page displays it and does not compare percents.
- **No chart library.** Bars are drawn with the page's own markup and styles, so no new dependency needs a constitution change.
- **The agent setting** is the existing `VITE_AGENT_ID`. Signing in is out of scope.
- **The legend** is the shell's existing legend, which also lists "Under review". The server leaves under-review results out of the rows, so that stone does not appear in them.
- **The "See your progress" button on My calls** is not wired here. The calls page is legacy JavaScript and is not touched by this feature.
- **The Figma frame** is not available to the build. Layout follows the issue's description and the shell's look. The pull request screenshot is compared with Figma by a person.
- **Depends on** feature 006 on this branch and on the app shell from `feat/31-app-shell-ts` (PR #48, not yet merged to main).
