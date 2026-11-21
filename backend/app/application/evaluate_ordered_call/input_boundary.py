from typing import Protocol

from app.application.evaluate_ordered_call.input_data import EvaluateOrderedCallInputData
from app.application.evaluate_ordered_call.output_data import EvaluateOrderedCallOutputData


class EvaluateOrderedCallInputBoundary(Protocol):
    async def execute(self, data: EvaluateOrderedCallInputData) -> EvaluateOrderedCallOutputData: ...
