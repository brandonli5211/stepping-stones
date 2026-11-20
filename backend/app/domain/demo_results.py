"""Pure rules for applying curated demo results to stored calls.

Standard library only. No FastAPI, SQLAlchemy, Alembic, or psycopg.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

TORONTO = ZoneInfo("America/Toronto")

COMPLETED, MISSED, WRONG = "completed", "missed", "wrong"


@dataclass(frozen=True)
class SeverityBand:
    name: str
    min_lost: int
    max_lost: int | None  # None: no upper bound


@dataclass(frozen=True)
class ResultsRow:
    demo_id: str
    external_id: str
    call_type: str
    date: str
    time: str
    missed: frozenset[str]
    wrong: frozenset[str]
    # Optional hand-labelled evidence for one missed or wrong step, kept raw so that problems name the row.
    evidence_step: str = ""
    evidence_turn: str = ""
    evidence_quote: str = ""


@dataclass(frozen=True)
class StepEvidence:
    step: str
    turn: int
    quote: str


@dataclass(frozen=True)
class StoredStep:
    key: str
    name: str
    points: int
    status: str
    detail: str | None


@dataclass(frozen=True)
class StoredCall:
    external_id: str
    call_type: str
    steps: tuple[StoredStep, ...]


@dataclass(frozen=True)
class ScoredStep:
    key: str
    status: str
    severity: str
    points_lost: int
    detail: str | None
    evidence_turn: int | None = None
    evidence_quote: str | None = None


@dataclass(frozen=True)
class ScoredCall:
    external_id: str
    started_at: datetime
    score: int
    points_lost: int
    steps_total: int
    steps_completed: int
    steps_missed: int
    steps_wrong: int
    steps: tuple[ScoredStep, ...]


def parse_step_keys(cell: str | None) -> frozenset[str]:
    """Split a semicolon-separated cell into trimmed, non-empty step keys."""
    return frozenset(part.strip() for part in (cell or "").split(";") if part.strip())


def toronto_start(date: str, time: str) -> datetime:
    """Read YYYY-MM-DD and HH:MM as America/Toronto local time; return it in UTC.

    Raises ValueError when the date or time is malformed.
    """
    local = datetime.strptime(f"{date.strip()} {time.strip()}", "%Y-%m-%d %H:%M")
    return local.replace(tzinfo=TORONTO).astimezone(timezone.utc)


def severity_for(bands: Sequence[SeverityBand], lost: int) -> str:
    """Name of the band that covers `lost` points; "none" when nothing was lost."""
    if lost <= 0:
        return "none"
    for band in bands:
        if band.min_lost <= lost and (band.max_lost is None or lost <= band.max_lost):
            return band.name
    return bands[-1].name


def duplicate_problems(rows: Sequence[ResultsRow]) -> list[str]:
    """One problem for every row after the first that names the same call."""
    seen: set[str] = set()
    problems = []
    for row in rows:
        if row.external_id in seen:
            problems.append(f"{row.demo_id}: call {row.external_id} listed more than once")
        seen.add(row.external_id)
    return problems


def row_problems(row: ResultsRow, stored: StoredCall | None) -> list[str]:
    """Everything wrong with one row against its stored call. Empty when the row is valid."""
    prefix = f"{row.demo_id}: "
    if stored is None:
        return [prefix + "call not loaded"]
    problems = []
    if not stored.steps:
        problems.append(prefix + "call has no rubric steps (load with --demo-results)")
    if row.call_type != stored.call_type:
        problems.append(prefix + f"call_type {row.call_type}, loaded call is {stored.call_type}")
    if stored.steps:
        known = {step.key for step in stored.steps}
        problems += [prefix + f"unknown step {key}" for key in sorted((row.missed | row.wrong) - known)]
    problems += [prefix + f"step {key} is both missed and wrong" for key in sorted(row.missed & row.wrong)]
    try:
        toronto_start(row.date, row.time)
    except ValueError:
        problems.append(prefix + f"bad date/time {row.date} {row.time}")
    return problems


def _evidence_values(row: ResultsRow) -> tuple[str, str, str]:
    return row.evidence_step.strip(), row.evidence_turn.strip(), row.evidence_quote.strip()


def has_evidence(row: ResultsRow) -> bool:
    """True when any of the row's three evidence values is filled in."""
    return any(_evidence_values(row))


def evidence_problems(row: ResultsRow, turns: Mapping[int, str]) -> list[str]:
    """Everything wrong with the row's evidence against its call's stored turns (turn number -> text).

    Empty when the row has no evidence or the evidence is valid. The quote must appear word for word (exact,
    case-sensitive) in the turn it names.
    """
    if not has_evidence(row):
        return []
    prefix = f"{row.demo_id}: "
    step, turn, quote = _evidence_values(row)
    if not (step and turn and quote):
        return [prefix + "evidence needs evidence_step, evidence_turn and evidence_quote"]
    if not (turn.isascii() and turn.isdigit()) or int(turn) < 1:
        return [prefix + f"bad evidence turn {turn}"]
    problems = []
    if step not in row.missed | row.wrong:
        problems.append(prefix + f"evidence step {step} is not missed or wrong")
    number = int(turn)
    if number not in turns:
        problems.append(prefix + f"call has no turn {number}")
    elif quote not in turns[number]:
        problems.append(prefix + f"quote not in turn {number}")
    return problems


def evidence_for(row: ResultsRow) -> StepEvidence | None:
    """The row's evidence, or None. Call only for a row whose evidence_problems are empty."""
    if not has_evidence(row):
        return None
    step, turn, quote = _evidence_values(row)
    return StepEvidence(step=step, turn=int(turn), quote=quote)


def score_call(row: ResultsRow, stored: StoredCall, bands: Sequence[SeverityBand]) -> ScoredCall:
    """New step results and call totals for a valid row (see row_problems and evidence_problems).

    The step named by the row's evidence carries it; every other step has none.
    """
    evidence = evidence_for(row)
    steps = []
    counts = {COMPLETED: 0, MISSED: 0, WRONG: 0}
    total_lost = 0
    for step in stored.steps:
        status = MISSED if step.key in row.missed else WRONG if step.key in row.wrong else COMPLETED
        lost = 0 if status == COMPLETED else step.points
        cited = evidence is not None and evidence.step == step.key
        steps.append(ScoredStep(
            key=step.key,
            status=status,
            severity=severity_for(bands, lost),
            points_lost=lost,
            detail=step.detail if status == step.status else None,
            evidence_turn=evidence.turn if cited else None,
            evidence_quote=evidence.quote if cited else None,
        ))
        counts[status] += 1
        total_lost += lost
    return ScoredCall(
        external_id=stored.external_id,
        started_at=toronto_start(row.date, row.time),
        score=max(0, 100 - total_lost),
        points_lost=total_lost,
        steps_total=len(steps),
        steps_completed=counts[COMPLETED],
        steps_missed=counts[MISSED],
        steps_wrong=counts[WRONG],
        steps=tuple(steps),
    )
