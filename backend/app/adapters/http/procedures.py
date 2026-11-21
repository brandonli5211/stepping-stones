"""GET /procedures: active templates for the Procedures screen."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.persistence.engine import get_session
from app.adapters.persistence.procedure_list_reader import SqlAlchemyProcedureReader
from app.application.list_procedures import ListProcedures
from app.domain.procedure_list import Procedure

router = APIRouter()


def present(procedures: tuple[Procedure, ...]) -> dict:
    return {"procedures": [
        {
            "task_type": procedure.task_type,
            "name": procedure.name,
            "description": procedure.description,
            "steps": [
                {
                    "order": step.order,
                    "step_name": step.step_name,
                    "step_description": step.step_description,
                }
                for step in procedure.steps
            ],
        }
        for procedure in procedures
    ]}


async def get_list_procedures(session: AsyncSession = Depends(get_session)) -> ListProcedures:
    return ListProcedures(reader=SqlAlchemyProcedureReader(session))


@router.get("/procedures")
async def list_procedures(use_case: ListProcedures = Depends(get_list_procedures)) -> dict:
    return present(await use_case.execute())
