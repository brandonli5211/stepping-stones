import asyncio

import pytest

from app.adapters.http.health import health
from app.application.check_health import CheckHealth, HealthStatus


class _FakeCheck:
    def __init__(self, error: Exception | None = None):
        self.error = error
        self.calls = 0

    async def execute(self) -> HealthStatus:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return HealthStatus(status="ok", database="connected")


def test_health_route_delegates_to_check_health():
    check = _FakeCheck()
    body = asyncio.run(health(check=check))
    assert body == {"status": "ok", "database": "connected"}
    assert check.calls == 1


def test_health_route_does_not_report_ok_when_check_fails():
    check = _FakeCheck(error=RuntimeError("database unavailable"))
    with pytest.raises(RuntimeError):
        asyncio.run(health(check=check))


def test_health_route_does_not_execute_sql_itself():
    import inspect

    import app.adapters.http.health as module

    source = inspect.getsource(module.health)
    assert "SELECT" not in source
    assert "execute" not in source or "check.execute" in source
