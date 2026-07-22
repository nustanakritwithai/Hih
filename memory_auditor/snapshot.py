"""Read-only database snapshot — never writes to source store."""

from __future__ import annotations

import shutil
import sqlite3
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SnapshotInfo:
    source_path: str
    snapshot_path: str
    created_at: float
    read_only_uri: str


def create_readonly_snapshot(source_db: str | Path) -> SnapshotInfo:
    """Copy DB to temp path and return read-only connection URI. No source mutation."""
    source = Path(source_db)
    if not source.exists():
        raise FileNotFoundError(f"source database not found: {source}")

    tmp = Path(tempfile.gettempdir()) / f"dioo-auditor-snapshot-{int(time.time() * 1000)}.db"
    shutil.copy2(source, tmp)
    uri = f"file:{tmp}?mode=ro"
    return SnapshotInfo(
        source_path=str(source.resolve()),
        snapshot_path=str(tmp),
        created_at=time.time(),
        read_only_uri=uri,
    )


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
