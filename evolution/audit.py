"""Append-only audit log."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from typing import Any

from evolution.util import new_id, now_iso


def _hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def log(
    conn: sqlite3.Connection,
    actor: str,
    action: str,
    target: str,
    before: Any = None,
    after: Any = None,
    reason: str = "",
    permission_source: str = "",
) -> str:
    audit_id = new_id("audit")
    conn.execute(
        """
        INSERT INTO audit_log (
            audit_id, actor, action, target, before_hash, after_hash,
            reason, permission_source, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            audit_id, actor, action, target,
            _hash(before) if before is not None else None,
            _hash(after) if after is not None else None,
            reason, permission_source, now_iso(),
        ),
    )
    return audit_id
