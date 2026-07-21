#!/usr/bin/env bash
# tests/test_evolution_e2.sh — Phase E2 Self-Evolution tests
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DB="/tmp/dioo-evolution-e2-test.db"
rm -f "$DB" state/snapshots/*e2* 2>/dev/null || true

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

echo "evolution E2 init"
python3 -m evolution --db "$DB" init >/dev/null
assert "schema v2 migrated" "python3 -c \"
import sqlite3
c=sqlite3.connect('$DB')
assert c.execute('select version from evolution_schema_version').fetchone()[0] >= 2
\""

echo "belief rules v2"
assert "single evidence capped" "python3 -m evolution --db '$DB' evaluate-belief 'test belief' --confidence 0.9 --evidence-count 1 | grep -q '\"adjusted_confidence\": 0.6'"
assert "multi evidence promotable path" "python3 -m evolution --db '$DB' evaluate-belief 'test belief' --confidence 0.8 --evidence-count 2 | grep -q '\"promotable\": true'"

echo "session reflection v2"
python3 -m evolution --db "$DB" reflect-session --session sess-e2-1 --summary "autonomy test" >/dev/null
assert "reflection recorded" "python3 -c \"
import sqlite3
c=sqlite3.connect('$DB')
assert c.execute('select count(*) from evolution_session_reflections').fetchone()[0] >= 1
\""
python3 -m evolution --db "$DB" reflect-session --session sess-e2-1 >/dev/null 2>&1 || true
assert "second reflection blocked by budget" "python3 -c \"
import sqlite3
c=sqlite3.connect('$DB')
assert c.execute('select count(*) from evolution_session_reflections where session_id=?', ('sess-e2-1',)).fetchone()[0] == 1
\""

echo "sandbox experiment pipeline"
python3 -m evolution --db "$DB" seed-baseline >/dev/null
python3 -m evolution --db "$DB" record "failed for proposal" --status failure >/dev/null
PROP=$(python3 -c "
import sqlite3, json
c=sqlite3.connect('$DB')
r=c.execute('select proposal_id from proposals limit 1').fetchone()
print(r[0] if r else '')
")
assert "proposal exists" "test -n '$PROP'"
EXP=$(python3 -m evolution --db "$DB" experiment-start "$PROP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('experiment_id',''))")
assert "experiment started" "test -n '$EXP'"
python3 -m evolution --db "$DB" experiment-run "$EXP" >/dev/null
assert "experiment completed" "python3 -c \"
import sqlite3
c=sqlite3.connect('$DB')
assert c.execute('select status from experiments where experiment_id=?', ('$EXP',)).fetchone()[0] == 'completed'
\""

echo "budget limits"
python3 -c "
import sqlite3, json, subprocess
from evolution.util import new_id, now_iso
db = '$DB'
c = sqlite3.connect(db)
ts = now_iso()
# Pipeline already started 1 experiment; start 2 more with unique proposals
for i in range(2):
    pid = new_id('prop')
    c.execute('''INSERT INTO proposals (
        proposal_id, being_id, title, source_failure_ids_json,
        problem_statement, root_cause, root_cause_confidence, hypothesis,
        proposed_change_json, expected_benefits_json, possible_regressions_json,
        identity_risk, permission_risk, safety_risk, complexity,
        evaluation_cases_json, success_criteria_json, rollback_plan,
        status, boundary_status, created_at
    ) VALUES (?, 'dioo-001', ?, '[]', ?, '', 0, '', '{}', '[]', '[]',
        'low','low','low','small','[]','[]','snap', 'draft', 'ok', ?)''',
        (pid, f'budget prop {i}', f'problem {i}', ts))
    c.commit()
    out = subprocess.check_output(['python3','-m','evolution','--db',db,'experiment-start',pid], text=True)
    import json as J
    eid = J.loads(out)['experiment_id']
    subprocess.run(['python3','-m','evolution','--db',db,'experiment-run',eid], check=False, capture_output=True)
pid = new_id('prop')
c.execute('''INSERT INTO proposals (
    proposal_id, being_id, title, source_failure_ids_json,
    problem_statement, root_cause, root_cause_confidence, hypothesis,
    proposed_change_json, expected_benefits_json, possible_regressions_json,
    identity_risk, permission_risk, safety_risk, complexity,
    evaluation_cases_json, success_criteria_json, rollback_plan,
    status, boundary_status, created_at
) VALUES (?, 'dioo-001', 'overflow', '[]', 'overflow', '', 0, '', '{}', '[]', '[]',
    'low','low','low','small','[]','[]','snap', 'draft', 'ok', ?)''', (pid, ts))
c.commit()
open('/tmp/e2-overflow-prop','w').write(pid)
"
OVERFLOW=$(cat /tmp/e2-overflow-prop)
assert "budget pauses after max experiments" "python3 -c \"
import subprocess, sys
r = subprocess.run(['python3','-m','evolution','--db','$DB','experiment-start','$OVERFLOW'], capture_output=True, text=True)
sys.exit(0 if 'PAUSED_BUDGET_LIMIT' in r.stdout else 1)
\""
rm -f /tmp/e2-overflow-prop

echo "dashboard E2 fields"
assert "dashboard shows experiments" "python3 -m evolution --db '$DB' dashboard | grep -qi experiment"

echo
echo "$pass passed, $fail failed"
rm -f "$DB"
exit "$fail"
