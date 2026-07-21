"""Self-Evolution Engine CLI — Phase E1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from evolution.boundaries import check_boundary
from evolution.engine import EvolutionEngine
from evolution.redaction import redact_text


def load_baseline_cases() -> list[dict]:
    path = Path("evals/baseline/cases.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["cases"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dioo Self-Evolution Engine — Phase E1")
    parser.add_argument("--db", default="state/dioo.db")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Initialize evolution schema + skill registry")
    sub.add_parser("dashboard", help="Show evolution status dashboard")
    sub.add_parser("seed-baseline", help="Seed 20 baseline eval cases")
    sub.add_parser("run-baseline", help="Run baseline evaluation suite")
    sub.add_parser("snapshot", help="Create stable DB snapshot")
    snap = sub.add_parser("snapshot-candidate", help="Create candidate DB snapshot")
    snap.add_argument("--notes", default="candidate")

    recover = sub.add_parser("recover", help="Restore DB from snapshot")
    recover.add_argument("snapshot_id")

    sub.add_parser("check-corruption", help="Detect DB corruption")
    sub.add_parser("rollback-test", help="Verify snapshot restore integrity")

    record = sub.add_parser("record", help="Record task trajectory + evaluate")
    record.add_argument("objective")
    record.add_argument("--status", default="success", choices=["success", "partial", "failure"])
    record.add_argument("--being", default="dioo-001")

    check = sub.add_parser("check-boundary", help="Test immutable boundary")
    check.add_argument("action")

    args = parser.parse_args(argv)
    engine = EvolutionEngine(args.db)

    try:
        if args.command == "init":
            engine.seed_skill_registry()
            print(json.dumps({"status": "initialized", "phase": "E1"}, indent=2))
            return 0

        if args.command == "dashboard":
            print(engine.dashboard_text())
            print()
            print(json.dumps(engine.dashboard(), ensure_ascii=False, indent=2))
            return 0

        if args.command == "seed-baseline":
            cases = load_baseline_cases()
            n = engine.seed_baseline_cases(cases)
            print(json.dumps({"seeded": n, "total_cases": len(cases)}, indent=2))
            return 0

        if args.command == "run-baseline":
            result = engine.run_baseline_suite()
            print(json.dumps({
                "total": result["total"],
                "passed": result["passed"],
                "failed": result["failed"],
                "pass_rate": round(result["passed"] / max(result["total"], 1), 2),
            }, indent=2))
            return 0 if result["failed"] == 0 else 1

        if args.command == "snapshot":
            sid = engine.persistence.create_snapshot(engine.conn, "stable", "manual")
            engine.conn.commit()
            print(json.dumps({"snapshot_id": sid}, indent=2))
            return 0

        if args.command == "snapshot-candidate":
            sid = engine.create_candidate_snapshot(args.notes)
            engine.conn.commit()
            print(json.dumps({"snapshot_id": sid, "type": "candidate"}, indent=2))
            return 0

        if args.command == "recover":
            result = engine.recover(args.snapshot_id)
            print(json.dumps(result, indent=2))
            return 0

        if args.command == "check-corruption":
            print(json.dumps(engine.check_corruption(), indent=2))
            return 0

        if args.command == "rollback-test":
            result = engine.rollback_test()
            print(json.dumps(result, indent=2))
            return 0 if result["passed"] else 1

        if args.command == "record":
            result = engine.record_task_cycle(
                args.being, redact_text(args.objective), result_status=args.status,
            )
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
            return 0

        if args.command == "check-boundary":
            result = check_boundary(args.action)
            print(json.dumps(result, indent=2))
            return 0 if result["allowed"] else 2

    finally:
        engine.close()

    return 1


if __name__ == "__main__":
    sys.exit(main())
