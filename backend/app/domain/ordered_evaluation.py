"""Pure ordered-step evaluation rules.

The model supplies observations; Python owns the saved coaching judgment.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
from typing import Literal

CONFIDENT_DECISION_THRESHOLD = 0.80
CONFIDENT_ACTION_MATCH_THRESHOLD = 0.70

StepKind = Literal["simple", "collection", "confirmation"]


@dataclass(frozen=True)
class ProcedureCheck:
    """One persisted procedure sub-check, kept as data for Python to judge."""

    key: str
    kind: str
    points: int
    fields: tuple[str, ...] = ()
    expected: str | None = None


@dataclass(frozen=True)
class CheckOutcome:
    key: str
    points_lost: int
    under_review: bool = False


@dataclass(frozen=True)
class RequiredStep:
    key: str
    points: int
    name: str = ""
    done_when: str = ""
    logged_action_keys: tuple[str, ...] = ()
    checks_logged_actions: bool = False
    checks: tuple[ProcedureCheck, ...] = ()

    @property
    def kind(self) -> StepKind:
        """Classify from procedure data instead of step-name conventions.

        A procedure's confirmation checks need request/read-back facts; a
        collection step needs a value supplied by either speaker; all other
        steps are simple agent actions.
        """
        if self.checks or self.checks_logged_actions:
            return "confirmation"
        if self.logged_action_keys:
            return "collection"
        return "simple"


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
    facts: Mapping[str, str] | None = None
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


def next_transcript_cursor(
    cursor: int, decision: StepDecision, evidence_valid: bool
) -> int:
    """Advance only when a confident cited fact was observed.

    The cursor is deliberately inclusive.  A single caller turn can give the
    amount, source, and destination, so later collection steps may cite the
    same turn.  Absence and uncertainty never consume transcript evidence.
    """
    if (
        decision.choice == "completed_step"
        and evidence_valid
        and decision.confidence >= CONFIDENT_DECISION_THRESHOLD
        and decision.evidence is not None
    ):
        return decision.evidence.turn_idx
    return cursor


def _normal(value: object) -> str:
    return " ".join(str(value or "").lower().replace("_", " ").split())


def evaluate_checks(
    checks: tuple[ProcedureCheck, ...], facts: Mapping[str, str], logged_actions: Mapping[str, object]
) -> tuple[CheckOutcome, ...]:
    """Apply procedure comparisons in Python after the model cites facts.

    Fact keys are ``request:<field>`` and ``read_back:<field>``. Missing
    required facts are reviewable, rather than being guessed as failures.
    """
    outcomes = []
    for check in checks:
        if check.kind == "logged_task_type":
            passed = _normal(logged_actions.get("task_type")) == _normal(check.expected)
            outcomes.append(CheckOutcome(check.key, 0 if passed else check.points))
            continue
        if check.kind == "confirmation_evidence":
            # The cited evidence itself is validated by the caller.
            continue
        if check.kind == "logged_matches_request":
            pairs = [(facts.get(f"request:{field}"), logged_actions.get(field)) for field in check.fields]
        elif check.kind == "read_back_matches_request":
            pairs = [(facts.get(f"request:{field}"), facts.get(f"read_back:{field}")) for field in check.fields]
        elif check.kind == "stated_matches_system_record":
            field = check.fields[0] if check.fields else ""
            pairs = [(facts.get(f"read_back:{field}"), logged_actions.get(field))]
        else:
            outcomes.append(CheckOutcome(check.key, check.points, under_review=True))
            continue
        if any(left is None or right is None for left, right in pairs):
            outcomes.append(CheckOutcome(check.key, 0, under_review=True))
        elif all(_normal(left) == _normal(right) for left, right in pairs):
            outcomes.append(CheckOutcome(check.key, 0))
        else:
            outcomes.append(CheckOutcome(check.key, check.points))
    return tuple(outcomes)


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
