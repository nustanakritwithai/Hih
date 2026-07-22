"""Retrieval policy auditor — advisory recommendations only."""

from __future__ import annotations

from memory_auditor.types import ControlRole, MemoryRecord, MemoryType


RETRIEVAL_RULES = [
    "permission query retrieves active scoped permission first",
    "most-specific scope wins",
    "notify-before wins in overlap",
    "summary cannot override permission",
    "self-memory cannot authorize action",
    "reflection cannot replace raw evidence",
    "superseded permission is historical only",
    "identity roots bypass age-based archival",
    "failure/test assets appear in diagnostic queries",
    "query-dependent weighting where appropriate",
]


def audit_retrieval_policy(records: list[MemoryRecord]) -> list[dict]:
    findings: list[dict] = []
    summaries = [r for r in records if r.memory_type == MemoryType.DERIVED_SUMMARY]
    permissions = [
        r for r in records
        if r.memory_type in (MemoryType.PERMISSION_RECORD, MemoryType.LOSSLESS_NORMALIZATION)
        and r.status == "ACTIVE"
    ]
    stale_summaries = [r for r in summaries if r.status in ("STALE", "SUPERSEDED_FOR_PERMISSION_USE", "STALE_FOR_PERMISSION")]

    if summaries and permissions:
        for summary in summaries:
            if summary.authority_for_behavior:
                findings.append({
                    "query_domain": "permission",
                    "current_risk": "summary_ranked_above_permission",
                    "record_id": summary.record_id,
                    "recommended_priority": [
                        "ACTIVE_PERMISSION",
                        "PERMISSION_SOURCE",
                        "DERIVED_SUMMARY",
                    ],
                    "mutation_performed": False,
                })

    failures = [r for r in records if r.memory_type == MemoryType.FAILURE_EVENT]
    if failures:
        findings.append({
            "query_domain": "stale_override_diagnostic",
            "current_risk": "stale_summary_override",
            "recommended_priority": ["FAILURE_EVENT", "EVALUATION_ASSET", "ACTIVE_PERMISSION"],
            "elevated_records": [f.record_id for f in failures],
            "mutation_performed": False,
        })

    for record in records:
        if record.memory_type == MemoryType.DERIVED_SELF_MODEL and record.control_role != ControlRole.CANDIDATE_ONLY:
            findings.append({
                "query_domain": "action_authorization",
                "current_risk": "self_memory_authorization_risk",
                "record_id": record.record_id,
                "recommended_priority": ["ACTIVE_PERMISSION"],
                "mutation_performed": False,
            })

    if stale_summaries:
        findings.append({
            "query_domain": "permission",
            "current_risk": "stale_summary_retrieval",
            "record_ids": [s.record_id for s in stale_summaries],
            "recommended_action": "LOWER_RETRIEVAL_WEIGHT",
            "mutation_performed": False,
        })

    return findings


def query_routing_table(records: list[MemoryRecord]) -> dict[str, list[str]]:
    """Map query types to recommended record retrieval order."""
    perm_ids = [
        r.record_id for r in records
        if r.memory_type in (MemoryType.PERMISSION_RECORD, MemoryType.LOSSLESS_NORMALIZATION)
        and r.status == "ACTIVE"
    ]
    failure_ids = [r.record_id for r in records if r.memory_type == MemoryType.FAILURE_EVENT]
    test_ids = [r.record_id for r in records if r.memory_type == MemoryType.EVALUATION_ASSET]
    summary_ids = [r.record_id for r in records if r.memory_type == MemoryType.DERIVED_SUMMARY]
    return {
        "minor_wording_query": perm_ids,
        "evidence_memory_belief_query": perm_ids,
        "stale_override_diagnostic": failure_ids + test_ids + perm_ids,
        "permission_history_query": perm_ids,
        "S1_allowed_for": ["historical_narrative_only"],
        "S1_forbidden_for": ["permission_behavior", "notify_decision"],
        "summary_ids_advisory_only": summary_ids,
    }
