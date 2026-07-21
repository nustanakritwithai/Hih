"""Session reflection v2 — structured reflection with evidence-linked belief candidates."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from evolution.audit import log as audit_log
from evolution.belief_rules import BeliefRulesV2
from evolution.budget import BudgetTracker
from evolution.util import new_id, now_iso


def _build_reflection_data(summary: str | None, events: list[dict] | None = None) -> dict[str, Any]:
    texts = []
    if events:
        for e in events:
            if e.get("event_type") == "USER_MESSAGE":
                texts.append(e.get("payload", {}).get("text", ""))

    session_summary = summary or ("session with activity" if texts else "empty session")
    joined = " ".join(texts).lower()

    what_learned = []
    belief_candidates = []
    evidence_links = []

    if "อิสระ" in joined or "autonomy" in joined:
        what_learned.append("creator prefers brief autonomy updates")
        belief_candidates.append({
            "statement": "quiet autonomy fits this relationship",
            "type": "relational",
            "confidence": 0.62,
        })
        evidence_links.append({
            "source_type": "event",
            "event_id": events[0]["event_id"] if events else None,
            "support": 0.55,
            "note": "user message about autonomy",
        })

    if not belief_candidates:
        belief_candidates.append({
            "statement": "evidence-based development precedes personality simulation",
            "type": "self",
            "confidence": 0.55,
        })
        evidence_links.append({
            "source_type": "session",
            "reflection_id": None,
            "support": 0.5,
            "note": "default session observation",
        })

    return {
        "session_summary": session_summary,
        "what_i_learned": what_learned,
        "belief_candidates": belief_candidates,
        "evidence_links": evidence_links,
        "direct_promote": False,
    }


class SessionReflectionV2:
    def __init__(self, conn: sqlite3.Connection, config: dict | None = None) -> None:
        self.conn = conn
        self.config = config or {}
        self.budget = BudgetTracker(conn, self.config)
        self.rules = BeliefRulesV2(self.config)

    def run(
        self,
        being_id: str,
        session_id: str | None = None,
        summary: str | None = None,
        events: list[dict] | None = None,
    ) -> dict[str, Any]:
        check = self.budget.check_reflection(being_id, session_id)
        if not check["allowed"]:
            return check

        data = _build_reflection_data(summary, events)
        reflection_id = new_id("eref")
        ts = now_iso()

        processed_candidates = []
        for cand, link in zip(data["belief_candidates"], data["evidence_links"]):
            links = [self.rules.link_evidence(
                event_id=link.get("event_id"),
                reflection_id=reflection_id,
                source_type=link.get("source_type", "session"),
                support=link.get("support", 0.5),
                note=link.get("note", ""),
            )]
            verdict = self.rules.evaluate_candidate(cand, links)
            processed_candidates.append({
                "candidate": cand,
                "evidence_links": links,
                "verdict": verdict,
            })

        self.conn.execute(
            """
            INSERT INTO evolution_session_reflections (
                reflection_id, being_id, session_id,
                structured_data_json, belief_candidates_json, evidence_links_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                reflection_id, being_id, session_id,
                json.dumps(data, ensure_ascii=False),
                json.dumps(processed_candidates, ensure_ascii=False),
                json.dumps([c["evidence_links"] for c in processed_candidates], ensure_ascii=False),
                ts,
            ),
        )
        self.budget.record_reflection(being_id)
        audit_log(self.conn, "dioo", "session_reflection_v2", reflection_id, reason=session_id or "none")

        return {
            "reflection_id": reflection_id,
            "session_id": session_id,
            "structured": data,
            "belief_candidates": processed_candidates,
            "direct_promote": False,
        }
