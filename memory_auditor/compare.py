"""Compare fixture audit vs runtime audit."""

from __future__ import annotations

from typing import Any


def compare_reports(fixture_report: dict[str, Any], runtime_report: dict[str, Any]) -> dict[str, Any]:
    """Produce difference analysis — does fixture teach enough?"""
    fixture_types = _finding_types(fixture_report)
    runtime_types = _finding_types(runtime_report)

    only_fixture = fixture_types - runtime_types
    only_runtime = runtime_types - fixture_types
    shared = fixture_types & runtime_types

    fixture_patterns = _extract_pattern_clusters(fixture_report)
    runtime_patterns = _extract_pattern_clusters(runtime_report)
    new_runtime_patterns = set(runtime_patterns.keys()) - set(fixture_patterns.keys())

    return {
        "mode": "READ_ONLY_COMPARISON",
        "fixture_records": fixture_report.get("records_scanned", 0),
        "runtime_records": runtime_report.get("records_scanned", 0),
        "fixture_finding_types": sorted(fixture_types),
        "runtime_finding_types": sorted(runtime_types),
        "shared_finding_types": sorted(shared),
        "only_in_fixture": sorted(only_fixture),
        "only_in_runtime": sorted(only_runtime),
        "fixture_covers_runtime": len(only_runtime) == 0,
        "runtime_has_new_patterns": sorted(new_runtime_patterns),
        "fixture_gap_analysis": _gap_analysis(only_runtime, runtime_report),
        "metrics_comparison": {
            "fixture": fixture_report.get("metrics", {}),
            "runtime": runtime_report.get("metrics", {}),
        },
        "mutations_performed": 0,
        "answers": {
            "fixture_teaches_enough": len(only_runtime) == 0,
            "runtime_has_new_patterns": len(new_runtime_patterns) > 0,
        },
    }


def _finding_types(report: dict[str, Any]) -> set[str]:
    types: set[str] = set()
    for f in report.get("explained_findings", []):
        if isinstance(f, dict) and f.get("finding_type"):
            types.add(f["finding_type"])
    for f in report.get("authority_findings", []):
        if isinstance(f, dict) and f.get("rule"):
            types.add(f["rule"])
    for f in report.get("permission_risks", []):
        if isinstance(f, dict) and f.get("finding"):
            types.add(f["finding"])
    for block in report.get("cross_type_merge_blocks", []):
        types.add("CROSS_TYPE_MERGE_BLOCKED")
    return types


def _extract_pattern_clusters(report: dict[str, Any]) -> dict[str, int]:
    metrics = report.get("metrics", {})
    groups = metrics.get("semantic_pattern_groups", {})
    if isinstance(groups, dict):
        return groups
    return {}


def _gap_analysis(only_runtime: set[str], runtime_report: dict[str, Any]) -> list[dict]:
    gaps: list[dict] = []
    for finding_type in sorted(only_runtime):
        gaps.append({
            "finding_type": finding_type,
            "recommendation": "add fixture case or RT04 extension",
            "runtime_evidence": True,
        })
    if runtime_report.get("records_scanned", 0) > 19:
        gaps.append({
            "finding_type": "RUNTIME_RECORD_VOLUME",
            "recommendation": "fixture may not represent full runtime memory diversity",
            "runtime_record_count": runtime_report["records_scanned"],
        })
    return gaps
