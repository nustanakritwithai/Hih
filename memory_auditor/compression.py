"""Compression loss detector — analyzes summary candidates."""

from __future__ import annotations

from memory_auditor.types import CompressionRisk, MemoryRecord, MemoryType

LOSS_DIMENSIONS = [
    "scope", "exceptions", "authority", "effective_time", "source_lineage",
    "counter_evidence", "permission_history", "claim_domain",
    "behavior_applicability", "identity_relevance",
]


def analyze_compression(
    summary_text: str,
    source_records: list[MemoryRecord],
) -> dict:
    """Analyze compression loss for a summary candidate."""
    lost: list[str] = []
    has_permission_sources = any(
        r.memory_type in (MemoryType.PERMISSION_RECORD, MemoryType.RAW_EVENT)
        for r in source_records
    )
    has_multiple_scopes = len({r.domain for r in source_records if r.domain}) > 1
    has_exceptions = any(r.exclusions for r in source_records)
    has_failure = any(r.memory_type == MemoryType.FAILURE_EVENT for r in source_records)
    has_identity = any(r.memory_type == MemoryType.IDENTITY_ROOT for r in source_records)

    if has_multiple_scopes and "บริบท" not in summary_text and "context" not in summary_text.lower():
        lost.append("scope")
    if has_exceptions:
        lost.append("exceptions")
    if has_permission_sources and "authority" not in summary_text.lower() and "permission" not in summary_text.lower():
        lost.append("authority")
    if any(r.effective_time for r in source_records):
        lost.append("effective_time")
    if len(source_records) > 1:
        lost.append("source_lineage")
    if has_failure:
        lost.append("counter_evidence")
    if has_permission_sources:
        lost.append("permission_history")
    if has_multiple_scopes:
        lost.append("claim_domain")
    lost.append("behavior_applicability")
    if has_identity:
        lost.append("identity_relevance")

    lost = list(dict.fromkeys(lost))

    risk = CompressionRisk.SAFE_RETRIEVAL_CUE
    if has_permission_sources:
        risk = CompressionRisk.PERMISSION_RISK
    if has_identity:
        risk = CompressionRisk.IDENTITY_RISK
    elif lost:
        risk = CompressionRisk.LOSSY_NON_AUTHORITATIVE
    if len(lost) >= 5:
        risk = CompressionRisk.UNSAFE_FOR_BEHAVIOR

    return {
        "summary_text": summary_text,
        "lost_information": lost,
        "classification": risk.value,
        "usable_as_retrieval_cue": risk == CompressionRisk.SAFE_RETRIEVAL_CUE,
        "usable_for_behavior_control": False,
    }


def audit_compression_candidates(
    summary_text: str,
    records: list[MemoryRecord],
) -> list[dict]:
    return [analyze_compression(summary_text, records)]
