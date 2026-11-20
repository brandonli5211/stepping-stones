# Procedure rules, schema 3

| File | What it is |
| --- | --- |
| `_common.json` | Shared rules: severity bands, field types and how to compare them, sub-check types, judging rules, the prompt template. |
| `transfer_money.json`, `check_balance.json`, `replace_card.json`, `schedule_appointment.json` | One call type each: its gate question, fields, steps, points and sub-checks. |

Store each file as one row (for example a JSONB column keyed by `call_type` and `version`), and `_common.json` as its own row.

## Using it on a call

1. Load `_common` and the procedure for the call type.
2. Fill `_common.prompt_template` (the placeholders are described in `_common.prompt_placeholders`) with the agent name, the transcript, and the procedure's steps and fields.
3. Send it to the model. Ask for JSON, temperature 0, fixed seed (`model_settings`).
4. In code: check every quote is in its turn word for word and contains its value. If `is_expected_call` is false, send the call to review.
5. In code: judge each step and sub-check as `_common.sub_check_types` says, then take the failed parts' points off 100.

Send the model only the transcript and the agent's name. Never send `tasks` or the logged values (`_common.metadata_use`).

## Fields

- `role: logged`: the agent enters it. Compared with what the caller asked for (`reference: caller_request`).
- `role: told_to_caller`: the agent must say it. Compared with the bank's own record (`reference: system_record`). In HarperValleyBank the record is `tasks["account balance"]`. In production it is the bank system. Never show it to the model.
- `model_reports`: which model sections list it (`caller_request`, `agent_read_back`).
- `type`: how values are compared (`_common.field_types`).

## Changed from the transfer file I sent earlier (version 2)

- `is_transfer_call` is now `is_expected_call` for every call type, and the gate question moves into each procedure.
- Sub-checks have a `type` (`logged_task_type`, `logged_matches_request`, `read_back_matches_request`, `stated_matches_system_record`, `confirmation_evidence`) with parameters, instead of a name tied to one call type. Points are unchanged.
- The model is asked for step evidence only on steps that leave evidence in the call (no sub-checks, or a `confirmation_evidence` sub-check). Log steps happen in the system, not in the conversation.

## Adding a call type

Copy the closest file, change the call type, fields and steps, and run:

    python3 docs/procedures/validate.py <call_type>.json

Order checks, pay bill and reset password are written (field types `address`, `phone` and `text` were added to `_common.json`). Get branch hours is written too: the hours the agent states are reported but not scored.

## Used by the API

`POST /calls/{call_id}` (backend/app/calls_api.py) reads these files and builds the prompt for the local model.
