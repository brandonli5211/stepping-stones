"""CLI controller/presenter for the ordered evaluator."""

from __future__ import annotations

from dataclasses import asdict

from app.application.evaluate_ordered_call.input_data import EvaluateOrderedCallInputData
from app.application.evaluate_ordered_call.output_data import EvaluateOrderedCallOutputData


class AnalyzePresenter:
    """Presents the use case's output as stable, JSON-friendly command data."""

    def present(self, output: EvaluateOrderedCallOutputData) -> EvaluateOrderedCallOutputData:
        return output

    @staticmethod
    def as_dict(output: EvaluateOrderedCallOutputData) -> dict[str, int]:
        return asdict(output)


async def evaluate_one(interactor, call_id: int) -> EvaluateOrderedCallOutputData:
    """Translate a CLI id into input-boundary data; no SQL or environment access here."""
    return await interactor.execute(EvaluateOrderedCallInputData(call_id))
