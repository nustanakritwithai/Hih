#!/usr/bin/env bash
# hooks/postwrite.sh — fired after Write/Edit. Scans the touched file for
# obvious secret leakage and emits a warning (non-blocking).
set -euo pipefail

input="${1:-}"
if [[ -z "$input" && ! -t 0 ]]; then
  payload="$(cat || true)"
  input="$(printf '%s' "$payload" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n1)"
fi

path="${input:-}"
[[ -z "$path" || ! -f "$path" ]] && exit 0

# Skip binary files cheaply.
if file --mime-encoding "$path" 2>/dev/null | grep -qi binary; then
  exit 0
fi

# Patterns that almost always indicate a leaked secret.
patterns=(
  'AKIA[0-9A-Z]{16}'                        # AWS access key id
  'aws_secret_access_key[[:space:]]*='      # AWS secret
  'gh[pousr]_[A-Za-z0-9]{30,}'              # GitHub token
  'sk-[A-Za-z0-9_-]{30,}'                   # OpenAI / Anthropic-shape token
  '-----BEGIN [A-Z ]*PRIVATE KEY-----'      # PEM private key
)

found=0
for pat in "${patterns[@]}"; do
  if grep -EnI "$pat" "$path" >/dev/null 2>&1; then
    echo "[hih:secret-scan] possible secret in $path matching /$pat/" >&2
    found=1
  fi
done

# Warning only — don't fail the tool call. Claude can react to stderr.
exit 0
