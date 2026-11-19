"""JobTracker adapter: the spec's `jobs` table in SQLite (data/desiquip.db)."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

SCHEMA = """CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'new', retries INTEGER NOT NULL DEFAULT 0, youtube_id TEXT, error TEXT)"""


class SqliteJobs:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.execute(SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create(self, job_id: str) -> None:
        with self._conn() as c:
            c.execute("INSERT OR IGNORE INTO jobs (job_id) VALUES (?)", (job_id,))

    def set(self, job_id: str, status: str, error: str | None = None, youtube_id: str | None = None) -> None:
        with self._conn() as c:
            c.execute("UPDATE jobs SET status = ?, error = ?, youtube_id = COALESCE(?, youtube_id), "
                      "updated_at = CURRENT_TIMESTAMP WHERE job_id = ?", (status, error, youtube_id, job_id))

    def incr_retries(self, job_id: str) -> int:
        with self._conn() as c:
            c.execute("UPDATE jobs SET retries = retries + 1 WHERE job_id = ?", (job_id,))
            return c.execute("SELECT retries FROM jobs WHERE job_id = ?", (job_id,)).fetchone()[0]

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self._conn() as c:
            row = c.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        return dict(row) if row else None

    def list(self, status: str | None = None) -> list[dict[str, Any]]:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM jobs" + (" WHERE status = ?" if status else "") +
                             " ORDER BY created_at DESC", (status,) if status else ()).fetchall()
        return [dict(r) for r in rows]

    def counts(self) -> dict[str, int]:
        with self._conn() as c:
            return {r[0]: r[1] for r in c.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")}
