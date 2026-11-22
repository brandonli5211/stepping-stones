import asyncio
from collections import defaultdict

from demo_48_data import DEMO_TODAY, RULES, load_demo_48

from app.adapters.files.shared_steps import JsonSharedSteps
from app.adapters.http.progress.presenter import GetProgressPresenter
from app.adapters.http.progress.view_model import ProgressViewModel
from app.application.get_progress.input_data import GetProgressInputData
from app.application.get_progress.interactor import GetProgressInteractor
from app.domain.call_list import WeekTotals, week_monday
from app.domain.progress import RESOLVED, CallTypeTotals, StepResult
from app.infrastructure.clock import FixedClock


class MemoryProgressData:
    def __init__(self, stored, scored, names):
        self.stored, self.scored, self.names = stored, scored, names

    def _inside(self, window):
        return [c for c in self.scored if window.since <= c.started_at < window.until]

    async def week_totals(self, window):
        weeks = defaultdict(lambda: [0, 0])
        for call in self._inside(window):
            weeks[week_monday(call.started_at)][0] += call.steps_completed
            weeks[week_monday(call.started_at)][1] += call.steps_total
        return [WeekTotals(week, done, total) for week, (done, total) in sorted(weeks.items())]

    async def call_type_totals(self, window):
        types = defaultdict(lambda: [0, 0, 0])
        for call in self._inside(window):
            totals = types[self.stored[call.external_id].call_type]
            totals[0] += call.steps_completed
            totals[1] += call.steps_total
            totals[2] += 1
        return [CallTypeTotals(key, self.names[key], *t) for key, t in sorted(types.items())]

    async def step_results(self, window):
        results = []
        for call_id, call in enumerate(sorted(self._inside(window), key=lambda c: c.started_at), 1):
            seeded = self.stored[call.external_id]
            step_names = {s.key: s.name for s in seeded.steps}
            results += [StepResult(call_id, call.started_at, seeded.call_type, self.names[seeded.call_type],
                                   step.key, step_names[step.key], position, step.status)
                        for position, step in enumerate(call.steps, 1) if step.status in RESOLVED]
        return results

    async def has_demo_calls(self, window):
        return bool(self._inside(window))


def test_progress_demo_48():
    _, stored, scored, names = load_demo_48()
    view_model = ProgressViewModel()
    interactor = GetProgressInteractor(data=MemoryProgressData(stored, scored, names), shared_steps=JsonSharedSteps(RULES),
                                       clock=FixedClock(DEMO_TODAY), presenter=GetProgressPresenter(view_model))

    asyncio.run(interactor.execute(GetProgressInputData()))
    body = view_model.body()

    assert view_model.error is None
    assert [(w["week_start"], w["steps_completed"], w["steps_total"], w["percent"]) for w in body["weeks"]] == [
        ("2026-08-17", 16, 25, 64), ("2026-08-24", 16, 23, 70), ("2026-08-31", 17, 25, 68),
        ("2026-09-07", 24, 32, 75), ("2026-09-14", 45, 56, 80), ("2026-09-21", 31, 39, 79),
        ("2026-09-28", 19, 22, 86), ("2026-10-05", 53, 59, 90),
    ]
    assert [w["is_current"] for w in body["weeks"]] == [False] * 7 + [True]
    assert body["this_week"] == {"steps_completed": 53, "steps_total": 59, "percent": 90}
    assert body["first_week_percent"] == 64
    assert body["comparison"] == "Up from 64% in week 1"
    assert body["demo_data"] is True
    # the real demo values, not Figma's 97..78
    assert [(t["name"], t["percent"], t["calls"]) for t in body["call_types"]] == [
        ("Check balance", 88, 8), ("Get branch hours", 86, 7), ("Order checks", 85, 4), ("Reset password", 80, 5),
        ("Pay bill", 79, 4), ("Schedule appointment", 77, 5), ("Replace card", 73, 8), ("Transfer money", 69, 7),
    ]

    steps = body["steps"]
    short = {"completed": "o", "missed": "M", "wrong": "W"}
    assert len(steps) == 26
    assert [s["misses"] > 0 for s in steps] == [True] * 13 + [False] * 13
    assert [(s["name"], s["label"], "".join(short[r] for r in s["results"]), s["summary"]) for s in steps[:13]] == [
        ("Confirm replacement", "Replace card", "oMoMM", "Missed on 3 of your last 5 replace-card calls"),
        ("Confirm appointment", "Schedule appointment", "MMooM",
         "Missed on 3 of your last 5 schedule-appointment calls"),
        ("Offer further help", "All call types", "ooooooMooM", "Missed on 2 of your last 10 calls"),
        ("State account balance", "Check balance", "ooMMo", "Missed on 2 of your last 5 check-balance calls"),
        ("Collect company address", "Pay bill", "MMoo", "Missed on 2 of your last 4 pay-bill calls"),
        ("Collect time", "Schedule appointment", "oMooM", "Missed on 2 of your last 5 schedule-appointment calls"),
        ("Collect source account", "Transfer money", "MooMo", "Missed on 2 of your last 5 transfer-money calls"),
        ("Submit and confirm transfer", "Transfer money", "oMooW", "Missed on 2 of your last 5 transfer-money calls"),
        ("Collect home address", "Order checks", "Mooo", "Missed on 1 of your last 4 order-checks calls"),
        ("Collect payment amount", "Pay bill", "Mooo", "Missed on 1 of your last 4 pay-bill calls"),
        ("Collect phone number", "Reset password", "ooMoo", "Missed on 1 of your last 5 reset-password calls"),
        ("Collect transfer amount", "Transfer money", "oooMo", "Missed on 1 of your last 5 transfer-money calls"),
        ("Collect destination account", "Transfer money", "oooMo", "Missed on 1 of your last 5 transfer-money calls"),
    ]
    assert all(s["window"] == 10 for s in steps if s["call_type"] is None)
    assert all(s["summary"].startswith("Done on all of your last ") for s in steps[13:])
