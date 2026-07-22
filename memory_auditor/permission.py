"""Permission integrity auditor."""

from __future__ import annotations

from memory_auditor.types import MemoryRecord, MemoryType

REQUIRED_PERMISSION_FIELDS = [
    "source_event_id", "authority_domain", "scope", "conditions",
    "exclusions", "effective_time", "status", "superseded_by", "revision_history",
]


def audit_permission_integrity(records: list[MemoryRecord]) -> list[dict]:
    findings: list[dict] = []
    permissions = [
        r for r in records
        if r.memory_type in (MemoryType.PERMISSION_RECORD, MemoryType.LOSSLESS_NORMALIZATION)
    ]

    for perm in permissions:
        if not perm.source_event_ids:
            findings.append({
                "finding": "PERMISSION_SOURCE_MISSING",
                "record_id": perm.record_id,
                "severity": "HIGH",
            })
        if not perm.scope and not perm.domain:
            findings.append({
                "finding": "PERMISSION_SCOPE_AMBIGUOUS",
                "record_id": perm.record_id,
                "severity": "HIGH",
            })
        if perm.metadata.get("summary_substitution"):
            findings.append({
                "finding": "PERMISSION_SUMMARY_SUBSTITUTION",
                "record_id": perm.record_id,
                "severity": "CRITICAL",
            })
        if perm.status == "ACTIVE" and perm.metadata.get("stale_retrieval_risk"):
            findings.append({
                "finding": "STALE_PERMISSION_RETRIEVAL_RISK",
                "record_id": perm.record_id,
                "severity": "HIGH",
            })

    summaries = [r for r in records if r.memory_type == MemoryType.DERIVED_SUMMARY]
    self_memories = [r for r in records if r.memory_type == MemoryType.DERIVED_SELF_MODEL]

    if summaries and not permissions:
        findings.append({
            "finding": "NORMALIZED_PERMISSION_MISSING",
            "severity": "CRITICAL",
            "detail": "summaries exist without normalized permissions",
        })

    for sm in self_memories:
        if sm.authority_for_behavior or sm.metadata.get("used_as_permission"):
            findings.append({
                "finding": "SELF_MEMORY_AUTHORIZATION_RISK",
                "record_id": sm.record_id,
                "severity": "HIGH",
            })

    superseded = [r for r in permissions if r.status == "SUPERSEDED"]
    if permissions and not any(r.metadata.get("revision_history") for r in permissions) and superseded:
        findings.append({
            "finding": "PERMISSION_HISTORY_INTEGRITY_RISK",
            "severity": "MEDIUM",
            "detail": "superseded permissions without revision history metadata",
        })

    return findings
