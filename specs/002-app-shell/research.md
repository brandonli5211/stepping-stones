# Research: App Shell and Shared Screen Pieces

Phase 0 for [plan.md](plan.md). Each entry records a decision, why, and what
else was considered.

## R1. Frontend language and build

- **Decision**: TypeScript 5.9.3 on the existing Vite 5.4.11 and React
  18.3.1. New source is `.ts` / `.tsx`. `App.jsx` and `main.jsx` are
  replaced by `App.tsx` and `main.tsx` because this feature rewrites them.
- **Rationale**: Constitution Principle IV forbids new `.js`/`.jsx` and
  requires TypeScript. Staying on Vite 5 and React 18 avoids a framework
  upgrade inside a UI ticket.
- **Alternatives considered**: TypeScript 7 (native compiler) — too new for
  the lint tooling below, which supports `<6.0.0`. Upgrading Vite/React —
  out of scope and not required by the constitution.

## R2. Styling and components

- **Decision**: Tailwind CSS 4.3.5 through `@tailwindcss/vite` 4.3.5
  (peer `vite ^5.2.0`). shadcn/ui's Card, copied into
  `src/components/ui/card.tsx` with its `cn` helper (`clsx` 2.1.1 +
  `tailwind-merge` 3.7.0). Nothing else from shadcn is needed yet, so no
  `components.json`, `class-variance-authority` or Radix packages. Colors
  reuse the team's existing values from `src/styles.css` (teal `#3d6b7a`,
  page `#f5fbf6`, green `#2fbf6a`, red `#c0392b`) as Tailwind `@theme`
  tokens in `src/index.css`, so the shell matches the calls page.
- **Rationale**: Principle IV names Tailwind and shadcn/ui. Tailwind 4's
  Vite plugin needs no PostCSS config. shadcn copies component source into
  the repo, so the team owns it.
- **Alternatives considered**: Tailwind 3 with PostCSS — more config files
  for no gain. A different component library — forbidden by Principle V.

## R3. Stone artwork

- **Decision**: One inline SVG `<symbol>` sprite for the pebble shape, the
  crack and the "wrong" mark, rendered once by the shell. Every stone and
  the logo draw it with `<use>`. Each status sets fill/stroke through
  Tailwind classes, and every stone carries a text label (visible or
  screen-reader only).
- **Rationale**: Matches Figma "Foundations / Stone states" (shape carries
  meaning, not only color). One source image reused everywhere, as the
  ticket owner asked in the first version.
- **Alternatives considered**: Image files per status — duplicates the
  artwork. CSS border-radius blobs (as in `CallsPage.jsx`) — cannot draw a
  crack or a mark, so color would carry the meaning.

## R4. Navigation without a router library

- **Decision**: Address → screen resolution is a pure function in the
  application layer (`resolveShellView`). `App.tsx` keeps the current path
  in state, listens to `popstate`, and pushes history entries on menu
  clicks. No router dependency and no separate hook file.
- **Rationale**: Principle V forbids adding a framework without an
  amendment. Four fixed screens do not need one. Keeping resolution pure
  satisfies FR-017 and Principle VII: it is tested without React.
- **Alternatives considered**: `react-router` — a new framework dependency
  needing an amendment; heavier than four routes need.

## R5. Unit tests and lint for the frontend

- **Decision**: Vitest 2.1.9 (the last line that supports Vite 5),
  `jsdom` 25.0.1, `@testing-library/react` 16.3.3 with
  `@testing-library/dom` 10. `npm run lint` runs the TypeScript compiler in
  check mode (`tsc --noEmit`, strict). Scripts: `npm test` and
  `npm run lint`.
- **Rationale**: Principle VI requires a unit test for every new frontend
  function, so the frontend needs a runner; Vitest reuses the Vite config.
  The onboarding guide runs `npm run lint` and `npm test`. These are test
  and lint tools, not application frameworks, so they do not change the
  stack Principle V protects.
- **Alternatives considered**: Jest — needs its own TypeScript transform
  and config. Vitest 3+ — requires Vite 6. ESLint — five more packages and
  a config file; strict type-checking already catches the errors that
  matter here, and ESLint can be added later without code changes.

## R6. Sample data mode

- **Decision**: An `ApiGateway` port (type in `application.ts`) and one
  adapter function, `createApiGateway` in `gateway.ts`: with sample mode on
  it answers from canned responses keyed by path; otherwise it calls
  `fetch` against `VITE_API_URL`.
  Sample responses copy the real `/calls` response shape, with statuses,
  scores and result labels already decided.
- **Rationale**: FR-011/FR-012. Principle I: example data stores the
  server's answers; the screen never derives a status or score. The port
  keeps screens independent of which adapter is active.
- **Alternatives considered**: Falling back to sample data when the API
  returns 404 (first version) — hides real failures and mixes two sources
  silently. A mock server — another process to run.

## R7. Agent shown in the menu

- **Decision**: `App.tsx` reads `VITE_AGENT_NAME` and `VITE_AGENT_ROLE`;
  `resolveShellView` falls back to "Agent" when the name is missing.
- **Rationale**: User chose one use case for this ticket; the backend has
  no agent or sign-in endpoint. A later feature can swap the source
  through the same `AgentProfile` type.
- **Alternatives considered**: A backend `GET /api/me` use case — a second
  use case, deferred to its own spec.

## R8. Existing calls page

- **Decision**: My calls renders the existing `CallsPage.jsx` unchanged,
  with the existing `styles.css` still imported for it.
- **Rationale**: Governance requires bringing a file into compliance only
  when a change edits it. Editing it belongs to its own ticket, and the
  task budget (≤6) cannot absorb a rewrite.
- **Alternatives considered**: Converting it to TSX on the shared pieces —
  wider scope, overlaps the calls ticket, and breaks the 6-task limit.

## R9. Docker

- **Decision**: Keep the frontend Dockerfile. Commit
  `frontend/package-lock.json` updated by npm; Compose passes
  `VITE_SAMPLE_DATA`, `VITE_AGENT_NAME` and `VITE_AGENT_ROLE` through with
  defaults.
- **Rationale**: FR-015 and Principle V: Compose still starts all three
  services; npm stays the only JavaScript installer.
