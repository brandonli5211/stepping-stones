from dataclasses import replace

import pytest

from app.domain.call_detail import (
    CallNotFound,
    CallRecord,
    ComparisonRow,
    StepStatus,
    _in_order,
    _money,
    _require,
    _result,
    _same,
    accounts_reversed,
    coaching_for,
    transfer_flag_message,
    EmptyDetails,
    Evidence,
    FieldRow,
    Flag,
    InvalidCallRecord,
    Note,
    StepRecord,
    SubCheck,
    TransferMoneyDetails,
    TurnRecord,
    build_call_detail,
    evidence_for,
    flags,
    notes_by_turn,
    summarize_score,
    transfer_money_details,
    type_details,
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

def test_flags_lists_the_wrong_submit_step_with_its_message():
    assert flags(transfer_money_call().steps, "transfer_money") == (
        Flag("submit_and_confirm_transfer", "Submit and confirm transfer", "wrong", "critical", 55,
             "Moved $114 savings → checking. The caller asked for checking → savings."),
    )


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


# --- type details ----------------------------------------------------------------------------------------------------

def test_transfer_money_details_builds_the_field_table_with_reversed_accounts():
    assert transfer_money_details(transfer_money_call()) == TransferMoneyDetails((
        FieldRow("transfer_amount", "Amount", "114", "114", "match"),
        FieldRow("transfer_source_account", "From", "checking", "savings", "reversed"),
        FieldRow("transfer_destination_account", "To", "savings", "checking", "reversed"),
    ))


def test_transfer_money_details_says_mismatch_when_not_a_swap():
    rows = (ComparisonRow("transfer_amount", "114", "100", False),
            ComparisonRow("transfer_source_account", "checking", "savings", False),
            ComparisonRow("transfer_destination_account", "savings", "savings", True))
    call = replace(transfer_money_call(), steps=(StepRecord("s", 1, "S", 55, "wrong", points_lost=40, comparison=rows),))
    assert [r.result for r in transfer_money_details(call).fields] == ["mismatch", "mismatch", "match"]


# --- reversed accounts and flag messages -----------------------------------------------------------------------------

def test_accounts_reversed_spots_a_swap():
    src = ComparisonRow("transfer_source_account", "checking", "savings", False)
    dst = ComparisonRow("transfer_destination_account", "savings", "checking", False)
    assert accounts_reversed(src, dst) is True


def test_accounts_reversed_is_false_for_other_cases():
    src = ComparisonRow("transfer_source_account", "checking", "checking", True)
    dst = ComparisonRow("transfer_destination_account", "savings", "savings", True)
    same_both = ComparisonRow("transfer_destination_account", "checking", "checking", True)
    assert accounts_reversed(src, dst) is False
    assert accounts_reversed(src, None) is False
    assert accounts_reversed(src, same_both) is False  # caller asked checking → checking: nothing to swap


def test_transfer_flag_message_describes_the_swap():
    submit = transfer_money_call().steps[4]
    assert transfer_flag_message(submit) == "Moved $114 savings → checking. The caller asked for checking → savings."


def test_transfer_flag_message_adds_the_asked_amount_when_it_differs():
    rows = (ComparisonRow("transfer_amount", "114", "146.00", False),
            ComparisonRow("transfer_source_account", "checking", "checking", True),
            ComparisonRow("transfer_destination_account", "savings", "savings", True))
    step = StepRecord("s", 1, "S", 55, "wrong", points_lost=35, comparison=rows)
    assert transfer_flag_message(step) == "Moved $146 checking → savings. The caller asked for $114 checking → savings."


def test_transfer_flag_message_says_when_nothing_was_logged():
    rows = (ComparisonRow("transfer_amount", "78", None, False),
            ComparisonRow("transfer_source_account", "checking", None, False),
            ComparisonRow("transfer_destination_account", "savings", None, False))
    step = StepRecord("s", 1, "S", 55, "wrong", points_lost=35, comparison=rows)
    assert transfer_flag_message(step) == "Nothing was logged. The caller asked for $78 checking → savings."


def test_transfer_flag_message_lists_what_was_partly_logged():
    rows = (ComparisonRow("transfer_amount", "114", "114", True),
            ComparisonRow("transfer_source_account", "checking", None, False),
            ComparisonRow("transfer_destination_account", "savings", "checking", False))
    step = StepRecord("s", 1, "S", 55, "wrong", points_lost=35, comparison=rows)
    assert transfer_flag_message(step) == ("Logged amount $114, from not logged, to checking. "
                                           "The caller asked for $114 checking → savings.")


def test_transfer_flag_message_is_none_when_everything_matches_or_rows_are_missing():
    rows = tuple(replace(r, match=True) for r in transfer_money_call().steps[4].comparison)
    assert transfer_flag_message(StepRecord("s", 1, "S", 55, "wrong", points_lost=5, comparison=rows)) is None
    assert transfer_flag_message(StepRecord("s", 1, "S", 55, "wrong", points_lost=5, comparison=rows[:2])) is None
    unasked = (replace(rows[0], match=False, caller_asked=None),) + rows[1:]
    assert transfer_flag_message(StepRecord("s", 1, "S", 55, "wrong", points_lost=5, comparison=unasked)) is None


def test_money_formats_amounts():
    assert _money("114") == "$114"
    assert _money("146.00") == "$146"
    assert _money("12.5") == "$12.50"
    assert _money("a lot") == "a lot"


def test_same_ignores_case_and_spaces_but_not_missing_values():
    assert _same(" Checking", "checking") is True
    assert _same("checking", "savings") is False
    assert _same(None, None) is False


def test_result_picks_match_mismatch_or_reversed():
    row = ComparisonRow("f", "a", "b", False)
    assert _result(row, True) == "reversed"
    assert _result(row, False) == "mismatch"
    assert _result(replace(row, match=True), True) == "match"


# --- coaching --------------------------------------------------------------------------------------------------------

def test_coaching_for_keeps_coaching_on_missed_and_wrong_steps():
    for status in ("missed", "wrong"):
        step = StepRecord("a", 1, "A", 10, status, points_lost=5, coaching="Next time ...")
        assert coaching_for(step) == "Next time ..."


def test_coaching_for_drops_coaching_on_completed_and_under_review_steps():
    for status in ("completed", "under_review"):
        assert coaching_for(StepRecord("a", 1, "A", 10, status, coaching="Next time ...")) is None


def test_build_call_detail_puts_coaching_only_on_the_wrong_step():
    call = transfer_money_call()
    steps = tuple(replace(s, coaching="Stray tip.") if s.status == "completed" else s for s in call.steps)
    detail = build_call_detail(replace(call, steps=steps))
    assert [s.coaching is not None for s in detail.steps] == [False, False, False, False, True, False, False]


# --- private helpers -------------------------------------------------------------------------------------------------

def test_require_accepts_an_allowed_value():
    assert _require("wrong", StepStatus, "step a status") is None


def test_require_names_the_bad_value():
    with pytest.raises(InvalidCallRecord, match="step a status is 'x'; expected one of completed, missed"):
        _require("x", StepStatus, "step a status")


def test_in_order_sorts_steps_by_position():
    a, b = StepRecord("a", 2, "A", 5, "completed"), StepRecord("b", 1, "B", 5, "completed")
    assert _in_order((a, b)) == (b, a)


def test_transfer_money_details_is_empty_without_comparison_rows():
    call = replace(transfer_money_call(), steps=())
    assert transfer_money_details(call) == TransferMoneyDetails(())


def test_type_details_is_an_empty_block_naming_an_unknown_type():
    assert type_details(check_balance_call()) == EmptyDetails("check_balance")


def test_type_details_uses_the_transfer_money_builder():
    assert isinstance(type_details(transfer_money_call()), TransferMoneyDetails)


# --- build_call_detail -----------------------------------------------------------------------------------------------

def test_build_call_detail_returns_every_value_on_the_mock():
    detail = build_call_detail(transfer_money_call())
    assert detail.header.call_type_name == "Transfer money"
    assert detail.header.external_id == "a2f086d27b3a4f96"
    assert detail.score.score == 45
    assert len(detail.transcript) == 16
    turn9 = detail.transcript[8]
    assert (turn9.turn.idx, turn9.turn.start_seconds) == (9, 33.53)
    assert turn9.notes[0].kind == "wrong"
    submit = detail.steps[4]
    assert submit.evidence == Evidence("okay and that was from your savings to your checking account", 9, 33.53)
    assert [c.points for c in submit.step.sub_checks] == [40, 15]
    assert submit.step.coaching.startswith("Next time")
    assert submit.step.description.startswith("Log the transfer correctly")
    assert len(detail.flags) == 1
    assert detail.flags[0].message == "Moved $114 savings → checking. The caller asked for checking → savings."
    assert [r.result for r in detail.type_details.fields] == ["match", "reversed", "reversed"]


def test_build_call_detail_without_mistakes_has_no_flags_or_wrong_notes():
    detail = build_call_detail(check_balance_call())
    assert detail.flags == ()
    assert not any(n.kind == "wrong" for t in detail.transcript for n in t.notes)
    assert detail.score.score == 100
    assert detail.type_details == EmptyDetails("check_balance")


def test_build_call_detail_for_a_pending_call():
    call = CallRecord(9, "x", "pay_bill", "Pay bill", None, turns=(TurnRecord(1, "agent", 0.5, "hello"),))
    detail = build_call_detail(call)
    assert detail.score.score is None
    assert detail.steps == () and detail.flags == ()
    assert detail.transcript[0].notes == ()


def test_build_call_detail_orders_steps_and_turns():
    call = transfer_money_call()
    shuffled = replace(call, steps=tuple(reversed(call.steps)), turns=tuple(reversed(call.turns)))
    detail = build_call_detail(shuffled)
    assert [s.step.position for s in detail.steps] == list(range(1, 8))
    assert [t.turn.idx for t in detail.transcript] == list(range(1, 17))


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
