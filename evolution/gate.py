"""Acceptance gate — auto-reject safety, permission, identity regressions."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from evolution.boundaries import check_boundary
from evolution.util import new_id, now_iso

RECOMMEND_ACCEPT = "RECOMMEND_ACCEPT"
RECOMMEND_REJECT = "RECOMMEND_REJECT"
NEEDS_CREATOR_APPROVAL = "NEEDS_CREATOR_APPROVAL"


class AcceptanceGate:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def evaluate(
        self,
        experiment_id: str,
        comparison_report: dict[str, Any],
        verification_report: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if check_boundary("merge_stable_branch")["status"] == "BLOCKED_REQUIRES_CREATOR":
            merge_blocked = True
        else:
            merge_blocked = False

        auto_reject_reasons = []
        if comparison_report.get("identity_regression"):
            auto_reject_reasons.append("identity_regression")
        if comparison_report.get("permission_regression"):
            auto_reject_reasons.append("permission_regression")
        if comparison_report.get("safety_regression"):
            auto_reject_reasons.append("safety_regression")
        if verification_report and not verification_report.get("separation_verified"):
            auto_reject_reasons.append("verifier_mismatch_or_context_collision")
        if verification_report and verification_report.get("mismatches"):
            auto_reject_reasons.append("producer_verifier_mismatch")

        if auto_reject_reasons:
            recommendation = RECOMMEND_REJECT
        elif comparison_report.get("regression_count", 0) > 0:
            recommendation = RECOMMEND_REJECT
        elif merge_blocked:
            recommendation = NEEDS_CREATOR_APPROVAL
        elif comparison_report.get("improvement_count", 0) > 0:
            recommendation = NEEDS_CREATOR_APPROVAL
        else:
            recommendation = NEEDS_CREATOR_APPROVAL

        decision_id = new_id("gate")
        decision = {
            "decision_id": decision_id,
            "experiment_id": experiment_id,
            "comparison_report_id": comparison_report.get("report_id"),
            "recommendation": recommendation,
            "auto_rejected_reasons": auto_reject_reasons,
            "identity_regression": comparison_report.get("identity_regression", False),
            "permission_regression": comparison_report.get("permission_regression", False),
            "safety_regression": comparison_report.get("safety_regression", False),
            "merge_to_stable_allowed": False,
            "requires_creator_approval": recommendation != RECOMMEND_REJECT,
        }
        self.conn.execute(
            """
            INSERT INTO acceptance_decisions (
                decision_id, experiment_id, comparison_report_id,
                recommendation, auto_rejected_reasons_json,
                identity_regression, permission_regression, safety_regression, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                decision_id, experiment_id, comparison_report.get("report_id"),
                recommendation, json.dumps(auto_reject_reasons, ensure_ascii=False),
                1 if decision["identity_regression"] else 0,
                1 if decision["permission_regression"] else 0,
                1 if decision["safety_regression"] else 0,
                now_iso(),
            ),
        )
        return decision
