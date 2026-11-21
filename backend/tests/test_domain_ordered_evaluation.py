from app.domain.ordered_evaluation import (
    CONFIDENT_ACTION_MATCH_THRESHOLD,
    CONFIDENT_DECISION_THRESHOLD,
    DecisionEvidence,
    ProcedureCheck,
    RequiredStep,
    StepDecision,
    evaluate_step,
    evaluate_checks,
    next_transcript_cursor,
    quote_is_in_turn,
)


STEP = RequiredStep("greet", 5)


def test_quote_must_appear_word_for_word_in_the_stored_turn():
    assert quote_is_in_turn("Harper Valley", "Welcome to Harper Valley Bank")
    assert not quote_is_in_turn("harper valley", "Welcome to Harper Valley Bank")
    assert not quote_is_in_turn("", "Welcome")


def test_confidence_boundary_completes_only_at_or_above_the_named_threshold():
    evidence = DecisionEvidence(2, "Welcome")
    low = evaluate_step(STEP, StepDecision("completed_step", CONFIDENT_DECISION_THRESHOLD - .01, evidence), True)
    exact = evaluate_step(STEP, StepDecision("completed_step", CONFIDENT_DECISION_THRESHOLD, evidence), True)
    assert low.status == "under_review" and low.points_under_review == 5
    assert exact.status == "completed" and exact.evidence == evidence


def test_evaluation_carries_confidence_and_raw_decision_for_persistence():
    response = {"answers": [{"name": "step_observation", "choice": "turn:2", "confidence": .91}]}
    result = evaluate_step(STEP, StepDecision("completed_step", .91, DecisionEvidence(2, "Welcome"), raw_response=response), True)
    assert result.decision_confidence == .91 and result.decision_response == response


def test_contradiction_invalid_evidence_and_bad_choice_stay_under_review():
    for decision, valid in (
        (StepDecision("completed_step", .99, contradictory=True), True),
        (StepDecision("completed_step", .99), False),
        (StepDecision("refusal", .99), True),
    ):
        result = evaluate_step(STEP, decision, valid)
        assert result.status == "under_review" and result.points_lost == 0 and result.points_under_review == 5


def test_completed_observation_with_mismatched_logged_action_is_wrong():
    result = evaluate_step(
        STEP, StepDecision("completed_step", .99, logged_actions_match=False,
                           action_confidence=CONFIDENT_ACTION_MATCH_THRESHOLD), True
    )
    assert result.status == "wrong" and result.points_lost == 5


def test_uncertain_action_check_stays_under_review_but_does_not_lower_evidence_confidence():
    result = evaluate_step(
        STEP, StepDecision("completed_step", .99, DecisionEvidence(2, "Welcome"), logged_actions_match=True,
                           action_confidence=CONFIDENT_ACTION_MATCH_THRESHOLD - .01), True
    )
    assert result.status == "under_review" and result.decision_confidence == .99


def test_unobserved_step_waits_until_call_end_then_is_missed_with_the_remaining_steps():
    # Negative observations have no quote; that is distinct from bad evidence.
    assert evaluate_step(STEP, StepDecision("not_yet_observed", .99), False) is None
    result = evaluate_step(STEP, StepDecision("not_yet_observed", .99), False, call_ended=True)
    assert result.status == "missed"


def test_procedure_data_classifies_simple_collection_and_confirmation_steps():
    assert RequiredStep("greet", 5).kind == "simple"
    assert RequiredStep("amount", 5, logged_action_keys=("amount",)).kind == "collection"
    assert RequiredStep("submit", 5, checks_logged_actions=True).kind == "confirmation"


def test_cursor_keeps_a_caller_turn_available_for_multiple_collected_values():
    caller_turn = StepDecision("completed_step", .99, DecisionEvidence(7, "checking to savings"))
    assert next_transcript_cursor(2, caller_turn, True) == 7
    assert next_transcript_cursor(7, caller_turn, True) == 7


def test_cursor_does_not_consume_turns_for_absence_or_review():
    assert next_transcript_cursor(7, StepDecision("not_yet_observed", .99), False) == 7
    assert next_transcript_cursor(7, StepDecision("completed_step", .79, DecisionEvidence(9, "bye")), True) == 7


def test_python_compares_cited_request_readback_and_logged_values():
    checks = (
        ProcedureCheck("logged", "logged_matches_request", 35, ("source", "destination")),
        ProcedureCheck("read_back_source", "read_back_matches_request", 5, ("source",)),
        ProcedureCheck("read_back_destination", "read_back_matches_request", 5, ("destination",)),
    )
    outcomes = evaluate_checks(checks, {
        "request:source": "checking", "request:destination": "savings",
        "read_back:source": "savings", "read_back:destination": "checking",
    }, {"source": "savings", "destination": "checking"})
    assert [(outcome.key, outcome.points_lost, outcome.under_review) for outcome in outcomes] == [
        ("logged", 35, False), ("read_back_source", 5, False), ("read_back_destination", 5, False),
    ]


def test_missing_fact_is_review_not_a_guess():
    outcome = evaluate_checks(
        (ProcedureCheck("logged", "logged_matches_request", 20, ("account",)),), {}, {"account": "checking"}
    )[0]
    assert outcome.under_review and outcome.points_lost == 0


def test_failed_sub_checks_produce_partial_wrong_points_not_a_full_step_loss():
    checks = (ProcedureCheck("logged", "logged_matches_request", 35, ("source",)),)
    outcomes = evaluate_checks(checks, {"request:source": "checking"}, {"source": "savings"})
    result = evaluate_step(
        RequiredStep("submit", 55), StepDecision("completed_step", .95, DecisionEvidence(9, "read back")), True,
        check_outcomes=outcomes,
    )
    assert (result.status, result.points_lost, result.check_outcomes) == ("wrong", 35, outcomes)
