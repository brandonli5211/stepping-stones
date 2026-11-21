# Feature Specification: Call detail page: transcript, score, flags

**Feature Branch**: `feat/35-call-detail-transcript`

**Created**: 2026-11-21

**Status**: Draft

**Input**: User description: "Ticket #35: the left and top part of the call detail screen, where an agent reads one call with every check marked on it: header, score panel, transcript with evidence and wrong labels, flags, and a way to select a step so its turns are highlighted. Figma frame 'Call review' (Transfer money, call a2f086d27b3a4f96). Data comes from the stored call detail; the page never analyzes anything."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read how one call went (Priority: P1)

An agent opens one of their calls from My calls. At the top they see which call it is (call type and reference), their score for the call, how many required steps they did right, how many points they lost and how many of the problems were critical, plus one sentence that sums up what happened.

**Why this priority**: This is the first thing an agent needs after a call: "how did I do, and what went wrong in one sentence". Without it the rest of the page has no context.

**Independent Test**: Open the stored Transfer money demo call (a2f086d27b3a4f96) and check the header and score panel against the Figma frame "Call review".

**Acceptance Scenarios**:

1. **Given** the Transfer money demo call is stored with 6 of 7 steps done right and 55 points lost, **When** the agent opens it, **Then** the page shows "Transfer money", the call reference, a score ring reading 45 of 100 in the "Focus here" band, "6 of 7 steps done right" and "1 critical, 55 points lost".
2. **Given** the stored call has a summary sentence, **When** the page opens, **Then** that sentence appears under the score.
3. **Given** the agent is on the call page, **When** they choose "Back to my calls", **Then** they return to My calls.
4. **Given** some of the call's points are still under review, **When** the page opens, **Then** the score is marked as provisional ("so far") and the points under review are shown.

---

### User Story 2 - See the transcript with every check marked on it (Priority: P1)

Below the header the agent reads the conversation turn by turn. Each turn shows who spoke, when, and what was said. Turns that prove a step was done are marked as evidence and say which step. Turns where something went wrong are marked as wrong and say what was wrong. A turn can carry both marks. Every other turn stays plain.

**Why this priority**: The transcript is how the agent understands *why* they got their score. It is the main teaching surface of the product.

**Independent Test**: Open the Transfer money demo call and compare each turn's speaker, time, text and labels with the Figma frame.

**Acceptance Scenarios**:

1. **Given** the demo call, **When** the transcript loads, **Then** the greeting turn at 0:02 is marked "Evidence for Greet and open".
2. **Given** the demo call, **When** the transcript loads, **Then** the 0:33 read-back turn is marked wrong with the label "Wrong: read back reversed. The caller asked checking → savings."
3. **Given** a turn that is wrong for one step and evidence for another (the 0:44 turn), **When** it is shown, **Then** it carries the wrong label and also says it is evidence for Offer further help.
4. **Given** a turn with no checks on it, **When** it is shown, **Then** it has no label and no highlight.
5. **Given** any marked turn, **When** it is shown, **Then** its meaning is conveyed by its text label and an icon, not by colour alone.

---

### User Story 3 - See what to fix first (Priority: P2)

Under the transcript the agent sees a Flags section: how many flags there are by severity, and one card per missed or wrong step with the step name, the points lost and one sentence on what went wrong.

**Why this priority**: Flags turn the marked transcript into a short to-do list, but the page is already useful without them.

**Independent Test**: Open the demo call and check that the Flags section shows "1 critical" and one card "Submit and confirm transfer, −55 points" with its message; open a call with no missed or wrong steps and check the clean state.

**Acceptance Scenarios**:

1. **Given** the demo call has one wrong critical step, **When** the page opens, **Then** Flags shows "1 critical" and one card for Submit and confirm transfer with −55 points and the stored message.
2. **Given** a call with no missed or wrong steps, **When** the page opens, **Then** Flags shows a clean state saying nothing needs fixing.

---

### User Story 4 - Jump to the turns behind a step (Priority: P2)

The agent can select a step, and the transcript scrolls to the turns marked for that step and highlights them. In this ticket a step is selected by choosing its flag card; the required-steps list from #36 will use the same selection.

**Why this priority**: It links "what went wrong" to "where it happened", and #36 depends on it, but the page works without it.

**Independent Test**: On the demo call, choose the Submit and confirm transfer flag and check that the transcript scrolls to the 0:33 and 0:44 turns and highlights them.

**Acceptance Scenarios**:

1. **Given** the demo call, **When** the agent chooses the Submit and confirm transfer flag, **Then** the transcript scrolls to the first turn marked for that step and every turn marked for it is highlighted.
2. **Given** a step is selected, **When** the agent selects a different step, **Then** only the new step's turns are highlighted.
3. **Given** a selected step has no marked turns, **When** it is selected, **Then** nothing scrolls and no turn is highlighted.

---

### Edge Cases

