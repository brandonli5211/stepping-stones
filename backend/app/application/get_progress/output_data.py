"""Output Data for GetProgress."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.call_list import WeekNumbers
from app.domain.progress import CallTypeProgress, ProgressWeek, StepRow


@dataclass(frozen=True)
class GetProgressOutputData:
    weeks: tuple[ProgressWeek, ...]  # exactly 8, oldest first
    this_week: WeekNumbers | None
    first_week_percent: int | None
    call_types: tuple[CallTypeProgress, ...]
    step_rows: tuple[StepRow, ...]
    demo_data: bool
