"""Schema migrations for Life Engine."""

from __future__ import annotations

import sqlite3

V2_STATEMENTS = [
    "ALTER TABLE goals ADD COLUMN tier TEXT NOT NULL DEFAULT 'current'",
    "ALTER TABLE goals ADD COLUMN parent_goal_id TEXT",
    "ALTER TABLE self_memories ADD COLUMN memory_type TEXT NOT NULL DEFAULT 'observation'",
    "ALTER TABLE self_memories ADD COLUMN structured_data TEXT NOT NULL DEFAULT '{}'",
    "ALTER TABLE reflections ADD COLUMN structured_data TEXT NOT NULL DEFAULT '{}'",
    """
    CREATE TABLE IF NOT EXISTS beliefs (
        belief_id TEXT PRIMARY KEY,
        being_id TEXT NOT NULL REFERENCES beings(being_id),
        statement TEXT NOT NULL,
        belief_type TEXT NOT NULL DEFAULT 'self',
        confidence REAL NOT NULL DEFAULT 0.5,
        status TEXT NOT NULL DEFAULT 'candidate',
        created_at TEXT NOT NULL,
        last_reviewed_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS belief_evidence (
        evidence_id TEXT PRIMARY KEY,
        belief_id TEXT NOT NULL REFERENCES beliefs(belief_id),
        event_id TEXT,
        reflection_id TEXT,
        support REAL NOT NULL DEFAULT 0.5,
        counter REAL NOT NULL DEFAULT 0,
        note TEXT,
        created_at TEXT NOT NULL
    )
    """,
]


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r[1] == column for r in rows)


def migrate(conn: sqlite3.Connection) -> int:
    current = conn.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
    version = current[0] if current else 1
    if version >= 2:
        return version

    for stmt in V2_STATEMENTS:
        if "ALTER TABLE goals ADD COLUMN tier" in stmt and _column_exists(conn, "goals", "tier"):
            continue
        if "ALTER TABLE goals ADD COLUMN parent" in stmt and _column_exists(conn, "goals", "parent_goal_id"):
            continue
        if "self_memories ADD COLUMN memory_type" in stmt and _column_exists(conn, "self_memories", "memory_type"):
            continue
        if "self_memories ADD COLUMN structured_data" in stmt and _column_exists(conn, "self_memories", "structured_data"):
            continue
        if "reflections ADD COLUMN structured_data" in stmt and _column_exists(conn, "reflections", "structured_data"):
            continue
        conn.execute(stmt)

    conn.execute("UPDATE schema_version SET version = 2")
    conn.commit()
    return 2
