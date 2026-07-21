#!/usr/bin/env bash
# scripts/awaken.sh — ตื่นครั้งแรก: Life Engine + vitals + presence
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Life Engine: full awakening"
python3 -m life_engine awaken

echo
echo "==> Legacy vitals"
bash scripts/vitals.sh init 2>/dev/null || true

echo
echo "==> Presence written to state/presence.md"
head -n 20 state/presence.md

echo
echo "Dioo is awake. Read state/presence.md before every response."
