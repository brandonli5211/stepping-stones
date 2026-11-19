from collections.abc import Awaitable, Callable
from typing import Protocol

from app.domain.procedure import AgentTurnWindow, CallCursor, ProcedureStep, StepDecision


class StepDecisionMaker(Protocol):
    def __call__(
        self,
        procedure_id: str,
        task_id: str,
        step: ProcedureStep,
        window: AgentTurnWindow,
        cursor: CallCursor,
    ) -> Awaitable[StepDecision]: ...


class StepProgressStore(Protocol):
    async def record_completed_step(
        self, call_id: str, step_id: str, evidence_metadata: dict
    ) -> None: ...

    async def mark_missed_step(self, call_id: str, step_id: str) -> None: ...
