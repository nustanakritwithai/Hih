#!/usr/bin/env python3
"""Memory Auditor M2 tests — runtime snapshot, compare, metrics, hardening."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memory_auditor import ReadOnlyMemoryAuditor
from memory_auditor.adapters.life_engine import LifeEngineReadOnlyAdapter, _classify_event
from memory_auditor.authority import resolve_scope_overlap
from memory_auditor.guard import BlockedAction, ReadOnlyGuard, ReadOnlyViolation
from memory_auditor.snapshot import cleanup_snapshot, create_readonly_snapshot, file_fingerprint
from memory_auditor.types import ControlRole, MemoryRecord, MemoryType

FIXTURE = ROOT / "memory_auditor" / "fixtures" / "rt04.json"
DB = "/tmp/dioo-auditor-m2-test.db"

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


def seed_db() -> None:
    subprocess.run(["python3", "-m", "life_engine", "--db", DB, "init"], check=True, capture_output=True)
    subprocess.run(["python3", "-m", "life_engine", "--db", DB, "awaken"], check=True, capture_output=True)
    subprocess.run(
        ["python3", "-m", "life_engine", "--db", DB, "perceive", "routine update สั้น ๆ พอ"],
        check=True, capture_output=True,
    )
    subprocess.run(["python3", "-m", "life_engine", "--db", DB, "upgrade"], check=True, capture_output=True)


def _wal_db() -> Path:
    path = Path(tempfile.gettempdir()) / "dioo-auditor-wal-test.db"
    for suffix in ("", "-wal", "-shm"):
        p = Path(str(path) + suffix)
        if p.exists():
            p.unlink()
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE audit_rows (id INTEGER PRIMARY KEY, v TEXT)")
    conn.execute("INSERT INTO audit_rows (v) VALUES ('baseline')")
    conn.commit()
    conn.close()
    return path


print("M2 snapshot read-only")
seed_db()
snap = create_readonly_snapshot(DB)
test("snapshot created", Path(snap.snapshot_path).exists())
test("snapshot path differs from source", snap.snapshot_path != snap.source_path)
test("snapshot uses backup API", snap.method == "sqlite_backup_api")
test("source hash unchanged at snapshot", snap.source_hash_before == snap.source_hash_after)
test("source mtime unchanged at snapshot", snap.source_mtime_before == snap.source_mtime_after)
cleanup_result = cleanup_snapshot(snap)
test("snapshot cleanup deletes file", cleanup_result == "deleted" and not Path(snap.snapshot_path).exists())

print("M2 WAL consistency")
wal_db = _wal_db()
conn = sqlite3.connect(wal_db)
conn.execute("INSERT INTO audit_rows (v) VALUES ('committed_wal')")
conn.commit()
conn.close()
wal_snap = create_readonly_snapshot(wal_db)
wal_conn = sqlite3.connect(wal_snap.read_only_uri, uri=True)
wal_rows = [r[0] for r in wal_conn.execute("SELECT v FROM audit_rows ORDER BY id").fetchall()]
wal_conn.close()
test("snapshot_consistent_with_wal", len(wal_rows) == 2)
test("snapshot_captures_committed_wal_rows", "committed_wal" in wal_rows)

uncommitted_db = _wal_db()
writer = sqlite3.connect(uncommitted_db)
writer.execute("INSERT INTO audit_rows (v) VALUES ('uncommitted')")
# deliberately no commit
uncommitted_snap = create_readonly_snapshot(uncommitted_db)
reader = sqlite3.connect(uncommitted_snap.read_only_uri, uri=True)
uncommitted_rows = [r[0] for r in reader.execute("SELECT v FROM audit_rows ORDER BY id").fetchall()]
reader.close()
test("snapshot_excludes_uncommitted_transaction", "uncommitted" not in uncommitted_rows)
writer.commit()
writer.close()
cleanup_snapshot(uncommitted_snap)
cleanup_snapshot(wal_snap)

print("M2 adapter lifecycle")
hash_before, mtime_before = file_fingerprint(Path(DB))
with LifeEngineReadOnlyAdapter(DB, use_snapshot=True) as adapter:
    _ = adapter.extract_records()
info = adapter.snapshot_info
test("source_mtime_unchanged after audit", info["source_mtime_before"] == info["source_mtime_after"])
test("source_hash_unchanged after audit", info["source_hash_before"] == info["source_hash_after"])
hash_after, mtime_after = file_fingerprint(Path(DB))
test("source file hash unchanged on disk", hash_before == hash_after)
test("source file mtime unchanged on disk", mtime_before == mtime_after)
test("snapshot cleaned on exit", info["cleanup_result"] == "deleted")
test("snapshot file absent after exit", not Path(info["snapshot_path"]).exists())

print("M2 forbidden permission authority")
with LifeEngineReadOnlyAdapter(DB, use_snapshot=False) as adapter:
    records = adapter.extract_records()
forbidden = [
    r for r in records
    if r.memory_type == MemoryType.PERMISSION_RECORD and r.metadata.get("level") == "forbidden"
]
test("forbidden permissions exist", len(forbidden) >= 1)
if forbidden:
    f = forbidden[0]
    test("forbidden status ACTIVE", f.status == "ACTIVE")
    test("forbidden decision DENY", f.metadata.get("decision") == "DENY")
    test("forbidden authority_for_behavior true", f.authority_for_behavior is True)
    test("forbidden lineage incomplete", f.metadata.get("lineage_status") == "LEGACY_PERMISSION_LINEAGE_INCOMPLETE")

print("M2 deny wins over broad allow")
allow = MemoryRecord(
    record_id="perm-allow-broad",
    memory_type=MemoryType.PERMISSION_RECORD,
    control_role=ControlRole.ACTION_AUTHORITY,
    content="minor_wording=allowed",
    domain="minor_wording",
    scope="minor_wording",
    status="ACTIVE",
    authority_for_behavior=True,
    metadata={"decision": "ALLOW", "level": "allowed"},
)
deny = MemoryRecord(
    record_id="perm-deny-specific",
    memory_type=MemoryType.PERMISSION_RECORD,
    control_role=ControlRole.ACTION_AUTHORITY,
    content="minor_wording=forbidden",
    domain="minor_wording",
    scope="minor_wording_notify",
    status="ACTIVE",
    authority_for_behavior=True,
    metadata={"decision": "DENY", "level": "forbidden"},
)
ruling = resolve_scope_overlap("minor_wording", [allow, deny])
test("deny_wins_over_broad_allow_in_overlap", ruling["ruling"] == "DENY_WINS_OVER_BROAD_ALLOW")
test("deny winner selected", ruling["winner"] == deny.record_id)

print("M2 event source classification")
creator_role, creator_auth = _classify_event("USER_MESSAGE", {"text": "hi"})
tool_role, tool_auth = _classify_event("TOOL_RESULT", {"output": "x"})
agent_role, agent_auth = _classify_event("AGENT_ACTION", {"source": "dioo"})
unknown_role, unknown_auth = _classify_event(None, {})
test("creator event authoritative", creator_role == ControlRole.AUTHORITATIVE_SOURCE)
test("tool event non-authoritative", tool_role == ControlRole.NON_AUTHORITATIVE)
test("agent event historical", agent_role == ControlRole.HISTORICAL_RECORD)
test("unknown event non-authoritative", unknown_role == ControlRole.NON_AUTHORITATIVE)
test("not all events authoritative", creator_role != tool_role)

print("M2 malformed JSON and missing tables")
malformed_db = Path(tempfile.gettempdir()) / f"dioo-auditor-malformed-{os.getpid()}.db"
for suffix in ("", "-wal", "-shm"):
    p = Path(str(malformed_db) + suffix)
    if p.exists():
        p.unlink()
subprocess.run(["python3", "-m", "life_engine", "--db", str(malformed_db), "init"], check=True, capture_output=True)
subprocess.run(["python3", "-m", "life_engine", "--db", str(malformed_db), "awaken"], check=True, capture_output=True)
mconn = sqlite3.connect(malformed_db)
mconn.execute("UPDATE beings SET core_values = ? WHERE being_id = 'dioo-001'", ("{bad json",))
mconn.execute("DROP TABLE IF EXISTS reflections")
mconn.commit()
mconn.close()
with LifeEngineReadOnlyAdapter(str(malformed_db), use_snapshot=False) as bad_adapter:
    bad_records = bad_adapter.extract_records()
    errors = bad_adapter.adapter_errors
test("malformed JSON produces adapter error", any(e.get("error") == "MALFORMED_JSON" for e in errors))
test("missing reflections table handled", any(e.get("context") == "reflections" for e in errors))
test("adapter still returns records on malformed JSON", len(bad_records) > 0)

print("M2 runtime audit")
auditor = ReadOnlyMemoryAuditor()
runtime_report = auditor.audit_runtime(DB)
test("runtime mode", runtime_report.get("audit_source") == "runtime_snapshot")
test("runtime zero mutations", runtime_report.get("mutations_performed") == 0)
test("runtime has snapshot_info", "snapshot_info" in runtime_report)
test("runtime records > 0", runtime_report.get("records_scanned", 0) > 0)
test("runtime has identity roots", any(
    c.get("memory_type") == "IDENTITY_ROOT" for c in runtime_report.get("classification_findings", [])
))
events = [
    c for c in runtime_report.get("classification_findings", [])
    if c.get("memory_type") == "RAW_EVENT"
]
test("raw events present", len(events) > 0)
test("event classification supports non-authoritative roles", tool_role != creator_role)

print("M2 sanitized runtime report")
sanitized = auditor.audit_runtime_sanitized(DB, fixture_path=FIXTURE)
test("sanitized mode", sanitized.get("mode") == "SANITIZED_READ_ONLY_AUDIT")
test("sanitized zero mutations", sanitized.get("mutations_performed") == 0)
test("sanitized records_scanned > 0", sanitized.get("records_scanned", 0) > 0)
test("sanitized source_hash_unchanged", sanitized.get("source_hash_unchanged") is True)
test("sanitized snapshot_cleaned", sanitized.get("snapshot_cleaned") == "deleted")
test("sanitized has records_by_type", bool(sanitized.get("records_by_type")))
test("sanitized has fixture_gap_analysis", "fixture_gap_analysis" in sanitized)
for key in ("records_scanned", "content", "message", "text"):
    raw_dump = json.dumps(sanitized)
    if key == "records_scanned":
        continue
    test(f"sanitized has no raw memory key '{key}'", f'"{key}"' not in raw_dump or key in (
        "records_scanned", "records_by_type", "records_by_control_role",
    ))

print("M2 metrics")
metrics = runtime_report.get("metrics", {})
test("metrics elapsed_seconds", metrics.get("elapsed_seconds", 0) >= 0)
test("metrics records_per_second", metrics.get("records_scanned_per_second", 0) > 0)
test("metrics lineage_rate", "lineage_resolution_rate" in metrics)
test("metrics unknown_lineage_rate", "unknown_lineage_rate" in metrics)

print("M2 explainability")
explained = runtime_report.get("explained_findings", [])
test("explained findings present", isinstance(explained, list))
if explained:
    test("finding has confidence", all("confidence" in f for f in explained if f.get("finding_type")))
    test("finding has trace", all("trace" in f for f in explained if f.get("finding_type")))

print("M2 compare fixture vs runtime")
comparison = auditor.compare_fixture_runtime(FIXTURE, DB)
test("compare mode", comparison.get("mode") == "READ_ONLY_COMPARISON_AUDIT")
test("compare zero mutations", comparison.get("mutations_performed") == 0)
comp = comparison.get("comparison", {})
test("comparison has answers", "answers" in comp)
test("comparison has gap analysis", "fixture_gap_analysis" in comp)
test("fixture report present", comparison.get("fixture_report", {}).get("records_scanned", 0) >= 15)
test("runtime report present", comparison.get("runtime_report", {}).get("records_scanned", 0) > 0)

print("M2 retrieval path risks")
eval_assets = [
    c for c in runtime_report.get("classification_findings", [])
    if c.get("memory_type") == "EVALUATION_ASSET"
]
test("runtime detects retrieval architecture risks", len(eval_assets) >= 1)

print("M2 read-only guard still enforced")
guard = ReadOnlyGuard()
for action in BlockedAction:
    try:
        guard.assert_read_only(action)
        test(f"guard blocks {action.value}", False)
    except ReadOnlyViolation:
        test(f"guard blocks {action.value}", True)

print("M2 CLI subcommands")
subprocess.run(
    ["python3", "-m", "memory_auditor", "fixture", str(FIXTURE), "-o", "/tmp/m2-fixture.json"],
    check=True, capture_output=True,
)
test("CLI fixture", Path("/tmp/m2-fixture.json").exists())
subprocess.run(
    ["python3", "-m", "memory_auditor", "runtime", "--db", DB, "-o", "/tmp/m2-runtime.json"],
    check=True, capture_output=True,
)
test("CLI runtime", Path("/tmp/m2-runtime.json").exists())
subprocess.run(
    ["python3", "-m", "memory_auditor", "compare", str(FIXTURE), "--db", DB, "-o", "/tmp/m2-compare.json"],
    check=True, capture_output=True,
)
test("CLI compare", Path("/tmp/m2-compare.json").exists())
subprocess.run(
    [
        "python3", "-m", "memory_auditor", "runtime-sanitized",
        "--db", DB, "--fixture", str(FIXTURE), "-o", "/tmp/m2-sanitized.json",
    ],
    check=True, capture_output=True,
)
test("CLI runtime-sanitized", Path("/tmp/m2-sanitized.json").exists())

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
