"""Typed response schema for GET /calls/{id} (contract: docs/api-contract.md). Outer layer: Pydantic lives here only."""

from __future__ import annotations

from typing import Literal, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

Severity = Literal["none", "slip", "inaccuracy", "mistake", "critical"]

# Call types that have their own type_details variant. They may never come back as an empty block.
TYPES_WITH_DETAILS = frozenset({"transfer_money"})


class _Out(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HeaderOut(_Out):
    call_id: int
    external_id: str
    call_type: str
    call_type_name: str
    summary: str | None


class ScoreOut(_Out):
    score: int | None = Field(description="100 minus points_lost; null when the call has no steps yet")
    out_of: int
    steps_done_right: int
    steps_total: int
    points_lost: int
    critical_count: int
    points_under_review: int
    provisional: bool = Field(description="True while points are still under review: show the score as 'so far'")


class NoteOut(_Out):
    kind: Literal["evidence", "wrong"]
    step_key: str
    text: str


class TurnOut(_Out):
    idx: int
    speaker: Literal["agent", "caller"]
    start_seconds: float | None
    text: str
    notes: list[NoteOut]


class SubCheckOut(_Out):
    key: str
    description: str
    points: int
    result: Literal["passed", "failed", "under_review"]


class EvidenceOut(_Out):
    quote: str
    turn_idx: int
    start_seconds: float | None


class StepDetailsOut(_Out):
    description: str | None = Field(description="What the step asks for, from the call's procedure rules")
    detail: str | None
    sub_checks: list[SubCheckOut]
    evidence: EvidenceOut | None
    coaching: str | None


class StepOut(_Out):
    key: str
    position: int
    name: str
    status: Literal["completed", "missed", "wrong", "under_review"]
    severity: Severity
    points: int
    points_lost: int
    points_under_review: int
    details: StepDetailsOut


class FlagOut(_Out):
    step_key: str
    step_name: str
    status: Literal["missed", "wrong"]
    severity: Severity
    points_lost: int
    message: str | None = Field(description="One sentence on what went wrong")


class FieldRowOut(_Out):
    field: str
    label: str
    caller_asked: str | None
    logged: str | None
    result: Literal["match", "mismatch", "reversed"]


class TransferMoneyDetailsOut(_Out):
    type: Literal["transfer_money"]
    fields: list[FieldRowOut]


class EmptyDetailsOut(_Out):
    """Any call type without its own block: only the type."""

    type: str

    @field_validator("type")
    @classmethod
    def _not_a_type_with_details(cls, value: str) -> str:
        if value in TYPES_WITH_DETAILS:
            raise ValueError(f"{value} has its own type_details block and cannot be empty")
        return value


TypeDetailsOut = Union[TransferMoneyDetailsOut, EmptyDetailsOut]


class CallDetailOut(_Out):
    header: HeaderOut
    score: ScoreOut
    transcript: list[TurnOut]
    steps: list[StepOut]
    flags: list[FlagOut]
    type_details: TypeDetailsOut = Field(union_mode="left_to_right", description="Tagged by `type`")
