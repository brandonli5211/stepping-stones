import asyncio
from datetime import date, datetime, timezone
from types import SimpleNamespace as Row

from sqlalchemy.dialects import postgresql

from app.adapters.persistence.call_list_reader import (
    SqlAlchemyCallListReader,
    count_query,
    list_clauses,
    recent_calls_query,
    steps_query,
    to_records,
    week_totals_query,
    window_clauses,
)
from app.domain.call_list import CallRecord, CallWindow, ListFilter, StepOutcome, WeekTotals

SINCE = datetime(2026, 8, 14, 23, 59, 59, tzinfo=timezone.utc)
STARTED = datetime(2026, 10, 7, 20, 48, tzinfo=timezone.utc)


def sql(stmt):
    return str(stmt.compile(dialect=postgresql.dialect())).replace("\n", " ")


def call_row(id, external_id="e"):
    return Row(id=id, external_id=f"{external_id}{id}", call_type="transfer_money", name="Transfer money",
               started_at=STARTED, status="scored", score=45, steps_completed=6, steps_total=7)


class Result:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class FakeSession:
    def __init__(self, results=(), scalar=None):
        self.results = list(results)
        self.scalar_value = scalar
        self.statements = []

    async def execute(self, stmt):
        self.statements.append(stmt)
        return Result(self.results.pop(0))

    async def scalar(self, stmt):
        self.statements.append(stmt)
        return self.scalar_value


# clause builders and queries

def test_window_clauses():
    assert window_clauses(CallWindow(None, None)) == []
    assert len(window_clauses(CallWindow(SINCE, None))) == 1
    assert len(window_clauses(CallWindow(SINCE, 4))) == 2


def test_list_clauses_add_call_type_and_has_missed_only_when_set():
    assert len(list_clauses(CallWindow(None, None), ListFilter(None, False))) == 0
    assert len(list_clauses(CallWindow(SINCE, 4), ListFilter("transfer_money", True))) == 4


def test_recent_calls_query_sql():
    text = sql(recent_calls_query(CallWindow(SINCE, 4), ListFilter("transfer_money", True), 100))
    assert "JOIN procedures ON procedures.id = calls.procedure_id" in text
    assert "calls.started_at >= " in text and "calls.agent_id = " in text
    assert "calls.call_type = " in text and "calls.steps_missed + calls.steps_wrong > " in text
    assert "ORDER BY calls.started_at DESC, calls.id DESC" in text and "LIMIT " in text


def test_recent_calls_query_without_filters_has_no_where():
    assert "WHERE" not in sql(recent_calls_query(CallWindow(None, None), ListFilter(None, False), 10))


def test_steps_query_sql():
    text = sql(steps_query([1, 2]))
    assert "call_steps.call_id IN" in text
    assert "ORDER BY call_steps.call_id, call_steps.position" in text


def test_count_query_uses_window_only():
    text = sql(count_query(CallWindow(SINCE, None)))
    assert "count(*)" in text and "calls.started_at >= " in text and "call_type" not in text


def test_week_totals_query_groups_by_utc_week():
    text = sql(week_totals_query(CallWindow(SINCE, None)))
    assert "date_trunc(%(date_trunc_1)s, calls.started_at AT TIME ZONE %(started_at_1)s)" in text
    assert "GROUP BY date_trunc" in text and "ORDER BY date_trunc" in text
    compiled = week_totals_query(CallWindow(None, None)).compile(dialect=postgresql.dialect())
    assert set(compiled.params.values()) == {"week", "UTC"}


# mapping

def test_to_records_groups_steps_per_call_in_order():
    rows = [call_row(2), call_row(1)]
    step_rows = [Row(call_id=1, step_key="a", name="A", status="missed"),
                 Row(call_id=2, step_key="b", name="B", status="completed"),
                 Row(call_id=2, step_key="c", name="C", status="wrong")]
    records = to_records(rows, step_rows)
    assert [r.id for r in records] == [2, 1]
    assert records[0] == CallRecord(2, "e2", "transfer_money", "Transfer money", STARTED, "scored", 45, 6, 7,
                                    (StepOutcome("b", "B", "completed"), StepOutcome("c", "C", "wrong")))
    assert records[1].steps == (StepOutcome("a", "A", "missed"),)


# reader methods

def test_recent_calls_runs_both_queries():
    session = FakeSession(results=[[call_row(1)], [Row(call_id=1, step_key="a", name="A", status="completed")]])
    records = asyncio.run(SqlAlchemyCallListReader(session).recent_calls(CallWindow(None, None), ListFilter(None, False), 10))
    assert [r.external_id for r in records] == ["e1"]
    assert len(session.statements) == 2


def test_recent_calls_skips_step_query_without_calls():
    session = FakeSession(results=[[]])
    assert asyncio.run(SqlAlchemyCallListReader(session).recent_calls(CallWindow(None, None), ListFilter(None, False), 10)) == []
    assert len(session.statements) == 1


def test_count_calls_returns_scalar():
    session = FakeSession(scalar=48)
    assert asyncio.run(SqlAlchemyCallListReader(session).count_calls(CallWindow(SINCE, None))) == 48


def test_week_totals_maps_dates_and_ints():
    session = FakeSession(results=[[Row(week=datetime(2026, 10, 5), done=53, total=59)]])
    assert asyncio.run(SqlAlchemyCallListReader(session).week_totals(CallWindow(None, None))) == [
        WeekTotals(date(2026, 10, 5), 53, 59)]
