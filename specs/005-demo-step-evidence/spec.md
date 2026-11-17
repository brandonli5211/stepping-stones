# Feature Specification: Demo Step Evidence

**Feature Branch**: `feat/33-load-demo-48`

**Created**: 2026-11-16

**Status**: Draft

**Input**: User description: "Feature 005. Demo evidence for a wrong step. Issue #33 milestone 1 says the Transfer money demo call a2f086d27b3a4f96 must be written out in full on the call detail screen: step 5 (submit_and_confirm_transfer) marked Wrong with the quote at 0:33, the flag, and the 'caller asked vs logged' table. Today the status (wrong), severity (critical, which is the flag), points lost and the comparison table are already stored after load_calls --demo-results and apply-demo-results; only call_steps.evidence_turn_idx and call_steps.evidence_quote are never written. Add hand-labelled evidence for a demo step: the demo results data names the call, the step, the turn index, and the quote; applying demo results stores evidence_turn_idx and evidence_quote on that step. For a2f086d27b3a4f96 that is turn 9 (starts at 33.53 s, so 0:33), agent, quote 'okay and that was from your savings to your checking account' (the whole turn). The quote must appear word for word in the named turn of that call (judging rule unverifiable_means_review); a missing turn, a quote that is not in the turn, or evidence for a step that is not missed or wrong is a problem that saves nothing (all-or-nothing, like the existing ApplyDemoResults). Calls without evidence keep null evidence. Fill only what is missing: no new columns, no migration, no flag column, no change to scores, statuses, severity, comparison, GET /calls or POST /calls/{id}. One primary use case: extend ApplyDemoResults."

**Primary use case**: ApplyDemoResults, extended (feature 002). This feature adds no new use case.

## Context: what is already stored

After the demo calls are loaded with demo results and `sample/demo_48/results.csv` is applied, the Transfer money call `a2f086d27b3a4f96` already has everything issue #33 asks for on its step 5, "Submit and confirm transfer", except the evidence:

| Issue #33 asks for | Stored today |
|---|---|
| Step 5 marked Wrong | yes: status wrong, 55 points lost, call score 45 |
| The flag | yes: severity "critical" on the wrong step (decided with the product owner; no separate flag field) |
| "Caller asked vs logged" table | yes: amount 114 / 114 match; source checking / savings no match; destination savings / checking no match |
| Transcript | yes: 16 turns |
| The quote at 0:33 and the turn it comes from | **no: never written** |

This feature fills only that last row.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The wrong step points at the moment it went wrong (Priority: P1)

A demo presenter hand-labels which turn of a demo call shows a step going wrong, and the exact words. They add this to the curated results file next to that call's missed and wrong steps, then apply the file as before. Afterwards the call detail screen can show the step as Wrong together with the quote and jump to that turn in the transcript (0:33 for the Transfer money call).

**Why this priority**: This is the one part of issue #33 milestone 1 still missing. Without it, the Wrong step on the call detail screen has no evidence to show.

**Independent Test**: Load demo_48 with demo results and apply `results.csv`. Then read step `submit_and_confirm_transfer` of call `a2f086d27b3a4f96`. Its evidence is turn 9 with the quote "okay and that was from your savings to your checking account". Its status, severity, points lost, score and comparison table are the same as before this feature.

**Acceptance Scenarios**:

1. **Given** the 48 demo calls are loaded and row `HVB-DEMO-06` names the evidence for `submit_and_confirm_transfer` as turn 9 with quote "okay and that was from your savings to your checking account", **When** the file is applied, **Then** that step stores evidence turn 9 and that quote, and the run reports 48 calls updated.
2. **Given** the same apply, **When** the stored results are compared with a run before this feature, **Then** every call's score, points lost, step counts and start time, every step's status, severity, points lost, note and comparison table, and the weekly figures (this week 53 of 59, 90%; weekly 64, 70, 68, 75, 80, 79, 86, 90) are unchanged.
3. **Given** a row with no evidence, **When** the file is applied, **Then** every step of that call has no evidence.
4. **Given** a results file written before this feature, with no evidence columns at all, **When** it is applied, **Then** it is accepted and behaves exactly as it did before, and no step has evidence.

---

### User Story 2 - Evidence that cannot be verified changes nothing (Priority: P2)

The presenter types the turn number and quote by hand and can get them wrong. If the evidence does not match the stored transcript, the run fails, reports every problem with the row's demo ID, and saves nothing, the same as any other bad row.

**Why this priority**: The shared judging rule (`unverifiable_means_review`) says every quote must appear word for word in the turn it names. A demo that shows a quote the agent never said would undermine the product's main promise.

**Independent Test**: Apply a file in which the quote for `a2f086d27b3a4f96` is changed by one word. The run fails, names `HVB-DEMO-06`, and no call changes, including the valid rows.

**Acceptance Scenarios**:

