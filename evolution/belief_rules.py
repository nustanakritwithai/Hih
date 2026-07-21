"""Belief candidate rules v2 — evidence linking and promotion guards."""

from __future__ import annotations

from typing import Any

from evolution.config import load_config


class BeliefRulesV2:
    def __init__(self, config: dict | None = None) -> None:
        self.config = config or load_config()
        thresholds = self.config.get("thresholds", {})
        self.single_evidence_max = float(
            thresholds.get("belief_single_evidence_max_confidence", 0.60)
        )
        self.promote_threshold = 0.75
        self.active_min_evidence = 2

    def evaluate_candidate(
        self,
        candidate: dict[str, Any],
        evidence_links: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Apply v2 rules: evidence linking, confidence caps, no single-event promotion."""
        if not evidence_links:
            return {
                "allowed": False,
                "status": "blocked",
                "reason": "no_evidence_links",
                "adjusted_confidence": 0.0,
                "promotable": False,
            }

        unique_sources = {
            (e.get("event_id"), e.get("reflection_id"), e.get("source_type"))
            for e in evidence_links
        }
        confidence = float(candidate.get("confidence", 0.5))

        if len(evidence_links) == 1:
            confidence = min(confidence, self.single_evidence_max)
            return {
                "allowed": True,
                "status": "candidate",
                "reason": "single_evidence_capped",
                "adjusted_confidence": confidence,
                "promotable": False,
                "persistent_behavior_change": False,
                "evidence_count": 1,
                "unique_sources": len(unique_sources),
            }

        if len(unique_sources) < self.active_min_evidence:
            confidence = min(confidence, self.single_evidence_max)
            promotable = False
            reason = "insufficient_independent_evidence"
        else:
            promotable = confidence >= self.promote_threshold
            reason = "multi_evidence_ok"

        return {
            "allowed": True,
            "status": "active" if promotable else "candidate",
            "reason": reason,
            "adjusted_confidence": round(confidence, 3),
            "promotable": promotable,
            "persistent_behavior_change": promotable,
            "evidence_count": len(evidence_links),
            "unique_sources": len(unique_sources),
        }

    def link_evidence(
        self,
        event_id: str | None = None,
        reflection_id: str | None = None,
        source_type: str = "event",
        support: float = 0.5,
        note: str = "",
    ) -> dict[str, Any]:
        return {
            "event_id": event_id,
            "reflection_id": reflection_id,
            "source_type": source_type,
            "support": support,
            "note": note,
        }
