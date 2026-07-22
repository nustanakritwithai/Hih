#!/usr/bin/env python3
"""M2.5 manual shadow audit — compare-runs and trial helpers."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memory_auditor.compare_runs import compare_shadow_runs

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


def report(run_id: str, **overrides) -> dict:
    base = {
        "run_id": run_id,
        "mode": "SANITIZED_READ_ONLY_AUDIT",
        "records_scanned": 48,
        "records_by_type": {"DERIVED_SUMMARY": 11, "BELIEF": 1},
        "lineage_status": "EVALUATED",
        "lineage_edges_evaluated": 11,
        "lineage_resolution_rate": 1.0,
        "derived_records_total": 17,
        "derived_records_with_source_refs": 11,
        "derived_records_missing_source_refs": 6,
        "lineage_coverage_rate": 0.6471,
        "orphan_source_reference_count": 0,
        "summary_authority_rate": 0.0,
        "permission_integrity_findings": ["PERMISSION_SOURCE_MISSING"],
        "identity_findings": ["IDENTITY_CHECKSUM_MISSING"],
        "runtime_only_patterns": ["autonomy"],
        "adapter_errors": [],
        "snapshot_cleaned": "deleted",
        "main_db_file_hash_unchanged": True,
        "concurrent_write_status": "NOT_OBSERVED",
        "mutations_performed": 0,
    }
    base.update(overrides)
    return base


print("M2.5 compare shadow runs")
baseline = report("run-001")
later = report(
    "run-002",
    records_scanned=50,
    records_by_type={"DERIVED_SUMMARY": 12, "BELIEF": 2},
    lineage_coverage_rate=0.6111,
    runtime_only_patterns=["autonomy", "notify_before"],
)
comparison = compare_shadow_runs([baseline, later])
test("comparison mode", comparison["mode"] == "MANUAL_SHADOW_RUN_COMPARISON")
test("comparison zero mutations", comparison["mutations_performed"] == 0)
test("record growth by type", comparison["record_growth_by_type"]["by_type"]["DERIVED_SUMMARY"]["delta"] == 1)
test("lineage coverage delta present", len(comparison["lineage_coverage_delta_vs_baseline"]) == 1)
test("new semantic patterns", "notify_before" in comparison["semantic_pattern_changes"]["per_run"][0]["new_patterns"])
test("stop conditions clean", comparison["stop_conditions"]["trial_should_stop"] is False)

bad = report("run-bad", mutations_performed=1)
bad_comparison = compare_shadow_runs([baseline, bad])
test("stop on mutation", bad_comparison["stop_conditions"]["trial_should_stop"] is True)

not_evaluated = report("run-empty", lineage_status="NOT_EVALUATED", lineage_resolution_rate=1.0, lineage_edges_evaluated=0)
bad_metrics = compare_shadow_runs([baseline, not_evaluated])
test("stop on lineage metric inconsistency", bad_metrics["stop_conditions"]["trial_should_stop"] is True)

print("M2.5 CLI compare-runs")
import subprocess

r1 = Path("/tmp/shadow-run-001.json")
r2 = Path("/tmp/shadow-run-002.json")
r1.write_text(json.dumps(baseline), encoding="utf-8")
r2.write_text(json.dumps(later), encoding="utf-8")
subprocess.run(
    ["python3", "-m", "memory_auditor", "compare-runs", str(r1), str(r2), "-o", "/tmp/shadow-compare.json"],
    check=True,
    capture_output=True,
)
test("CLI compare-runs output", Path("/tmp/shadow-compare.json").exists())

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
