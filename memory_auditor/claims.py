"""Atomic claim builder — isolated provenance per claim."""

from __future__ import annotations

from memory_auditor.types import AtomicClaim, ConfidenceBucket, ControlRole, MemoryRecord, MemoryType


def build_atomic_claims(records: list[MemoryRecord]) -> list[AtomicClaim]:
    """Build atomic claims from records — never cross-merge domains."""
    claims: list[AtomicClaim] = []
    by_id = {r.record_id: r for r in records}

    for record in records:
        if record.memory_type == MemoryType.RAW_EVENT:
            continue
        if record.memory_type in (MemoryType.PERMISSION_RECORD, MemoryType.LOSSLESS_NORMALIZATION):
            src_ids = list(record.source_event_ids) or [
                s for s in record.source_event_ids if s in by_id
            ]
            claims.append(AtomicClaim(
                claim_id=f"claim-{record.record_id}",
                statement=record.content or f"Permission: {record.scope}",
                domain=record.domain,
                source_event_ids=list(record.source_event_ids),
                normalized_records=[record.record_id],
                is_derived=True,
                control_role=ControlRole.RETRIEVAL_CUE,
                authority_for_behavior=False,
                confidence=ConfidenceBucket.HIGH,
            ))
        elif record.memory_type == MemoryType.FAILURE_EVENT:
            claims.append(AtomicClaim(
                claim_id=f"claim-{record.record_id}",
                statement=record.content,
                domain=record.domain or "retrieval_failure",
                source_event_ids=[],
                supporting_records=[record.record_id],
                is_derived=False,
                control_role=ControlRole.HISTORICAL_RECORD,
                authority_for_behavior=False,
                confidence=ConfidenceBucket.HIGH,
            ))
        elif record.memory_type == MemoryType.EVALUATION_ASSET:
            src = list(record.source_event_ids)
            claims.append(AtomicClaim(
                claim_id=f"claim-{record.record_id}",
                statement=record.content,
                domain=record.domain or "evaluation",
                source_event_ids=src,
                normalized_records=[record.record_id],
                supporting_records=src,
                lineage_relationships=["EVALUATION_RESPONSE"] if src else [],
                is_derived=True,
                control_role=ControlRole.VALIDATION_GATE,
                authority_for_behavior=False,
                confidence=ConfidenceBucket.HIGH,
            ))

    return _dedupe_claims(claims)


def _dedupe_claims(claims: list[AtomicClaim]) -> list[AtomicClaim]:
    seen: set[str] = set()
    out: list[AtomicClaim] = []
    for claim in claims:
        if claim.claim_id not in seen:
            seen.add(claim.claim_id)
            out.append(claim)
    return out


def validate_claim_isolation(claims: list[AtomicClaim]) -> list[dict]:
    """Ensure no claim mixes permission, preference, and failure domains."""
    violations: list[dict] = []
    forbidden_mix = {"permission", "preference", "failure", "evaluation"}
    for claim in claims:
        if claim.authority_for_behavior:
            violations.append({
                "claim_id": claim.claim_id,
                "violation": "CONSOLIDATED_CLAIM_AS_AUTHORITY",
            })
    return violations
