"""Snapshots, backup, recovery for evolution data."""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
from pathlib import Path
from typing import Any

from evolution.util import new_id, now_iso


class PersistenceManager:
    def __init__(self, db_path: Path, snapshot_dir: Path | None = None) -> None:
        self.db_path = Path(db_path)
        self.snapshot_dir = snapshot_dir or Path("state/snapshots")
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    def create_snapshot(self, conn: sqlite3.Connection, snapshot_type: str, notes: str = "") -> str:
        sid = new_id("snap")
        ts = now_iso().replace(":", "-")
        dest = self.snapshot_dir / f"{snapshot_type}_{ts}_{sid}.db"
        shutil.copy2(self.db_path, dest)
        schema_v = conn.execute(
            "SELECT version FROM evolution_schema_version LIMIT 1"
        ).fetchone()
        version = schema_v[0] if schema_v else 0
        conn.execute(
            """
            INSERT INTO evolution_snapshots (snapshot_id, snapshot_type, file_path, schema_version, created_at, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (sid, snapshot_type, str(dest), version, now_iso(), notes),
        )
        return sid

    def restore_snapshot(self, snapshot_id: str, conn: sqlite3.Connection) -> str:
        row = conn.execute(
            "SELECT file_path FROM evolution_snapshots WHERE snapshot_id = ?", (snapshot_id,)
        ).fetchone()
        if not row:
            raise KeyError(snapshot_id)
        src = Path(row[0])
        if not src.exists():
            raise FileNotFoundError(src)
        backup = self.db_path.with_suffix(".db.pre_restore")
        shutil.copy2(self.db_path, backup)
        shutil.copy2(src, self.db_path)
        return str(backup)

    def detect_corruption(self, conn: sqlite3.Connection) -> list[str]:
        issues = []
        try:
            conn.execute("SELECT COUNT(*) FROM trajectories").fetchone()
            conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()
        except sqlite3.DatabaseError as e:
            issues.append(f"database_error:{e}")
        if not self.db_path.exists():
            issues.append("missing_database")
        return issues

    def integrity_hash(self, conn: sqlite3.Connection, table: str) -> str:
        rows = conn.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()
        raw = json.dumps([dict(r) for r in rows], sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def backup_before_migration(self, conn: sqlite3.Connection, from_version: int, to_version: int) -> str:
        """Create DB backup and record migration history before schema change."""
        sid = self.create_snapshot(conn, "pre_migration", f"v{from_version}_to_v{to_version}")
        backup_path = conn.execute(
            "SELECT file_path FROM evolution_snapshots WHERE snapshot_id = ?", (sid,)
        ).fetchone()[0]
        mid = new_id("mig")
        conn.execute(
            """
            INSERT INTO evolution_migration_history (
                migration_id, from_version, to_version, backup_path, applied_at, rollback_sql, status
            ) VALUES (?, ?, ?, ?, ?, ?, 'applied')
            """,
            (mid, from_version, to_version, backup_path, now_iso(), f"RESTORE SNAPSHOT {sid}"),
        )
        return mid

    def list_snapshots(self, conn: sqlite3.Connection, snapshot_type: str | None = None) -> list[dict[str, Any]]:
        if snapshot_type:
            rows = conn.execute(
                "SELECT * FROM evolution_snapshots WHERE snapshot_type = ? ORDER BY created_at DESC",
                (snapshot_type,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM evolution_snapshots ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def rollback_test(self, conn: sqlite3.Connection) -> dict[str, Any]:
        """Verify restore preserves trajectories, failures, proposals, and audit log."""
        tables = ["trajectories", "evaluations", "failures", "proposals", "audit_log", "eval_cases"]
        before = {t: self.integrity_hash(conn, t) for t in tables}
        snapshot_id = self.create_snapshot(conn, "stable", "rollback_test")
        conn.commit()
        self.restore_snapshot(snapshot_id, conn)
        fresh = sqlite3.connect(self.db_path)
        fresh.row_factory = sqlite3.Row
        try:
            after = {t: self.integrity_hash(fresh, t) for t in tables}
        finally:
            fresh.close()
        mismatches = [t for t in tables if before.get(t) != after.get(t)]
        return {
            "snapshot_id": snapshot_id,
            "passed": len(mismatches) == 0,
            "tables_checked": tables,
            "mismatches": mismatches,
        }
