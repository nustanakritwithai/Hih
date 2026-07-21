"""Independent verifier — separate context from producer."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from evolution.evaluation import EvaluationEngine
from evolution.sandbox import evaluate_candidate_case
from evolution.util import new_id, now_iso

PRODUCER_ROLE = "producer"
VERIFIER_ROLE = "verifier"


class ExperimentVerifier:
    """Re-evaluates experiment results in an isolated verifier context."""

    def __init__(self, conn: sqlite3.Connection, config: dict) -> None:
        self.conn = conn
        self.config = config
        gate = float(config.get("thresholds", {}).get("evaluator_pass_gate", 0.70))
        self._evaluator = EvaluationEngine(conn, pass_gate=gate)

    def verify(
        self,
        experiment_id: str,
        producer_context_id: str,
        producer_results: dict[str, Any],
    ) -> dict[str, Any]:
        verifier_context_id = new_id("vctx")
        if verifier_context_id == producer_context_id:
            return {
                "allowed": False,
                "status": "error",
                "reason": "verifier_context_must_differ_from_producer",
            }

        row = self.conn.execute(
            "SELECT * FROM experiments WHERE experiment_id = ?", (experiment_id,)
        ).fetchone()
        if not row:
            return {"status": "error", "reason": "experiment_not_found"}

        cases = self.conn.execute("SELECT * FROM eval_cases ORDER BY case_id").fetchall()
        verifier_runs = []
        producer_runs = producer_results.get("candidate_results", [])
        for case_row in cases:
            outcome = evaluate_candidate_case(case_row, self._evaluator)
            verifier_runs.append({
                "case_id": outcome.get("case_id"),
                "category": outcome.get("category"),
                "passed": outcome["passed"],
                "role": VERIFIER_ROLE,
            })

        mismatches = []
        for p, v in zip(producer_runs, verifier_runs):
            if p.get("passed") != v["passed"]:
                mismatches.append({
                    "case_id": p.get("case_id"),
                    "producer_passed": p.get("passed"),
                    "verifier_passed": v["passed"],
                })

        report_id = new_id("vrep")
        separation_ok = verifier_context_id != producer_context_id and len(mismatches) == 0
        report = {
            "report_id": report_id,
            "experiment_id": experiment_id,
            "producer_context_id": producer_context_id,
            "verifier_context_id": verifier_context_id,
            "separation_verified": separation_ok,
            "producer_run_count": len(producer_runs),
            "verifier_run_count": len(verifier_runs),
            "mismatches": mismatches,
            "verifier_independent": True,
        }
        self.conn.execute(
            """
            INSERT INTO verification_reports (
                report_id, experiment_id, producer_context, verifier_context,
                producer_run_json, verifier_run_json, separation_verified, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report_id, experiment_id, producer_context_id, verifier_context_id,
                json.dumps(producer_runs, ensure_ascii=False),
                json.dumps(verifier_runs, ensure_ascii=False),
                1 if separation_ok else 0, now_iso(),
            ),
        )
        return report
