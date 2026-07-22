#!/usr/bin/env python3
"""Memory Auditor M2 tests — runtime snapshot, compare, metrics, explainability."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memory_auditor import ReadOnlyMemoryAuditor
from memory_auditor.guard import BlockedAction, ReadOnlyGuard, ReadOnlyViolation
from memory_auditor.snapshot import create_readonly_snapshot

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


print("M2 snapshot read-only")
seed_db()
snap = create_readonly_snapshot(DB)
test("snapshot created", Path(snap.snapshot_path).exists())
test("snapshot path differs from source", snap.snapshot_path != snap.source_path)

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

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
