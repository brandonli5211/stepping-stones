import asyncio
from collections import defaultdict
from datetime import UTC, datetime

from app.adapters.http.progress.presenter import GetProgressPresenter
from app.adapters.http.progress.view_model import ProgressViewModel
from app.application.get_progress.input_data import GetProgressInputData
from app.application.get_progress.interactor import GetProgressInteractor
from app.domain.call_list import WeekTotals, week_monday
from app.domain.progress import CallTypeTotals, StepResult
from app.infrastructure.clock import FixedClock

NOW = datetime(2026, 10, 9, 12, tzinfo=UTC)
NAMES = {"replace_card": "Replace card", "pay_bill": "Pay bill"}
STEP_NAMES = {"greet": "Greet and open", "confirm": "Confirm replacement", "amount": "Collect amount", "close": "Close"}
CALLS = [
    (1, datetime(2026, 9, 22, tzinfo=UTC), "replace_card",
     {"greet": "completed", "confirm": "missed", "close": "completed"}),
    (2, datetime(2026, 9, 24, tzinfo=UTC), "pay_bill",
     {"greet": "completed", "amount": "completed", "close": "completed"}),
    (3, datetime(2026, 9, 29, tzinfo=UTC), "replace_card",
     {"greet": "completed", "confirm": "wrong", "close": "completed"}),
    (4, datetime(2026, 9, 30, tzinfo=UTC), "replace_card",
     {"greet": "completed", "confirm": "under_review", "close": "completed"}),
    (5, datetime(2026, 10, 6, tzinfo=UTC), "pay_bill",
     {"greet": "completed", "amount": "missed", "close": "completed"}),
    (6, datetime(2026, 10, 7, tzinfo=UTC), "replace_card",
     {"greet": "completed", "confirm": "completed", "close": "completed"}),
]


class FakeProgressData:
    # like the SQL: a step under review is not required
    @staticmethod
    def _sums(calls):
        done = sum(s == "completed" for _, _, _, steps in calls for s in steps.values())
        return done, sum(s != "under_review" for _, _, _, steps in calls for s in steps.values())

    async def week_totals(self, window):
        weeks = defaultdict(list)
        for call in CALLS:
            weeks[week_monday(call[1])].append(call)
        return [WeekTotals(week, *self._sums(calls)) for week, calls in sorted(weeks.items())]

    async def call_type_totals(self, window):
        types = defaultdict(list)
        for call in CALLS:
            types[call[2]].append(call)
        return [CallTypeTotals(key, NAMES[key], *self._sums(calls), len(calls)) for key, calls in types.items()]

    async def step_results(self, window):
        return [StepResult(call_id, started, call_type, NAMES[call_type], key, STEP_NAMES[key], position, status)
                for call_id, started, call_type, steps in CALLS
                for position, (key, status) in enumerate(steps.items(), 1)]

    async def has_demo_calls(self, window):
        return False


class FixedSharedSteps:
    async def load(self):
        return frozenset({"greet", "close"})


def test_progress_small_dataset():
    view_model = ProgressViewModel()
    interactor = GetProgressInteractor(data=FakeProgressData(), shared_steps=FixedSharedSteps(), clock=FixedClock(NOW),
                                       presenter=GetProgressPresenter(view_model))

    asyncio.run(interactor.execute(GetProgressInputData()))
    body = view_model.body()

    assert [w["percent"] for w in body["weeks"]] == [None, None, None, None, None, 83, 80, 83]
    assert [(w["steps_completed"], w["steps_total"]) for w in body["weeks"][5:]] == [(5, 6), (4, 5), (5, 6)]
    assert body["this_week"] == {"steps_completed": 5, "steps_total": 6, "percent": 83}
    assert body["comparison"] == "Same as 83% in week 1"
    assert [(t["name"], t["steps_completed"], t["steps_total"], t["percent"]) for t in body["call_types"]] == [
        ("Pay bill", 5, 6, 83), ("Replace card", 9, 11, 82)]

    top = body["steps"][0]
    assert (top["name"], top["label"], top["misses"]) == ("Confirm replacement", "Replace card", 2)
    assert top["results"] == ["missed", "wrong", "completed"]
    assert top["summary"] == "Missed on 2 of your last 3 replace-card calls"
    assert not [s for s in body["steps"] if "under_review" in s["results"]]
