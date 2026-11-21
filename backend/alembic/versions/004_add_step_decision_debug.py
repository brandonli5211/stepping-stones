"""add per-step Decisions debug data

Revision ID: 004
Revises: 003
Create Date: 2026-11-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("call_steps", sa.Column("decision_confidence", sa.Float(), nullable=True))
    op.add_column("call_steps", sa.Column("decision_response", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("call_steps", "decision_response")
    op.drop_column("call_steps", "decision_confidence")
