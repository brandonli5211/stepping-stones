import asyncio
import json
import os
from pathlib import Path

import pytest

from app.adapters.openai_decisions import OpenAIDecisionsAdapter
from app.domain.procedure import COMPLETED_STEP, AgentTurnWindow, CallCursor, ProcedureStep


@pytest.mark.skipif(
    os.getenv("RUN_LIVE_DECISIONS_TEST") != "1",
    reason="Set RUN_LIVE_DECISIONS_TEST=1 to call the paid OpenAI Decisions API.",
)
def test_harper_valley_greeting_is_completed_by_live_decisions_api():
    fixture_path = Path(__file__).parent / "fixtures" / "harper-valley-transfer-money-020e48edcf0940a4.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    greeting = fixture["steps"][0]
    example = greeting["model_example"]
    step = ProcedureStep(
        id="greet_and_open",
        objective=greeting["step_description"],
        evidence_requirements=("Name the bank.", "Give the agent's name.", "Ask how the agent can help."),
        acceptable_variants=("The greeting may span consecutive agent turns.",),
        exclusions=("Do not infer missing words from call metadata.",),
    )
    window = AgentTurnWindow(
        agent_turn="\n".join(turn["transcript"] for turn in example["agent_turns"]),
        surrounding_context=(example["caller_reply"],),
    )

    result = asyncio.run(
        OpenAIDecisionsAdapter()(fixture["model_example_sid"], fixture["task_type"], step, window, CallCursor(0, 1))
    )

    assert result.choice == COMPLETED_STEP
    assert result.confidence >= 0.80
