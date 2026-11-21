"""Pure ordered-step evaluation rules.

The model supplies observations; Python owns the saved coaching judgment.
"""

from __future__ import annotations

from dataclasses import dataclass

CONFIDENT_DECISION_THRESHOLD = 0.80
CONFIDENT_ACTION_MATCH_THRESHOLD = 0.70


@dataclass(frozen=True)
class RequiredStep:
    key: str
    points: int
    name: str = ""
    done_when: str = ""
    logged_action_keys: tuple[str, ...] = ()
    checks_logged_actions: bool = False


@dataclass(frozen=True)
class DecisionEvidence:
    turn_idx: int
    quote: str


@dataclass(frozen=True)
class StepDecision:
    choice: str
    confidence: float
    evidence: DecisionEvidence | None = None
    contradictory: bool = False
    logged_actions_match: bool | None = True
    action_confidence: float | None = None
    raw_response: dict | None = None


@dataclass(frozen=True)
class EvaluatedStep:
    key: str
    status: str
    points_lost: int
    points_under_review: int
    evidence: DecisionEvidence | None
    decision_confidence: float | None = None
    decision_response: dict | None = None


@dataclass(frozen=True)
class CallForEvaluation:
    id: int
    steps: tuple[RequiredStep, ...]
    turn_texts: dict[int, str]
    agent_turn_indices: tuple[int, ...] = ()
    logged_actions: dict[str, object] | None = None
    call_ended: bool = True


def quote_is_in_turn(quote: str, turn_text: str) -> bool:
    """Evidence must be a non-empty, exact substring of its stored turn."""
    return bool(quote) and quote in turn_text


def evaluate_step(
    step: RequiredStep, decision: StepDecision, evidence_valid: bool, call_ended: bool = False
) -> EvaluatedStep | None:
    """Turn one model observation into a stored step judgment."""
    # An observed completion must cite exact evidence.  A negative observation
    # intentionally has no quote and is valid unless it is low-confidence or
    # explicitly contradictory.
    action_is_uncertain = (
        decision.logged_actions_match is None
        or (decision.action_confidence is not None and decision.action_confidence < CONFIDENT_ACTION_MATCH_THRESHOLD)
    )
    action_is_confident_mismatch = (
        decision.logged_actions_match is False
        and decision.action_confidence is not None
        and decision.action_confidence >= CONFIDENT_ACTION_MATCH_THRESHOLD
    )
    if action_is_confident_mismatch:
        return EvaluatedStep(step.key, "wrong", step.points, 0, decision.evidence,
                             decision.confidence, decision.raw_response)
    completion_lacks_evidence = decision.choice == "completed_step" and not evidence_valid
    review = (
        decision.confidence < CONFIDENT_DECISION_THRESHOLD
        or decision.contradictory
        or action_is_uncertain
        or completion_lacks_evidence
    )
    if review or decision.choice not in {"completed_step", "not_yet_observed"}:
        return EvaluatedStep(step.key, "under_review", 0, step.points, decision.evidence,
                             decision.confidence, decision.raw_response)
    if decision.choice == "not_yet_observed" and not call_ended:
        return None
    if decision.choice == "not_yet_observed":
        return EvaluatedStep(step.key, "missed", step.points, 0, None, decision.confidence, decision.raw_response)
    return EvaluatedStep(step.key, "completed", 0, 0, decision.evidence,
                         decision.confidence, decision.raw_response)
