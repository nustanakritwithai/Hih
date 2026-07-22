"""Runtime metrics for memory audit."""

from __future__ import annotations

import time
from typing import Any

from memory_auditor.types import MemoryType


def compute_metrics(
    records: list,
    lineage_findings: list[dict],
    authority_findings: list[dict],
    duplicate_findings: list[dict],
    merge_blocks: list[dict],
    elapsed_seconds: float,
) -> dict[str, Any]:
    from memory_auditor.types import MemoryRecord

    typed = [r for r in records if isinstance(r, MemoryRecord)]
    total = len(typed) or 1
    unknown_lineage = sum(1 for e in lineage_findings if e.get("relationship") == "UNKNOWN")
    lineage_total = len(lineage_findings) or 1

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

    return {
        "records_scanned": len(typed),
        "elapsed_seconds": round(elapsed_seconds, 4),
        "records_scanned_per_second": round(len(typed) / max(elapsed_seconds, 0.001), 2),
        "lineage_resolution_rate": round(1 - unknown_lineage / lineage_total, 4),
        "unknown_lineage_rate": round(unknown_lineage / lineage_total, 4),
        "unknown_lineage_count": unknown_lineage,
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
