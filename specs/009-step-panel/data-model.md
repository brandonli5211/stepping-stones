# Data model: Call detail step panel

These are the values the call page keeps after mapping `GET /calls/{id}`. Names here are the application's names. The response still uses snake_case.

## Step

| Field | Meaning |
| --- | --- |
| key | Stable step key |
| position | Order on the checklist |
| name | Label shown in the list |
| status | `completed`, `missed`, `wrong`, or `under_review` |
| severity | Existing severity union, including `none` |
| points | Points the step is worth |
| pointsLost | Points lost on this step |
| pointsUnderReview | Points not yet decided |
| description | What the procedure asked for |
| detail | Optional short reason |
| subChecks | Zero or more sub-checks |
| evidence | Quote, turn index, start seconds, or null |
| coaching | Stored sentence, or null |

A step whose status is not one of the four words is not mapped.

## SubCheck

`key`, `description`, `points`, and `result` (`passed`, `failed`, `under_review`). A sub-check with another result is dropped.

## FieldRow

`field`, `label`, `callerAsked`, `logged`, `result` (`match`, `mismatch`, `reversed`). Only present when `type_details.type` is `transfer_money`. A row with another result is dropped.

## TypeDetails

`type` plus `fields`. A non-transfer type has an empty field list.

## CallDetail

Gains `callType` (the procedure key, such as `transfer_money`), `steps`, and `typeDetails`. Everything else is unchanged.

## Selected step

Still view state on the view model, not part of the loaded call. The presenter sets it to the first missed or wrong step key when the current key is not in the loaded steps.
