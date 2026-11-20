"""CallAnalysisSource over an async SQLAlchemy session."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.call_analysis import CallToAnalyze
from app.models import Call, CallTurn, Procedure


def call_query(call_id: int):
    return (
        select(Call.id, Call.external_id, Call.call_type, Call.raw_metadata, Call.raw_transcript, Procedure.rules)
        .join(Procedure, Procedure.id == Call.procedure_id)
        .where(Call.id == call_id)
    )


def turns_query(call_id: int):
    return select(CallTurn.speaker, CallTurn.text).where(CallTurn.call_id == call_id).order_by(CallTurn.idx)


def to_call(row) -> CallToAnalyze | None:
    if row is None:
        return None
    return CallToAnalyze(id=row.id, external_id=row.external_id, call_type=row.call_type,
                         metadata=row.raw_metadata, raw_transcript=row.raw_transcript, rules=row.rules)


class SqlAlchemyCallAnalysisSource:
    """CallAnalysisSource backed by an AsyncSession."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def load(self, call_id: int) -> CallToAnalyze | None:
        return to_call((await self._session.execute(call_query(call_id))).first())

    async def turns(self, call_id: int) -> list[tuple[str, str]]:
        return [(t.speaker, t.text) for t in (await self._session.execute(turns_query(call_id))).all()]
