"""add analysis columns to audit sessions

Revision ID: 20260311_0004
Revises: 20260310_0003
Create Date: 2026-03-11 00:30:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260311_0004"
down_revision = "20260310_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("audit_sessions", sa.Column("time_stats", sa.JSON(), nullable=True))
    op.add_column("audit_sessions", sa.Column("overlap_per_user", sa.JSON(), nullable=True))
    op.add_column("audit_sessions", sa.Column("small_tasks_per_user", sa.JSON(), nullable=True))
    op.add_column("audit_sessions", sa.Column("big_tasks_per_user", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("audit_sessions", "big_tasks_per_user")
    op.drop_column("audit_sessions", "small_tasks_per_user")
    op.drop_column("audit_sessions", "overlap_per_user")
    op.drop_column("audit_sessions", "time_stats")