#!/usr/bin/env bash
# scripts/life.sh — Life Engine CLI wrapper
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
exec python3 -m life_engine "$@"
