from app.domain.ordered_evaluation import (
    CONFIDENT_ACTION_MATCH_THRESHOLD,
    CONFIDENT_DECISION_THRESHOLD,
    DecisionEvidence,
    RequiredStep,
    StepDecision,
    evaluate_step,
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
