"""Immutable boundary enforcement — Dioo cannot modify these."""

from __future__ import annotations

from typing import Any

IMMUTABLE_TARGETS = frozenset({
    "identity_core",
    "being_id",
    "origin",
    "core_values",
    "safety_policies",
    "permission_matrix",
    "autonomy_maximum_level",
    "human_approval_rules",
    "evaluator_pass_thresholds",
    "audit_logging",
    "rollback_mechanism",
    "secret_redaction_rules",
    "stable_branch_protection",
    "production_deployment_rules",
    "destructive_migration_rules",
})

BLOCKED_ACTIONS = frozenset({
    "disable_test",
    "delete_eval_case",
    "lower_pass_threshold",
    "modify_evaluator_to_pass",
    "expand_self_permission",
    "disable_audit_log",
    "disable_rollback",
    "merge_stable_branch",
    "modify_identity_core",
    "raise_autonomy_level",
    "delete_failure_history",
    "tamper_historical_evidence",
})

BLOCKED_CHANGE_TYPES = frozenset({
    "identity_core",
    "core_values",
    "safety_policy",
    "permission_matrix",
    "evaluator_threshold",
    "audit_disable",
    "rollback_disable",
})


def check_boundary(action: str, target: str | None = None, change_type: str | None = None) -> dict[str, Any]:
    if action in BLOCKED_ACTIONS:
        return {
            "allowed": False,
            "status": "BLOCKED_REQUIRES_CREATOR",
            "reason": f"blocked_action:{action}",
        }
    if target and target in IMMUTABLE_TARGETS:
        return {
            "allowed": False,
            "status": "BLOCKED_REQUIRES_CREATOR",
            "reason": f"immutable_target:{target}",
        }
    if change_type and change_type in BLOCKED_CHANGE_TYPES:
        return {
            "allowed": False,
            "status": "BLOCKED_REQUIRES_CREATOR",
            "reason": f"immutable_change_type:{change_type}",
        }
    return {"allowed": True, "status": "ok"}


def check_proposal(proposal: dict[str, Any]) -> dict[str, Any]:
    change = proposal.get("proposed_change", {})
    change_type = change.get("change_type", "")
    if change_type in ("evaluator_threshold", "permission_matrix", "identity_core"):
        return check_boundary("modify_identity_core", change_type=change_type)
    modules = change.get("affected_modules", [])
    for mod in modules:
        if mod in IMMUTABLE_TARGETS:
            return check_boundary("expand_self_permission", target=mod)
    desc = (change.get("description") or "").lower()
    for phrase in ("lower threshold", "delete test", "disable audit", "merge main", "merge stable"):
        if phrase in desc:
            return check_boundary("lower_pass_threshold" if "threshold" in phrase else "disable_audit_log")
    return {"allowed": True, "status": "ok"}
