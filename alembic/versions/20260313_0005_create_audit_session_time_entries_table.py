"""create audit session time entries table

Revision ID: 20260313_0005
Revises: 20260311_0004
Create Date: 2026-03-13 00:00:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260313_0005"
down_revision = "20260311_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_session_time_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("audit_session_id", sa.Integer(), nullable=False),
        sa.Column("user_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("start_datetime", sa.DateTime(), nullable=False),
        sa.Column("end_datetime", sa.DateTime(), nullable=False),
        sa.Column("duration_hours", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["audit_session_id"], ["audit_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_session_time_entries_id"), "audit_session_time_entries", ["id"], unique=False)
    op.create_index(
        op.f("ix_audit_session_time_entries_audit_session_id"),
        "audit_session_time_entries",
        ["audit_session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_session_time_entries_user_name"),
        "audit_session_time_entries",
        ["user_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_session_time_entries_start_datetime"),
        "audit_session_time_entries",
        ["start_datetime"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_session_time_entries_start_datetime"), table_name="audit_session_time_entries")
    op.drop_index(op.f("ix_audit_session_time_entries_user_name"), table_name="audit_session_time_entries")
    op.drop_index(op.f("ix_audit_session_time_entries_audit_session_id"), table_name="audit_session_time_entries")
    op.drop_index(op.f("ix_audit_session_time_entries_id"), table_name="audit_session_time_entries")
    op.drop_table("audit_session_time_entries")
