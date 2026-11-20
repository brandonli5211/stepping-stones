"""Pure rules for the Progress screen: the 8 weeks, the call types, and the "steps you skip most" rows.

Standard library plus the calls-list rules (week and percent), which are reused, not copied.
No FastAPI, SQLAlchemy, Alembic, psycopg, or environment access.
"""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

from app.domain.call_list import WeekTotals, percent, week_monday

WEEKS = 8
TYPE_WINDOW = 5  # a step of one call type: that call type's last 5 calls
SHARED_WINDOW = 10  # a step every call type has: the last 10 calls
RESOLVED = ("completed", "missed", "wrong")  # under_review is left out until it is resolved
MISSES = ("missed", "wrong")  # wrong counts as not completed


@dataclass(frozen=True)
class ProgressWindow:
    since: datetime
    until: datetime  # exclusive
    agent_id: int | None


@dataclass(frozen=True)
class ProgressWeek:
    week_start: date  # the Monday
    steps_completed: int
    steps_total: int
    percent: int | None
    is_current: bool


@dataclass(frozen=True)
class CallTypeTotals:
    call_type: str
    name: str
    done: int
    total: int
    calls: int


@dataclass(frozen=True)
class CallTypeProgress:
    call_type: str
    name: str
    steps_completed: int
    steps_total: int
    percent: int | None
    calls: int


@dataclass(frozen=True)
class StepResult:
    call_id: int
    started_at: datetime
    call_type: str
    call_type_name: str
    step_key: str
    step_name: str
    position: int
    status: str


@dataclass(frozen=True)
class StepRow:
    step_key: str
    step_name: str
    call_type: str | None  # None: a step shared by all call types
    call_type_name: str | None
    results: tuple[str, ...]  # oldest first
    misses: int
    window: int


def _midnight(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=timezone.utc)


def progress_window(now: datetime, agent_id: int | None) -> ProgressWindow:
    """The 8 calendar weeks (Monday start, UTC) that end with the week containing `now`."""
    monday = week_monday(now)
    return ProgressWindow(
        since=_midnight(monday - timedelta(weeks=WEEKS - 1)),
        until=_midnight(monday + timedelta(weeks=1)),
        agent_id=agent_id or None,
    )


def eight_weeks(totals: Sequence[WeekTotals], now: datetime) -> tuple[ProgressWeek, ...]:
    """Exactly 8 weeks, oldest first. A week with no totals is empty; totals for other weeks are ignored."""
    monday = week_monday(now)
    by_week = {t.week: t for t in totals}
    weeks = []
    for back in range(WEEKS - 1, -1, -1):
        start = monday - timedelta(weeks=back)
        hit = by_week.get(start)
        done, total = (int(hit.done), int(hit.total)) if hit else (0, 0)
        weeks.append(ProgressWeek(week_start=start, steps_completed=done, steps_total=total,
                                  percent=percent(done, total), is_current=back == 0))
    return tuple(weeks)


def call_type_progress(totals: Sequence[CallTypeTotals]) -> tuple[CallTypeProgress, ...]:
    """One per call type, highest percent first (no percent last), ties by name."""
    rows = [CallTypeProgress(call_type=t.call_type, name=t.name, steps_completed=t.done, steps_total=t.total,
                             percent=percent(t.done, t.total), calls=t.calls) for t in totals]
    return tuple(sorted(rows, key=lambda r: (r.percent is None, -(r.percent or 0), r.name)))


def step_rows(results: Sequence[StepResult], shared_keys: Collection[str]) -> tuple[StepRow, ...]:
    """One row per step: its last results (10 across all call types for a shared step, else 5 of its call type).

    Most misses first; then shared rows, call type name, the step's position, and its key.
    """
    resolved = sorted((r for r in results if r.status in RESOLVED), key=lambda r: (r.started_at, r.call_id))
    groups: dict[tuple[str | None, str], list[StepResult]] = {}
    for r in resolved:
        groups.setdefault((None if r.step_key in shared_keys else r.call_type, r.step_key), []).append(r)
    ordered = []
    for (call_type, step_key), group in groups.items():
        kept = group[-(SHARED_WINDOW if call_type is None else TYPE_WINDOW):]
        newest = kept[-1]
        row = StepRow(
            step_key=step_key,
            step_name=newest.step_name,
            call_type=call_type,
            call_type_name=None if call_type is None else newest.call_type_name,
            results=tuple(r.status for r in kept),
            misses=sum(r.status in MISSES for r in kept),
            window=len(kept),
        )
        ordered.append(((-row.misses, call_type is not None, row.call_type_name or "", newest.position, step_key), row))
    return tuple(row for _, row in sorted(ordered, key=lambda pair: pair[0]))
