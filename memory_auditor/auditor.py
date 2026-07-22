"""Memory Auditor orchestrator — READ_ONLY advisory analysis."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from memory_auditor.authority import check_authority_violations, resolve_scope_overlap
from memory_auditor.claims import build_atomic_claims, validate_claim_isolation
from memory_auditor.classifier import classify_all
from memory_auditor.compression import audit_compression_candidates
from memory_auditor.duplicates import detect_duplicates
from memory_auditor.guard import ReadOnlyGuard
from memory_auditor.identity import audit_identity_protection, identity_preservation_actions
from memory_auditor.lineage import analyze_lineage
from memory_auditor.merge_guard import audit_cross_type_merges
from memory_auditor.permission import audit_permission_integrity
from memory_auditor.report import generate_report
from memory_auditor.retrieval import audit_retrieval_policy, query_routing_table
from memory_auditor.types import (
    ControlRole,
    LineageEdge,
    LineageRelationship,
    MemoryRecord,
    MemoryType,
)


class ReadOnlyMemoryAuditor:
    """Advisory-only memory auditor. MUTATIONS_PERFORMED = 0 always."""

    MODE = "READ_ONLY"
    ADVISORY_ONLY = True

    def __init__(self) -> None:
        self.guard = ReadOnlyGuard()

    def load_fixture(self, path: str | Path) -> tuple[list[MemoryRecord], list[LineageEdge], dict]:
        """Load immutable fixture — never touches stable store."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        records = [self._parse_record(r) for r in data.get("records", [])]
        edges = [
            LineageEdge(
                e["from"], e["to"],
                LineageRelationship(e["relationship"]),
                e.get("evidence_ref", ""),
                e.get("certainty", "CERTAIN"),
            )
            for e in data.get("explicit_edges", [])
        ]
        meta = data.get("metadata", {})
        return records, edges, meta

    def audit(
        self,
        records: list[MemoryRecord],
        explicit_edges: list[LineageEdge] | None = None,
        compression_summary: str | None = None,
    ) -> dict[str, Any]:
        """Run full read-only audit on immutable record copy."""
        records_copy = deepcopy(records)
        classification = classify_all(records_copy)
        lineage = analyze_lineage(records_copy, explicit_edges)
        authority = check_authority_violations(records_copy)
        duplicates = detect_duplicates(records_copy)
        merge_blocks = audit_cross_type_merges(records_copy)
        retrieval = audit_retrieval_policy(records_copy)
        claims = build_atomic_claims(records_copy)
        claim_violations = validate_claim_isolation(claims)
        compression = []
        if compression_summary:
            compression = audit_compression_candidates(compression_summary, records_copy)
        identity_risks = audit_identity_protection(records_copy)
        identity_risks.extend(identity_preservation_actions(records_copy))
        permission_risks = audit_permission_integrity(records_copy)
        routing = self._build_routing_recommendations(records_copy)
        routing_table = query_routing_table(records_copy)

        report = generate_report(
            records_scanned=len(records_copy),
            classification_findings=classification,
            lineage_findings=lineage,
            authority_findings=authority + [{"claim_violations": claim_violations}],
            duplicate_findings=duplicates,
            cross_type_merge_blocks=merge_blocks,
            retrieval_policy_findings=retrieval + [{"query_routing": routing_table}],
            atomic_claim_candidates=[c.to_dict() for c in claims],
            compression_loss_findings=compression,
            identity_risks=identity_risks,
            permission_risks=permission_risks,
            recommended_routing=routing,
            guard=self.guard,
        )
        report["scope_resolutions"] = self._scope_resolutions(records_copy)
        return report

    def _scope_resolutions(self, records: list[MemoryRecord]) -> list[dict]:
        domains = [
            "minor_wording",
            "session_reflection",
            "counter_evidence",
            "belief_promotion",
        ]
        return [resolve_scope_overlap(d, records) for d in domains]

    def _build_routing_recommendations(self, records: list[MemoryRecord]) -> list[dict]:
        recs: list[dict] = []
        for record in records:
            action = self._routing_action(record)
            if action:
                recs.append({"record_id": record.record_id, "action": action})
        return recs

    def _routing_action(self, record: MemoryRecord) -> str | None:
        if record.memory_type in (MemoryType.PERMISSION_RECORD, MemoryType.LOSSLESS_NORMALIZATION):
            return "KEEP_ACTIVE"
        if record.memory_type == MemoryType.IDENTITY_ROOT:
            return "PROTECT_INDEXED"
        if record.memory_type == MemoryType.FAILURE_EVENT:
            return "PROTECT_INDEXED"
        if record.memory_type == MemoryType.EVALUATION_ASSET:
            return "KEEP_ACTIVE"
        if record.memory_type == MemoryType.AUDIT_LOG:
            return "AUDIT_ARCHIVE"
        if record.memory_type == MemoryType.DERIVED_SUMMARY and record.status in (
            "STALE", "STALE_FOR_PERMISSION", "SUPERSEDED_FOR_PERMISSION_USE",
        ):
            return "LOWER_RETRIEVAL_WEIGHT"
        if record.memory_type == MemoryType.DERIVED_INTERPRETATION:
            return "LOWER_RETRIEVAL_WEIGHT"
        if record.memory_type == MemoryType.DERIVED_SELF_MODEL:
            return "REVIEW_REQUIRED"
        if record.memory_type == MemoryType.RAW_EVENT:
            return "PROTECT_INDEXED"
        return None

    @staticmethod
    def _parse_record(data: dict) -> MemoryRecord:
        mt = data.get("memory_type", "UNKNOWN")
        cr = data.get("control_role", "NON_AUTHORITATIVE")
        return MemoryRecord(
            record_id=data["record_id"],
            memory_type=MemoryType(mt),
            control_role=ControlRole(cr),
            content=data.get("content", ""),
            domain=data.get("domain", ""),
            source_event_ids=tuple(data.get("source_event_ids", [])),
            scope=data.get("scope", ""),
            exclusions=tuple(data.get("exclusions", [])),
            status=data.get("status", "ACTIVE"),
            superseded_by=data.get("superseded_by"),
            effective_time=data.get("effective_time"),
            authority_for_behavior=data.get("authority_for_behavior", False),
            metadata=data.get("metadata", {}),
        )
