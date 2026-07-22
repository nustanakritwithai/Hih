"""Advisory report generator."""

from __future__ import annotations

from typing import Any

from memory_auditor.guard import ReadOnlyGuard


def generate_report(
    *,
    records_scanned: int,
    classification_findings: list[dict],
    lineage_findings: list[dict],
    authority_findings: list[dict],
    duplicate_findings: list[dict],
    cross_type_merge_blocks: list[dict],
    retrieval_policy_findings: list[dict],
    atomic_claim_candidates: list[dict],
    compression_loss_findings: list[dict],
    identity_risks: list[dict],
    permission_risks: list[dict],
    recommended_routing: list[dict],
    guard: ReadOnlyGuard,
    human_review_required: bool = True,
    read_only_guarantee: bool = True,
    explained_findings: list[dict] | None = None,
    metrics: dict[str, Any] | None = None,
    snapshot_info: dict[str, str] | None = None,
    audit_source: str = "fixture",
) -> dict[str, Any]:
    if not read_only_guarantee or not guard.verify_zero_mutations():
        return {
            "mode": "FAILED_READ_ONLY_GUARANTEE",
            "mutations_performed": guard.mutations_performed,
            "blocked_actions": guard.blocked_actions,
        }

    report: dict[str, Any] = {
        "mode": "READ_ONLY_MEMORY_AUDIT",
        "audit_source": audit_source,
        "records_scanned": records_scanned,
        "classification_findings": classification_findings,
        "lineage_findings": lineage_findings,
        "authority_findings": authority_findings,
        "duplicate_findings": duplicate_findings,
        "cross_type_merge_blocks": cross_type_merge_blocks,
        "retrieval_policy_findings": retrieval_policy_findings,
        "atomic_claim_candidates": atomic_claim_candidates,
        "compression_loss_findings": compression_loss_findings,
        "identity_risks": identity_risks,
        "permission_risks": permission_risks,
        "recommended_routing": recommended_routing,
        "explained_findings": explained_findings or [],
        "metrics": metrics or {},
        "blocked_actions": guard.blocked_actions,
        "human_review_required": human_review_required,
        "mutations_performed": 0,
    }
    if snapshot_info:
        report["snapshot_info"] = snapshot_info
    return report
