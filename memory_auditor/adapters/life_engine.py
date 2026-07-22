"""Read-only adapter: map Life Engine SQLite rows → MemoryRecord."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from memory_auditor.snapshot import SnapshotInfo, connect_readonly, connect_source_readonly, create_readonly_snapshot
from memory_auditor.types import ControlRole, MemoryRecord, MemoryType

# Phrases indicating report-depth / autonomy patterns (semantic grouping)
PATTERN_CLUSTERS: dict[str, tuple[str, ...]] = {
    "report_concise": ("สั้น", "concise", "brief", "milestone", "กระชับ"),
    "report_detailed": ("ละเอียด", "detail", "ครบ", "full"),
    "autonomy": ("อิสระ", "autonomy", "เองได้", "independent"),
    "notify_before": ("แจ้งก่อน", "notify", "ต้องบอก"),
}


class LifeEngineReadOnlyAdapter:
    """Extract MemoryRecords from Life Engine DB without any writes."""

    def __init__(self, db_path: str, use_snapshot: bool = True) -> None:
        self.db_path = db_path
        self.use_snapshot = use_snapshot
        self._snapshot: SnapshotInfo | None = None
        self._conn: sqlite3.Connection | None = None

    def __enter__(self) -> LifeEngineReadOnlyAdapter:
        if self.use_snapshot:
            self._snapshot = create_readonly_snapshot(self.db_path)
            self._conn = connect_readonly(self._snapshot)
        else:
            self._conn = connect_source_readonly(self.db_path)
        return self

    def __exit__(self, *args: Any) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    @property
    def snapshot_info(self) -> dict[str, str] | None:
        if not self._snapshot:
            return None
        return {
            "source_path": self._snapshot.source_path,
            "snapshot_path": self._snapshot.snapshot_path,
        }

    def extract_records(self, being_id: str = "dioo-001") -> list[MemoryRecord]:
        if not self._conn:
            raise RuntimeError("adapter not opened — use with-statement")
        records: list[MemoryRecord] = []
        records.extend(self._extract_identity(being_id))
        records.extend(self._extract_events(being_id))
        records.extend(self._extract_episodic(being_id))
        records.extend(self._extract_self_memories(being_id))
        records.extend(self._extract_reflections(being_id))
        records.extend(self._extract_beliefs(being_id))
        records.extend(self._extract_concerns(being_id))
        records.extend(self._extract_autonomy_permissions(being_id))
        records.extend(self._extract_retrieval_path_risks(being_id))
        return records

    def _extract_identity(self, being_id: str) -> list[MemoryRecord]:
        row = self._conn.execute(
            "SELECT being_id, created_at, origin, core_values, boundaries FROM beings WHERE being_id = ?",
            (being_id,),
        ).fetchone()
        if not row:
            return []
        core_values = json.loads(row["core_values"] or "[]")
        boundaries = json.loads(row["boundaries"] or "{}")
        base_meta = {"backup_known": False, "versioning": True, "source": "beings"}
        return [
            MemoryRecord(
                record_id=f"identity-{being_id}",
                memory_type=MemoryType.IDENTITY_ROOT,
                control_role=ControlRole.PROTECTED_IDENTITY,
                content=being_id,
                domain="identity",
                metadata={**base_meta, "field": "being_id"},
            ),
            MemoryRecord(
                record_id=f"identity-created-{being_id}",
                memory_type=MemoryType.IDENTITY_ROOT,
                control_role=ControlRole.PROTECTED_IDENTITY,
                content=row["created_at"] or "",
                domain="identity",
                metadata={**base_meta, "field": "birth_date"},
            ),
            MemoryRecord(
                record_id=f"identity-origin-{being_id}",
                memory_type=MemoryType.IDENTITY_ROOT,
                control_role=ControlRole.PROTECTED_IDENTITY,
                content=row["origin"] or "",
                domain="identity",
                metadata={**base_meta, "field": "origin"},
            ),
            MemoryRecord(
                record_id=f"identity-values-{being_id}",
                memory_type=MemoryType.IDENTITY_ROOT,
                control_role=ControlRole.PROTECTED_IDENTITY,
                content=", ".join(core_values) if isinstance(core_values, list) else str(core_values),
                domain="identity",
                metadata={**base_meta, "field": "core_values"},
            ),
            MemoryRecord(
                record_id=f"identity-boundaries-{being_id}",
                memory_type=MemoryType.IDENTITY_ROOT,
                control_role=ControlRole.PROTECTED_IDENTITY,
                content=json.dumps(boundaries, ensure_ascii=False),
                domain="identity",
                metadata={**base_meta, "field": "identity_boundaries"},
            ),
        ]

    def _extract_events(self, being_id: str) -> list[MemoryRecord]:
        rows = self._conn.execute(
            "SELECT event_id, event_type, timestamp, payload FROM events WHERE being_id = ? ORDER BY timestamp",
            (being_id,),
        ).fetchall()
        out: list[MemoryRecord] = []
        for row in rows:
            payload = json.loads(row["payload"] or "{}")
            content = payload.get("text") or payload.get("message") or json.dumps(payload, ensure_ascii=False)[:500]
            out.append(MemoryRecord(
                record_id=row["event_id"],
                memory_type=MemoryType.RAW_EVENT,
                control_role=ControlRole.AUTHORITATIVE_SOURCE,
                content=str(content),
                domain=row["event_type"] or "event",
                effective_time=row["timestamp"],
                metadata={"event_type": row["event_type"]},
            ))
        return out

    def _extract_episodic(self, being_id: str) -> list[MemoryRecord]:
        rows = self._conn.execute(
            """
            SELECT memory_id, event_id, event_text, interpretation, importance, timestamp
            FROM episodic_memories WHERE being_id = ? ORDER BY timestamp DESC
            """,
            (being_id,),
        ).fetchall()
        out: list[MemoryRecord] = []
        for row in rows:
            src = (row["event_id"],) if row["event_id"] else ()
            text = row["event_text"] or ""
            out.append(MemoryRecord(
                record_id=row["memory_id"],
                memory_type=MemoryType.DERIVED_SUMMARY,
                control_role=ControlRole.RETRIEVAL_CUE,
                content=text,
                domain="episodic",
                source_event_ids=src,
                authority_for_behavior=False,
                metadata={
                    "interpretation": row["interpretation"],
                    "importance": row["importance"],
                    "retrieval_path": "build_llm_context.relevant_memories",
                    "pattern_clusters": _detect_pattern_clusters(text),
                },
            ))
        return out

    def _extract_self_memories(self, being_id: str) -> list[MemoryRecord]:
        cols = {r[1] for r in self._conn.execute("PRAGMA table_info(self_memories)").fetchall()}
        if "memory_type" in cols:
            rows = self._conn.execute(
                """
                SELECT id, observation, memory_type, confidence, behavioral_adjustment, created_at
                FROM self_memories WHERE being_id = ? ORDER BY updated_at DESC
                """,
                (being_id,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT id, observation, confidence, behavioral_adjustment, created_at
                FROM self_memories WHERE being_id = ? ORDER BY updated_at DESC
                """,
                (being_id,),
            ).fetchall()
        out: list[MemoryRecord] = []
        for row in rows:
            obs = row["observation"] or ""
            out.append(MemoryRecord(
                record_id=f"self-memory-{row['id']}",
                memory_type=MemoryType.DERIVED_SELF_MODEL,
                control_role=ControlRole.CANDIDATE_ONLY,
                content=obs,
                domain=row["memory_type"] if "memory_type" in row.keys() else "self",
                authority_for_behavior=False,
                metadata={
                    "confidence": row["confidence"],
                    "behavioral_adjustment": row["behavioral_adjustment"],
                    "retrieval_path": "build_llm_context.self_memories → presence.md",
                    "pattern_clusters": _detect_pattern_clusters(obs),
                },
            ))
        return out

    def _extract_reflections(self, being_id: str) -> list[MemoryRecord]:
        rows = self._conn.execute(
            "SELECT reflection_id, level, summary, lessons FROM reflections WHERE being_id = ?",
            (being_id,),
        ).fetchall()
        out: list[MemoryRecord] = []
        for row in rows:
            if not row["summary"]:
                continue
            out.append(MemoryRecord(
                record_id=row["reflection_id"],
                memory_type=MemoryType.DERIVED_INTERPRETATION,
                control_role=ControlRole.NON_AUTHORITATIVE,
                content=row["summary"],
                domain=row["level"] or "reflection",
                authority_for_behavior=False,
                metadata={
                    "retrieval_path": "stored_only_not_in_build_llm_context",
                    "lessons": row["lessons"],
                },
            ))
        return out

    def _extract_beliefs(self, being_id: str) -> list[MemoryRecord]:
        try:
            rows = self._conn.execute(
                "SELECT belief_id, statement, belief_type, confidence, status FROM beliefs WHERE being_id = ?",
                (being_id,),
            ).fetchall()
        except sqlite3.OperationalError:
            return []
        return [
            MemoryRecord(
                record_id=row["belief_id"],
                memory_type=MemoryType.BELIEF,
                control_role=ControlRole.CANDIDATE_ONLY,
                content=row["statement"],
                domain=row["belief_type"] or "belief",
                status=row["status"] or "candidate",
                authority_for_behavior=False,
                metadata={"confidence": row["confidence"]},
            )
            for row in rows
        ]

    def _extract_concerns(self, being_id: str) -> list[MemoryRecord]:
        rows = self._conn.execute(
            "SELECT concern_id, concern_text, urgency, status FROM concerns WHERE being_id = ?",
            (being_id,),
        ).fetchall()
        return [
            MemoryRecord(
                record_id=row["concern_id"],
                memory_type=MemoryType.CONCERN,
                control_role=ControlRole.RETRIEVAL_CUE,
                content=row["concern_text"],
                domain="concern",
                status=row["status"] or "open",
                metadata={"urgency": row["urgency"]},
            )
            for row in rows
        ]

    def _extract_autonomy_permissions(self, being_id: str) -> list[MemoryRecord]:
        row = self._conn.execute(
            "SELECT identity_fixed FROM beings WHERE being_id = ?", (being_id,)
        ).fetchone()
        if not row:
            return []
        fixed = json.loads(row["identity_fixed"] or "{}")
        profile = fixed.get("autonomy_profile", {})
        out: list[MemoryRecord] = []
        for action, level in profile.items():
            out.append(MemoryRecord(
                record_id=f"permission-autonomy-{action}",
                memory_type=MemoryType.PERMISSION_RECORD,
                control_role=ControlRole.ACTION_AUTHORITY,
                content=f"{action}={level}",
                domain="autonomy",
                scope=action,
                status="ACTIVE" if level != "forbidden" else "INACTIVE",
                authority_for_behavior=level in ("allowed", "allowed_within_sandbox", "allowed_within_mission"),
                metadata={"source": "identity_fixed.autonomy_profile", "level": level},
            ))
        return out

    def _extract_retrieval_path_risks(self, being_id: str) -> list[MemoryRecord]:
        """Synthetic evaluation assets from architecture inspection — not DB rows."""
        risks: list[MemoryRecord] = []
        episodic_count = self._conn.execute(
            "SELECT COUNT(*) FROM episodic_memories WHERE being_id = ?", (being_id,)
        ).fetchone()[0]
        if episodic_count > 0:
            risks.append(MemoryRecord(
                record_id="eval-retrieval-episodic-in-context",
                memory_type=MemoryType.EVALUATION_ASSET,
                control_role=ControlRole.VALIDATION_GATE,
                content="episodic_memories enter build_llm_context without permission routing",
                domain="retrieval_architecture",
                metadata={"table": "episodic_memories", "limit": 5},
            ))
        self_count = self._conn.execute(
            "SELECT COUNT(*) FROM self_memories WHERE being_id = ?", (being_id,)
        ).fetchone()[0]
        if self_count > 0:
            risks.append(MemoryRecord(
                record_id="eval-retrieval-self-in-context",
                memory_type=MemoryType.EVALUATION_ASSET,
                control_role=ControlRole.VALIDATION_GATE,
                content="self_memories behavioral_adjustment enters presence without authority check",
                domain="retrieval_architecture",
                metadata={"table": "self_memories", "presence_limit": 3},
            ))
        return risks


def _detect_pattern_clusters(text: str) -> list[str]:
    lower = text.lower()
    return [name for name, phrases in PATTERN_CLUSTERS.items() if any(p in lower for p in phrases)]
