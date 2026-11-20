# Feature Specification: App Shell and Shared Screen Pieces

**Feature Branch**: `feat/31-app-shell-ts`

**Created**: 2026-11-11

**Status**: Draft

**Input**: User description: "App shell and shared UI components (#31). All four screens share the same left menu, colors, fonts and the little colored stones that show a step's status. Build these once so everyone else can reuse them. Pages and navigation for My calls, a call detail page, Progress and Procedures. The left menu highlights the current page and shows the signed-in agent's name and role. The colors, fonts, spacing and card style from Figma. Reusable pieces: the step stone (Completed, Missed, Wrong, Under review), the status legend, the score ring, a page header, a card, an empty state and an error state. A small helper for calling the API and a sample data mode that uses example responses instead of the real API, so a screen can be built before its endpoint exists. Done when all four pages open inside the shell with placeholder content, the stone shows all four statuses and has a text label so color is not the only signal, sample data mode turns on with one setting, the app still starts with one command, and the pull request has screenshots next to the design frames."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Move between the coaching screens (Priority: P1)

An agent opens Stepping Stones and sees one consistent frame: a menu on the
left and the current screen beside it. The menu lists My calls, Progress and
Procedures, marks the screen the agent is on, and shows the agent's name and
role. Opening a single call shows the call detail screen inside the same
frame, with a way back to My calls, and the menu still marks My calls.

**Why this priority**: Every later coaching screen lives inside this frame.
Until it exists, each teammate builds their own menu and layout, and the
screens drift apart.

**Independent Test**: Open the app, use the menu to visit each screen, open
a call, and go back. Every screen appears inside the same frame, the right
menu item is marked each time, and the agent's name and role stay visible.

**Acceptance Scenarios**:

1. **Given** the app is open, **When** the agent chooses Progress in the
   menu, **Then** the Progress screen shows and Progress is marked as the
   current item.
2. **Given** the agent is on My calls, **When** they open a call, **Then**
   the call detail screen shows, My calls stays marked, and a back link
   returns to My calls.
3. **Given** any screen is showing, **When** the agent looks at the menu,
   **Then** it shows the configured agent's name and role.
4. **Given** someone types an address that is not one of the four screens,
   **When** the app loads, **Then** it shows My calls instead of a blank or
   broken page.

---

### User Story 2 - Read step results the same way everywhere (Priority: P2)

Wherever a screen built on the shared pieces shows a call's steps, each
step is shown as a stone. Completed,
Missed, Wrong and Under review each have their own shape and a text label,
so the result can be read without relying on color. A legend explains the
stones, a ring shows the call's score, and every screen uses the same
header, card, empty message and error message.

**Why this priority**: Agents learn one visual language once. Coaches and
teammates can rely on a stone meaning the same thing on every screen.

**Independent Test**: View a screen that shows one stone of each status,
the legend, a score ring, an empty message and an error message. Each stone
is distinguishable in grayscale and announces its label to assistive
technology.

**Acceptance Scenarios**:

1. **Given** a step result of Completed, Missed, Wrong or Under review,
   **When** it is shown, **Then** it appears as that status's stone with the
   status name as its text label.
2. **Given** the screen is viewed without color, **When** the agent compares
   the four stones, **Then** each status can still be told apart by shape
   or label.
3. **Given** a score supplied for a call, **When** the score ring shows it,
   **Then** it displays exactly that score and never a value worked out on
   the screen.
4. **Given** a screen has no data to show, **When** it loads, **Then** it
   shows the shared empty message; **given** its data cannot be loaded,
   **then** it shows the shared error message.

---

### User Story 3 - Build a screen before its data exists (Priority: P3)

A teammate building a screen loads its data through the shared access
point. With one setting turned on, that access point answers with example
results shaped like the real ones, so the screen can be built and reviewed
before its endpoint is ready. With the setting off, it uses the real
service.

**Why this priority**: Screens and endpoints are built by different people
at different times. Sample mode stops one from blocking the other.

**Independent Test**: Ask the shared access point for the calls list with
the setting on and confirm it returns example content without contacting
the real service. Ask again with the setting off and confirm it requests
the configured service address.

**Acceptance Scenarios**:

1. **Given** sample data mode is on, **When** a screen asks the shared
   access point for data, **Then** it receives example content and the real
   service is not contacted.
2. **Given** sample data mode is off, **When** a screen asks the shared
   access point for data, **Then** the request goes to the configured
   service address.
3. **Given** sample data mode is on, **When** example results include step
   statuses and scores, **Then** those values come already decided in the
   example data, the same way the real service supplies them.

### Edge Cases

