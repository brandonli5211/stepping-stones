# Phase 1 Data Model: Design Language

**Feature**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md) · **Date**: 2026-11-18

Frontend only. No backend, schema or migration change.

## Domain (`frontend/src/domain.ts`)

- **StepStatus** (existing): `"completed" | "missed" | "wrong" |
  "under_review" | "procedure"`, with `STATUS_LABELS`.
- **ScoreBand** (new): `"on_track" | "getting_there" | "focus_here"`.
- **SCORE_BANDS** (new, constant, highest first):

  | key | label | from | colour token |
  | --- | --- | --- | --- |
  | `on_track` | On track | 85 | `good` (#0CCE6B) |
  | `getting_there` | Getting there | 60 | `amber` (#F1C40F) |
  | `focus_here` | Focus here | below 60 | `bad` (#E65F5C) |

  The legend text comes from this table: "On track 85 to 100 · Getting there
  60 to 84 · Focus here under 60".

- **scoreBand(score: number | null) → ScoreBand | null** (new): `null` for no
  score; else the first band whose `from` the score reaches (R2).

## Application (`frontend/src/application.ts`)

- **ScoreView** (new): what one ring draws.
  - `value: number | null`: the score exactly as given
  - `text: string`: `"45"`, or `"–"` when there is no score
  - `fill: number`: 0 to 1, the score / 100 clamped (0 when none)
  - `band: ScoreBand | null`
  - `bandLabel: string | null`: "Focus here", …
  - `ariaLabel: string`: "Score 45 of 100, Focus here", or "No score yet"
- **describeScore(score: number | null) → ScoreView** (new, primary use case).

## Display pieces (`frontend/src/components/pieces.tsx`)

- **Stone look** per state (shape or mark first, colour second):

  | state | face | mark |
  | --- | --- | --- |
  | completed | solid `good` | check (new) |
  | missed | soft `bad` fill, `bad` outline | crack |
  | wrong | solid `bad` | white X |
  | under review | no fill, dashed `review` outline | none |
  | procedure | solid `brand` | none (the only plain stone) |

- **Pebble variant**: 0–3, taken as `variant mod 4`, default 0.

No state transitions: the pieces hold no state.
