import pytest

from app.domain.call_detail import (
    CallNotFound,
    StepStatus,
    _require,
    InvalidCallRecord,
    StepRecord,
    SubCheck,
    TurnRecord,
    summarize_score,
)
from call_detail_fixtures import check_balance_call, transfer_money_call


# --- summarize_score -------------------------------------------------------------------------------------------------

def test_summarize_score_matches_the_transfer_money_mock():
    score = summarize_score(transfer_money_call().steps)
    assert (score.score, score.out_of) == (45, 100)
    assert (score.steps_done_right, score.steps_total) == (6, 7)
    assert score.points_lost == 55
    assert score.critical_count == 1
    assert score.points_under_review == 0
    assert score.provisional is False


def test_summarize_score_is_100_when_nothing_is_lost():
    score = summarize_score(check_balance_call().steps)
    assert (score.score, score.steps_done_right, score.steps_total, score.points_lost) == (100, 3, 3, 0)
    assert score.critical_count == 0


def test_summarize_score_is_provisional_while_a_step_is_under_review():
    steps = (
        StepRecord("a", 1, "A", 40, "completed"),
        StepRecord("b", 2, "B", 60, "under_review", points_under_review=15),
    )
    score = summarize_score(steps)
    assert score.score == 100
    assert score.points_under_review == 15
    assert score.provisional is True
    assert score.steps_done_right == 1


def test_summarize_score_has_no_score_without_steps():
    score = summarize_score(())
    assert score.score is None
    assert (score.steps_done_right, score.steps_total, score.points_lost) == (0, 0, 0)


def test_summarize_score_never_goes_below_zero():
    steps = (StepRecord("a", 1, "A", 80, "wrong", points_lost=80), StepRecord("b", 2, "B", 40, "missed", points_lost=40))
    assert summarize_score(steps).score == 0


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
