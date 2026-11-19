# Contract: shared design pieces

What other tickets (#30, #32, #35, #36, #37) can rely on. All pieces draw what
they are given and decide nothing; the score always comes from the backend.

## `describeScore(score)` (`frontend/src/application.ts`)

```ts
describeScore(score: number | null): ScoreView
```

| Input | `text` | `fill` | `band` | `bandLabel` | `ariaLabel` |
| --- | --- | --- | --- | --- | --- |
| `45` | `"45"` | `0.45` | `focus_here` | Focus here | Score 45 of 100, Focus here |
| `59` | `"59"` | `0.59` | `focus_here` | Focus here | … |
| `60` | `"60"` | `0.6` | `getting_there` | Getting there | … |
| `84` | `"84"` | `0.84` | `getting_there` | Getting there | … |
| `85` | `"85"` | `0.85` | `on_track` | On track | … |
| `null` | `"–"` | `0` | `null` | `null` | No score yet |

## Components (`frontend/src/components/pieces.tsx`)

| Piece | Props | Draws |
| --- | --- | --- |
| `StoneSprite` | none | Once per page: the four pebble shapes and the check, crack and X marks. |
| `Stone` | `status: string`, `label?`, `size?` (default 26), `showLabel?`, `variant?: number` (new, default 0) | One stone. Unknown status → Under review. Screen readers read `label` or the state name. |
| `StatusLegend` | none | Completed, Missed, Wrong, Under review, with names. |
| `ScoreRing` | `value: number \| null`, `size?` (default 88), `showBand?` (new, default false) | Without `showBand`: as before (`75%`). With it: "45 / of 100" in the ring and a `BandLabel` beside it; reads `ariaLabel`. |
| `BandLabel` (new) | `band: ScoreBand \| null` | Coloured dot + label; nothing when `null`. |
| `BandLegend` (new) | none | "On track 85 to 100 · Getting there 60 to 84 · Focus here under 60", each with its dot. |

## Usage

```tsx
<StoneSprite />                                  // once, in the shell
{steps.map((s, i) => <Stone key={s.key} status={s.status} label={s.name} variant={i} />)}
<ScoreRing value={detail.score.score} showBand />
<BandLegend />
```
