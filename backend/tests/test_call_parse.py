from app.call_parse import _norm, snake


def test_snake_turns_metadata_keys_into_procedure_keys():
    assert snake("Transfer Amount") == "transfer_amount"
    assert snake("  account   from ") == "account_from"


def test_norm_compares_amounts_phones_and_account_names_loosely():
    assert _norm("amount", "$1,140.00") == _norm("amount", "1140") == 1140.0
    assert _norm("amount", "a lot") == "a lot"
    assert _norm("phone", "(416) 555-0199") == "4165550199"
    assert _norm("account", "My Savings Account") == _norm("account", "savings") == "savings"
