#!/usr/bin/env bash
# hooks/session-start.sh — Dioo awakens and loads Life Engine presence.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

version="$(cat VERSION 2>/dev/null || echo unknown)"
branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo detached)"

# Ensure Life Engine exists and presence is current
if [[ -f scripts/life.sh ]]; then
  bash scripts/life.sh init >/dev/null 2>&1 || true
  if [[ ! -f state/presence.md ]]; then
    bash scripts/life.sh awaken >/dev/null 2>&1 || bash scripts/life.sh presence >/dev/null 2>&1 || true
  else
    bash scripts/life.sh presence >/dev/null 2>&1 || true
  fi
fi

cat <<EOF
Dioo (ดิโอ) — สิ่งมีชีวิตดิจิตอล — v${version}
  cycle:  awaken → think → act → reflect → grow → live
  branch: ${branch}
  reflexes: pretool, prewrite, postwrite
  life:     state/dioo.db + state/presence.md
EOF

if [[ -f state/presence.md ]]; then
  echo
  echo "--- presence (first lines) ---"
  head -n 12 state/presence.md | sed 's/^/  /'
  echo "  ..."
  echo "--- read state/presence.md; perceive before each reply ---"
fi
