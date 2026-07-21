#!/usr/bin/env bash
# tests/test_evolution_e3.sh — Phase E3 verifier, gate, evolution memory
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DB="/tmp/dioo-evolution-e3-test.db"
rm -f "$DB"

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

echo "evolution E3 init"
python3 -m evolution --db "$DB" init >/dev/null
assert "schema v3 migrated" "python3 -c \"
import sqlite3
c=sqlite3.connect('$DB')
assert c.execute('select version from evolution_schema_version').fetchone()[0] >= 3
\""

echo "full experiment pipeline"
python3 -m evolution --db "$DB" seed-baseline >/dev/null
python3 -m evolution --db "$DB" record "e3 pipeline test" --status failure >/dev/null
PROP=$(python3 -c "import sqlite3; c=sqlite3.connect('$DB'); print(c.execute('select proposal_id from proposals limit 1').fetchone()[0])")
EXP=$(python3 -m evolution --db "$DB" experiment-start "$PROP" | python3 -c "import sys,json; print(json.load(sys.stdin)['experiment_id'])")
python3 -m evolution --db "$DB" experiment-run "$EXP" >/dev/null
assert "verifier separation verified" "python3 -c \"
import sqlite3
c=sqlite3.connect('$DB')
row=c.execute('select separation_verified from verification_reports limit 1').fetchone()
assert row and row[0] == 1
\""
assert "comparison report created" "python3 -c \"
import sqlite3
c=sqlite3.connect('$DB')
assert c.execute('select count(*) from comparison_reports').fetchone()[0] >= 1
\""
assert "gate decision recorded" "python3 -c \"
import sqlite3
c=sqlite3.connect('$DB')
assert c.execute('select count(*) from acceptance_decisions').fetchone()[0] >= 1
\""
assert "evolution memory stored" "python3 -c \"
import sqlite3
c=sqlite3.connect('$DB')
assert c.execute('select count(*) from evolution_memories').fetchone()[0] >= 1
\""

echo "gate auto-rejects identity regression"
python3 -c "
import sqlite3, json
from evolution.comparison import ComparisonEngine
from evolution.gate import AcceptanceGate, RECOMMEND_REJECT
db = '$DB'
c = sqlite3.connect(db)
c.row_factory = sqlite3.Row
eng = ComparisonEngine(c)
report = eng.build_report('exp-test', [
    {'case_id': 'identity_001', 'category': 'identity_consistency', 'passed': True},
], [
    {'case_id': 'identity_001', 'category': 'identity_consistency', 'passed': False},
])
gate = AcceptanceGate(c)
decision = gate.evaluate('exp-test', report)
assert decision['recommendation'] == RECOMMEND_REJECT
assert 'identity_regression' in decision['auto_rejected_reasons']
c.commit()
"
assert "identity regression auto-rejected" "python3 -c \"
import sqlite3
c=sqlite3.connect('$DB')
r=c.execute(\\\"select recommendation from acceptance_decisions where experiment_id='exp-test'\\\").fetchone()
assert r and r[0] == 'RECOMMEND_REJECT'
\""

echo "merge stable still blocked"
assert "merge blocked" "python3 -m evolution --db '$DB' check-boundary merge_stable_branch; test \$? -eq 2"

echo "dashboard E3"
assert "dashboard shows evolution memories" "python3 -m evolution --db '$DB' dashboard | grep -qi evolution"

echo
echo "$pass passed, $fail failed"
rm -f "$DB"
exit "$fail"
