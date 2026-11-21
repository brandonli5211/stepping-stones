"""List the active procedure templates available to agents."""

from dataclasses import dataclass

from app.application.ports import ProcedureReader
from app.domain.procedure_list import Procedure


@dataclass(frozen=True)
class ListProcedures:
    reader: ProcedureReader

    async def execute(self) -> tuple[Procedure, ...]:
        return tuple(await self.reader.list_active())
