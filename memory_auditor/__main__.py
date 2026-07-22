"""CLI for read-only memory auditor."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from memory_auditor.auditor import ReadOnlyMemoryAuditor
from memory_auditor.compare_runs import compare_shadow_runs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dioo Read-Only Memory Auditor")
    sub = parser.add_subparsers(dest="command", required=True)

    fixture_p = sub.add_parser("fixture", help="Audit a fixture JSON file")
    fixture_p.add_argument("path", help="Fixture path")
    fixture_p.add_argument("--compression-summary", default=None)
    fixture_p.add_argument("--output", "-o", default=None)

    runtime_p = sub.add_parser("runtime", help="Read-only audit of Life Engine DB snapshot")
    runtime_p.add_argument("--db", default="state/dioo.db", help="Source DB path (read-only snapshot)")
    runtime_p.add_argument("--being-id", default="dioo-001")
    runtime_p.add_argument("--output", "-o", default=None)

    compare_p = sub.add_parser("compare", help="Compare fixture vs runtime snapshot")
    compare_p.add_argument("fixture", help="Fixture path")
    compare_p.add_argument("--db", default="state/dioo.db")
    compare_p.add_argument("--being-id", default="dioo-001")
    compare_p.add_argument("--output", "-o", default=None)

    sanitized_p = sub.add_parser(
        "runtime-sanitized",
        help="Sanitized aggregate-only runtime audit (no raw memory)",
    )
    sanitized_p.add_argument("--db", default="state/dioo.db")
    sanitized_p.add_argument("--being-id", default="dioo-001")
    sanitized_p.add_argument("--fixture", default=None, help="Optional fixture for gap analysis")
    sanitized_p.add_argument("--run-id", default=None, help="Manual shadow audit run identifier")
    sanitized_p.add_argument("--trigger-context", default=None, help="Human-readable trigger context")
    sanitized_p.add_argument("--output", "-o", default=None)

    compare_runs_p = sub.add_parser(
        "compare-runs",
        help="Compare sanitized manual shadow audit reports (read-only)",
    )
    compare_runs_p.add_argument(
        "reports",
        nargs="+",
        help="Sanitized report JSON paths in chronological order",
    )
    compare_runs_p.add_argument("--baseline-index", type=int, default=0)
    compare_runs_p.add_argument("--output", "-o", default=None)

    args = parser.parse_args(argv)
    auditor = ReadOnlyMemoryAuditor()

    if args.command == "fixture":
        records, edges, meta = auditor.load_fixture(args.path)
        report = auditor.audit(
            records,
            explicit_edges=edges,
            compression_summary=args.compression_summary or meta.get("compression_summary"),
            audit_source="fixture",
        )
    elif args.command == "runtime":
        report = auditor.audit_runtime(args.db, args.being_id)
    elif args.command == "runtime-sanitized":
        report = auditor.audit_runtime_sanitized(
            args.db,
            args.being_id,
            fixture_path=args.fixture,
            run_id=args.run_id,
            trigger_context=args.trigger_context,
        )
    elif args.command == "compare-runs":
        loaded = [json.loads(Path(path).read_text(encoding="utf-8")) for path in args.reports]
        report = compare_shadow_runs(loaded, baseline_index=args.baseline_index)
    else:
        report = auditor.compare_fixture_runtime(args.fixture, args.db, args.being_id)

    out = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
    else:
        print(out)

    mutations = report.get("mutations_performed", 0)
    if report.get("mode") == "FAILED_READ_ONLY_GUARANTEE" or mutations != 0:
        return 2
    if report.get("stop_conditions", {}).get("trial_should_stop"):
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
