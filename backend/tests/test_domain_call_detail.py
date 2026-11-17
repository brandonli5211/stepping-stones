import pytest

from app.domain.call_detail import (
    CallNotFound,
    StepStatus,
    _in_order,
    _require,
    coaching_for,
    Evidence,
    InvalidCallRecord,
    Note,
    StepRecord,
    SubCheck,
    TurnRecord,
    evidence_for,
    flags,
    notes_by_turn,
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


# --- notes_by_turn ---------------------------------------------------------------------------------------------------

def test_notes_by_turn_puts_evidence_and_wrong_notes_on_their_turns():
    notes = notes_by_turn(transfer_money_call().steps)
    assert notes[2] == (Note("evidence", "greet_and_open", "Evidence for Greet and open"),)
    assert [n.step_key for n in notes[7]] == ["collect_source_account", "collect_destination_account"]
    assert notes[9] == (Note("wrong", "submit_and_confirm_transfer",
                             "Wrong: read back reversed. The caller asked checking → savings"),)


def test_notes_by_turn_has_no_wrong_notes_without_mistakes():
    notes = notes_by_turn(check_balance_call().steps)
    assert all(n.kind == "evidence" for turn in notes.values() for n in turn)


def test_notes_by_turn_skips_missed_and_under_review_steps_and_steps_without_a_turn():
    steps = (
        StepRecord("m", 1, "M", 10, "missed", points_lost=10, evidence_turn_idx=1),
        StepRecord("r", 2, "R", 10, "under_review", evidence_turn_idx=1),
        StepRecord("c", 3, "C", 10, "completed"),
    )
    assert notes_by_turn(steps) == {}


def test_notes_by_turn_falls_back_to_the_step_name_without_a_detail():
    steps = (StepRecord("w", 1, "Close", 10, "wrong", points_lost=5, evidence_turn_idx=3),)
    assert notes_by_turn(steps) == {3: (Note("wrong", "w", "Wrong: Close"),)}


# --- flags -----------------------------------------------------------------------------------------------------------

def test_flags_falls_back_to_the_step_detail_for_other_types():
    steps = (StepRecord("a", 1, "A", 10, "wrong", points_lost=5, detail="Said the wrong balance."),)
    assert flags(steps, "check_balance")[0].message == "Said the wrong balance."


def test_flags_has_no_message_without_a_builder_or_detail():
    assert flags((StepRecord("a", 1, "A", 10, "missed", points_lost=10),))[0].message is None


def test_flags_is_empty_without_mistakes():
    assert flags(check_balance_call().steps) == ()


def test_flags_includes_missed_but_not_under_review_steps_in_procedure_order():
    steps = (
        StepRecord("late", 3, "Late", 10, "missed", severity="inaccuracy", points_lost=10),
        StepRecord("review", 2, "Review", 10, "under_review", points_under_review=10),
        StepRecord("early", 1, "Early", 10, "wrong", severity="slip", points_lost=5),
    )
    assert [f.step_key for f in flags(steps)] == ["early", "late"]


# --- evidence_for ----------------------------------------------------------------------------------------------------

def test_evidence_for_gives_the_quote_and_its_time():
    call = transfer_money_call()
    submit = next(s for s in call.steps if s.key == "submit_and_confirm_transfer")
    assert evidence_for(submit, call.turns) == Evidence(
        "okay and that was from your savings to your checking account", 9, 33.53)


def test_evidence_for_is_none_for_a_missed_step():
    step = StepRecord("m", 1, "M", 10, "missed", points_lost=10)
    assert evidence_for(step, ()) is None


def test_evidence_for_keeps_the_quote_when_the_turn_has_no_time():
    step = StepRecord("c", 1, "C", 10, "completed", evidence_turn_idx=1, evidence_quote="hello")
    turns = (TurnRecord(1, "agent", None, "hello there"),)
    assert evidence_for(step, turns) == Evidence("hello", 1, None)


# --- coaching --------------------------------------------------------------------------------------------------------

def test_coaching_for_keeps_coaching_on_missed_and_wrong_steps():
    for status in ("missed", "wrong"):
        step = StepRecord("a", 1, "A", 10, status, points_lost=5, coaching="Next time ...")
        assert coaching_for(step) == "Next time ..."


def test_coaching_for_drops_coaching_on_completed_and_under_review_steps():
    for status in ("completed", "under_review"):
        assert coaching_for(StepRecord("a", 1, "A", 10, status, coaching="Next time ...")) is None


# --- private helpers -------------------------------------------------------------------------------------------------

def test_require_accepts_an_allowed_value():
    assert _require("wrong", StepStatus, "step a status") is None


def test_require_names_the_bad_value():
    with pytest.raises(InvalidCallRecord, match="step a status is 'x'; expected one of completed, missed"):
        _require("x", StepStatus, "step a status")


def test_in_order_sorts_steps_by_position():
    a, b = StepRecord("a", 2, "A", 5, "completed"), StepRecord("b", 1, "B", 5, "completed")
    assert _in_order((a, b)) == (b, a)


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
