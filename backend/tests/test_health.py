import asyncio

import pytest

from app.main import health


class _ResultSession:
    def __init__(self, error: Exception | None = None):
        self.error = error
        self.statements: list[str] = []

    async def execute(self, statement):
        self.statements.append(str(statement))
        if self.error is not None:
            raise self.error


def test_health_reports_connected_database():
    session = _ResultSession()
    body = asyncio.run(health(session=session))
    assert body == {"status": "ok", "database": "connected"}
    assert any("SELECT 1" in statement for statement in session.statements)


def test_health_does_not_report_ok_when_the_database_fails():
    session = _ResultSession(error=RuntimeError("database unavailable"))
    with pytest.raises(RuntimeError):
        asyncio.run(health(session=session))
