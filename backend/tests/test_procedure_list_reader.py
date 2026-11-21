import asyncio
from types import SimpleNamespace as Row

from app.adapters.persistence.procedure_list_reader import SqlAlchemyProcedureReader


class Result:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class Session:
    def __init__(self):
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        return Result([Row(
            call_type="transfer_money", name="Transfer money",
            rules={"description": "Move money.", "steps": [
                {"key": "greet_and_open", "name": "Greet and open", "description": "Open the call."},
            ]},
        )])


def test_reader_maps_active_procedure_rows_to_display_records():
    session = Session()

    procedures = asyncio.run(SqlAlchemyProcedureReader(session).list_active())

    assert procedures[0].task_type == "transfer_money"
    assert procedures[0].steps[0].key == "greet_and_open"
    assert procedures[0].steps[0].order == 1
    assert len(session.statements) == 1
    assert str(session.statements[0]).lstrip().upper().startswith("SELECT")
