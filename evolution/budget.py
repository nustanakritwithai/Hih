"""Budget controls — PAUSED_BUDGET_LIMIT when exceeded."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

from evolution.config import load_config
from evolution.util import new_id, now_iso

PAUSED_BUDGET_LIMIT = "PAUSED_BUDGET_LIMIT"


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class BudgetTracker:
    def __init__(self, conn: sqlite3.Connection, config: dict | None = None) -> None:
        self.conn = conn
        self.config = config or load_config()
        self.limits = self.config.get("budget", {})

    def _row(self, being_id: str) -> sqlite3.Row:
        day = _today()
        row = self.conn.execute(
            "SELECT * FROM budget_usage WHERE being_id = ? AND usage_day = ?",
            (being_id, day),
        ).fetchone()
        if row:
            return row
        uid = new_id("bud")
        self.conn.execute(
            """
            INSERT INTO budget_usage (usage_id, being_id, usage_day, experiments_count, reflections_count, status)
            VALUES (?, ?, ?, 0, 0, 'active')
            """,
            (uid, being_id, day),
        )
        return self.conn.execute(
            "SELECT * FROM budget_usage WHERE being_id = ? AND usage_day = ?",
            (being_id, day),
        ).fetchone()

    def status(self, being_id: str) -> dict[str, Any]:
        row = self._row(being_id)
        limits = {
            "max_experiments_per_day": int(self.limits.get("max_experiments_per_day", 3)),
            "max_reflection_per_session": int(self.limits.get("max_reflection_per_session", 1)),
            "max_candidate_branches": int(self.limits.get("max_candidate_branches", 3)),
            "max_concurrent_experiments": int(self.limits.get("max_concurrent_experiments", 1)),
        }
        paused = row["status"] == PAUSED_BUDGET_LIMIT
        return {
            "status": row["status"],
            "paused": paused,
            "experiments_today": row["experiments_count"],
            "reflections_today": row["reflections_count"],
            "limits": limits,
            "can_start_experiment": (
                not paused
                and row["experiments_count"] < limits["max_experiments_per_day"]
            ),
        }

    def check_experiment(self, being_id: str) -> dict[str, Any]:
        st = self.status(being_id)
        if st["paused"]:
            return {"allowed": False, "status": PAUSED_BUDGET_LIMIT, "reason": "budget_paused"}
        if not st["can_start_experiment"]:
            return {
                "allowed": False,
                "status": PAUSED_BUDGET_LIMIT,
                "reason": "max_experiments_per_day",
            }
        active = self.conn.execute(
            "SELECT COUNT(*) FROM experiments WHERE being_id = ? AND status = 'running'",
            (being_id,),
        ).fetchone()[0]
        max_concurrent = int(self.limits.get("max_concurrent_experiments", 1))
        if active >= max_concurrent:
            return {
                "allowed": False,
                "status": PAUSED_BUDGET_LIMIT,
                "reason": "max_concurrent_experiments",
            }
        return {"allowed": True, "status": "ok"}

    def record_experiment_start(self, being_id: str) -> None:
        row = self._row(being_id)
        count = row["experiments_count"] + 1
        max_exp = int(self.limits.get("max_experiments_per_day", 3))
        status = PAUSED_BUDGET_LIMIT if count >= max_exp else "active"
        self.conn.execute(
            """
            UPDATE budget_usage SET experiments_count = ?, status = ?
            WHERE being_id = ? AND usage_day = ?
            """,
            (count, status, being_id, _today()),
        )

    def check_reflection(self, being_id: str, session_id: str | None) -> dict[str, Any]:
        st = self.status(being_id)
        if st["paused"]:
            return {"allowed": False, "status": PAUSED_BUDGET_LIMIT, "reason": "budget_paused"}
        max_per_session = int(self.limits.get("max_reflection_per_session", 1))
        if session_id:
            existing = self.conn.execute(
                """
                SELECT COUNT(*) FROM evolution_session_reflections
                WHERE being_id = ? AND session_id = ?
                """,
                (being_id, session_id),
            ).fetchone()[0]
            if existing >= max_per_session:
                return {
                    "allowed": False,
                    "status": PAUSED_BUDGET_LIMIT,
                    "reason": "max_reflection_per_session",
                }
        return {"allowed": True, "status": "ok"}

    def record_reflection(self, being_id: str) -> None:
        row = self._row(being_id)
        self.conn.execute(
            """
            UPDATE budget_usage SET reflections_count = reflections_count + 1
            WHERE being_id = ? AND usage_day = ?
            """,
            (being_id, _today()),
        )

    def check_candidate_branch(self, being_id: str) -> dict[str, Any]:
        active = self.conn.execute(
            "SELECT COUNT(*) FROM candidate_branches WHERE status = 'active'"
        ).fetchone()[0]
        max_branches = int(self.limits.get("max_candidate_branches", 3))
        if active >= max_branches:
            return {
                "allowed": False,
                "status": PAUSED_BUDGET_LIMIT,
                "reason": "max_candidate_branches",
            }
        return {"allowed": True, "status": "ok"}
