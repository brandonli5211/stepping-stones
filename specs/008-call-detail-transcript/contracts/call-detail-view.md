# UI contract: Call detail page (transcript, score, flags)

**Consumes**: `GET /calls/{id}`, as documented in [docs/api-contract.md](../../../docs/api-contract.md). This feature adds no endpoint and changes no response.

## Route

| Path | Shows |
| --- | --- |
| `/calls/{id}` with `id` a positive whole number | the call detail page for that call |
| `/calls/{anything else}` | the not-found state (no request is sent) |

## What the page promises

| Area | Shows | Never |
| --- | --- | --- |
| Header | "Back to my calls" link to `/`, `call_type_name` as the title, `external_id` as the reference | invents a title |
| Score panel | `score` in the ring with its band name, "`steps_done_right` of `steps_total` steps done right", "`critical_count` critical, `points_lost` points lost" (critical part left out when 0; whole line left out when nothing is lost), "so far" and points under review when `provisional`, `summary` when not null; "Not scored yet" when `score` is null | recomputes any number |
| Transcript | turns in `idx` order without filler turns, each with Agent/Customer, `m:ss` from `start_seconds` (left out when null), the text, and every note as a label with an icon; count "`N` turns, verbatim"; "Transcript not available" when nothing is left to show | hides a turn that has a note |
| Flags | count per severity ("1 critical"), one card per flag with `step_name`, "−`points_lost` points", `message`; "Nothing to fix on this call" when `flags` is empty | creates or reorders flags |
| Selection | choosing a flag card selects its `step_key`; the first turn with a note for that step scrolls into view and every such turn is highlighted | changes data |

## Hand-off to #36

`controller.selectStep(stepKey: string | null)` and `viewModel.selectedStepKey` are the shared selection. The steps list in #36 calls the same method; nothing in this page changes when it does.
