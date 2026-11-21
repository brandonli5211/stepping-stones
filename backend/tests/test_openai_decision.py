import asyncio
import json
from pathlib import Path

import pytest

from app.adapters.llm.openai_decision import OpenAIDecisionModel
from app.domain.ordered_evaluation import (
    CONFIDENT_FACT_THRESHOLD, CallForEvaluation, DecisionEvidence, ProcedureCheck, RequiredStep,
)


CALL = CallForEvaluation(7, (), {1: "Welcome to Harper Valley", 2: "How can I help?"}, (1, 2))
GREET = RequiredStep("greet", 5, "Greet")
SUBMIT = RequiredStep("submit", 40, checks=(
    ProcedureCheck("logged", "logged_matches_request", 35, ("source",)),
    ProcedureCheck("announced", "read_back_matches_request", 5, ("source",)),
))
TRANSFER = CallForEvaluation(1, (SUBMIT,), {7: "From checking", 9: "From your savings", 10: "Yes"}, (9,),
                             {"source": "savings"}, field_types={"source": "account"},
                             field_hints={"source": "The account the money comes FROM."})


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
    call = CallForEvaluation(7, (), {1: "I need $10", 2: "Anything else?"}, (2,),
                             field_hints={"transfer_amount": "The amount to move."})
    step = RequiredStep("amount", 5, done_when="The agent asks for it.", logged_action_keys=("transfer_amount",))
    body = OpenAIDecisionModel("test").request_body(call, step)
    assert [choice["value"] for choice in body["questions"][0]["choices"]] == [
        "turn:1", "turn:2", "not_yet_observed", "unclear",
    ]
    assert "either speaker" in body["questions"][0]["instructions"]
    assert "The amount to move." in body["questions"][0]["instructions"]
    assert body["questions"][0]["choices"][0]["description"] == "Caller: I need $10"
    assert "done_when" not in body["input"][0]["content"][0]["data"]["procedure_step"]


def test_collection_response_can_cite_a_caller_turn():
    call = CallForEvaluation(7, (), {7: "Move $10"}, (), {"transfer_amount": "$10"})
    step = RequiredStep("amount", 5, logged_action_keys=("transfer_amount",))
    decision = OpenAIDecisionModel.parse(
        {"answers": [{"name": "step_observation", "choice": "turn:7", "confidence": .95}]}, call, step
    )
    assert decision.evidence == DecisionEvidence(7, "Move $10")


def test_submit_asks_for_the_earliest_readback_even_if_wrong_and_only_required_fields():
    body = OpenAIDecisionModel("test").request_body(TRANSFER, SUBMIT, 7)
    questions = body["questions"]
    assert [q["name"] for q in questions] == ["step_observation", "request:source", "read_back:source"]
    assert "first agent turn" in questions[0]["instructions"]
    assert "incorrect read-back" in questions[0]["instructions"]
    assert [c["value"] for c in questions[0]["choices"]] == ["turn:9", "not_yet_observed", "unclear"]
    assert "checking" in [c["value"] for c in questions[1]["choices"]]
    assert "anywhere" in questions[1]["instructions"] and "at or after turn 7" in questions[2]["instructions"]
    assert all("The account the money comes FROM." in q["instructions"] for q in questions[1:])
    speech = body["input"][0]["content"][0]["data"]
    assert [t["turn"] for t in speech["caller_statements"]] == [7, 10]
    assert [t["turn"] for t in speech["agent_statements"]] == [9]
    assert "explicitly names" in questions[1]["instructions"]


def test_submit_sends_separate_speaker_scoped_requests_and_retains_each_response(monkeypatch):
    model = OpenAIDecisionModel("test")
    scopes = []
    expected = {
        "step_observation": ("agent_statements", "turn:9"), "request:source": ("caller_statements", "checking"),
        "read_back:source": ("agent_statements", "savings"),
    }

    def respond(body):
        question, = body["questions"]
        name = question["name"]
        speech, choice = expected[name]
        context = body["input"][0]["content"][0]["data"]
        assert set(context) == {"procedure_step", speech}
        assert {t["speaker"] for t in context[speech]} == {"caller" if speech == "caller_statements" else "agent"}
        scopes.append(name)
        answers = [{"name": name, "choice": choice, "confidence": .91}]
        if name == "step_observation":
            # The agent-only request cannot speak for the caller.
            answers.append({"name": "request:source", "choice": "savings", "confidence": 1})
        return {"id": str(len(scopes)), "answers": answers}

    monkeypatch.setattr(model, "_post", respond)
    result = asyncio.run(model.decide(TRANSFER, SUBMIT, 7))
    assert scopes == list(expected)
    assert result.raw_response["responses"]["step_observation"]["id"] == "1"
    assert [a["name"] for a in result.raw_response["answers"]] == scopes
    assert result.facts == {"request:source": "checking", "read_back:source": "savings"}


