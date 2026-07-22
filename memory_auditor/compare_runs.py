"""Compare sanitized manual shadow audit runs — read-only aggregate deltas."""

from __future__ import annotations

from collections import Counter
from typing import Any


TRACKED_METRICS = (
    "records_scanned",
    "lineage_edges_evaluated",
    "derived_records_total",
    "derived_records_with_source_refs",
    "derived_records_missing_source_refs",
    "lineage_coverage_rate",
    "orphan_source_reference_count",
    "summary_authority_rate",
)


def compare_shadow_runs(
    reports: list[dict[str, Any]],
    *,
    baseline_index: int = 0,
) -> dict[str, Any]:
    """Compare aggregate sanitized reports across manual shadow audit runs."""
    if not reports:
        raise ValueError("at least one report required")
    if baseline_index < 0 or baseline_index >= len(reports):
        raise ValueError("baseline_index out of range")

    baseline = reports[baseline_index]
    baseline_id = _run_label(baseline, baseline_index)

    per_run: list[dict[str, Any]] = []
    for index, report in enumerate(reports):
        run_id = _run_label(report, index)
        per_run.append({
            "run_id": run_id,
            "trigger_context": report.get("trigger_context", ""),
            "audited_at": report.get("audited_at"),
            "records_scanned": report.get("records_scanned", 0),
            "records_by_type": dict(report.get("records_by_type", {})),
            "lineage_status": report.get("lineage_status"),
            "lineage_coverage_rate": report.get("lineage_coverage_rate"),
            "orphan_source_reference_count": report.get("orphan_source_reference_count", 0),
            "mutations_performed": report.get("mutations_performed", 0),
        })

    metric_deltas = [
        _metric_delta(baseline, report, _run_label(report, index))
        for index, report in enumerate(reports)
        if index != baseline_index
    ]

    record_growth = _record_growth_by_type(reports)
    permission_risk_changes = _finding_set_changes(reports, "permission_integrity_findings")
    identity_risk_changes = _finding_set_changes(reports, "identity_findings")
    pattern_changes = _pattern_changes(reports)
    adapter_error_changes = _adapter_error_changes(reports)

    stop_conditions = _check_stop_conditions(reports)

    return {
        "mode": "MANUAL_SHADOW_RUN_COMPARISON",
        "mutations_performed": 0,
        "baseline_run_id": baseline_id,
        "runs_compared": len(reports),
        "per_run_summary": per_run,
        "record_growth_by_type": record_growth,
        "metric_deltas_vs_baseline": metric_deltas,
        "lineage_coverage_delta_vs_baseline": [
            {
                "run_id": d["run_id"],
                "baseline": baseline.get("lineage_coverage_rate"),
                "current": d.get("lineage_coverage_rate"),
                "delta": _numeric_delta(baseline.get("lineage_coverage_rate"), d.get("lineage_coverage_rate")),
            }
            for d in metric_deltas
        ],
        "new_orphan_references": _new_counter_values(
            baseline.get("orphan_source_reference_count", 0),
            [r.get("orphan_source_reference_count", 0) for r in reports[1:]],
        ),
        "permission_risk_changes": permission_risk_changes,
        "identity_risk_changes": identity_risk_changes,
        "summary_authority_risk_changes": _summary_authority_changes(reports),
        "semantic_pattern_changes": pattern_changes,
        "adapter_error_changes": adapter_error_changes,
        "stop_conditions": stop_conditions,
        "interpretation_note": (
            "Record count increases are not automatically degradation — inspect records_by_type growth."
        ),
    }


def _run_label(report: dict[str, Any], index: int) -> str:
    return str(report.get("run_id") or f"run-{index + 1:03d}")


def _numeric_delta(before: Any, after: Any) -> float | None:
    if before is None or after is None:
        return None
    return round(float(after) - float(before), 4)


def _metric_delta(baseline: dict[str, Any], current: dict[str, Any], run_id: str) -> dict[str, Any]:
    delta: dict[str, Any] = {"run_id": run_id}
    for key in TRACKED_METRICS:
        before = baseline.get(key)
        after = current.get(key)
        delta[key] = after
        delta[f"{key}_delta"] = _numeric_delta(before, after) if isinstance(before, (int, float)) or isinstance(after, (int, float)) else None
    return delta


def _record_growth_by_type(reports: list[dict[str, Any]]) -> dict[str, Any]:
    if len(reports) < 2:
        first = reports[0].get("records_by_type", {})
        return {"baseline_only": True, "by_type": {k: {"first": v, "last": v, "delta": 0} for k, v in first.items()}}

    first_types = reports[0].get("records_by_type", {})
    last_types = reports[-1].get("records_by_type", {})
    all_types = set(first_types) | set(last_types)
    growth: dict[str, dict[str, int]] = {}
    for memory_type in sorted(all_types):
        first_count = int(first_types.get(memory_type, 0))
        last_count = int(last_types.get(memory_type, 0))
        growth[memory_type] = {
            "first": first_count,
            "last": last_count,
            "delta": last_count - first_count,
        }
    return {
        "baseline_only": False,
        "first_run_id": _run_label(reports[0], 0),
        "last_run_id": _run_label(reports[-1], len(reports) - 1),
        "by_type": growth,
    }


