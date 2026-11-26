# Feature Specification: Stone loading path

**Feature Branch**: `feat/stone-loader`

**Created**: 2026-11-22

**Status**: Implemented

**Input**: User description: "While a screen is loading, show the stepping-stone path from the mock: pale stones, one brand-coloured stone with a ripple, and the words Finding your footing. Use the stones the app already draws. Do not restyle the scored screens and do not call the model."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See the path while a screen loads (Priority: P1)

An agent opening a call, their progress, or the procedures sees a short path of stones and the words "Finding your footing…" until the stored screen is ready. The stone in the middle is the brand colour and has a ripple. The other stones are pale.

**Why this priority**: The wait is the moment the product should feel like itself. A plain sentence does not.

**Independent Test**: Open a call while it is still loading. The path and the words are on screen, and the screen's own loading sentence is still available to assistive technology.

**Acceptance Scenarios**:

1. **Given** a call, progress, or procedures screen is loading, **When** the agent is looking at it, **Then** they see five stones in a path, the middle one marked as the active stone, and the words "Finding your footing…".
2. **Given** the screen has its own loading sentence, **When** the path is shown, **Then** that sentence remains available to assistive technology.
3. **Given** the agent prefers reduced motion, **When** the path is shown, **Then** the active stone does not ripple.

### Edge Cases

- The path is only for loading. An error or an empty screen keeps its current message.
- My calls still uses the older page. This feature does not redraw that page.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A loading call, progress, or procedures screen MUST show a path of five stones and the words "Finding your footing…".
- **FR-002**: The middle stone MUST be visibly the active one. The other four MUST be pale.
- **FR-003**: The screen's existing loading sentence MUST remain available to assistive technology.
- **FR-004**: The ripple MUST stop when the agent prefers reduced motion.
- **FR-005**: The path MUST NOT score a call, choose a step, or request a model.

### Key Entities

- **Loading path**: five stones, one active, plus the footing words and the screen's own loading sentence.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On each of the three screens, a loading state shows the footing words and exactly one active stone.
- **SC-002**: The call screen's existing loading sentence is still present for assistive technology.
- **SC-003**: No request is added. The path replaces the loading sentence's appearance only.

## Assumptions

- The scored screens already use the shared stone. This feature does not replace those stones.
- The Figma file's full frame-by-frame refresh is out of scope. The path is the element being added.
