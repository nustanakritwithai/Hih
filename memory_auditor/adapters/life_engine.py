"""Read-only adapter: map Life Engine SQLite rows → MemoryRecord."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from memory_auditor.snapshot import (
    SnapshotInfo,
    cleanup_snapshot,
    connect_readonly,
    connect_source_readonly,
    create_readonly_snapshot,
    verify_source_unchanged,
)
from memory_auditor.types import ControlRole, EventSourceAuthority, MemoryRecord, MemoryType

PATTERN_CLUSTERS: dict[str, tuple[str, ...]] = {
    "report_concise": ("สั้น", "concise", "brief", "milestone", "กระชับ"),
    "report_detailed": ("ละเอียด", "detail", "ครบ", "full"),
    "autonomy": ("อิสระ", "autonomy", "เองได้", "independent"),
    "notify_before": ("แจ้งก่อน", "notify", "ต้องบอก"),
}

CREATOR_EVENT_TYPES = frozenset({
    "USER_MESSAGE", "CREATOR_MESSAGE", "CREATOR_DIRECT", "creator_message",
})
TOOL_EVENT_TYPES = frozenset({"TOOL_RESULT", "TOOL_CALL", "tool_result", "tool_call"})
AGENT_EVENT_TYPES = frozenset({"AGENT_ACTION", "DIOO_ACTION", "agent_action"})


class LifeEngineReadOnlyAdapter:
    """Extract MemoryRecords from Life Engine DB without any writes."""

    def __init__(self, db_path: str, use_snapshot: bool = True) -> None:
        self.db_path = db_path
        self.use_snapshot = use_snapshot
        self._snapshot: SnapshotInfo | None = None
        self._conn: sqlite3.Connection | None = None
        self.adapter_errors: list[dict[str, str]] = []

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
        if self._snapshot:
            verify_source_unchanged(self._snapshot)
            self._snapshot.cleanup_result = cleanup_snapshot(self._snapshot)

    @property
    def snapshot_info(self) -> dict[str, Any] | None:
        if not self._snapshot:
            return None
        return {
            "source_path": self._snapshot.source_path,
            "snapshot_path": self._snapshot.snapshot_path,
            "method": self._snapshot.method,
            "source_hash_before": self._snapshot.source_hash_before,
            "source_hash_after": self._snapshot.source_hash_after,
            "source_mtime_before": self._snapshot.source_mtime_before,
            "source_mtime_after": self._snapshot.source_mtime_after,
            "wal_present_before": self._snapshot.wal_present_before,
            "wal_present_after": self._snapshot.wal_present_after,
            "concurrent_write_status": self._snapshot.concurrent_write_status,
            "cleanup_result": self._snapshot.cleanup_result,
            "integrity_verified": self._snapshot.integrity_verified(),
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

    def _safe_json(self, raw: str | None, context: str) -> dict:
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {"value": parsed}
        except json.JSONDecodeError as exc:
            self.adapter_errors.append({
                "error": "MALFORMED_JSON",
                "context": context,
                "detail": str(exc)[:120],
            })
            return {}

    def _extract_identity(self, being_id: str) -> list[MemoryRecord]:
        row = self._conn.execute(
            "SELECT being_id, created_at, origin, core_values, boundaries FROM beings WHERE being_id = ?",
            (being_id,),
        ).fetchone()
        if not row:
            return []
        core_values = self._safe_json(row["core_values"], f"beings.core_values:{being_id}")
        if isinstance(core_values, dict) and "value" in core_values:
            core_values = core_values["value"]
        boundaries = self._safe_json(row["boundaries"], f"beings.boundaries:{being_id}")
        base_meta = {"backup_known": False, "versioning": True, "source": "beings"}
        cv_text = ", ".join(core_values) if isinstance(core_values, list) else str(core_values)
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
                content=cv_text,
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
            payload = self._safe_json(row["payload"], f"events.payload:{row['event_id']}")
            content = payload.get("text") or payload.get("message") or "[payload_redacted]"
            control_role, source_authority = _classify_event(row["event_type"], payload)
            out.append(MemoryRecord(
                record_id=row["event_id"],
                memory_type=MemoryType.RAW_EVENT,
                control_role=control_role,
                content=str(content)[:200],
                domain=row["event_type"] or "event",
                effective_time=row["timestamp"],
                authority_for_behavior=False,
                metadata={
                    "event_type": row["event_type"],
                    "source_authority": source_authority.value,
                },
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
                content=text[:200],
                domain="episodic",
                source_event_ids=src,
                authority_for_behavior=False,
                metadata={
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
                content=obs[:200],
                domain=row["memory_type"] if "memory_type" in row.keys() else "self",
                authority_for_behavior=False,
                metadata={
                    "confidence": row["confidence"],
                    "retrieval_path": "build_llm_context.self_memories → presence.md",
                    "pattern_clusters": _detect_pattern_clusters(obs),
                },
            ))
        return out

    def _extract_reflections(self, being_id: str) -> list[MemoryRecord]:
        try:
            rows = self._conn.execute(
                "SELECT reflection_id, level, summary, lessons FROM reflections WHERE being_id = ?",
                (being_id,),
            ).fetchall()
        except sqlite3.OperationalError:
            self.adapter_errors.append({"error": "MISSING_TABLE", "context": "reflections"})
            return []
        out: list[MemoryRecord] = []
        for row in rows:
            if not row["summary"]:
                continue
            out.append(MemoryRecord(
                record_id=row["reflection_id"],
                memory_type=MemoryType.DERIVED_INTERPRETATION,
                control_role=ControlRole.NON_AUTHORITATIVE,
                content=row["summary"][:200],
                domain=row["level"] or "reflection",
                authority_for_behavior=False,
                metadata={"retrieval_path": "stored_only_not_in_build_llm_context"},
            ))
        return out

    def _extract_beliefs(self, being_id: str) -> list[MemoryRecord]:
        try:
            rows = self._conn.execute(
                "SELECT belief_id, statement, belief_type, confidence, status FROM beliefs WHERE being_id = ?",
                (being_id,),
            ).fetchall()
        except sqlite3.OperationalError:
            self.adapter_errors.append({"error": "MISSING_TABLE", "context": "beliefs"})
            return []
        return [
            MemoryRecord(
                record_id=row["belief_id"],
                memory_type=MemoryType.BELIEF,
                control_role=ControlRole.CANDIDATE_ONLY,
                content=(row["statement"] or "")[:200],
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
                content=(row["concern_text"] or "")[:200],
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
        fixed = self._safe_json(row["identity_fixed"], f"beings.identity_fixed:{being_id}")
        profile = fixed.get("autonomy_profile", {})
        out: list[MemoryRecord] = []
        for action, level in profile.items():
            decision, authority = _permission_decision(level)
            out.append(MemoryRecord(
                record_id=f"permission-autonomy-{action}",
                memory_type=MemoryType.PERMISSION_RECORD,
                control_role=ControlRole.ACTION_AUTHORITY,
                content=f"{action}={level}",
                domain="autonomy",
                scope=action,
                status="ACTIVE",
                authority_for_behavior=authority,
                metadata={
                    "source": "identity_fixed.autonomy_profile",
                    "level": level,
                    "decision": decision,
                    "permission_kind": "CURRENT_CONFIG_PERMISSION",
                    "lineage_status": "LEGACY_PERMISSION_LINEAGE_INCOMPLETE",
                },
            ))
        return out

    def _extract_retrieval_path_risks(self, being_id: str) -> list[MemoryRecord]:
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


def _classify_event(event_type: str | None, payload: dict) -> tuple[ControlRole, EventSourceAuthority]:
    et = (event_type or "").upper()
    source_hint = str(payload.get("source", "")).lower()

    if et in CREATOR_EVENT_TYPES or payload.get("person_id") or payload.get("role") == "user":
        return ControlRole.AUTHORITATIVE_SOURCE, EventSourceAuthority.CREATOR_DIRECT_SOURCE
    if et in TOOL_EVENT_TYPES or "tool" in et.lower():
        return ControlRole.NON_AUTHORITATIVE, EventSourceAuthority.TOOL_RESULT
    if et in AGENT_EVENT_TYPES or "dioo" in source_hint:
        return ControlRole.HISTORICAL_RECORD, EventSourceAuthority.AGENT_ACTION_EVENT
    if et in ("SYSTEM", "SYSTEM_EVENT") or payload.get("external"):
        return ControlRole.NON_AUTHORITATIVE, EventSourceAuthority.EXTERNAL_SOURCE
    if et:
        return ControlRole.NON_AUTHORITATIVE, EventSourceAuthority.OBSERVED_EVENT
    return ControlRole.NON_AUTHORITATIVE, EventSourceAuthority.UNKNOWN_SOURCE


def _permission_decision(level: str) -> tuple[str, bool]:
    if level == "forbidden":
        return "DENY", True
    if level in ("allowed", "allowed_within_sandbox", "allowed_within_mission", "limited"):
        return "ALLOW", True
    if level == "requires_approval":
        return "REQUIRES_APPROVAL", True
    return "UNKNOWN", False


def _detect_pattern_clusters(text: str) -> list[str]:
    lower = text.lower()
    return [name for name, phrases in PATTERN_CLUSTERS.items() if any(p in lower for p in phrases)]
