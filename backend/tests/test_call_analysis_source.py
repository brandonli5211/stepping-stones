import asyncio
from types import SimpleNamespace as Row

from sqlalchemy.dialects import postgresql

from app.adapters.persistence.call_analysis_source import (
    SqlAlchemyCallAnalysisSource,
    call_query,
    to_call,
    turns_query,
)
from app.domain.call_analysis import CallToAnalyze

ROW = Row(id=5, external_id="abc", call_type="pay_bill", raw_metadata={"m": 1},
          raw_transcript=[{"speaker_role": "agent"}], rules={"r": 1})


def sql(stmt):
    return str(stmt.compile(dialect=postgresql.dialect())).replace("\n", " ")


class Result:
    def __init__(self, rows):
        self.rows = rows

    def first(self):
        return self.rows[0] if self.rows else None

    def all(self):
        return self.rows


class FakeSession:
    def __init__(self, rows):
        self.rows, self.statements = rows, []

    async def execute(self, stmt):
        self.statements.append(stmt)
        return Result(self.rows)


def test_call_query_joins_procedure_and_filters_by_id():
    text = sql(call_query(5))
    assert "procedures.rules" in text and "calls.raw_transcript" in text and "calls.raw_metadata" in text
    assert "JOIN procedures ON procedures.id = calls.procedure_id" in text
    assert "WHERE calls.id = " in text


def test_turns_query_orders_by_idx():
    text = sql(turns_query(5))
    assert "call_turns.speaker, call_turns.text" in text
    assert "WHERE call_turns.call_id = " in text and "ORDER BY call_turns.idx" in text


def test_to_call_maps_row_or_none():
    assert to_call(ROW) == CallToAnalyze(5, "abc", "pay_bill", {"m": 1}, [{"speaker_role": "agent"}], {"r": 1})
    assert to_call(None) is None


def test_load_returns_call_or_none():
    assert asyncio.run(SqlAlchemyCallAnalysisSource(FakeSession([ROW])).load(5)).external_id == "abc"
    assert asyncio.run(SqlAlchemyCallAnalysisSource(FakeSession([])).load(5)) is None


def test_turns_returns_pairs_in_order():
    rows = [Row(speaker="agent", text="Hi"), Row(speaker="caller", text="Hello")]
    assert asyncio.run(SqlAlchemyCallAnalysisSource(FakeSession(rows)).turns(5)) == [("agent", "Hi"), ("caller", "Hello")]
