"""Sanitized audit report — aggregates only, no raw memory content."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any


def build_sanitized_report(
    full_report: dict[str, Any],
    *,
    snapshot_info: dict[str, Any] | None = None,
    adapter_errors: list[dict] | None = None,
    comparison: dict[str, Any] | None = None,
    run_id: str | None = None,
    trigger_context: str | None = None,
) -> dict[str, Any]:
    """Produce aggregate-only report safe for external review."""
    metrics = full_report.get("metrics", {})
    classification = full_report.get("classification_findings", [])
    snap = snapshot_info or full_report.get("snapshot_info") or {}

    by_type = Counter(c.get("memory_type", "UNKNOWN") for c in classification)

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

    hash_before = snap.get("source_hash_before")
    hash_after = snap.get("source_hash_after")
    mtime_before = snap.get("source_mtime_before")
    mtime_after = snap.get("source_mtime_after")

    report: dict[str, Any] = {
        "mode": "SANITIZED_READ_ONLY_AUDIT",
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "records_scanned": full_report.get("records_scanned", 0),
        "records_by_type": dict(by_type),
        "lineage_status": metrics.get("lineage_status", "NOT_EVALUATED"),
        "lineage_edges_evaluated": metrics.get("lineage_edges_evaluated", 0),
        "derived_records_total": metrics.get("derived_records_total", 0),
        "derived_records_with_source_refs": metrics.get("derived_records_with_source_refs", 0),
        "derived_records_missing_source_refs": metrics.get("derived_records_missing_source_refs", 0),
        "lineage_coverage_rate": metrics.get("lineage_coverage_rate"),
        "lineage_coverage_by_type": metrics.get("lineage_coverage_by_type", {}),
        "orphan_source_reference_count": metrics.get("orphan_source_reference_count", 0),
        "lineage_resolution_rate": metrics.get("lineage_resolution_rate"),
        "unknown_lineage_rate": metrics.get("unknown_lineage_rate"),
        "main_db_file_hash_unchanged": (
            hash_before == hash_after if hash_before and hash_after else None
        ),
        "main_db_file_mtime_unchanged": (
            mtime_before == mtime_after if mtime_before is not None and mtime_after is not None else None
        ),
        "wal_present_before": snap.get("wal_present_before"),
        "wal_present_after": snap.get("wal_present_after"),
        "concurrent_write_status": snap.get("concurrent_write_status", "NOT_DETERMINED"),
        "summary_authority_rate": metrics.get("summary_authority_rate", 0),
        "permission_integrity_findings": permission_findings,
        "identity_findings": identity_findings,
        "runtime_only_patterns": runtime_patterns,
        "adapter_errors": adapter_errors or [],
        "snapshot_method": snap.get("method", "unknown"),
        "snapshot_cleaned": snap.get("cleanup_result", "pending"),
        "fixture_gap_analysis": (comparison or {}).get("fixture_gap_analysis", []),
        "mutations_performed": 0,
    }
    if run_id:
        report["run_id"] = run_id
    if trigger_context:
        report["trigger_context"] = trigger_context
    return report
