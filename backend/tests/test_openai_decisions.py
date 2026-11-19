import json
from pathlib import Path

from app.adapters.openai_decisions import OpenAIDecisionsAdapter
from app.domain.procedure import AgentTurnWindow, CallCursor, ProcedureStep


def _harper_valley_greeting_fixture() -> dict:
    path = Path(__file__).parent / "fixtures" / "harper_valley_replace_card_greeting.json"
    return json.loads(path.read_text(encoding="utf-8"))

def test_decisions_body_uses_required_model_endpoint_inputs_and_two_choices():
    adapter = OpenAIDecisionsAdapter(api_key="test", base_url="https://example.test")
    body = adapter._request_body("procedure", "task", ProcedureStep("step", "Verify", ("name",), ("confirm",), ("skip",)), AgentTurnWindow("I confirmed", ("customer asked",)), CallCursor(2, 4))
    assert adapter._url == "https://example.test/v1/decisions" and body["model"] == "gpt-6-luna"
    assert body["input"][0]["content"][0]["data"]["call_cursor"]["expected_step_index"] == 2
    question = body["questions"][0]
    assert question["type"] == "choice" and [item["value"] for item in question["choices"]] == ["completed_step", "not_yet_observed"]

def test_decisions_response_parses_named_choice_and_confidence():
    decision = OpenAIDecisionsAdapter._parse({"answers": [{"name": "expected_step_observation", "choice": "completed_step", "confidence": .91}]})
    assert decision.choice == "completed_step" and decision.confidence == .91


def test_decisions_body_uses_the_harper_valley_call_fixture():
    fixture = _harper_valley_greeting_fixture()
    step = ProcedureStep(**{
        key: tuple(value) if isinstance(value, list) else value
        for key, value in fixture["current_step"].items()
    })
    window_data = fixture["agent_turn_window"]
    window = AgentTurnWindow(
        agent_turn=window_data["agent_turn"],
        surrounding_context=tuple(window_data["surrounding_context"]),
        contradictory_evidence=window_data["contradictory_evidence"],
    )
    cursor = CallCursor(**fixture["call_cursor"])

    body = OpenAIDecisionsAdapter(api_key="test")._request_body(
        fixture["procedure_id"], fixture["task_id"], step, window, cursor
    )

    data = body["input"][0]["content"][0]["data"]
    assert data["procedure_id"] == "replace_card"
    assert data["current_step"]["id"] == "greet_and_open"
    assert data["current_agent_turn"] == window_data["agent_turn"]
    assert data["call_cursor"] == fixture["call_cursor"]
