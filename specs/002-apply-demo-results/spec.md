# Feature Specification: Apply Demo Results

**Feature Branch**: `feat/33-load-demo-48`

**Created**: 2026-11-11

**Status**: Draft

**Input**: User description: "Feature A — ApplyDemoResults (issue #33). A demo presenter applies sample/demo_48/results.csv to the already-loaded demo_48 calls. Each row sets that call's start time from date+time in America/Toronto and sets every rubric step to missed, wrong, or completed from missed_steps and wrong_steps. Score, points lost, severity and step counts are recomputed from the rubric; severity bands come from the existing schema3 procedure rules — no second band table. An unknown step key or a missing call fails the whole run and saves nothing. calls_sample_56 is untouched. Exactly one use case: ApplyDemoResults. Replaces the rejected apply_results.py script."

**Primary use case**: ApplyDemoResults (one use case for this feature; listing calls with a demo clock is a separate, later feature, ListCalls).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Apply a curated results file to the demo calls (Priority: P1)

A demo presenter has loaded the 48 demo calls. Each call has a curated outcome in `results.csv`: when it happened (local Toronto date and time) and which rubric steps the agent missed or got wrong. The presenter runs one command with that file. Afterwards every listed call has the curated start time, every rubric step has the curated outcome (missed, wrong, or completed if not listed), and the call's score, points lost, per-step severity, and step counts agree with the rubric.

**Why this priority**: The 8-week coaching demo depends on believable, hand-picked results. Without them, the demo calls carry the rough seed results and their original dates, so the weekly figures say nothing.

**Independent Test**: Load demo_48 with demo results, apply `results.csv`, then read call `a2f086d27b3a4f96` back. It is scored 45, its "Submit and confirm transfer" step is wrong with 55 points lost, and its other steps are completed.

**Acceptance Scenarios**:

1. **Given** the 48 demo calls are loaded, **When** the presenter applies `sample/demo_48/results.csv`, **Then** the run reports 48 calls updated and saves them.
2. **Given** row `HVB-DEMO-06` (call `a2f086d27b3a4f96`, transfer_money, 2026-10-07 16:48, wrong: `submit_and_confirm_transfer`), **When** the file is applied, **Then** that call starts at 2026-10-07 16:48 Toronto time (20:48 UTC), the step is wrong and loses its full 55 points with severity "critical", every other step is completed with 0 points lost and severity "none", and the call's score is 45 with 55 points lost, 7 steps total, 6 completed, 0 missed, 1 wrong, 0 under review.
3. **Given** a row with both cells empty, **When** the file is applied, **Then** every step of that call is completed and the call scores 100.
4. **Given** a row listing two missed steps worth 5 points each, **When** the file is applied, **Then** each of those steps is missed with 5 points lost and severity "slip", and the score is 90.

---

### User Story 2 - A bad results file changes nothing (Priority: P2)

