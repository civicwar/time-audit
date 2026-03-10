import os
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock


LOGIN_MAX_ATTEMPTS_PER_IP = int(os.getenv("TIME_AUDIT_LOGIN_MAX_ATTEMPTS_PER_IP", "10"))
LOGIN_MAX_ATTEMPTS_PER_USERNAME = int(os.getenv("TIME_AUDIT_LOGIN_MAX_ATTEMPTS_PER_USERNAME", "5"))
LOGIN_ATTEMPT_WINDOW_SECONDS = int(os.getenv("TIME_AUDIT_LOGIN_ATTEMPT_WINDOW_SECONDS", "900"))
LOGIN_LOCKOUT_SECONDS = int(os.getenv("TIME_AUDIT_LOGIN_LOCKOUT_SECONDS", "900"))


@dataclass(frozen=True)
class LockoutState:
    retry_after_seconds: int
    reason: str


class LoginAttemptGuard:
    def __init__(self) -> None:
        self._lock = Lock()
        self._attempts_by_ip: dict[str, deque[datetime]] = {}
        self._attempts_by_username: dict[str, deque[datetime]] = {}
        self._blocked_ip_until: dict[str, datetime] = {}
        self._blocked_username_until: dict[str, datetime] = {}

    def check_lockout(self, client_ip: str, username: str) -> LockoutState | None:
        now = self._now()
        normalized_username = self._normalize_username(username)

        with self._lock:
            self._prune(now)

            blocked_ip_until = self._blocked_ip_until.get(client_ip)
            if blocked_ip_until and blocked_ip_until > now:
                return LockoutState(
                    retry_after_seconds=self._seconds_until(blocked_ip_until, now),
                    reason="Too many failed login attempts from this address.",
                )

            blocked_username_until = self._blocked_username_until.get(normalized_username)
            if blocked_username_until and blocked_username_until > now:
                return LockoutState(
                    retry_after_seconds=self._seconds_until(blocked_username_until, now),
                    reason="Too many failed login attempts for this account.",
                )

        return None

    def register_failure(self, client_ip: str, username: str) -> LockoutState | None:
        now = self._now()
        normalized_username = self._normalize_username(username)
        lockout_until = now + timedelta(seconds=LOGIN_LOCKOUT_SECONDS)

        with self._lock:
            self._prune(now)

            ip_attempts = self._attempts_by_ip.setdefault(client_ip, deque())
            ip_attempts.append(now)

            username_attempts = self._attempts_by_username.setdefault(normalized_username, deque())
            username_attempts.append(now)

            if len(ip_attempts) >= LOGIN_MAX_ATTEMPTS_PER_IP:
                self._blocked_ip_until[client_ip] = lockout_until
                self._attempts_by_ip.pop(client_ip, None)
                return LockoutState(
                    retry_after_seconds=LOGIN_LOCKOUT_SECONDS,
                    reason="Too many failed login attempts from this address.",
                )

            if len(username_attempts) >= LOGIN_MAX_ATTEMPTS_PER_USERNAME:
                self._blocked_username_until[normalized_username] = lockout_until
                self._attempts_by_username.pop(normalized_username, None)
                return LockoutState(
                    retry_after_seconds=LOGIN_LOCKOUT_SECONDS,
                    reason="Too many failed login attempts for this account.",
                )

        return None

    def register_success(self, client_ip: str, username: str) -> None:
        normalized_username = self._normalize_username(username)
        with self._lock:
            self._attempts_by_ip.pop(client_ip, None)
            self._attempts_by_username.pop(normalized_username, None)
            self._blocked_ip_until.pop(client_ip, None)
            self._blocked_username_until.pop(normalized_username, None)

    def _prune(self, now: datetime) -> None:
        cutoff = now - timedelta(seconds=LOGIN_ATTEMPT_WINDOW_SECONDS)

        for attempts in self._attempts_by_ip.values():
            while attempts and attempts[0] < cutoff:
                attempts.popleft()
        for attempts in self._attempts_by_username.values():
            while attempts and attempts[0] < cutoff:
                attempts.popleft()

        self._attempts_by_ip = {key: attempts for key, attempts in self._attempts_by_ip.items() if attempts}
        self._attempts_by_username = {
            key: attempts for key, attempts in self._attempts_by_username.items() if attempts
        }
        self._blocked_ip_until = {
            key: blocked_until for key, blocked_until in self._blocked_ip_until.items() if blocked_until > now
        }
        self._blocked_username_until = {
            key: blocked_until
            for key, blocked_until in self._blocked_username_until.items()
            if blocked_until > now
        }

    @staticmethod
    def _normalize_username(username: str) -> str:
        return username.strip().casefold()

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _seconds_until(until: datetime, now: datetime) -> int:
        return max(1, int((until - now).total_seconds()))


login_attempt_guard = LoginAttemptGuard()