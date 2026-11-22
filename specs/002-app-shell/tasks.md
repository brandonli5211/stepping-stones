---

description: "Task list for the app shell and shared screen pieces"
---

# Tasks: App Shell and Shared Screen Pieces

**Input**: Design documents from `/specs/002-app-shell/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ui-shell.md, quickstart.md

**Tests**: Unit tests sit inside each task (constitution VI). Every new function gets a test that calls it and checks its result.

**Organization**: One Clean Architecture use case, `ResolveShellView`. Six tasks.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: `[US1]` for the single use-case slice
- Exact file paths in every task

## Path Conventions

- Frontend layers are files: `frontend/src/domain.ts` ← `frontend/src/application.ts` ← `frontend/src/gateway.ts` ← `frontend/src/components/` + `frontend/src/App.tsx`
- No backend change, no migration

## Use Case: ResolveShellView (from plan.md Summary)

**Goal**: Every screen opens inside one shell; the address decides the screen and the marked menu item; the agent shows in the menu; shared pieces and a one-setting sample mode are ready for later screens.

**Independent Test**: `npm test` and `npm run lint` pass in `frontend/`; `docker compose up --build` serves the shell at http://localhost:5173 and quickstart.md §3–4 pass.

- [X] T001 [US1] Tooling: in `frontend/package.json` add exact-pinned `typescript` 5.9.3, `@types/react` 18.3.31, `@types/react-dom` 18.3.7, `tailwindcss` 4.3.5, `@tailwindcss/vite` 4.3.5, `clsx` 2.1.1, `tailwind-merge` 3.7.0, `vitest` 2.1.9, `jsdom` 25.0.1, `@testing-library/react` 16.3.3, `@testing-library/dom` 10.x; scripts `test` = `vitest run`, `lint` = `tsc --noEmit`. Add `frontend/tsconfig.json` (strict, `allowJs`, `jsx: react-jsx`, types `vite/client` + `vitest/globals`). Replace `frontend/vite.config.js` with `frontend/vite.config.ts` (react + tailwind plugins, `test: { environment: "jsdom", globals: true }`). Point `frontend/index.html` at `/src/main.tsx`. Add `frontend/src/index.css` (`@import "tailwindcss"` + `@theme` colors from research R2). Run `npm install` so `frontend/package-lock.json` updates.
- [X] T002 [US1] Domain + use case: `frontend/src/domain.ts` with `StepStatus`, `STATUS_LABELS`, `Screen`, `SCREENS`, `MenuItem`, `MENU`, `AgentProfile` (types and constants only). `frontend/src/application.ts` with the `ApiGateway` type and `resolveShellView(path, agent)` returning `{ screen, callId, menu, agent }` per data-model.md (unknown path → My calls; `/calls/<id>` → call detail marking My calls; missing name → "Agent"; empty role → null). Test in `frontend/src/application.test.ts`: each of the four addresses, an unknown address, exactly one `current` menu item, the agent defaults. Neither file imports React, Vite env, `fetch` or `window`.
- [X] T003 [P] [US1] Adapter: `frontend/src/gateway.ts` with `createApiGateway({ apiUrl, sampleData, fetchImpl })` implementing `ApiGateway`, plus a `/calls` sample response copied in shape from `backend/app/calls_api.py::list_calls` with literal statuses, scores and result labels. Test in `frontend/src/gateway.test.ts`: sample mode returns the `/calls` sample and never calls `fetchImpl`; sample mode rejects an unknown path; HTTP mode calls `fetchImpl` with `apiUrl + path` and returns the JSON; HTTP mode rejects on a non-OK status.
- [X] T004 [P] [US1] Shared pieces: `frontend/src/lib/utils.ts` (`cn`), `frontend/src/components/ui/card.tsx` (shadcn `Card`, `CardHeader`, `CardTitle`, `CardContent`), and `frontend/src/components/pieces.tsx` with `StoneSprite`, `Stone` (distinct shape per status, text label always present, unknown status drawn as Under review), `StatusLegend`, `ScoreRing` (shows the given value, "–" for null, computes nothing), `PageHeader` (title, subtitle, optional back link) and `StateMessage` (`kind` empty | error, error has `role="alert"`). Test every one of these in `frontend/src/components/pieces.test.tsx`.
- [X] T005 [US1] Composition: `frontend/src/App.tsx` replaces `frontend/src/App.jsx`: reads `VITE_API_URL`, `VITE_SAMPLE_DATA`, `VITE_AGENT_NAME`, `VITE_AGENT_ROLE`; keeps the path in state with `popstate` + `history.pushState`; calls `resolveShellView`; renders the sprite, the menu (`aria-current="page"` on the marked item), the agent, and the screen — My calls renders the existing `frontend/src/CallsPage.jsx` unchanged; Call detail, Progress and Procedures are placeholders built from the shared pieces; Progress loads `/calls` through `createApiGateway` and shows `summary.this_week` in a `ScoreRing` (the server's numbers, nothing computed), or a `StateMessage` error if it fails. `frontend/src/main.tsx` replaces `frontend/src/main.jsx` and loads `index.css` and the existing `styles.css`. Test in `frontend/src/App.test.tsx`: menu click switches screen and marked item, `/calls/7` shows "Call 7" with My calls marked, unknown path shows My calls, agent name shows.
- [X] T006 [US1] Wiring and validation: in `docker-compose.yml` pass `VITE_SAMPLE_DATA`, `VITE_AGENT_NAME` and `VITE_AGENT_ROLE` to the frontend with defaults; document the three settings in `.env.example` and the README frontend section. Run quickstart.md §1–4 and fix failures in the files above.

**Checkpoint**: `ResolveShellView` drives the shell through the layers; `domain.ts` and `application.ts` import nothing from React, Vite, `fetch` or `window`; no screen computes a status or score.

---

## Dependencies & Execution Order

1. T001 (tooling) first
2. T002 (domain + use case) before T005
3. T003 and T004 after T001, in parallel with each other
4. T005 after T002–T004
5. T006 last

## Implementation Strategy

1. T001 → T006 in order (T003/T004 can swap)
2. Stop when the independent test passes
3. A signed-in agent, call lookup and moving `CallsPage.jsx` onto the shared pieces are later features, not more rows here

## Notes

- Six tasks, the hard ceiling
- Keep files and functions to the minimum listed above
- Code comments, where needed, are lowercase and casual
