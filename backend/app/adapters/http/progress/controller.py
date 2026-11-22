"""Controller for GetProgress: turns the request's values into input data and calls the input boundary."""

from __future__ import annotations

from app.application.get_progress.input_boundary import GetProgressInputBoundary
from app.application.get_progress.input_data import GetProgressInputData


class GetProgressController:
    def __init__(self, use_case: GetProgressInputBoundary) -> None:
        self.use_case = use_case

    async def execute(self, agent_id: int | None) -> None:
        await self.use_case.execute(GetProgressInputData(agent_id=agent_id))
