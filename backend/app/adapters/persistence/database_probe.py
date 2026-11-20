from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import DatabaseProbe


class SqlAlchemyDatabaseProbe:
    """DatabaseProbe backed by an async SQLAlchemy session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def ping(self) -> None:
        await self._session.execute(text("SELECT 1"))


def as_database_probe(session: AsyncSession) -> DatabaseProbe:
    return SqlAlchemyDatabaseProbe(session)
