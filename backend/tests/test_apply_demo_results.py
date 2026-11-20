import asyncio

import pytest

from app.application.apply_demo_results import ApplyDemoResults, ApplyOutcome
from app.domain.demo_results import ResultsRow, SeverityBand, StoredCall, StoredStep, parse_step_keys

BANDS = (SeverityBand("slip", 1, 5), SeverityBand("inaccuracy", 6, 10),
         SeverityBand("mistake", 11, 20), SeverityBand("critical", 21, None))
STEPS = (StoredStep("greet", "Greet", 5, "completed", None), StoredStep("submit", "Submit", 55, "completed", None),
         StoredStep("close", "Close", 40, "completed", None))
QUOTE = "okay and that was from your savings to your checking account"


class FakeStore:
    def __init__(self):
        self.calls = {"c1": StoredCall("c1", "transfer_money", STEPS), "c2": StoredCall("c2", "transfer_money", STEPS),
                      "bare": StoredCall("bare", "transfer_money", ())}
        self.turns = {"c2": {1: "hello", 9: QUOTE}}
        self.saved = None

    async def find_calls(self, external_ids):
        return {i: self.calls[i] for i in external_ids if i in self.calls}

    async def find_turns(self, external_ids):
        return {i: self.turns[i] for i in external_ids if i in self.turns}

    async def save_results(self, calls):
        self.saved = list(calls)


def row(demo_id, external_id, missed="", wrong="", call_type="transfer_money", date="2026-10-07", evidence=("", "", "")):
    return ResultsRow(demo_id, external_id, call_type, date, "16:48", parse_step_keys(missed), parse_step_keys(wrong),
                      *evidence)


@pytest.mark.parametrize("bad,problem", [
    (row("D9", "missing"), "D9: call not loaded"),
    (row("D9", "bare"), "D9: call has no rubric steps (load with --demo-results)"),
    (row("D9", "c2", wrong="nope"), "D9: unknown step nope"),
    (row("D9", "c2", missed="close", wrong="close"), "D9: step close is both missed and wrong"),
    (row("D9", "c2", call_type="pay_bill"), "D9: call_type pay_bill, loaded call is transfer_money"),
    (row("D9", "c2", date="2026-02-30"), "D9: bad date/time 2026-02-30 16:48"),
    (row("D9", "c1"), "D9: call c1 listed more than once"),
    (row("D9", "c2", wrong="submit", evidence=("submit", "9", "")),
     "D9: evidence needs evidence_step, evidence_turn and evidence_quote"),
    (row("D9", "c2", wrong="submit", evidence=("submit", "x", QUOTE)), "D9: bad evidence turn x"),
    (row("D9", "c2", wrong="submit", evidence=("close", "9", QUOTE)), "D9: evidence step close is not missed or wrong"),
    (row("D9", "c2", wrong="submit", evidence=("submit", "12", QUOTE)), "D9: call has no turn 12"),
    (row("D9", "c2", wrong="submit", evidence=("submit", "9", QUOTE.replace("savings", "saving"))),
     "D9: quote not in turn 9"),
], ids=["missing", "no-steps", "unknown-step", "missed-and-wrong", "call-type", "bad-date", "duplicate",
        "evidence-partial", "evidence-turn", "evidence-step", "evidence-no-turn", "evidence-quote"])
def test_bad_file_saves_nothing(bad, problem):
    store = FakeStore()

    outcome = asyncio.run(ApplyDemoResults(store=store, bands=BANDS).execute([row("D1", "c1", wrong="submit"), bad]))

    assert outcome == ApplyOutcome(updated=0, problems=(problem,), saved=False)
    assert store.saved is None
