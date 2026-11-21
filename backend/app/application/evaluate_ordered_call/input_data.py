from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluateOrderedCallInputData:
    call_id: int
