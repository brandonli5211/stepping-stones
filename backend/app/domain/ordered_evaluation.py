"""Pure ordered-step evaluation rules.

The model supplies observations; Python owns the saved coaching judgment.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Literal

from app.domain.call_detail import ComparisonRow, SubCheck, SubCheckResult

CONFIDENT_DECISION_THRESHOLD = 0.80
CONFIDENT_FACT_THRESHOLD = 0.70
NOT_STATED = "not_stated"
DIFFERENT_VALUE = "different_value"

StepKind = Literal["simple", "collection", "confirmation"]


@dataclass(frozen=True)
class ProcedureCheck:
    """One persisted procedure sub-check, kept as data for Python to judge."""

    key: str
    kind: str
    points: int
    fields: tuple[str, ...] = ()
    expected: str | None = None
    description: str = ""


@dataclass(frozen=True)
class RequiredStep:
    key: str
    points: int
    name: str = ""
    done_when: str = ""
    logged_action_keys: tuple[str, ...] = ()
    checks: tuple[ProcedureCheck, ...] = ()

    @property
    def kind(self) -> StepKind:
        """Classify from procedure data instead of step-name conventions.

        A procedure's confirmation checks need request/read-back facts; a
        collection step needs a value supplied by either speaker; all other
        steps are simple agent actions.
        """
        if self.checks:
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
    check_outcomes: tuple[SubCheck, ...] = ()
    comparison: tuple[ComparisonRow, ...] = ()


@dataclass(frozen=True)
class CallForEvaluation:
    id: int
    steps: tuple[RequiredStep, ...]
    turn_texts: dict[int, str]
    agent_turn_indices: tuple[int, ...] = ()
    logged_actions: dict[str, object] | None = None
    call_ended: bool = True
    field_types: dict[str, str] = field(default_factory=dict)
    field_hints: dict[str, str] = field(default_factory=dict)
    system_record: dict[str, object] = field(default_factory=dict)


def quote_is_in_turn(quote: str, turn_text: str) -> bool:
    """Evidence must be a non-empty, exact substring of its stored turn."""
    return bool(quote) and quote in turn_text


def _normalized(value: object, field_type: str) -> str | Decimal:
    text = " ".join(str(value).casefold().split())
    if field_type == "amount":
        try:
            return Decimal(text.replace("$", "").replace(",", ""))
        except InvalidOperation:
            return text
    if field_type == "phone":
        return "".join(c for c in text if c.isdigit())
    if field_type in ("account", "card_type"):
        return " ".join(w for w in text.split() if w not in {"your", "my", "the", "account", "card"})
    return text


def _matches(reference: object, actual: object, field_type: str) -> bool | None:
    """None means the available observations cannot decide equality."""
    if actual == NOT_STATED:
        return False
    if reference in (None, "", NOT_STATED) or actual in (None, ""):
        return None
    if reference == actual == DIFFERENT_VALUE:
        # Two out-of-list values may denote different things.
        return None
    if DIFFERENT_VALUE in (reference, actual):
        return False
    return _normalized(reference, field_type) == _normalized(actual, field_type)


def _combined(matches: list[bool | None]) -> SubCheckResult:
    if False in matches:
        return "failed"
    if not matches or None in matches:
        return "under_review"
    return "passed"


def _evaluate_check(
    check: ProcedureCheck, call: CallForEvaluation, facts: Mapping[str, str],
    observation: SubCheckResult, comparisons: dict[str, ComparisonRow],
) -> SubCheckResult:
    logged = call.logged_actions or {}
    if check.kind == "confirmation_evidence":
        return observation
    if check.kind == "logged_task_type":
        actual = str(logged.get("task_type") or "").strip().lower().replace(" ", "_")
        return "passed" if actual == check.expected else "failed"

    matches = []
    for key in check.fields:
        requested = facts.get(f"request:{key}")
        read_back = facts.get(f"read_back:{key}")
        field_type = call.field_types.get(key, "")
        if check.kind == "logged_matches_request":
            recorded = logged.get(key)
            match = False if recorded in (None, "") else _matches(requested, recorded, field_type)
            # The detail table has a boolean match column. Only publish determinate
            # comparisons, and never display a choice sentinel as a caller's words.
            if match is not None and requested not in (None, NOT_STATED):
                comparisons[key] = ComparisonRow(
                    key, None if requested == DIFFERENT_VALUE else requested,
                    None if recorded is None else str(recorded), match,
                )
        elif check.kind == "read_back_matches_request":
            match = _matches(requested, read_back, field_type)
        elif check.kind == "stated_matches_system_record":
            match = _matches(call.system_record.get(key), read_back, field_type)
        else:
            return "under_review"
        matches.append(match)
    return _combined(matches)


def evaluate_step(
    step: RequiredStep, decision: StepDecision, evidence_valid: bool, call: CallForEvaluation,
) -> EvaluatedStep | None:
    """Score each rubric item from the evidence needed for that item."""
    observation: SubCheckResult = "under_review"
    if not decision.contradictory and decision.confidence >= CONFIDENT_DECISION_THRESHOLD:
        if decision.choice == "completed_step" and evidence_valid:
            observation = "passed"
        elif decision.choice == "not_yet_observed":
            if not call.call_ended and not step.checks:
                return None
            if call.call_ended:
                observation = "failed"

    comparisons: dict[str, ComparisonRow] = {}
    outcomes = tuple(
        SubCheck(check.key, check.description, check.points,
                 _evaluate_check(check, call, decision.facts or {}, observation, comparisons))
        for check in step.checks
    )
    if outcomes:
        lost = sum(c.points for c in outcomes if c.result == "failed")
        pending = sum(c.points for c in outcomes if c.result == "under_review")
        status = "wrong" if lost else "under_review" if pending else "completed"
    else:
        status = {"passed": "completed", "failed": "missed", "under_review": "under_review"}[observation]
        lost = step.points if status == "missed" else 0
        pending = step.points if status == "under_review" else 0

    return EvaluatedStep(
        step.key, status, lost, pending, decision.evidence if observation == "passed" else None,
        decision.confidence, decision.raw_response, outcomes, tuple(comparisons.values()),
    )
