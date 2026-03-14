"""create audit sessions table

Revision ID: 20260310_0003
Revises: 20260310_0002
Create Date: 2026-03-10 11:40:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260310_0003"
down_revision = "20260310_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("run_dir", sa.String(length=64), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False, server_default="clockify"),
        sa.Column("clockify_workspace_id", sa.String(length=64), nullable=True),
        sa.Column("clockify_workspace_name", sa.String(length=255), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("timezone", sa.String(length=128), nullable=True),
        sa.Column("big_task_hours", sa.Float(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_dir"),
    )
    op.create_index(op.f("ix_audit_sessions_id"), "audit_sessions", ["id"], unique=False)
    op.create_index(op.f("ix_audit_sessions_run_dir"), "audit_sessions", ["run_dir"], unique=True)
    op.create_index(op.f("ix_audit_sessions_created_by_user_id"), "audit_sessions", ["created_by_user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_sessions_created_by_user_id"), table_name="audit_sessions")
    op.drop_index(op.f("ix_audit_sessions_run_dir"), table_name="audit_sessions")
    op.drop_index(op.f("ix_audit_sessions_id"), table_name="audit_sessions")
    op.drop_table("audit_sessions")