import asyncio
from app.application.evaluate_ordered_step import EvaluateOrderedStep
from app.domain.procedure import AgentTurnWindow, CallCursor, ProcedureStep, StepDecision

class Store:
    def __init__(self): self.completed, self.missed = [], []
    async def record_completed_step(self, call_id, step_id, evidence_metadata): self.completed.append((call_id, step_id, evidence_metadata))
    async def mark_missed_step(self, call_id, step_id): self.missed.append((call_id, step_id))

def run(decision, window=AgentTurnWindow("turn"), ended=False):
    async def decide(*_): return decision
    store, cursor = Store(), CallCursor(0, 0, ended)
    result = asyncio.run(EvaluateOrderedStep(decide, store)(call_id="c", procedure_id="p", task_id="t", steps=(ProcedureStep("s", "Verify"),), window=window, cursor=cursor))
    return result, store, cursor

def test_completed_high_confidence_persists_evidence_and_advances():
    result, store, cursor = run(StepDecision("completed_step", .8, {"quote": "verified"}))
    assert result.advanced and store.completed and cursor.expected_step_index == 1

def test_not_observed_retains_step_for_later_turn():
    result, store, cursor = run(StepDecision("not_yet_observed", .99))
    assert not result.advanced and not store.completed and cursor.expected_step_index == 0 and cursor.agent_turn_index == 1

def test_low_confidence_or_contradiction_requires_review_without_advance():
    for decision, window in ((StepDecision("completed_step", .79), AgentTurnWindow("x")), (StepDecision("completed_step", .99), AgentTurnWindow("x", contradictory_evidence=True))):
        result, store, cursor = run(decision, window)
        assert result.requires_human_review and not result.advanced and not store.completed and cursor.expected_step_index == 0

def test_only_application_marks_current_step_missed_after_call_end():
    result, store, cursor = run(StepDecision("not_yet_observed", .99), ended=True)
    assert result.missed_step_id == "s" and store.missed == [("c", "s")] and cursor.expected_step_index == 0
