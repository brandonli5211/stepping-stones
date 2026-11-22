// same shape as GET /calls/{id} (docs/api-contract.md, the Transfer money example). every number, label and
// flag is typed in as the server would send it, the page only draws them. the 0:44 turn also carries the
// "wrong" note the Figma frame shows.
export const SAMPLE_CALL_DETAIL = {
  "header": {
    "call_id": 1,
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
          "kind": "wrong",
          "step_key": "submit_and_confirm_transfer",
          "text": "Wrong: transferred savings → checking"
        },
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
};