- The call does not exist: the page shows a not-found state with a way back to My calls.
- The call detail cannot be loaded (network or server error): the page shows an error state with a way to try again.
- While the call detail is loading, the page shows a loading state instead of empty panels.
- The call has no transcript: the transcript area shows "Transcript not available" and the rest of the page still shows.
- A very long transcript scrolls inside its panel without pushing or breaking the rest of the layout.
- A turn has no start time: the time is left out for that turn only.
- The call has no summary sentence: the summary line is left out.
- The call has no score yet (no step results): the score panel says the call has not been scored instead of showing 0.
- A turn carries several labels (evidence for several steps, or wrong and evidence): all labels are shown.
- A filler turn has a note attached (for example an "okay" cited as evidence): it is shown, because a marked turn is never hidden.
- Every turn of a call is filler: the transcript area shows "Transcript not available".

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The page MUST show the call it is for: a link back to My calls, the call type name as the title, and the call reference.
- **FR-002**: The page MUST show the stored score out of 100 in a ring placed in its band (On track 85 to 100, Getting there 60 to 84, Focus here under 60), the steps done right out of the total, the number of critical problems and the points lost.
- **FR-003**: When points are under review, the page MUST mark the score as provisional and show the points under review.
- **FR-004**: The page MUST show the stored summary sentence when there is one.
- **FR-005**: The page MUST show the transcript's turns in order, with the speaker (Agent or Customer), the time from the start of the call in minutes and seconds, and the text as stored.
- **FR-005a**: The page MUST hide filler turns (see Assumptions) unless a note is attached to them, and the turn count next to the heading ("9 turns, verbatim") MUST count only the turns shown.
- **FR-006**: The page MUST show each stored note on its turn: evidence notes as evidence labels, wrong notes as wrong labels, with all notes of a turn shown together.
- **FR-007**: Marked turns MUST be distinguishable without colour, through their label text and an icon for evidence and for wrong.
- **FR-008**: The page MUST show a Flags section with the number of flags per severity and one card per stored flag (step name, points lost, message), or a clean state when there are no flags.
- **FR-009**: The page MUST let the agent select a step by choosing its flag; selecting a step MUST scroll the transcript to that step's first marked turn and highlight all turns marked for it.
- **FR-010**: The step selection MUST be usable by other parts of the page (the #36 steps list) without changing this behaviour.
- **FR-011**: The page MUST show loading, error (with retry) and not-found states, and "Transcript not available" when the call has no turns.
- **FR-012**: The page MUST NOT decide whether a step was done, compute the score, or create labels or flags; it shows only what the stored call detail contains.
- **FR-013**: Every interactive element (back link, flag cards, retry) MUST be reachable and usable with the keyboard.

### Key Entities

- **Call detail**: one stored call as the agent sees it: header (reference, call type, summary), score (score, steps done right, steps total, points lost, critical count, points under review, provisional), transcript, flags.
- **Turn**: one thing said in the call: order, speaker, start time, text, and its notes.
- **Note**: a mark on a turn that ties it to a step: kind (evidence or wrong), the step, and the label text.
- **Flag**: one missed or wrong step to fix: step, status, severity, points lost, message.
- **Selected step**: the step whose turns are currently highlighted, or none.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For the Transfer money demo call, the page shows 9 turns, and each turn's speaker, time, text and labels match the Figma frame "Call review", including the 0:44 turn that is both wrong and evidence for Offer further help.
- **SC-002**: The score panel for the demo call shows exactly the stored values (score, 6 of 7, 1 critical, points lost), with no number worked out on the page.
- **SC-003**: Each of the five page states (loaded, loading, error, not found, no transcript) and the clean Flags state can be reached and is shown correctly.
- **SC-004**: With colour removed (greyscale), an agent can still tell evidence turns, wrong turns and plain turns apart on the demo call.
- **SC-005**: A transcript of 200 turns stays readable: the page layout does not break and the header and score panel stay in place.
- **SC-006**: Choosing a flag brings that step's first marked turn into view within one second on the demo call.

## Assumptions

- The stored call detail already contains the score, counts, notes and flags; this page only displays them (the call detail API from #34).
- "Back to my calls" goes to the existing My calls screen; any filters it had are not restored in this ticket.
- The required-steps list, the step detail panel, the coaching phrase, the Caller asked / Logged table, "I did do this" and "See procedure" are part of #36 and out of scope here.
- The signed-in agent is the fixed demo agent; there is no login.
- The stones and score ring follow the shared design language (#25); until it lands, the existing shell pieces are used.
- Filler turns are hidden to match the 9-turn Figma frame (clarified 2026-11-21). A filler turn is one whose whole text is only non-speech markers (such as "[noise]", "[laughter]" or "<unk>") and/or one short filler ("okay", "ok", "and", "um", "uh", "yeah", "mm hmm", "mhm"), with nothing else said. On the demo call this leaves exactly the 9 turns in the frame. "yes" is not filler, because the frame shows the caller's "yes" after the reversed read-back. This is a display rule; it never changes the score, notes or flags.
