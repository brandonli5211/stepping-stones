import asyncio
import inspect
from datetime import datetime, timezone
from types import SimpleNamespace

import app.adapters.http.calls as calls_module
from app.adapters.http.calls import get_list_calls, list_calls, present_call_list
from app.adapters.persistence.call_list_reader import SqlAlchemyCallListReader
from app.application.list_calls import ListCalls, ListCallsQuery
from app.domain.call_list import (
    CallList,
    CallRecord,
    CallResult,
    CallSummary,
    ListHeader,
    StepOutcome,
    WeekNumbers,
)
from app.infrastructure.clock import FixedClock

STARTED = datetime(2026, 10, 7, 20, 48, tzinfo=timezone.utc)

SAMPLE = CallList(
    summary=ListHeader(calls_reviewed=48, weeks=8, this_week=WeekNumbers(53, 59, 90), first_week_percent=64),
    calls=(
        CallSummary(
            record=CallRecord(7, "a2f086d27b3a4f96", "transfer_money", "Transfer money", STARTED, "scored", 45, 6, 7,
                              (StepOutcome("greet_and_open", "Greet and open", "completed"),
                               StepOutcome("submit_and_confirm_transfer", "Submit and confirm transfer", "wrong"))),
            result=CallResult("Wrong: Submit and confirm transfer", "wrong"),
        ),
        CallSummary(
            record=CallRecord(8, "x", "pay_bill", "Pay bill", STARTED, "pending", None, 0, 0, ()),
            result=None,
        ),
    ),
)


def test_present_call_list_exact_shape_and_key_order():
    body = present_call_list(SAMPLE)
    assert body == {
        "summary": {"calls_reviewed": 48, "weeks": 8,
                    "this_week": {"steps_completed": 53, "steps_total": 59, "percent": 90},
                    "first_week_percent": 64},
        "calls": [
            {"id": 7, "external_id": "a2f086d27b3a4f96", "call_type": "transfer_money",
             "call_type_name": "Transfer money", "started_at": STARTED, "status": "scored", "score": 45,
             "steps_completed": 6, "steps_total": 7,
             "steps": [{"key": "greet_and_open", "name": "Greet and open", "status": "completed"},
                       {"key": "submit_and_confirm_transfer", "name": "Submit and confirm transfer", "status": "wrong"}],
             "result": {"label": "Wrong: Submit and confirm transfer", "status": "wrong"}},
            {"id": 8, "external_id": "x", "call_type": "pay_bill", "call_type_name": "Pay bill",
             "started_at": STARTED, "status": "pending", "score": None, "steps_completed": 0, "steps_total": 0,
             "steps": [], "result": None},
        ],
    }
    assert list(body) == ["summary", "calls"]
    assert list(body["summary"]) == ["calls_reviewed", "weeks", "this_week", "first_week_percent"]
    assert list(body["calls"][0]) == ["id", "external_id", "call_type", "call_type_name", "started_at", "status",
                                      "score", "steps_completed", "steps_total", "steps", "result"]


def test_present_call_list_empty_this_week():
    empty = CallList(ListHeader(0, None, None, None), ())
    assert present_call_list(empty) == {
        "summary": {"calls_reviewed": 0, "weeks": None, "this_week": None, "first_week_percent": None}, "calls": []}


class FakeUseCase:
    def __init__(self):
        self.queries = []

    async def execute(self, query):
        self.queries.append(query)
        return SAMPLE


def test_handler_builds_query_and_delegates():
    use_case = FakeUseCase()
    body = asyncio.run(list_calls(agent_id=3, call_type="Transfer Money", has_missed=True, limit=100, weeks=8,
                                  use_case=use_case))
    assert use_case.queries == [ListCallsQuery(agent_id=3, call_type="Transfer Money", has_missed=True, limit=100, weeks=8)]
    assert body == present_call_list(SAMPLE)


def test_handler_holds_no_sql_or_configuration():
    source = inspect.getsource(calls_module.list_calls)
    for forbidden in ("select(", "execute(session", "session.", "os.environ", "DEMO_TODAY", "timedelta"):
        assert forbidden not in source
    assert inspect.iscoroutinefunction(calls_module.list_calls)


def test_get_list_calls_wires_reader_and_app_clock():
    clock = FixedClock(STARTED)
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(clock=clock)))
    session = object()
    use_case = asyncio.run(get_list_calls(request, session))
    assert isinstance(use_case, ListCalls)
    assert isinstance(use_case.reader, SqlAlchemyCallListReader)
    assert use_case.reader._session is session
    assert use_case.clock is clock


def test_main_app_routes():
    from app.main import app

    routes = [(r.path, sorted(r.methods)) for r in app.routes if hasattr(r, "methods")]
    assert routes.count(("/calls", ["GET"])) == 1
    assert ("/calls/{call_id}", ["POST"]) in routes
    assert ("/api/health", ["GET"]) in routes
