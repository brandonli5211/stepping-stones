# Feature Specification: Design Language (stones and score ring)

**Feature Branch**: `feat/25-design-language`

**Created**: 2026-11-18

**Status**: Draft

**Input**: User description: "Ticket #25 Feat: Design language. Reusable visual pieces for every page: the stone step components in their five states (completed, missed, wrong, under review, procedure step) and a score ring with its three bands (On track 85 to 100, Getting there 60 to 84, Focus here under 60). Done when the five stones are distinct without relying on colour, and the ring puts the edge scores 59, 60, 84 and 85 in the right bands. Visual reference: the Figma 'Stepping Stones — UI Mockup' (Foundations / Stone states, the Stone component, the palette, and the score bands on the Home 'Your week' and call review screens)."

## Clarifications

### Session 2026-11-18

- Q: The Figma draws the procedure step as a solid stone in the brand colour,
  the same solid shape as completed. How do they differ without colour? → A:
  The **completed** stone gets a small check mark; the procedure step stays a
  plain solid stone in the brand colour, as in Figma.
  - Nuance: this is a deliberate change from the Figma, where completed is a
    plain solid stone. The ticket's "done when" (five stones distinct without
    colour) wins over the mockup. The pull request must say so, with a
    screenshot next to the Figma frame, so the designer can update the Stone
    component or object.
  - Nuance: with the check, every call result now carries a mark (✓, crack,
    X, dashes), and only the procedure step, which is not a result, is plain.
    That makes "plain stone = a step as written, not a result" a rule of its
    own.
  - Nuance: completed is the most common stone, so the check must stay quiet
    (thin, in the stone's own colour family) and must still be visible on the
    smallest stones.
- Q: Principle I says the backend owns the judgment and the frontend must not
  compute the score. Where are the score bands decided? → A: In the frontend,
  as a display rule applied to the score the backend sends.
  - Nuance: the frontend never calculates, adjusts or rounds the score; it
    only names the range the given number falls in, the same way it picks a
    colour for a status. That is why it does not break Principle I, which
    forbids deciding whether a step was completed or computing the score.
  - Nuance: the band edges (85 and 60) are a product rule, so they live in one
    place with their own tests, not inside any component, so no page can
    draw its own bands.
  - Nuance: if the team later decides the band is coaching judgment (for
    example, edges that differ by call type or by agent), the API should send
    the band and the frontend should show what it is given. That would be a
    separate ticket touching #30 and #34.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read a step's result from its stone, without colour (Priority: P1)

An agent looks at a row of stones (on a call row, the call's path of required
steps, a habit row or a procedure) and can tell for each stone what happened to
that step: completed, missed, wrong, under review, or a procedure step that is
not a result at all. The stone's shape says it, so an agent with colour
blindness, a greyscale screen or a printout reads the same thing.

**Why this priority**: Stones are the core visual of the product. Every
screen (My calls, call detail, Progress, Procedures) draws them, so if their
meaning is unclear, every screen is unclear.

**Independent Test**: Draw one stone of each of the five states side by side,
remove all colour (greyscale), and check that each state can still be told
apart and that each stone announces its state as text to a screen reader.

**Acceptance Scenarios**:

1. **Given** the five states drawn side by side, **When** they are viewed in
   greyscale, **Then** no two states look the same: completed is a solid
   stone with a check mark, missed is a cracked stone, wrong is a stone with
   an X mark, under review is a dashed outline, and the procedure step is a
   plain solid stone.
2. **Given** any stone, **When** a screen reader reaches it, **Then** it reads
   the state name ("Completed", "Missed", "Wrong", "Under review", "Procedure
   step"), plus the step name when one is given.
3. **Given** a status the stone does not know, **When** it is drawn, **Then**
   it shows as "Under review" rather than breaking or looking completed.
4. **Given** a row of several stones in the same state, **When** it is drawn,
   **Then** the stones vary slightly in pebble shape (four variants, as in
   Figma) so the row looks natural, while the state stays recognisable.

---

### User Story 2 - See which band a score is in (Priority: P1)

An agent sees a score ring (on the call review header, the weekly overview or
the recent-calls list) and, next to the number, the band it falls in: "On
track" (85 to 100), "Getting there" (60 to 84) or "Focus here" (under 60),
each with its own coloured dot. A legend explains the three bands.

**Why this priority**: The band turns a number into a message the agent can
act on, and the ticket's "done when" depends on scores at the edges landing in
the right band.

**Independent Test**: Show the ring for the scores 59, 60, 84 and 85 and check
the bands: Focus here, Getting there, Getting there, On track.

**Acceptance Scenarios**:

1. **Given** a score of 85 or 100, **When** the ring is shown, **Then** it
   says "On track".
2. **Given** a score of 60 or 84, **When** the ring is shown, **Then** it says
   "Getting there".
3. **Given** a score of 59, 45 or 0, **When** the ring is shown, **Then** it
   says "Focus here".
4. **Given** no score yet (a call still being reviewed), **When** the ring is
   shown, **Then** it shows "–" and no band.
5. **Given** the band legend, **When** it is shown, **Then** it reads "On
   track 85 to 100 · Getting there 60 to 84 · Focus here under 60", each with
   its dot.
6. **Given** any ring, **When** a screen reader reaches it, **Then** it reads
   the score and the band (for example "Score 45 of 100, Focus here").

---

### User Story 3 - One look everywhere (Priority: P2)

A developer building any page (#30, #35, #36, #37, #32) uses the same stone,
stone legend, score ring and band legend, in the product palette, instead of
drawing their own.

**Why this priority**: It keeps every page consistent with the Figma
foundations, but the pages themselves belong to other tickets.

**Independent Test**: Check that the stone legend lists the call statuses with
their names, and that the pieces use only the palette colours.

**Acceptance Scenarios**:

1. **Given** the stone legend, **When** it is shown on a call screen, **Then**
   it lists Completed, Missed, Wrong and Under review with their stones and
   names (the procedure step is not a call result, so it is left out).
2. **Given** any of the pieces, **When** it is drawn, **Then** it uses only the
   palette: Mint Cream #F7FFF6, Cerulean #3C7A89, #272727, #0CCE6B, #E65F5C and
   Bright Amber #F1C40F.

---

### Edge Cases

- A score below 0 or above 100 (bad data): the ring is clamped to 0 or 100 for
  drawing and banded as Focus here or On track.
- A score with a fraction (for example 84.5): banded by its value, so 84.5 is
  Getting there and 85 is On track; the number is shown as given.
- A missing score: "–", an empty ring, no band.
- An unknown stone status: drawn as Under review (User Story 1, scenario 3).
- Very small stones (for example 12 px in a dense row): the crack, X mark and
  dashed outline must still be visible.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: There MUST be one reusable stone that draws five states:
  completed, missed, wrong, under review and procedure step.
- **FR-002**: Each state MUST differ from every other state by shape or mark,
  not by colour alone: completed solid with a check mark, missed cracked,
  wrong with an X mark, under review a dashed outline, and the procedure step
  a plain solid stone in the brand colour. The check on completed is a
  deliberate change from the Figma (see Clarifications), and the marks MUST
  stay visible on the smallest stones.
- **FR-003**: Every stone MUST expose its state name as text to assistive
  technology, and MAY show the name visibly next to it.
- **FR-004**: An unknown state MUST be drawn as Under review.
- **FR-005**: The stone MUST come in four slightly different pebble shapes, as
  in the Figma Stone component, chosen so the same stone in the same place
  always looks the same (not random on every redraw).
- **FR-006**: There MUST be a stone legend listing the four call statuses
  (Completed, Missed, Wrong, Under review).
- **FR-007**: There MUST be one rule that maps a score to its band: 85 and
  above On track, 60 to under 85 Getting there, under 60 Focus here, and no
  band when there is no score. This is a display rule applied in the frontend
  to the score the backend sends; it lives in one place with its own tests,
  and no component draws bands of its own (see Clarifications for why this
  respects Principle I).
- **FR-008**: The score ring MUST show the score out of 100, its band label
  and the band's coloured dot (On track green, Getting there amber, Focus here
  red), and MUST read both score and band to assistive technology.
- **FR-009**: There MUST be a band legend: "On track 85 to 100 · Getting there
  60 to 84 · Focus here under 60", each with its dot.
- **FR-010**: The ring MUST NOT change the score it is given; it only draws it
  and names its band.
- **FR-011**: The pieces MUST use the palette above and nothing else for
  colour.
- **FR-012**: Each new function MUST have a unit test, including the edge
  scores 59, 60, 84 and 85 and one test per stone state showing its distinct
  shape or mark.

### Key Entities

- **Stone state**: one of completed, missed, wrong, under review, procedure
  step; has a display name and a distinct shape or mark.
- **Score band**: one of On track, Getting there, Focus here; has a range, a
  label and a colour.
- **Score**: a whole number from 0 to 100 given by the backend, or none yet.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a greyscale view of the five stones, all five can be told
  apart (5 of 5 distinct), by a reviewer comparing them with the Figma
  foundations frame.
- **SC-002**: The scores 59, 60, 84 and 85 land in Focus here, Getting there,
  Getting there and On track (4 of 4).
- **SC-003**: 100% of stones and rings announce their meaning as text (state
  name; score and band) to a screen reader.
- **SC-004**: The pieces match the Figma foundations (shapes, palette, band
  colours), checked by a screenshot next to the Figma frame in the pull
  request; the one intended difference, the check on completed, is named in
  the pull request.
- **SC-005**: Any page can show a stone, the stone legend, a ring and the band
  legend by reusing these pieces, with no page-specific copy of them.

## Assumptions

- Built on the TypeScript app shell from PR #48 (ticket #31), which already
  has a Stone with the five states, a stone legend and a score ring with no
  band. This feature extends those pieces rather than replacing them.
- The Wrong state means evidence was found but the step was done incorrectly
  (as in #34's call detail API); its look (a red stone with an X mark) comes
  from the Figma Stone component.
- The procedure step is never shown in the same row as call results (it is
  used only on the Procedures page), but it must still be distinct on its own.
- Scores come from the backend as whole numbers from 0 to 100, or none
  (the call detail API from #34); the frontend never calculates a score.
- Out of scope: the pages that use the pieces (#30, #35, #36, #37, #32), the
  typography and spacing scale, dark mode, and animation.
