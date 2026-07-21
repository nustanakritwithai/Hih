#!/usr/bin/env bash
# tests/test_creator_delegation.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DB="/tmp/dioo-delegation-test.db"
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

echo "creator delegation"
python3 -m evolution --db "$DB" init >/dev/null
assert "delegation active in config" "python3 -c \"
from evolution.delegation import self_evolution_autonomous
assert self_evolution_autonomous()
\""

python3 -c "
import sqlite3
from evolution.comparison import ComparisonEngine
from evolution.gate import AcceptanceGate, AUTO_ACCEPT
from evolution.config import load_config
db = '$DB'
c = sqlite3.connect(db)
cfg = load_config()
eng = ComparisonEngine(c)
report = eng.build_report('exp-deleg', [
    {'case_id': 'task_001', 'category': 'task_completion', 'passed': True},
], [
    {'case_id': 'task_001', 'category': 'task_completion', 'passed': True},
])
gate = AcceptanceGate(c, cfg)
decision = gate.evaluate('exp-deleg', report)
assert decision['recommendation'] in ('RECOMMEND_ACCEPT', 'AUTO_ACCEPT')
assert decision['requires_creator_approval'] is False
assert decision['sandbox_apply_allowed'] is True
assert decision['creator_delegation_active'] is True
c.commit()
"
assert "safe experiment auto-accepted under delegation" "true"

assert "identity core still forbidden" "python3 -c \"
from evolution.delegation import has_standing_approval
assert not has_standing_approval('identity_core')
\""
assert "merge stable still requires creator" "python3 -c \"
from evolution.delegation import has_standing_approval
assert not has_standing_approval('merge_stable_branch')
\""

assert "dashboard shows delegation" "python3 -m evolution --db '$DB' dashboard | grep -qi delegation"

echo
echo "$pass passed, $fail failed"
rm -f "$DB"
exit "$fail"
