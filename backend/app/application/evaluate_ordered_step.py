from app.domain.procedure import (
    COMPLETED_STEP,
    NOT_YET_OBSERVED,
    AgentTurnWindow,
    CallCursor,
    EvaluationResult,
    ProcedureStep,
)
from app.ports.step_decision import StepDecisionMaker, StepProgressStore


class EvaluateOrderedStep:
    """Apply the only application-owned transition for one expected step."""

    def __init__(
        self, decision_maker: StepDecisionMaker, progress_store: StepProgressStore) -> None:
        self._decision_maker = decision_maker
        self._progress_store = progress_store

    async def __call__(
        self,
        *,
        call_id: str,
        procedure_id: str,
        task_id: str,
        steps: tuple[ProcedureStep, ...],
        window: AgentTurnWindow,
        cursor: CallCursor,
    ) -> EvaluationResult:
        if cursor.expected_step_index >= len(steps):
            return EvaluationResult(advanced=False, requires_human_review=False)

        step = steps[cursor.expected_step_index]
        decision = await self._decision_maker(procedure_id, task_id, step, window, cursor)
        if decision.choice not in {COMPLETED_STEP, NOT_YET_OBSERVED}:
            raise ValueError("Decision choice must be completed_step or not_yet_observed")

        review = decision.confidence < 0.80 or window.contradictory_evidence
        if decision.choice == COMPLETED_STEP and not review:
            await self._progress_store.record_completed_step(call_id, step.id, decision.evidence_metadata)
            cursor.expected_step_index += 1
            return EvaluationResult(advanced=True, requires_human_review=False)

        cursor.agent_turn_index += 1
        if cursor.call_ended:
            await self._progress_store.mark_missed_step(call_id, step.id)
            return EvaluationResult(False, review, missed_step_id=step.id)
        return EvaluationResult(False, review)
