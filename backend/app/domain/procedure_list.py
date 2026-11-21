"""Display-safe procedure records for the Procedures page."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProcedureStep:
    order: int
    step_name: str
    step_description: str


@dataclass(frozen=True)
class Procedure:
    task_type: str
    name: str
    description: str
    steps: tuple[ProcedureStep, ...]
