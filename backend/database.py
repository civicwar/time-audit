import os

from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.settings import (
    ADMIN_SEED_FULL_NAME,
    ADMIN_SEED_USERNAME,
    DATABASE_URL,
    require_admin_seed_password,
)


connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db() -> None:
    with engine.connect():
        pass
    seed_default_users()


def seed_default_users() -> None:
    from backend.models import Role, User
    from backend.security import get_password_hash

    if not inspect(engine).has_table("users"):
        return

    with SessionLocal() as session:
        existing_admin = session.execute(
            select(User.id).where(User.username == ADMIN_SEED_USERNAME)
        ).scalar_one_or_none()
        if existing_admin is not None:
            return

        session.add(
            User(
                username=ADMIN_SEED_USERNAME,
                full_name=ADMIN_SEED_FULL_NAME,
                password_hash=get_password_hash(require_admin_seed_password()),
                role=Role.ADMIN,
                is_active=True,
            )
        )
        session.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
