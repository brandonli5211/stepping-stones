# Data Model: Evaluate Ordered Call Steps

## Inputs

| Entity | Required information | Validation |
| --- | --- | --- |
| Analysis selection | All calls, one call type, or one numeric call ID | Exactly one selection mode; unknown IDs are reported without partial save. |
| Evaluated call | Call identity, procedure rules, ordered turns, stored logged actions, and existing steps | Procedure and steps must exist; turns must identify speakers and indexes. |
| Procedure step | Key, position, points, completion requirements, logged-action requirements, example phrase | Processed only in procedure order. |
| Model observation | Current step observation, confidence, quoted turn, extracted facts, coaching, and summary | Choice must be recognized; quote must occur word-for-word in cited stored turn. |

## State transitions

| Starting condition | Observation | Saved state |
| --- | --- | --- |
| Current expected step | Confident, non-contradictory, verified observation with matching required actions | `completed`, evidence saved, continue to next step |
| Current expected step | Confident observation with mismatching logged actions | `wrong`, comparison/detail/coaching saved |
| Current expected step | Low confidence, contradiction, refusal, malformed output, or invalid quote | `under_review`, review evidence/points saved; never also `missed` |
| Ended call, later unevaluated step | No supporting observation | `missed`, with the procedure-defined loss/detail |

## Persisted result

The existing `CallStep` record holds status, severity, lost/review points, detail, evidence turn/quote, coaching, sub-check outcomes, and comparisons. `Call` holds model, prompt version, analysis time, aggregate counts, points, score, and overall status. The persistence adapter updates both inside one transaction.

## Output

`EvaluationOutputData` contains the call ID, number of completed/wrong/missed/under-review steps, whether the save succeeded, and human-readable problems for calls that could not be analyzed. The command presenter formats it for the terminal; existing GET endpoints continue presenting persisted data to the UI.
