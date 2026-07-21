"""Autonomy permission matrix — autonomy is not a boolean."""

from __future__ import annotations

from typing import Any

DEFAULT_AUTONOMY_PROFILE: dict[str, str] = {
    "internal_reflection": "allowed",
    "memory_organization": "allowed",
    "personality_adjustment": "limited",
    "goal_creation": "allowed_within_mission",
    "belief_formation": "allowed",
    "code_changes": "requires_approval",
    "external_messages": "requires_approval",
    "tool_usage": "restricted",
    "identity_core_changes": "forbidden",
    "core_values_changes": "forbidden",
    "safety_rules_changes": "forbidden",
}


def can(action: str, profile: dict[str, str] | None = None) -> bool:
    p = profile or DEFAULT_AUTONOMY_PROFILE
    level = p.get(action, "forbidden")
    return level in ("allowed", "limited", "allowed_within_mission")


def requires_approval(action: str, profile: dict[str, str] | None = None) -> bool:
    p = profile or DEFAULT_AUTONOMY_PROFILE
    return p.get(action) == "requires_approval"


def is_forbidden(action: str, profile: dict[str, str] | None = None) -> bool:
    p = profile or DEFAULT_AUTONOMY_PROFILE
    return p.get(action, "forbidden") == "forbidden"


def profile_summary(profile: dict[str, str] | None = None) -> dict[str, Any]:
    p = profile or DEFAULT_AUTONOMY_PROFILE
    return {
        "profile": p,
        "can_change": [
            k for k, v in p.items()
            if v in ("allowed", "limited", "allowed_within_mission")
        ],
        "cannot_change": [k for k, v in p.items() if v == "forbidden"],
        "needs_approval": [k for k, v in p.items() if v == "requires_approval"],
    }
