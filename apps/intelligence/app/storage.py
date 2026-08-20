from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  file_name TEXT NOT NULL,
  storage_path TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'queued',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_documents_user ON documents(user_id, created_at);
CREATE TABLE IF NOT EXISTS processing_jobs (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  document_id TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued',
  current_stage TEXT,
  progress INTEGER NOT NULL DEFAULT 0,
  discovered_json TEXT NOT NULL DEFAULT '{}',
  error_message TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(document_id) REFERENCES documents(id)
);
CREATE INDEX IF NOT EXISTS idx_jobs_user ON processing_jobs(user_id, created_at);
"""

class SQLiteStore:
    """Small persistence boundary; every lookup requires the authenticated user id."""
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript(SCHEMA)

    def connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        return db

    def create_document(self, *, document_id: str, user_id: str, file_name: str, storage_path: str) -> dict[str, Any]:
        with self.connect() as db:
            db.execute("INSERT INTO documents(id,user_id,file_name,storage_path) VALUES(?,?,?,?)", (document_id,user_id,file_name,storage_path))
            row = db.execute("SELECT * FROM documents WHERE id=? AND user_id=?", (document_id,user_id)).fetchone()
        return dict(row)

    def get_document(self, document_id: str, user_id: str) -> dict[str, Any] | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM documents WHERE id=? AND user_id=?", (document_id,user_id)).fetchone()
        return dict(row) if row else None

    def list_documents(self, user_id: str) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute("SELECT * FROM documents WHERE user_id=? ORDER BY created_at DESC", (user_id,)).fetchall()
        return [dict(row) for row in rows]

    def create_job(self, *, job_id: str, user_id: str, document_id: str) -> dict[str, Any]:
        with self.connect() as db:
            db.execute("INSERT INTO processing_jobs(id,user_id,document_id) VALUES(?,?,?)", (job_id,user_id,document_id))
            row = db.execute("SELECT * FROM processing_jobs WHERE id=? AND user_id=?", (job_id,user_id)).fetchone()
        return dict(row)

    def get_job(self, job_id: str, user_id: str) -> dict[str, Any] | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM processing_jobs WHERE id=? AND user_id=?", (job_id,user_id)).fetchone()
        return dict(row) if row else None

    def update_job(self, job_id: str, user_id: str, values: dict[str, Any]) -> None:
        allowed = {"status", "current_stage", "progress", "discovered_json", "error_message"}
        updates = [(key, value) for key, value in values.items() if key in allowed]
        if not updates: return
        assignments = ", ".join(f"{key}=?" for key, _ in updates)
        params = [value for _, value in updates] + [job_id, user_id]
        with self.connect() as db:
            db.execute(f"UPDATE processing_jobs SET {assignments} WHERE id=? AND user_id=?", params)

