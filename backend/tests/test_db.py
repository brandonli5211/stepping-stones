import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_engine, get_session

_DATABASE_URL = "postgresql://tester:secret@db.example:5432/stones"
_ASYNC_DATABASE_URL = "postgresql+psycopg://tester:secret@db.example:5432/stones"


def test_get_engine_uses_psycopg_scheme_without_connecting(monkeypatch):
    for database_url in (_DATABASE_URL, _ASYNC_DATABASE_URL):
        monkeypatch.setenv("DATABASE_URL", database_url)
        engine = get_engine()
        try:
            assert engine.url.drivername == "postgresql+psycopg"
            pool = engine.sync_engine.pool
            assert pool.checkedout() == 0
            assert pool.checkedin() == 0
        finally:
            engine.sync_engine.dispose()


def test_get_session_yields_async_session(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", _ASYNC_DATABASE_URL)

    async def pull():
        generator = get_session()
        session = await anext(generator)
        try:
            assert isinstance(session, AsyncSession)
        finally:
            await generator.aclose()

    asyncio.run(pull())
