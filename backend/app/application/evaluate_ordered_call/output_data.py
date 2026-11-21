from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluateOrderedCallOutputData:
    call_id: int
    completed: int
    wrong: int
    missed: int
    under_review: int
