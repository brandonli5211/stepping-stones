from dataclasses import dataclass, field
from typing import Any


COMPLETED_STEP = "completed_step"
NOT_YET_OBSERVED = "not_yet_observed"


@dataclass(frozen=True)
class ProcedureStep:
    id: str
    objective: str
    evidence_requirements: tuple[str, ...] = ()
    acceptable_variants: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = ()


@dataclass
class CallCursor:
    expected_step_index: int
    agent_turn_index: int
    call_ended: bool = False


@dataclass(frozen=True)
class AgentTurnWindow:
    agent_turn: str
    surrounding_context: tuple[str, ...] = ()
    contradictory_evidence: bool = False


@dataclass(frozen=True)
class StepDecision:
    choice: str
    confidence: float
    evidence_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvaluationResult:
    advanced: bool
    requires_human_review: bool
    missed_step_id: str | None = None
