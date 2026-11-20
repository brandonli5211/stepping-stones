# Implementation Plan: View Progress

**Branch**: `feat/37-progress` (issue #37, frontend half) | **Date**: 2026-11-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/007-view-progress/spec.md`

## Summary

**Primary use case**: `ViewProgress`. When the agent opens Progress, it gets the agent's progress from the server through a data access interface and hands it to a presenter, which fills the view model that the page renders. It also reports loading and failure.

The server (feature 006) already sends every number, order and sentence. This use case only fetches and shapes for display.

**Inward dependency path** (all under `frontend/src/progress/`):

| Layer | Modules | What they hold |
| --- | --- | --- |
| Entities | `entities.ts` | The typed progress answer the app works with (`Progress`, `ProgressWeek`, `CallTypeProgress`, `StepRow`). Types only. |
| Application | `inputData.ts`, `inputBoundary.ts`, `outputData.ts`, `outputBoundary.ts`, `dataAccess.ts`, `interactor.ts` | The use case and its boundaries. Imports entities only. No React, no `fetch`. |
| Interface adapters | `controller.ts`, `presenter.ts`, `viewModel.ts`, `api.ts` | The controller, the presenter, the view model, and the typed gateway that implements the data access interface over the shell's `ApiGateway`. No React. |
| UI | `ProgressPage.tsx`, `parts.tsx`, `components/ui/badge.tsx` | Components. They render the view model and call the controller. |
| Composition | `compose.ts`, `App.tsx` | Build the parts once and mount the page. `App.tsx` stays the only place that reads environment settings. |

Nothing inner imports anything outer.

### The nine CSC207 parts

All nine apply on the frontend. Each is its own class or interface in its own file.

| Part | Name | Module |
| --- | --- | --- |
| Controller | `ViewProgressController` (class) | `frontend/src/progress/controller.ts` |
| Input Boundary | `ViewProgressInputBoundary` (interface) | `frontend/src/progress/inputBoundary.ts` |
| Input Data | `ViewProgressInputData` (class) | `frontend/src/progress/inputData.ts` |
| Interactor | `ViewProgressInteractor` (class) | `frontend/src/progress/interactor.ts` |
| Output Boundary | `ViewProgressOutputBoundary` (interface) | `frontend/src/progress/outputBoundary.ts` |
| Output Data | `ViewProgressOutputData` (class) | `frontend/src/progress/outputData.ts` |
| Presenter | `ViewProgressPresenter` (class) | `frontend/src/progress/presenter.ts` |
| View Model | `ProgressViewModel` (class) | `frontend/src/progress/viewModel.ts` |
| Data Access Interface | `ProgressDataAccess` (interface), implemented by `ProgressApi` in `api.ts` | `frontend/src/progress/dataAccess.ts` |

The **View** is `ProgressPage.tsx`.

**How opening the page flows**:

1. `ProgressPage` mounts and calls `controller.load()`.
2. The controller builds `ViewProgressInputData(agentId)` and calls the Input Boundary.
3. The interactor calls `presenter.prepareLoadingView()`, then asks `ProgressDataAccess.getProgress(agentId)`.
4. `ProgressApi` calls `GET /progress` through the shell's gateway and maps the JSON to entities.
5. The interactor calls `prepareSuccessView(new ViewProgressOutputData(progress))`, or `prepareFailView(message)` when the request failed. An answer to an older request is dropped.
6. The presenter sets the view model's state. The page, subscribed to the view model, re-renders.

## Use Cases

*Accurate after Phase 0 (research) and after Phase 1 (design).*

| Use case | Responsibility | Module |
| --- | --- | --- |
| `ViewProgress` (primary) | Loads one agent's progress through the `ProgressDataAccess` interface and passes it, or a loading or failure notice, to the Output Boundary. It never touches React, `fetch` or wording. | `frontend/src/progress/interactor.ts` |

**Out of scope for this plan**:
- Converting the legacy calls page (`CallsPage.jsx`, `api.js`) to TypeScript.
- Wiring the "See your progress" button on My calls.
- Any backend change. Feature 006 is done.

## Technical Context

**Language/Version**: TypeScript 5.9, React 18.3, as set up by the app shell.

**Primary Dependencies**: Tailwind CSS 4, the shell's shadcn/ui card, `clsx` and `tailwind-merge`, all existing. No new dependency: no chart library, and the badge is written without `class-variance-authority` ([research.md](research.md) R5).

**Storage**: none. The page reads `GET /progress`.

**Testing**: Vitest with jsdom and Testing Library (`npm test`), and the type check (`npm run lint`). Three tests cover this feature: `progress shows what the api sends` (the whole app with a mocked `fetch`: gateway, typed API, interactor, presenter and page, including "Show all"), `progress error state` and `imports point inward`. Not every class, function and component has its own test (see Complexity Tracking). End to end is checked in the browser against the API on a throwaway database ([quickstart.md](quickstart.md)).

**Target Platform**: desktop browsers, laptop width and up.

**Project Type**: web application frontend.

**Performance Goals**: one request when the page opens. 26 rows at most on screen.

**Constraints**:
- **Principle I**: the page computes no percent, count, order or sentence.
- **Principle IV**: new files are `.ts` or `.tsx`, styled with Tailwind, with shared components in the shadcn/ui style.
- **Principle VII**: components render state and dispatch intent. API access, DTO mapping and view-model shaping sit outside them.

**Scale/Scope**: one use case, 15 new source modules, 3 edited modules (`App.tsx`, `gateway.ts`, `.env.example`), 6 tasks.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Before research | After design |
| --- | --- | --- |
| I. Server owns the judgment | Pass. The spec forbids computing percents, counts, order or sentences on the page. | Pass. The presenter formats only: `"90%"`, `"Aug 17"`, `"42 of 48 steps"`, a bar length from a percent, and the first-N slice of rows. The comparison and summary lines are shown as sent. |
| II, III. Async API and persistence | Pass. No backend change. | Pass. |
| IV. Typed component UI | Pass (planned). | Pass. Every new file is `.ts` or `.tsx`. Styling is Tailwind. The badge follows the shadcn/ui pattern beside the existing card. |
| V. One stack | Pass. No new package. | Pass. |
| VI. Unit test every new function | Pass (planned). | **Deviation, accepted 2026-11-19.** The tests were cut to three; see Complexity Tracking. |
| VII. Clean Architecture | Pass. One use case with boundaries and a data access interface. | Pass. All nine parts are separate. `ProgressPage` renders and dispatches only. `fetch`, DTO mapping and formatting are in `api.ts` and `presenter.ts`. A test checks that the application and adapter modules do not import React and that the components do not import `api.ts` or the gateway. |
| Workflow | Pass. Branch `feat/37-progress`, issue #37, one primary use case in the Summary and in Use Cases. | Pass. The tasks are planned as one vertical slice of 6. |
| Governance: touched non-compliant files | Pass. `App.tsx` and `gateway.ts` are TypeScript and compliant. `CallsPage.jsx`, `api.js` and `styles.css` are legacy and are not touched. | Pass. |

Principle VI is not met after the 2026-11-19 test cut; the deviation is recorded in Complexity Tracking. No other gate failed.

## Project Structure

### Documentation (this feature)

```text
specs/007-view-progress/
├── spec.md
├── plan.md              # this file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   └── progress-view.md # the view model the page renders
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
frontend/src/
├── progress/
│   ├── entities.ts            # NEW  Progress, ProgressWeek, CallTypeProgress, StepRow
│   ├── inputData.ts           # NEW  ViewProgressInputData
│   ├── inputBoundary.ts       # NEW  ViewProgressInputBoundary
│   ├── outputData.ts          # NEW  ViewProgressOutputData
│   ├── outputBoundary.ts      # NEW  ViewProgressOutputBoundary
│   ├── dataAccess.ts          # NEW  ProgressDataAccess
│   ├── interactor.ts          # NEW  ViewProgressInteractor
│   ├── controller.ts          # NEW  ViewProgressController
│   ├── presenter.ts           # NEW  ViewProgressPresenter
│   ├── viewModel.ts           # NEW  ProgressViewModel and its state types
│   ├── api.ts                 # NEW  ProgressApi, the typed gateway, and the DTO types
│   ├── compose.ts             # NEW  createProgressScreen(api, agentId)
│   ├── parts.tsx              # NEW  WeekChart, CallTypeBars, StepRows
│   ├── ProgressPage.tsx       # NEW  the view
│   ├── ProgressPage.test.tsx  # NEW  the error state
│   └── layering.test.ts       # NEW  dependencies point inward
├── components/ui/badge.tsx    # NEW  shadcn-style badge
├── gateway.ts                 # EDIT sample answer for /progress; sample lookup ignores the query string
├── App.tsx                    # EDIT mount ProgressPage; remove the placeholder; read VITE_AGENT_ID
└── App.test.tsx               # EDIT the existing progress test expects the new error text; new test: the page shows what the API sends
.env.example                   # EDIT document VITE_AGENT_ID
```

**Structure Decision**: one folder per use case, `frontend/src/progress/`, with one part per file. The shell's own modules (`application.ts`, `domain.ts`, `gateway.ts`) keep their layout.

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
| --- | --- | --- |
| Principle VI (unit test every new function) is not met. | On 2026-11-19 the product owner cut this feature's tests to `progress shows what the api sends` (App level), `progress error state` and `imports point inward`. The interactor, typed API, presenter, view model, controller, composition and components are covered only through the App-level test and the error-state test. These have no test: dropping an older request's answer, the empty state, `parseAgentId`, the sample answer for `/progress` in `gateway.ts`, and the badge on its own. The browser run in quickstart.md is their only other check. | One unit test per function was the original plan and was cut on purpose. Reviewers must accept this deviation explicitly. |

## Phase 0 and Phase 1 outputs

- **Phase 0**: [research.md](research.md), decisions R1–R8. No NEEDS CLARIFICATION remained.
- **Phase 1**: [data-model.md](data-model.md), [contracts/progress-view.md](contracts/progress-view.md), [quickstart.md](quickstart.md).

**Step rows shown first**: 5, confirmed by the product owner. It is `FIRST_STEP_ROWS` in `presenter.ts`.

**Post-design constitution check**: all gates passed at design time (Principle VI is a recorded deviation since the 2026-11-19 test cut). Components hold no fetching, mapping or formatting. The application modules import neither React nor the gateway. The Use Cases section lists exactly one primary use case after both phases.
