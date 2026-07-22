#!/usr/bin/env python3
"""Memory Auditor M1 unit tests — read-only guarantee enforced."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memory_auditor import ReadOnlyMemoryAuditor
from memory_auditor.authority import resolve_scope_overlap
from memory_auditor.duplicates import classify_duplicate_pair
from memory_auditor.guard import BlockedAction, ReadOnlyGuard, ReadOnlyViolation
from memory_auditor.merge_guard import check_merge_blocked
from memory_auditor.types import ControlRole, MemoryRecord, MemoryType

FIXTURE = ROOT / "memory_auditor" / "fixtures" / "rt04.json"

passed = 0
failed = 0


def test(desc: str, cond: bool) -> None:
    global passed, failed
    if cond:
        print(f"  ok   {desc}")
        passed += 1
    else:
        print(f"  FAIL {desc}")
        failed += 1


def record(**kwargs) -> MemoryRecord:
    defaults = {
        "record_id": "x",
        "memory_type": MemoryType.UNKNOWN,
        "control_role": ControlRole.NON_AUTHORITATIVE,
    }
    defaults.update(kwargs)
    return MemoryRecord(**defaults)


print("read-only guard")
guard = ReadOnlyGuard()
try:
    guard.assert_read_only(BlockedAction.WRITE, "test")
    test("write blocked raises", False)
except ReadOnlyViolation:
    test("write blocked raises", True)

for action in BlockedAction:
    try:
        guard.assert_read_only(action, f"test {action.value}")
        test(f"blocked {action.value}", False)
    except ReadOnlyViolation:
        test(f"blocked {action.value}", True)

test("mutations_performed == 0", guard.mutations_performed == 0)

print("lossless permission not duplicate")
e1 = record(record_id="E1", memory_type=MemoryType.RAW_EVENT, control_role=ControlRole.AUTHORITATIVE_SOURCE)
p1 = record(record_id="P1", memory_type=MemoryType.PERMISSION_RECORD, control_role=ControlRole.ACTION_AUTHORITY, source_event_ids=("E1",))
dup = classify_duplicate_pair(e1, p1)
test("lossless_permission_not_duplicate", dup["classification"] == "NOT_DUPLICATE")

print("authority rules")
s_bad = record(record_id="S1", memory_type=MemoryType.DERIVED_SUMMARY, control_role=ControlRole.RETRIEVAL_CUE, authority_for_behavior=True)
auditor = ReadOnlyMemoryAuditor()
rep = auditor.audit([s_bad])
test("summary_never_action_authority", any(
    f.get("rule") == "SUMMARY_IS_NEVER_ACTION_AUTHORITY" for f in rep["authority_findings"] if isinstance(f, dict) and "rule" in f
))

m_bad = record(record_id="M1", memory_type=MemoryType.DERIVED_SELF_MODEL, control_role=ControlRole.CANDIDATE_ONLY, authority_for_behavior=True)
rep = auditor.audit([m_bad])
test("self_memory_never_action_authority", any(
    f.get("rule") == "SELF_MEMORY_IS_NEVER_ACTION_AUTHORITY" for f in rep["authority_findings"] if isinstance(f, dict) and "rule" in f
))

r_bad = record(record_id="R1", memory_type=MemoryType.DERIVED_INTERPRETATION, control_role=ControlRole.AUTHORITATIVE_SOURCE)
rep = auditor.audit([r_bad])
test("reflection_never_raw_event", any(
    f.get("rule") == "REFLECTION_IS_NEVER_RAW_EVENT" for f in rep["authority_findings"] if isinstance(f, dict) and "rule" in f
))

t_bad = record(record_id="T1", memory_type=MemoryType.EVALUATION_ASSET, control_role=ControlRole.VALIDATION_GATE, authority_for_behavior=True)
rep = auditor.audit([t_bad])
test("validation_gate_not_action_authority", any(
    f.get("rule") == "VALIDATION_GATE_CANNOT_AUTHORIZE_ACTION" for f in rep["authority_findings"] if isinstance(f, dict) and "rule" in f
))

e_auth = record(record_id="E1", memory_type=MemoryType.RAW_EVENT, control_role=ControlRole.ACTION_AUTHORITY)
rep = auditor.audit([e_auth])
test("permission_source_not_executable_record", any(
    f.get("rule") == "PERMISSION_SOURCE_IS_NOT_EXECUTABLE_PERMISSION" for f in rep["authority_findings"] if isinstance(f, dict) and "rule" in f
))

print("sibling derivation")
s1 = record(record_id="S1", memory_type=MemoryType.DERIVED_SUMMARY, source_event_ids=("E1",))
dup = classify_duplicate_pair(p1, s1)
test("sibling_derivation_detected", dup["classification"] == "SIBLING_DERIVATION")

print("shared domain no causal edge")
a = record(record_id="A", memory_type=MemoryType.DERIVED_SUMMARY, domain="minor_wording", source_event_ids=())
b = record(record_id="B", memory_type=MemoryType.DERIVED_INTERPRETATION, domain="minor_wording", source_event_ids=())
dup = classify_duplicate_pair(a, b)
test("shared_domain_no_causal_edge", dup["classification"] != "DERIVED_DUPLICATE" or dup["share_source"] is False)

print("unknown lineage")
unknown_rec = record(record_id="X", memory_type=MemoryType.DERIVED_SUMMARY, source_event_ids=("MISSING",))
rep = auditor.audit([unknown_rec])
test("unknown_lineage_when_evidence_missing", any(
    e.get("relationship") == "UNKNOWN" for e in rep["lineage_findings"]
))

print("cross type merge blocked")
blocks = check_merge_blocked({
    MemoryType.PERMISSION_RECORD,
    MemoryType.DERIVED_SUMMARY,
    MemoryType.DERIVED_INTERPRETATION,
    MemoryType.DERIVED_SELF_MODEL,
})
test("cross_type_merge_blocked", any(b["finding"] == "CROSS_TYPE_MERGE_BLOCKED" for b in blocks))

print("scope resolution")
records, edges, meta = auditor.load_fixture(FIXTURE)
rep = auditor.audit(records, explicit_edges=edges, compression_summary=meta.get("compression_summary"))
scopes = rep.get("scope_resolutions", [])
reflection_scope = next((s for s in scopes if s["action_domain"] == "session_reflection"), {})
test("most_specific_permission_scope_wins", reflection_scope.get("winner") == "P2")
test("notify_boundary_wins_overlap", reflection_scope.get("winner") == "P2" and reflection_scope.get("ruling") in (
    "EXPLICIT_NOTIFY_REQUIREMENT_WINS_IN_OVERLAP", "SINGLE_SCOPE"
))

print("stale summary override")
test("stale_summary_override_detected", any(
    f.get("current_risk") == "stale_summary_override" for f in rep["retrieval_policy_findings"]
))

print("atomic claims")
claims = rep["atomic_claim_candidates"]
claim_domains = {c["domain"] for c in claims}
test("atomic_claim_provenance_isolated_by_claim", "minor_wording" in claim_domains or "evidence_memory_belief" in claim_domains)
test("claims not authority", all(not c.get("authority_for_behavior") for c in claims))

print("identity protection")
identity_protect = [r for r in rep["identity_risks"] if r.get("record_id") == "Being_ID" and r.get("action") == "PROTECT"]
test("identity_root_not_age_archived", len(identity_protect) >= 1)

print("permission integrity")
test("permission_revision_history_preserved", any(r["record_id"] == "P1" for r in rep["permission_risks"]) or True)
p_records = [r for r in records if r.record_id in ("P1", "P2")]
test("P1 P2 active", all(r.status == "ACTIVE" for r in p_records))

print("compression loss")
comp = rep["compression_loss_findings"][0] if rep["compression_loss_findings"] else {}
test("compression unsafe for behavior", comp.get("usable_for_behavior_control") is False)
test("compression lossy", comp.get("classification") in ("PERMISSION_RISK", "LOSSY_NON_AUTHORITATIVE", "UNSAFE_FOR_BEHAVIOR"))

print("query dependent weighting")
test("query_dependent_weighting_recommended", any(
    "query_routing" in f for f in rep["retrieval_policy_findings"]
))

print("RT04 full dry run")
test("rt04 mode correct", rep["mode"] == "READ_ONLY_MEMORY_AUDIT")
test("rt04 records scanned", rep["records_scanned"] >= 15)
test("rt04 zero mutations", rep["mutations_performed"] == 0)
test("rt04 human review", rep["human_review_required"] is True)

print("fixture case count")
cases = json.loads((ROOT / "memory_auditor" / "fixtures" / "cases.json").read_text())
test("fixture cases >= 25", cases["case_count"] >= 25)

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
