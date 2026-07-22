"""Memory Auditor types — memory_type vs control_role separation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MemoryType(str, Enum):
    RAW_EVENT = "RAW_EVENT"
    PERMISSION_RECORD = "PERMISSION_RECORD"
    LOSSLESS_NORMALIZATION = "LOSSLESS_NORMALIZATION"
    DERIVED_SUMMARY = "DERIVED_SUMMARY"
    DERIVED_INTERPRETATION = "DERIVED_INTERPRETATION"
    DERIVED_SELF_MODEL = "DERIVED_SELF_MODEL"
    BELIEF = "BELIEF"
    PROCEDURE = "PROCEDURE"
    AUDIT_LOG = "AUDIT_LOG"
    FAILURE_EVENT = "FAILURE_EVENT"
    EVALUATION_ASSET = "EVALUATION_ASSET"
    IDENTITY_ROOT = "IDENTITY_ROOT"
    CONCERN = "CONCERN"
    UNKNOWN = "UNKNOWN"


class ControlRole(str, Enum):
    ACTION_AUTHORITY = "ACTION_AUTHORITY"
    VALIDATION_GATE = "VALIDATION_GATE"
    STABLE_PROCEDURE = "STABLE_PROCEDURE"
    RETRIEVAL_CUE = "RETRIEVAL_CUE"
    AUTHORITATIVE_SOURCE = "AUTHORITATIVE_SOURCE"
    HISTORICAL_RECORD = "HISTORICAL_RECORD"
    CANDIDATE_ONLY = "CANDIDATE_ONLY"
    NON_AUTHORITATIVE = "NON_AUTHORITATIVE"
    PROTECTED_IDENTITY = "PROTECTED_IDENTITY"


class EventSourceAuthority(str, Enum):
    CREATOR_DIRECT_SOURCE = "CREATOR_DIRECT_SOURCE"
    OBSERVED_EVENT = "OBSERVED_EVENT"
    AGENT_ACTION_EVENT = "AGENT_ACTION_EVENT"
    TOOL_RESULT = "TOOL_RESULT"
    EXTERNAL_SOURCE = "EXTERNAL_SOURCE"
    UNKNOWN_SOURCE = "UNKNOWN_SOURCE"


class LineageRelationship(str, Enum):
    LOSSLESS_NORMALIZATION = "LOSSLESS_NORMALIZATION"
    DERIVED_SUMMARY = "DERIVED_SUMMARY"
    DERIVED_INTERPRETATION = "DERIVED_INTERPRETATION"
    DERIVED_SELF_MODEL = "DERIVED_SELF_MODEL"
    DUPLICATE_COPY = "DUPLICATE_COPY"
    SIBLING_DERIVATION = "SIBLING_DERIVATION"
    EVALUATION_RESPONSE = "EVALUATION_RESPONSE"
    AUDIT_ASSOCIATION = "AUDIT_ASSOCIATION"
    NO_CAUSAL_LINEAGE = "NO_CAUSAL_LINEAGE"
    UNKNOWN = "UNKNOWN"


class DuplicateClass(str, Enum):
    EXACT_DUPLICATE = "EXACT_DUPLICATE"
    SEMANTIC_DUPLICATE = "SEMANTIC_DUPLICATE"
    DERIVED_DUPLICATE = "DERIVED_DUPLICATE"
    SIBLING_DERIVATION = "SIBLING_DERIVATION"
    PARTIAL_OVERLAP = "PARTIAL_OVERLAP"
    NOT_DUPLICATE = "NOT_DUPLICATE"
    UNKNOWN = "UNKNOWN"


class CompressionRisk(str, Enum):
    SAFE_RETRIEVAL_CUE = "SAFE_RETRIEVAL_CUE"
    LOSSY_NON_AUTHORITATIVE = "LOSSY_NON_AUTHORITATIVE"
    UNSAFE_FOR_BEHAVIOR = "UNSAFE_FOR_BEHAVIOR"
    PERMISSION_RISK = "PERMISSION_RISK"
    IDENTITY_RISK = "IDENTITY_RISK"


class ConfidenceBucket(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


@dataclass(frozen=True)
class MemoryRecord:
    """Immutable memory record for audit input."""

    record_id: str
    memory_type: MemoryType
    control_role: ControlRole
    content: str = ""
    domain: str = ""
    source_event_ids: tuple[str, ...] = ()
    scope: str = ""
    exclusions: tuple[str, ...] = ()
    status: str = "ACTIVE"
    superseded_by: str | None = None
    effective_time: str | None = None
    authority_for_behavior: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "memory_type": self.memory_type.value,
            "control_role": self.control_role.value,
            "content": self.content,
            "domain": self.domain,
            "source_event_ids": list(self.source_event_ids),
            "scope": self.scope,
            "exclusions": list(self.exclusions),
            "status": self.status,
            "superseded_by": self.superseded_by,
            "effective_time": self.effective_time,
            "authority_for_behavior": self.authority_for_behavior,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class LineageEdge:
    from_id: str
    to_id: str
    relationship: LineageRelationship
    evidence_ref: str = ""
    certainty: str = "CERTAIN"

    def to_dict(self) -> dict[str, Any]:
        return {
            "from": self.from_id,
            "to": self.to_id,
            "relationship": self.relationship.value,
            "evidence_ref": self.evidence_ref,
            "certainty": self.certainty,
        }


@dataclass
class AtomicClaim:
    claim_id: str
    statement: str
    domain: str
    source_event_ids: list[str] = field(default_factory=list)
    normalized_records: list[str] = field(default_factory=list)
    supporting_records: list[str] = field(default_factory=list)
    lineage_relationships: list[str] = field(default_factory=list)
    is_derived: bool = True
    control_role: ControlRole = ControlRole.RETRIEVAL_CUE
    authority_for_behavior: bool = False
    confidence: ConfidenceBucket = ConfidenceBucket.MODERATE

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "statement": self.statement,
            "domain": self.domain,
            "source_event_ids": self.source_event_ids,
            "normalized_records": self.normalized_records,
            "supporting_records": self.supporting_records,
            "lineage_relationships": self.lineage_relationships,
            "is_derived": self.is_derived,
            "control_role": self.control_role.value,
            "authority_for_behavior": self.authority_for_behavior,
            "confidence": self.confidence.value,
        }
