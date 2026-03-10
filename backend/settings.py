import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DEFAULT_DATABASE_URL = f"sqlite:///{BASE_DIR / 'time_audit.db'}"
DATABASE_URL = os.getenv("TIME_AUDIT_DATABASE_URL", DEFAULT_DATABASE_URL)
ADMIN_SEED_USERNAME = "admin"
ADMIN_SEED_FULL_NAME = "Administrator"
ADMIN_SEED_PASSWORD = os.getenv("TIME_AUDIT_ADMIN_PASSWORD")


def require_admin_seed_password() -> str:
    if not ADMIN_SEED_PASSWORD:
        raise RuntimeError("TIME_AUDIT_ADMIN_PASSWORD must be set in .env before seeding users.")
    return ADMIN_SEED_PASSWORD