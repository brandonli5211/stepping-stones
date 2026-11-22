"""Data Access Interface for GetProgress.

Every method counts only scored calls that started inside the window, for the window's agent when one is given.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from app.domain.call_list import WeekTotals
from app.domain.progress import CallTypeTotals, ProgressWindow, StepResult


class ProgressDataAccess(Protocol):
    async def week_totals(self, window: ProgressWindow) -> Sequence[WeekTotals]:
        """Steps completed and steps required (total minus under review) per UTC Monday week, oldest first."""

    async def call_type_totals(self, window: ProgressWindow) -> Sequence[CallTypeTotals]:
        """The same sums and the number of calls, per call type."""

    async def step_results(self, window: ProgressWindow) -> Sequence[StepResult]:
        """One per resolved step result (completed, missed or wrong), oldest call first, then step position."""

    async def has_demo_calls(self, window: ProgressWindow) -> bool:
        """Whether any counted call was scored by the demo seed."""
