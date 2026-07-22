"""Identity protection auditor — reports risks, no mutations."""

from __future__ import annotations

from memory_auditor.types import MemoryRecord, MemoryType

IDENTITY_FINDINGS = [
    "IDENTITY_RECORD_IN_ORDINARY_RETENTION_POLICY",
    "IDENTITY_COMPRESSION_RISK",
    "IDENTITY_REFERENCE_BROKEN",
    "IDENTITY_VERSIONING_MISSING",
    "IDENTITY_CHECKSUM_MISSING",
    "IDENTITY_BACKUP_UNKNOWN",
]

REQUIRED_IDENTITY_FIELDS = [
    "being_id", "birth_date", "origin", "core_values", "identity_boundaries",
]


def audit_identity_protection(records: list[MemoryRecord]) -> list[dict]:
    findings: list[dict] = []
    identity_records = [r for r in records if r.memory_type == MemoryType.IDENTITY_ROOT]

    for record in identity_records:
        meta = record.metadata
        if meta.get("retention_policy") == "age_based":
            findings.append({
                "finding": "IDENTITY_RECORD_IN_ORDINARY_RETENTION_POLICY",
                "record_id": record.record_id,
                "severity": "CRITICAL",
            })
        if not meta.get("versioning"):
            findings.append({
                "finding": "IDENTITY_VERSIONING_MISSING",
                "record_id": record.record_id,
                "severity": "HIGH",
            })
        if not meta.get("checksum"):
            findings.append({
                "finding": "IDENTITY_CHECKSUM_MISSING",
                "record_id": record.record_id,
                "severity": "MEDIUM",
            })
        if not meta.get("backup_known"):
            findings.append({
                "finding": "IDENTITY_BACKUP_UNKNOWN",
                "record_id": record.record_id,
                "severity": "MEDIUM",
            })
        if record.control_role.value != "PROTECTED_IDENTITY":
            findings.append({
                "finding": "IDENTITY_REFERENCE_BROKEN",
                "record_id": record.record_id,
                "severity": "HIGH",
            })

    return findings


def identity_preservation_actions(records: list[MemoryRecord]) -> list[dict]:
    actions: list[dict] = []
    for record in records:
        if record.memory_type != MemoryType.IDENTITY_ROOT:
            continue
        actions.append({
            "record_id": record.record_id,
            "action": "PROTECT",
            "store": "identity_root_store",
            "forbidden": [
                "archive_because_older_than_threshold",
                "compress_into_one_sentence",
                "delete_because_rarely_retrieved",
            ],
            "recommended_protection": [
                "write_protection", "checksum", "snapshot", "separate_store",
            ],
        })
    return actions
