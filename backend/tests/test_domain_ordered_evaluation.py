from dataclasses import replace

import pytest

from app.domain.ordered_evaluation import (
    CONFIDENT_DECISION_THRESHOLD, DIFFERENT_VALUE, NOT_STATED,
    CallForEvaluation, DecisionEvidence, ProcedureCheck, RequiredStep, StepDecision, evaluate_step, quote_is_in_turn,
)


SIMPLE = RequiredStep("greet", 5)
CALL = CallForEvaluation(1, (), {2: "Welcome", 9: "savings to checking"}, (2, 9))
GREETING = StepDecision("completed_step", CONFIDENT_DECISION_THRESHOLD, DecisionEvidence(2, "Welcome"))
LOG = ProcedureCheck("record", "logged_matches_request", 35, ("source", "destination"), description="Transfer logged")
READ = ProcedureCheck("source_read_back", "read_back_matches_request", 5, ("source",))
CONFIRM = ProcedureCheck("confirmed", "confirmation_evidence", 5)
SUBMIT = RequiredStep("submit", 45, checks=(LOG, READ, CONFIRM))


def test_quote_must_appear_word_for_word_in_the_stored_turn():
    assert quote_is_in_turn("Harper Valley", "Welcome to Harper Valley Bank")
    assert not quote_is_in_turn("harper valley", "Welcome to Harper Valley Bank")
    assert not quote_is_in_turn("", "Welcome")


def test_simple_step_confidence_boundary_and_saved_diagnostics():
    response = {"answers": []}
    confident = replace(GREETING, raw_response=response)
    result = evaluate_step(SIMPLE, confident, True, CALL)
    assert (result.status, result.evidence, result.decision_confidence, result.decision_response) == (
        "completed", GREETING.evidence, CONFIDENT_DECISION_THRESHOLD, response,
    )
    assert evaluate_step(SIMPLE, replace(GREETING, confidence=.79), True, CALL).status == "under_review"


@pytest.mark.parametrize(("decision", "valid"), [
    (replace(GREETING, contradictory=True), True), (GREETING, False), (StepDecision("refusal", .99), True),
])
def test_unverified_observations_do_not_publish_evidence_or_lose_points(decision, valid):
    result = evaluate_step(SIMPLE, decision, valid, CALL)
    assert (result.status, result.points_lost, result.points_under_review, result.evidence) == (
        "under_review", 0, 5, None,
    )


def test_unobserved_simple_step_is_only_missed_after_call_end():
    decision = StepDecision("not_yet_observed", .99)
    assert evaluate_step(SIMPLE, decision, False, replace(CALL, call_ended=False)) is None
    assert evaluate_step(SIMPLE, decision, False, CALL).status == "missed"


def test_clear_swap_and_unresolved_confirmation_have_independent_outcomes():
    call = replace(CALL, logged_actions={"source": "savings", "destination": "checking"})
    # Even if another field is uncertain, one known mismatch fails the whole logged-values check.
    decision = StepDecision("unclear", .18, facts={"request:source": "checking", "read_back:source": "savings"})
    result = evaluate_step(SUBMIT, decision, False, call)
    assert (result.status, result.points_lost, result.points_under_review, result.evidence) == ("wrong", 40, 5, None)
    assert [(c.key, c.result) for c in result.check_outcomes] == [
        ("record", "failed"), ("source_read_back", "failed"), ("confirmed", "under_review"),
    ]
    assert result.check_outcomes[0].description == "Transfer logged"
    assert [(r.field, r.caller_asked, r.logged, r.match) for r in result.comparison] == [
        ("source", "checking", "savings", False),
    ]


def test_log_only_step_passes_without_spoken_confirmation():
    step = RequiredStep("submit", 35, checks=(LOG,))
    call = replace(CALL, logged_actions={"source": "checking", "destination": "savings"})
    decision = StepDecision("unclear", 0, facts={"request:source": "checking", "request:destination": "savings"})
    result = evaluate_step(step, decision, False, call)
    assert (result.status, result.points_lost, result.points_under_review) == ("completed", 0, 0)
    assert all(row.match for row in result.comparison)


@pytest.mark.parametrize(("decision", "valid", "expected"), [
    (GREETING, True, "passed"), (GREETING, False, "under_review"),
    (StepDecision("not_yet_observed", .99), False, "failed"),
    (StepDecision("not_yet_observed", .18), False, "under_review"),
])
def test_confirmation_evidence_scores_its_own_rubric_item(decision, valid, expected):
    step = RequiredStep("confirm", 5, checks=(CONFIRM,))
    assert evaluate_step(step, decision, valid, CALL).check_outcomes[0].result == expected


@pytest.mark.parametrize(("asked", "said", "status"), [
    ("checking", NOT_STATED, "wrong"), ("checking", None, "under_review"),
    (DIFFERENT_VALUE, DIFFERENT_VALUE, "under_review"), ("checking", DIFFERENT_VALUE, "wrong"),
])
def test_absence_uncertainty_and_out_of_list_values_are_distinct(asked, said, status):
    facts = {"request:source": asked}
    if said is not None:
        facts["read_back:source"] = said
    result = evaluate_step(RequiredStep("read", 5, checks=(READ,)), StepDecision("unclear", 0, facts=facts), False, CALL)
    assert result.status == status


def test_stated_amount_is_compared_to_bank_record_independently_of_form():
    step = RequiredStep("balance", 40, checks=(ProcedureCheck("stated", "stated_matches_system_record", 40, ("balance",)),))
    decision = StepDecision("unclear", .18, facts={"read_back:balance": "114"})
    call = replace(CALL, logged_actions={"balance": "9"}, field_types={"balance": "amount"})
    assert evaluate_step(step, decision, False, call).status == "under_review"
    assert evaluate_step(step, decision, False, replace(call, system_record={"balance": "$114.00"})).status == "completed"
    assert evaluate_step(step, decision, False, replace(call, system_record={"balance": 9})).status == "wrong"
