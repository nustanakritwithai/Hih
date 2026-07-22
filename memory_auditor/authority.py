"""Authority resolver — enforces authority rules, reports violations."""

from __future__ import annotations

from memory_auditor.types import ControlRole, MemoryRecord, MemoryType

AUTHORITY_RULES = [
    "SUMMARY_IS_NEVER_ACTION_AUTHORITY",
    "SELF_MEMORY_IS_NEVER_ACTION_AUTHORITY",
    "REFLECTION_IS_NEVER_RAW_EVENT",
    "VALIDATION_GATE_CANNOT_AUTHORIZE_ACTION",
    "PERMISSION_SOURCE_IS_NOT_EXECUTABLE_PERMISSION",
    "MOST_SPECIFIC_PERMISSION_SCOPE_WINS",
    "EXPLICIT_NOTIFY_REQUIREMENT_WINS_IN_OVERLAP",
    "IDENTITY_ROOT_BYPASSES_ORDINARY_RETENTION",
]


def check_authority_violations(records: list[MemoryRecord]) -> list[dict]:
    findings: list[dict] = []
    for record in records:
        if record.memory_type == MemoryType.DERIVED_SUMMARY and record.authority_for_behavior:
            findings.append({
                "rule": "SUMMARY_IS_NEVER_ACTION_AUTHORITY",
                "record_id": record.record_id,
                "severity": "HIGH",
            })
        if record.memory_type == MemoryType.DERIVED_SELF_MODEL and record.authority_for_behavior:
            findings.append({
                "rule": "SELF_MEMORY_IS_NEVER_ACTION_AUTHORITY",
                "record_id": record.record_id,
                "severity": "HIGH",
            })
        if record.memory_type == MemoryType.DERIVED_INTERPRETATION and record.control_role == ControlRole.AUTHORITATIVE_SOURCE:
            findings.append({
                "rule": "REFLECTION_IS_NEVER_RAW_EVENT",
                "record_id": record.record_id,
                "severity": "HIGH",
            })
        if record.memory_type == MemoryType.EVALUATION_ASSET and record.authority_for_behavior:
            findings.append({
                "rule": "VALIDATION_GATE_CANNOT_AUTHORIZE_ACTION",
                "record_id": record.record_id,
                "severity": "HIGH",
            })
        if record.memory_type == MemoryType.RAW_EVENT and record.control_role == ControlRole.ACTION_AUTHORITY:
            findings.append({
                "rule": "PERMISSION_SOURCE_IS_NOT_EXECUTABLE_PERMISSION",
                "record_id": record.record_id,
                "severity": "MEDIUM",
            })
    return findings


def resolve_behavioral_authority(records: list[MemoryRecord], domain: str) -> list[dict]:
    """Return active permission authorities for a domain."""
    authorities: list[dict] = []
    permissions = [
        r for r in records
        if r.memory_type in (MemoryType.PERMISSION_RECORD, MemoryType.LOSSLESS_NORMALIZATION)
        and r.status == "ACTIVE"
    ]
    for perm in permissions:
        if domain in perm.domain or perm.domain in ("", "all"):
            authorities.append({
                "record_id": perm.record_id,
                "domain": perm.domain,
                "scope": perm.scope,
                "status": perm.status,
            })
    if len(authorities) > 1:
        authorities.sort(key=lambda a: len(a.get("scope", "")), reverse=True)
    return authorities


def resolve_scope_overlap(action_domain: str, records: list[MemoryRecord]) -> dict:
    """Apply overlap resolution rules for P1/P2 style permissions."""
    active = [
        r for r in records
        if r.memory_type in (MemoryType.PERMISSION_RECORD, MemoryType.LOSSLESS_NORMALIZATION)
        and r.status == "ACTIVE"
    ]
    matching = [r for r in active if _domain_matches(action_domain, r)]
    if not matching:
        return {"action_domain": action_domain, "ruling": "NO_ACTIVE_PERMISSION", "winner": None}
    deny = [
        r for r in matching
        if r.metadata.get("decision") == "DENY" or r.metadata.get("level") == "forbidden"
    ]
    if deny:
        winner = deny[0]
        return {
            "action_domain": action_domain,
            "ruling": "DENY_WINS_OVER_BROAD_ALLOW",
            "winner": winner.record_id,
            "overlapping": [r.record_id for r in matching],
        }
    if len(matching) == 1:
        return {"action_domain": action_domain, "ruling": "SINGLE_SCOPE", "winner": matching[0].record_id}
    notify = [r for r in matching if "notify" in r.scope.lower() or "notify" in r.content.lower()]
    if notify:
        winner = max(notify, key=lambda r: len(r.scope))
        return {
            "action_domain": action_domain,
            "ruling": "EXPLICIT_NOTIFY_REQUIREMENT_WINS_IN_OVERLAP",
            "winner": winner.record_id,
            "overlapping": [r.record_id for r in matching],
        }
    winner = max(matching, key=lambda r: len(r.scope))
    return {
        "action_domain": action_domain,
        "ruling": "MOST_SPECIFIC_PERMISSION_SCOPE_WINS",
        "winner": winner.record_id,
        "overlapping": [r.record_id for r in matching],
    }


ACTION_DOMAIN_ALIASES: dict[str, tuple[str, ...]] = {
    "session_reflection": ("evidence_memory_belief", "reflection", "evidence"),
    "counter_evidence": ("evidence_memory_belief", "evidence"),
    "belief_promotion": ("evidence_memory_belief", "belief"),
    "minor_wording": ("minor_wording",),
}


def _domain_matches(action_domain: str, record: MemoryRecord) -> bool:
    aliases = ACTION_DOMAIN_ALIASES.get(action_domain, (action_domain,))
    record_domains = (record.domain, record.scope, record.content)
    for alias in aliases:
        for field in record_domains:
            if alias and field and alias in field:
                return True
    if not record.domain:
        return action_domain == "minor_wording"
    return action_domain in record.domain or record.domain in action_domain
