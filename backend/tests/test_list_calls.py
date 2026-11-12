import ast
import asyncio
from datetime import date, datetime, timezone
from pathlib import Path

import app.application.list_calls as use_case_module
import app.application.ports as ports_module
from app.application.list_calls import ListCalls, ListCallsQuery
from app.domain.call_list import (
    CallRecord,
    CallResult,
    CallWindow,
    ListFilter,
    StepOutcome,
    WeekNumbers,
    WeekTotals,
)

DEMO = datetime(2026, 10, 9, 23, 59, 59, tzinfo=timezone.utc)


def record(id, *statuses):
    steps = tuple(StepOutcome(f"s{i}", f"Step {i}", s) for i, s in enumerate(statuses, 1))
    return CallRecord(id, f"ext{id}", "transfer_money", "Transfer money", DEMO, "scored", 90, 0, len(steps), steps)


class FakeClock:
    def __init__(self, instant):
        self.instant = instant
        self.calls = 0

    def now(self):
        self.calls += 1
        return self.instant


class FakeReader:
    def __init__(self, records=(), count=0, weeks=()):
        self.records, self.count, self.weeks = list(records), count, list(weeks)
        self.log = []

    async def recent_calls(self, window, filters, limit):
        self.log.append(("recent_calls", window, filters, limit))
        return self.records

    async def count_calls(self, window):
        self.log.append(("count_calls", window))
        return self.count

    async def week_totals(self, window):
        self.log.append(("week_totals", window))
        return self.weeks


def run(reader, clock, **query):
    return asyncio.run(ListCalls(reader=reader, clock=clock).execute(ListCallsQuery(**query)))


def test_window_and_filters_come_from_clock_and_query():
    reader, clock = FakeReader(), FakeClock(DEMO)
    run(reader, clock, weeks=8, agent_id=3, call_type=" Transfer Money ", has_missed=True, limit=100)
    window = CallWindow(since=datetime(2026, 8, 14, 23, 59, 59, tzinfo=timezone.utc), agent_id=3)
    assert reader.log == [
        ("recent_calls", window, ListFilter("transfer_money", True), 100),
        ("count_calls", window),
        ("week_totals", window),
    ]
    assert clock.calls == 1


def test_empty_call_type_means_no_filter():
    reader = FakeReader()
    run(reader, FakeClock(DEMO), call_type="")
    assert reader.log[0][2] == ListFilter(None, False)
    assert reader.log[0][1] == CallWindow(None, None)


def test_header_numbers_from_week_totals():
    weeks = [WeekTotals(date(2026, 8, 17), 16, 25), WeekTotals(date(2026, 10, 5), 53, 59)]
    result = run(FakeReader(count=48, weeks=weeks), FakeClock(DEMO), weeks=8)
    assert result.summary.calls_reviewed == 48
    assert result.summary.weeks == 8
    assert result.summary.this_week == WeekNumbers(53, 59, 90)
    assert result.summary.first_week_percent == 64


def test_header_this_week_empty_with_real_time_outside_data():
    weeks = [WeekTotals(date(2026, 10, 5), 53, 59)]
    result = run(FakeReader(weeks=weeks), FakeClock(datetime(2026, 11, 11, tzinfo=timezone.utc)))
    assert result.summary.this_week is None
    assert result.summary.first_week_percent == 90


def test_labels_attached_in_record_order():
    records = [record(2, "completed", "wrong"), record(1, "missed"), record(3, "completed")]
    result = run(FakeReader(records=records), FakeClock(DEMO))
    assert [c.record.id for c in result.calls] == [2, 1, 3]
    assert [c.result for c in result.calls] == [
        CallResult("Wrong: Step 2", "wrong"), CallResult("Missed Step 1", "missed"), None]


def test_application_modules_import_nothing_outer():
    for module in (use_case_module, ports_module):
        tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        assert not any(n.split(".", 1)[0] in {"fastapi", "sqlalchemy", "alembic", "psycopg", "os"} for n in imported)
        assert not any(n.startswith(("app.adapters", "app.infrastructure")) for n in imported)
