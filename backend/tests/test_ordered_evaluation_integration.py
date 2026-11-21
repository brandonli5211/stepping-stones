"""Replay transfer facts through the Decisions adapter and the command's use case."""

import asyncio
import json
import os
from pathlib import Path

import pytest

from app.adapters.command.analyze import AnalyzePresenter, evaluate_one
from app.adapters.llm.openai_decision import OpenAIDecisionModel
from app.adapters.persistence.ordered_call_store import required_steps
from app.application.evaluate_ordered_call.interactor import EvaluateOrderedCallInteractor
from app.domain.ordered_evaluation import CallForEvaluation


class RecordingStore:
    def __init__(self, call):
        self.call = call

    async def load_for_evaluation(self, call_id):
        assert call_id == self.call.id
        return self.call

    async def save_evaluation(self, call, steps):
        self.results = {step.key: step for step in steps}


@pytest.mark.parametrize(("anchor", "anchor_confidence", "source_confidence", "lost", "review"), [
    ("turn:9", .98, .99, 45, 0),
    ("unclear", .18, .99, 45, 0),
    ("turn:9", .98, .20, 40, 5),
])
def test_transfer_swap_through_decisions_and_command(monkeypatch, anchor, anchor_confidence,
                                                    source_confidence, lost, review):
    rules_dir = Path(os.getenv("RULES_DIR", Path(__file__).resolve().parents[2] / "docs/procedures/schema3"))
    rules = json.loads((rules_dir / "transfer_money.json").read_text(encoding="utf-8"))
    amount, source, destination = (f["key"] for f in rules["fields"])
    turns = {
        2: "Welcome to Harper Valley National Bank, this is Alex. How may I help?",
        6: "What is the transfer amount?",
        7: "Move 114 dollars from my checking account to my savings account.",
        9: "Okay, that was from your savings to your checking account.",
        13: "I've moved 114 dollars from savings to checking. Anything else I can help with?",
        16: "Thank you for calling, have a great day.",
    }
    call = CallForEvaluation(1, required_steps(rules), turns, (2, 6, 9, 13, 16),
                             {"task_type": "transfer money", amount: "114", source: "savings", destination: "checking"},
                             field_types={f["key"]: f["type"] for f in rules["fields"]})
    store = RecordingStore(call)
    model = OpenAIDecisionModel("unit-test")
    observations = iter(["turn:2", "turn:6", "turn:7", "turn:7", anchor, "turn:13", "turn:16"])
    fields = {
        f"request:{amount}": ("114", .98), f"read_back:{amount}": ("114", .98),
        f"request:{source}": ("checking", .99), f"read_back:{source}": ("savings", source_confidence),
        f"request:{destination}": ("savings", .99), f"read_back:{destination}": ("checking", .99),
    }

    def reply(body):
        observed = next(observations) if any(q["name"] == "step_observation" for q in body["questions"]) else None
        answers = []
        for question in body["questions"]:
            name = question["name"]
            if name == "step_observation":
                choice, confidence = observed, anchor_confidence if observed == anchor else .99
            else:
                choice, confidence = fields[name]
            assert choice in {option["value"] for option in question["choices"]}
            answers.append({"type": "choice", "name": name, "choice": choice, "confidence": confidence})
        return {"answers": answers}

    monkeypatch.setattr(model, "_post", reply)
    output = asyncio.run(evaluate_one(EvaluateOrderedCallInteractor(store, model, AnalyzePresenter()), 1))
    assert (output.completed, output.wrong, output.missed, output.under_review) == (6, 1, 0, 0)
    submit = store.results["submit_and_confirm_transfer"]
    assert (submit.status, submit.points_lost, submit.points_under_review) == ("wrong", lost, review)
    assert (submit.evidence.turn_idx if submit.evidence else None) == (9 if anchor == "turn:9" else None)
    assert store.results["collect_source_account"].evidence.turn_idx == 7
    assert store.results["collect_destination_account"].evidence.turn_idx == 7
