"""Input Boundary for GetProgress: what a controller may ask of the use case."""

from __future__ import annotations

from typing import Protocol

from app.application.get_progress.input_data import GetProgressInputData


class GetProgressInputBoundary(Protocol):
    async def execute(self, input_data: GetProgressInputData) -> None:
        """Work out the progress and hand it to the output boundary."""
