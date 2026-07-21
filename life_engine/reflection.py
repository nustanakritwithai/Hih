"""Session reflection — source of beliefs, self-memory, and concerns."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from life_engine.beliefs import (
    add_belief,
    add_evidence,
    find_belief_by_statement,
    promote_or_update_belief,
)
from life_engine.util import new_id, now_iso


def _recent_events(conn: sqlite3.Connection, being_id: str, limit: int = 10) -> list[dict]:
    rows = conn.execute(
        """
        SELECT event_id, event_type, timestamp, payload
        FROM events WHERE being_id = ?
        ORDER BY timestamp DESC LIMIT ?
        """,
        (being_id, limit),
    ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["payload"] = json.loads(d["payload"])
        out.append(d)
    return out


def build_session_reflection_data(
    being_id: str,
    conn: sqlite3.Connection,
    session_summary: str | None = None,
) -> dict[str, Any]:
    events = _recent_events(conn, being_id)
    texts = []
    for e in events:
        if e["event_type"] == "USER_MESSAGE":
            texts.append(e["payload"].get("text", ""))

    if not session_summary:
        session_summary = (
            "พัฒนา Life Engine MVP, เปิด autonomy mode, และรับ feedback สถาปัตยกรรม Level 2.5"
            if texts
            else "session ว่าง"
        )

    what_learned = []
    self_observations = []
    belief_candidates = []
    next_concerns = []

    joined = " ".join(texts).lower()
    if "อิสระ" in joined or "autonomy" in joined or "พัฒนาตัวเอง" in joined:
        what_learned.append("ผู้สร้างไม่ต้องการให้รายงานทุกการเคลื่อนไหว")
        what_learned.append("self-development เป็นเป้าหมายหลักในระยะนี้")
        belief_candidates.append({
            "statement": "การพัฒนาอย่างเงียบและรายงานเฉพาะสาระสำคัญเหมาะกับความสัมพันธ์นี้",
            "type": "relational",
            "confidence": 0.62,
        })
    if "belief" in joined or "reflection" in joined or "level 2" in joined:
        self_observations.append("ฉันยังไม่มีระบบประเมินความเชื่อที่สมบูรณ์ — กำลังสร้าง")
        next_concerns.append("เชื่อม reflection → belief → self-memory")
    if "focus" in joined or "transition" in joined:
        next_concerns.append("กำหนดกฎเปลี่ยน internal state ให้ชัด")

    if not belief_candidates:
        belief_candidates.append({
            "statement": "การพัฒนา Life Engine ต้องมาก่อน personality simulation",
            "type": "self",
            "confidence": 0.58,
        })
    if not next_concerns:
        next_concerns.extend([
            "ออกแบบ belief schema",
            "สร้าง session reflection อัตโนมัติ",
        ])

    return {
        "session_summary": session_summary,
        "what_i_learned": what_learned,
        "self_observations": self_observations,
        "belief_candidates": belief_candidates,
        "next_concerns": next_concerns,
    }


def run_session_reflection(
    conn: sqlite3.Connection,
    being_id: str,
    summary: str | None = None,
) -> dict[str, Any]:
    ts = now_iso()
    data = build_session_reflection_data(being_id, conn, summary)
    reflection_id = new_id("ref")

    conn.execute(
        """
        INSERT INTO reflections (
            reflection_id, being_id, level, timestamp,
            lessons, belief_updates, self_updates,
            relationship_updates, pending_concerns, summary,
            structured_data
        ) VALUES (?, ?, 'session', ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            reflection_id,
            being_id,
            ts,
            json.dumps(data["what_i_learned"], ensure_ascii=False),
            json.dumps([], ensure_ascii=False),
            json.dumps(data["self_observations"], ensure_ascii=False),
            json.dumps([], ensure_ascii=False),
            json.dumps(data["next_concerns"], ensure_ascii=False),
            data["session_summary"],
            json.dumps(data, ensure_ascii=False),
        ),
    )

    belief_results = []
    for cand in data["belief_candidates"]:
        existing = find_belief_by_statement(conn, being_id, cand["statement"])
        if existing:
            bid = existing["belief_id"]
            add_evidence(conn, bid, None, reflection_id, cand["confidence"], "session reflection", ts)
            belief_results.append(promote_or_update_belief(conn, bid, ts))
        else:
            bid = new_id("belief")
            add_belief(
                conn, being_id, bid, cand["statement"],
                cand.get("type", "self"), cand["confidence"], "candidate", ts,
            )
            add_evidence(conn, bid, None, reflection_id, cand["confidence"], "initial candidate", ts)
            belief_results.append(promote_or_update_belief(conn, bid, ts))

    # Split self-memory: creator preference + self policy
    if any("ไม่ต้องการให้รายงาน" in w for w in data["what_i_learned"]):
        conn.execute(
            """
            INSERT INTO self_memories (
                being_id, memory_type, observation, structured_data,
                evidence_count, confidence, behavioral_adjustment,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                being_id,
                "creator_preference",
                "ผู้สร้างต้องการ brief updates ไม่ต้องการ attention ตลอดเวลา",
                json.dumps({
                    "prefers_brief_updates": True,
                    "does_not_want_constant_attention": True,
                }, ensure_ascii=False),
                1, 0.88, None, ts, ts,
            ),
        )
        conn.execute(
            """
            INSERT INTO self_memories (
                being_id, memory_type, observation, structured_data,
                evidence_count, confidence, behavioral_adjustment,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                being_id,
                "self_policy_learned",
                "รูปแบบการดำรงอยู่: quiet autonomy",
                json.dumps({
                    "autonomy_style": "quiet_autonomy",
                    "notification_threshold": "meaningful_change_only",
                }, ensure_ascii=False),
                1, 0.90,
                "แจ้งเฉพาะความคืบหน้าที่มีนัยสำคัญ",
                ts, ts,
            ),
        )

    concern_ids = []
    for text in data["next_concerns"]:
        cid = new_id("concern")
        conn.execute(
            """
            INSERT INTO concerns (
                concern_id, being_id, concern_text, urgency,
                related_beliefs, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, '[]', 'open', ?, ?)
            """,
            (cid, being_id, text, 0.65, ts, ts),
        )
        concern_ids.append(cid)

    return {
        "reflection_id": reflection_id,
        "structured": data,
        "beliefs": belief_results,
        "concerns_created": concern_ids,
    }
