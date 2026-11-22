"""Interactor for GetProgress. Depends on the domain, its boundaries and ports only."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.get_progress.data_access import ProgressDataAccess
from app.application.get_progress.input_data import GetProgressInputData
from app.application.get_progress.output_boundary import GetProgressOutputBoundary
from app.application.get_progress.output_data import GetProgressOutputData
from app.application.ports import Clock, RulesUnavailable, SharedStepsSource
from app.domain.call_list import first_week_percent, this_week
from app.domain.progress import call_type_progress, eight_weeks, progress_window, step_rows


@dataclass(frozen=True)
class GetProgressInteractor:
    """One agent's progress over the 8 weeks that end with the clock's week."""

    data: ProgressDataAccess
    shared_steps: SharedStepsSource
    clock: Clock
    presenter: GetProgressOutputBoundary

    async def execute(self, input_data: GetProgressInputData) -> None:
        now = self.clock.now()
        window = progress_window(now, input_data.agent_id)
        try:
            shared = await self.shared_steps.load()
        except RulesUnavailable as error:
            self.presenter.prepare_fail_view(str(error))
            return
        totals = await self.data.week_totals(window)
        self.presenter.prepare_success_view(GetProgressOutputData(
            weeks=eight_weeks(totals, now),
            this_week=this_week(totals, now),
            first_week_percent=first_week_percent(totals),
            call_types=call_type_progress(await self.data.call_type_totals(window)),
            step_rows=step_rows(await self.data.step_results(window), shared),
            demo_data=await self.data.has_demo_calls(window),
        ))
