import ast
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import app.domain.call_list as call_list
from app.domain.call_list import (
    CallResult,
    CallWindow,
    StepOutcome,
    WeekNumbers,
    WeekTotals,
    first_week_percent,
    normalize_call_type,
    percent,
    result_for,
    this_week,
    week_monday,
    window_for,
)

DEMO = datetime(2026, 10, 9, 23, 59, 59, tzinfo=timezone.utc)


def steps(*pairs):
    return tuple(StepOutcome(key=name.lower().replace(" ", "_"), name=name, status=status) for name, status in pairs)


# result_for

def test_result_for_missed_has_no_colon():
    assert result_for(steps(("Greet", "completed"), ("Close", "missed"))) == CallResult("Missed Close", "missed")


def test_result_for_wrong_has_colon():
    assert result_for(steps(("Submit and confirm transfer", "wrong"))) == CallResult(
        "Wrong: Submit and confirm transfer", "wrong")


def test_result_for_takes_first_problem_in_step_order():
    assert result_for(steps(("Greet", "completed"), ("Collect", "wrong"), ("Close", "missed"))).label == "Wrong: Collect"


def test_result_for_ignores_under_review_and_returns_none_without_problem():
    assert result_for(steps(("Greet", "under_review"), ("Close", "completed"))) is None
    assert result_for(()) is None


# percent

def test_percent_rounds_like_today():
    assert percent(53, 59) == 90
    assert percent(16, 23) == 70
    assert percent(16, 25) == 64


def test_percent_half_to_even_and_zero_total():
    assert percent(1, 8) == 12  # 12.5
    assert percent(3, 8) == 38  # 37.5
    assert percent(0, 0) is None


# window_for

def test_window_for_counts_back_from_reference():
    assert window_for(DEMO, 8, None) == CallWindow(since=DEMO - timedelta(weeks=8), agent_id=None)
    assert window_for(DEMO, 8, None).since == datetime(2026, 8, 14, 23, 59, 59, tzinfo=timezone.utc)


def test_window_for_without_weeks_or_agent_has_no_limits():
    assert window_for(DEMO, None, None) == CallWindow(None, None)
    assert window_for(DEMO, None, 0) == CallWindow(None, None)
    assert window_for(DEMO, None, 3) == CallWindow(None, 3)


# week_monday

def test_week_monday_sunday_late_and_monday_midnight():
    assert week_monday(datetime(2026, 10, 11, 23, 59, 59, tzinfo=timezone.utc)) == date(2026, 10, 5)
    assert week_monday(datetime(2026, 10, 12, 0, 0, tzinfo=timezone.utc)) == date(2026, 10, 12)


def test_week_monday_uses_utc_not_the_given_offset():
    toronto = timezone(timedelta(hours=-4))
    assert week_monday(datetime(2026, 10, 9, 19, 59, 59, tzinfo=toronto)) == date(2026, 10, 5)
    # Sunday 22:00 in Toronto is Monday 02:00 UTC
    assert week_monday(datetime(2026, 10, 11, 22, 0, tzinfo=toronto)) == date(2026, 10, 12)


# this_week / first_week_percent

WEEKS = (WeekTotals(date(2026, 8, 17), 16, 25), WeekTotals(date(2026, 10, 5), 53, 59))


def test_this_week_found():
    assert this_week(WEEKS, DEMO) == WeekNumbers(53, 59, 90)


def test_this_week_missing():
    assert this_week(WEEKS, datetime(2026, 11, 11, tzinfo=timezone.utc)) is None


def test_first_week_percent():
    assert first_week_percent(WEEKS) == 64
    assert first_week_percent(()) is None


# normalize_call_type

def test_normalize_call_type():
    assert normalize_call_type(" Transfer  Money ") == "transfer_money"
    assert normalize_call_type("transfer_money") == "transfer_money"


# layering

def test_domain_module_imports_nothing_outer():
    tree = ast.parse(Path(call_list.__file__).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", 1)[0])
    assert imported.isdisjoint({"fastapi", "sqlalchemy", "alembic", "psycopg", "os", "app"})