- An address that matches no screen shows My calls.
- A call detail address shows the placeholder for whatever call id it
  names. Looking the call up, and saying "call not found", belongs to the
  call detail ticket.
- The service is unreachable or answers with an error: the shared access
  point reports the failure so the screen can show the shared error
  message, and the menu stays usable.
- No agent name is configured: the menu shows a neutral placeholder
  ("Agent") instead of an empty space.
- A step result arrives with a status outside the four known ones: it is
  shown as Under review and keeps its text label, rather than breaking the
  row.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The app MUST have exactly four screens: My calls, Call
  detail, Progress and Procedures. No other screens are added by this
  feature.
- **FR-002**: Every screen MUST appear inside one shared frame with a left
  menu listing My calls, Progress and Procedures.
- **FR-003**: The menu MUST mark the current screen. The call detail screen
  MUST mark My calls.
- **FR-004**: The menu MUST show the agent's name and role, taken from
  configuration. Signing in is out of scope.
- **FR-005**: An address that matches no screen MUST show My calls.
- **FR-006**: Call detail, Progress and Procedures MUST use the shared page
  header: a title, an optional one-line subtitle, and on Call detail a link
  back to My calls. My calls keeps its existing heading (FR-013).
- **FR-007**: A step result MUST be shown as a stone for one of four
  statuses (Completed, Missed, Wrong, Under review). Each status MUST
  differ by shape and MUST carry its status name as a text label. A
  procedure step that is not a call result MUST have its own stone.
- **FR-008**: A status legend MUST explain the four call statuses with the
  same stones and labels.
- **FR-009**: The score ring MUST display the score it is given. The screen
  MUST NOT decide whether a step was completed and MUST NOT calculate a
  score.
- **FR-010**: The app MUST provide a shared card, a shared empty message
  and a shared error message for every screen to use. The placeholder
  screens in this feature use the card and the empty message.
- **FR-011**: Screens MUST get their data through one shared access point
  that reads the service address from configuration.
- **FR-012**: One setting MUST switch the shared access point to example
  responses. Example responses MUST have the same shape as the real
  service's responses, including already-decided statuses and scores.
- **FR-013**: My calls MUST keep showing the existing calls list, unchanged.
  Call detail, Progress and Procedures MUST open with placeholder content.
- **FR-014**: Colors, type, spacing and card style MUST follow the project
  design file.
- **FR-015**: The whole application MUST still start for local work with
  the project's single start command.
- **FR-016**: Every new function MUST have an automated check that calls it
  and asserts its result or the failure it is specified to raise.
- **FR-017**: The rules for which screen an address opens, which menu item
  is marked, and how the agent is shown MUST be expressible and checkable
  without the screen-drawing layer.

### Key Entities

- **Screen**: One of the four places an agent can be. Has a title, an
  address, and the menu item it marks.
- **Menu item**: A label and the screen it opens. Exactly one is marked at
  a time.
- **Agent profile**: The name and role shown in the menu.
- **Step result**: A step name and one of four statuses, as decided by the
  service.
- **Call result**: A call's steps, the count completed, the total, and the
  score, as decided by the service.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An agent can reach any of the four screens from any other in
  at most two clicks.
- **SC-002**: In a check of every screen, 100% show the same frame, and
  the marked menu item matches the screen shown.
- **SC-003**: In a grayscale view, a reviewer identifies all four step
  statuses correctly from shape or label alone, with zero mistakes.
- **SC-004**: Switching between example data and the real service needs a
  change to one setting and no change to any screen.
- **SC-005**: A fresh copy of the project starts with one documented
  command and shows My calls within 10 minutes, not counting first-time
  downloads.
- **SC-006**: Every new function has an automated check, and breaking any
  of the navigation or display rules in FR-003, FR-005, FR-007 or FR-009
  fails at least one check.

## Assumptions

- The agent's name and role come from configuration until a later feature
  adds sign-in. Showing the real signed-in agent from the service is a
  separate use case and a separate specification.
- The calls list already built on this branch is reused as the content of
  My calls, unchanged. It keeps its own data loading and its own stones
  until its owner moves it onto the shared access point and shared pieces;
  changing how calls are listed or filtered is out of scope.
- Call detail, Progress and Procedures show placeholders. Their real
  content belongs to later tickets.
- Statuses and scores are always decided by the service. Example data
  stores them already decided; the screen never derives them.
- The design file is "Stepping Stones — UI Mockup", frames Home / Your
  calls and Foundations / Stone states.
- The earlier version of this ticket (merged as pull request #43) did not
  follow the project rules and is replaced by this feature.
- Screenshots beside the design frames are a pull request requirement, not
  something the app itself produces.
