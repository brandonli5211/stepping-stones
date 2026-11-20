# Contract change: `apply-demo-results` command

This extends [feature 002's contract](../../002-apply-demo-results/contracts/apply-demo-results-command.md). The invocation, arguments, output format and exit codes are unchanged.

## Input file: three optional columns

| Column | Meaning | Example (`HVB-DEMO-06`) |
| --- | --- | --- |
| `evidence_step` | step key the evidence supports; must be in this row's `missed_steps` or `wrong_steps` | `submit_and_confirm_transfer` |
| `evidence_turn` | stored turn number of this call (from 1) | `9` |
| `evidence_quote` | words that appear exactly in that turn | `okay and that was from your savings to your checking account` |

The three values on a row must be either all empty or all filled in. A file without these columns is valid and behaves as before.

## New problem messages

These are added to the existing list. The format stays `"<demo_id>: <problem>"`.

- `evidence needs evidence_step, evidence_turn and evidence_quote`
- `bad evidence turn <value>`
- `evidence step <key> is not missed or wrong`
- `call has no turn <n>`
- `quote not in turn <n>`

## Database effect (valid file)

The step named by a row's evidence gets `call_steps.evidence_turn_idx` and `evidence_quote`. Every other step of every applied call gets NULL in both. Nothing else differs from feature 002.
