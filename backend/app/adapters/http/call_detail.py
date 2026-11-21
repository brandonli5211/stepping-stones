"""GET /calls/{call_id}: one call's detail. Delegates to GetCallDetail; runs no SQL and no rules itself."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.http.call_detail_schema import (
    CallDetailOut,
    EmptyDetailsOut,
    EvidenceOut,
    FieldRowOut,
    FlagOut,
    HeaderOut,
    NoteOut,
    ScoreOut,
    StepDetailsOut,
    StepOut,
    SubCheckOut,
    TransferMoneyDetailsOut,
    TurnOut,
    TypeDetailsOut,
)
from app.adapters.persistence.call_detail_reader import SqlAlchemyCallDetailReader
from app.adapters.persistence.engine import get_session
from app.application.get_call_detail import GetCallDetail
from app.domain.call_detail import CallDetail, CallNotFound, StepDetail, TransferMoneyDetails, TypeDetails

router = APIRouter()


def _step(item: StepDetail) -> StepOut:
    s = item.step
    return StepOut(
        key=s.key, position=s.position, name=s.name, status=s.status, severity=s.severity, points=s.points,
        points_lost=s.points_lost, points_under_review=s.points_under_review,
        details=StepDetailsOut(
            description=s.description,
            detail=s.detail,
            sub_checks=[SubCheckOut(key=c.key, description=c.description, points=c.points, result=c.result)
                        for c in s.sub_checks],
            evidence=None if item.evidence is None else EvidenceOut(
                quote=item.evidence.quote, turn_idx=item.evidence.turn_idx,
                start_seconds=item.evidence.start_seconds),
            coaching=item.coaching,
        ),
    )


def _type_details(details: TypeDetails) -> TypeDetailsOut:
    if isinstance(details, TransferMoneyDetails):
        return TransferMoneyDetailsOut(type="transfer_money", fields=[
            FieldRowOut(field=r.field, label=r.label, caller_asked=r.caller_asked, logged=r.logged, result=r.result)
            for r in details.fields
        ])
    return EmptyDetailsOut(type=details.type)


def present(detail: CallDetail) -> CallDetailOut:
    """Map the domain CallDetail onto the typed response. No judgment here: every value is already worked out."""
    h, sc = detail.header, detail.score
    return CallDetailOut(
        header=HeaderOut(call_id=h.call_id, external_id=h.external_id, call_type=h.call_type,
                         call_type_name=h.call_type_name, summary=h.summary),
        score=ScoreOut(score=sc.score, out_of=sc.out_of, steps_done_right=sc.steps_done_right,
                       steps_total=sc.steps_total, points_lost=sc.points_lost, critical_count=sc.critical_count,
                       points_under_review=sc.points_under_review, provisional=sc.provisional),
        transcript=[
            TurnOut(idx=t.turn.idx, speaker=t.turn.speaker, start_seconds=t.turn.start_seconds, text=t.turn.text,
                    notes=[NoteOut(kind=n.kind, step_key=n.step_key, text=n.text) for n in t.notes])
            for t in detail.transcript
        ],
        steps=[_step(s) for s in detail.steps],
        flags=[FlagOut(step_key=f.step_key, step_name=f.step_name, status=f.status, severity=f.severity,
                       points_lost=f.points_lost, message=f.message) for f in detail.flags],
        type_details=_type_details(detail.type_details),
    )


async def get_get_call_detail(session: AsyncSession = Depends(get_session)) -> GetCallDetail:
    return GetCallDetail(reader=SqlAlchemyCallDetailReader(session))


@router.get(
    "/calls/{call_id}",
    response_model=CallDetailOut,
    responses={404: {"description": "No call with this id"}},
)
async def get_call_detail(call_id: int, use_case: GetCallDetail = Depends(get_get_call_detail)) -> CallDetailOut:
    """Everything the call detail screen shows for one call, read from stored data. call_id is the `id` from
    GET /calls. Nothing is analyzed."""
    try:
        detail = await use_case.execute(call_id)
    except CallNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return present(detail)
