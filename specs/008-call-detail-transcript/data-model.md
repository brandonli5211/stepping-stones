# Data Model: Call detail page: transcript, score, flags

All of this is frontend state. Nothing is stored. Source: `GET /calls/{id}` ([contract](../../docs/api-contract.md)). Only the parts this ticket draws are mapped; `steps` and `type_details` are left for #36.

## Entities (application layer, `callDetail/entities.ts`)

| Entity | Fields | From the API |
| --- | --- | --- |
| `CallDetail` | `callId: number`, `externalId: string`, `callTypeName: string`, `summary: string \| null`, `score: Score`, `turns: Turn[]`, `flags: Flag[]` | `header`, `score`, `transcript`, `flags` |
| `Score` | `score: number \| null`, `outOf: number`, `stepsDoneRight: number`, `stepsTotal: number`, `pointsLost: number`, `criticalCount: number`, `pointsUnderReview: number`, `provisional: boolean` | `score` |
| `Turn` | `idx: number`, `speaker: "agent" \| "caller"`, `startSeconds: number \| null`, `text: string`, `notes: Note[]` | `transcript[]` |
| `Note` | `kind: "evidence" \| "wrong"`, `stepKey: string`, `text: string` | `transcript[].notes[]` |
| `Flag` | `stepKey: string`, `stepName: string`, `status: "missed" \| "wrong"`, `severity: Severity`, `pointsLost: number`, `message: string \| null` | `flags[]` |

`Severity` is `"none" | "slip" | "inaccuracy" | "mistake" | "critical"`, as the API sends it.

Validation: none beyond the types; the API is the source of truth (constitution I). An unknown `speaker` or note `kind` is passed through by the API mapper only if it is one of the listed values; anything else is dropped from notes and shown as a plain turn.

## View state (adapter layer, `callDetail/viewModel.ts`)

```text
CallDetailViewState
├── { kind: "loading", message }
├── { kind: "error", title, message }            # retry calls controller.load() again
├── { kind: "notFound", title, backHref: "/" }
└── { kind: "ready",
      header:  { title, reference, backHref: "/", backLabel: "Back to my calls" },
      score:   { value | null, outOfText ("of 100"), band: "on_track" | "getting_there" | "focus_here" | null, bandLabel,
                 stepsText ("6 of 7 steps done right", "… so far" when provisional), lostText ("1 critical, 55 points lost" | null),
                 reviewText ("10 points under review" | null), provisional, summary | null },
      transcript: { countText ("9 turns, verbatim"), empty: boolean,
                    turns: [{ idx, speakerLabel ("Agent" | "Customer"), timeText ("0:33" | null),
                              text, tone ("plain" | "evidence" | "wrong"),
                              labels: [{ kind, text }], stepKeys: string[] }] },
      flags: { countText ("1 critical" | null), empty: boolean,
               cards: [{ stepKey, title, pointsText ("−55 points"), message | null, severity }] } }

selectedStepKey: string | null      # separate from the state, survives re-renders
```

`tone` is `wrong` when any note is wrong, else `evidence` when any note is evidence, else `plain`. Labels keep the API's text in the API's order.

## State transitions

```text
(start) ──load()──▶ loading ──200──▶ ready
                         ├──404──▶ notFound
                         └──other error──▶ error ──retry (load())──▶ loading
ready: selectStep(key) sets selectedStepKey; selectStep(null) clears it
```

A newer `load()` drops the answer of an older one (same guard as Progress).
