"""Output Boundary for GetProgress: what the use case may ask of a presenter."""

from __future__ import annotations

from typing import Protocol

from app.application.get_progress.output_data import GetProgressOutputData


class GetProgressOutputBoundary(Protocol):
    def prepare_success_view(self, output_data: GetProgressOutputData) -> None:
        """Show the progress."""

    def prepare_fail_view(self, message: str) -> None:
        """Show that the progress could not be worked out."""
