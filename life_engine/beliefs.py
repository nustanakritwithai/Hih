"""Belief system — candidates, evidence, promotion, conflict."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

PROMOTE_THRESHOLD = 0.75
DISPUTE_THRESHOLD = 0.35
CANDIDATE_MIN_EVIDENCE = 1
ACTIVE_MIN_EVIDENCE = 2


def belief_from_candidate(
    statement: str,
    belief_type: str = "self",
    initial_confidence: float = 0.55,
) -> dict[str, Any]:
    return {
        "statement": statement,
        "type": belief_type,
        "confidence": initial_confidence,
        "status": "candidate",
    }


def compute_status(confidence: float, evidence_count: int, has_counter: bool) -> str:
    if has_counter and confidence < DISPUTE_THRESHOLD:
        return "disputed"
    if evidence_count >= ACTIVE_MIN_EVIDENCE and confidence >= PROMOTE_THRESHOLD:
        return "active"
    if evidence_count >= CANDIDATE_MIN_EVIDENCE:
        return "candidate"
    return "candidate"


def adjust_confidence(current: float, support: float, counter: float = 0.0) -> float:
    delta = support * 0.08 - counter * 0.12
    return max(0.0, min(1.0, current + delta))


def add_belief(
    conn: sqlite3.Connection,
    being_id: str,
    belief_id: str,
    statement: str,
    belief_type: str,
    confidence: float,
    status: str,
    ts: str,
) -> None:
    conn.execute(
        """
        INSERT INTO beliefs (
            belief_id, being_id, statement, belief_type, confidence,
            status, created_at, last_reviewed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (belief_id, being_id, statement, belief_type, confidence, status, ts, ts),
    )


def add_evidence(
    conn: sqlite3.Connection,
    belief_id: str,
    event_id: str | None,
    reflection_id: str | None,
    support: float,
    note: str,
    ts: str,
) -> str:
    from life_engine.util import new_id, now_iso

    eid = new_id("bev")
    conn.execute(
        """
        INSERT INTO belief_evidence (
            evidence_id, belief_id, event_id, reflection_id,
            support, counter, note, created_at
        ) VALUES (?, ?, ?, ?, ?, 0, ?, ?)
        """,
        (eid, belief_id, event_id, reflection_id, support, note, ts),
    )
    return eid


def promote_or_update_belief(conn: sqlite3.Connection, belief_id: str, ts: str) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM beliefs WHERE belief_id = ?", (belief_id,)).fetchone()
    if not row:
        raise KeyError(belief_id)
    evidence = conn.execute(
        "SELECT support, counter FROM belief_evidence WHERE belief_id = ?", (belief_id,)
    ).fetchall()
    support_sum = sum(r["support"] for r in evidence if r["counter"] == 0)
    counter_sum = sum(r["counter"] for r in evidence)
    count = len(evidence)
    confidence = adjust_confidence(float(row["confidence"]), support_sum / max(count, 1), counter_sum / max(count, 1))
    status = compute_status(confidence, count, counter_sum > 0)
    conn.execute(
        """
        UPDATE beliefs SET confidence = ?, status = ?, last_reviewed_at = ?
        WHERE belief_id = ?
        """,
        (confidence, status, ts, belief_id),
    )
    return {"belief_id": belief_id, "confidence": confidence, "status": status}


def find_belief_by_statement(conn: sqlite3.Connection, being_id: str, statement: str) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT * FROM beliefs
        WHERE being_id = ? AND statement = ? AND status != 'retired'
        """,
        (being_id, statement),
    ).fetchone()


def list_beliefs(conn: sqlite3.Connection, being_id: str, status: str | None = None) -> list[dict]:
    if status:
        rows = conn.execute(
            "SELECT * FROM beliefs WHERE being_id = ? AND status = ? ORDER BY confidence DESC",
            (being_id, status),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM beliefs WHERE being_id = ? AND status != 'retired' ORDER BY confidence DESC",
            (being_id,),
        ).fetchall()
    return [dict(r) for r in rows]
