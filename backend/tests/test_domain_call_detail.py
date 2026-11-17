import pytest

from app.domain.call_detail import (
    CallNotFound,
    StepStatus,
    _require,
    InvalidCallRecord,
    StepRecord,
    SubCheck,
    TurnRecord,
)


# --- private helpers -------------------------------------------------------------------------------------------------

def test_require_accepts_an_allowed_value():
    assert _require("wrong", StepStatus, "step a status") is None


def test_require_names_the_bad_value():
    with pytest.raises(InvalidCallRecord, match="step a status is 'x'; expected one of completed, missed"):
        _require("x", StepStatus, "step a status")


# --- records and errors ----------------------------------------------------------------------------------------------

def test_step_record_rejects_more_points_lost_than_it_is_worth():
    with pytest.raises(InvalidCallRecord, match="step a points_lost is 11; expected 0 to 10"):
        StepRecord("a", 1, "A", 10, "wrong", points_lost=11)


def test_step_record_rejects_an_unknown_status():
    with pytest.raises(InvalidCallRecord, match="step a status is 'skipped'"):
        StepRecord("a", 1, "A", 10, "skipped")


def test_step_record_rejects_an_unknown_severity():
    with pytest.raises(InvalidCallRecord, match="step a severity is 'huge'"):
        StepRecord("a", 1, "A", 10, "wrong", severity="huge", points_lost=5)


def test_sub_check_rejects_an_unknown_result():
    with pytest.raises(InvalidCallRecord, match="sub-check k result is 'skipped'"):
        SubCheck("k", "d", 5, "skipped")


def test_turn_record_rejects_an_unknown_speaker():
    with pytest.raises(InvalidCallRecord, match="turn 1 speaker is 'bot'"):
        TurnRecord(1, "bot", None, "hi")


def test_invalid_call_record_is_a_value_error():
    assert issubclass(InvalidCallRecord, ValueError)


def test_call_not_found_names_the_id():
    error = CallNotFound(42)
    assert error.call_id == 42
    assert str(error) == "no call with id 42"
