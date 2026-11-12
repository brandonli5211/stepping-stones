"""GET /calls: translate the request, delegate to ListCalls, present the result. No SQL and no rules here."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.persistence.call_list_reader import SqlAlchemyCallListReader
from app.adapters.persistence.engine import get_session
from app.application.list_calls import ListCalls, ListCallsQuery
from app.domain.call_list import CallList

router = APIRouter()


def present_call_list(result: CallList) -> dict:
    """The response shape GET /calls has always had: same keys, order, and types."""
    s = result.summary
    return {
        "summary": {
            "calls_reviewed": s.calls_reviewed, "weeks": s.weeks,
            "this_week": None if s.this_week is None else {
                "steps_completed": s.this_week.steps_completed, "steps_total": s.this_week.steps_total,
                "percent": s.this_week.percent},
            "first_week_percent": s.first_week_percent,
        },
        "calls": [
            {
                "id": c.record.id, "external_id": c.record.external_id, "call_type": c.record.call_type,
                "call_type_name": c.record.call_type_name, "started_at": c.record.started_at,
                "status": c.record.status, "score": c.record.score,
                "steps_completed": c.record.steps_completed, "steps_total": c.record.steps_total,
                "steps": [{"key": st.key, "name": st.name, "status": st.status} for st in c.record.steps],
                "result": None if c.result is None else {"label": c.result.label, "status": c.result.status},
            }
            for c in result.calls
        ],
    }


async def get_list_calls(request: Request, session: AsyncSession = Depends(get_session)) -> ListCalls:
    return ListCalls(reader=SqlAlchemyCallListReader(session), clock=request.app.state.clock)


@router.get("/calls")
async def list_calls(
    agent_id: int | None = None,
    call_type: str | None = None,
    has_missed: bool = False,
    limit: int = Query(10, ge=1, le=100),
    weeks: int | None = Query(None, ge=1, le=520),
    use_case: ListCalls = Depends(get_list_calls),
) -> dict:
    """The master list: the most recent calls (newest first) with their steps, plus the header numbers.

    weeks limits everything (list and header numbers) to calls from the last N weeks. Left out, there is no date
    limit and the list is just the `limit` most recent calls.
    """
    query = ListCallsQuery(agent_id=agent_id, call_type=call_type, has_missed=has_missed, limit=limit, weeks=weeks)
    return present_call_list(await use_case.execute(query))
