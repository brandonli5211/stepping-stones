"""ProgressDataAccess over an async SQLAlchemy session: the four queries GET /progress needs. No rules here.

Every query counts only scored calls inside the window, for the window's agent when one is given.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.persistence.call_list_reader import WEEK
from app.domain.call_list import WeekTotals
from app.domain.progress import RESOLVED, CallTypeTotals, ProgressWindow, StepResult
from app.models import Call, CallStep, Procedure

DEMO_MODEL = "demo-seed"  # what load_calls --demo-results writes to calls.model

# Steps required: a step under review is not counted until it is resolved.
REQUIRED = Call.steps_total - Call.steps_under_review


def window_clauses(window: ProgressWindow) -> list:
    clauses = [Call.status == "scored", Call.started_at >= window.since, Call.started_at < window.until]
    if window.agent_id:
        clauses.append(Call.agent_id == window.agent_id)
    return clauses


def week_totals_query(window: ProgressWindow):
    return (
        select(WEEK.label("week"), func.sum(Call.steps_completed).label("done"), func.sum(REQUIRED).label("total"))
        .where(*window_clauses(window))
        .group_by(WEEK)
        .order_by(WEEK)
    )


def call_type_totals_query(window: ProgressWindow):
    return (
        select(Call.call_type, func.max(Procedure.name).label("name"), func.sum(Call.steps_completed).label("done"),
               func.sum(REQUIRED).label("total"), func.count().label("calls"))
        .join(Procedure, Procedure.id == Call.procedure_id)
        .where(*window_clauses(window))
        .group_by(Call.call_type)
        .order_by(Call.call_type)
    )


def step_results_query(window: ProgressWindow):
    return (
        select(Call.id.label("call_id"), Call.started_at, Call.call_type, Procedure.name.label("call_type_name"),
               CallStep.step_key, CallStep.name.label("step_name"), CallStep.position, CallStep.status)
        .join(Call, Call.id == CallStep.call_id)
        .join(Procedure, Procedure.id == Call.procedure_id)
        .where(*window_clauses(window), CallStep.status.in_(RESOLVED))
        .order_by(Call.started_at, Call.id, CallStep.position)
    )


def demo_calls_query(window: ProgressWindow):
    return select(exists().where(*window_clauses(window), Call.model == DEMO_MODEL))


def to_week_totals(rows: Sequence) -> list[WeekTotals]:
    return [WeekTotals(week=r.week.date(), done=int(r.done), total=int(r.total)) for r in rows]


def to_call_type_totals(rows: Sequence) -> list[CallTypeTotals]:
    return [CallTypeTotals(call_type=r.call_type, name=r.name, done=int(r.done), total=int(r.total), calls=int(r.calls))
            for r in rows]


def to_step_results(rows: Sequence) -> list[StepResult]:
    return [StepResult(call_id=r.call_id, started_at=r.started_at, call_type=r.call_type,
                       call_type_name=r.call_type_name, step_key=r.step_key, step_name=r.step_name,
                       position=r.position, status=r.status) for r in rows]


class SqlAlchemyProgressDataAccess:
    """ProgressDataAccess backed by an AsyncSession."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def week_totals(self, window: ProgressWindow) -> list[WeekTotals]:
        return to_week_totals((await self._session.execute(week_totals_query(window))).all())

    async def call_type_totals(self, window: ProgressWindow) -> list[CallTypeTotals]:
        return to_call_type_totals((await self._session.execute(call_type_totals_query(window))).all())

    async def step_results(self, window: ProgressWindow) -> list[StepResult]:
        return to_step_results((await self._session.execute(step_results_query(window))).all())

    async def has_demo_calls(self, window: ProgressWindow) -> bool:
        return bool(await self._session.scalar(demo_calls_query(window)))
