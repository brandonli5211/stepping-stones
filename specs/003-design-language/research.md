# Phase 0 Research: Design Language

**Feature**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md) · **Date**: 2026-11-18

No open NEEDS CLARIFICATION: both spec questions were settled in the spec's
Clarifications (check mark on completed; band as a frontend display rule).

## R1. Where the band rule lives (Principle I)

- **Decision**: `scoreBand(score)` in `domain.ts`, used only by the
  `describeScore` use case. Components never compare scores themselves.
- **Rationale**: Principle I forbids deciding step results and computing the
  score. The band neither changes nor derives the score; it names the range of
  the number the backend sent, like picking a colour for a status. Keeping the
  edges in one domain function, with tests, means no page can draw its own
  bands, and moving the decision to the API later only replaces this one
  function with a value read from the response.
- **Alternatives**: the API sends the band (strictest, but changes #30 and
  #34; deferred unless bands become coaching judgment); edges inside
  `ScoreRing` (rejected: a rule hidden in a component, against Principle VII).

## R2. Band edges and odd values

- **Decision**: `score >= 85` On track, `score >= 60` Getting there, otherwise
  Focus here; `null` gives no band. Fractions are compared as they are (84.5
  is Getting there). Values below 0 or above 100 are banded as they compare
  (Focus here, On track) and the ring's fill is clamped to 0–1; the number
  shown is never changed.
- **Rationale**: matches the ticket ("85 to 100", "60 to 84", "under 60") and
  needs no rounding, which would change the score.
- **Alternatives**: rounding first (rejected: changes the score); rejecting
  out-of-range values (rejected: one bad value should not break a page).

## R3. The check mark on completed

- **Decision**: a new sprite symbol `stone-check`, a short thin tick in the
  middle of the stone, stroked in the ink colour at reduced opacity so it is
  quiet but still clear.
- **Rationale**: the ticket needs five shapes; Figma's completed stone is
  plain (clarified: deliberate change, named in the PR). A white tick on
  #0CCE6B has about 2:1 contrast, under the 3:1 that WCAG 1.4.11 asks of
  graphics; dark ink passes easily.
- **Alternatives**: white tick (too faint); a mark on the procedure stone
  instead (rejected in the clarification).

## R4. Four pebble shapes

- **Decision**: `StoneSprite` defines four outline symbols (`stone-0` to
  `stone-3`), traced from the Figma Stone component. `Stone` takes an
  optional `variant` number (default 0) and uses `variant mod 4`; a row passes
  each stone's index, so the same stone in the same place always looks the
  same. Marks (check, crack, X) sit in the centre and fit all four shapes.
- **Rationale**: deterministic, no randomness in rendering or tests, and one
  number for callers to pass.
- **Alternatives**: random shape per render (rejected: flickers and breaks
  snapshot-free tests); a hash of the step key (more code for the same result).

## R5. Palette tokens

- **Decision**: in `index.css` `@theme`: `brand` #3C7A89, `page` #F7FFF6,
  `ink` #272727, `good` #0CCE6B, `bad` #E65F5C, new `amber` #F1C40F. Keep the
  soft tints (`brand-soft`, `bad-soft`, `review`, `muted`) but derive them from
  the palette colours.
- **Rationale**: FR-011 asks for the Figma palette; the current tokens are
  close but not equal (for example brand #3d6b7a, good #2fbf6a, bad #c0392b).
  Changing the tokens updates every Tailwind piece at once.
- **Alternatives**: new token names beside the old ones (rejected: two
  palettes in one app).

## R6. Which rings show a band

- **Decision**: `ScoreRing` shows the band only when given `showBand`; it then
  shows "45 of 100" style text with `BandLabel` beside it. Without it, the
  ring draws as today.
- **Rationale**: the shell also uses the ring for the week's step completion
  (a percentage, not a call score), where a score band would be wrong.
- **Alternatives**: a separate banded ring component (rejected: two rings to
  keep in step).

## R7. Files left alone

- **Decision**: `CallsPage.jsx`, `api.js` and `styles.css` are not edited.
- **Rationale**: same rule as #31; the calls page has its own older stone and
  moves to the shared pieces in the calls ticket (#30). Constitution IV
  forbids new `.jsx` work.
