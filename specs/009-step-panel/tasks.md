---
description: "Tasks for the call detail step panel (#36)"
---

# Tasks: Call detail step panel and coaching

**Input**: Design documents from `/specs/009-step-panel/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [data-model.md](./data-model.md), [contracts/step-panel.md](./contracts/step-panel.md)

**Tests**: Every new function has a Vitest test in the same commit.

**Organization**: One use case, `ViewCallDetail`, extended. No new endpoint.

## Use Case: ViewCallDetail (from plan.md Summary)

**Goal**: An agent opens a stored call and sees its required steps, the first failed step selected, and that step's quote, coaching, and Transfer money comparison.

**Independent Test**: [quickstart.md](./quickstart.md) section 1, on `/calls/1`.

- [ ] T001 Map `steps`, `type_details` and `call_type` in `callDetail/entities.ts` and `callDetail/api.ts`. Tests in `api.test.ts`: the sample call yields seven steps, the wrong step's coaching sentence, the three transfer rows, and a step with an unknown status is dropped.

- [ ] T002 Format the step list and the selected panel in `callDetail/presenter.ts` and add the views to `callDetail/viewModel.ts`. Tests in `presenter.test.ts`: status and points wording, the sample panel (0:33 quote, coaching, reversed From/To), a completed step with no coaching and no table, and the default selection.

- [ ] T003 Draw the step list and panel in `callDetail/parts.tsx` and `callDetail/CallDetailPage.tsx`. Test in `CallDetailPage.test.tsx`: opening the sample call selects the wrong step, shows the coaching sentence and the reversed accounts, and choosing "Greet and open" clears the coaching.

- [ ] T004 Confirm `callDetail/layering.test.ts` still passes: the page and parts do not import the API adapter, the gateway, the interactor, or the composer.
