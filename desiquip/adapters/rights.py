"""RightsRegistry adapter: the spec's `rights` table in SQLite (data/desiquip.db).

Spec: every video's source must have a rights record (original / licensed / cc / stock / commentary).
"""
from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

SCHEMA = """CREATE TABLE IF NOT EXISTS rights (
    source_id TEXT PRIMARY KEY, source_type TEXT NOT NULL, owner TEXT NOT NULL,
    licence_url TEXT, proof_path TEXT, expires_at TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)"""


class SqliteRights:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.execute(SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def add(self, source_id: str, source_type: str, owner: str, licence_url: str | None = None,
            proof_path: str | None = None, expires_at: str | None = None) -> None:
        with self._conn() as c:
            c.execute("INSERT OR REPLACE INTO rights (source_id, source_type, owner, licence_url, proof_path, "
                      "expires_at) VALUES (?, ?, ?, ?, ?, ?)",
                      (source_id, source_type, owner, licence_url, proof_path, expires_at))

    def is_valid(self, source_id: str) -> bool:
        with self._conn() as c:
            row = c.execute("SELECT expires_at FROM rights WHERE source_id = ?", (source_id,)).fetchone()
        if row is None:
            return False
        return row[0] is None or row[0] >= date.today().isoformat()
