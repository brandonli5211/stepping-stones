"""CallListReader over an async SQLAlchemy session: the three queries GET /calls needs. No rules here."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.call_list import CallRecord, CallWindow, ListFilter, StepOutcome, WeekTotals
from app.models import Call, CallStep, Procedure

# Monday-start week in UTC whatever the session's time zone (FR-006).
WEEK = func.date_trunc("week", Call.started_at.op("AT TIME ZONE")("UTC"))


def window_clauses(window: CallWindow) -> list:
    clauses = []
    if window.since:
        clauses.append(Call.started_at >= window.since)
    if window.agent_id:
        clauses.append(Call.agent_id == window.agent_id)
    return clauses


def list_clauses(window: CallWindow, filters: ListFilter) -> list:
    clauses = window_clauses(window)
    if filters.call_type:
        clauses.append(Call.call_type == filters.call_type)
    if filters.has_missed:  # a step that was missed or done wrong
        clauses.append(Call.steps_missed + Call.steps_wrong > 0)
    return clauses


def recent_calls_query(window: CallWindow, filters: ListFilter, limit: int):
    return (
        select(Call.id, Call.external_id, Call.call_type, Procedure.name, Call.started_at, Call.status, Call.score,
               Call.steps_completed, Call.steps_total)
        .join(Procedure, Procedure.id == Call.procedure_id)
        .where(*list_clauses(window, filters))
        .order_by(Call.started_at.desc(), Call.id.desc())
        .limit(limit)
    )


def steps_query(call_ids: Sequence[int]):
    return (
        select(CallStep.call_id, CallStep.step_key, CallStep.name, CallStep.status)
        .where(CallStep.call_id.in_(list(call_ids)))
        .order_by(CallStep.call_id, CallStep.position)
    )


def count_query(window: CallWindow):
    return select(func.count()).select_from(Call).where(*window_clauses(window))


def week_totals_query(window: CallWindow):
    return (
        select(WEEK.label("week"), func.sum(Call.steps_completed).label("done"), func.sum(Call.steps_total).label("total"))
        .where(*window_clauses(window))
        .group_by(WEEK)
        .order_by(WEEK)
    )


def to_records(rows: Sequence, step_rows: Sequence) -> list[CallRecord]:
    steps: dict[int, list[StepOutcome]] = {r.id: [] for r in rows}
    for st in step_rows:
        steps[st.call_id].append(StepOutcome(key=st.step_key, name=st.name, status=st.status))
    return [
        CallRecord(id=r.id, external_id=r.external_id, call_type=r.call_type, call_type_name=r.name,
                   started_at=r.started_at, status=r.status, score=r.score, steps_completed=r.steps_completed,
                   steps_total=r.steps_total, steps=tuple(steps[r.id]))
        for r in rows
    ]


class SqlAlchemyCallListReader:
    """CallListReader backed by an AsyncSession."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def recent_calls(self, window: CallWindow, filters: ListFilter, limit: int) -> list[CallRecord]:
        rows = (await self._session.execute(recent_calls_query(window, filters, limit))).all()
        step_rows = (await self._session.execute(steps_query([r.id for r in rows]))).all() if rows else []
        return to_records(rows, step_rows)

    async def count_calls(self, window: CallWindow) -> int:
        return await self._session.scalar(count_query(window))

    async def week_totals(self, window: CallWindow) -> list[WeekTotals]:
        rows = (await self._session.execute(week_totals_query(window))).all()
        return [WeekTotals(week=r.week.date(), done=int(r.done), total=int(r.total)) for r in rows]
