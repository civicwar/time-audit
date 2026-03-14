"""sync admin seed and remove extra seeded users

Revision ID: 20260310_0002
Revises: 20260310_0001
Create Date: 2026-03-10 02:15:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from pwdlib import PasswordHash

from backend.settings import ADMIN_SEED_FULL_NAME, ADMIN_SEED_USERNAME, require_admin_seed_password


# revision identifiers, used by Alembic.
revision = "20260310_0002"
down_revision = "20260310_0001"
branch_labels = None
depends_on = None


password_hash = PasswordHash.recommended()


def upgrade() -> None:
    connection = op.get_bind()

    connection.execute(
        sa.text("DELETE FROM users WHERE username IN ('developer', 'reviewer')")
    )

    admin_exists = connection.execute(
        sa.text("SELECT id FROM users WHERE username = :username"),
        {"username": ADMIN_SEED_USERNAME},
    ).scalar_one_or_none()

    hashed_password = password_hash.hash(require_admin_seed_password())
    if admin_exists is None:
        connection.execute(
            sa.text(
                """
                INSERT INTO users (username, full_name, password_hash, role, is_active)
                VALUES (:username, :full_name, :password_hash, 'Admin', 1)
                """
            ),
            {
                "username": ADMIN_SEED_USERNAME,
                "full_name": ADMIN_SEED_FULL_NAME,
                "password_hash": hashed_password,
            },
        )
        return

    connection.execute(
        sa.text(
            """
            UPDATE users
            SET full_name = :full_name, password_hash = :password_hash, role = 'Admin', is_active = 1
            WHERE username = :username
            """
        ),
        {
            "username": ADMIN_SEED_USERNAME,
            "full_name": ADMIN_SEED_FULL_NAME,
            "password_hash": hashed_password,
        },
    )


def downgrade() -> None:
    pass