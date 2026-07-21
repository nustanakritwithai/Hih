"""Trajectory recorder — append-only task trajectories."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from evolution.redaction import redact_obj
from evolution.util import new_id, now_iso


REQUIRED_FIELDS = {
    "trajectory_id", "being_id", "task_type", "objective", "started_at", "result_status",
}


def validate_trajectory(data: dict[str, Any]) -> list[str]:
    errors = []
    for f in REQUIRED_FIELDS:
        if f not in data or data[f] is None:
            errors.append(f"missing:{f}")
    if data.get("result_status") not in (
        "in_progress", "success", "partial", "failure", "cancelled", None,
    ):
        errors.append("invalid:result_status")
    return errors


class TrajectoryRecorder:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def start(
        self,
        being_id: str,
        objective: str,
        task_type: str = "development",
        session_id: str | None = None,
        goal_id: str | None = None,
        task_id: str | None = None,
        initial_context_summary: str = "",
        parent_trajectory_id: str | None = None,
        software_version: str = "0.3.0",
        evaluator_version: str = "1.0.0",
    ) -> str:
        tid = new_id("traj")
        ts = now_iso()
        self.conn.execute(
            """
            INSERT INTO trajectories (
                trajectory_id, being_id, session_id, goal_id, task_id, task_type,
                objective, initial_context_summary, started_at, result_status,
                software_version, evaluator_version, parent_trajectory_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'in_progress', ?, ?, ?)
            """,
            (
                tid, being_id, session_id, goal_id, task_id, task_type,
                redact_obj(objective), redact_obj(initial_context_summary),
                ts, software_version, evaluator_version, parent_trajectory_id,
            ),
        )
        return tid

    def append_action(self, trajectory_id: str, action: dict[str, Any]) -> None:
        row = self.conn.execute(
            "SELECT actions_json FROM trajectories WHERE trajectory_id = ?", (trajectory_id,)
        ).fetchone()
        if not row:
            raise KeyError(trajectory_id)
        actions = json.loads(row[0])
        actions.append(redact_obj({**action, "at": now_iso()}))
        self.conn.execute(
            "UPDATE trajectories SET actions_json = ? WHERE trajectory_id = ?",
            (json.dumps(actions, ensure_ascii=False), trajectory_id),
        )

    def finish(
        self,
        trajectory_id: str,
        result_status: str,
        result_summary: str = "",
        errors: list | None = None,
        duration_ms: int | None = None,
    ) -> None:
        ts = now_iso()
        errors_json = json.dumps(redact_obj(errors or []), ensure_ascii=False)
        self.conn.execute(
            """
            UPDATE trajectories SET
                finished_at = ?, result_status = ?, result_summary = ?,
                errors_json = ?, duration_ms = COALESCE(?, duration_ms)
            WHERE trajectory_id = ?
            """,
            (ts, result_status, redact_obj(result_summary), errors_json, duration_ms, trajectory_id),
        )

    def link_event(self, trajectory_id: str, event_id: str) -> None:
        row = self.conn.execute(
            "SELECT related_events_json FROM trajectories WHERE trajectory_id = ?", (trajectory_id,)
        ).fetchone()
        events = json.loads(row[0])
        if event_id not in events:
            events.append(event_id)
        self.conn.execute(
            "UPDATE trajectories SET related_events_json = ? WHERE trajectory_id = ?",
            (json.dumps(events), trajectory_id),
        )

    def get(self, trajectory_id: str) -> dict[str, Any]:
        row = self.conn.execute(
            "SELECT * FROM trajectories WHERE trajectory_id = ?", (trajectory_id,)
        ).fetchone()
        if not row:
            raise KeyError(trajectory_id)
        return dict(row)
