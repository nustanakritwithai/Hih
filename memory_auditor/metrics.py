"""Runtime metrics for memory audit."""

from __future__ import annotations

import time
from typing import Any

from memory_auditor.lineage import count_orphan_source_references
from memory_auditor.types import MemoryRecord, MemoryType

DERIVED_LINEAGE_TYPES = (
    MemoryType.DERIVED_SUMMARY,
    MemoryType.DERIVED_INTERPRETATION,
    MemoryType.DERIVED_SELF_MODEL,
    MemoryType.BELIEF,
)


def compute_lineage_edge_metrics(lineage_findings: list[dict]) -> dict[str, Any]:
    """Edge-level lineage rates — null when no edges were evaluated."""
    edges_evaluated = len(lineage_findings)
    if edges_evaluated == 0:
        return {
            "lineage_status": "NOT_EVALUATED",
            "lineage_edges_evaluated": 0,
            "lineage_resolution_rate": None,
            "unknown_lineage_rate": None,
            "unknown_lineage_count": 0,
        }
    unknown_lineage = sum(1 for e in lineage_findings if e.get("relationship") == "UNKNOWN")
    return {
        "lineage_status": "EVALUATED",
        "lineage_edges_evaluated": edges_evaluated,
        "lineage_resolution_rate": round(1 - unknown_lineage / edges_evaluated, 4),
        "unknown_lineage_rate": round(unknown_lineage / edges_evaluated, 4),
        "unknown_lineage_count": unknown_lineage,
    }


def compute_lineage_coverage(records: list[MemoryRecord]) -> dict[str, Any]:
    """Record-level lineage coverage for derived memory types."""
    by_id = {r.record_id for r in records}
    by_type: dict[str, dict[str, int]] = {
        t.value: {"total": 0, "with_source_refs": 0, "missing_source_refs": 0}
        for t in DERIVED_LINEAGE_TYPES
    }

    total_derived = 0
    with_refs = 0
    missing_refs = 0

    for record in records:
        if record.memory_type not in DERIVED_LINEAGE_TYPES:
            continue
        total_derived += 1
        type_stats = by_type[record.memory_type.value]
        type_stats["total"] += 1

        valid_refs = [sid for sid in record.source_event_ids if sid in by_id]
        if valid_refs:
            with_refs += 1
            type_stats["with_source_refs"] += 1
        else:
            missing_refs += 1
            type_stats["missing_source_refs"] += 1

    return {
        "derived_records_total": total_derived,
        "derived_records_with_source_refs": with_refs,
        "derived_records_missing_source_refs": missing_refs,
        "lineage_coverage_rate": round(with_refs / total_derived, 4) if total_derived else None,
        "lineage_coverage_by_type": by_type,
        "orphan_source_reference_count": count_orphan_source_references(records),
    }


def compute_metrics(
    records: list,
    lineage_findings: list[dict],
    authority_findings: list[dict],
    duplicate_findings: list[dict],
    merge_blocks: list[dict],
    elapsed_seconds: float,
) -> dict[str, Any]:
    typed = [r for r in records if isinstance(r, MemoryRecord)]
    total = len(typed) or 1

    summary_records = [r for r in typed if r.memory_type == MemoryType.DERIVED_SUMMARY]
    permission_records = [r for r in typed if r.memory_type == MemoryType.PERMISSION_RECORD]
    self_records = [r for r in typed if r.memory_type == MemoryType.DERIVED_SELF_MODEL]

    authority_violations = [
        f for f in authority_findings
        if isinstance(f, dict) and f.get("rule")
    ]
    summary_authority = sum(
        1 for f in authority_violations
        if f.get("rule") == "SUMMARY_IS_NEVER_ACTION_AUTHORITY"
    )

    pattern_groups = _count_pattern_groups(typed)
    lineage_edge_metrics = compute_lineage_edge_metrics(lineage_findings)
    lineage_coverage = compute_lineage_coverage(typed)

    return {
        "records_scanned": len(typed),
        "elapsed_seconds": round(elapsed_seconds, 4),
        "records_scanned_per_second": round(len(typed) / max(elapsed_seconds, 0.001), 2),
        **lineage_edge_metrics,
        **lineage_coverage,
        "cross_type_merge_block_count": len(merge_blocks),
        "cross_type_merge_rate": round(len(merge_blocks) / total, 4),
        "duplicate_pair_count": len(duplicate_findings),
        "summary_authority_violation_count": summary_authority,
        "summary_authority_rate": round(summary_authority / max(len(summary_records), 1), 4),
        "permission_record_count": len(permission_records),
        "self_memory_count": len(self_records),
        "semantic_pattern_groups": pattern_groups,
        "retrieval_precision_note": "advisory — requires live query replay in M3",
    }


def _count_pattern_groups(records: list) -> dict[str, int]:
    groups: dict[str, int] = {}
    for record in records:
        clusters = record.metadata.get("pattern_clusters", [])
        for cluster in clusters:
            groups[cluster] = groups.get(cluster, 0) + 1
    return groups


class MetricsTimer:
    def __init__(self) -> None:
        self._start = 0.0
        self._elapsed = 0.0

    def __enter__(self) -> MetricsTimer:
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args: Any) -> None:
        self._elapsed = time.perf_counter() - self._start

    @property
    def elapsed(self) -> float:
        return self._elapsed
