# Research: Call detail page: transcript, score, flags

No NEEDS CLARIFICATION items were left in the Technical Context. These are the design choices made while planning.

## 1. Module layout

- **Decision**: a `frontend/src/callDetail/` module with the same files as `frontend/src/progress/` (entities, input/output data and boundaries, data access, interactor, api, presenter, view model, controller, compose, page, parts, layering test).
- **Rationale**: Progress is the team's accepted Clean Architecture example on the frontend (constitution VII). Matching it keeps reviews quick and lets the layering test be reused.
- **Alternatives considered**: one component fetching in `useEffect` (breaks VII, logic in the view); a shared generic "screen" abstraction (more code than one more module).

## 2. Telling "not found" apart from "failed"

- **Decision**: `gateway.ts` throws an `ApiError` carrying the HTTP status. `CallDetailApi.getCallDetail` returns `null` on 404 and rethrows everything else. The interactor sends `null` to `prepareNotFoundView`.
- **Rationale**: the spec needs separate not-found and error states (FR-011). Parsing the status out of the current error message would be fragile. `ApiError extends Error`, so Progress and My calls keep working unchanged.
- **Alternatives considered**: matching `"(404)"` in the message (fragile); a separate `getOrNull` gateway method (widens the shell interface for one caller).

## 3. Score band on the ring

- **Decision**: the presenter maps the stored score to its band: 85 to 100 "On track", 60 to 84 "Getting there", under 60 "Focus here", none when there is no score. `ScoreRing` in `components/pieces.tsx` takes the band and colours the ring by it, and the band name is shown as text next to it.
- **Rationale**: the band is display wording for a number the server already gave (constitution I is about step judgement and the score itself). The same ring and thresholds belong to the design language (#25), so the change sits in the shared piece.
- **Alternatives considered**: a `band` field from the API (backend change outside this ticket); colouring without the band name (fails "colour is never the only signal").

## 4. Filler turns

- **Decision**: the presenter hides a turn when, after removing non-speech markers in `[...]` or `<...>`, its text is empty or exactly one of `okay`, `ok`, `and`, `um`, `uh`, `yeah`, `mm hmm`, `mhm` (case-insensitive), and it has no notes. The heading count is the number of turns shown.
- **Rationale**: clarified in the spec (FR-005a). Checked against the demo call: 16 stored turns become the 9 in the Figma frame. A turn with a note is never hidden, so no evidence disappears.
- **Alternatives considered**: hiding in the API (changes a merged contract that #36 and tests rely on); a longer stop-word list (risks hiding real answers like "yes").

## 5. Step selection and scrolling

- **Decision**: the view model holds `selectedStepKey`. `controller.selectStep(key)` sets it. Each turn view lists the step keys of its notes; the page highlights turns whose list contains the selected key and scrolls the first one into view with `scrollIntoView`.
- **Rationale**: selection is page state, not a use case (no data is loaded). Keeping it in the view model lets #36's steps list call the same `selectStep` (FR-010).
- **Alternatives considered**: putting the selection in the URL (useful later for "See procedure" links, not needed now); React context (a second place for state).

## 6. Sample data mode

- **Decision**: `gateway.ts` answers any `/calls/{n}` path in sample mode with the Transfer money example from `docs/api-contract.md`, with turns trimmed to the ones in the frame plus a few filler turns.
- **Rationale**: the other screens work with `VITE_SAMPLE_DATA=true`; this page should too, and the sample doubles as a fixture for page tests.
- **Alternatives considered**: no sample (the page would be the only one that fails in sample mode).

## 7. Long transcripts

- **Decision**: the transcript card scrolls on its own (`max-height` with `overflow-y: auto`), and the header and score panel stay in normal flow above it.
- **Rationale**: SC-005 (200 turns without breaking the layout) and SC-006 (scrolling to a turn) both work inside one scroll container.
- **Alternatives considered**: virtualising the list (unneeded at 200 turns, adds code).
