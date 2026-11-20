"""Pure rules for the calls list: window, this week, percent, and the result label.

Standard library only. No FastAPI, SQLAlchemy, Alembic, psycopg, or environment access.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone


@dataclass(frozen=True)
class StepOutcome:
    key: str
    name: str
    status: str


@dataclass(frozen=True)
class CallResult:
    label: str
    status: str


@dataclass(frozen=True)
class CallRecord:
    id: int
    external_id: str
    call_type: str
    call_type_name: str
    started_at: datetime
    status: str
    score: int | None
    steps_completed: int
    steps_total: int
    steps: tuple[StepOutcome, ...]


@dataclass(frozen=True)
class CallSummary:
    record: CallRecord
    result: CallResult | None


@dataclass(frozen=True)
class CallWindow:
    since: datetime | None
    agent_id: int | None


@dataclass(frozen=True)
class ListFilter:
    call_type: str | None
    has_missed: bool


@dataclass(frozen=True)
class WeekTotals:
    week: date  # the Monday
    done: int
    total: int


@dataclass(frozen=True)
class WeekNumbers:
    steps_completed: int
    steps_total: int
    percent: int | None


@dataclass(frozen=True)
class ListHeader:
    calls_reviewed: int
    weeks: int | None
    this_week: WeekNumbers | None
    first_week_percent: int | None


@dataclass(frozen=True)
class CallList:
    summary: ListHeader
    calls: tuple[CallSummary, ...]


def normalize_call_type(text: object) -> str:
    """'Transfer Money' -> 'transfer_money'."""
    return "_".join(str(text).strip().lower().split())


def result_for(steps: Sequence[StepOutcome]) -> CallResult | None:
    """The first missed or wrong step, in step order: 'Missed <name>' (no colon) or 'Wrong: <name>'."""
    for step in steps:
        if step.status == "missed":
            return CallResult(label=f"Missed {step.name}", status="missed")
        if step.status == "wrong":
            return CallResult(label=f"Wrong: {step.name}", status="wrong")
    return None


def percent(done: int, total: int) -> int | None:
    return round(100 * done / total) if total else None


def window_for(reference: datetime, weeks: int | None, agent_id: int | None) -> CallWindow:
    return CallWindow(since=reference - timedelta(weeks=weeks) if weeks else None, agent_id=agent_id or None)


def week_monday(reference: datetime) -> date:
    """The Monday (UTC) of the week that contains `reference`."""
    utc = reference.astimezone(timezone.utc)
    return (utc - timedelta(days=utc.weekday())).date()


def this_week(weeks: Sequence[WeekTotals], reference: datetime) -> WeekNumbers | None:
    monday = week_monday(reference)
    hit = next((w for w in weeks if w.week == monday), None)
    if hit is None:
        return None
    return WeekNumbers(steps_completed=int(hit.done), steps_total=int(hit.total), percent=percent(hit.done, hit.total))


def first_week_percent(weeks: Sequence[WeekTotals]) -> int | None:
    return percent(weeks[0].done, weeks[0].total) if weeks else None
