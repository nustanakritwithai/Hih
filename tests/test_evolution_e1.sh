#!/usr/bin/env bash
# tests/test_evolution_e1.sh — Phase E1 Self-Evolution tests
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DB="/tmp/dioo-evolution-test.db"
rm -f "$DB" /tmp/dioo-evolution-test.db.pre_restore

pass=0
fail=0
green=$'\033[32m'
red=$'\033[31m'
reset=$'\033[0m'

assert() {
  local desc="$1" cmd="$2"
  if eval "$cmd" >/dev/null 2>&1; then
    printf "  ${green}ok${reset}   %s\n" "$desc"
    pass=$((pass + 1))
  else
    printf "  ${red}FAIL${reset} %s\n" "$desc"
    fail=$((fail + 1))
  fi
}

echo "evolution init"
python3 -m evolution --db "$DB" init >/dev/null
assert "schema initialized" "python3 -m evolution --db '$DB' dashboard | grep -q Self-Evolution"

echo "immutable boundaries"
assert "block merge stable" "python3 -m evolution --db '$DB' check-boundary merge_stable_branch; test \$? -eq 2"
assert "block threshold" "python3 -m evolution --db '$DB' check-boundary lower_pass_threshold; test \$? -eq 2"
assert "allow record" "python3 -m evolution --db '$DB' check-boundary record_trajectory; test \$? -eq 0"

echo "trajectory + evaluation"
python3 -m evolution --db "$DB" record "test task E1" --status success >/dev/null
assert "trajectory recorded" "python3 -m evolution --db '$DB' dashboard | grep -q 'Trajectories: 1'"

echo "baseline eval set"
python3 -m evolution --db "$DB" seed-baseline >/dev/null
assert "20 cases seeded" "python3 -m evolution --db '$DB' dashboard | grep -qi 'eval cases: 20'"

python3 -m evolution --db "$DB" run-baseline >/dev/null
assert "baseline suite passes" "python3 -m evolution --db '$DB' run-baseline | grep -q '\"failed\": 0'"

echo "failure + proposal on failed task"
python3 -m evolution --db "$DB" record "failed task" --status failure >/dev/null
assert "failure recorded" "python3 -m evolution --db '$DB' dashboard | grep -q 'Open failures'"
assert "proposal created" "python3 -c \"
import sqlite3
c=sqlite3.connect('$DB')
assert c.execute('select count(*) from proposals').fetchone()[0] >= 1
\""

echo "persistence + recovery"
python3 -m evolution --db "$DB" rollback-test >/dev/null
assert "rollback test passes" "python3 -m evolution --db '$DB' rollback-test | grep -q '\"passed\": true'"
assert "corruption check healthy" "python3 -m evolution --db '$DB' check-corruption | grep -q '\"healthy\": true'"

echo "snapshot"
python3 -m evolution --db "$DB" snapshot >/dev/null
assert "snapshot created" "test -d state/snapshots || test -f /tmp/*.db || python3 -c \"
import sqlite3
c=sqlite3.connect('$DB')
assert c.execute('select count(*) from evolution_snapshots').fetchone()[0] >= 1
\""

echo "secret redaction"
assert "redacts api key" "python3 -c \"
from evolution.redaction import redact_text
assert '[REDACTED]' in redact_text('api_key=secret123')
\""

echo
echo "$pass passed, $fail failed"
rm -f "$DB"
exit "$fail"
