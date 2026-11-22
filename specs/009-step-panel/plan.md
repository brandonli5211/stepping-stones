# Implementation Plan: Call detail step panel and coaching

**Branch**: `feat/36-call-detail-steps` | **Date**: 2026-11-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/009-step-panel/spec.md`

## Summary

Keep the existing `ViewCallDetail` use case. The call page already loads `GET /calls/{id}` and already selects a step for the transcript. This work maps the stored `steps` and `type_details` that the mapper currently drops, presents the selected step, and draws the list and panel on the right of the call page. The page still does not score.

## Technical Context

**Language/Version**: TypeScript 5, React 19

**Primary Dependencies**: Vite, Tailwind, the existing shadcn/ui pieces, Vitest

**Storage**: None. The rows are already on the call.

**Testing**: Vitest. Every new function has a test in the same commit.

**Target Platform**: The call page at `/calls/{id}`

**Project Type**: Web frontend, extending `frontend/src/callDetail/`

**Performance Goals**: No extra request. The panel uses the response the page already loads.

**Constraints**: One use case. No new endpoint. Formatting lives in the presenter. The page only draws. "I did do this" stays hidden.

**Scale/Scope**: One call, its steps, one selected step.

## Constitution Check

*GATE: Must pass before implementation. Re-check after design.*

- One primary use case: `ViewCallDetail`. This feature extends its mapper, presenter and view. It does not add a second use case that reloads the call.
- Server owns judgment. Step result, points, quote, coaching and field result are read from the stored response.
- New functions are unit tested. The page test covers the Transfer money story end to end.
- The new drawing stays in `callDetail/parts.tsx` and `CallDetailPage.tsx`. They do not import the gateway, the API adapter, or the interactor.

## Use Cases *(mandatory)*

### ViewCallDetail

- **Actor**: an agent reviewing one stored call
- **Input**: the call id already used by the page
- **Output**: the existing header, score, transcript and flags, plus the step list and the selected step's panel
- **Flow**: the interactor loads the call as it does today. The mapper now keeps steps and type details. The presenter formats them and selects the first missed or wrong step when nothing valid is selected. The page draws the list and panel and calls the existing `selectStep`.
- **Rules**: the first missed or wrong step is the default. A completed step shows no deduction and no coaching. The Transfer money table is shown only while a missed or wrong step is selected, and only the stored result words are used. An unrecognised step result is dropped.
- **Errors**: the existing loading, not-found and failure states stay. A call with no steps shows an empty list.

## Project Structure

### Documentation (this feature)

```text
specs/009-step-panel/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/step-panel.md
└── tasks.md
```

### Source Code (repository root)

```text
frontend/src/callDetail/
├── entities.ts      # Step, SubCheck, FieldRow added to CallDetail
├── api.ts           # map steps and type_details
├── presenter.ts     # step rows, panel, default selection
├── viewModel.ts     # step views on the ready state
├── parts.tsx        # step list and panel
└── CallDetailPage.tsx
```

**Structure Decision**: Extend the existing call-detail module. No backend change. No new route.

## Complexity Tracking

No constitution violation.
