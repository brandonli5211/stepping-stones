"""Database tables (SQLAlchemy models).

One class = one table. One attribute = one column.
Only conversations and turns exist so far. Templates, steps and call scores
will be added here as the product grows (see docs/TECH_STACK.md, "Where new code goes").
"""
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    # e.g. "HVB-0001"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    # e.g. "hvb-speaker-17" — lets us follow one agent across calls
    agent_id: Mapped[str] = mapped_column(String, index=True)
    # e.g. "replace card" — decides which template a call is scored against
    task_type: Mapped[str] = mapped_column(String, index=True)
    # what the agent logged during the call (customer_record.captured_by_agent), kept as JSON
    captured_by_agent: Mapped[dict] = mapped_column(JSONB, default=dict)

    turns: Mapped[list["Turn"]] = relationship(
        back_populates="conversation",
        order_by="Turn.turn_number",
        cascade="all, delete-orphan",
    )


class Turn(Base):
    __tablename__ = "turns"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    turn_number: Mapped[int]
    speaker: Mapped[str] = mapped_column(String)  # "agent" or "customer"
    text: Mapped[str] = mapped_column(Text)
    dialog_acts: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    conversation: Mapped[Conversation] = relationship(back_populates="turns")
