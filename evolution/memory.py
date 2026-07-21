"""Evolution memory — separate from Life Engine episodic/self-memory."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from evolution.util import new_id, now_iso


class EvolutionMemoryStore:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def record(
        self,
        being_id: str,
        memory_type: str,
        content: dict[str, Any],
        source_experiment_id: str | None = None,
        source_proposal_id: str | None = None,
        evidence: list[dict] | None = None,
        confidence: float = 0.7,
        immutable: bool = False,
    ) -> dict[str, Any]:
        mid = new_id("emem")
        ts = now_iso()
        self.conn.execute(
            """
            INSERT INTO evolution_memories (
                memory_id, being_id, memory_type, content_json,
                source_experiment_id, source_proposal_id, evidence_json,
                confidence, immutable, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                mid, being_id, memory_type,
                json.dumps(content, ensure_ascii=False),
                source_experiment_id, source_proposal_id,
                json.dumps(evidence or [], ensure_ascii=False),
                confidence, 1 if immutable else 0, ts,
            ),
        )
        return {"memory_id": mid, "memory_type": memory_type, "created_at": ts}

    def record_gate_decision(
        self,
        being_id: str,
        decision: dict[str, Any],
        comparison: dict[str, Any],
    ) -> dict[str, Any]:
        return self.record(
            being_id,
            "gate_decision",
            {
                "recommendation": decision.get("recommendation"),
                "auto_rejected_reasons": decision.get("auto_rejected_reasons", []),
                "regression_count": comparison.get("regression_count", 0),
            },
            source_experiment_id=decision.get("experiment_id"),
            evidence=[{"source": "acceptance_gate", "comparison_report_id": comparison.get("report_id")}],
            confidence=0.9,
            immutable=True,
        )

    def list_memories(self, being_id: str, memory_type: str | None = None) -> list[dict]:
        if memory_type:
            rows = self.conn.execute(
                "SELECT * FROM evolution_memories WHERE being_id = ? AND memory_type = ? ORDER BY created_at DESC",
                (being_id, memory_type),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM evolution_memories WHERE being_id = ? ORDER BY created_at DESC",
                (being_id,),
            ).fetchall()
        return [dict(r) for r in rows]
