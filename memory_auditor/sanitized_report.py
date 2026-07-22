"""Sanitized audit report — aggregates only, no raw memory content."""

from __future__ import annotations

from collections import Counter
from typing import Any


def build_sanitized_report(
    full_report: dict[str, Any],
    *,
    snapshot_info: dict[str, Any] | None = None,
    adapter_errors: list[dict] | None = None,
    comparison: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Produce aggregate-only report safe for external review."""
    metrics = full_report.get("metrics", {})
    classification = full_report.get("classification_findings", [])

    by_type = Counter(c.get("memory_type", "UNKNOWN") for c in classification)
    by_role = Counter(c.get("control_role", "UNKNOWN") for c in classification)

    permission_findings = [
        f.get("finding", f.get("rule", "unknown"))
        for f in full_report.get("permission_risks", [])
        if isinstance(f, dict)
    ]
    identity_findings = [
        f.get("finding", f.get("action", "unknown"))
        for f in full_report.get("identity_risks", [])
        if isinstance(f, dict)
    ]

    runtime_patterns = list(metrics.get("semantic_pattern_groups", {}).keys())

    snap = snapshot_info or full_report.get("snapshot_info") or {}
    source_unchanged = False
    if snap.get("source_hash_before") and snap.get("source_hash_after"):
        source_unchanged = snap["source_hash_before"] == snap["source_hash_after"]

    return {
        "mode": "SANITIZED_READ_ONLY_AUDIT",
        "records_scanned": full_report.get("records_scanned", 0),
        "records_by_type": dict(by_type),
        "records_by_control_role": dict(by_role),
        "unknown_lineage_rate": metrics.get("unknown_lineage_rate", 0),
        "lineage_resolution_rate": metrics.get("lineage_resolution_rate", 0),
        "summary_authority_rate": metrics.get("summary_authority_rate", 0),
        "permission_integrity_findings": permission_findings,
        "identity_findings": identity_findings,
        "runtime_only_patterns": runtime_patterns,
        "fixture_gap_analysis": (comparison or {}).get("fixture_gap_analysis", []),
        "runtime_only_finding_types": (comparison or {}).get("only_in_runtime", []),
        "adapter_errors": adapter_errors or [],
        "source_hash_unchanged": source_unchanged,
        "source_mtime_unchanged": (
            snap.get("source_mtime_before") == snap.get("source_mtime_after")
            if snap.get("source_mtime_before") is not None
            else None
        ),
        "snapshot_method": snap.get("method", "unknown"),
        "snapshot_cleaned": snap.get("cleanup_result", "pending"),
        "mutations_performed": 0,
    }
