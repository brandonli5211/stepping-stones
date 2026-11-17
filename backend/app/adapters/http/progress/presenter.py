"""Presenter for GetProgress: turns the use case's output data into the view model. No rules here, only wording
and shape."""

from __future__ import annotations

from app.adapters.http.progress.view_model import ProgressViewModel
from app.application.get_progress.output_data import GetProgressOutputData
from app.domain.call_list import WeekNumbers
from app.domain.progress import StepRow

ALL_CALL_TYPES = "All call types"


class GetProgressPresenter:
    """Implements GetProgressOutputBoundary."""

    def __init__(self, view_model: ProgressViewModel) -> None:
        self.view_model = view_model

    def prepare_success_view(self, output_data: GetProgressOutputData) -> None:
        vm = self.view_model
        week = output_data.this_week
        vm.error = None
        vm.demo_data = output_data.demo_data
        vm.weeks = [
            {"week_start": w.week_start.isoformat(), "steps_completed": w.steps_completed,
             "steps_total": w.steps_total, "percent": w.percent, "is_current": w.is_current}
            for w in output_data.weeks
        ]
        vm.this_week = None if week is None else {
            "steps_completed": week.steps_completed, "steps_total": week.steps_total, "percent": week.percent}
        vm.first_week_percent = output_data.first_week_percent
        vm.comparison = self.comparison(week, output_data.first_week_percent)
        vm.call_types = [
            {"call_type": t.call_type, "name": t.name, "steps_completed": t.steps_completed,
             "steps_total": t.steps_total, "percent": t.percent, "calls": t.calls}
            for t in output_data.call_types
        ]
        vm.steps = [
            {"step_key": r.step_key, "name": r.step_name, "call_type": r.call_type, "label": self.label(r),
             "results": list(r.results), "misses": r.misses, "window": r.window, "summary": self.summary(r)}
            for r in output_data.step_rows
        ]

    def prepare_fail_view(self, message: str) -> None:
        self.view_model.error = message

    @staticmethod
    def comparison(this_week: WeekNumbers | None, first_week_percent: int | None) -> str | None:
        """This week against the first week, for example "Up from 64% in week 1". None when either is unknown."""
        if this_week is None or this_week.percent is None or first_week_percent is None:
            return None
        if this_week.percent > first_week_percent:
            word = "Up from"
        elif this_week.percent < first_week_percent:
            word = "Down from"
        else:
            word = "Same as"
        return f"{word} {first_week_percent}% in week 1"

    @staticmethod
    def label(row: StepRow) -> str:
        """The call type's name, or "All call types" for a step every call type has."""
        return ALL_CALL_TYPES if row.call_type is None else (row.call_type_name or row.call_type)

    @staticmethod
    def summary(row: StepRow) -> str:
        """For example "Missed on 3 of your last 5 replace-card calls"."""
        kind = "" if row.call_type is None else row.call_type.replace("_", "-") + " "
        if row.window == 1:
            return f"{'Missed' if row.misses else 'Done'} on your last {kind}call"
        if row.misses:
            return f"Missed on {row.misses} of your last {row.window} {kind}calls"
        return f"Done on all of your last {row.window} {kind}calls"
