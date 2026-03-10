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
CLOCKIFY_API_KEY = os.getenv("TIME_AUDIT_CLOCKIFY_API_KEY")
CLOCKIFY_API_BASE_URL = os.getenv("TIME_AUDIT_CLOCKIFY_API_BASE_URL", "https://api.clockify.me/api/v1")
CLOCKIFY_REPORTS_BASE_URL = os.getenv(
    "TIME_AUDIT_CLOCKIFY_REPORTS_BASE_URL",
    "https://reports.api.clockify.me/v1",
)
CLOCKIFY_WORKSPACE_ID = os.getenv("TIME_AUDIT_CLOCKIFY_WORKSPACE_ID")


def require_admin_seed_password() -> str:
    if not ADMIN_SEED_PASSWORD:
        raise RuntimeError("TIME_AUDIT_ADMIN_PASSWORD must be set in .env before seeding users.")
    return ADMIN_SEED_PASSWORD


def require_clockify_api_key() -> str:
    if not CLOCKIFY_API_KEY:
        raise RuntimeError("TIME_AUDIT_CLOCKIFY_API_KEY must be set in .env before fetching Clockify reports.")
    return CLOCKIFY_API_KEY