The presenter edits `results.csv` by hand and might mistype a step key or a call ID. When anything in the file does not match the loaded data, the run stops, tells the presenter every problem it found (the row's demo ID and what is wrong), and leaves every call exactly as it was.

**Why this priority**: A partial apply would leave the demo data half curated and the weekly numbers wrong in ways that are hard to see. All or nothing keeps the data trustworthy.

**Independent Test**: Apply a file in which one row names a step key that is not one of the call's stored steps. The run fails, reports that row, and no call changes, including the valid rows.

**Acceptance Scenarios**:

1. **Given** a row whose missed or wrong cell names a step key that is not one of the call's stored steps, **When** the file is applied, **Then** the run fails, reports the row's demo ID and the unknown key, and saves no change to any call.
2. **Given** a row whose call ID has no loaded call, **When** the file is applied, **Then** the run fails, reports the row's demo ID as "call not loaded", and saves no change to any call.
3. **Given** a row that lists the same step key in both its missed and its wrong cell, **When** the file is applied, **Then** the run fails, reports the row's demo ID and the conflicting key, and saves no change to any call.
4. **Given** a row whose `call_type` differs from the loaded call's type, **When** the file is applied, **Then** the run fails, reports the row's demo ID with the expected and found types, and saves no change to any call.
5. **Given** a row whose call is loaded but has no stored rubric steps (it was loaded without demo results), **When** the file is applied, **Then** the run fails, reports the row's demo ID with "call has no rubric steps", and saves no change to any call.
6. **Given** two rows naming the same call, **When** the file is applied, **Then** the run fails, reports the second row's demo ID as listing that call more than once, and saves no change to any call.
7. **Given** a row whose date or time cannot be read (for example `2026-13-01` or `25:00`), **When** the file is applied, **Then** the run fails, reports the row's demo ID with the bad value, and saves no change to any call.
8. **Given** a file with several bad rows, **When** the file is applied, **Then** all of the problems are reported together, not just the first.

---

### Edge Cases

- **Step listed as both missed and wrong**: the row is bad. The run reports it and saves nothing. No current row does this.
- **Spaces around keys and empty items**: `"a; b;"` is read as `{a, b}`.
- **Unlisted steps**: they become completed, including steps the seed had marked "under review". After an apply, no step of an updated call is under review.
- **Explanatory note on a step**: the note is kept only when the step's status is unchanged. Otherwise it is cleared, because it described the old outcome.
- **Daylight-saving dates**: the local date and time is converted with Toronto's offset for that date. All current rows are in Eastern Daylight Time, which is UTC−4.
- **Call with no stored steps**: the row is bad. Such a call was loaded without demo results, and scoring it would give a meaningless 100 out of zero steps.
- **The same call on two rows**: every row after the first one for that call is bad. Nothing is saved.
- **Malformed date or time**: the row is bad.
- **Applying the same file twice**: the result is the same as applying it once.
- **The `call_type` column**: it must equal the loaded call's type. A mismatch makes the row bad.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST read a results file with the columns `demo_id`, `hvb_call_id`, `call_type`, `date` (YYYY-MM-DD), `time` (HH:MM), `missed_steps`, and `wrong_steps`. `missed_steps` and `wrong_steps` hold semicolon-separated rubric step keys.
- **FR-002**: For each row, the system MUST find the loaded call whose external ID equals `hvb_call_id`.
- **FR-003**: The system MUST set the call's start time to `date` and `time` read as America/Toronto local time.
- **FR-004**: The system MUST set each of the call's rubric steps to "missed" if it is listed in `missed_steps`, to "wrong" if it is listed in `wrong_steps`, and otherwise to "completed". A key listed in both cells is a bad row (FR-008).
- **FR-005**: A missed or wrong step MUST lose its full point value. A completed step MUST lose 0. No points stay under review.
- **FR-006**: Each step's severity MUST come from the points that step lost, using the severity bands in the shared procedure rules (schema3 `_common`), with 0 lost meaning "none". There MUST NOT be a second, separately maintained band table.
- **FR-007**: The call's points lost MUST be the sum over its steps. Its score MUST be 100 minus points lost, never below 0. Its counts (total, completed, missed, wrong, under review = 0) MUST match its steps, and its status MUST be "scored".
- **FR-008**: The system MUST validate the whole file before saving anything. A row is bad if any of these hold:
  - its call is missing
  - its call has no rubric steps stored
  - its call is named by another row in the same file (every row after the first one for that call is bad)
  - it names an unknown step key, meaning a key that is not one of the call's stored steps
  - it lists the same key as both missed and wrong
  - its `call_type` differs from the loaded call's type
  - its `date` or `time` is malformed

  If any row is bad, the run MUST fail, report every problem with the row's demo ID, and save nothing.
- **FR-009**: When the file is valid, all rows MUST be saved together, and the run MUST report how many calls were updated.
- **FR-010**: Calls not named in the file MUST NOT change. The `calls_sample_56` data set stays in the repository unchanged.
- **FR-011**: The scoring rules (step status, points lost, severity, score, counts) MUST be computable and testable without a database or web server.
- **FR-012**: The rejected one-off script (`backend/app/apply_results.py`) MUST NOT exist after this change.

### Key Entities

- **Results row**: one curated outcome. It holds a demo ID (for messages), the call's external ID, the call type (must match the loaded call), a local date and time, and the sets of missed and wrong step keys.
- **Call**: a loaded call. It holds an external ID, start time, status, score, points lost, and step counts.
- **Step result**: one rubric step of a call. It holds a key, name, point value, status, severity, points lost, points under review, and an optional explanatory note.
- **Severity bands**: the shared rubric's named ranges of points lost (slip 1–5, inaccuracy 6–10, mistake 11–20, critical 21+ at the time of writing).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After load and apply, all 48 rows are updated in one run, with no problems reported.
- **SC-002**: Call `a2f086d27b3a4f96` has score 45 after apply.
- **SC-003**: A file with one bad row leaves 100% of calls unchanged, and every bad row is named in the output.
- **SC-004**: Every scoring rule has an automated test that runs with no database.
- **SC-005**: End to end, together with feature ListCalls and the demo clock 2026-10-09T23:59:59Z, the screen shows:
  - this week: 53 of 59 required steps, 90%
  - weekly percents: 64, 70, 68, 75, 80, 79, 86, 90
  - call `a2f086d27b3a4f96` labelled "Wrong: Submit and confirm transfer"

  This is verified after ListCalls, not by this feature alone.

## Assumptions

- The demo calls are loaded first with the existing loader in demo-results mode, so each call already has its rubric steps. Apply updates steps; it does not create them.
- "Unknown step key" means a key that is not one of that call's stored steps. For a demo call, those are its procedure's steps.
- 8 of the 48 demo call IDs also appear in `calls_sample_56`. If both sets are loaded, those 8 calls are updated by apply. That is expected; the sample files themselves are not changed.
- The command is a presenter or developer tool run from the backend folder with the same database setting as the loader. It is not a web endpoint.
- The existing loader (`load_calls`) is not changed by this feature.
