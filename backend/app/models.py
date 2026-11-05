from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class AppMeta(Base):
    """Non-coaching starting table. Rows are optional and are not seeded."""

    __tablename__ = "app_meta"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)


class Student(Base):
    """A student: first name, last name and age."""

    __tablename__ = "students"
    __table_args__ = (CheckConstraint("age >= 0", name="ck_students_age"),)

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    first_name: Mapped[str] = mapped_column(Text, nullable=False)
    last_name: Mapped[str] = mapped_column(Text, nullable=False)
    age: Mapped[int] = mapped_column(SmallInteger, nullable=False)


# --- Calls: one analysed call, its turns and its steps -------------------------------------------

CALL_STATUSES = ("pending", "scored", "needs_review", "failed")
STEP_STATUSES = ("completed", "missed", "wrong", "under_review")
SEVERITIES = ("none", "slip", "inaccuracy", "mistake", "critical")


def _in(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


class Agent(Base):
    """A contact-centre agent. Every call belongs to one agent, and agents only see their own calls."""

    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False, server_default="agent")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Procedure(Base):
    """One version of the rules for a call type: the whole schema3 JSON (docs/procedures/schema3).

    Only one version per call type can be active. Calls point at the version they were scored against.
    """

    __tablename__ = "procedures"
    __table_args__ = (
        UniqueConstraint("call_type", "version"),
        Index("uq_procedures_one_active", "call_type", unique=True, postgresql_where=text("is_active")),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    call_type: Mapped[str] = mapped_column(Text, nullable=False)  # snake_case, e.g. transfer_money
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)  # e.g. Transfer money
    rules: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Call(Base):
    """One call and the result of analysing it. The master view reads this table alone."""

    __tablename__ = "calls"
    __table_args__ = (
        CheckConstraint(_in("status", CALL_STATUSES), name="ck_calls_status"),
        CheckConstraint("score BETWEEN 0 AND 100", name="ck_calls_score"),
        Index("ix_calls_agent_started", "agent_id", text("started_at DESC")),
        Index("ix_calls_call_type", "call_type"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    external_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)  # the call id in the URL
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"), nullable=False)
    call_type: Mapped[str] = mapped_column(Text, nullable=False)
    procedure_id: Mapped[int] = mapped_column(ForeignKey("procedures.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="pending")
    score: Mapped[int | None] = mapped_column(SmallInteger)  # null until scored, and when needs_review
    points_lost: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    steps_total: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")
    steps_completed: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")
    steps_missed: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")
    steps_wrong: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")
    steps_under_review: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")
    summary: Mapped[str | None] = mapped_column(Text)  # the sentence under the score on the detail view

    # The metadata file as received, including the dataset's answer key (`tasks`). Never send that to the model.
    raw_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    # The transcript file as received (every field: dialog_acts, emotion, word timings...). call_turns is the clean copy.
    raw_transcript: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    model: Mapped[str | None] = mapped_column(Text)  # e.g. deepseek-r1:8b
    prompt_version: Mapped[str | None] = mapped_column(Text)
    model_output: Mapped[str | None] = mapped_column(Text)  # the model's raw answer, for debugging
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    turns: Mapped[list["CallTurn"]] = relationship(back_populates="call", order_by="CallTurn.idx", cascade="all, delete-orphan")
    steps: Mapped[list["CallStep"]] = relationship(back_populates="call", order_by="CallStep.position", cascade="all, delete-orphan")


class CallTurn(Base):
    """One turn of the conversation, in order. Evidence on a step points at a turn here."""

    __tablename__ = "call_turns"
    __table_args__ = (CheckConstraint(_in("speaker", ("agent", "caller")), name="ck_call_turns_speaker"),)

    call_id: Mapped[int] = mapped_column(ForeignKey("calls.id", ondelete="CASCADE"), primary_key=True)
    idx: Mapped[int] = mapped_column(Integer, primary_key=True)  # the turn number the model cites, from 1
    speaker: Mapped[str] = mapped_column(Text, nullable=False)
    start_seconds: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))  # null if the file has no timing
    text: Mapped[str] = mapped_column(Text, nullable=False)  # human_transcript, else transcript
    machine_text: Mapped[str | None] = mapped_column(Text)  # transcript (speech recognition)

    call: Mapped[Call] = relationship(back_populates="turns")


class CallStep(Base):
    """One required step of one call, with its result. name, position and points are copied from the procedure
    so that changing the rules later does not change old calls."""

    __tablename__ = "call_steps"
    __table_args__ = (
        UniqueConstraint("call_id", "position"),
        ForeignKeyConstraint(
            ["call_id", "evidence_turn_idx"], ["call_turns.call_id", "call_turns.idx"], name="fk_call_steps_evidence_turn"
        ),
        CheckConstraint(_in("status", STEP_STATUSES), name="ck_call_steps_status"),
        CheckConstraint(_in("severity", SEVERITIES), name="ck_call_steps_severity"),
        CheckConstraint("points_lost >= 0 AND points_lost <= points", name="ck_call_steps_points_lost"),
        Index("ix_call_steps_not_completed", "call_id", postgresql_where=text("status <> 'completed'")),
    )

    call_id: Mapped[int] = mapped_column(ForeignKey("calls.id", ondelete="CASCADE"), primary_key=True)
    step_key: Mapped[str] = mapped_column(Text, primary_key=True)  # e.g. collect_transfer_amount
    position: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # order in the procedure, from 1
    name: Mapped[str] = mapped_column(Text, nullable=False)  # e.g. Collect transfer amount
    points: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    status: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False, server_default="none")
    points_lost: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")
    points_under_review: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")
    detail: Mapped[str | None] = mapped_column(Text)  # why, in one sentence
    evidence_turn_idx: Mapped[int | None] = mapped_column(Integer)
    evidence_quote: Mapped[str | None] = mapped_column(Text)  # words from that turn, verified word for word
    coaching: Mapped[str | None] = mapped_column(Text)  # "Next time, say something like ..."

    # Shown only on the step detail panel, never filtered on, so they stay JSON.
    sub_checks: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))  # rows with points lost
    comparison: Mapped[list | None] = mapped_column(JSONB)  # field / caller asked / logged / result table

    call: Mapped[Call] = relationship(back_populates="steps")