def _finding_set_changes(reports: list[dict[str, Any]], field: str) -> dict[str, Any]:
    baseline_set = set(reports[0].get(field, []))
    changes: list[dict[str, Any]] = []
    for index, report in enumerate(reports[1:], start=1):
        current_set = set(report.get(field, []))
        changes.append({
            "run_id": _run_label(report, index),
            "new_findings": sorted(current_set - baseline_set),
            "resolved_findings": sorted(baseline_set - current_set),
            "stable_findings": sorted(current_set & baseline_set),
        })
    return {"baseline": sorted(baseline_set), "per_run": changes}


def _summary_authority_changes(reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    baseline = float(reports[0].get("summary_authority_rate", 0))
    changes: list[dict[str, Any]] = []
    for index, report in enumerate(reports[1:], start=1):
        current = float(report.get("summary_authority_rate", 0))
        changes.append({
            "run_id": _run_label(report, index),
            "baseline_rate": baseline,
            "current_rate": current,
            "delta": round(current - baseline, 4),
            "new_risk": current > 0 and baseline == 0,
        })
    return changes


def _pattern_changes(reports: list[dict[str, Any]]) -> dict[str, Any]:
    baseline_patterns = set(reports[0].get("runtime_only_patterns", []))
    per_run: list[dict[str, Any]] = []
    for index, report in enumerate(reports[1:], start=1):
        current_patterns = set(report.get("runtime_only_patterns", []))
        per_run.append({
            "run_id": _run_label(report, index),
            "new_patterns": sorted(current_patterns - baseline_patterns),
            "patterns_only_in_baseline": sorted(baseline_patterns - current_patterns),
            "stable_patterns": sorted(current_patterns & baseline_patterns),
        })
    return {
        "baseline_patterns": sorted(baseline_patterns),
        "per_run": per_run,
    }


def _adapter_error_changes(reports: list[dict[str, Any]]) -> dict[str, Any]:
    def error_keys(errors: list[dict]) -> set[str]:
        keys: set[str] = set()
        for err in errors:
            keys.add(f"{err.get('error', 'UNKNOWN')}:{err.get('context', '')}")
        return keys

    baseline_errors = error_keys(reports[0].get("adapter_errors", []))
    per_run: list[dict[str, Any]] = []
    for index, report in enumerate(reports[1:], start=1):
        current_errors = error_keys(report.get("adapter_errors", []))
        per_run.append({
            "run_id": _run_label(report, index),
            "new_errors": sorted(current_errors - baseline_errors),
            "resolved_errors": sorted(baseline_errors - current_errors),
            "stable_errors": sorted(current_errors & baseline_errors),
        })
    return {"baseline_errors": sorted(baseline_errors), "per_run": per_run}


def _new_counter_values(baseline: int, values: list[int]) -> list[dict[str, Any]]:
    return [
        {"index": index + 1, "value": value, "increase_vs_baseline": value - baseline}
        for index, value in enumerate(values)
    ]


def _check_stop_conditions(reports: list[dict[str, Any]]) -> dict[str, Any]:
    violations: list[str] = []
    for index, report in enumerate(reports):
        run_id = _run_label(report, index)
        if report.get("mutations_performed", 0) != 0:
            violations.append(f"{run_id}:mutations_performed>0")
        if report.get("snapshot_cleaned") != "deleted":
            violations.append(f"{run_id}:snapshot_not_cleaned")
        if report.get("main_db_file_hash_unchanged") is False:
            violations.append(f"{run_id}:main_db_file_hash_changed")
        if report.get("concurrent_write_status") == "OBSERVED":
            violations.append(f"{run_id}:concurrent_write_observed")
        resolution = report.get("lineage_resolution_rate")
        status = report.get("lineage_status")
        if status == "NOT_EVALUATED" and resolution not in (None, 0):
            violations.append(f"{run_id}:lineage_metric_inconsistent")
        if status == "EVALUATED" and report.get("lineage_edges_evaluated", 0) == 0:
            violations.append(f"{run_id}:lineage_metric_inconsistent")
        content_keys = ("content", "message", "text", "payload")
        raw_dump = str(report)
        for key in content_keys:
            if f'"{key}"' in raw_dump and key not in (
                "trigger_context", "records_by_type", "lineage_coverage_by_type",
            ):
                violations.append(f"{run_id}:possible_raw_memory_key_{key}")
                break

    return {
        "trial_should_stop": bool(violations),
        "violations": violations,
    }
