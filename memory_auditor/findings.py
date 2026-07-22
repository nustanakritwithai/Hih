"""Enrich audit findings with confidence and explainability traces."""

from __future__ import annotations

from memory_auditor.explain import (
    trace_cross_type_merge,
    trace_lineage_unknown,
    trace_stale_retrieval,
    trace_summary_authority_risk,
)
from memory_auditor.types import ConfidenceBucket, MemoryRecord, MemoryType


def enrich_authority_findings(raw: list[dict], records: list[MemoryRecord]) -> tuple[list[dict], list[dict]]:
    """Return (raw findings, explained findings with traces)."""
    explained: list[dict] = []
    by_id = {r.record_id: r for r in records}
    for finding in raw:
        if not isinstance(finding, dict) or "rule" not in finding:
            continue
        rid = finding.get("record_id", "")
        rule = finding["rule"]
        if rule == "SUMMARY_IS_NEVER_ACTION_AUTHORITY":
            explained.append(trace_summary_authority_risk(rid))
        elif rule == "SELF_MEMORY_IS_NEVER_ACTION_AUTHORITY":
            explained.append({
                **finding,
                "finding_type": "SELF_MEMORY_AUTHORITY_RISK",
                "confidence": ConfidenceBucket.HIGH.value,
                "trace": [
                    {"rule": rule, "record_id": rid, "step": "violation"},
                ],
            })
        else:
            explained.append({
                **finding,
                "finding_type": rule,
                "confidence": ConfidenceBucket.HIGH.value,
                "trace": [{"rule": rule, "record_id": rid, "step": "violation"}],
            })
    return raw, explained


def enrich_lineage_findings(lineage: list[dict]) -> list[dict]:
    explained: list[dict] = []
    for edge in lineage:
        if edge.get("relationship") == "UNKNOWN" or edge.get("certainty") == "LINEAGE_UNCERTAIN":
            explained.append(trace_lineage_unknown(edge.get("from", ""), edge.get("to", "")))
    return explained


def enrich_merge_blocks(blocks: list[dict]) -> list[dict]:
    return [
        trace_cross_type_merge(b.get("group", "unknown"), b.get("types", []))
        for b in blocks
    ]


def enrich_retrieval_risks(records: list[MemoryRecord], retrieval_findings: list[dict]) -> list[dict]:
    explained: list[dict] = []
    stale = [r for r in records if r.memory_type == MemoryType.DERIVED_SUMMARY and "STALE" in r.status]
    for record in stale:
        explained.append(trace_stale_retrieval(record.record_id))
    for finding in retrieval_findings:
        if isinstance(finding, dict) and finding.get("current_risk") == "stale_summary_override":
            explained.append(trace_stale_retrieval("S1", failure_id="F1"))
    return explained


def build_explained_findings(
    records: list[MemoryRecord],
    authority_raw: list[dict],
    lineage: list[dict],
    merge_blocks: list[dict],
    retrieval: list[dict],
) -> list[dict]:
    _, auth_explained = enrich_authority_findings(authority_raw, records)
    explained = auth_explained
    explained.extend(enrich_lineage_findings(lineage))
    explained.extend(enrich_merge_blocks(merge_blocks))
    explained.extend(enrich_retrieval_risks(records, retrieval))
    return explained
