"""#33: recalculate the demo numbers from seed/demo_calls.json and compare them with Figma.

Percentages count steps, not points (#29): steps completed / steps required.
Wrong counts as not completed. Nothing here is typed in from the JSON: it is all recalculated.
"""

import json
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

DATA = json.loads((Path(__file__).resolve().parents[1] / "seed" / "demo_calls.json").read_text())
CALLS = sorted(DATA["calls"], key=lambda c: c["started_at"])
REFERENCE = date.fromisoformat(DATA["reference_date"])

# Figma targets (card changed to 37 of 41 with 7-step Transfer money; by-type bars updated in #33).
WEEKLY = [64, 70, 68, 75, 80, 79, 86, 90]
BY_TYPE = {
    "check balance": 96, "get branch hours": 90, "order checks": 88, "reset password": 85,
    "pay bill": 81, "schedule appointment": 75, "replace card": 72, "transfer money": 67,
}


def pct(done: int, required: int) -> int:
    return int(done * 100 / required + 0.5)


def week_of(call: dict) -> int:
    """Week 8 is the week of the reference date, week 1 is seven weeks before."""
    monday = REFERENCE - timedelta(days=REFERENCE.weekday())
    day = datetime.fromisoformat(call["started_at"]).date()
    return 8 - (monday - day + timedelta(days=6)).days // 7


def counts(calls: list[dict]) -> tuple[int, int]:
    steps = [s for c in calls for s in c["steps"] if s["status"] != "under_review"]
    return sum(s["status"] == "completed" for s in steps), len(steps)


def test_48_calls_over_8_weeks():
    assert len(CALLS) == 48
    assert {week_of(c) for c in CALLS} == set(range(1, 9))


def test_my_calls_card_this_week():
    done, required = counts([c for c in CALLS if week_of(c) == 8])
    assert (done, required) == (37, 41)
    assert pct(done, required) == 90


@pytest.mark.parametrize("week,expected", list(enumerate(WEEKLY, start=1)))
def test_weekly_percentages(week, expected):
    assert pct(*counts([c for c in CALLS if week_of(c) == week])) == expected


@pytest.mark.parametrize("call_type,expected", BY_TYPE.items())
def test_by_call_type(call_type, expected):
    assert pct(*counts([c for c in CALLS if c["call_type"] == call_type])) == expected


def dots(call_type: str, step_id: str) -> str:
    """Last 5 calls of a type, oldest to newest: C = completed, M = not completed."""
    calls = [c for c in CALLS if c["call_type"] == call_type][-5:]
    return "".join("C" if next(s for s in c["steps"] if s["step_id"] == step_id)["status"] == "completed"
                   else "M" for c in calls)


def test_progress_dots_match_figma():
    assert dots("replace card", "confirm_ordered") == "CMCMM"
    assert dots("transfer money", "submit") == "CMCCM"


def test_greet_and_close_done_on_last_10_calls():
    for call in CALLS[-10:]:
        for step in call["steps"]:
            if step["step_id"] in ("greet", "close"):
                assert step["status"] == "completed", call["id"]


def test_reversed_transfer_call():
    call = next(c for c in CALLS if c["hvb_call_id"] == "a2f086d27b3a4f96")
    submit = next(s for s in call["steps"] if s["step_id"] == "submit")
    assert submit["status"] == "wrong" and submit["quote_start_ms"] == 33530
    assert 100 - sum(s["points_lost"] for s in call["steps"]) == 45
    assert [f["severity"] for f in call["flags"]] == ["critical"]
    table = {r["field"]: r["result"] for r in call["type_details"]["caller_asked_vs_logged"]}
    assert table == {"Amount": "match", "From": "mismatch", "To": "mismatch"}


def test_all_results_marked_as_demo():
    assert all(c["source"] == "demo" for c in CALLS)
