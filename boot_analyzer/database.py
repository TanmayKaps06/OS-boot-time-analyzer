"""SQLite persistence for boot snapshots."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from .models import BootSnapshot


def initialize(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS boot_sessions (
                boot_time TEXT PRIMARY KEY,
                observed_at TEXT NOT NULL,
                uptime_seconds REAL,
                login_window_seconds REAL,
                login_window_note TEXT NOT NULL,
                collection_note TEXT NOT NULL DEFAULT ''
            )
            """
        )


def save_snapshot(database_path: Path, snapshot: BootSnapshot) -> bool:
    """Insert a boot once. Returns True only for a newly saved session."""
    if snapshot.boot_time is None:
        return False
    initialize(database_path)
    with sqlite3.connect(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO boot_sessions
            (boot_time, observed_at, uptime_seconds, login_window_seconds,
             login_window_note, collection_note)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot.boot_time.isoformat(), snapshot.observed_at.isoformat(),
                snapshot.uptime_seconds, snapshot.login_window_seconds,
                snapshot.login_window_note, snapshot.collection_note,
            ),
        )
    return cursor.rowcount == 1


def load_history(database_path: Path) -> pd.DataFrame:
    initialize(database_path)
    with sqlite3.connect(database_path) as connection:
        data = pd.read_sql_query(
            "SELECT * FROM boot_sessions ORDER BY boot_time ASC", connection,
            parse_dates=["boot_time", "observed_at"],
        )
    return data
