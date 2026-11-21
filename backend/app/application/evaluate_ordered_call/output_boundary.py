from typing import Protocol

from app.application.evaluate_ordered_call.output_data import EvaluateOrderedCallOutputData


class EvaluateOrderedCallOutputBoundary(Protocol):
    def present(self, output: EvaluateOrderedCallOutputData) -> EvaluateOrderedCallOutputData: ...
