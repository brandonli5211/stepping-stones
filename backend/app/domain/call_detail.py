"""Call detail: the records read for one call and the pure rules that turn them into what the detail screen shows.

Score, counts, transcript notes, flags and the per-type block are worked out here, from the stored step results
only (constitution Principles I and VII). No framework, ORM or HTTP imports.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
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


TRANSFER_FIELD_LABELS: Mapping[str, str] = {
    "transfer_amount": "Amount",
    "transfer_source_account": "From",
    "transfer_destination_account": "To",
}


AMOUNT, SOURCE, DESTINATION = TRANSFER_FIELD_LABELS


def _same(a: str | None, b: str | None) -> bool:
    """Two stored values name the same thing (ignoring case and surrounding spaces). Missing never matches."""
    return a is not None and b is not None and a.strip().lower() == b.strip().lower()


def accounts_reversed(source: ComparisonRow | None, destination: ComparisonRow | None) -> bool:
    """The agent logged the caller's two accounts the wrong way round: logged From is the asked To and the reverse."""
    return (
        source is not None and destination is not None
        and not _same(source.caller_asked, destination.caller_asked)
        and _same(source.logged, destination.caller_asked)
        and _same(destination.logged, source.caller_asked)
    )


def _result(row: ComparisonRow, reversed_: bool) -> Literal["match", "mismatch", "reversed"]:
    if row.match:
        return "match"
    return "reversed" if reversed_ else "mismatch"


def transfer_money_details(record: CallRecord) -> TransferMoneyDetails:
    """The Caller asked / Logged / Result table, from the comparison rows stored on the steps: Amount, From, To.
    From and To are both `reversed` when the accounts were swapped."""
    rows = {r.field: r for s in record.steps for r in s.comparison if r.field in TRANSFER_FIELD_LABELS}
    swapped = accounts_reversed(rows.get(SOURCE), rows.get(DESTINATION))
    return TransferMoneyDetails(tuple(
        FieldRow(key, label, rows[key].caller_asked, rows[key].logged,
                 _result(rows[key], swapped and key in (SOURCE, DESTINATION)))
        for key, label in TRANSFER_FIELD_LABELS.items()
        if key in rows
    ))


def _money(value: str) -> str:
    """'114' → '$114', '146.00' → '$146', '12.5' → '$12.50'. Anything that is not a number is kept as it is."""
    try:
        amount = Decimal(value.strip())
    except InvalidOperation:
        return value
    return f"${amount:.0f}" if amount == amount.to_integral_value() else f"${amount:.2f}"


def transfer_flag_message(step: StepRecord) -> str | None:
    """'Moved $114 savings → checking. The caller asked for checking → savings.' from the step's field table.
    None when the table is incomplete or everything matches, so the step's own reason is used instead."""
    rows = {r.field: r for r in step.comparison}
    if not all(key in rows for key in TRANSFER_FIELD_LABELS) or all(r.match for r in rows.values()):
        return None
    amount, source, destination = rows[AMOUNT], rows[SOURCE], rows[DESTINATION]
    if any(r.caller_asked is None for r in (amount, source, destination)):
        return None
    logged = (amount.logged, source.logged, destination.logged)
    if all(v is None for v in logged):
        return (f"Nothing was logged. The caller asked for {_money(amount.caller_asked)} "
                f"{source.caller_asked} → {destination.caller_asked}.")
    if any(v is None for v in logged):
        parts = (f"amount {_money(amount.logged) if amount.logged is not None else 'not logged'}",
                 f"from {source.logged or 'not logged'}",
                 f"to {destination.logged or 'not logged'}")
        return (f"Logged {', '.join(parts)}. The caller asked for {_money(amount.caller_asked)} "
                f"{source.caller_asked} → {destination.caller_asked}.")
    asked_amount = "" if amount.match else f"{_money(amount.caller_asked)} "
    return (f"Moved {_money(amount.logged)} {source.logged} → {destination.logged}. "
            f"The caller asked for {asked_amount}{source.caller_asked} → {destination.caller_asked}.")


FLAG_MESSAGE_BUILDERS: Mapping[str, Callable[[StepRecord], str | None]] = {
    "transfer_money": transfer_flag_message,
}


TYPE_DETAIL_BUILDERS: Mapping[str, Callable[[CallRecord], TypeDetails]] = {
    "transfer_money": transfer_money_details,
}


def type_details(record: CallRecord) -> TypeDetails:
    """The block for this call type. A type without a builder gets an empty block that still names it."""
    build = TYPE_DETAIL_BUILDERS.get(record.call_type)
    return build(record) if build else EmptyDetails(record.call_type)


def build_call_detail(record: CallRecord) -> CallDetail:
    """Everything the call detail screen shows, worked out from one stored call."""
    steps = _in_order(record.steps)
    turns = tuple(sorted(record.turns, key=lambda t: t.idx))
    notes = notes_by_turn(steps)
    return CallDetail(
        header=CallHeader(record.id, record.external_id, record.call_type, record.call_type_name, record.summary),
        score=summarize_score(steps),
        transcript=tuple(TranscriptTurn(t, notes.get(t.idx, ())) for t in turns),
        steps=tuple(StepDetail(s, evidence_for(s, turns), coaching_for(s)) for s in steps),
        flags=flags(steps, record.call_type),
        type_details=type_details(record),
    )
