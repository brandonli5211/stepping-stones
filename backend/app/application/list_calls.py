"""ListCalls use case. Depends on the domain and ports only."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.ports import CallListReader, Clock
from app.domain.call_list import (
    CallList,
    CallSummary,
    ListFilter,
    ListHeader,
    first_week_percent,
    normalize_call_type,
    result_for,
    this_week,
    window_for,
)


@dataclass(frozen=True)
class ListCallsQuery:
    agent_id: int | None = None
    call_type: str | None = None
    has_missed: bool = False
    limit: int = 10
    weeks: int | None = None


@dataclass(frozen=True)
class ListCalls:
    """The recent calls with their result labels, plus the header numbers, measured from the clock's instant."""

    reader: CallListReader
    clock: Clock

    async def execute(self, query: ListCallsQuery) -> CallList:
        now = self.clock.now()
        window = window_for(now, query.weeks, query.agent_id)
        filters = ListFilter(
            call_type=normalize_call_type(query.call_type) if query.call_type else None,
            has_missed=query.has_missed,
        )
        records = await self.reader.recent_calls(window, filters, query.limit)
        reviewed = await self.reader.count_calls(window)
        weeks = await self.reader.week_totals(window)
        return CallList(
            summary=ListHeader(
                calls_reviewed=reviewed,
                weeks=query.weeks,
                this_week=this_week(weeks, now),
                first_week_percent=first_week_percent(weeks),
            ),
            calls=tuple(CallSummary(record=r, result=result_for(r.steps)) for r in records),
        )
