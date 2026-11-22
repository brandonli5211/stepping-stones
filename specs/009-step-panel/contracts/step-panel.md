# Contract: Step panel view

The page reads this from the ready state. It does not read the API body.

## Step row

- `key`, `name`
- `statusLabel`: Completed, Missed, Wrong, or Under review
- `pointsText`: `−N points`, `−1 point`, or empty when nothing was lost
- `failed`: true when the status is missed or wrong

## Step panel

- `name`, `description` (nullable), `reason` (the stored short reason, nullable), `statusLabel`
- `worthText`: `Worth N points`
- `lostText`: nullable, same wording as the row
- `severityLabel`: Critical, Mistake, Inaccuracy, Slip, or null when none
- `subChecks[]`: `description`, `resultLabel` (Passed, Failed, Under review), `pointsText`
- `evidence`: `{ quote, timeText }` or null. `timeText` uses the existing minute:second format.
- `coaching`: the stored sentence, or null
- `comparison`: field rows, or null. Each row has `label`, `callerAsked`, `logged`, `resultLabel` (Match, Doesn't match, Reversed). Shown only for a missed or wrong step on a transfer call.

## Procedure link

`/procedures?task=` plus the call type when the type is a lowercase procedure key. Otherwise `/procedures`.

## Default step

The first step in order whose status is `missed` or `wrong`. If there is none, the first step. If there are no steps, no selection.
