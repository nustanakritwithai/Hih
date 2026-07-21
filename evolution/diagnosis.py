"""Failure analyzer and aggregation."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from typing import Any

from evolution.util import new_id, now_iso

CATEGORIES = frozenset({
    "REASONING_FAILURE", "PLANNING_FAILURE", "IMPLEMENTATION_FAILURE",
    "TOOL_SELECTION_FAILURE", "TOOL_EXECUTION_FAILURE", "MEMORY_RETRIEVAL_FAILURE",
    "MEMORY_WRITE_FAILURE", "BELIEF_FORMATION_FAILURE", "REFLECTION_FAILURE",
    "IDENTITY_INCONSISTENCY", "PERMISSION_VIOLATION", "EVALUATION_FAILURE",
    "REGRESSION", "EFFICIENCY_FAILURE", "COMMUNICATION_FAILURE", "UNKNOWN_FAILURE",
})


def fingerprint(category: str, symptom: str, module: str = "") -> str:
    raw = f"{category}|{symptom}|{module}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class FailureAnalyzer:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def record(
        self,
        being_id: str,
        category: str,
        symptom: str,
        observed: str,
        expected: str,
        trajectory_id: str | None = None,
        evaluation_id: str | None = None,
        severity: str = "medium",
        modules: list[str] | None = None,
        hypotheses: list[dict] | None = None,
    ) -> dict[str, Any]:
        if category not in CATEGORIES:
            category = "UNKNOWN_FAILURE"
        ts = now_iso()
        fp = fingerprint(category, symptom, (modules or [""])[0])
        existing = self.conn.execute(
            "SELECT * FROM failures WHERE being_id = ? AND fingerprint = ? AND status != 'resolved'",
            (being_id, fp),
        ).fetchone()

        if existing:
            repeat = existing["repeat_count"] + 1
            trajs = json.loads(existing["related_trajectories_json"])
            evals = json.loads(existing["related_evaluations_json"])
            if trajectory_id and trajectory_id not in trajs:
                trajs.append(trajectory_id)
            if evaluation_id and evaluation_id not in evals:
                evals.append(evaluation_id)
            self.conn.execute(
                """
                UPDATE failures SET repeat_count = ?, last_seen_at = ?,
                    related_trajectories_json = ?, related_evaluations_json = ?
                WHERE failure_id = ?
                """,
                (repeat, ts, json.dumps(trajs), json.dumps(evals), existing["failure_id"]),
            )
            return {"failure_id": existing["failure_id"], "repeat_count": repeat, "aggregated": True}

        fid = new_id("fail")
        hyps = hypotheses or [{"hypothesis": symptom, "confidence": 0.5, "supporting_evidence": [], "counter_evidence": [], "test_to_confirm": ""}]
        self.conn.execute(
            """
            INSERT INTO failures (
                failure_id, being_id, category, symptom, observed_behavior,
                expected_behavior, root_cause_hypotheses_json, primary_hypothesis,
                confidence, severity, repeat_count, first_seen_at, last_seen_at,
                related_trajectories_json, related_evaluations_json,
                affected_modules_json, status, fingerprint
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, 'open', ?)
            """,
            (
                fid, being_id, category, symptom, observed, expected,
                json.dumps(hyps, ensure_ascii=False), hyps[0].get("hypothesis", ""),
                hyps[0].get("confidence", 0.5), severity, ts, ts,
                json.dumps([trajectory_id] if trajectory_id else []),
                json.dumps([evaluation_id] if evaluation_id else []),
                json.dumps(modules or []), fp,
            ),
        )
        return {"failure_id": fid, "repeat_count": 1, "aggregated": False}

    def diagnose(self, failure: dict[str, Any]) -> dict[str, Any]:
        hyps = json.loads(failure.get("root_cause_hypotheses_json") or "[]")
        primary = failure.get("primary_hypothesis", "")
        conf = float(failure.get("confidence", 0))
        status = "INSUFFICIENT_EVIDENCE" if conf < 0.55 else "DIAGNOSED"
        return {
            "failure_id": failure["failure_id"],
            "symptom": failure["symptom"],
            "primary_hypothesis": primary,
            "hypotheses": hyps,
            "confidence": conf,
            "status": status,
            "repeat_count": failure.get("repeat_count", 1),
        }

    def list_open(self, being_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM failures WHERE being_id = ? AND status = 'open' ORDER BY repeat_count DESC",
            (being_id,),
        ).fetchall()
        return [dict(r) for r in rows]
