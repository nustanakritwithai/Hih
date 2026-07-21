#!/usr/bin/env bash
# hooks/prewrite.sh — fired before Write/Edit. Blocks writes to credential files.
set -euo pipefail

input="${1:-}"
if [[ -z "$input" && ! -t 0 ]]; then
  payload="$(cat || true)"
  input="$(printf '%s' "$payload" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n1)"
fi

path="${input:-}"
[[ -z "$path" ]] && exit 0

block() { echo "[hih:R05] BLOCKED writing $path: $*" >&2; exit 2; }

case "$path" in
  *.env|*.env.*|*.pem|*id_rsa|*id_rsa.pub|*credentials.json|*secrets.yaml|*secrets.yml)
    block "credential / secret file"
    ;;
esac

exit 0
