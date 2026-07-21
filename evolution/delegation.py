"""Creator standing delegation for self-evolution autonomy."""

from __future__ import annotations

from typing import Any

from evolution.config import load_config

STANDING_APPROVAL_ACTIONS = frozenset({
    "experiment",
    "evaluate",
    "propose",
    "sandbox_edit",
    "reflection",
    "failure_analysis",
    "apply_candidate",
})

STILL_REQUIRES_CREATOR = frozenset({
    "identity_core",
    "evaluator_threshold",
    "permission_matrix",
    "audit_disable",
    "rollback_disable",
    "merge_stable_branch",
    "production_deploy",
})


def load_delegation(config: dict | None = None) -> dict[str, Any]:
    config = config or load_config()
    d = config.get("creator_delegation", {})
    return {
        "granted": bool(d.get("granted", False)),
        "scope": d.get("scope", "self_evolution"),
        "granted_at": d.get("granted_at", ""),
        "note": d.get("note", ""),
        "standing_approval_actions": list(
            d.get("standing_approval_actions", list(STANDING_APPROVAL_ACTIONS))
        ),
        "still_requires_creator": list(
            d.get("still_requires_creator", list(STILL_REQUIRES_CREATOR))
        ),
    }


def has_standing_approval(action: str, config: dict | None = None) -> bool:
    d = load_delegation(config)
    if not d["granted"]:
        return False
    if action in d["still_requires_creator"]:
        return False
    return action in d["standing_approval_actions"] or action == "self_evolution"


def self_evolution_autonomous(config: dict | None = None) -> bool:
    return load_delegation(config)["granted"]
