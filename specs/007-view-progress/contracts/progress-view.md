# Contract: the Progress view model

This is the contract between the presenter and the page. `ProgressPage` renders exactly this and computes nothing from it.

The server contract it is built from is [feature 006's `GET /progress`](../../006-get-progress/contracts/get-progress.md).

## States

```ts
type ProgressViewState =
  | { kind: "loading"; message: string }
  | { kind: "error"; title: string; message: string }
  | { kind: "empty"; showDemoBadge: boolean; message: string }
  | ProgressReadyState;

type ProgressReadyState = {
  kind: "ready";
  showDemoBadge: boolean;
  weeks: WeekBarView[];            // always 8, oldest first
  thisWeekText: string;            // "53 of 59 required steps completed"
  comparison: string | null;       // the server's line, unchanged
  callTypes: CallTypeBarView[];    // the server's order
  firstSteps: StepRowView[];       // the first FIRST_STEP_ROWS rows
  allSteps: StepRowView[];         // every row, the server's order
  showAllLabel: string | null;     // "Show all 26 steps"; null when nothing more to show
  showFewerLabel: string;          // "Show fewer"
};

type WeekBarView = { label: string; percentText: string; height: number; isCurrent: boolean; currentText: string | null };
type CallTypeBarView = { key: string; name: string; percentText: string; stepsText: string; width: number };
type StepRowView = { key: string; name: string; label: string; stones: { status: string }[]; summary: string };
```

`height` and `width` are whole numbers from 0 to 100, used as CSS percentages.

## What the page shows for each state

| State | On screen |
| --- | --- |
| `loading` | the title and `message` |
| `error` | the title and an alert with `title` and `message`; no chart |
| `empty` | the title, the badge when `showDemoBadge`, and `message` |
| `ready` | the title, the badge when `showDemoBadge`, a card with the week chart, `thisWeekText` and `comparison` when present, a "By call type" card, a "Steps you skip most" card with `firstSteps` or `allSteps`, the show-all control when `showAllLabel` is not `null`, and the legend |

## With the demo data (2026-10-09)

- `showDemoBadge`: `true`
- `weeks`: labels `Aug 17, Aug 24, Aug 31, Sep 7, Sep 14, Sep 21, Sep 28, Oct 5`; texts `64%, 70%, 68%, 75%, 80%, 79%, 86%, 90%`; only the last is current
- `thisWeekText`: `53 of 59 required steps completed`; `comparison`: `Up from 64% in week 1`
- `callTypes`: Check balance 88%, Get branch hours 86%, Order checks 85%, Reset password 80%, Pay bill 79%, Schedule appointment 77%, Replace card 73%, Transfer money 69%
- `firstSteps`: Confirm replacement, Confirm appointment, Offer further help, State account balance, Collect company address
- `allSteps`: 26 rows; `showAllLabel`: `Show all 26 steps`
