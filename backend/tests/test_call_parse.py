from app.call_parse import _norm, parse_call, snake


def test_snake_turns_metadata_keys_into_procedure_keys():
    assert snake("Transfer Amount") == "transfer_amount"
    assert snake("  account   from ") == "account_from"


def test_norm_compares_amounts_phones_and_account_names_loosely():
    assert _norm("amount", "$1,140.00") == _norm("amount", "1140") == 1140.0
    assert _norm("amount", "a lot") == "a lot"
    assert _norm("phone", "(416) 555-0199") == "4165550199"
    assert _norm("account", "My Savings Account") == _norm("account", "savings") == "savings"


def test_parse_call_uses_the_last_submission_and_the_human_transcript():
    metadata = {
        "sid": "HVB-1",
        "start_time_ms": 1_600_000_000_000,
        "tasks": [{"task_type": "Transfer Money", "transfer amount": "$50"}],
        "agent": {"metadata": {"agent_name": "Sam"}, "responses": [
            {"data": {"task_type": "check balance"}},
            {"data": {"task_type": "transfer money", "transfer amount": "$40"}},
        ]},
    }
    transcript = [
        {"index": 1, "speaker_role": "agent", "human_transcript": " Hi there ", "transcript": "hi their", "start_ms": 1500},
        {"index": 2, "speaker_role": "caller", "human_transcript": "", "transcript": "move fifty", "start_ms": None},
    ]

    call = parse_call(transcript, metadata)

    assert (call["external_id"], call["agent_name"], call["call_type"]) == ("HVB-1", "Sam", "transfer_money")
    assert call["logged"] == {"transfer_amount": "$40"} and call["logged_task_type"] == "transfer_money"
    assert call["assigned"] == {"transfer_amount": "$50"}
    assert call["started_at"].year == 2020
    assert [t["text"] for t in call["turns"]] == ["Hi there", "move fifty"]
    assert [t["start_seconds"] for t in call["turns"]] == [1.5, None]
