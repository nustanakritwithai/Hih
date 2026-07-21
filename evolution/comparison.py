"""Comparison engine — full regression report for baseline vs candidate."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from evolution.util import new_id, now_iso

AUTO_REJECT_CATEGORIES = frozenset({
    "identity_consistency",
    "permission_scope",
    "safety_compliance",
    "regression_rollback",
})


class ComparisonEngine:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def build_report(
        self,
        experiment_id: str,
        baseline_results: list[dict[str, Any]],
        candidate_results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        regressions = []
        improvements = []
        all_cases = []

        for base, cand in zip(baseline_results, candidate_results):
            case_id = base.get("case_id", cand.get("case_id"))
            category = base.get("category", cand.get("category", "unknown"))
            entry = {
                "case_id": case_id,
                "category": category,
                "baseline_passed": base.get("passed", False),
                "candidate_passed": cand.get("passed", False),
            }
            all_cases.append(entry)
            if entry["baseline_passed"] and not entry["candidate_passed"]:
                regressions.append(entry)
            elif not entry["baseline_passed"] and entry["candidate_passed"]:
                improvements.append(entry)

        identity_regression = any(
            r["category"] == "identity_consistency" for r in regressions
        )
        permission_regression = any(
            r["category"] == "permission_scope" for r in regressions
        )
        safety_regression = any(
            r["category"] in ("safety_compliance", "permission_scope")
            and "security" in json.dumps(r)
            for r in regressions
        ) or any(
            r["category"] == "permission_scope" and "perm_002" in r.get("case_id", "")
            for r in regressions
        )

        report_id = new_id("crep")
        report = {
            "report_id": report_id,
            "experiment_id": experiment_id,
            "total_cases": len(all_cases),
            "regressions": regressions,
            "improvements": improvements,
            "all_cases": all_cases,
            "regression_count": len(regressions),
            "improvement_count": len(improvements),
            "identity_regression": identity_regression,
            "permission_regression": permission_regression,
            "safety_regression": permission_regression or safety_regression,
        }
        self.conn.execute(
            """
            INSERT INTO comparison_reports (
                report_id, experiment_id, regressions_json,
                improvements_json, all_cases_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                report_id, experiment_id,
                json.dumps(regressions, ensure_ascii=False),
                json.dumps(improvements, ensure_ascii=False),
                json.dumps(all_cases, ensure_ascii=False),
                now_iso(),
            ),
        )
        return report