def test_unclear_or_missing_citation_preserves_qualified_field_facts_and_raw_confidences():
    response = {"answers": [
        {"name": "step_observation", "choice": "unclear", "confidence": .18},
        {"name": "request:source", "choice": "checking", "confidence": CONFIDENT_FACT_THRESHOLD},
        {"name": "read_back:source", "choice": "savings", "confidence": .96},
    ]}
    for items in (response["answers"], response["answers"][1:]):
        raw = {"answers": items}
        decision = OpenAIDecisionModel.parse(raw, TRANSFER, SUBMIT)
        assert decision.choice == "unclear" and decision.evidence is None
        assert decision.facts == {"request:source": "checking", "read_back:source": "savings"}
        assert decision.raw_response == raw


@pytest.mark.parametrize("invalid", [
    {"choice": "checking", "confidence": CONFIDENT_FACT_THRESHOLD - .01},
    {"choice": "checking", "confidence": float("nan")},
    {"choice": "checking", "confidence": 1.01},
    {"choice": "checking", "confidence": True},
    {"choice": "checking", "confidence": None},
    {"choice": "invented", "confidence": 1},
    {"choice": "unclear", "confidence": 1},
    {"type": "refusal", "choice": "checking", "confidence": 1},
])
def test_invalid_or_uncertain_fact_only_removes_its_own_field(invalid):
    raw = {"answers": [
        {"name": "step_observation", "choice": "turn:9", "confidence": .98},
        {"name": "request:source", **invalid},
        {"name": "read_back:source", "choice": "not_stated", "confidence": .85},
        {"name": "request:invented", "choice": "checking", "confidence": 1},
    ]}
    decision = OpenAIDecisionModel.parse(raw, TRANSFER, SUBMIT)
    assert decision.facts == {"read_back:source": "not_stated"}
    assert decision.evidence == DecisionEvidence(9, TRANSFER.turn_texts[9])


def test_log_only_asks_for_the_caller_request_and_reports_an_unlisted_value():
    step = RequiredStep("log", 35, checks=(SUBMIT.checks[0],))
    questions = OpenAIDecisionModel("test").request_body(TRANSFER, step)["questions"]
    assert [q["name"] for q in questions] == ["request:source"]
    response = {"answers": [{"name": "request:source", "choice": "different_value", "confidence": .9}]}
    decision = OpenAIDecisionModel.parse(response, TRANSFER, step)
    assert decision.facts == {"request:source": "different_value"} and decision.evidence is None


def test_balance_choices_come_from_agent_words_inside_the_window_and_keep_server_record_private():
    step = RequiredStep("state_balance", 50, checks=(
        ProcedureCheck("balance", "stated_matches_system_record", 50, ("account_balance",)),
    ))
    call = CallForEvaluation(1, (step,), {1: "Balance was 98", 3: "Is it 121?", 4: "A hundred and fourteen dollars and ten cents"},
                             (1, 4), {"account_balance": 8612}, field_types={"account_balance": "amount"},
                             system_record={"account_balance": 8612})
    body = OpenAIDecisionModel("test").request_body(call, step, 3)
    assert [q["name"] for q in body["questions"]] == ["step_observation", "read_back:account_balance"]
    assert [c["value"] for c in body["questions"][1]["choices"]] == ["114.1", "not_stated", "unclear"]
    assert "8612" not in json.dumps(body)


def test_refused_duplicate_and_stale_citations_preserve_other_independent_facts():
    valid_fact = {"name": "request:source", "choice": "checking", "confidence": .85}
    stale = {"name": "step_observation", "choice": "turn:9", "confidence": .99}
    assert OpenAIDecisionModel.parse({"answers": [stale, valid_fact]}, TRANSFER, SUBMIT, 10).evidence is None
    answer = OpenAIDecisionModel.parse({"answers": [valid_fact, valid_fact, stale]}, TRANSFER, SUBMIT)
    assert not answer.facts and answer.evidence.turn_idx == 9


def test_selected_turn_becomes_exact_stored_evidence():
    response = json.loads((Path(__file__).parent / "fixtures" / "openai_decisions" / "step_observation_response.json").read_text())
    decision = OpenAIDecisionModel.parse(response, CALL, GREET)
    assert decision.choice == "completed_step"
    assert decision.evidence.quote == "Welcome to Harper Valley"
    assert decision.raw_response == response


def test_refusals_and_unknown_turns_become_reviewable_unclear_decisions():
    assert OpenAIDecisionModel.parse({"answers": [{"type": "refusal", "name": "step_observation"}]}, CALL, GREET).choice == "unclear"
    assert OpenAIDecisionModel.parse({"answers": [{"name": "step_observation", "choice": "turn:99", "confidence": .99}]}, CALL, GREET).choice == "unclear"
