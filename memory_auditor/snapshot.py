"""Read-only database snapshot via SQLite Backup API — never writes to source."""

from __future__ import annotations

import hashlib
import os
import sqlite3
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SnapshotInfo:
    source_path: str
    snapshot_path: str
    created_at: float
    read_only_uri: str
    source_hash_before: str
    source_mtime_before: float
    method: str = "sqlite_backup_api"
    source_hash_after: str = ""
    source_mtime_after: float = 0.0
    cleanup_result: str = "pending"

    def integrity_verified(self) -> bool:
        return (
            self.source_hash_before == self.source_hash_after
            and self.source_mtime_before == self.source_mtime_after
        )


def file_fingerprint(path: Path) -> tuple[str, float]:
    """SHA256 hash and mtime — used to verify source unchanged."""
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest(), path.stat().st_mtime


def create_readonly_snapshot(source_db: str | Path) -> SnapshotInfo:
    """
    Create consistent snapshot using SQLite Backup API from read-only source.
    Does not write to source; handles WAL-mode databases correctly.
    """
    source = Path(source_db).resolve()
    if not source.exists():
        raise FileNotFoundError(f"source database not found: {source}")

    hash_before, mtime_before = file_fingerprint(source)
    tmp = Path(tempfile.gettempdir()) / f"dioo-auditor-snapshot-{int(time.time() * 1000)}.db"

    source_uri = f"file:{source}?mode=ro"
    source_conn = sqlite3.connect(source_uri, uri=True)
    snapshot_conn = sqlite3.connect(str(tmp))
    try:
        source_conn.backup(snapshot_conn)
    finally:
        snapshot_conn.close()
        source_conn.close()

    os.chmod(tmp, 0o600)

    hash_after, mtime_after = file_fingerprint(source)

    return SnapshotInfo(
        source_path=str(source),
        snapshot_path=str(tmp),
        created_at=time.time(),
        read_only_uri=f"file:{tmp}?mode=ro",
        source_hash_before=hash_before,
        source_mtime_before=mtime_before,
        source_hash_after=hash_after,
        source_mtime_after=mtime_after,
        method="sqlite_backup_api",
    )


def cleanup_snapshot(snapshot: SnapshotInfo) -> str:
    """Delete temporary snapshot file. Owner-only permissions enforced before delete."""
    path = Path(snapshot.snapshot_path)
    if not path.exists():
        return "already_absent"
    try:
        os.chmod(path, 0o600)
        path.unlink()
        return "deleted"
    except OSError as exc:
        return f"failed:{exc}"


def verify_source_unchanged(snapshot: SnapshotInfo) -> SnapshotInfo:
    """Re-check source hash/mtime after audit completes."""
    source = Path(snapshot.source_path)
    hash_after, mtime_after = file_fingerprint(source)
    snapshot.source_hash_after = hash_after
    snapshot.source_mtime_after = mtime_after
    return snapshot


def connect_readonly(snapshot: SnapshotInfo) -> sqlite3.Connection:
    """Open read-only connection to snapshot."""
    conn = sqlite3.connect(snapshot.read_only_uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def connect_source_readonly(source_db: str | Path) -> sqlite3.Connection:
    """Open source DB read-only via URI (no snapshot). For tests when file is ephemeral."""
    source = Path(source_db).resolve()
    uri = f"file:{source}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn
