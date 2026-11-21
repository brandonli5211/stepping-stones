from app.infrastructure.analyze_command import parse_args


def test_command_requires_exactly_one_selector():
    assert parse_args(["--call-id", "4"]).call_id == 4
    assert parse_args(["--call-type", "transfer_money"]).call_type == "transfer_money"
    assert parse_args(["--all"]).all


def test_force_must_be_explicit_to_replace_an_existing_result():
    assert not parse_args(["--call-id", "4"]).force
    assert parse_args(["--call-id", "4", "--force"]).force
