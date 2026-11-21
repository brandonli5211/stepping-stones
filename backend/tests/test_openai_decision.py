import json
from pathlib import Path

from app.adapters.llm.openai_decision import OpenAIDecisionModel
from app.domain.ordered_evaluation import CallForEvaluation, ProcedureCheck, RequiredStep


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


def test_collection_request_offers_caller_and_agent_turns():
    call = CallForEvaluation(7, (), {1: "I need $10", 2: "Anything else?"}, (2,))
    step = RequiredStep("amount", 5, logged_action_keys=("transfer_amount",))
    body = OpenAIDecisionModel("test").request_body(call, step)
    assert [choice["value"] for choice in body["questions"][0]["choices"]] == [
        "turn:1", "turn:2", "not_yet_observed", "unclear",
    ]
    assert "either speaker" in body["questions"][0]["instructions"]


def test_collection_response_can_cite_a_caller_turn():
    call = CallForEvaluation(7, (), {7: "Move $10"}, (), {"transfer_amount": "$10"})
    step = RequiredStep("amount", 5, logged_action_keys=("transfer_amount",))
    decision = OpenAIDecisionModel.parse(
        {"answers": [{"name": "step_observation", "choice": "turn:7", "confidence": .95}]}, call, step
    )
    assert decision.evidence == type(decision.evidence)(7, "Move $10")


def test_confirmation_requests_request_and_readback_facts_not_a_correctness_judgment():
    call = CallForEvaluation(7, (), {1: "Move $10"}, (1,), {"transfer_amount": "$10"})
    body = OpenAIDecisionModel("test").request_body(
        call, RequiredStep("log", 5, logged_action_keys=("transfer_amount",), checks=(
            ProcedureCheck("logged", "logged_matches_request", 5, ("transfer_amount",)),
        ))
    )
    assert [question["name"] for question in body["questions"]] == [
        "step_observation", "request:transfer_amount", "read_back:transfer_amount",
    ]
    assert body["input"][0]["content"][0]["data"]["procedure_step"]["logged_actions"] == {"transfer_amount": "$10"}


def test_confirmation_response_parses_facts_without_a_model_correctness_judgment():
    response = {"answers": [
        {"name": "step_observation", "choice": "turn:1", "confidence": .94},
        {"name": "request:source", "choice": "checking", "confidence": .96},
        {"name": "read_back:source", "choice": "savings", "confidence": .96},
    ]}
    decision = OpenAIDecisionModel.parse(response, CALL)
    assert decision.confidence == .94
    assert decision.facts == {"request:source": "checking", "read_back:source": "savings"}


def test_selected_turn_becomes_exact_stored_evidence():
    response = json.loads((Path(__file__).parent / "fixtures" / "openai_decisions" / "step_observation_response.json").read_text())
    decision = OpenAIDecisionModel.parse(response, CALL)
    assert decision.choice == "completed_step"
    assert decision.evidence.quote == "Welcome to Harper Valley"
    assert decision.raw_response == response


def test_refusals_and_unknown_turns_become_reviewable_unclear_decisions():
    assert OpenAIDecisionModel.parse({"answers": [{"type": "refusal", "name": "step_observation"}]}, CALL).choice == "unclear"
    assert OpenAIDecisionModel.parse({"answers": [{"name": "step_observation", "choice": "turn:99", "confidence": .99}]}, CALL).choice == "unclear"
