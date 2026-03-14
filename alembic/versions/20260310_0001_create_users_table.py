"""create users table

Revision ID: 20260310_0001
Revises: 
Create Date: 2026-03-10 00:30:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from pwdlib import PasswordHash

from backend.settings import ADMIN_SEED_FULL_NAME, ADMIN_SEED_USERNAME, require_admin_seed_password


# revision identifiers, used by Alembic.
revision = "20260310_0001"
down_revision = None
branch_labels = None
depends_on = None


password_hash = PasswordHash.recommended()


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.Enum("Admin", "Developer", "Reviewer", name="role", native_enum=False), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    users_table = sa.table(
        "users",
        sa.column("username", sa.String()),
        sa.column("full_name", sa.String()),
        sa.column("password_hash", sa.String()),
        sa.column("role", sa.String()),
        sa.column("is_active", sa.Boolean()),
    )

    op.bulk_insert(
        users_table,
        [
            {
                "username": ADMIN_SEED_USERNAME,
                "full_name": ADMIN_SEED_FULL_NAME,
                "password_hash": password_hash.hash(require_admin_seed_password()),
                "role": "Admin",
                "is_active": True,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")