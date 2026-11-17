"""Call detail: the records read for one call and the pure rules that turn them into what the detail screen shows.

Score, counts, transcript notes, flags and the per-type block are worked out here, from the stored step results
only (constitution Principles I and VII). No framework, ORM or HTTP imports.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Literal, get_args

Speaker = Literal["agent", "caller"]
StepStatus = Literal["completed", "missed", "wrong", "under_review"]
Severity = Literal["none", "slip", "inaccuracy", "mistake", "critical"]
SubCheckResult = Literal["passed", "failed", "under_review"]

OUT_OF = 100


class InvalidCallRecord(ValueError):
    """Stored call data breaks a rule (an unknown status, more points lost than a step is worth...)."""


def _require(value: object, allowed: object, what: str) -> None:
    options = get_args(allowed)
    if value not in options:
        raise InvalidCallRecord(f"{what} is {value!r}; expected one of {', '.join(options)}")


class CallNotFound(LookupError):
    """No stored call has this id."""

    def __init__(self, call_id: int) -> None:
        super().__init__(f"no call with id {call_id}")
        self.call_id = call_id


# --- What is read for one call ---------------------------------------------------------------------------------------


@dataclass(frozen=True)
class TurnRecord:
    idx: int
    speaker: Speaker
    start_seconds: float | None
    text: str

    def __post_init__(self) -> None:
        _require(self.speaker, Speaker, f"turn {self.idx} speaker")


@dataclass(frozen=True)
class SubCheck:
    key: str
    description: str
    points: int
    result: SubCheckResult

    def __post_init__(self) -> None:
        _require(self.result, SubCheckResult, f"sub-check {self.key} result")


@dataclass(frozen=True)
class ComparisonRow:
    field: str
    caller_asked: str | None
    logged: str | None
    match: bool


@dataclass(frozen=True)
class StepRecord:
    key: str
    position: int
    name: str
    points: int
    status: StepStatus
    severity: Severity = "none"
    points_lost: int = 0
    points_under_review: int = 0
    detail: str | None = None
    evidence_turn_idx: int | None = None
    evidence_quote: str | None = None
    coaching: str | None = None
    sub_checks: tuple[SubCheck, ...] = ()
    comparison: tuple[ComparisonRow, ...] = ()
    description: str | None = None  # from the call's procedure rules

    def __post_init__(self) -> None:
        _require(self.status, StepStatus, f"step {self.key} status")
        _require(self.severity, Severity, f"step {self.key} severity")
        if not 0 <= self.points_lost <= self.points:
            raise InvalidCallRecord(
                f"step {self.key} points_lost is {self.points_lost}; expected 0 to {self.points}")


@dataclass(frozen=True)
class CallRecord:
    id: int
    external_id: str
    call_type: str
    call_type_name: str
    summary: str | None
    turns: tuple[TurnRecord, ...] = ()
    steps: tuple[StepRecord, ...] = ()


# --- What the rules produce ------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ScoreSummary:
    score: int | None
    steps_done_right: int
    steps_total: int
    points_lost: int
    critical_count: int
    points_under_review: int
    out_of: int = OUT_OF

    @property
    def provisional(self) -> bool:
        return self.points_under_review > 0


@dataclass(frozen=True)
class Note:
    kind: Literal["evidence", "wrong"]
    step_key: str
    text: str


@dataclass(frozen=True)
class Flag:
    step_key: str
    step_name: str
    status: Literal["missed", "wrong"]
    severity: Severity
    points_lost: int
    message: str | None = None


@dataclass(frozen=True)
class Evidence:
    quote: str
    turn_idx: int
    start_seconds: float | None


@dataclass(frozen=True)
class FieldRow:
    field: str
    label: str
    caller_asked: str | None
    logged: str | None
    result: Literal["match", "mismatch", "reversed"]


@dataclass(frozen=True)
class TransferMoneyDetails:
    fields: tuple[FieldRow, ...]
    type: str = "transfer_money"


@dataclass(frozen=True)
class EmptyDetails:
    type: str


TypeDetails = TransferMoneyDetails | EmptyDetails


@dataclass(frozen=True)
class CallHeader:
    call_id: int
    external_id: str
    call_type: str
    call_type_name: str
    summary: str | None


@dataclass(frozen=True)
class TranscriptTurn:
    turn: TurnRecord
    notes: tuple[Note, ...]


@dataclass(frozen=True)
class StepDetail:
    step: StepRecord
    evidence: Evidence | None
    coaching: str | None = None


@dataclass(frozen=True)
class CallDetail:
    header: CallHeader
    score: ScoreSummary
    transcript: tuple[TranscriptTurn, ...]
    steps: tuple[StepDetail, ...]
    flags: tuple[Flag, ...]
    type_details: TypeDetails


# --- Rules -----------------------------------------------------------------------------------------------------------


def _in_order(steps: tuple[StepRecord, ...]) -> tuple[StepRecord, ...]:
    return tuple(sorted(steps, key=lambda s: s.position))


def summarize_score(steps: tuple[StepRecord, ...]) -> ScoreSummary:
    """100 minus the points lost on the steps. No steps yet (a pending call): no score."""
    points_lost = sum(s.points_lost for s in steps)
    return ScoreSummary(
        score=max(0, OUT_OF - points_lost) if steps else None,
        steps_done_right=sum(s.status == "completed" for s in steps),
        steps_total=len(steps),
        points_lost=points_lost,
        critical_count=sum(s.severity == "critical" for s in steps),
        points_under_review=sum(s.points_under_review for s in steps),
    )


def notes_by_turn(steps: tuple[StepRecord, ...]) -> dict[int, tuple[Note, ...]]:
    """Notes for each evidence turn: "Evidence for <step>" on completed steps, "Wrong: <why>" on wrong ones.
    Missed and under-review steps add none."""
    notes: dict[int, list[Note]] = {}
    for s in _in_order(steps):
        if s.evidence_turn_idx is None:
            continue
        if s.status == "completed":
            note = Note("evidence", s.key, f"Evidence for {s.name}")
        elif s.status == "wrong":
            note = Note("wrong", s.key, f"Wrong: {s.detail or s.name}")
        else:
            continue
        notes.setdefault(s.evidence_turn_idx, []).append(note)
    return {idx: tuple(n) for idx, n in notes.items()}


def flags(steps: tuple[StepRecord, ...], call_type: str = "") -> tuple[Flag, ...]:
    """One flag per missed or wrong step, in procedure order. Its message comes from the call type's builder when it
    has one, else from the step's stored reason."""
    build = FLAG_MESSAGE_BUILDERS.get(call_type)
    return tuple(
        Flag(s.key, s.name, s.status, s.severity, s.points_lost,  # type: ignore[arg-type]
             (build(s) if build else None) or s.detail)
        for s in _in_order(steps)
        if s.status in ("missed", "wrong")
    )


def evidence_for(step: StepRecord, turns: tuple[TurnRecord, ...]) -> Evidence | None:
    """The quote that proves the step and the time of its turn. None without both a turn and a quote."""
    if step.evidence_turn_idx is None or not step.evidence_quote:
        return None
    turn = next((t for t in turns if t.idx == step.evidence_turn_idx), None)
    return Evidence(step.evidence_quote, step.evidence_turn_idx, turn.start_seconds if turn else None)


def coaching_for(step: StepRecord) -> str | None:
    """Coaching is for what went wrong: missed and wrong steps only. Completed and under-review steps get none."""
    return step.coaching if step.status in ("missed", "wrong") else None


FLAG_MESSAGE_BUILDERS: Mapping[str, Callable[[StepRecord], str | None]] = {}
