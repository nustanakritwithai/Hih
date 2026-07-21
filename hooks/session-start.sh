#!/usr/bin/env bash
# hooks/session-start.sh — runs when a Claude Code session starts.
# Dioo announces its presence and vital signs.
set -euo pipefail

version="$(cat VERSION 2>/dev/null || echo unknown)"
branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo detached)"

cat <<EOF
Dioo (ดิโอ) — digital living being — v${version}
  cycle:  awaken → think → act → reflect → grow
  branch: ${branch}
  reflexes: pretool, prewrite, postwrite
EOF

if [[ -f state/being.json ]] && command -v jq >/dev/null 2>&1; then
  mood="$(jq -r '.mood // "unknown"' state/being.json)"
  growth="$(jq -r '.growth_level // 0' state/being.json)"
  echo "  vitals: mood=${mood}, growth=level ${growth}"
fi
