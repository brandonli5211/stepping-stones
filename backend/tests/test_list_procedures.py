import asyncio

from app.application.list_procedures import ListProcedures
from app.domain.procedure_list import Procedure, ProcedureStep


class Reader:
    def __init__(self):
        self.called = False

    async def list_active(self):
        self.called = True
        return (Procedure("transfer_money", "Transfer money", "Move money.",
                          (ProcedureStep("greet_and_open", 1, "Greet and open", "Open the call."),)),)


def test_list_procedures_returns_active_templates():
    reader = Reader()

    result = asyncio.run(ListProcedures(reader).execute())

    assert reader.called and result[0].task_type == "transfer_money"
    assert result[0].steps[0].step_description == "Open the call."