1. **Given** evidence naming a turn number the call does not have, **When** the file is applied, **Then** the run fails, reports the row's demo ID and the turn number, and saves nothing.
2. **Given** evidence whose quote does not appear word for word in the named turn's text, **When** the file is applied, **Then** the run fails, reports the row's demo ID and the turn number, and saves nothing.
3. **Given** evidence for a step that the same row does not list as missed or wrong, **When** the file is applied, **Then** the run fails, reports the row's demo ID and the step key, and saves nothing.
4. **Given** a row that fills in some evidence values but not all three (step, turn, quote), **When** the file is applied, **Then** the run fails, reports the row's demo ID, and saves nothing.
5. **Given** a turn value that is not a whole number of 1 or more, **When** the file is applied, **Then** the run fails, reports the row's demo ID and the value, and saves nothing.
6. **Given** a file with evidence problems and other bad rows, **When** the file is applied, **Then** all the problems are reported together.

---

### Edge Cases

- **Word for word**: the quote must be an exact, case-sensitive substring of the turn's stored text after trimming spaces at both ends of the quote. Matching does not ignore punctuation, case, or spacing inside the quote. The whole turn is a valid quote.
- **Which text**: the turn's stored text, meaning the human transcript or, when that is empty, the speech-recognition transcript. The loader already stores turns this way.
- **Speaker**: not checked. The step being judged decides who the right speaker is, and the presenter chooses the turn. Turn 9 of `a2f086d27b3a4f96` is an agent turn.
- **One evidence per row**: a row can carry evidence for at most one of its steps. That covers every case in issue #33.
- **Re-applying**: applying the same file twice gives the same result. Applying a file without evidence for a call clears any earlier evidence on that call's steps, the same way a changed status clears the old note.
- **Time on screen**: the 0:33 shown on screen comes from the stored turn's start time (33.53 s). The results file does not store the time.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The results file MAY carry three more columns, `evidence_step`, `evidence_turn` and `evidence_quote`. A file without them MUST be read exactly as before (feature 002, FR-001).
- **FR-002**: On a row, the three evidence values MUST be either all empty (no evidence) or all filled in. Anything else makes the row bad.
- **FR-003**: `evidence_turn` MUST be a whole number of 1 or more, and it MUST be the turn number of a stored turn of that row's call. Otherwise the row is bad.
- **FR-004**: `evidence_step` MUST be one of the steps the same row lists as missed or wrong. Otherwise the row is bad.
- **FR-005**: `evidence_quote`, trimmed, MUST be non-empty and appear word for word (exact, case-sensitive substring) in the named turn's stored text. Otherwise the row is bad.
- **FR-006**: Evidence problems MUST be reported and handled like the existing problems: every problem is listed with the row's demo ID, and if any row is bad, nothing is saved (feature 002, FR-008).
- **FR-007**: When the file is valid, the named step MUST store the evidence turn number and the trimmed quote. Every other step of every applied call MUST store no evidence.
- **FR-008**: This feature MUST NOT change any call's score, points lost, step counts, status or start time. It MUST NOT change any step's status, severity, points lost, points under review, note, sub-checks or comparison table. It MUST NOT change the GET /calls or POST /calls/{id} responses.
- **FR-009**: No new database column, table or migration. The existing step evidence fields hold the values.
- **FR-010**: `sample/demo_48/results.csv` MUST give row `HVB-DEMO-06` the evidence `submit_and_confirm_transfer`, turn `9`, quote "okay and that was from your savings to your checking account". Every other row MUST have no evidence.
- **FR-011**: The evidence checks (FR-002 to FR-005) MUST be computable and testable without a database or web server.

### Key Entities

- **Results row** (extended): the existing curated outcome, plus optional evidence made of a step key, a turn number and a quote.
- **Turn**: one stored turn of a call. It holds a turn number (from 1), a speaker, a start time and its text.
- **Step result** (extended use): the existing step result's evidence turn number and evidence quote are now filled in for hand-labelled evidence.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After load and apply, step "Submit and confirm transfer" of call `a2f086d27b3a4f96` has evidence turn 9 (start 0:33) and the quote "okay and that was from your savings to your checking account".
- **SC-002**: All 48 rows still apply in one run with no problems reported. Score, status and severity values for all 48 calls and their 281 steps match the run before this feature.
- **SC-003**: A file in which the quote is changed by one word, or the turn number is changed to one the call does not have, leaves 100% of calls unchanged and names the row.
- **SC-004**: Every evidence check (FR-002 to FR-005) has an automated case that runs with no database, in `test_bad_file_saves_nothing`. *(Narrowed on 2026-11-19: the checks are tested through the use case, not one by one.)*
- **SC-005**: Exactly one call step in the demo data has evidence after apply.

## Assumptions

- "The flag" in issue #33 is the Wrong status with critical severity that is already stored. The product owner confirmed this on 2026-11-16. No flag field is added.
- The quote is the whole of turn 9, as chosen by the product owner.
- The demo calls are loaded first, with turns, as in feature 002. Apply reads the stored turns. It does not read transcript files.
- The call detail screen and its API (#34, #35) are out of scope. This feature only makes the data available.
- The loader (`load_calls`, `call_parse`) is not changed.
