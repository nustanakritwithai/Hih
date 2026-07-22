"""CLI for read-only memory auditor."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from memory_auditor.auditor import ReadOnlyMemoryAuditor


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dioo Read-Only Memory Auditor")
    parser.add_argument("fixture", help="Path to fixture JSON")
    parser.add_argument("--compression-summary", default=None, help="Optional summary to analyze")
    parser.add_argument("--output", "-o", default=None, help="Write report JSON to file")
    args = parser.parse_args(argv)

    auditor = ReadOnlyMemoryAuditor()
    records, edges, meta = auditor.load_fixture(args.fixture)
    report = auditor.audit(
        records,
        explicit_edges=edges,
        compression_summary=args.compression_summary or meta.get("compression_summary"),
    )

    out = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
    else:
        print(out)

    if report.get("mode") == "FAILED_READ_ONLY_GUARANTEE":
        return 2
    if report.get("mutations_performed", 0) != 0:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
