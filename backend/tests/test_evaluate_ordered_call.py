import asyncio

from app.application.evaluate_ordered_call.input_data import EvaluateOrderedCallInputData
from app.application.evaluate_ordered_call.interactor import EvaluateOrderedCallInteractor
from app.domain.ordered_evaluation import CallForEvaluation, DecisionEvidence, RequiredStep, StepDecision


class Store:
    def __init__(self, call):
        self.call = call
        self.saved = None

    async def load_for_evaluation(self, call_id):
        return self.call if call_id == self.call.id else None

    async def save_evaluation(self, call, steps):
        self.saved = (call.id, steps)


class Model:
    def __init__(self, decisions):
        self.decisions = iter(decisions)

    async def decide(self, call, step):
        return next(self.decisions)


class Presenter:
    def present(self, output):
        return output


def test_under_review_step_does_not_prevent_later_steps_from_being_evaluated():
    call = CallForEvaluation(
        7,
        (RequiredStep("greet", 2), RequiredStep("verify", 3), RequiredStep("close", 5)),
        {1: "Welcome"},
    )
    store = Store(call)
    output = asyncio.run(EvaluateOrderedCallInteractor(
        store, Model((
            StepDecision("completed_step", .79, DecisionEvidence(1, "Welcome")),
            StepDecision("completed_step", .99, DecisionEvidence(1, "Welcome")),
            StepDecision("not_yet_observed", .99),
        )), Presenter()
    ).execute(EvaluateOrderedCallInputData(7)))
    assert [step.status for step in store.saved[1]] == ["under_review", "completed", "missed"]
    assert (output.completed, output.under_review, output.missed) == (1, 1, 1)


def test_missed_step_does_not_prevent_later_steps_from_being_evaluated():
    call = CallForEvaluation(7, (RequiredStep("greet", 2), RequiredStep("close", 5)), {1: "Welcome"})
    store = Store(call)
    output = asyncio.run(EvaluateOrderedCallInteractor(
        store, Model((
            StepDecision("not_yet_observed", .99),
            StepDecision("completed_step", .99, DecisionEvidence(1, "Welcome")),
        )), Presenter()
    ).execute(EvaluateOrderedCallInputData(7)))
    assert [step.status for step in store.saved[1]] == ["missed", "completed"]
    assert (output.missed, output.completed) == (1, 1)
