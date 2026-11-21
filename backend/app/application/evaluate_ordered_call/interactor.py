from collections import Counter
from dataclasses import dataclass

from app.application.evaluate_ordered_call.input_data import EvaluateOrderedCallInputData
from app.application.evaluate_ordered_call.output_boundary import EvaluateOrderedCallOutputBoundary
from app.application.evaluate_ordered_call.output_data import EvaluateOrderedCallOutputData
from app.application.ports import OrderedCallStore, StepDecisionModel
from app.domain.ordered_evaluation import evaluate_step, finalize_remaining, quote_is_in_turn


@dataclass(frozen=True)
class EvaluateOrderedCallInteractor:
    store: OrderedCallStore
    model: StepDecisionModel
    presenter: EvaluateOrderedCallOutputBoundary

    async def execute(self, data: EvaluateOrderedCallInputData) -> EvaluateOrderedCallOutputData:
        call = await self.store.load_for_evaluation(data.call_id)
        if call is None:
            raise LookupError(f"no call with id {data.call_id}")
        results = []
        for index, step in enumerate(call.steps):
            decision = await self.model.decide(call, step)
            evidence_valid = decision.evidence is not None and quote_is_in_turn(
                decision.evidence.quote, call.turn_texts.get(decision.evidence.turn_idx, "")
            )
            result = evaluate_step(step, decision, evidence_valid, call.call_ended)
            if result is None:
                break
            results.append(result)
            if call.call_ended and result.status == "missed":
                results.extend(finalize_remaining(call.steps[index + 1:]))
                break
            if result.status == "under_review":
                if call.call_ended:
                    results.extend(finalize_remaining(call.steps[index + 1:]))
                break
        if call.call_ended and len(results) < len(call.steps):
            results.extend(finalize_remaining(call.steps[len(results):]))
        await self.store.save_evaluation(call, tuple(results))
        counts = Counter(result.status for result in results)
        return self.presenter.present(EvaluateOrderedCallOutputData(
            call.id, counts["completed"], counts["wrong"], counts["missed"], counts["under_review"]
        ))
