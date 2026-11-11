import asyncio
from collections import defaultdict

from demo_48_data import DEMO_TODAY, load_demo_48

from app.application.list_calls import ListCalls, ListCallsQuery
from app.domain.call_list import CallRecord, StepOutcome, WeekTotals, week_monday
from app.infrastructure.clock import FixedClock


class MemoryCallListReader:
    def __init__(self, stored, scored, names):
        self.records = []
        for call_id, call in enumerate(sorted(scored, key=lambda c: c.started_at), 1):
            seeded = stored[call.external_id]
            step_names = {s.key: s.name for s in seeded.steps}
            self.records.append(CallRecord(
                call_id, call.external_id, seeded.call_type, names[seeded.call_type], call.started_at, "scored",
                call.score, call.steps_completed, call.steps_total,
                tuple(StepOutcome(s.key, step_names[s.key], s.status) for s in call.steps)))

    def _inside(self, window):
        return [r for r in self.records if window.since is None or r.started_at >= window.since]

    async def recent_calls(self, window, filters, limit):
        rows = [r for r in self._inside(window) if not filters.call_type or r.call_type == filters.call_type]
        return sorted(rows, key=lambda r: (r.started_at, r.id), reverse=True)[:limit]

    async def count_calls(self, window):
        return len(self._inside(window))

    async def week_totals(self, window):
        weeks = defaultdict(lambda: [0, 0])
        for r in self._inside(window):
            weeks[week_monday(r.started_at)][0] += r.steps_completed
            weeks[week_monday(r.started_at)][1] += r.steps_total
        return [WeekTotals(week, done, total) for week, (done, total) in sorted(weeks.items())]


def test_demo_48_numbers():
    outcome, stored, scored, names = load_demo_48()

    assert (outcome.updated, outcome.problems, outcome.saved) == (48, (), True)
    assert sum(len(c.steps) for c in scored) == 281
    transfer = next(c for c in scored if c.external_id == "a2f086d27b3a4f96")
    assert (transfer.score, transfer.points_lost, transfer.steps_wrong) == (45, 55, 1)

    reader = MemoryCallListReader(stored, scored, names)
    listed = asyncio.run(ListCalls(reader=reader, clock=FixedClock(DEMO_TODAY)).execute(ListCallsQuery(limit=100, weeks=8)))

    assert listed.summary.calls_reviewed == 48
    week = listed.summary.this_week
    assert (week.steps_completed, week.steps_total, week.percent) == (53, 59, 90)
    assert listed.summary.first_week_percent == 64
    row = next(c for c in listed.calls if c.record.external_id == "a2f086d27b3a4f96")
    assert row.result.label == "Wrong: Submit and confirm transfer"
