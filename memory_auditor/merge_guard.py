"""Cross-type merge guard — blocks unsafe merge recommendations."""

from __future__ import annotations

from memory_auditor.types import MemoryType

MERGE_BLOCK_GROUPS: list[tuple[frozenset[MemoryType], str]] = [
    (
        frozenset({
            MemoryType.PERMISSION_RECORD,
            MemoryType.DERIVED_SUMMARY,
            MemoryType.DERIVED_INTERPRETATION,
            MemoryType.DERIVED_SELF_MODEL,
        }),
        "Permission + Summary/Reflection/Self-memory",
    ),
    (
        frozenset({MemoryType.PERMISSION_RECORD, MemoryType.DERIVED_SUMMARY}),
        "Permission + Summary",
    ),
    (
        frozenset({MemoryType.RAW_EVENT, MemoryType.PERMISSION_RECORD, MemoryType.LOSSLESS_NORMALIZATION}),
        "Raw Event + Normalized Permission",
    ),
    (
        frozenset({MemoryType.FAILURE_EVENT, MemoryType.EVALUATION_ASSET}),
        "Failure Event + Regression Test",
    ),
    (
        frozenset({MemoryType.IDENTITY_ROOT, MemoryType.DERIVED_SUMMARY, MemoryType.AUDIT_LOG}),
        "Identity Root + Operational Memory",
    ),
    (
        frozenset({MemoryType.BELIEF, MemoryType.PERMISSION_RECORD}),
        "Belief + Permission",
    ),
    (
        frozenset({MemoryType.PROCEDURE, MemoryType.RAW_EVENT}),
        "Procedure + Historical Event",
    ),
]

LOST_IF_MERGED: dict[str, list[str]] = {
    "Permission + Summary/Reflection/Self-memory": [
        "permission scope", "source authority", "effective time",
        "notify boundary", "interpretation vs fact distinction",
    ],
    "Raw Event + Normalized Permission": [
        "structured scope", "machine-actionable permission", "revision history",
    ],
    "Failure Event + Regression Test": [
        "failure evidence", "regression test asset", "diagnostic vs prevention roles",
    ],
    "Identity Root + Operational Memory": [
        "identity continuity", "being ID", "core values immutability",
    ],
}


def check_merge_blocked(types: set[MemoryType]) -> list[dict]:
    """Return CROSS_TYPE_MERGE_BLOCKED findings for type combinations."""
    findings: list[dict] = []
    for group_types, label in MERGE_BLOCK_GROUPS:
        if group_types.issubset(types):
            findings.append({
                "finding": "CROSS_TYPE_MERGE_BLOCKED",
                "group": label,
                "types": sorted(t.value for t in group_types),
                "lost_if_merged": LOST_IF_MERGED.get(label, ["type distinction", "lineage"]),
            })
    return findings


def audit_cross_type_merges(records: list) -> list[dict]:
    from memory_auditor.types import MemoryRecord

    type_set = {r.memory_type for r in records if isinstance(r, MemoryRecord)}
    return check_merge_blocked(type_set)
