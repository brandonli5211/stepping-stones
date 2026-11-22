# Contract: Step panel view

The page reads this from the ready state. It does not read the API body.

## Step row

- `key`, `name`
- `status`: the stored status, drawn with that stone. Under review is not drawn as completed.
- `statusLabel`: Completed, Missed, Wrong, or Under review
- `pointsText`: `−N points` or `−1 point` for a missed or wrong step, otherwise empty. An under-review step shows its status label, not a deduction.

## Step panel

- `name`, `description` (nullable), `reason` (the stored short reason, nullable), `statusLabel`
- `worthText`: `Worth N points`
- `lostText`: nullable, same wording as the row. Empty unless the step is missed or wrong.
- `reviewText`: `N points under review` when the step still has points pending, otherwise null
- `severityLabel`: Critical, Mistake, Inaccuracy, Slip, or null when none
- `subChecks[]`: `description`, `resultLabel` (Passed, Failed, Under review), `pointsText`. `pointsText` is a deduction only when the result is failed, so an under-review sub-check keeps the words "Under review".
- `evidence`: `{ quote, timeText }` or null. `timeText` uses the existing minute:second format.
- `coaching`: the stored sentence, or null
- `comparison`: field rows, or null. Each row has `label`, `callerAsked`, `logged`, `resultLabel` (Match, Doesn't match, Reversed). Shown only for a missed or wrong step on a transfer call.

## Procedure link

`/procedures?task=` plus the call type when the type is a lowercase procedure key. Otherwise `/procedures`.

## Default step

The first step in order whose status is `missed` or `wrong`. If there is none, the first step. If there are no steps, no selection.
