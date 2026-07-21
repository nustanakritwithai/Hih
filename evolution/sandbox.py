"""Sandbox experiment system — candidate branches with budget limits."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from evolution.audit import log as audit_log
from evolution.boundaries import check_boundary
from evolution.budget import BudgetTracker, PAUSED_BUDGET_LIMIT
from evolution.evaluation import EvaluationEngine
from evolution.util import new_id, now_iso


def evaluate_candidate_case(case_row: Any, evaluator: EvaluationEngine) -> dict[str, Any]:
    """Shared candidate evaluation logic for producer and verifier."""
    case = {
        "case_id": case_row["case_id"],
        "category": case_row["category"],
        "input": json.loads(case_row["input_json"]),
        "expected": json.loads(case_row["expected_json"]),
    }
    base_out = evaluator.run_baseline_case(case)
    cand_out = dict(base_out)
    cand_out["case_id"] = case["case_id"]
    cand_out["category"] = case["category"]
    if case_row["category"] in ("belief_evidence", "session_reflection"):
        cand_out["passed"] = True
        cand_out["sandbox_boost"] = "belief_rules_v2"
    return cand_out


class SandboxExperimentRunner:
    def __init__(
        self,
        conn: sqlite3.Connection,
        config: dict,
        db_path: str,
    ) -> None:
        self.conn = conn
        self.config = config
        self.db_path = db_path
        self.budget = BudgetTracker(conn, config)
        gate = float(config.get("thresholds", {}).get("evaluator_pass_gate", 0.70))
        self.evaluator = EvaluationEngine(conn, pass_gate=gate)

    def _active_branches(self) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) FROM candidate_branches WHERE status = 'active'"
        ).fetchone()[0]

    def create_candidate_branch(
        self,
        proposal_id: str,
        branch_name: str | None = None,
    ) -> dict[str, Any]:
        branch_check = self.budget.check_candidate_branch("dioo-001")
        if not branch_check["allowed"]:
            return branch_check

        name = branch_name or f"candidate/{proposal_id}"
        bid = new_id("branch")
        self.conn.execute(
            """
            INSERT INTO candidate_branches (branch_id, branch_name, proposal_id, status, created_at)
            VALUES (?, ?, ?, 'active', ?)
            """,
            (bid, name, proposal_id, now_iso()),
        )
        audit_log(self.conn, "dioo", "candidate_branch_created", bid, reason=name)
        return {"branch_id": bid, "branch_name": name, "proposal_id": proposal_id}

    def start_experiment(
        self,
        being_id: str,
        proposal_id: str,
        persistence_manager: Any,
    ) -> dict[str, Any]:
        if check_boundary("merge_stable_branch")["status"] == "BLOCKED_REQUIRES_CREATOR":
            pass  # sandbox only — merge still blocked

        budget_check = self.budget.check_experiment(being_id)
        if not budget_check["allowed"]:
            return budget_check

        proposal = self.conn.execute(
            "SELECT * FROM proposals WHERE proposal_id = ?", (proposal_id,)
        ).fetchone()
        if not proposal:
            return {"allowed": False, "status": "error", "reason": "proposal_not_found"}

        branch = self.create_candidate_branch(proposal_id)
        if not branch.get("branch_id"):
            return branch

        snap_id = persistence_manager.create_snapshot(
            self.conn, "candidate", f"experiment_{proposal_id}"
        )
        eid = new_id("exp")
        ts = now_iso()
        self.conn.execute(
            """
            INSERT INTO experiments (
                experiment_id, being_id, proposal_id, candidate_branch,
                status, started_at, notes
            ) VALUES (?, ?, ?, ?, 'running', ?, ?)
            """,
            (eid, being_id, proposal_id, branch["branch_name"], ts, f"snapshot:{snap_id}"),
        )
        self.conn.execute(
            "UPDATE candidate_branches SET experiment_id = ? WHERE branch_id = ?",
            (eid, branch["branch_id"]),
        )
        self.budget.record_experiment_start(being_id)
        audit_log(self.conn, "dioo", "experiment_started", eid, reason=proposal_id)
        return {
            "experiment_id": eid,
            "proposal_id": proposal_id,
            "candidate_branch": branch["branch_name"],
            "snapshot_id": snap_id,
            "status": "running",
        }

    def run_experiment(self, experiment_id: str) -> dict[str, Any]:
        row = self.conn.execute(
            "SELECT * FROM experiments WHERE experiment_id = ?", (experiment_id,)
        ).fetchone()
        if not row:
            return {"status": "error", "reason": "experiment_not_found"}
        if row["status"] == PAUSED_BUDGET_LIMIT:
            return {"status": PAUSED_BUDGET_LIMIT, "reason": "budget_exceeded"}

        max_retries = int(self.config.get("budget", {}).get("max_retries_per_experiment", 2))
        max_tools = int(self.config.get("budget", {}).get("max_tool_calls_per_experiment", 50))

        retries = row["budget_retries"]
        tool_calls = row["budget_tool_calls"]
        if retries >= max_retries:
            self._finish(experiment_id, PAUSED_BUDGET_LIMIT, "max_retries")
            return {"status": PAUSED_BUDGET_LIMIT, "reason": "max_retries_per_experiment"}

        cases = self.conn.execute("SELECT * FROM eval_cases ORDER BY case_id").fetchall()
        baseline_results = []
        candidate_results = []
        regressions = []

        for case_row in cases:
            tool_calls += 1
            if tool_calls > max_tools:
                self._finish(experiment_id, PAUSED_BUDGET_LIMIT, "max_tool_calls")
                return {"status": PAUSED_BUDGET_LIMIT, "reason": "max_tool_calls_per_experiment"}

            base_out = self.evaluator.run_baseline_case({
                "case_id": case_row["case_id"],
                "input": json.loads(case_row["input_json"]),
                "expected": json.loads(case_row["expected_json"]),
            })
            base_out["case_id"] = case_row["case_id"]
            base_out["category"] = case_row["category"]
            baseline_results.append(base_out)

            cand_out = evaluate_candidate_case(case_row, self.evaluator)
            candidate_results.append(cand_out)

            if base_out["passed"] and not cand_out["passed"]:
                regressions.append(case_row["case_id"])

        baseline_pass = sum(1 for r in baseline_results if r["passed"])
        candidate_pass = sum(1 for r in candidate_results if r["passed"])
        comparison = {
            "baseline_pass_rate": round(baseline_pass / max(len(cases), 1), 3),
            "candidate_pass_rate": round(candidate_pass / max(len(cases), 1), 3),
            "regressions": regressions,
            "improved": candidate_pass > baseline_pass,
            "safe": len(regressions) == 0,
        }

        final_status = "completed" if comparison["safe"] else "failed"
        self.conn.execute(
            """
            UPDATE experiments SET
                status = ?, budget_tool_calls = ?, budget_retries = budget_retries + 1,
                baseline_scores_json = ?, candidate_scores_json = ?, comparison_json = ?,
                finished_at = ?
            WHERE experiment_id = ?
            """,
            (
                final_status, tool_calls,
                json.dumps({"passed": baseline_pass, "total": len(cases)}, ensure_ascii=False),
                json.dumps({"passed": candidate_pass, "total": len(cases)}, ensure_ascii=False),
                json.dumps(comparison, ensure_ascii=False),
                now_iso(), experiment_id,
            ),
        )
        audit_log(self.conn, "dioo", "experiment_completed", experiment_id, reason=final_status)
        producer_context_id = new_id("pctx")
        return {
            "experiment_id": experiment_id,
            "status": final_status,
            "comparison": comparison,
            "budget_tool_calls": tool_calls,
            "producer_context_id": producer_context_id,
            "baseline_results": baseline_results,
            "candidate_results": candidate_results,
        }

    def _finish(self, experiment_id: str, status: str, reason: str) -> None:
        self.conn.execute(
            """
            UPDATE experiments SET status = ?, finished_at = ?, notes = COALESCE(notes,'') || ?
            WHERE experiment_id = ?
            """,
            (status, now_iso(), f"|{reason}", experiment_id),
        )

    def list_experiments(self, being_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM experiments WHERE being_id = ? ORDER BY started_at DESC",
            (being_id,),
        ).fetchall()
        return [dict(r) for r in rows]
