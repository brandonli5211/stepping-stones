import ast
import asyncio

import pytest

from app.application.get_call_detail import GetCallDetail
from app.domain.call_detail import CallNotFound, build_call_detail
from call_detail_fixtures import transfer_money_call


class _FakeReader:
    """Only a get method: the use case has nothing it could write through."""

    def __init__(self, record=None):
        self.record = record
        self.asked: list[int] = []

    async def get(self, call_id: int):
        self.asked.append(call_id)
        return self.record


def test_get_call_detail_builds_the_detail_of_a_stored_call():
    reader = _FakeReader(transfer_money_call())
    detail = asyncio.run(GetCallDetail(reader=reader).execute(6))
    assert detail == build_call_detail(transfer_money_call())
    assert reader.asked == [6]


def test_get_call_detail_raises_not_found_for_an_unknown_call():
    reader = _FakeReader(None)
    with pytest.raises(CallNotFound) as error:
        asyncio.run(GetCallDetail(reader=reader).execute(999999))
    assert error.value.call_id == 999999
    assert reader.asked == [999999]


def test_call_detail_domain_and_application_import_no_framework():
    import app.application.get_call_detail as use_case
    import app.application.ports as ports
    import app.domain.call_detail as domain

    forbidden = {"fastapi", "sqlalchemy", "alembic", "pydantic"}
    for module in (domain, use_case, ports):
        tree = ast.parse(open(module.__file__, encoding="utf-8").read())
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".", 1)[0])
        assert imported.isdisjoint(forbidden), module.__name__
