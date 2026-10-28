import os
from collections.abc import AsyncIterator

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def _async_database_url(database_url: str) -> str:
    url = make_url(database_url)
    if url.drivername == "postgresql+psycopg":
        return database_url
    if url.drivername in {"postgresql", "postgres"}:
        return url.set(drivername="postgresql+psycopg").render_as_string(hide_password=False)
    return database_url


def get_engine() -> AsyncEngine:
    """Build an async engine. Does not open a connection."""
    return create_async_engine(_async_database_url(os.environ["DATABASE_URL"]))


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield one async session, then close it."""
    engine = get_engine()
    session = async_sessionmaker(engine, expire_on_commit=False)()
    try:
        yield session
    finally:
        await session.close()
        await engine.dispose()
