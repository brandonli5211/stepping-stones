---

description: "Task list for ViewProgress (issue #37, frontend half)"
---

# Tasks: View Progress

**Input**: Design documents from `/specs/007-view-progress/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/progress-view.md, quickstart.md, constitution.md (1.5.0)

**Tests**: cut on 2026-11-19 to three Vitest tests at the product owner's request. This does not meet constitution VI or all of spec FR-016; the deviation is recorded in plan.md Complexity Tracking. The browser check is T006.

**Organization**: ONE Clean Architecture use case, `ViewProgress` (plan.md Summary), as a single vertical slice of 6 tasks. Spec stories US1–US4 are all served by this one slice.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: `[US1]` = the single use-case slice
- Paths are relative to the repository root

## Use Case: ViewProgress (from plan.md Summary)

**Goal**: opening Progress shows the server's 8-week chart, this week and the comparison line, the by-call-type bars, the step rows with stones, the legend and the "Demo data" badge. The page computes nothing.

**Independent Test** (full steps in quickstart.md):
1. `npm test` and `npm run lint` are green in `frontend/`.
2. With the demo data and `DEMO_TODAY=2026-10-09T23:59:59+00:00`, the page shows the values listed in contracts/progress-view.md "With the demo data".
3. With the API stopped, the page shows "Couldn't load your progress".

- [X] T001 [US1] **Entities and application.** In `frontend/src/progress/` create `entities.ts`, `inputData.ts` (`ViewProgressInputData`), `inputBoundary.ts` (`ViewProgressInputBoundary`), `outputData.ts` (`ViewProgressOutputData`), `outputBoundary.ts` (`ViewProgressOutputBoundary`), `dataAccess.ts` (`ProgressDataAccess`) and `interactor.ts` (`ViewProgressInteractor`), per data-model.md "Entities" and "Application". The interactor follows the five steps there, including "If a newer request has started since, do nothing" and `"Unknown error"` for a rejection that is not an `Error`. No unit test of its own (2026-11-19 test cut): the interactor runs in T005's App-level test (success) and T004's error-state test.
- [X] T002 [P] [US1] **Typed gateway and sample data.** Create `frontend/src/progress/api.ts` (`ProgressDto` types, `ProgressApi` with `getProgress`, `progressPath`, `toProgress`) per data-model.md and research.md R3. Edit `frontend/src/gateway.ts`: add `SAMPLE["/progress"]` in the server contract's shape (8 weeks, 2 call types, 3 step rows, `demo_data: true`, a `comparison` line), and look samples up by `path.split("?")[0]`. No unit test (2026-11-19 test cut): `ProgressApi` runs in T005's App-level test; the sample answer is checked only in the browser (T006).
- [X] T003 [P] [US1] **Presenter and view model.** Create `frontend/src/progress/viewModel.ts` (state types from contracts/progress-view.md and `ProgressViewModel` with `getState`, `setState`, `subscribe`) and `presenter.ts` (`FIRST_STEP_ROWS = 5`, `ViewProgressPresenter` with the three boundary methods and the helpers `weekLabel`, `percentText`, `barSize`, `thisWeekText`), exactly per the "Presenter rules" table in data-model.md. No unit test of its own (2026-11-19 test cut): both run in T005's App-level test and T004's error-state test.
- [X] T004 [US1] **Controller, composition and components.** Create `frontend/src/progress/controller.ts` (`ViewProgressController`), `compose.ts` (`createProgressScreen`, `parseAgentId`), `parts.tsx` (`WeekChart`, `CallTypeBars`, `StepRows`), `ProgressPage.tsx` and `frontend/src/components/ui/badge.tsx` (`Badge`), per data-model.md "Interface adapters" and "UI" and research.md R4–R6. Components use the shell's `Card`, `PageHeader`, `Stone`, `StatusLegend` and `StateMessage`. Tests:
  - `ProgressPage.test.tsx`: `progress error state`: the page calls `controller.load()` once on mount; after `prepareFailView` it shows an alert with \"Couldn't load your progress\" and the reason, no chart and no badge.
  - `layering.test.ts`: `imports point inward`: the application and adapter modules (`entities`, `inputData`, `inputBoundary`, `outputData`, `outputBoundary`, `dataAccess`, `interactor`, `controller`, `presenter`, `viewModel`, `api`) do not import `react` or components; the application modules import only each other; `ProgressPage.tsx` and `parts.tsx` do not import `./api`, `../gateway`, `./interactor` or `./compose`.
  - The controller, composition, parts and badge have no unit test of their own (2026-11-19 test cut); they run in T005's App-level test.
- [X] T005 [US1] **Wire into the shell.** Edit `frontend/src/App.tsx`: build `createProgressScreen(api, parseAgentId(import.meta.env.VITE_AGENT_ID))` once next to `api`; render `<ProgressPage viewModel={…} controller={…} />` for the progress screen; remove the placeholder's `week` and `error` state, its effect and its markup. Edit `frontend/src/App.test.tsx`: the existing progress test (by the shell's author) expects "Couldn't load your progress" when the API is down (a one-line change), and a new test, `progress shows what the api sends`, answers `fetch` with a progress body of 6 step rows and checks the comparison line, the badge, this week, a summary line, the marked menu item, and that "Show all 6 steps" shows the sixth row and "Show fewer" hides it again. Edit `.env.example`: document `VITE_AGENT_ID`. The other three screens are unchanged.
- [X] T006 [US1] **Verification.** Run `npm install`, `npm test` and `npm run lint` in `frontend/`, and `uv run test` in `backend/`. Run quickstart.md step 2 against PostgreSQL 18 in a throwaway database and record the results here: the values on the page (SC-001 to SC-006), the failure message (SC-007), sample mode, and the other pages. Save a screenshot of the Progress page with the demo data to `specs/007-view-progress/screenshots/progress-demo-data.png` (SC-009). Drop the throwaway database.

  **Results (2026-11-16)**:
  - `npm test`: 24 passed in 6 files (21 before this feature), as rebuilt on 2026-11-19. `npm run lint`: clean. Backend `uv run test`: 63 passed.
  - Browser run (headless Chrome) against the API on PostgreSQL 18 in the throwaway database `stepping_stones_verify_007` (dropped afterwards; the main database was not touched), with `DEMO_TODAY=2026-10-09T23:59:59+00:00`:
    - SC-001: 8 bars, Aug 17 to Oct 5, reading 64%, 70%, 68%, 75%, 80%, 79%, 86%, 90%; only the last is current and says "This week".
    - SC-002: "53 of 59 required steps completed" and "Up from 64% in week 1".
    - SC-003: Check balance 88%, Get branch hours 86%, Order checks 85%, Reset password 80%, Pay bill 79%, Schedule appointment 77%, Replace card 73%, Transfer money 69%.
    - SC-004: 5 rows shown, in the server's order (Confirm replacement, Confirm appointment, Offer further help, State account balance, Collect company address), with a "Show all 26 steps" button. Clicking "Show all" was checked by the App-level test (with 6 rows), not in the browser.
    - SC-005: the stones of the five visible rows were compared with the same steps on the My calls page for the calls that page lists (its 10 newest): 7 stones compared, 0 mismatches. The Transfer money rows are not among the five visible rows; their agreement with `GET /calls` was checked for feature 006 at the API.
    - SC-006: the "Demo data" badge shows. The legend shows under the rows.
    - SC-007: with the API stopped, the page shows an alert "Couldn't load your progress" with "Failed to fetch" and no chart.
    - Sample mode (`VITE_SAMPLE_DATA=true`, no API): the sample answer shows, with 8 bars.
    - Other pages: My calls, Call 7 and Procedures render as before.
  - SC-009: screenshot saved to `specs/007-view-progress/screenshots/progress-demo-data.png` (1440 px wide). Comparing it with the Figma frame is left to a person.

## Dependencies & Execution Order

1. T001 comes first.
2. T002 and T003 depend on T001 and can run in parallel.
3. T004 depends on T001–T003.
4. T005 depends on T004.
5. T006 depends on all of the above.

## Implementation Strategy

1. Implement T001→T006 in order. `npm test` and `npm run lint` must be green before the next task.
2. Stop when the independent test above passes.

## Notes

- 6 tasks, one use case. Hard ceiling reached; convergence findings must be folded into an existing task.
- No new dependency. No backend change.
- Do not commit until asked.
