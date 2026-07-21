#!/usr/bin/env bash
# tests/test_life_engine.sh — smoke tests for Life Engine MVP
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DB="/tmp/dioo-life-test.db"
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

echo "life_engine init"
python3 -m life_engine --db "$DB" init >/dev/null
assert "init creates being" "python3 -m life_engine --db '$DB' status | grep -q dioo-001"

echo "life_engine event cycle"
python3 -m life_engine --db "$DB" event "อธิบาย Life Engine" >/dev/null
assert "event increases memory count" "python3 -m life_engine --db '$DB' status | grep -q episodic_memories"

echo "life_engine goals/concerns"
python3 -m life_engine --db "$DB" goal "ทดสอบเป้าหมาย" >/dev/null
python3 -m life_engine --db "$DB" concern "ทดสอบ concern" >/dev/null
assert "context includes goals" "python3 -m life_engine --db '$DB' context | grep -q active_goals"

echo "life_engine stability"
python3 -m life_engine --db "$DB" event "ขอบคุณมาก เข้าใจแล้ว" >/dev/null
assert "trust stays bounded" "python3 -c \"
import json, subprocess
out = subprocess.check_output(['python3','-m','life_engine','--db','$DB','status'])
data = json.loads(out)
trust = data['state']['social']['trust']
assert 0 <= trust <= 1, trust
\""

echo
echo "$pass passed, $fail failed"
rm -f "$DB"
exit "$fail"
