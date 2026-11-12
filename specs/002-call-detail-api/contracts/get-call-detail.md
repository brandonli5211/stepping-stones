# Contract: `GET /calls/{id}`

**Feature**: [../spec.md](../spec.md) · **Date**: 2026-11-08 · **Consumers**: #35, #36

Returns everything the call detail screen needs for one call, read from stored
data. Nothing is analyzed and nothing is written.

## Request

| Part | Value |
| --- | --- |
| Method | `GET` |
| Path | `/calls/{id}` |
| `id` | integer: the call's numeric `id`, as returned by `GET /calls`. Not the dataset's `external_id`. |
| Body | none |

## Responses

| Status | When | Body |
| --- | --- | --- |
| `200` | The call is stored | `CallDetail` (below) |
| `404` | No call with that `id` | `{"detail": "no call with id {id}"}` |
| `422` | `id` is not an integer | FastAPI's standard validation error |

## `CallDetail` shape

```text
CallDetail
├── header
│   ├── call_id: int
│   ├── external_id: str              # shown as the call's reference
│   ├── call_type: str                # snake_case key, e.g. transfer_money
│   ├── call_type_name: str           # e.g. "Transfer money"
│   └── summary: str | null           # the one-sentence summary
├── score
│   ├── score: int | null             # 100 - points_lost; null when the call has no steps yet
│   ├── out_of: 100
│   ├── steps_done_right: int         # "6 of 7" → 6
│   ├── steps_total: int              # "6 of 7" → 7
│   ├── points_lost: int
│   ├── critical_count: int
│   ├── points_under_review: int      # 0 when nothing is under review
│   └── provisional: bool             # true when points_under_review > 0 ("so far")
├── transcript: Turn[]                # in order
│   ├── idx: int                      # from 1
│   ├── speaker: "agent" | "caller"
│   ├── start_seconds: number | null  # the page formats it, e.g. 33.53 → "0:33"
│   ├── text: str
│   └── notes: Note[]
│       ├── kind: "evidence" | "wrong"
│       ├── step_key: str
│       └── text: str                 # "Evidence for Greet and open" / "Wrong: ..."
├── steps: Step[]                     # procedure order
│   ├── key: str
│   ├── position: int
│   ├── name: str
│   ├── status: "completed" | "missed" | "wrong" | "under_review"
│   ├── severity: "none" | "slip" | "inaccuracy" | "mistake" | "critical"
│   ├── points: int
│   ├── points_lost: int
│   ├── points_under_review: int
│   └── details
│       ├── description: str | null   # what the step asks for, from the procedure rules
│       ├── detail: str | null        # why, in one sentence
│       ├── sub_checks: SubCheck[]    # key, description, points, result: "passed" | "failed" | "under_review"
│       ├── evidence: { quote: str, turn_idx: int, start_seconds: number | null } | null
│       └── coaching: str | null      # only on missed and wrong steps
├── flags: Flag[]                     # one per missed or wrong step; [] when there are none
│   ├── step_key: str
│   ├── step_name: str
│   ├── status: "missed" | "wrong"
│   ├── severity: "none" | "slip" | "inaccuracy" | "mistake" | "critical"   # same values as the step
│   ├── points_lost: int
│   └── message: str | null           # one sentence on what went wrong
└── type_details                      # tagged by "type"
    ├── { type: "transfer_money", fields: FieldRow[] }
    │       FieldRow: field, label ("Amount" | "From" | "To"), caller_asked, logged, result: "match" | "mismatch" | "reversed"   # From and To are both "reversed" when swapped
    └── { type: "<any other call type>" }   # empty block; never "transfer_money"
```

Rules the consumers can rely on:

- `score.score`, the counts, `flags` and the `notes` are worked out by the
  API. The page must not recompute them (constitution Principle I).
- A call with no mistakes has `flags: []` and no note with `kind: "wrong"`.
- New call types add a new `type_details` variant; the rest of the shape does
  not change.

## Example: Transfer money (demo call HVB-DEMO-06)

`id` and `summary` are illustrative. Every other value matches the Figma frame
"Transfer money, call detail" and the #33 demo call `a2f086d27b3a4f96`, except
the step `description`, which is returned as the procedure rules store it
("Log the transfer correctly…"; the frame says "Submit the transfer…").

