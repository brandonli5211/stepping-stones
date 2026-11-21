import json
from pathlib import Path

from app.adapters.llm.openai_decision import OpenAIDecisionModel
from app.domain.ordered_evaluation import CallForEvaluation, RequiredStep


CALL = CallForEvaluation(7, (), {1: "Welcome to Harper Valley", 2: "How can I help?"}, (1, 2))


def test_request_offers_only_stored_agent_turns_and_safe_fallbacks():
    body = OpenAIDecisionModel("test", "https://example.test").request_body(CALL, RequiredStep("greet", 5, "Greet"))
    assert body["model"] == "gpt-6-luna"
    values = [choice["value"] for choice in body["questions"][0]["choices"]]
    assert values == ["turn:1", "turn:2", "not_yet_observed", "unclear"]


def test_request_does_not_offer_evidence_before_the_procedure_cursor():
    body = OpenAIDecisionModel("test").request_body(CALL, RequiredStep("close", 5), minimum_evidence_turn=2)
    values = [choice["value"] for choice in body["questions"][0]["choices"]]
    assert values == ["turn:2", "not_yet_observed", "unclear"]


def test_logged_action_check_is_separate_from_the_step_observation():
    call = CallForEvaluation(7, (), {1: "Move $10"}, (1,), {"transfer_amount": "$10"})
    body = OpenAIDecisionModel("test").request_body(
        call, RequiredStep("log", 5, logged_action_keys=("transfer_amount",), checks_logged_actions=True)
    )
    assert [question["name"] for question in body["questions"]] == ["step_observation", "logged_actions_match"]
    assert body["input"][0]["content"][0]["data"]["procedure_step"]["logged_actions"] == {"transfer_amount": "$10"}


def test_action_confidence_is_not_folded_into_the_evidence_confidence():
    response = {"answers": [
        {"name": "step_observation", "choice": "turn:1", "confidence": .54},
        {"name": "logged_actions_match", "choice": "mismatch", "confidence": .96},
    ]}
    decision = OpenAIDecisionModel.parse(response, CALL)
    assert (decision.confidence, decision.logged_actions_match, decision.action_confidence) == (.54, False, .96)


def test_confident_action_mismatch_survives_an_unclear_evidence_choice():
    response = {"answers": [
        {"name": "step_observation", "choice": "unclear", "confidence": .18},
        {"name": "logged_actions_match", "choice": "mismatch", "confidence": .89},
    ]}
    decision = OpenAIDecisionModel.parse(response, CALL)
    assert (decision.choice, decision.logged_actions_match, decision.action_confidence) == ("unclear", False, .89)


def test_selected_turn_becomes_exact_stored_evidence():
    response = json.loads((Path(__file__).parent / "fixtures" / "openai_decisions" / "step_observation_response.json").read_text())
    decision = OpenAIDecisionModel.parse(response, CALL)
    assert decision.choice == "completed_step"
    assert decision.evidence.quote == "Welcome to Harper Valley"
    assert decision.raw_response == response


def test_refusals_and_unknown_turns_become_reviewable_unclear_decisions():
    assert OpenAIDecisionModel.parse({"answers": [{"type": "refusal", "name": "step_observation"}]}, CALL).choice == "unclear"
    assert OpenAIDecisionModel.parse({"answers": [{"name": "step_observation", "choice": "turn:99", "confidence": .99}]}, CALL).choice == "unclear"
