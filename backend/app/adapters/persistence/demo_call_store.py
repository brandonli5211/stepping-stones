"""DemoCallStore over an async SQLAlchemy session.

Writes run inside the caller's transaction: this adapter never begins, commits, or rolls back.
"""

from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping, Sequence

from sqlalchemy import bindparam, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.demo_results import ScoredCall, StoredCall, StoredStep
from app.models import Call, CallStep

_calls = Call.__table__
_steps = CallStep.__table__

FIND_CALLS = (
    select(
        _calls.c.external_id, _calls.c.call_type,
        _steps.c.step_key, _steps.c.name, _steps.c.points, _steps.c.status, _steps.c.detail,
    )
    .select_from(_calls.outerjoin(_steps, _steps.c.call_id == _calls.c.id))
    .where(_calls.c.external_id.in_(bindparam("external_ids", expanding=True)))
    .order_by(_calls.c.external_id, _steps.c.position)
)

UPDATE_CALL = (
    update(_calls)
    .where(_calls.c.external_id == bindparam("b_external_id"))
    .values(
        started_at=bindparam("b_started_at"), status="scored", score=bindparam("b_score"),
        points_lost=bindparam("b_points_lost"), steps_total=bindparam("b_steps_total"),
        steps_completed=bindparam("b_steps_completed"), steps_missed=bindparam("b_steps_missed"),
        steps_wrong=bindparam("b_steps_wrong"), steps_under_review=0,
    )
    .returning(_calls.c.id)
)

UPDATE_STEP = (
    update(_steps)
    .where(_steps.c.call_id == bindparam("b_call_id"), _steps.c.step_key == bindparam("b_step_key"))
    .values(
        status=bindparam("b_status"), severity=bindparam("b_severity"), points_lost=bindparam("b_points_lost"),
        points_under_review=0, detail=bindparam("b_detail"),
    )
)


def to_stored_calls(rows: Iterable[Sequence]) -> dict[str, StoredCall]:
    """Group joined (external_id, call_type, step_key, name, points, status, detail) rows by call.

    Rows arrive in step position order. A call with no steps has a single row whose step columns are null.
    """
    grouped: dict[str, tuple[str, list[StoredStep]]] = {}
    for external_id, call_type, key, name, points, status, detail in rows:
        _, steps = grouped.setdefault(external_id, (call_type, []))
        if key is not None:
            steps.append(StoredStep(key=key, name=name, points=points, status=status, detail=detail))
    return {eid: StoredCall(eid, call_type, tuple(steps)) for eid, (call_type, steps) in grouped.items()}


def call_params(call: ScoredCall) -> dict:
    return {
        "b_external_id": call.external_id, "b_started_at": call.started_at, "b_score": call.score,
        "b_points_lost": call.points_lost, "b_steps_total": call.steps_total,
        "b_steps_completed": call.steps_completed, "b_steps_missed": call.steps_missed,
        "b_steps_wrong": call.steps_wrong,
    }


def step_params(call_id: int, call: ScoredCall) -> list[dict]:
    return [
        {"b_call_id": call_id, "b_step_key": s.key, "b_status": s.status, "b_severity": s.severity,
         "b_points_lost": s.points_lost, "b_detail": s.detail}
        for s in call.steps
    ]


class SqlAlchemyDemoCallStore:
    """DemoCallStore backed by an AsyncSession. The caller owns the transaction."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_calls(self, external_ids: Collection[str]) -> Mapping[str, StoredCall]:
        if not external_ids:
            return {}
        result = await self._session.execute(FIND_CALLS, {"external_ids": list(external_ids)})
        return to_stored_calls(result.all())

    async def save_results(self, calls: Sequence[ScoredCall]) -> None:
        for call in calls:
            result = await self._session.execute(UPDATE_CALL, call_params(call))
            call_id = result.scalar_one()
            if call.steps:
                await self._session.execute(UPDATE_STEP, step_params(call_id, call))
