"""create agents, procedures, calls, call_turns, call_steps

Revision ID: 002
Revises: 001
Create Date: 2026-11-02

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _created_at() -> sa.Column:
    return sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)


def upgrade() -> None:
    op.create_table(
        "agents",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), server_default="agent", nullable=False),
        _created_at(),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "procedures",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("call_type", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("rules", postgresql.JSONB(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        _created_at(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("call_type", "version"),
    )
    op.create_index("uq_procedures_one_active", "procedures", ["call_type"], unique=True, postgresql_where=sa.text("is_active"))

    op.create_table(
        "calls",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("external_id", sa.Text(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("call_type", sa.Text(), nullable=False),
        sa.Column("procedure_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("status", sa.Text(), server_default="pending", nullable=False),
        sa.Column("score", sa.SmallInteger(), nullable=True),
        sa.Column("points_lost", sa.Integer(), server_default="0", nullable=False),
        sa.Column("steps_total", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("steps_completed", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("steps_missed", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("steps_wrong", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("steps_under_review", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("raw_metadata", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("model", sa.Text(), nullable=True),
        sa.Column("prompt_version", sa.Text(), nullable=True),
        sa.Column("model_output", sa.Text(), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True),
        _created_at(),
        sa.CheckConstraint("status IN ('pending', 'scored', 'needs_review', 'failed')", name="ck_calls_status"),
        sa.CheckConstraint("score BETWEEN 0 AND 100", name="ck_calls_score"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["procedure_id"], ["procedures.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_id"),
    )
    op.create_index("ix_calls_agent_started", "calls", ["agent_id", sa.text("started_at DESC")])
    op.create_index("ix_calls_call_type", "calls", ["call_type"])

    op.create_table(
        "call_turns",
        sa.Column("call_id", sa.Integer(), nullable=False),
        sa.Column("idx", sa.Integer(), nullable=False),
        sa.Column("speaker", sa.Text(), nullable=False),
        sa.Column("start_seconds", sa.Numeric(8, 2), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("machine_text", sa.Text(), nullable=True),
        sa.CheckConstraint("speaker IN ('agent', 'caller')", name="ck_call_turns_speaker"),
        sa.ForeignKeyConstraint(["call_id"], ["calls.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("call_id", "idx"),
    )

    op.create_table(
        "call_steps",
        sa.Column("call_id", sa.Integer(), nullable=False),
        sa.Column("step_key", sa.Text(), nullable=False),
        sa.Column("position", sa.SmallInteger(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("points", sa.SmallInteger(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), server_default="none", nullable=False),
        sa.Column("points_lost", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("points_under_review", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("evidence_turn_idx", sa.Integer(), nullable=True),
        sa.Column("evidence_quote", sa.Text(), nullable=True),
        sa.Column("coaching", sa.Text(), nullable=True),
        sa.Column("sub_checks", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("comparison", postgresql.JSONB(), nullable=True),
        sa.CheckConstraint("status IN ('completed', 'missed', 'wrong', 'under_review')", name="ck_call_steps_status"),
        sa.CheckConstraint(
            "severity IN ('none', 'slip', 'inaccuracy', 'mistake', 'critical')", name="ck_call_steps_severity"
        ),
        sa.CheckConstraint("points_lost >= 0 AND points_lost <= points", name="ck_call_steps_points_lost"),
        sa.ForeignKeyConstraint(["call_id"], ["calls.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["call_id", "evidence_turn_idx"], ["call_turns.call_id", "call_turns.idx"], name="fk_call_steps_evidence_turn"
        ),
        sa.PrimaryKeyConstraint("call_id", "step_key"),
        sa.UniqueConstraint("call_id", "position"),
    )
    op.create_index("ix_call_steps_not_completed", "call_steps", ["call_id"], postgresql_where=sa.text("status <> 'completed'"))


def downgrade() -> None:
    op.drop_table("call_steps")
    op.drop_table("call_turns")
    op.drop_table("calls")
    op.drop_table("procedures")
    op.drop_table("agents")
