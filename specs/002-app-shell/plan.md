# Implementation Plan: App Shell and Shared Screen Pieces

**Branch**: `feat/31-app-shell-ts` | **Date**: 2026-11-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-app-shell/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

**Primary use case**: `ResolveShellView` — given the current address and
the configured agent, decide which of the four screens to show, its
parameters, which menu item is marked, and the agent shown in the menu.

Rebuild ticket #31 to the constitution: the frontend moves to TypeScript,
Tailwind CSS and shadcn/ui, with Vitest unit tests and a strict type-check
as lint. Everything is kept to the fewest files and functions. A shell
frame (menu + page area) hosts four screens: My calls (the existing calls
list, unchanged), Call detail, Progress and Procedures (placeholders).
Shared display pieces — stone, status legend, score ring, page header,
card, empty and error state — draw values they are given and decide
nothing. An `ApiGateway` port with HTTP and sample adapters gives later
screens one access point and a one-setting sample mode.

Clean Architecture path: `domain.ts` (step statuses, screens, menu, agent
profile; types and constants, no React) ← `application.ts`
(`resolveShellView` + the `ApiGateway` port) ← `gateway.ts` (adapter:
HTTP or sample responses) ← `components/` and `App.tsx` (React pieces and
composition, reads env and the browser address). `domain.ts` and
`application.ts` import nothing from React, Vite, `fetch` or `window`.

## Use Cases

| Use case | Responsibility | Module |
| --- | --- | --- |
| `ResolveShellView` (primary) | Map an address and agent profile to the screen, its params, the marked menu item and the agent shown; it must not render anything, read `window`, or fetch data. | `frontend/src/application.ts` |

**Out of scope for this plan**: `GetCurrentAgent` (agent from a backend
sign-in endpoint), `GetCallDetail` (call lookup — call detail ticket),
moving `CallsPage.jsx` onto the shared gateway and stones (calls ticket).

## Technical Context

**Language/Version**: TypeScript 5.9.3, React 18.3.1, Vite 5.4.11 (existing)

**Primary Dependencies**: Tailwind CSS 4.3.5 + `@tailwindcss/vite` 4.3.5;
shadcn/ui Card with `clsx` 2.1.1 and `tailwind-merge` 3.7.0. See
[research.md](research.md) R1–R2.

**Storage**: N/A — no database change, no Alembic migration.

**Testing**: Vitest 2.1.9 + jsdom 25.0.1 + `@testing-library/react`
16.3.3 (`npm test`); `tsc --noEmit` strict (`npm run lint`). Research R5.

**Target Platform**: Browser, served by Vite in Docker Compose at
http://localhost:5173.

**Project Type**: Web application (frontend change only).

**Performance Goals**: Screen switch without a page reload; first screen
visible within normal Vite dev load.

**Constraints**: Server owns judgment (no status or score computed in the
frontend, including sample data). No router or component library beyond
shadcn/ui. New source `.ts`/`.tsx` only. ≤ 6 tasks.

**Scale/Scope**: 4 screens, 6 shared display pieces + shadcn Card, 1 use
case, 1 port with 1 adapter function.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Before research | After design |
| --- | --- | --- |
| I. Server owns the judgment | Pass. Shell, stones and ring only display values. | Pass. `StepStatus` is read from the API; `ScoreRing` shows the given value; sample responses store decided scores and labels ([data-model.md](data-model.md)). |
| II. Asynchronous API | Pass. No backend route added or changed. | Pass. |
| III. Asynchronous persistence | Pass. No schema change, so no migration. | Pass. |
| IV. Typed component UI | Pass, with required work: the frontend is JS today. This feature adds TypeScript, Tailwind and shadcn/ui and replaces `App.jsx`/`main.jsx` with `.tsx`. | Pass. Every new file in the layout below is `.ts`/`.tsx`; shared primitives come from shadcn/ui. `CallsPage.jsx` and `api.js` are not edited (R8). |
| V. One stack | Pass. npm only; Compose unchanged in shape. | Pass. No router library (R4). Vitest is test tooling required by Principle VI, not a runtime framework (R5). |
| VI. Unit test every new function | Pass. The use case, the gateway, `cn`, each shared piece and `App` get a test; `domain.ts` has no functions. | Pass. Test files are listed beside each module below. |
| VII. Clean Architecture | Pass. One use case with domain types and a port. | Pass. `domain.ts` and `application.ts` import no React, Vite env, `fetch` or `window`; `gateway.ts` implements the port; components render and dispatch only. |

No gate failed. Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/002-app-shell/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── ui-shell.md
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
frontend/
├── package.json               # + TS, Tailwind, clsx, tailwind-merge, vitest; scripts test, lint
├── tsconfig.json              # strict, allowJs (existing CallsPage.jsx), vite/client + vitest types
├── vite.config.ts             # replaces vite.config.js; react + tailwind plugins; vitest jsdom
├── index.html                 # entry → /src/main.tsx
└── src/
    ├── domain.ts              # types + STATUS_LABELS, SCREENS, MENU (no functions)
    ├── application.ts         # resolveShellView (primary use case) + ApiGateway port
    ├── application.test.ts
    ├── gateway.ts             # createApiGateway: fetch or sample responses
    ├── gateway.test.ts
    ├── lib/utils.ts           # shadcn cn()
    ├── components/ui/card.tsx # shadcn Card
    ├── components/pieces.tsx  # StoneSprite, Stone, StatusLegend, ScoreRing, PageHeader, StateMessage
    ├── components/pieces.test.tsx  # also covers cn and Card
    ├── App.tsx                # shell + screens + address state (replaces App.jsx)
    ├── App.test.tsx
    ├── main.tsx               # replaces main.jsx
    ├── index.css              # tailwind + color tokens
    ├── CallsPage.jsx          # existing, not edited
    ├── api.js                 # existing, not edited (used by CallsPage)
    └── styles.css             # existing, not edited, still loaded for CallsPage
docker-compose.yml             # pass VITE_SAMPLE_DATA, VITE_AGENT_NAME, VITE_AGENT_ROLE
.env.example, README.md        # document the three settings
```

**Structure Decision**: Keep `backend/` untouched. Inside `frontend/src/`
the layers are files, not folders: `domain.ts` ← `application.ts` ←
`gateway.ts` ← `components/` + `App.tsx`/`main.tsx`. Tests sit beside the
module they test. `App.jsx`, `main.jsx` and `vite.config.js` are removed
because their replacements are rewrites. The existing calls page files
stay as they are (R8).

## Complexity Tracking

No constitution violations require justification.

## Phase 0 and Phase 1 outputs

Research: [research.md](research.md). Design: [data-model.md](data-model.md),
[contracts/ui-shell.md](contracts/ui-shell.md), [quickstart.md](quickstart.md).

Post-design constitution check: all seven gates still pass. The Use Cases
section is unchanged after Phase 1: one primary use case,
`ResolveShellView`, at `frontend/src/application.ts`.
