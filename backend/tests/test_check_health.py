import asyncio

import pytest

from app.application.check_health import CheckHealth


class _FakeProbe:
    def __init__(self, error: Exception | None = None):
        self.error = error
        self.pings = 0

    async def ping(self) -> None:
        self.pings += 1
        if self.error is not None:
            raise self.error


def test_check_health_returns_ok_when_probe_succeeds():
    probe = _FakeProbe()
    status = asyncio.run(CheckHealth(probe=probe).execute())
    assert status.as_dict() == {"status": "ok", "database": "connected"}
    assert probe.pings == 1


def test_check_health_does_not_return_ok_when_probe_fails():
    probe = _FakeProbe(error=RuntimeError("database unavailable"))
    with pytest.raises(RuntimeError):
        asyncio.run(CheckHealth(probe=probe).execute())


def test_application_modules_do_not_import_frameworks():
    import ast

    import app.application.check_health as check_health
    import app.application.ports as ports

    forbidden = {"fastapi", "sqlalchemy", "alembic"}
    for module in (check_health, ports):
        tree = ast.parse(open(module.__file__, encoding="utf-8").read())
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".", 1)[0])
        assert imported.isdisjoint(forbidden)
