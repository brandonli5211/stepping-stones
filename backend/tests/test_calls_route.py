from datetime import datetime, timezone

from app.adapters.http.calls import present_call_list
from app.domain.call_list import CallList, CallRecord, CallResult, CallSummary, ListHeader, StepOutcome, WeekNumbers
from app.infrastructure.clock import SystemClock, clock_from_env

STARTED = datetime(2026, 10, 7, 20, 48, tzinfo=timezone.utc)
CALLS = CallList(
    summary=ListHeader(calls_reviewed=48, weeks=8, this_week=WeekNumbers(53, 59, 90), first_week_percent=64),
    calls=(
        CallSummary(
            record=CallRecord(7, "a2f086d27b3a4f96", "transfer_money", "Transfer money", STARTED, "scored", 45, 6, 7,
                              (StepOutcome("greet_and_open", "Greet and open", "completed"),
                               StepOutcome("submit_and_confirm_transfer", "Submit and confirm transfer", "wrong"))),
            result=CallResult("Wrong: Submit and confirm transfer", "wrong"),
        ),
        CallSummary(record=CallRecord(8, "x", "pay_bill", "Pay bill", STARTED, "pending", None, 0, 0, ()), result=None),
    ),
)


def test_calls_body_without_demo_today():
    assert isinstance(clock_from_env({}), SystemClock)
    assert isinstance(clock_from_env({"DEMO_TODAY": "  "}), SystemClock)

    body = present_call_list(CALLS)

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
    # dict equality ignores order, and the old route's key order is part of the response
    assert list(body) == ["summary", "calls"]
    assert list(body["summary"]) == ["calls_reviewed", "weeks", "this_week", "first_week_percent"]
    assert list(body["calls"][0]) == ["id", "external_id", "call_type", "call_type_name", "started_at", "status",
                                      "score", "steps_completed", "steps_total", "steps", "result"]
