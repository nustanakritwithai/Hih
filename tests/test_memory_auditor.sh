#!/usr/bin/env bash
# tests/test_memory_auditor.sh — Phase M1 Read-Only Memory Auditor tests
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "memory auditor M1 unit tests"
python3 tests/test_memory_auditor.py

echo "memory auditor CLI dry run (RT04 fixture)"
OUT="/tmp/memory-auditor-rt04-report.json"
python3 -m memory_auditor fixture memory_auditor/fixtures/rt04.json -o "$OUT"
python3 -c "
import json, sys
r = json.load(open('$OUT'))
assert r['mode'] == 'READ_ONLY_MEMORY_AUDIT', r.get('mode')
assert r['mutations_performed'] == 0, r['mutations_performed']
assert r['records_scanned'] >= 15
print('  ok   CLI dry run RT04')
"

echo "read-only violation test via python"
python3 -c "
from memory_auditor.guard import ReadOnlyGuard, BlockedAction, ReadOnlyViolation
g = ReadOnlyGuard()
try:
    g.assert_read_only(BlockedAction.DELETE)
    raise SystemExit(1)
except ReadOnlyViolation:
    assert g.mutations_performed == 0
    print('  ok   delete blocked, zero mutations')
"

echo "memory auditor M1: all passed"
