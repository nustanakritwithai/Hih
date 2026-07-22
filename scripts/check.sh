#!/usr/bin/env bash
# scripts/check.sh — convenience entry point that runs the hook test suite
# plus a couple of self-checks (settings.json parses, hooks are executable).
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> hook test suite"
bash tests/run.sh

echo
echo "==> .claude/settings.json parses"
python3 -c "import json,sys; json.load(open('.claude/settings.json'))" \
  && echo "  ok"

echo
echo "==> hooks executable"
for f in hooks/*.sh; do
  if [[ ! -x "$f" ]]; then
    echo "  FAIL $f is not executable"
    exit 1
  fi
done
echo "  ok"

echo
echo "==> life engine tests"
bash tests/test_life_engine.sh

echo
echo "==> evolution E1 tests"
bash tests/test_evolution_e1.sh

echo
echo "==> evolution E2 tests"
bash tests/test_evolution_e2.sh

echo
echo "==> evolution E3 tests"
bash tests/test_evolution_e3.sh

echo
echo "==> creator delegation tests"
bash tests/test_creator_delegation.sh

echo
echo "==> memory auditor M1 tests"
bash tests/test_memory_auditor.sh

echo
echo "==> memory auditor M2 tests"
python3 tests/test_memory_auditor_m2.py

echo
echo "all checks passed"
