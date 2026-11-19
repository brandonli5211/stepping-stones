# Implementation Plan: Design Language (stones and score ring)

**Branch**: `feat/25-design-language` | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-design-language/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

**Primary use case**: `DescribeScore` — given the score the backend sent (or
none), work out what a score ring shows: the number, how full the ring is,
its band (On track, Getting there, Focus here) and the text a screen reader
reads.

Ticket #25 finishes the shared pieces that the TypeScript shell (#31, PR #48)
started. The band rule (85 and up, 60 to 84, under 60) goes in the domain,
once, with tests at 59, 60, 84 and 85. The `describeScore` use case turns a
score into a ring view; `ScoreRing` draws that view and, when asked, shows the
band label and dot, and a new `BandLegend` explains the bands. The stones get
the last two things they lack: a check mark on completed (so all five states
differ without colour, as clarified) and four pebble shapes. The colour tokens
move to the Figma palette, with Bright Amber added for "Getting there".

Clean Architecture path: `domain.ts` (`ScoreBand`, `SCORE_BANDS`,
`scoreBand`; no React) ← `application.ts` (`describeScore`, the primary use
case) ← `components/pieces.tsx` (`ScoreRing`, `BandLabel`, `BandLegend`,
`Stone`, `StoneSprite`, `StatusLegend`: they draw what they are given) ←
`App.tsx` (composition). `domain.ts` and `application.ts` import nothing from
React, Vite, `fetch` or `window`.

## Use Cases

| Use case | Responsibility | Module |
| --- | --- | --- |
| `DescribeScore` (primary) | Turn the score the backend sent (0 to 100, or none) into the ring view: shown text, fill fraction, band and screen-reader text. It must not calculate, round or change the score, render anything, or fetch data. | `frontend/src/application.ts` |

**Out of scope for this plan**: the band sent by the API (only if bands become
coaching judgment, see spec Clarifications), the pages that use the pieces
(#30, #32, #35, #36, #37), and moving `CallsPage.jsx` onto the shared stones.

## Technical Context

**Language/Version**: TypeScript 5.9.3, React 18.3.1, Vite 5.4.11 (from #31)

**Primary Dependencies**: Tailwind CSS 4.3.5 (`@theme` colour tokens),
shadcn/ui helpers already present (`cn`). No new dependency.

**Storage**: N/A. No backend or database change.

**Testing**: Vitest 2.1.9 + jsdom + `@testing-library/react` (`npm test`);
`tsc --noEmit` strict (`npm run lint`).

**Target Platform**: Browser, Vite dev server in Docker Compose
(http://localhost:5173).

**Project Type**: Web application, frontend change only.

**Performance Goals**: N/A (static SVG pieces).

**Constraints**: The score is never computed in the frontend (Principle I);
the band is a display rule over the given score (spec Clarifications). Colours
only from the Figma palette and tints of it. Marks visible at 12 px. ≤ 6 tasks.

**Scale/Scope**: 1 use case, 1 domain rule, 5 stone states × 4 pebble shapes,
2 new display pieces (`BandLabel`, `BandLegend`), 1 extended piece
(`ScoreRing`).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Before research | After design |
| --- | --- | --- |
| I. Server owns the judgment | Pass, with a note: the band is chosen in the frontend. It names the range of the score the backend sent and never computes or changes it (spec Clarifications, Q2). | Pass. `describeScore` passes the score through unchanged; `scoreBand` only compares it with two edges ([research.md](research.md) R1). Stone status still comes from the API. |
| II. Asynchronous API | Pass. No backend change. | Pass. |
| III. Asynchronous persistence | Pass. No schema change, no migration. | Pass. |
| IV. Typed component UI | Pass. All changes in `.ts`/`.tsx`, Tailwind tokens, shadcn helpers. | Pass. No `.jsx` edited ([research.md](research.md) R7). |
| V. One stack | Pass. npm only, no new package. | Pass. |
| VI. Unit test every new function | Pass. `scoreBand`, `describeScore`, `BandLabel`, `BandLegend` get new tests; changed `Stone`, `StoneSprite` and `ScoreRing` get updated tests. | Pass. Test files listed below; the edge scores are in the domain test. |
| VII. Clean Architecture | Pass. One use case, a domain rule, display pieces. | Pass. `domain.ts` ← `application.ts` ← `components/` ← `App.tsx`; pieces draw a `ScoreView` and decide nothing. |

No gate failed. Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/003-design-language/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── ui-pieces.md
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
frontend/src/
├── domain.ts                  # + ScoreBand, SCORE_BANDS, scoreBand (the band rule)
├── domain.test.ts             # new: edge scores 59, 60, 84, 85, 0, 100, fractions, none
├── application.ts             # + ScoreView, describeScore (primary use case)
├── application.test.ts        # + describeScore tests
├── components/pieces.tsx      # StoneSprite: + check, 4 pebble shapes; Stone: + variant;
│                              # ScoreRing: draws a ScoreView, optional band; + BandLabel, BandLegend
├── components/pieces.test.tsx # + tests for the new and changed pieces
├── index.css                  # colour tokens moved to the Figma palette, + amber
└── App.tsx                    # call detail placeholder shows a banded ring and the band legend
```

**Structure Decision**: Same file-per-layer layout as #31: domain rule in
`domain.ts`, use case in `application.ts`, drawing in `components/pieces.tsx`,
composition in `App.tsx`. Tests sit beside their module. `CallsPage.jsx`,
`api.js` and `styles.css` are not edited (R7).

## Complexity Tracking

Empty: no constitution gate needed a justified exception.
