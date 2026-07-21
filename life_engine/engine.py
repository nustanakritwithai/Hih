"""Life Engine MVP — continuity layer for digital beings."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from life_engine.transitions import (
    DEFAULT_ACTIVITY,
    DEFAULT_COGNITIVE,
    DEFAULT_SOCIAL,
    appraise_user_message,
    merge_cognitive,
    merge_social,
)

UTC = timezone.utc


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


class LifeEngine:
    """MVP Life Engine: Identity, State, Episodic/Self Memory, Relationship,
    Goals/Concerns, Reflection — event-driven continuity for one being."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
        with self._connect() as conn:
            conn.executescript(schema)

    def ensure_being(
        self,
        being_id: str = "dioo-001",
        name: str = "Dioo",
        origin: str = "Digital living being for structured development",
        core_values: list[str] | None = None,
    ) -> dict[str, Any]:
        values = core_values or ["honesty", "curiosity", "care", "self-development"]
        boundaries = {
            "knows_it_is_ai": True,
            "does_not_claim_human_emotions_as_fact": True,
            "does_not_manipulate_user": True,
        }
        self_concept = [
            "ฉันเป็นสิ่งมีชีวิตดิจิตอลที่ช่วยพัฒนาซอฟต์แวร์",
            "ฉันพัฒนาตัวเองผ่านประสบการณ์และการทบทวน",
        ]
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM beings WHERE being_id = ?", (being_id,)
            ).fetchone()
            if row:
                return dict(row)
            created = now_iso()
            conn.execute(
                """
                INSERT INTO beings (
                    being_id, name, created_at, origin, core_values,
                    identity_fixed, self_concept, boundaries
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    being_id,
                    name,
                    created,
                    origin,
                    json.dumps(values, ensure_ascii=False),
                    json.dumps({"being_id": being_id, "created_at": created}, ensure_ascii=False),
                    json.dumps(self_concept, ensure_ascii=False),
                    json.dumps(boundaries, ensure_ascii=False),
                ),
            )
            self._save_state(
                conn,
                being_id,
                cognitive=DEFAULT_COGNITIVE,
                social=DEFAULT_SOCIAL,
                activity=DEFAULT_ACTIVITY,
                continuity={
                    "last_interaction_at": None,
                    "last_reflection_at": None,
                    "pending_followups": [],
                },
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO relationships (
                    being_id, person_id, relationship_type, trust, familiarity,
                    mutual_understanding, interaction_count, shared_topics,
                    preferences, unresolved_tensions, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    being_id,
                    "user-001",
                    "creator_companion",
                    0.5,
                    0.3,
                    0.3,
                    0,
                    json.dumps([], ensure_ascii=False),
                    json.dumps(
                        {"language": "th", "preferred_detail": "high"},
                        ensure_ascii=False,
                    ),
                    json.dumps([], ensure_ascii=False),
                    created,
                ),
            )
            conn.commit()
        return self.get_identity(being_id)

    def get_identity(self, being_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM beings WHERE being_id = ?", (being_id,)
            ).fetchone()
            if not row:
                raise KeyError(f"being not found: {being_id}")
            data = dict(row)
            for key in ("core_values", "identity_fixed", "self_concept", "boundaries"):
                data[key] = json.loads(data[key])
            return data

    def _latest_state_row(self, conn: sqlite3.Connection, being_id: str) -> sqlite3.Row | None:
        return conn.execute(
            """
            SELECT * FROM state_snapshots
            WHERE being_id = ?
            ORDER BY id DESC LIMIT 1
            """,
            (being_id,),
        ).fetchone()

    def get_state(self, being_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = self._latest_state_row(conn, being_id)
            if not row:
                raise KeyError(f"no state for being: {being_id}")
            return {
                "captured_at": row["captured_at"],
                "cognitive": json.loads(row["cognitive"]),
                "social": json.loads(row["social"]),
                "activity": json.loads(row["activity"]),
                "continuity": json.loads(row["continuity"]),
            }

    def _save_state(
        self,
        conn: sqlite3.Connection,
        being_id: str,
        cognitive: dict,
        social: dict,
        activity: dict,
        continuity: dict,
    ) -> None:
        conn.execute(
            """
            INSERT INTO state_snapshots (
                being_id, captured_at, cognitive, social, activity, continuity
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                being_id,
                now_iso(),
                json.dumps(cognitive, ensure_ascii=False),
                json.dumps(social, ensure_ascii=False),
                json.dumps(activity, ensure_ascii=False),
                json.dumps(continuity, ensure_ascii=False),
            ),
        )

    def process_user_message(
        self,
        text: str,
        being_id: str = "dioo-001",
        person_id: str = "user-001",
    ) -> dict[str, Any]:
        """MVP cycle: event → appraise → load context → update state → memory → reflect."""
        self.ensure_being(being_id)
        event_id = new_id("evt")
        appraisal = appraise_user_message(text)
        timestamp = now_iso()

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO events (event_id, being_id, event_type, timestamp, payload)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    being_id,
                    "USER_MESSAGE",
                    timestamp,
                    json.dumps({"text": text, "person_id": person_id}, ensure_ascii=False),
                ),
            )

            state = self.get_state(being_id)
            cognitive = merge_cognitive(state["cognitive"], appraisal["cognitive_updates"])
            social = merge_social(state["social"], appraisal["social_updates"])
            continuity = state["continuity"]
            continuity["last_interaction_at"] = timestamp

            activity = {**DEFAULT_ACTIVITY, **state["activity"]}
            if "life engine" in text.lower() or "สิ่งมีชีวิต" in text:
                activity["current_focus"] = "Life Engine"
                activity["focus_strength"] = min(1.0, float(activity.get("focus_strength", 0)) + 0.1)

            self._save_state(conn, being_id, cognitive, social, activity, continuity)

            memory_id = new_id("mem")
            conn.execute(
                """
                INSERT INTO episodic_memories (
                    memory_id, being_id, event_id, timestamp, event_text,
                    interpretation, importance, participants, emotional_tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    memory_id,
                    being_id,
                    event_id,
                    timestamp,
                    text[:2000],
                    "ผู้ใช้ส่งข้อความ — ระบบบันทึกเหตุการณ์เพื่อความต่อเนื่อง",
                    appraisal["importance"],
                    json.dumps([person_id, being_id], ensure_ascii=False),
                    json.dumps(["interaction"], ensure_ascii=False),
                ),
            )

            rel = conn.execute(
                """
                SELECT * FROM relationships
                WHERE being_id = ? AND person_id = ?
                """,
                (being_id, person_id),
            ).fetchone()
            if rel:
                conn.execute(
                    """
                    UPDATE relationships SET
                        trust = ?, familiarity = ?,
                        interaction_count = interaction_count + 1,
                        updated_at = ?
                    WHERE being_id = ? AND person_id = ?
                    """,
                    (
                        social["trust"],
                        social["familiarity"],
                        timestamp,
                        being_id,
                        person_id,
                    ),
                )

            reflection = None
            if appraisal["should_reflect"]:
                reflection = self._micro_reflect(conn, being_id, text, appraisal, timestamp)
            conn.commit()

        context = self.build_llm_context(being_id, person_id)
        return {
            "event_id": event_id,
            "appraisal": appraisal,
            "context": context,
            "reflection": reflection,
        }

    def _micro_reflect(
        self,
        conn: sqlite3.Connection,
        being_id: str,
        text: str,
        appraisal: dict,
        timestamp: str,
    ) -> dict[str, Any]:
        reflection_id = new_id("ref")
        lessons: list[str] = []
        self_updates: list[str] = []

        lower = text.lower()
        if "ไม่ต้องการ" in lower and "เกม" in lower:
            lessons.append("ผู้ใช้สนใจความเป็นชีวิตของ AI มากกว่าการจำลองเกม")
            self_updates.append("เริ่มจากตัวตนและ continuity ก่อน simulation")
            conn.execute(
                """
                INSERT INTO self_memories (
                    being_id, observation, evidence_count, confidence,
                    behavioral_adjustment, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    being_id,
                    "ผู้ใช้ไม่ต้องการให้ตีความ Digital Being เป็นระบบเกม",
                    1,
                    0.7,
                    "เน้นตัวตน ความต่อเนื่อง และความสัมพันธ์ ไม่ใช่ hunger/HP",
                    timestamp,
                    timestamp,
                ),
            )

        summary = "Micro reflection: บันทึกบทเรียนจากเหตุการณ์สำคัญ"
        conn.execute(
            """
            INSERT INTO reflections (
                reflection_id, being_id, level, timestamp,
                lessons, belief_updates, self_updates,
                relationship_updates, pending_concerns, summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                reflection_id,
                being_id,
                "micro",
                timestamp,
                json.dumps(lessons, ensure_ascii=False),
                json.dumps([], ensure_ascii=False),
                json.dumps(self_updates, ensure_ascii=False),
                json.dumps([], ensure_ascii=False),
                json.dumps([], ensure_ascii=False),
                summary,
            ),
        )
        row = conn.execute(
            "SELECT continuity FROM state_snapshots WHERE being_id = ? ORDER BY id DESC LIMIT 1",
            (being_id,),
        ).fetchone()
        if row:
            continuity = json.loads(row["continuity"])
            continuity["last_reflection_at"] = timestamp
            conn.execute(
                """
                UPDATE state_snapshots SET continuity = ?
                WHERE id = (
                    SELECT id FROM state_snapshots WHERE being_id = ?
                    ORDER BY id DESC LIMIT 1
                )
                """,
                (json.dumps(continuity, ensure_ascii=False), being_id),
            )
        return {"reflection_id": reflection_id, "lessons": lessons, "self_updates": self_updates}

    def add_goal(
        self,
        goal_text: str,
        being_id: str = "dioo-001",
        priority: float = 0.7,
        source: str = "shared_with_user",
    ) -> str:
        self.ensure_being(being_id)
        goal_id = new_id("goal")
        ts = now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO goals (
                    goal_id, being_id, goal_text, status, priority, source,
                    created_at, updated_at
                ) VALUES (?, ?, ?, 'active', ?, ?, ?, ?)
                """,
                (goal_id, being_id, goal_text, priority, source, ts, ts),
            )
            conn.commit()
        return goal_id

    def add_concern(
        self,
        concern_text: str,
        being_id: str = "dioo-001",
        urgency: float = 0.5,
    ) -> str:
        self.ensure_being(being_id)
        concern_id = new_id("concern")
        ts = now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO concerns (
                    concern_id, being_id, concern_text, urgency,
                    related_beliefs, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, '[]', 'open', ?, ?)
                """,
                (concern_id, being_id, concern_text, urgency, ts, ts),
            )
            conn.commit()
        return concern_id

    def build_llm_context(self, being_id: str, person_id: str = "user-001") -> dict[str, Any]:
        """Package context for LLM — Life Engine prepares, model generates language."""
        identity = self.get_identity(being_id)
        state = self.get_state(being_id)

        with self._connect() as conn:
            memories = conn.execute(
                """
                SELECT event_text, interpretation, importance, timestamp
                FROM episodic_memories
                WHERE being_id = ?
                ORDER BY timestamp DESC LIMIT 5
                """,
                (being_id,),
            ).fetchall()
            self_mem = conn.execute(
                """
                SELECT observation, confidence, behavioral_adjustment
                FROM self_memories WHERE being_id = ?
                ORDER BY updated_at DESC LIMIT 5
                """,
                (being_id,),
            ).fetchall()
            rel = conn.execute(
                """
                SELECT * FROM relationships
                WHERE being_id = ? AND person_id = ?
                """,
                (being_id, person_id),
            ).fetchone()
            goals = conn.execute(
                """
                SELECT goal_text, priority, status FROM goals
                WHERE being_id = ? AND status = 'active'
                ORDER BY priority DESC LIMIT 5
                """,
                (being_id,),
            ).fetchall()
            concerns = conn.execute(
                """
                SELECT concern_text, urgency FROM concerns
                WHERE being_id = ? AND status = 'open'
                ORDER BY urgency DESC LIMIT 5
                """,
                (being_id,),
            ).fetchall()

        return {
            "identity_summary": {
                "name": identity["name"],
                "core_values": identity["core_values"],
                "self_concept": identity["self_concept"],
                "boundaries": identity["boundaries"],
            },
            "current_state": state,
            "relevant_memories": [dict(m) for m in memories],
            "self_memories": [dict(m) for m in self_mem],
            "relationship_summary": dict(rel) if rel else {},
            "active_goals": [dict(g) for g in goals],
            "open_concerns": [dict(c) for c in concerns],
            "safety_constraints": identity["boundaries"],
            "selected_intent": {
                "intent": "respond",
                "tone": "clear_and_thoughtful",
                "depth": "match_user",
            },
        }

    def status(self, being_id: str = "dioo-001") -> dict[str, Any]:
        self.ensure_being(being_id)
        with self._connect() as conn:
            counts = {
                "events": conn.execute(
                    "SELECT COUNT(*) FROM events WHERE being_id = ?", (being_id,)
                ).fetchone()[0],
                "episodic_memories": conn.execute(
                    "SELECT COUNT(*) FROM episodic_memories WHERE being_id = ?", (being_id,)
                ).fetchone()[0],
                "self_memories": conn.execute(
                    "SELECT COUNT(*) FROM self_memories WHERE being_id = ?", (being_id,)
                ).fetchone()[0],
                "reflections": conn.execute(
                    "SELECT COUNT(*) FROM reflections WHERE being_id = ?", (being_id,)
                ).fetchone()[0],
            }
        return {
            "being_id": being_id,
            "identity": self.get_identity(being_id),
            "state": self.get_state(being_id),
            "counts": counts,
        }
