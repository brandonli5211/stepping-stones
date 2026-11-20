from app.call_parse import snake


def test_snake_turns_metadata_keys_into_procedure_keys():
    assert snake("Transfer Amount") == "transfer_amount"
    assert snake("  account   from ") == "account_from"
