"""SQLAlchemy reader for the active procedure templates."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.procedure_list import Procedure, ProcedureStep
from app.models import Procedure as StoredProcedure


class SqlAlchemyProcedureReader:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self) -> tuple[Procedure, ...]:
        rows = (await self._session.execute(
            select(StoredProcedure.call_type, StoredProcedure.name, StoredProcedure.rules)
            .where(StoredProcedure.is_active)
            .order_by(StoredProcedure.name)
        )).all()
        return tuple(
            Procedure(
                task_type=row.call_type,
                name=row.name,
                description=row.rules["description"],
                steps=tuple(
                    ProcedureStep(step["key"], index, step["name"], step["description"])
                    for index, step in enumerate(row.rules["steps"], start=1)
                ),
            )
            for row in rows
        )
