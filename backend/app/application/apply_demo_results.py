"""ApplyDemoResults use case. Depends on the domain and ports only."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from app.application.ports import DemoCallStore
from app.domain.demo_results import (
    ResultsRow,
    SeverityBand,
    duplicate_problems,
    row_problems,
    score_call,
)


@dataclass(frozen=True)
class ApplyOutcome:
    updated: int
    problems: tuple[str, ...]
    saved: bool

    def as_dict(self) -> dict:
        return {"updated": self.updated, "problems": list(self.problems), "saved": self.saved}


@dataclass(frozen=True)
class ApplyDemoResults:
    """Validate every results row, then rescore and save all calls, or save nothing."""

    store: DemoCallStore
    bands: tuple[SeverityBand, ...]

    async def execute(self, rows: Sequence[ResultsRow]) -> ApplyOutcome:
        ids = list(dict.fromkeys(r.external_id for r in rows))
        stored = await self.store.find_calls(ids)
        problems = duplicate_problems(rows)
        for r in rows:
            problems += row_problems(r, stored.get(r.external_id))
        if problems:
            return ApplyOutcome(updated=0, problems=tuple(problems), saved=False)
        await self.store.save_results([score_call(r, stored[r.external_id], self.bands) for r in rows])
        return ApplyOutcome(updated=len(rows), problems=(), saved=True)
