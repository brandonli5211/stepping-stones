"""CallDetailReader backed by an async SQLAlchemy session: reads calls, call_turns and call_steps (#29). Read only."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.call_detail import CallRecord, ComparisonRow, InvalidCallRecord, StepRecord, SubCheck, TurnRecord
from app.models import Call, CallStep, CallTurn, Procedure


def _text(value: Any) -> str | None:
    return None if value is None else str(value)


def to_turn_record(row: Any) -> TurnRecord:
    return TurnRecord(
        idx=row.idx,
        speaker=row.speaker,
        start_seconds=None if row.start_seconds is None else float(row.start_seconds),
        text=row.text,
    )


def to_sub_check(item: dict) -> SubCheck:
    """A row of call_steps.sub_checks. The stored result is under `status`."""
    return SubCheck(
        key=item["key"],
        description=item.get("description", ""),
        points=int(item.get("points", 0)),
        result=item.get("status") or item.get("result") or "under_review",
    )


def to_comparison_row(item: dict) -> ComparisonRow:
    """A row of call_steps.comparison: field, caller_asked, logged, match."""
    return ComparisonRow(
        field=item["field"],
        caller_asked=_text(item.get("caller_asked")),
        logged=_text(item.get("logged")),
        match=bool(item.get("match")),
    )


def step_descriptions(rules: dict | None) -> dict[str, str]:
    """Step key → description, from a procedure's stored rules (procedures.rules.steps)."""
    return {
        s["key"]: s["description"]
        for s in (rules or {}).get("steps", [])
        if isinstance(s, dict) and s.get("key") and s.get("description")
    }


def to_step_record(row: Any, description: str | None = None) -> StepRecord:
    return StepRecord(
        key=row.step_key,
        position=row.position,
        name=row.name,
        points=row.points,
        status=row.status,
        severity=row.severity,
        points_lost=row.points_lost,
        points_under_review=row.points_under_review,
        detail=row.detail,
        evidence_turn_idx=row.evidence_turn_idx,
        evidence_quote=row.evidence_quote,
        coaching=row.coaching,
        sub_checks=tuple(to_sub_check(i) for i in row.sub_checks or ()),
        comparison=tuple(to_comparison_row(i) for i in row.comparison or ()),
        description=description,
    )


def to_call_record(call: Any, turns: list[Any], steps: list[Any]) -> CallRecord:
    descriptions = step_descriptions(getattr(call, "rules", None))
    return CallRecord(
        id=call.id,
        external_id=call.external_id,
        call_type=call.call_type,
        call_type_name=call.call_type_name,
        summary=call.summary,
        turns=tuple(to_turn_record(t) for t in turns),
        steps=tuple(to_step_record(s, descriptions.get(s.step_key)) for s in steps),
    )


class SqlAlchemyCallDetailReader:
    """Three read queries: the call with its procedure's name and rules, its turns, its steps. Never commits."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, call_id: int) -> CallRecord | None:
        call = (await self._session.execute(
            select(Call.id, Call.external_id, Call.call_type, Call.summary, Procedure.name.label("call_type_name"),
                   Procedure.rules)
            .join(Procedure, Procedure.id == Call.procedure_id)
            .where(Call.id == call_id)
        )).first()
        if call is None:
            return None
        turns = (await self._session.execute(
            select(CallTurn.idx, CallTurn.speaker, CallTurn.start_seconds, CallTurn.text)
            .where(CallTurn.call_id == call_id).order_by(CallTurn.idx)
        )).all()
        steps = (await self._session.execute(
            select(
                CallStep.step_key, CallStep.position, CallStep.name, CallStep.points, CallStep.status,
                CallStep.severity, CallStep.points_lost, CallStep.points_under_review, CallStep.detail,
                CallStep.evidence_turn_idx, CallStep.evidence_quote, CallStep.coaching, CallStep.sub_checks,
                CallStep.comparison,
            ).where(CallStep.call_id == call_id).order_by(CallStep.position)
        )).all()
        try:
            return to_call_record(call, list(turns), list(steps))
        except InvalidCallRecord as error:
            raise InvalidCallRecord(f"call {call_id}: {error}") from error
