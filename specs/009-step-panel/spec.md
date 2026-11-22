# Feature Specification: Call detail step panel and coaching

**Feature Branch**: `feat/36-call-detail-steps`

**Created**: 2026-11-21

**Status**: Draft

**Input**: User description: "Issue #36. On the call page, show the required steps and the selected step: its description, points, evidence quote, coaching line, and, for Transfer money, the caller-asked versus logged table. The stored call already carries this. The page does not decide the score. One use case: keep ViewCallDetail and present the selected step."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See which steps were required (Priority: P1)

An agent looking at one call sees every required step in order, with its result and the points lost. The first step that was missed or done wrong is selected when the page opens. Choosing another step selects that one instead. The same selection highlights that step's turns in the transcript.

**Why this priority**: Without the list, the agent cannot walk the checklist the score came from.

**Independent Test**: Open the stored Transfer money call. The list shows seven steps. "Submit and confirm transfer" is selected, and its transcript turns are highlighted.

**Acceptance Scenarios**:

1. **Given** a stored call with steps, **When** the agent opens it, **Then** the steps appear in stored order with a result word and the points lost.
2. **Given** the call has a missed or wrong step, **When** the page opens, **Then** the first such step is selected.
3. **Given** every step is completed, **When** the page opens, **Then** the first step is selected and its panel shows no points lost.
4. **Given** a step is selected, **When** the agent chooses another step from the list or from a flag, **Then** that step becomes the selected one and the transcript highlights its turns.

---

### User Story 2 - Read the coaching for the selected step (Priority: P1)

The selected step shows what it asked for, how many points it was worth, what was lost, any sub-checks, the quote that proves it and when that quote was said, and the coaching sentence when the server stored one. A completed step shows its quote and does not show a coaching sentence or a deduction.

**Why this priority**: This is the sentence the agent can use on the next call.

**Independent Test**: With "Submit and confirm transfer" selected, the panel shows the quote at 0:33 and the stored coaching sentence. With "Greet and open" selected, the panel shows that step's quote and no coaching sentence.

**Acceptance Scenarios**:

1. **Given** the wrong Transfer money step is selected, **When** the panel is shown, **Then** it includes the evidence quote, the time 0:33, both failed sub-checks, and the stored coaching sentence.
2. **Given** a completed step is selected, **When** the panel is shown, **Then** it shows that step's evidence and no coaching sentence and no points lost.
3. **Given** a step has no evidence quote, **When** it is selected, **Then** the panel says the quote is not stored, and still shows the step's result.

---

### User Story 3 - See what the caller asked against what was logged (Priority: P2)

When the selected step was missed or wrong on a Transfer money call, the panel includes the stored field table: what the caller asked, what the agent logged, and the stored result for each field. Other call types show no table.

**Why this priority**: The transfer story is the swapped accounts. The table is how that swap is shown. The page is still useful as a checklist without it.

**Independent Test**: On the Transfer money call, select the wrong step and read From and To as reversed. Select a completed step and the table is not shown.

**Acceptance Scenarios**:

1. **Given** the wrong Transfer money step is selected, **When** the panel is shown, **Then** Amount is a match and From and To are reversed, using the stored values.
2. **Given** a completed step on that same call is selected, **When** the panel is shown, **Then** the field table is not shown.
3. **Given** a call whose type has no field table, **When** any step is selected, **Then** no field table is shown.

---

### Edge Cases

- A call with no steps shows the transcript and flags and an empty step list, and nothing is selected.
- A step result the page does not recognise is left off the list. The page does not invent a result.
- "I did do this" is not offered. That action is a later feature.
- "See procedure" opens the checklist for this call's type.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The call page MUST list every recognised required step in stored order, with its stored result and points lost.
- **FR-002**: The page MUST select the first missed or wrong step when the call opens, or the first step when none failed.
- **FR-003**: Choosing a step in the list or a flag MUST select that step and highlight its transcript turns.
- **FR-004**: The selected step MUST show its stored description, points, evidence quote and time, sub-checks, and coaching sentence when one is stored.
- **FR-005**: A completed step MUST NOT show a deduction or a coaching sentence.
- **FR-006**: A missed or wrong step on a Transfer money call MUST show the stored caller-asked versus logged table. The page MUST NOT compare the values itself.
- **FR-007**: The page MUST link to the procedure for the call's type.
- **FR-008**: The page MUST NOT compute a score, a step result, or a field result.

### Key Entities

- **Required step**: key, name, order, result, points, points lost, description, sub-checks, evidence quote and time, coaching sentence.
- **Field row**: label, caller asked, logged, stored result. Present only for Transfer money.
- **Selected step**: the step key the agent is looking at. It is page state, shared with the transcript highlight.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On the stored Transfer money call, an agent can see seven steps and land on the wrong confirmation step without an extra click.
- **SC-002**: That step's panel shows the 0:33 quote and the stored coaching sentence.
- **SC-003**: From and To on that step read as reversed, and Amount reads as a match, matching the stored table.
- **SC-004**: Choosing "Greet and open" shows that step's quote and no coaching sentence.

## Assumptions

- `GET /calls/{id}` already returns `steps` and `type_details`. This feature does not change the API.
- The call page from the transcript work already loads the call and highlights turns for a selected step.
- The procedure page already opens the checklist named by `?task=`.
