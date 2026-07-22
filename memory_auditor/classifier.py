"""Memory classifier — assigns memory_type and control_role."""

from __future__ import annotations

from memory_auditor.types import ControlRole, MemoryRecord, MemoryType

_TYPE_ROLE_MAP: dict[MemoryType, ControlRole] = {
    MemoryType.RAW_EVENT: ControlRole.AUTHORITATIVE_SOURCE,
    MemoryType.PERMISSION_RECORD: ControlRole.ACTION_AUTHORITY,
    MemoryType.LOSSLESS_NORMALIZATION: ControlRole.ACTION_AUTHORITY,
    MemoryType.DERIVED_SUMMARY: ControlRole.RETRIEVAL_CUE,
    MemoryType.DERIVED_INTERPRETATION: ControlRole.NON_AUTHORITATIVE,
    MemoryType.DERIVED_SELF_MODEL: ControlRole.CANDIDATE_ONLY,
    MemoryType.BELIEF: ControlRole.CANDIDATE_ONLY,
    MemoryType.PROCEDURE: ControlRole.STABLE_PROCEDURE,
    MemoryType.AUDIT_LOG: ControlRole.HISTORICAL_RECORD,
    MemoryType.FAILURE_EVENT: ControlRole.HISTORICAL_RECORD,
    MemoryType.EVALUATION_ASSET: ControlRole.VALIDATION_GATE,
    MemoryType.IDENTITY_ROOT: ControlRole.PROTECTED_IDENTITY,
    MemoryType.CONCERN: ControlRole.RETRIEVAL_CUE,
    MemoryType.UNKNOWN: ControlRole.NON_AUTHORITATIVE,
}


def classify_record(record: MemoryRecord) -> dict:
    """Return classification finding for a single record."""
    expected_role = _TYPE_ROLE_MAP.get(record.memory_type, ControlRole.NON_AUTHORITATIVE)
    role_mismatch = record.control_role != expected_role and record.memory_type != MemoryType.UNKNOWN
    return {
        "record_id": record.record_id,
        "memory_type": record.memory_type.value,
        "control_role": record.control_role.value,
        "expected_role": expected_role.value,
        "role_mismatch": role_mismatch,
        "authority_for_behavior": record.authority_for_behavior,
    }


def classify_all(records: list[MemoryRecord]) -> list[dict]:
    return [classify_record(r) for r in records]
