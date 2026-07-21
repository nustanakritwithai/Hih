"""Evolution schema migrations."""

from __future__ import annotations

import sqlite3

V2_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS experiments (
        experiment_id       TEXT PRIMARY KEY,
        being_id            TEXT NOT NULL,
        proposal_id         TEXT,
        candidate_branch    TEXT,
        status              TEXT NOT NULL DEFAULT 'pending',
        budget_retries      INTEGER NOT NULL DEFAULT 0,
        budget_tool_calls   INTEGER NOT NULL DEFAULT 0,
        baseline_scores_json TEXT NOT NULL DEFAULT '{}',
        candidate_scores_json TEXT NOT NULL DEFAULT '{}',
        comparison_json     TEXT NOT NULL DEFAULT '{}',
        started_at          TEXT,
        finished_at         TEXT,
        notes               TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS candidate_branches (
        branch_id           TEXT PRIMARY KEY,
        branch_name         TEXT NOT NULL UNIQUE,
        proposal_id         TEXT,
        experiment_id       TEXT,
        status              TEXT NOT NULL DEFAULT 'active',
        created_at          TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS budget_usage (
        usage_id            TEXT PRIMARY KEY,
        being_id            TEXT NOT NULL,
        usage_day           TEXT NOT NULL,
        experiments_count   INTEGER NOT NULL DEFAULT 0,
        reflections_count   INTEGER NOT NULL DEFAULT 0,
        status              TEXT NOT NULL DEFAULT 'active',
        UNIQUE (being_id, usage_day)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS evolution_session_reflections (
        reflection_id       TEXT PRIMARY KEY,
        being_id            TEXT NOT NULL,
        session_id          TEXT,
        structured_data_json TEXT NOT NULL,
        belief_candidates_json TEXT NOT NULL,
        evidence_links_json TEXT NOT NULL,
        created_at          TEXT NOT NULL
    )
    """,
]


def migrate(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT version FROM evolution_schema_version LIMIT 1").fetchone()
    version = row[0] if row else 1
    if version < 2:
        for stmt in V2_STATEMENTS:
            conn.execute(stmt)
        conn.execute("UPDATE evolution_schema_version SET version = 2")
        conn.commit()
        version = 2
    if version >= 3:
        return version
    for stmt in V3_STATEMENTS:
        conn.execute(stmt)
    conn.execute("UPDATE evolution_schema_version SET version = 3")
    conn.commit()
    return 3


V3_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS verification_reports (
        report_id           TEXT PRIMARY KEY,
        experiment_id       TEXT NOT NULL,
        producer_context    TEXT NOT NULL,
        verifier_context    TEXT NOT NULL,
        producer_run_json   TEXT NOT NULL,
        verifier_run_json   TEXT NOT NULL,
        separation_verified INTEGER NOT NULL DEFAULT 0,
        created_at          TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS comparison_reports (
        report_id           TEXT PRIMARY KEY,
        experiment_id       TEXT NOT NULL,
        regressions_json    TEXT NOT NULL,
        improvements_json   TEXT NOT NULL,
        all_cases_json      TEXT NOT NULL,
        created_at          TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS acceptance_decisions (
        decision_id         TEXT PRIMARY KEY,
        experiment_id       TEXT NOT NULL,
        comparison_report_id TEXT,
        recommendation      TEXT NOT NULL,
        auto_rejected_reasons_json TEXT NOT NULL DEFAULT '[]',
        identity_regression INTEGER NOT NULL DEFAULT 0,
        permission_regression INTEGER NOT NULL DEFAULT 0,
        safety_regression   INTEGER NOT NULL DEFAULT 0,
        created_at          TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS evolution_memories (
        memory_id           TEXT PRIMARY KEY,
        being_id            TEXT NOT NULL,
        memory_type         TEXT NOT NULL,
        content_json        TEXT NOT NULL,
        source_experiment_id TEXT,
        source_proposal_id  TEXT,
        evidence_json       TEXT NOT NULL DEFAULT '[]',
        confidence          REAL NOT NULL DEFAULT 0.5,
        immutable           INTEGER NOT NULL DEFAULT 0,
        created_at          TEXT NOT NULL
    )
    """,
]
