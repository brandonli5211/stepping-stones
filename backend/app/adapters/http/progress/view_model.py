"""View Model for GET /progress: the response-ready state the presenter fills and the route returns."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProgressViewModel:
    demo_data: bool = False
    weeks: list[dict] = field(default_factory=list)
    this_week: dict | None = None
    first_week_percent: int | None = None
    comparison: str | None = None  # for example "Up from 64% in week 1"
    call_types: list[dict] = field(default_factory=list)
    steps: list[dict] = field(default_factory=list)
    error: str | None = None  # set when the progress could not be worked out

    def body(self) -> dict:
        """The response body, in the contract's field order. The error is not part of it."""
        return {
            "demo_data": self.demo_data,
            "weeks": self.weeks,
            "this_week": self.this_week,
            "first_week_percent": self.first_week_percent,
            "comparison": self.comparison,
            "call_types": self.call_types,
            "steps": self.steps,
        }
