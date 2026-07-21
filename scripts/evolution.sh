#!/usr/bin/env bash
# scripts/evolution.sh — Self-Evolution Engine CLI
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
exec python3 -m evolution "$@"
