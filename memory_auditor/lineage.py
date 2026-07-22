"""Lineage analyzer — builds lineage graph from records and explicit edges."""

from __future__ import annotations

from memory_auditor.types import LineageEdge, LineageRelationship, MemoryRecord, MemoryType


def infer_lineage_edges(records: list[MemoryRecord]) -> list[LineageEdge]:
    """Infer lineage edges from source_event_ids and memory types."""
    by_id = {r.record_id: r for r in records}
    edges: list[LineageEdge] = []
    seen: set[tuple[str, str, str]] = set()

    def add(edge: LineageEdge) -> None:
        key = (edge.from_id, edge.to_id, edge.relationship.value)
        if key not in seen:
            seen.add(key)
            edges.append(edge)

    for record in records:
        for src_id in record.source_event_ids:
            if src_id not in by_id:
                add(LineageEdge(src_id, record.record_id, LineageRelationship.UNKNOWN, "missing_source"))
                continue
            src = by_id[src_id]
            rel = _relationship_for_derivation(src, record)
            add(LineageEdge(src_id, record.record_id, rel, f"{src.record_id}->{record.record_id}"))

    return edges


def _relationship_for_derivation(source: MemoryRecord, derived: MemoryRecord) -> LineageRelationship:
    if derived.memory_type in (MemoryType.PERMISSION_RECORD, MemoryType.LOSSLESS_NORMALIZATION):
        if source.memory_type == MemoryType.RAW_EVENT:
            return LineageRelationship.LOSSLESS_NORMALIZATION
    if derived.memory_type == MemoryType.DERIVED_SUMMARY:
        return LineageRelationship.DERIVED_SUMMARY
    if derived.memory_type == MemoryType.DERIVED_INTERPRETATION:
        return LineageRelationship.DERIVED_INTERPRETATION
    if derived.memory_type == MemoryType.DERIVED_SELF_MODEL:
        return LineageRelationship.DERIVED_SELF_MODEL
    if derived.memory_type == MemoryType.EVALUATION_ASSET and source.memory_type == MemoryType.FAILURE_EVENT:
        return LineageRelationship.EVALUATION_RESPONSE
    if derived.memory_type == MemoryType.AUDIT_LOG:
        return LineageRelationship.AUDIT_ASSOCIATION
    if source.source_event_ids and derived.source_event_ids:
        if set(source.source_event_ids) & set(derived.source_event_ids):
            return LineageRelationship.SIBLING_DERIVATION
    if source.domain and derived.domain and source.domain == derived.domain:
        return LineageRelationship.NO_CAUSAL_LINEAGE
    return LineageRelationship.UNKNOWN


def merge_explicit_edges(
    inferred: list[LineageEdge],
    explicit: list[LineageEdge],
) -> list[LineageEdge]:
    """Explicit edges take precedence; no fabricated edges."""
    by_key: dict[tuple[str, str], LineageEdge] = {}
    for edge in inferred:
        by_key[(edge.from_id, edge.to_id)] = edge
    for edge in explicit:
        by_key[(edge.from_id, edge.to_id)] = edge
    return list(by_key.values())


def analyze_lineage(
    records: list[MemoryRecord],
    explicit_edges: list[LineageEdge] | None = None,
) -> list[dict]:
    inferred = infer_lineage_edges(records)
    edges = merge_explicit_edges(inferred, explicit_edges or [])
    return [e.to_dict() for e in edges]
