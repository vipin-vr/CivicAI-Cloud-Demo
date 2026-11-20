"""SQLite persistence for CivicAI."""
from __future__ import annotations

import json
import hashlib
import hmac
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DB_PATH = Path(__file__).with_name("civicai.db")
KNOWN_PUBLIC_STATIC_ROOTS = (PROJECT_ROOT / "static", PROJECT_ROOT / "public", PROJECT_ROOT / ".streamlit")
CLOUD_DIRECTORY_NAMES = {"onedrive", "dropbox", "google drive", "icloud drive"}


class DatabasePathError(ValueError):
    """Raised when a configured production database path is unsafe."""


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def resolve_database_path(environment: Mapping[str, str] | None = None) -> Path:
    """Use an explicitly configured safe absolute path, or retain the local default."""
    env = os.environ if environment is None else environment
    configured = env.get("CIVICAI_DB_PATH", "").strip()
    if not configured:
        return DEFAULT_DB_PATH
    candidate = Path(configured).expanduser()
    if not candidate.is_absolute():
        raise DatabasePathError("CIVICAI_DB_PATH must be an absolute path.")
    resolved = candidate.resolve()
    configured_cloud_roots = [env[key] for key in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial", "Dropbox", "GoogleDrivePath", "iCloudDrive") if env.get(key)]
    if _inside(resolved, PROJECT_ROOT) or any(_inside(resolved, root) for root in KNOWN_PUBLIC_STATIC_ROOTS):
        raise DatabasePathError("CIVICAI_DB_PATH must be outside the application and public/static directories.")
    if any(part.casefold() in CLOUD_DIRECTORY_NAMES for part in resolved.parts) or any(_inside(resolved, Path(root).expanduser().resolve()) for root in configured_cloud_roots):
        raise DatabasePathError("CIVICAI_DB_PATH must not be inside a detected cloud-synced directory.")
    if resolved.exists() and resolved.is_dir():
        raise DatabasePathError("CIVICAI_DB_PATH must name a SQLite database file.")
    return resolved


DB_PATH = resolve_database_path()

REVIEW_COLUMNS = {
    "ai_category": "TEXT",
    "ai_generated_description": "TEXT",
    "ai_suggested_department": "TEXT",
    "mismatch_flag": "INTEGER NOT NULL DEFAULT 0",
    "duplicate_complaint_id": "TEXT",
    "admin_confirmed_category": "TEXT",
    "admin_confirmed_department": "TEXT",
    "reviewed_flag": "INTEGER NOT NULL DEFAULT 0",
    "reviewed_at": "TEXT",
    "tracking_token_hash": "TEXT",
}


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise DatabasePathError(f"Unable to create the database directory: {DB_PATH.parent}") from error
    try:
        conn = sqlite3.connect(DB_PATH)
    except sqlite3.Error as error:
        raise DatabasePathError(f"Unable to open the configured SQLite database path: {DB_PATH}") from error
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def initialize_database() -> None:
    with connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                complaint_id TEXT NOT NULL UNIQUE,
                citizen_name TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                location TEXT NOT NULL,
                image_path TEXT,
                ai_analysis TEXT,
                severity TEXT NOT NULL,
                public_risk INTEGER NOT NULL,
                public_impact INTEGER NOT NULL,
                priority_score REAL NOT NULL,
                priority_label TEXT NOT NULL,
                suggested_department TEXT,
                ai_category TEXT,
                ai_generated_description TEXT,
                ai_suggested_department TEXT,
                mismatch_flag INTEGER NOT NULL DEFAULT 0,
                duplicate_flag INTEGER NOT NULL DEFAULT 0,
                duplicate_complaint_id TEXT,
                tracking_token_hash TEXT,
                admin_confirmed_category TEXT,
                admin_confirmed_department TEXT,
                reviewed_flag INTEGER NOT NULL DEFAULT 0,
                reviewed_at TEXT,
                status TEXT NOT NULL DEFAULT 'Submitted',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        existing_columns = {row["name"] for row in conn.execute("PRAGMA table_info(complaints)")}
        for column, definition in REVIEW_COLUMNS.items():
            if column not in existing_columns:
                conn.execute(f"ALTER TABLE complaints ADD COLUMN {column} {definition}")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_login_attempts (
                identifier_hash TEXT PRIMARY KEY,
                failed_count INTEGER NOT NULL,
                first_failed_at TEXT NOT NULL,
                last_failed_at TEXT NOT NULL,
                locked_until TEXT
            )
            """
        )


def create_complaint(record: dict[str, Any]) -> None:
    columns = ", ".join(record)
    placeholders = ", ".join(f":{key}" for key in record)
    with connection() as conn:
        conn.execute(f"INSERT INTO complaints ({columns}) VALUES ({placeholders})", record)


def generate_tracking_token() -> str:
    """Create a high-entropy token shown to a citizen only after a successful insert."""
    return secrets.token_urlsafe(32)


def hash_tracking_token(token: str) -> str:
    """Return the database-safe SHA-256 representation of a tracking token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def get_complaint(complaint_id: str) -> dict[str, Any] | None:
    with connection() as conn:
        row = conn.execute("SELECT * FROM complaints WHERE complaint_id = ?", (complaint_id.strip(),)).fetchone()
    return dict(row) if row else None


def get_complaint_for_tracking(complaint_id: str, tracking_token: str) -> dict[str, Any] | None:
    """Return a complaint only when its stored token hash matches the supplied token.

    Legacy complaints intentionally have no token hash and are not available through
    public tracking. Callers must return the same response for every failed lookup.
    """
    normalized_id = complaint_id.strip()
    if not normalized_id or not tracking_token:
        return None
    with connection() as conn:
        row = conn.execute(
            "SELECT tracking_token_hash FROM complaints WHERE complaint_id = ?",
            (normalized_id,),
        ).fetchone()
        if not row or not row["tracking_token_hash"]:
            return None
        supplied_hash = hash_tracking_token(tracking_token)
        if not hmac.compare_digest(row["tracking_token_hash"], supplied_hash):
            return None
        complaint = conn.execute("SELECT * FROM complaints WHERE complaint_id = ?", (normalized_id,)).fetchone()
    return dict(complaint) if complaint else None


def get_complaints(
    complaint_id: str = "", category: str = "All", priority: str = "All", status: str = "All"
) -> list[dict[str, Any]]:
    sql = "SELECT * FROM complaints WHERE 1=1"
    params: list[str] = []
    if complaint_id.strip():
        sql += " AND complaint_id LIKE ?"
        params.append(f"%{complaint_id.strip()}%")
    if category != "All":
        sql += " AND category = ?"
        params.append(category)
    if priority != "All":
        sql += " AND priority_label = ?"
        params.append(priority)
    if status != "All":
        sql += " AND status = ?"
        params.append(status)
    sql += " ORDER BY created_at DESC"
    with connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def update_complaint_status(complaint_id: str, status: str) -> bool:
    if status not in {"Submitted", "In Progress", "Resolved"}:
        return False
    now = datetime.now(timezone.utc).isoformat()
    with connection() as conn:
        conn.execute("UPDATE complaints SET status = ?, updated_at = ? WHERE complaint_id = ?", (status, now, complaint_id))
    return True


def update_complaint_review(complaint_id: str, category: str, department: str) -> bool:
    if not complaint_id.strip() or not category.strip() or not department.strip():
        return False
    now = datetime.now(timezone.utc).isoformat()
    with connection() as conn:
        cursor = conn.execute(
            """
            UPDATE complaints
            SET admin_confirmed_category = ?, admin_confirmed_department = ?,
                reviewed_flag = 1, reviewed_at = ?, updated_at = ?
            WHERE complaint_id = ?
            """,
            (category, department, now, now, complaint_id),
        )
    return cursor.rowcount == 1


def update_complaint_review_and_status(complaint_id: str, category: str, department: str, status: str) -> bool:
    """Save an administrator's review and status selection atomically."""
    if not complaint_id.strip() or not category.strip() or not department.strip():
        return False
    if status not in {"Submitted", "In Progress", "Resolved"}:
        return False
    now = datetime.now(timezone.utc).isoformat()
    with connection() as conn:
        cursor = conn.execute(
            """
            UPDATE complaints
            SET admin_confirmed_category = ?, admin_confirmed_department = ?,
                reviewed_flag = 1, reviewed_at = ?, status = ?, updated_at = ?
            WHERE complaint_id = ?
            """,
            (category, department, now, status, now, complaint_id),
        )
    return cursor.rowcount == 1


def dashboard_counts() -> dict[str, int]:
    with connection() as conn:
        rows = conn.execute("SELECT status, COUNT(*) AS total FROM complaints GROUP BY status").fetchall()
        total = conn.execute("SELECT COUNT(*) AS total FROM complaints").fetchone()["total"]
    counts = {row["status"]: row["total"] for row in rows}
    return {"Total": total, "Submitted": counts.get("Submitted", 0), "In Progress": counts.get("In Progress", 0), "Resolved": counts.get("Resolved", 0)}


def category_counts() -> list[dict[str, Any]]:
    with connection() as conn:
        rows = conn.execute("SELECT category, COUNT(*) AS count FROM complaints GROUP BY category ORDER BY count DESC").fetchall()
    return [dict(row) for row in rows]


def decode_analysis(raw: str | None) -> dict[str, Any]:
    try:
        return json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {"explanation": raw or "No AI analysis was recorded."}
