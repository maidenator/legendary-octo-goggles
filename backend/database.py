"""
Ayahay SmartScan - Database Layer (Module 4)
Handles all SQLite operations: initialization, saving scan results, and querying history.
Uses Python's built-in sqlite3 — no extra dependencies required.
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict

# Database file stored in the backend/ directory
DB_PATH = Path(__file__).parent / "smartscan.db"


def get_connection() -> sqlite3.Connection:
    """Open a connection with row_factory so rows come back as dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Create the scans table if it doesn't already exist.
    Safe to call multiple times (idempotent).
    """
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                filename           TEXT    NOT NULL,
                size_bytes         INTEGER,
                timestamp          TEXT,
                container_id       TEXT,
                validation_status  TEXT,
                raw_text_preview   TEXT,
                error              TEXT,
                created_at         DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    print("[DB] Database initialized at", DB_PATH)


def save_scan(
    filename: str,
    size_bytes: int,
    timestamp: str,
    container_id: Optional[str],
    validation_status: Optional[str],
    raw_text_preview: Optional[str],
    error: Optional[str],
) -> int:
    """
    Insert a scan record into the database.

    Returns:
        The auto-assigned row ID of the new record.
    """
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO scans
                (filename, size_bytes, timestamp, container_id, validation_status, raw_text_preview, error)
            VALUES
                (?, ?, ?, ?, ?, ?, ?)
            """,
            (filename, size_bytes, timestamp, container_id, validation_status, raw_text_preview, error),
        )
        conn.commit()
        row_id = cursor.lastrowid
    print(f"[DB] Saved scan record id={row_id} container_id={container_id}")
    return row_id


def get_scans(limit: int = 50) -> List[Dict]:
    """
    Retrieve the most recent scan records.

    Args:
        limit: Maximum number of records to return (default 50).

    Returns:
        List of dicts with all column values, newest first.
    """
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM scans ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_scan_by_id(scan_id: int) -> Optional[Dict]:
    """
    Retrieve a single scan record by its primary key.

    Returns:
        Dict with column values, or None if not found.
    """
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM scans WHERE id = ?", (scan_id,)
        ).fetchone()
    return dict(row) if row else None
