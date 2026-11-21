# Implementation Plan: Call detail page: transcript, score, flags

**Branch**: `feat/35-call-detail-transcript` | **Date**: 2026-11-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/008-call-detail-transcript/spec.md`

## Summary

**Primary use case**: `ViewCallDetail` — load one stored call and hand it, or a loading, not-found or failure notice, to the presenter.

The agent opens `/calls/{id}` and sees the header, score panel, transcript with evidence and wrong labels, and flags for that call. Everything comes from `GET /calls/{id}` (#34, merged in #50), which already works out the score, counts, notes and flags. The page only formats: it places the score in its band, turns seconds into `m:ss`, hides filler turns, and words the flag count. Choosing a flag selects that step, which scrolls the transcript to its first marked turn and highlights all of its turns; #36 reuses the same selection.

The module mirrors `frontend/src/progress/`: entities, input/output data and boundaries, the data access interface and the interactor form the application layer; controller, presenter, view model and the typed API form the adapters; `compose.ts` wires them; `CallDetailPage.tsx` and `parts.tsx` only draw the view model. Imports point inward, and a layering test checks it.

## Use Cases

| Use case | Responsibility | Module |
| --- | --- | --- |
| `ViewCallDetail` (primary) | Load one stored call by id and pass it, or loading / not-found / failure, to the output boundary. It never judges steps, computes the score or creates notes or flags. | `frontend/src/callDetail/interactor.ts` |

**Out of scope for this plan**: the required-steps list and step panel (#36), "I did do this" (#40), any backend change. Step selection is view state on the same page, not a second use case.

## Technical Context

**Language/Version**: TypeScript 5.9, React 18.3

**Primary Dependencies**: Tailwind CSS 4, shadcn/ui pieces already in `frontend/src/components/ui` (Card, Badge), the shell's `ApiGateway`

**Storage**: N/A (reads `GET /calls/{id}`)

**Testing**: Vitest 2 with Testing Library and jsdom (`npm test`), `npm run lint` (`tsc --noEmit`)

**Target Platform**: Desktop browser, served by Vite

**Project Type**: Web application (frontend module only)

**Performance Goals**: Choosing a flag brings the first marked turn into view within 1 s (SC-006); a 200-turn transcript renders without layout breakage (SC-005)

**Constraints**: Constitution I (no judgement on the page), IV (React + TypeScript + Tailwind + shadcn/ui, no new `.js`/`.jsx`), V (no new dependencies), VI (a unit test for every new function), VII (Clean Architecture)

**Scale/Scope**: One page, one use case, about 15 new files under `frontend/src/callDetail/`, small edits to `App.tsx`, `gateway.ts` and `components/pieces.tsx`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
| --- | --- | --- |
| I. Server owns the judgment | The page shows the stored score, counts, notes and flags. Banding the score, `m:ss` times, filler hiding and the flag count wording are display formatting in the presenter. | Pass |
| II. Asynchronous API | No backend change. | Pass (N/A) |
| III. Asynchronous persistence | No schema change. | Pass (N/A) |
| IV. Typed component UI | All new files are `.ts`/`.tsx`, styled with Tailwind, using the existing shadcn/ui Card and Badge. | Pass |
| V. One stack | No new dependency. | Pass |
| VI. Unit test every new function | Each new function and method has a Vitest test (api mapping, interactor paths, presenter formatters, view model, controller, compose helpers, page states). | Pass (enforced in tasks) |
| VII. Clean Architecture | Application files import only each other; adapters import no React or components; the page imports only the view model, controller and shared pieces. Checked by `layering.test.ts`. | Pass |

Post-design re-check (after Phase 1): still passes. The only shell edits are a typed `ApiError` in `gateway.ts` (so a 404 can be told apart from a failure), a band-aware `ScoreRing`, and the route in `App.tsx`; none moves logic across layers.

## Project Structure

### Documentation (this feature)

```text
specs/008-call-detail-transcript/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── call-detail-view.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
frontend/src/
├── callDetail/
│   ├── entities.ts          # CallDetail, Turn, Note, Flag, Score (application)
│   ├── inputData.ts         # ViewCallDetailInputData(callId)
│   ├── inputBoundary.ts     # ViewCallDetailInputBoundary
│   ├── outputData.ts        # ViewCallDetailOutputData(detail)
│   ├── outputBoundary.ts    # loading / success / not found / fail
│   ├── dataAccess.ts        # CallDetailDataAccess: getCallDetail(id) -> CallDetail | null
│   ├── interactor.ts        # ViewCallDetailInteractor
│   ├── api.ts               # CallDetailDto + CallDetailApi (DTO -> entities, 404 -> null)
│   ├── presenter.ts         # band, m:ss, filler hiding, flag counts, labels
│   ├── viewModel.ts         # view state + selected step
│   ├── controller.ts        # load(), selectStep(key)
│   ├── compose.ts           # parseCallId, createCallDetailScreen
│   ├── CallDetailPage.tsx   # draws the view model
│   ├── parts.tsx            # ScorePanel, Transcript, Flags
│   ├── *.test.ts(x)         # one test file per source file
│   └── layering.test.ts
├── components/pieces.tsx    # ScoreRing gains its band (shared with #25)
├── gateway.ts               # ApiError with status; sample answer for /calls/{id}
└── App.tsx                  # route /calls/{id} to CallDetailPage
```

**Structure Decision**: A feature module under `frontend/src/callDetail/`, laid out exactly like `frontend/src/progress/`, so both screens read the same way and the layering test can be copied.

## Complexity Tracking

No constitution violations to justify.
