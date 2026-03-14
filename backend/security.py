import os
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from backend.settings import BASE_DIR  # noqa: F401


AUTH_SECRET = os.getenv(
    "TIME_AUDIT_AUTH_SECRET",
    "change-me-in-production-please-use-a-long-random-secret",
)
AUTH_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("TIME_AUDIT_ACCESS_TOKEN_EXPIRE_MINUTES", "720"))

password_hash = PasswordHash.recommended()


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(subject: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": subject,
        "exp": expires_at,
    }
    return jwt.encode(payload, AUTH_SECRET, algorithm=AUTH_ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, AUTH_SECRET, algorithms=[AUTH_ALGORITHM])