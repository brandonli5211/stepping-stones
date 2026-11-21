import asyncio

from app.adapters.http.procedures import list_procedures, present
from app.domain.procedure_list import Procedure, ProcedureStep


PROCEDURES = (Procedure("transfer_money", "Transfer money", "Move money.",
                        (ProcedureStep("greet_and_open", 1, "Greet and open", "Open the call."),)),)


class UseCase:
    async def execute(self):
        return PROCEDURES


def test_present_exposes_only_page_safe_procedure_fields():
    assert present(PROCEDURES) == {
        "procedures": [{
            "call_type": "transfer_money", "name": "Transfer money", "description": "Move money.",
            "steps": [{"key": "greet_and_open", "order": 1, "step_name": "Greet and open", "step_description": "Open the call."}],
        }]
    }


def test_route_returns_the_presented_procedures():
    assert asyncio.run(list_procedures(UseCase())) == present(PROCEDURES)


def test_endpoint_is_in_the_catalogue():
    from app.main import app

    assert "/procedures" in app.openapi()["paths"]
