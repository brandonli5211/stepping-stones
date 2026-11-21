from collections import Counter
from dataclasses import dataclass

from app.application.evaluate_ordered_call.input_data import EvaluateOrderedCallInputData
from app.application.evaluate_ordered_call.output_boundary import EvaluateOrderedCallOutputBoundary
from app.application.evaluate_ordered_call.output_data import EvaluateOrderedCallOutputData
from app.application.ports import OrderedCallStore, StepDecisionModel
from app.domain.ordered_evaluation import evaluate_step, next_transcript_cursor, quote_is_in_turn


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
        transcript_cursor = 1
        for step in call.steps:
            decision = await self.model.decide(call, step, transcript_cursor)
            evidence_valid = (
                decision.evidence is not None
                and decision.evidence.turn_idx >= transcript_cursor
                and quote_is_in_turn(decision.evidence.quote, call.turn_texts.get(decision.evidence.turn_idx, ""))
            )
            result = evaluate_step(step, decision, evidence_valid, call.call_ended)
            if result is None:
                # This command evaluates complete calls. A future streaming caller
                # may stop here and resume later without treating it as a miss.
                continue
            results.append(result)
            transcript_cursor = next_transcript_cursor(transcript_cursor, decision, evidence_valid)
        if call.call_ended and len(results) != len(call.steps):
            raise ValueError("complete-call evaluation requires one result for every procedure step")
        await self.store.save_evaluation(call, tuple(results))
        counts = Counter(result.status for result in results)
        return self.presenter.present(EvaluateOrderedCallOutputData(
            call.id, counts["completed"], counts["wrong"], counts["missed"], counts["under_review"]
        ))
