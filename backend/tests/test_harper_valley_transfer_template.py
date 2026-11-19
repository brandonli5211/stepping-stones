import json
from pathlib import Path


FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_second_harper_valley_call_matches_the_transfer_template_schema():
    template = _load("harper-valley-transfer-money-template.json")
    candidate = _load("harper-valley-transfer-money-020e48edcf0940a4.json")

    assert candidate["task_type"] == template["task_type"] == "transfer money"
    assert set(candidate) == set(template)
    assert len(candidate["steps"]) == len(template["steps"])

    for expected, actual in zip(template["steps"], candidate["steps"], strict=True):
        assert set(actual) == set(expected)
        assert set(actual["model_example"]) == set(expected["model_example"])
        assert isinstance(actual["model_example"]["agent_turns"], list)
        assert all(set(turn) == {"index", "transcript"} for turn in actual["model_example"]["agent_turns"])
        assert actual["model_example"]["caller_reply"] is None or isinstance(actual["model_example"]["caller_reply"], str)
        assert actual["model_example"]["action_logged"] is None or isinstance(actual["model_example"]["action_logged"], dict)
