#!/usr/bin/env bash
# Manual shadow audit helper — MANUAL_INVOCATION_ONLY, read-only, no lifecycle hook.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

RUN_ID="${1:-}"
TRIGGER_CONTEXT="${2:-manual invocation}"
DB="${DB:-state/dioo.db}"
FIXTURE="${FIXTURE:-memory_auditor/fixtures/rt04.json}"
OUT_DIR="${OUT_DIR:-audit-reports}"

if [[ -z "$RUN_ID" ]]; then
  echo "usage: $0 <run-id> [trigger-context]" >&2
  echo "example: $0 run-001 'baseline after merge'" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"
OUTPUT="$OUT_DIR/manual-shadow-${RUN_ID}.json"

python3 -m memory_auditor runtime-sanitized \
  --db "$DB" \
  --fixture "$FIXTURE" \
  --run-id "$RUN_ID" \
  --trigger-context "$TRIGGER_CONTEXT" \
  -o "$OUTPUT"

echo "wrote $OUTPUT"
python3 -c "import json; r=json.load(open('$OUTPUT')); print('records_scanned=', r.get('records_scanned'), 'mutations=', r.get('mutations_performed'), 'snapshot_cleaned=', r.get('snapshot_cleaned'))"
