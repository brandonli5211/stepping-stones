import asyncio
from datetime import datetime, timezone

import pytest
from sqlalchemy.dialects import postgresql

from app.adapters.persistence.demo_call_store import (
    FIND_CALLS,
    UPDATE_CALL,
    UPDATE_STEP,
    SqlAlchemyDemoCallStore,
    call_params,
    step_params,
    to_stored_calls,
)
from app.domain.demo_results import ScoredCall, ScoredStep, StoredCall, StoredStep

STARTED = datetime(2026, 10, 7, 20, 48, tzinfo=timezone.utc)


def scored(external_id="a2f", steps=None):
    steps = steps if steps is not None else (
        ScoredStep("greet", "completed", "none", 0, "kept"),
        ScoredStep("submit", "wrong", "critical", 55, None),
    )
    return ScoredCall(external_id, STARTED, 45, 55, 2, 1, 0, 1, steps)


class FakeResult:
    def __init__(self, rows=None, scalar=None):
        self._rows, self._scalar = rows or [], scalar

    def all(self):
        return self._rows

    def scalar_one(self):
        return self._scalar


class FakeSession:
    def __init__(self, rows=None, call_ids=None, fail_on=None):
        self.rows = rows or []
        self.call_ids = call_ids or {}
        self.fail_on = fail_on
        self.executed = []
        self.transaction_calls = []

    async def execute(self, stmt, params=None):
        self.executed.append((stmt, params))
        if stmt is self.fail_on:
            raise RuntimeError("database error")
        if stmt is FIND_CALLS:
            return FakeResult(rows=self.rows)
        if stmt is UPDATE_CALL:
            return FakeResult(scalar=self.call_ids[params["b_external_id"]])
        return FakeResult()

    def begin(self):
        self.transaction_calls.append("begin")

    async def commit(self):
        self.transaction_calls.append("commit")

    async def rollback(self):
        self.transaction_calls.append("rollback")


# pure mapping helpers

def test_to_stored_calls_groups_steps_in_order_and_keeps_calls_without_steps():
    rows = [
        ("a2f", "transfer_money", "greet", "Greet", 5, "completed", None),
        ("a2f", "transfer_money", "submit", "Submit", 55, "under_review", "note"),
        ("bare", "pay_bill", None, None, None, None, None),
    ]
    assert to_stored_calls(rows) == {
        "a2f": StoredCall("a2f", "transfer_money", (
            StoredStep("greet", "Greet", 5, "completed", None),
            StoredStep("submit", "Submit", 55, "under_review", "note"),
        )),
        "bare": StoredCall("bare", "pay_bill", ()),
    }


def test_call_params_carry_every_total():
    assert call_params(scored()) == {
        "b_external_id": "a2f", "b_started_at": STARTED, "b_score": 45, "b_points_lost": 55,
        "b_steps_total": 2, "b_steps_completed": 1, "b_steps_missed": 0, "b_steps_wrong": 1,
    }


def test_step_params_one_per_step_keyed_by_call_id():
    assert step_params(7, scored()) == [
        {"b_call_id": 7, "b_step_key": "greet", "b_status": "completed", "b_severity": "none",
         "b_points_lost": 0, "b_detail": "kept"},
        {"b_call_id": 7, "b_step_key": "submit", "b_status": "wrong", "b_severity": "critical",
         "b_points_lost": 55, "b_detail": None},
    ]


def test_statements_set_fixed_columns_and_are_keyed_by_call():
    sql_call = str(UPDATE_CALL.compile(dialect=postgresql.dialect()))
    sql_step = str(UPDATE_STEP.compile(dialect=postgresql.dialect()))
    assert "WHERE calls.external_id = " in sql_call and "RETURNING calls.id" in sql_call
    assert "status=" in sql_call.replace(" ", "") and "steps_under_review=" in sql_call.replace(" ", "")
    assert "WHERE call_steps.call_id = " in sql_step and "call_steps.step_key = " in sql_step
    for untouched in ("sub_checks", "comparison", "coaching", "evidence"):
        assert untouched not in sql_step


# store methods

def test_find_calls_maps_rows():
    session = FakeSession(rows=[("a2f", "transfer_money", "greet", "Greet", 5, "completed", None)])
    found = asyncio.run(SqlAlchemyDemoCallStore(session).find_calls(["a2f", "zzz"]))
    assert found == {"a2f": StoredCall("a2f", "transfer_money", (StoredStep("greet", "Greet", 5, "completed", None),))}
    assert session.executed == [(FIND_CALLS, {"external_ids": ["a2f", "zzz"]})]


def test_find_calls_with_no_ids_skips_the_query():
    session = FakeSession()
    assert asyncio.run(SqlAlchemyDemoCallStore(session).find_calls([])) == {}
    assert session.executed == []


def test_save_results_updates_only_listed_calls_without_managing_the_transaction():
    session = FakeSession(call_ids={"a2f": 7, "b3c": 9})
    asyncio.run(SqlAlchemyDemoCallStore(session).save_results([scored("a2f"), scored("b3c")]))
    assert [stmt for stmt, _ in session.executed] == [UPDATE_CALL, UPDATE_STEP, UPDATE_CALL, UPDATE_STEP]
    assert [p["b_external_id"] for stmt, p in session.executed if stmt is UPDATE_CALL] == ["a2f", "b3c"]
    step_batches = [p for stmt, p in session.executed if stmt is UPDATE_STEP]
    assert {row["b_call_id"] for row in step_batches[0]} == {7}
    assert {row["b_call_id"] for row in step_batches[1]} == {9}
    assert session.transaction_calls == []


def test_save_results_skips_step_update_for_call_without_steps():
    session = FakeSession(call_ids={"a2f": 7})
    asyncio.run(SqlAlchemyDemoCallStore(session).save_results([scored(steps=())]))
    assert [stmt for stmt, _ in session.executed] == [UPDATE_CALL]


def test_save_results_propagates_database_errors():
    session = FakeSession(call_ids={"a2f": 7}, fail_on=UPDATE_STEP)
    with pytest.raises(RuntimeError, match="database error"):
        asyncio.run(SqlAlchemyDemoCallStore(session).save_results([scored()]))
    assert session.transaction_calls == []
