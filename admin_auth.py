"""Admin authentication, lockout controls, and redacted security logging."""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Mapping

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from database import connection

logger = logging.getLogger(__name__)
PASSWORD_HASHER = PasswordHasher()
MAX_FAILED_ATTEMPTS = 5
FAILURE_WINDOW = timedelta(minutes=15)
LOCKOUT_DURATION = timedelta(minutes=15)
MINIMUM_PASSWORD_LENGTH = 16
DISALLOWED_PROXY_HEADERS = {"x-forwarded-for", "forwarded", "x-real-ip"}
DEFAULT_USERNAMES = {"admin", "administrator", "root", "changeme", "your_admin_username"}


@dataclass(frozen=True)
class AuthenticationResult:
    authenticated: bool
    message: str
    locked: bool = False


@dataclass(frozen=True)
class ClientIdentifier:
    value: str
    proxy_verified: bool


def _value(environment: Mapping[str, str], key: str) -> str:
    return environment.get(key, "").strip()


def _is_placeholder(value: str) -> bool:
    lowered = value.casefold()
    return not value or "<" in value or ">" in value or "your_" in lowered or "example" in lowered or "change-this" in lowered


def validate_admin_configuration(environment: Mapping[str, str] | None = None) -> bool:
    """Accept only a non-default username and structurally valid Argon2id hash."""
    env = os.environ if environment is None else environment
    username = _value(env, "ADMIN_USERNAME")
    password_hash = _value(env, "ADMIN_PASSWORD_HASH")
    if "ADMIN_PASSWORD" in env or _is_placeholder(username) or _is_placeholder(password_hash):
        return False
    if username.casefold() in DEFAULT_USERNAMES or not password_hash.startswith("$argon2id$"):
        return False
    try:
        PASSWORD_HASHER.verify(password_hash, "configuration-validation-probe")
    except VerifyMismatchError:
        return True
    except (InvalidHashError, VerificationError):
        return False
    return False


def resolve_client_identifier(
    headers: Mapping[str, str], session_identifier: str, environment: Mapping[str, str] | None = None
) -> ClientIdentifier:
    """Use proxy identity only when a configured proxy-auth header proves its origin.

    The application deliberately never accepts X-Forwarded-For, Forwarded, or
    X-Real-IP as client identity. Hosting must keep Streamlit private behind the
    configured proxy, which strips client-supplied versions of these headers.
    """
    env = os.environ if environment is None else environment
    client_header = _value(env, "ADMIN_TRUSTED_CLIENT_ID_HEADER").casefold()
    proxy_auth_header = _value(env, "ADMIN_TRUSTED_PROXY_AUTH_HEADER").casefold()
    proxy_auth_value = _value(env, "ADMIN_TRUSTED_PROXY_AUTH_VALUE")
    normalized_headers = {key.casefold(): value for key, value in headers.items()}
    if (
        client_header
        and proxy_auth_header
        and proxy_auth_value
        and client_header not in DISALLOWED_PROXY_HEADERS
        and proxy_auth_header not in DISALLOWED_PROXY_HEADERS
    ):
        client_value = normalized_headers.get(client_header, "").strip()
        supplied_proxy_auth = normalized_headers.get(proxy_auth_header, "")
        if client_value and hmac.compare_digest(supplied_proxy_auth, proxy_auth_value):
            return ClientIdentifier(client_value, proxy_verified=True)
    return ClientIdentifier(session_identifier, proxy_verified=False)


def hash_client_identifier(identifier: str) -> str:
    return hashlib.sha256(identifier.encode("utf-8")).hexdigest()


def _now(now: datetime | None) -> datetime:
    return now or datetime.now(timezone.utc)


def _parse_timestamp(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _lockout_active(identifier_hash: str, now: datetime) -> bool:
    with connection() as conn:
        row = conn.execute(
            "SELECT locked_until FROM admin_login_attempts WHERE identifier_hash = ?", (identifier_hash,)
        ).fetchone()
    locked_until = _parse_timestamp(row["locked_until"]) if row else None
    return bool(locked_until and locked_until > now)


def _record_failed_attempt(identifier_hash: str, now: datetime) -> bool:
    """Record one failed attempt and return whether it caused a lockout."""
    with connection() as conn:
        row = conn.execute(
            "SELECT failed_count, first_failed_at FROM admin_login_attempts WHERE identifier_hash = ?", (identifier_hash,)
        ).fetchone()
        first_failed_at = _parse_timestamp(row["first_failed_at"]) if row else None
        failed_count = int(row["failed_count"]) if row else 0
        if not first_failed_at or now - first_failed_at > FAILURE_WINDOW:
            first_failed_at, failed_count = now, 0
        failed_count += 1
        locked_until = (now + LOCKOUT_DURATION).isoformat() if failed_count >= MAX_FAILED_ATTEMPTS else None
        conn.execute(
            """
            INSERT INTO admin_login_attempts (identifier_hash, failed_count, first_failed_at, last_failed_at, locked_until)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(identifier_hash) DO UPDATE SET
                failed_count = excluded.failed_count, first_failed_at = excluded.first_failed_at,
                last_failed_at = excluded.last_failed_at, locked_until = excluded.locked_until
            """,
            (identifier_hash, failed_count, first_failed_at.isoformat(), now.isoformat(), locked_until),
        )
    logger.warning("admin_login_failed client=%s failures=%d", identifier_hash[:12], failed_count)
    return locked_until is not None


def _clear_failed_attempts(identifier_hash: str) -> None:
    with connection() as conn:
        conn.execute("DELETE FROM admin_login_attempts WHERE identifier_hash = ?", (identifier_hash,))


def authenticate_admin(
    username: str,
    password: str,
    client_identifier: str,
    environment: Mapping[str, str] | None = None,
    now: datetime | None = None,
) -> AuthenticationResult:
    """Authenticate without storing or logging credentials, enforcing active locks first."""
    env = os.environ if environment is None else environment
    if not validate_admin_configuration(env):
        logger.error("admin_authentication_configuration_invalid")
        return AuthenticationResult(False, "Administrator login is unavailable.")
    current_time = _now(now)
    identifier_hash = hash_client_identifier(client_identifier)
    if _lockout_active(identifier_hash, current_time):
        logger.warning("admin_login_locked client=%s", identifier_hash[:12])
        return AuthenticationResult(False, "Invalid credentials or login temporarily unavailable.", locked=True)
    expected_username = _value(env, "ADMIN_USERNAME")
    expected_hash = _value(env, "ADMIN_PASSWORD_HASH")
    username_matches = hmac.compare_digest(username, expected_username)
    if len(password) < MINIMUM_PASSWORD_LENGTH:
        password_matches = False
    else:
        try:
            password_matches = PASSWORD_HASHER.verify(expected_hash, password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            password_matches = False
    if username_matches and password_matches:
        _clear_failed_attempts(identifier_hash)
        return AuthenticationResult(True, "")
    locked = _record_failed_attempt(identifier_hash, current_time)
    return AuthenticationResult(False, "Invalid credentials or login temporarily unavailable.", locked=locked)
