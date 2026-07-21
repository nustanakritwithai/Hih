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
echo "all checks passed"
