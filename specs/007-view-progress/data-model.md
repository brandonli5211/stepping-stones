# Data Model: View Progress

All modules are in `frontend/src/progress/` unless a path is given.

## Entities: `entities.ts` (types only)

| Type | Fields |
| --- | --- |
| `StepResultStatus` | `"completed" \| "missed" \| "wrong"` (any other string is passed through and drawn as under review) |
| `ProgressWeek` | `weekStart: string` (`YYYY-MM-DD`), `stepsCompleted: number`, `stepsTotal: number`, `percent: number \| null`, `isCurrent: boolean` |
| `WeekNumbers` | `stepsCompleted: number`, `stepsTotal: number`, `percent: number \| null` |
| `CallTypeProgress` | `callType: string`, `name: string`, `stepsCompleted: number`, `stepsTotal: number`, `percent: number \| null`, `calls: number` |
| `StepRow` | `stepKey: string`, `name: string`, `callType: string \| null`, `label: string`, `results: string[]`, `misses: number`, `window: number`, `summary: string` |
| `Progress` | `demoData: boolean`, `weeks: ProgressWeek[]`, `thisWeek: WeekNumbers \| null`, `firstWeekPercent: number \| null`, `comparison: string \| null`, `callTypes: CallTypeProgress[]`, `steps: StepRow[]` |

## Application

| Module | Name | Definition |
| --- | --- | --- |
| `inputData.ts` | `ViewProgressInputData` (class) | `constructor(readonly agentId: number \| null)` |
| `inputBoundary.ts` | `ViewProgressInputBoundary` (interface) | `execute(input: ViewProgressInputData): Promise<void>` |
| `outputData.ts` | `ViewProgressOutputData` (class) | `constructor(readonly progress: Progress)` |
| `outputBoundary.ts` | `ViewProgressOutputBoundary` (interface) | `prepareLoadingView(): void`; `prepareSuccessView(output: ViewProgressOutputData): void`; `prepareFailView(message: string): void` |
| `dataAccess.ts` | `ProgressDataAccess` (interface) | `getProgress(agentId: number \| null): Promise<Progress>`. Rejects with an `Error` when the progress cannot be loaded. |
| `interactor.ts` | `ViewProgressInteractor` (class, implements the Input Boundary) | `constructor(dataAccess, presenter)`; `execute(input)` |

**`ViewProgressInteractor.execute`**:

1. Take the next request number and call `presenter.prepareLoadingView()`.
2. `await dataAccess.getProgress(input.agentId)`.
3. If a newer request has started since, do nothing.
4. On success call `presenter.prepareSuccessView(new ViewProgressOutputData(progress))`.
5. On failure call `presenter.prepareFailView(message)`, where `message` is the error's message, or `"Unknown error"` when the rejection is not an `Error`.

## Interface adapters

| Module | Name | Definition |
| --- | --- | --- |
| `controller.ts` | `ViewProgressController` (class) | `constructor(useCase: ViewProgressInputBoundary, agentId: number \| null)`; `load(): Promise<void>` calls `useCase.execute(new ViewProgressInputData(agentId))` |
| `viewModel.ts` | `ProgressViewModel` (class) | `state: ProgressViewState` (starts as loading); `setState(state): void` stores it and calls every listener; `subscribe(listener): () => void` returns an unsubscribe function; `getState(): ProgressViewState` |
| `presenter.ts` | `ViewProgressPresenter` (class, implements the Output Boundary) | `constructor(viewModel)`; the three boundary methods; helpers below |
| `api.ts` | `ProgressApi` (class, implements `ProgressDataAccess`) | `constructor(gateway: ApiGateway)`; `getProgress(agentId)`; `progressPath(agentId): string`; `toProgress(dto: ProgressDto): Progress` |
| `compose.ts` | `createProgressScreen(gateway: ApiGateway, agentId: number \| null)` | returns `{ viewModel, controller }`, wired as in plan.md |
| `compose.ts` | `parseAgentId(value: string \| undefined): number \| null` | a whole number of 1 or more, otherwise `null` |

**View state** (`viewModel.ts`), see [contracts/progress-view.md](contracts/progress-view.md):

`ProgressViewState` = `{ kind: "loading"; message }` \| `{ kind: "error"; title; message }` \| `{ kind: "empty"; showDemoBadge; message }` \| `ProgressReadyState`.

**Presenter rules** (`presenter.ts`):

| Item | Rule |
| --- | --- |
| `FIRST_STEP_ROWS` | `5` |
| `prepareLoadingView()` | state `{ kind: "loading", message: "Loading your progress…" }` |
| `prepareFailView(message)` | state `{ kind: "error", title: "Couldn't load your progress", message }` |
| `prepareSuccessView(output)` | `empty` state with `"No analysed calls in the last 8 weeks"` when `callTypes` and `steps` are both empty. Otherwise the `ready` state. |
| `weekLabel("2026-08-17")` | `"Aug 17"` (split the string; fixed English month names; no `Date`) |
| `percentText(p)` | `"90%"`, or `"–"` for `null` |
| `barSize(p)` | `p` limited to 0–100, or `0` for `null` |
| `thisWeekText(week)` | `"53 of 59 required steps completed"`, or `"No analysed calls this week"` for `null` or 0 steps required |
| week bar | `{ label, percentText, height: barSize(percent), isCurrent, currentText: "This week" or null }` |
| call type bar | `{ key: callType, name, percentText, stepsText: "42 of 48 steps", width: barSize(percent) }` |
| step row view | `{ key: (callType or "all") + ":" + stepKey, name, label, stones: [{ status }], summary }`, with `summary` and `label` unchanged and stones in the given order |
| `firstSteps`, `allSteps` | the first `FIRST_STEP_ROWS` rows, and all rows |
| `showAllLabel` | `"Show all 26 steps"` when there are more than `FIRST_STEP_ROWS` rows, otherwise `null` |
| `comparison` | passed through unchanged (`null` stays `null`) |

## UI

| Module | Component | Renders |
| --- | --- | --- |
| `ProgressPage.tsx` | `ProgressPage({ viewModel, controller })` | Subscribes to the view model. Calls `controller.load()` once on mount. Draws the header, the badge when asked, then by `state.kind`: the loading text, the error or empty message (the shell's `StateMessage`), or the three sections and the legend. Holds one boolean, `expanded`. |
| `parts.tsx` | `WeekChart({ weeks })` | the 8 bars with percent, label and "This week" |
| `parts.tsx` | `CallTypeBars({ callTypes })` | one row per call type |
| `parts.tsx` | `StepRows({ rows })` | one row per step with the shell's `Stone` for each result |
| `components/ui/badge.tsx` | `Badge` | a small pill; `data-slot="badge"` |

## Edited modules

| Module | Change |
| --- | --- |
| `gateway.ts` | `SAMPLE["/progress"]`: a short answer in the contract's shape (8 weeks, 2 call types, 3 step rows, `demo_data: true`). The sample lookup uses `path.split("?")[0]`. |
| `App.tsx` | Build `createProgressScreen(api, parseAgentId(import.meta.env.VITE_AGENT_ID))` once. Render `<ProgressPage … />` for the progress screen. Remove the placeholder's state, effect and markup. |
| `.env.example` | Document `VITE_AGENT_ID`. |
