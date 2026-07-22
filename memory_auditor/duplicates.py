"""Duplicate detector — classifies duplicate relationships."""

from __future__ import annotations

from memory_auditor.types import DuplicateClass, MemoryRecord, MemoryType


def classify_duplicate_pair(a: MemoryRecord, b: MemoryRecord) -> dict:
    """Classify relationship between two records."""
    classification = _classify(a, b)
    return {
        "record_a": a.record_id,
        "record_b": b.record_id,
        "classification": classification.value,
        "share_source": bool(set(a.source_event_ids) & set(b.source_event_ids)),
    }


def _classify(a: MemoryRecord, b: MemoryRecord) -> DuplicateClass:
    if a.record_id == b.record_id:
        return DuplicateClass.EXACT_DUPLICATE
    if a.content and a.content == b.content and a.source_event_ids == b.source_event_ids:
        return DuplicateClass.EXACT_DUPLICATE

    raw_perm_pairs = (
        (MemoryType.RAW_EVENT, MemoryType.PERMISSION_RECORD),
        (MemoryType.RAW_EVENT, MemoryType.LOSSLESS_NORMALIZATION),
    )
    pair = (a.memory_type, b.memory_type)
    if pair in raw_perm_pairs or (pair[1], pair[0]) in raw_perm_pairs:
        return DuplicateClass.NOT_DUPLICATE

    shared = set(a.source_event_ids) & set(b.source_event_ids)
    if shared:
        if a.memory_type == b.memory_type:
            return DuplicateClass.SEMANTIC_DUPLICATE
        if _is_sibling_derivation(a, b):
            return DuplicateClass.SIBLING_DERIVATION
        if _is_derived_chain(a, b) or _is_derived_chain(b, a):
            return DuplicateClass.DERIVED_DUPLICATE
        if a.domain and b.domain and a.domain == b.domain:
            return DuplicateClass.PARTIAL_OVERLAP
        return DuplicateClass.DERIVED_DUPLICATE

    if a.content and b.content and _semantic_overlap(a.content, b.content):
        return DuplicateClass.SEMANTIC_DUPLICATE

    return DuplicateClass.NOT_DUPLICATE


def _is_sibling_derivation(a: MemoryRecord, b: MemoryRecord) -> bool:
    perm_types = {MemoryType.PERMISSION_RECORD, MemoryType.LOSSLESS_NORMALIZATION}
    summary_types = {MemoryType.DERIVED_SUMMARY}
    if (a.memory_type in perm_types and b.memory_type in summary_types) or (
        b.memory_type in perm_types and a.memory_type in summary_types
    ):
        return True
    return False


def _is_derived_chain(parent: MemoryRecord, child: MemoryRecord) -> bool:
    return parent.record_id in child.source_event_ids


def _semantic_overlap(a: str, b: str) -> bool:
    aw = set(a.lower().split())
    bw = set(b.lower().split())
    if not aw or not bw:
        return False
    overlap = len(aw & bw) / max(len(aw), len(bw))
    return overlap > 0.6


def detect_duplicates(records: list[MemoryRecord]) -> list[dict]:
    findings: list[dict] = []
    for i, a in enumerate(records):
        for b in records[i + 1 :]:
            finding = classify_duplicate_pair(a, b)
            if finding["classification"] != DuplicateClass.NOT_DUPLICATE.value:
                findings.append(finding)
    return findings
