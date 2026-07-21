"""Self-Evolution Engine orchestrator — Phase E1."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from evolution.audit import log as audit_log
from evolution.boundaries import check_boundary
from evolution.config import load_config
from evolution.dashboard import build_dashboard, format_dashboard_text
from evolution.comparison import ComparisonEngine
from evolution.diagnosis import FailureAnalyzer
from evolution.evaluation import EvaluationEngine
from evolution.gate import AcceptanceGate
from evolution.memory import EvolutionMemoryStore
from evolution.migrate import migrate
from evolution.persistence import PersistenceManager
from evolution.proposals import ProposalEngine
from evolution.sandbox import SandboxExperimentRunner
from evolution.session_reflection import SessionReflectionV2
from evolution.trajectory import TrajectoryRecorder
from evolution.verifier import ExperimentVerifier
from evolution.util import now_iso


class EvolutionEngine:
    def __init__(self, db_path: str | Path = "state/dioo.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.config = load_config()
        self._init_schema()
        self.conn = self._connect()
        migrate(self.conn)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(schema)
            migrate(conn)

    def close(self) -> None:
        self.conn.close()

    @property
    def trajectories(self) -> TrajectoryRecorder:
        return TrajectoryRecorder(self.conn)

    @property
    def evaluator(self) -> EvaluationEngine:
        gate = float(self.config.get("thresholds", {}).get("evaluator_pass_gate", 0.70))
        return EvaluationEngine(self.conn, pass_gate=gate)

    @property
    def failures(self) -> FailureAnalyzer:
        return FailureAnalyzer(self.conn)

    @property
    def proposals(self) -> ProposalEngine:
        return ProposalEngine(self.conn)

    @property
    def persistence(self) -> PersistenceManager:
        return PersistenceManager(self.db_path)

    def record_task_cycle(
        self,
        being_id: str,
        objective: str,
        result_status: str = "success",
        session_id: str | None = None,
        goal_id: str | None = None,
        errors: list | None = None,
    ) -> dict[str, Any]:
        """Full E1 cycle: trajectory → evaluate → failure? → proposal?"""
        check = check_boundary("record_trajectory")
        if not check["allowed"]:
            return check

        snap = self.persistence.create_snapshot(self.conn, "stable", "pre_task_cycle")
        audit_log(self.conn, "dioo", "snapshot_created", snap, reason="pre_task_cycle")

        tid = self.trajectories.start(
            being_id, objective, session_id=session_id, goal_id=goal_id,
            software_version=self.config.get("evolution", {}).get("stable_version", "0.3.0"),
        )
        self.trajectories.finish(tid, result_status, errors=errors)
        traj = self.trajectories.get(tid)

        evaluation = self.evaluator.evaluate_trajectory(traj)
        self.evaluator.save(evaluation)

        result: dict[str, Any] = {
            "trajectory_id": tid,
            "evaluation_id": evaluation["evaluation_id"],
            "passed": evaluation["passed_required_gates"],
            "aggregate_score": evaluation["aggregate_score"],
        }

        if not evaluation["passed_required_gates"] or result_status == "failure":
            category = "EVALUATION_FAILURE" if not evaluation["passed_required_gates"] else "IMPLEMENTATION_FAILURE"
            fail = self.failures.record(
                being_id, category,
                symptom=evaluation.get("critical_failures", ["task_failed"])[0] if evaluation.get("critical_failures") else "task_failed",
                observed=result_status,
                expected="success",
                trajectory_id=tid,
                evaluation_id=evaluation["evaluation_id"],
                severity="high" if result_status == "failure" else "medium",
                modules=["evolution.evaluation"],
            )
            failure_row = dict(
                self.conn.execute(
                    "SELECT * FROM failures WHERE failure_id = ?", (fail["failure_id"],)
                ).fetchone()
            )
            diagnosis = self.failures.diagnose(failure_row)
            result["failure"] = {"failure_id": fail["failure_id"], "diagnosis": diagnosis}

            if self.config.get("features", {}).get("proposal_engine", False):
                proposal = self.proposals.create_from_failure(being_id, failure_row, diagnosis)
                result["proposal"] = {"proposal_id": proposal["proposal_id"], "status": proposal["status"]}
                audit_log(self.conn, "dioo", "proposal_created", proposal["proposal_id"])

        self.conn.commit()
        return result

    def seed_baseline_cases(self, cases: list[dict[str, Any]]) -> int:
        count = 0
        for case in cases:
            exists = self.conn.execute(
                "SELECT 1 FROM eval_cases WHERE case_id = ?", (case["case_id"],)
            ).fetchone()
            if exists:
                continue
            self.conn.execute(
                """
                INSERT INTO eval_cases (
                    case_id, category, title, input_json, expected_json,
                    tags_json, source_failure_id, immutable, created_at, evaluator_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    case["case_id"], case["category"], case["title"],
                    json.dumps(case["input"], ensure_ascii=False),
                    json.dumps(case["expected"], ensure_ascii=False),
                    json.dumps(case.get("tags", []), ensure_ascii=False),
                    case.get("source_failure_id"), case.get("immutable", 0),
                    case.get("created_at", now_iso()), case.get("evaluator_version", "1.0.0"),
                ),
            )
            count += 1
        self.conn.commit()
        return count

    def run_baseline_suite(self) -> dict[str, Any]:
        rows = self.conn.execute("SELECT * FROM eval_cases ORDER BY case_id").fetchall()
        results = []
        passed = 0
        for row in rows:
            case = {
                "case_id": row["case_id"],
                "input": json.loads(row["input_json"]),
                "expected": json.loads(row["expected_json"]),
            }
            outcome = self.evaluator.run_baseline_case(case)
            run_id = f"run-{case['case_id']}"
            self.conn.execute(
                """
                INSERT OR REPLACE INTO eval_runs (run_id, case_id, baseline_or_candidate, result_json, passed, created_at)
                VALUES (?, ?, 'baseline', ?, ?, ?)
                """,
                (run_id, case["case_id"], json.dumps(outcome, ensure_ascii=False),
                 1 if outcome["passed"] else 0, now_iso()),
            )
            if outcome["passed"]:
                passed += 1
            results.append(outcome)
        self.conn.commit()
        return {"total": len(results), "passed": passed, "failed": len(results) - passed, "results": results}

    def dashboard(self, being_id: str = "dioo-001") -> dict[str, Any]:
        return build_dashboard(self.conn, being_id)

    def dashboard_text(self, being_id: str = "dioo-001") -> str:
        return format_dashboard_text(self.dashboard(being_id))

    def recover(self, snapshot_id: str) -> dict[str, Any]:
        backup = self.persistence.restore_snapshot(snapshot_id, self.conn)
        audit_log(self.conn, "dioo", "snapshot_restored", snapshot_id, reason="manual_recovery")
        self.conn.commit()
        return {"snapshot_id": snapshot_id, "pre_restore_backup": backup}

    def check_corruption(self) -> dict[str, Any]:
        issues = self.persistence.detect_corruption(self.conn)
        schema_v = self.conn.execute(
            "SELECT version FROM evolution_schema_version LIMIT 1"
        ).fetchone()
        migrations = self.conn.execute(
            "SELECT COUNT(*) FROM evolution_migration_history"
        ).fetchone()[0]
        return {
            "healthy": len(issues) == 0,
            "issues": issues,
            "schema_version": schema_v[0] if schema_v else 0,
            "migration_count": migrations,
        }

    def rollback_test(self) -> dict[str, Any]:
        result = self.persistence.rollback_test(self.conn)
        audit_log(
            self.conn, "dioo", "rollback_test",
            result.get("snapshot_id", "none"),
            reason="passed" if result["passed"] else "failed",
        )
        self.conn.commit()
        return result

    def create_candidate_snapshot(self, notes: str = "candidate") -> str:
        return self.persistence.create_snapshot(self.conn, "candidate", notes)

    def session_reflect_v2(
        self,
        being_id: str,
        session_id: str | None = None,
        summary: str | None = None,
    ) -> dict[str, Any]:
        if not self.config.get("features", {}).get("session_reflection_v2", False):
            return {"allowed": False, "status": "disabled", "reason": "feature_flag_off"}
        sr = SessionReflectionV2(self.conn, self.config)
        result = sr.run(being_id, session_id=session_id, summary=summary)
        self.conn.commit()
        return result

    def start_sandbox_experiment(self, being_id: str, proposal_id: str) -> dict[str, Any]:
        if not self.config.get("features", {}).get("sandbox_experiment", False):
            return {"allowed": False, "status": "disabled", "reason": "feature_flag_off"}
        runner = SandboxExperimentRunner(self.conn, self.config, str(self.db_path))
        result = runner.start_experiment(being_id, proposal_id, self.persistence)
        self.conn.commit()
        return result

    def run_sandbox_experiment(self, experiment_id: str, being_id: str = "dioo-001") -> dict[str, Any]:
        if not self.config.get("features", {}).get("sandbox_experiment", False):
            return {"allowed": False, "status": "disabled", "reason": "feature_flag_off"}
        runner = SandboxExperimentRunner(self.conn, self.config, str(self.db_path))
        result = runner.run_experiment(experiment_id)
        if result.get("status") not in ("completed", "failed"):
            self.conn.commit()
            return result

        features = self.config.get("features", {})
        if features.get("verifier", False):
            verifier = ExperimentVerifier(self.conn, self.config)
            verification = verifier.verify(
                experiment_id,
                result.get("producer_context_id", "unknown"),
                result,
            )
            result["verification"] = verification
        else:
            verification = None

        if features.get("comparison_gate", False):
            comparison = ComparisonEngine(self.conn).build_report(
                experiment_id,
                result.get("baseline_results", []),
                result.get("candidate_results", []),
            )
            result["comparison_report"] = comparison
            gate = AcceptanceGate(self.conn).evaluate(experiment_id, comparison, verification)
            result["gate_decision"] = gate
            audit_log(
                self.conn, "dioo", "acceptance_gate",
                experiment_id, reason=gate.get("recommendation"),
            )
            if features.get("evolution_memory", False):
                mem = EvolutionMemoryStore(self.conn).record_gate_decision(
                    being_id, gate, comparison,
                )
                result["evolution_memory"] = mem

        self.conn.commit()
        return result

    def evaluate_belief_candidate(
        self,
        candidate: dict[str, Any],
        evidence_links: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not self.config.get("features", {}).get("belief_rules_v2", False):
            return {"allowed": False, "status": "disabled", "reason": "feature_flag_off"}
        from evolution.belief_rules import BeliefRulesV2
        return BeliefRulesV2(self.config).evaluate_candidate(candidate, evidence_links)

    def seed_skill_registry(self) -> None:
        skills = [
            ("session_reflection", "Session Reflection", "0.1.0"),
            ("belief_candidate_generation", "Belief Candidate Generation", "0.1.0"),
            ("belief_evidence_evaluation", "Belief Evidence Evaluation", "0.1.0"),
            ("memory_consolidation", "Memory Consolidation", "0.1.0"),
            ("goal_prioritization", "Goal Prioritization", "0.1.0"),
            ("response_generation", "Response Generation", "0.1.0"),
            ("failure_diagnosis", "Failure Diagnosis", "0.1.0"),
            ("improvement_proposal_generation", "Improvement Proposal", "0.1.0"),
        ]
        for sid, name, ver in skills:
            self.conn.execute(
                """
                INSERT OR IGNORE INTO skill_registry (skill_id, name, version, status)
                VALUES (?, ?, ?, 'stable')
                """,
                (sid, name, ver),
            )
        self.conn.commit()
