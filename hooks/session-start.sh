#!/usr/bin/env bash
# hooks/session-start.sh — runs once when a Claude Code session starts.
# Prints a banner so the user (and Claude) know the harness is active.
set -euo pipefail

version="$(cat VERSION 2>/dev/null || echo unknown)"
branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo detached)"

cat <<EOF
hih harness active — v${version}
  loop:   setup → plan → work → review → ship
  branch: ${branch}
  hooks:  pretool, prewrite, postwrite
EOF
