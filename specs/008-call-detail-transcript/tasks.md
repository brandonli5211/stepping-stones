---

description: "Tasks for the call detail page: transcript, score, flags (#35)"
---

# Tasks: Call detail page: transcript, score, flags

**Input**: Design documents from `/specs/008-call-detail-transcript/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/call-detail-view.md](./contracts/call-detail-view.md)

**Tests**: Constitution VI applies. Every new or changed function gets its Vitest test in the same commit, listed inside each task.

**Organization**: One Clean Architecture use case, `ViewCallDetail`, in six tasks. Team rule: one commit per component or function, so each task lists its commits; each commit carries the code and its test and leaves `npm test`, `npm run lint` and `npm run build` passing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[US1]**: the single `ViewCallDetail` slice
- All paths are under `frontend/src/`

## Use Case: ViewCallDetail (from plan.md Summary)

**Goal**: An agent opens `/calls/{id}` and sees the header, score panel, transcript with evidence and wrong labels (filler turns hidden), and flags for that stored call; choosing a flag highlights that step's turns.

**Independent Test**: [quickstart.md](./quickstart.md) section 2: in sample mode `/calls/1` matches the Figma frame "Call review" (45 in "Focus here", 6 of 7, "1 critical, 55 points lost", 9 turns, the 0:44 turn wrong and also evidence for Offer further help, one flag), and `/calls/abc` shows the not-found state.

- [x] T001 [P] [US1] Shell support in `gateway.ts` and `components/pieces.tsx`. Commits:
  1. `ApiError` (extends `Error`, has `status: number`) thrown by `createApiGateway().get` when `res.ok` is false; tests in `gateway.test.ts` that a 404 rejects with `ApiError` whose `status` is 404 and that Progress-style callers still see an `Error`.
  2. Sample answer for any `/calls/{n}` path in sample mode: the Transfer money example from `docs/api-contract.md` (`header`, `score` 45 / 6 of 7 / 55 lost / 1 critical, `flags` with one critical wrong flag for `submit_and_confirm_transfer`), with the 9 frame turns and their notes plus a few filler turns (`[noise]`, `okay`, `<unk>`, `mm hmm`) that carry no notes; test that `/calls/1` and `/calls/7` both return it.
  3. `scoreBand(score: number | null)` returning `"on_track"` (85 to 100), `"getting_there"` (60 to 84), `"focus_here"` (under 60) or `null`, and `ScoreRing` taking an optional `band` to colour the ring; tests in `components/pieces.test.tsx` for 59, 60, 84, 85, null, and that the ring still renders without a band.

- [x] T002 [P] [US1] Application layer in `callDetail/`. Commits:
  1. `entities.ts` with `CallDetail`, `Score`, `Turn`, `Note`, `Flag`, `Severity` exactly as in data-model.md (`speaker: "agent" | "caller"`, `Note.kind: "evidence" | "wrong"`, `Flag.status: "missed" | "wrong"`, `Severity` is `"none" | "slip" | "inaccuracy" | "mistake" | "critical"`), plus `inputData.ts` (`ViewCallDetailInputData(callId: number)`), `inputBoundary.ts`, `outputData.ts` (`ViewCallDetailOutputData(detail)`), `outputBoundary.ts` (`prepareLoadingView`, `prepareSuccessView`, `prepareNotFoundView`, `prepareFailView(message)`) and `dataAccess.ts` (`getCallDetail(callId): Promise<CallDetail | null>`, null when the call does not exist).
  2. `interactor.ts`: `ViewCallDetailInteractor.execute` calls `prepareLoadingView`, then success with the detail, not found on `null`, or fail with the error message; an answer to an older request is dropped (same guard as `progress/interactor.ts`). Tests in `interactor.test.ts` with a fake data access and presenter for all four paths and the stale-answer case.

- [x] T003 [US1] Typed API adapter in `callDetail/api.ts`. One commit: `CallDetailDto` (the `GET /calls/{id}` body, snake_case names kept in this file) and `CallDetailApi implements CallDetailDataAccess` with `callDetailPath(id)` (`/calls/{id}`), `getCallDetail(id)` (returns `null` when the gateway rejects with `ApiError` status 404, rethrows anything else) and `toCallDetail(dto)` (maps `header`, `score`, `transcript`, `flags` to the entities; drops a note whose `kind` is not `evidence` or `wrong`). Tests in `api.test.ts`: path, full mapping of the sample answer, 404 → null, 500 → rejects, unknown note kind dropped.

- [x] T004 [US1] Presenter, view model and controller in `callDetail/`. Commits:
  1. `viewModel.ts`: `CallDetailViewState` (`loading`, `error`, `notFound`, `ready`) and `CallDetailViewModel` with `getState`, `setState`, `subscribe`, `selectedStepKey`, `selectStep(key | null)`; tests that subscribers are told on state and selection changes.
  2. Presenter helpers with their tests: `formatTime(seconds | null)` (`33.53` → `"0:33"`, `65` → `"1:05"`, null → null), `isFillerTurn(turn)` (true when the text, after removing `[...]` and `<...>` markers, is empty or exactly one of `okay`, `ok`, `and`, `um`, `uh`, `yeah`, `mm hmm`, `mhm` case-insensitively, and the turn has no notes; `yes` is not filler), `turnTone(notes)` (`wrong` if any wrong, else `evidence` if any evidence, else `plain`), `lostText(score)` (`"1 critical, 55 points lost"`, `"55 points lost"` when no critical, null when nothing lost), `flagCountText(flags)` (counts per severity, most severe first, e.g. `"1 critical"`, null when none).
  3. `presenter.ts`: `ViewCallDetailPresenter` builds the `ready` state from data-model.md (header, score with `scoreBand`, transcript with filler turns hidden and `"N turns, verbatim"` counting shown turns, `empty` when none are shown, flags with `"−55 points"`) and sets `loading` / `error` ("Couldn't load this call") / `notFound` ("Call not found"); tests that the sample answer gives exactly 9 turns, the 0:33 and 0:44 labels, "Not scored yet" for a null score and the provisional "so far" text.
  4. `controller.ts`: `ViewCallDetailController(useCase, callId, viewModel)` with `load()` and `selectStep(key)`; tests that `load()` sends `ViewCallDetailInputData(callId)` and `selectStep` updates the view model.

- [x] T005 [US1] Page and wiring. Commits:
  1. `callDetail/parts.tsx`: `ScorePanel`, `Transcript` (own scroll container; evidence and wrong labels with an icon each; turns whose `stepKeys` include the selected key are highlighted and the first is scrolled into view) and `FlagList` (flag cards are buttons calling `onSelect(stepKey)`; "Nothing to fix on this call" when empty); tests in `parts.test.tsx` with Testing Library.
  2. `callDetail/CallDetailPage.tsx`: draws loading, error with a Retry button calling `controller.load()`, not found with "Back to my calls", and ready (header, `ScorePanel`, `Transcript`, `FlagList`); tests in `CallDetailPage.test.tsx` for each state and that choosing the flag highlights the 0:33 and 0:44 turns.
  3. `callDetail/compose.ts`: `parseCallId(text)` (a positive whole number or null) and `createCallDetailScreen(gateway, callId)`; `App.tsx` replaces the call detail placeholder with `CallDetailPage` (a null id shows not found without a request); tests in `compose.test.ts` and an `App.test.tsx` case for `/calls/1` in sample mode.
  4. `callDetail/layering.test.ts`, copied from `progress/layering.test.ts` with this module's file names.

- [ ] T006 [US1] Validation per [quickstart.md](./quickstart.md): `npm test -- --run`, `npm run lint`, `npm run build`; sample mode at `/calls/1` and `/calls/abc`; real API with the demo data for the Transfer money call; greyscale check (SC-004); a 200-turn sample check (SC-005); take the screenshot next to the Figma frame for the PR.

**Checkpoint**: `ViewCallDetail` works through the layers; application files import only each other, adapters import no React, and the page never computes a score or judges a step.

---

## Dependencies & Execution Order

1. T001 and T002 are independent of each other ([P]).
2. T003 needs T001.1 (`ApiError`) and T002.1 (entities, data access).
3. T004 needs T002 (output boundary) and T001.3 (`scoreBand`).
4. T005 needs T003 and T004.
5. T006 last.

## Implementation Strategy

1. Implement T001 → T006 in order, one commit per listed item.
2. Stop when the independent test above passes.
3. The steps list and step panel (#36) are a new feature spec, not more rows here.

## Notes

- Six checkbox tasks, about 15 commits.
- No backend change and no new dependency.
- Keep labels, counts and flags exactly as the API sends them; the presenter only formats.
