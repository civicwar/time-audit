import argparse
import os

from sqlalchemy import select

from backend.database import SessionLocal
from backend.models import Role, User
from backend.security import get_password_hash


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create or update the admin user.")
    parser.add_argument("--username", default="admin", help="Admin username to create or update.")
    parser.add_argument("--full-name", default="Administrator", help="Full name to store on the admin user.")
    parser.add_argument(
        "--password",
        default=os.getenv("TIME_AUDIT_ADMIN_PASSWORD"),
        help="Admin password. Defaults to TIME_AUDIT_ADMIN_PASSWORD.",
    )
    return parser.parse_args()


def upsert_admin(username: str, full_name: str, password: str) -> tuple[str, int]:
    with SessionLocal() as session:
        user = session.execute(select(User).where(User.username == username)).scalar_one_or_none()

        if user is None:
            user = User(
                username=username,
                full_name=full_name,
                password_hash=get_password_hash(password),
                role=Role.ADMIN,
                is_active=True,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return "created", user.id

        user.full_name = full_name
        user.password_hash = get_password_hash(password)
        user.role = Role.ADMIN
        user.is_active = True
        session.add(user)
        session.commit()
        session.refresh(user)
        return "updated", user.id


def main() -> int:
    args = parse_args()
    if not args.password:
        raise SystemExit("Admin password is required. Provide --password or TIME_AUDIT_ADMIN_PASSWORD.")

    action, user_id = upsert_admin(args.username, args.full_name, args.password)
    print(f"Admin user '{args.username}' {action} (id={user_id}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())