```json
{
  "header": {
    "call_id": 6,
    "external_id": "a2f086d27b3a4f96",
    "call_type": "transfer_money",
    "call_type_name": "Transfer money",
    "summary": "The transfer was logged and read back with the accounts reversed, so the money went from savings to checking."
  },
  "score": {
    "score": 45,
    "out_of": 100,
    "steps_done_right": 6,
    "steps_total": 7,
    "points_lost": 55,
    "critical_count": 1,
    "points_under_review": 0,
    "provisional": false
  },
  "transcript": [
    {
      "idx": 1,
      "speaker": "agent",
      "start_seconds": 0.54,
      "text": "[noise]",
      "notes": []
    },
    {
      "idx": 2,
      "speaker": "agent",
      "start_seconds": 2.3,
      "text": "thank you for calling harper valley national bank my name is david how can i help you today",
      "notes": [
        {
          "kind": "evidence",
          "step_key": "greet_and_open",
          "text": "Evidence for Greet and open"
        }
      ]
    },
    {
      "idx": 3,
      "speaker": "caller",
      "start_seconds": 10.09,
      "text": "hi my name is john williams i would like to transfer money between my accounts",
      "notes": []
    },
    {
      "idx": 4,
      "speaker": "agent",
      "start_seconds": 17.14,
      "text": "okay",
      "notes": []
    },
    {
      "idx": 5,
      "speaker": "agent",
      "start_seconds": 18.47,
      "text": "and",
      "notes": []
    },
    {
      "idx": 6,
      "speaker": "agent",
      "start_seconds": 21.07,
      "text": "alright and what is the transfer amount",
      "notes": [
        {
          "kind": "evidence",
          "step_key": "collect_transfer_amount",
          "text": "Evidence for Collect transfer amount"
        }
      ]
    },
    {
      "idx": 7,
      "speaker": "caller",
      "start_seconds": 26.19,
      "text": "from my checking account to my savings account the amount is a hundred and fourteen dollars",
      "notes": [
        {
          "kind": "evidence",
          "step_key": "collect_source_account",
          "text": "Evidence for Collect source account"
        },
        {
          "kind": "evidence",
          "step_key": "collect_destination_account",
          "text": "Evidence for Collect destination account"
        }
      ]
    },
    {
      "idx": 8,
      "speaker": "agent",
      "start_seconds": 29.87,
      "text": "[noise]",
      "notes": []
    },
    {
      "idx": 9,
      "speaker": "agent",
      "start_seconds": 33.53,
      "text": "okay and that was from your savings to your checking account",
      "notes": [
        {
          "kind": "wrong",
          "step_key": "submit_and_confirm_transfer",
          "text": "Wrong: read back reversed. The caller asked checking → savings"
        }
      ]
    },
    {
      "idx": 10,
      "speaker": "caller",
      "start_seconds": 40.69,
      "text": "yes",
      "notes": []
    },
    {
      "idx": 11,
      "speaker": "agent",
      "start_seconds": 40.21,
      "text": "okay",
      "notes": []
    },
    {
      "idx": 12,
      "speaker": "caller",
      "start_seconds": 45.62,
      "text": "[noise]",
      "notes": []
    },
    {
      "idx": 13,
      "speaker": "agent",
      "start_seconds": 44.54,
      "text": "okay so i've transferred one hundred and fourteen dollars from your savings account to your checking account is there anything else i can help you with",
      "notes": [
        {
          "kind": "evidence",
          "step_key": "offer_further_help",
          "text": "Evidence for Offer further help"
        }
      ]
    },
    {
      "idx": 14,
      "speaker": "caller",
      "start_seconds": 52.99,
      "text": "[noise]",
      "notes": []
    },
    {
      "idx": 15,
      "speaker": "caller",
      "start_seconds": 55.93,
      "text": "no that's it thank you have a good day",
      "notes": []
    },
    {
      "idx": 16,
      "speaker": "agent",
      "start_seconds": 57.2,
      "text": "thank you for calling you have a great day",
      "notes": [
        {
          "kind": "evidence",
          "step_key": "close",
          "text": "Evidence for Close"
        }
      ]
    }
  ],
  "steps": [
    {
      "key": "greet_and_open",
      "position": 1,
      "name": "Greet and open",
      "status": "completed",
      "severity": "none",
      "points": 5,
      "points_lost": 0,
      "points_under_review": 0,
      "details": {
        "description": "State the bank name and your own name, then ask how you can help.",
        "detail": null,
        "sub_checks": [],
        "evidence": {
          "quote": "thank you for calling harper valley national bank my name is david how can i help you today",
          "turn_idx": 2,
          "start_seconds": 2.3
        },
        "coaching": null
      }
    },
    {
      "key": "collect_transfer_amount",
      "position": 2,
      "name": "Collect transfer amount",
      "status": "completed",
      "severity": "none",
      "points": 10,
      "points_lost": 0,
      "points_under_review": 0,
      "details": {
        "description": "Get the amount the caller wants to transfer, by asking or by confirming what the caller said.",
        "detail": null,
        "sub_checks": [],
        "evidence": {
          "quote": "what is the transfer amount",
          "turn_idx": 6,
          "start_seconds": 21.07
        },
        "coaching": null
      }
    },
    {
      "key": "collect_source_account",
      "position": 3,
      "name": "Collect source account",
      "status": "completed",
      "severity": "none",
      "points": 10,
      "points_lost": 0,
      "points_under_review": 0,
      "details": {
        "description": "Get the account the money comes from (checking or savings), by asking or by confirming.",
        "detail": null,
        "sub_checks": [],
        "evidence": {
          "quote": "from my checking account",
          "turn_idx": 7,
          "start_seconds": 26.19
        },
        "coaching": null
      }
    },
    {
      "key": "collect_destination_account",
      "position": 4,
      "name": "Collect destination account",
      "status": "completed",
      "severity": "none",
      "points": 10,
      "points_lost": 0,
      "points_under_review": 0,
      "details": {
        "description": "Get the account the money goes to (checking or savings), by asking or by confirming.",
        "detail": null,
        "sub_checks": [],
        "evidence": {
          "quote": "to my savings account",
          "turn_idx": 7,
          "start_seconds": 26.19
        },
        "coaching": null
      }
    },
    {
      "key": "submit_and_confirm_transfer",
      "position": 5,
      "name": "Submit and confirm transfer",
      "status": "wrong",
      "severity": "critical",
      "points": 55,
      "points_lost": 55,
      "points_under_review": 0,
      "details": {
        "description": "Log the transfer correctly, then read back the amount, source and destination to confirm it is done.",
        "detail": "read back reversed. The caller asked checking → savings",
        "sub_checks": [
          {
            "key": "logged_matches",
            "description": "Logged values match what the caller asked",
            "points": 40,
            "result": "failed"
          },
          {
            "key": "read_back",
            "description": "Read back amount and both accounts",
            "points": 15,
            "result": "failed"
          }
        ],
        "evidence": {
          "quote": "okay and that was from your savings to your checking account",
          "turn_idx": 9,
          "start_seconds": 33.53
        },
        "coaching": "Next time, read the accounts back in the order the caller gave them: \"So that's $114 from your checking to your savings, is that right?\""
      }
    },
    {
      "key": "offer_further_help",
      "position": 6,
      "name": "Offer further help",
      "status": "completed",
      "severity": "none",
      "points": 5,
      "points_lost": 0,
      "points_under_review": 0,
      "details": {
        "description": "Ask whether the caller needs anything else.",
        "detail": null,
        "sub_checks": [],
        "evidence": {
          "quote": "is there anything else i can help you with",
          "turn_idx": 13,
          "start_seconds": 44.54
        },
        "coaching": null
      }
    },
    {
      "key": "close",
      "position": 7,
      "name": "Close",
      "status": "completed",
      "severity": "none",
      "points": 5,
      "points_lost": 0,
      "points_under_review": 0,
      "details": {
        "description": "Thank the caller and end the call.",
        "detail": null,
        "sub_checks": [],
        "evidence": {
          "quote": "thank you for calling you have a great day",
          "turn_idx": 16,
          "start_seconds": 57.2
        },
        "coaching": null
      }
    }
  ],
  "flags": [
    {
      "step_key": "submit_and_confirm_transfer",
      "step_name": "Submit and confirm transfer",
      "status": "wrong",
      "severity": "critical",
      "points_lost": 55,
      "message": "Moved $114 savings → checking. The caller asked for checking → savings."
    }
  ],
  "type_details": {
    "type": "transfer_money",
    "fields": [
      {
        "field": "transfer_amount",
        "label": "Amount",
        "caller_asked": "114",
        "logged": "114",
        "result": "match"
      },
      {
        "field": "transfer_source_account",
        "label": "From",
        "caller_asked": "checking",
        "logged": "savings",
        "result": "reversed"
      },
      {
        "field": "transfer_destination_account",
        "label": "To",
        "caller_asked": "savings",
        "logged": "checking",
        "result": "reversed"
      }
    ]
  }
}
```

Difference from the #33 seed: the seed has a second "Wrong" note at 0:44
(turn 13) for the submit step. With one evidence turn per step (research R2)
the API returns one note per step; turn 13 carries only the "Offer further
help" evidence.

## Example: Check balance with no mistakes (demo call HVB-DEMO-02), trimmed

```json
{
  "header": {"call_id": 2, "external_id": "…", "call_type": "check_balance", "call_type_name": "Check balance", "summary": "…"},
  "score": {"score": 100, "out_of": 100, "steps_done_right": 3, "steps_total": 3, "points_lost": 0,
            "critical_count": 0, "points_under_review": 0, "provisional": false},
  "transcript": ["… turns with evidence notes only …"],
  "steps": ["… three completed steps …"],
  "flags": [],
  "type_details": {"type": "check_balance"}
}
```

## Example: not found

`GET /calls/999999` → `404`

```json
{"detail": "no call with id 999999"}
```
