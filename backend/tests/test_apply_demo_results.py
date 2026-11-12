import ast
import asyncio
from pathlib import Path

import pytest

import app.application.apply_demo_results as use_case_module
import app.application.ports as ports_module
from app.application.apply_demo_results import ApplyDemoResults, ApplyOutcome
from app.domain.demo_results import ResultsRow, SeverityBand, StoredCall, StoredStep, parse_step_keys

BANDS = (SeverityBand("slip", 1, 5), SeverityBand("inaccuracy", 6, 10),
         SeverityBand("mistake", 11, 20), SeverityBand("critical", 21, None))

STEPS = (
    StoredStep("greet", "Greet", 5, "completed", None),
    StoredStep("submit", "Submit", 55, "completed", None),
    StoredStep("close", "Close", 40, "completed", None),
)


class FakeStore:
    def __init__(self, calls):
        self.calls = calls
        self.asked = None
        self.saved = None

    async def find_calls(self, external_ids):
        self.asked = list(external_ids)
        return {i: self.calls[i] for i in external_ids if i in self.calls}

    async def save_results(self, calls):
        self.saved = list(calls)


def row(demo_id, external_id, *, missed="", wrong="", call_type="transfer_money", date="2026-10-07", time="16:48"):
    return ResultsRow(demo_id, external_id, call_type, date, time, parse_step_keys(missed), parse_step_keys(wrong))


def store():
    return FakeStore({
        "c1": StoredCall("c1", "transfer_money", STEPS),
        "c2": StoredCall("c2", "transfer_money", STEPS),
        "bare": StoredCall("bare", "transfer_money", ()),
    })


def run(s, rows):
    return asyncio.run(ApplyDemoResults(store=s, bands=BANDS).execute(rows))


def test_valid_run_saves_every_scored_call():
    s = store()
    outcome = run(s, [row("D1", "c1", wrong="submit"), row("D2", "c2")])
    assert outcome == ApplyOutcome(updated=2, problems=(), saved=True)
    assert s.asked == ["c1", "c2"]
    assert [(c.external_id, c.score) for c in s.saved] == [("c1", 45), ("c2", 100)]


def test_outcome_as_dict():
    assert ApplyOutcome(1, ("x",), False).as_dict() == {"updated": 1, "problems": ["x"], "saved": False}


@pytest.mark.parametrize("bad,message", [
    (row("D9", "missing"), "D9: call not loaded"),
    (row("D9", "bare"), "D9: call has no rubric steps (load with --demo-results)"),
    (row("D9", "c2", wrong="nope"), "D9: unknown step nope"),
    (row("D9", "c2", missed="close", wrong="close"), "D9: step close is both missed and wrong"),
    (row("D9", "c2", call_type="pay_bill"), "D9: call_type pay_bill, loaded call is transfer_money"),
    (row("D9", "c2", date="2026-02-30"), "D9: bad date/time 2026-02-30 16:48"),
    (row("D9", "c1"), "D9: call c1 listed more than once"),
])
def test_any_bad_row_saves_nothing(bad, message):
    s = store()
    outcome = run(s, [row("D1", "c1", wrong="submit"), bad])
    assert outcome == ApplyOutcome(updated=0, problems=(message,), saved=False)
    assert s.saved is None


def test_all_problems_are_reported_together():
    s = store()
    outcome = run(s, [row("D1", "missing"), row("D2", "c1", wrong="nope"), row("D3", "c1")])
    assert outcome.problems == ("D3: call c1 listed more than once", "D1: call not loaded", "D2: unknown step nope")
    assert outcome.saved is False
    assert s.saved is None


def test_application_modules_import_no_framework_or_driver():
    for module in (use_case_module, ports_module):
        tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        assert not any(name.split(".", 1)[0] in {"fastapi", "sqlalchemy", "alembic", "psycopg"} for name in imported)
        assert not any(name.startswith(("app.adapters", "app.infrastructure")) for name in imported)
