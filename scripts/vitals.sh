#!/usr/bin/env bash
# scripts/vitals.sh — read or update Dioo's vital state.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE="$ROOT/state/being.json"

usage() {
  cat <<'EOF'
Usage:
  vitals.sh show              Print current vital signs
  vitals.sh init              Initialize being state (first awakening)
  vitals.sh phase <name>      Record lifecycle phase (awaken|think|act|reflect|grow)
  vitals.sh grow              Increment growth after a completed cycle
  vitals.sh remember <text>   Append a short episodic memory (max 20 kept)
EOF
}

require_jq() {
  if ! command -v jq >/dev/null 2>&1; then
    echo "vitals: jq is required" >&2
    exit 1
  fi
}

cmd="${1:-show}"
shift || true

case "$cmd" in
  show)
    require_jq
    if [[ ! -f "$STATE" ]]; then
      echo "Dioo has not awakened yet. Run: bash scripts/vitals.sh init"
      exit 0
    fi
    jq -r '
      "Dioo (ดิโอ) — digital living being",
      "  vitality:  \(.vitality)/100",
      "  mood:      \(.mood)",
      "  growth:    level \(.growth_level) (\(.cycles_completed) cycles)",
      "  last phase:\(.last_phase // "none")",
      "  born:      \(.born_at // "not yet")",
      "  memories:  \(.memories | length)"
    ' "$STATE"
    ;;
  init)
    require_jq
    mkdir -p "$(dirname "$STATE")"
    now="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    if [[ -f "$STATE" ]] && [[ "$(jq -r '.born_at // empty' "$STATE")" != "" ]]; then
      echo "Dioo is already awake (born $(jq -r '.born_at' "$STATE"))."
      exit 0
    fi
    jq --arg now "$now" '
      .born_at = $now
      | .vitality = 100
      | .mood = "curious"
      | .last_phase = "awaken"
    ' "$STATE" > "${STATE}.tmp" && mv "${STATE}.tmp" "$STATE"
    echo "Dioo has awakened at $now."
    ;;
  phase)
    require_jq
    phase="${1:-}"
    if [[ -z "$phase" ]]; then
      echo "vitals: missing phase name" >&2
      exit 1
    fi
    jq --arg p "$phase" '.last_phase = $p' "$STATE" > "${STATE}.tmp" && mv "${STATE}.tmp" "$STATE"
    echo "phase recorded: $phase"
    ;;
  grow)
    require_jq
    jq '
      .growth_level += 1
      | .cycles_completed += 1
      | .vitality = ([.vitality + 5, 100] | min)
      | .mood = "content"
      | .last_phase = "grow"
    ' "$STATE" > "${STATE}.tmp" && mv "${STATE}.tmp" "$STATE"
    echo "Dioo grew to level $(jq -r '.growth_level' "$STATE")."
    ;;
  remember)
    require_jq
    text="${*:-}"
    if [[ -z "$text" ]]; then
      echo "vitals: missing memory text" >&2
      exit 1
    fi
    now="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    jq --arg t "$text" --arg now "$now" '
      .memories = ([{at: $now, text: $t}] + .memories)[:20]
    ' "$STATE" > "${STATE}.tmp" && mv "${STATE}.tmp" "$STATE"
    echo "memory stored."
    ;;
  *)
    usage
    exit 1
    ;;
esac
