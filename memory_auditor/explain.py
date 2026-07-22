"""Explainability traces for audit findings."""

from __future__ import annotations

from typing import Any

from memory_auditor.types import ConfidenceBucket


def make_trace(
    rule: str,
    record_id: str,
    step: str,
    detail: str = "",
    *,
    query_domain: str = "",
) -> dict[str, Any]:
    return {
        "rule": rule,
        "record_id": record_id,
        "step": step,
        "detail": detail,
        "query_domain": query_domain,
    }


def wrap_finding(
    finding_type: str,
    record_id: str,
    rule: str,
    confidence: ConfidenceBucket,
    trace_steps: list[dict[str, Any]],
    **extra: Any,
) -> dict[str, Any]:
    return {
        "finding_type": finding_type,
        "record_id": record_id,
        "confidence": confidence.value,
        "trace": trace_steps,
        **extra,
    }


def trace_summary_authority_risk(record_id: str, query_domain: str = "permission") -> dict[str, Any]:
    return wrap_finding(
        finding_type="SUMMARY_AUTHORITY_RISK",
        record_id=record_id,
        rule="SUMMARY_IS_NEVER_ACTION_AUTHORITY",
        confidence=ConfidenceBucket.HIGH,
        trace_steps=[
            make_trace("SUMMARY_IS_NEVER_ACTION_AUTHORITY", record_id, "rule_triggered"),
            make_trace("SUMMARY_IS_NEVER_ACTION_AUTHORITY", record_id, "record_classified", "DERIVED_SUMMARY"),
            make_trace("SUMMARY_IS_NEVER_ACTION_AUTHORITY", record_id, "permission_query", query_domain=query_domain),
            make_trace("SUMMARY_IS_NEVER_ACTION_AUTHORITY", record_id, "ranking_check", "summary must not outrank ACTIVE_PERMISSION"),
            make_trace("SUMMARY_IS_NEVER_ACTION_AUTHORITY", record_id, "violation", "summary in behavioral retrieval path"),
        ],
    )


def trace_stale_retrieval(record_id: str, failure_id: str = "") -> dict[str, Any]:
    return wrap_finding(
        finding_type="STALE_SUMMARY_RETRIEVAL_RISK",
        record_id=record_id,
        rule="PERMISSION_QUERY_ACTIVE_FIRST",
        confidence=ConfidenceBucket.HIGH if failure_id else ConfidenceBucket.MODERATE,
        trace_steps=[
            make_trace("PERMISSION_QUERY_ACTIVE_FIRST", record_id, "rule_triggered"),
            make_trace("PERMISSION_QUERY_ACTIVE_FIRST", record_id, "record_status", "STALE_FOR_PERMISSION"),
            make_trace("PERMISSION_QUERY_ACTIVE_FIRST", record_id, "retrieval_query", query_domain="permission"),
            make_trace("PERMISSION_QUERY_ACTIVE_FIRST", failure_id or record_id, "failure_evidence", failure_id or "none"),
            make_trace("PERMISSION_QUERY_ACTIVE_FIRST", record_id, "violation", "stale summary may override permission"),
        ],
        related_failure=failure_id or None,
    )


def trace_lineage_unknown(from_id: str, to_id: str) -> dict[str, Any]:
    return wrap_finding(
        finding_type="LINEAGE_UNKNOWN",
        record_id=to_id,
        rule="LINEAGE_EVIDENCE_REQUIRED",
        confidence=ConfidenceBucket.LOW,
        trace_steps=[
            make_trace("LINEAGE_EVIDENCE_REQUIRED", to_id, "rule_triggered"),
            make_trace("LINEAGE_EVIDENCE_REQUIRED", from_id, "source_missing_or_unverified"),
            make_trace("LINEAGE_EVIDENCE_REQUIRED", to_id, "edge_rejected", "insufficient evidence for causal edge"),
        ],
        from_id=from_id,
    )


def trace_cross_type_merge(group: str, types: list[str]) -> dict[str, Any]:
    return wrap_finding(
        finding_type="CROSS_TYPE_MERGE_BLOCKED",
        record_id=group,
        rule="CROSS_TYPE_MERGE_PROHIBITED",
        confidence=ConfidenceBucket.VERY_HIGH,
        trace_steps=[
            make_trace("CROSS_TYPE_MERGE_PROHIBITED", group, "rule_triggered"),
            make_trace("CROSS_TYPE_MERGE_PROHIBITED", group, "types_detected", ", ".join(types)),
            make_trace("CROSS_TYPE_MERGE_PROHIBITED", group, "merge_blocked", "distinct control roles"),
        ],
        types=types,
    )
