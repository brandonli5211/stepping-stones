# Feature Specification: Evaluate Ordered Call Steps

**Feature Branch**: `feat/evaluator-use-case`

**Created**: 2026-11-20

**Status**: Draft

**Input**: User description: "Replace PRs #51 and #52 with one end-to-end evaluator use case that uses a procedure and call evidence to save trustworthy step results for issue #38."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Save a confident observed step (Priority: P1)

As a coach, I need a call's next required step to be marked complete only when the agent's spoken and logged actions satisfy the procedure, so the saved call detail accurately reflects demonstrated work.

**Why this priority**: Accurate completed steps are the foundation for every coaching score, call flag, and progress view.

**Independent Test**: Run analysis for one stored call where the caller provides several values in one turn; verify that each collection step may cite that turn, while a later confirmation is judged by deterministic comparisons.

**Acceptance Scenarios**:

1. **Given** a stored call whose next required step is supported by non-contradictory spoken and logged evidence, **When** that turn window is evaluated with confidence at or above the approved threshold, **Then** the step is saved as completed with evidence and evaluation advances to the next step.
2. **Given** a stored call whose next required step has a logged action that conflicts with the procedure or spoken evidence, **When** that turn window is evaluated, **Then** the step is not marked completed and is available for human review.

---

### User Story 2 - Preserve uncertain decisions for review (Priority: P1)

As a coach, I need uncertain or contradictory model decisions to remain under review rather than being converted into misses, so the system never presents uncertain coaching as a confirmed failure.

**Why this priority**: A false missed-step flag harms the agent and makes the detail and progress views unreliable.

**Independent Test**: Evaluate a call-ending turn with low confidence or contradictory evidence and verify that the current step remains under review, has no missed flag, and retains the review evidence.

**Acceptance Scenarios**:

1. **Given** a model decision below the confidence threshold, **When** the call has ended, **Then** the current step remains under review and is not saved as missed.
2. **Given** contradictory evidence for the current step, **When** the call has ended, **Then** the current step remains under review and is not saved as missed.

---

### User Story 3 - Finalize the rest of an ended call (Priority: P2)

As a coach, I need every remaining required step to have a final, explainable state when a call ends, so the score and flags do not silently omit unfinished work.

**Why this priority**: An ended call must not leave later procedure steps unresolved.

**Independent Test**: End a call after its current expected step and verify that every later unobserved required step is saved as missed, while a current uncertain step remains under review.

**Acceptance Scenarios**:

1. **Given** an ended call with one or more later required steps that have no supporting evidence, **When** evaluation finalizes the call, **Then** every such later step is marked missed and appears in the stored coaching results.
2. **Given** an ended call whose current step requires human review, **When** evaluation finalizes the call, **Then** that current step remains under review while the defined finalization policy is applied to later unobserved steps.

### Edge Cases

- A decision exactly at the confidence threshold is treated as confident.
- Repeating the same evaluation does not duplicate evidence, counters, flags, or state transitions.
- A missing call, procedure, usable transcript turn, or required logged-action evidence produces a clear failure without partially saving results.
- A model refusal or malformed decision result does not mark any step complete or missed.
- A call that has already finalized cannot reopen completed or missed steps without an explicit later review workflow.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST scan the transcript and procedure in order. A step starts at the current transcript cursor; a confident fact may advance that cursor, while an absent or uncertain fact advances only the procedure step. One transcript turn MAY support multiple collection facts.
- **FR-002**: The system MUST mark a step completed only when the decision is confident, non-contradictory, and supported by the required evidence.
- **FR-003**: The system MUST store evidence sufficient for the existing call-detail experience to show why a step was completed, under review, missed, or wrong.
- **FR-004**: The system MUST preserve low-confidence, contradictory, refused, or malformed decisions as under review; it MUST NOT simultaneously mark them missed or prevent evaluation of later required steps.
- **FR-005**: When a call ends, the system MUST finalize every remaining required step according to a documented policy, without leaving later steps unresolved.
- **FR-006**: The system MUST update stored call and step summaries so existing call-list, call-detail, and progress views remain internally consistent.
- **FR-007**: The system MUST expose a command-level input boundary and output boundary for selecting calls to analyze, and present a clear command result while leaving the existing UI to read saved results.
- **FR-008**: The system MUST make all evaluator state changes atomically; an invalid input or external-decision failure MUST leave stored coaching results unchanged.
- **FR-009**: The system MUST expose the confidence threshold as a named business rule and test behavior below, at, and above it.
- **FR-010**: The system MUST use the configured OpenAI Decisions model only to extract cited facts: simple-step evidence, where a caller value was supplied, and where an agent read-back occurred. Python MUST compare those facts with recorded actions and apply all step-status, score, severity, and flag judgments.
- **FR-011**: The system MUST reject model evidence whose quote is not found word-for-word in the cited stored turn, and preserve that step for human review.
- **FR-012**: The system MUST record the model and prompt version that produced a saved evaluation result.

### Key Entities *(include if feature involves data)*

- **Evaluation request**: One stored call, its current procedure position, transcript cursor, speaker-labelled turns, relevant recorded actions, and whether the call has ended.
- **Step decision**: The Decisions model's typed, cited fact observation. It does not contain a completed/wrong/missed judgment.
- **Step evaluation result**: The saved state transition, review requirement, evidence, and next procedure position returned to the caller.
- **Call evaluation state**: The durable state needed to identify and finalize the next required step across multiple turn evaluations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of evaluated calls that end have a stored state for every required step.
- **SC-002**: 100% of low-confidence or contradictory decisions remain reviewable and produce no missed-step flag.
- **SC-003**: Re-evaluating the same request leaves the persisted result unchanged in 100% of automated idempotency checks.
- **SC-004**: Existing call-list, call-detail, and progress responses report matching counts and statuses for every automated evaluator fixture.

## Assumptions

- The configured OpenAI Decisions model remains the feature's model provider; model calls happen during the analysis command, not while someone opens a page.
- The existing stored procedure rules remain the source of required steps and logged-action requirements.
- A completed step must satisfy any procedure requirement that applies to an agent's logged action as well as spoken evidence.
- The existing call-detail and progress contracts are preserved; this feature enriches their stored inputs rather than changing their user-facing meaning.
- Human review resolution is outside this feature; it consumes the under-review state created here.
