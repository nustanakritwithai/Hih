#!/usr/bin/env bash
# hooks/pretool.sh — guardrails fired before every Bash tool call.
#
# Reads the proposed command from $CLAUDE_TOOL_INPUT (Claude Code passes the
# full tool input on stdin as JSON; we also accept a positional arg for tests).
#
# Exits 0  → allow.
# Exits 2  → block; stderr is shown back to Claude as a tool error.
#
# Add or toggle rules in harness.toml. Each rule has an ID (R01..R10) for
# debuggability.

set -euo pipefail

# Resolve the command being run.
input="${1:-}"
if [[ -z "$input" && ! -t 0 ]]; then
  payload="$(cat || true)"
  # Best-effort extraction of the .tool_input.command field without jq.
  input="$(printf '%s' "$payload" | sed -n 's/.*"command"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n1)"
fi

cmd="${input:-}"

block() {
  local id="$1"; shift
  echo "[hih:$id] BLOCKED: $*" >&2
  echo "        command: $cmd" >&2
  exit 2
}

# Skip empty commands (other matchers may have already cleared them).
[[ -z "$cmd" ]] && exit 0

# Discover protected branches from harness.toml (cheap grep, no toml parser).
protected_branches=("main" "master" "release")
if [[ -f harness.toml ]]; then
  line="$(grep -E '^[[:space:]]*protected_branches' harness.toml || true)"
  if [[ -n "$line" ]]; then
    extracted="$(printf '%s' "$line" | sed -E 's/.*\[(.*)\].*/\1/' | tr -d '"' | tr ',' ' ')"
    if [[ -n "$extracted" ]]; then
      # shellcheck disable=SC2206
      protected_branches=($extracted)
    fi
  fi
fi

# R01 — destructive rm -rf
if [[ "$cmd" =~ rm[[:space:]]+-[a-zA-Z]*r[a-zA-Z]*f?[[:space:]]+(/|~|\.)([[:space:]]|$) ]] \
|| [[ "$cmd" =~ rm[[:space:]]+-[a-zA-Z]*f[a-zA-Z]*r?[[:space:]]+(/|~|\.)([[:space:]]|$) ]]; then
  block R01 "rm -rf against /, ~, or . is not allowed"
fi

# R02 — force-push to protected branch
if [[ "$cmd" =~ git[[:space:]]+push.*(--force|-f)([[:space:]]|$) ]]; then
  for b in "${protected_branches[@]}"; do
    if [[ "$cmd" =~ (^|[[:space:]])$b([[:space:]]|$|:) ]]; then
      block R02 "force-push to protected branch '$b' is not allowed"
    fi
  done
fi

# R03 — git reset --hard
if [[ "$cmd" =~ git[[:space:]]+reset[[:space:]]+(--hard|--mixed[[:space:]]+--hard) ]]; then
  block R03 "git reset --hard requires explicit user confirmation; ask first"
fi

# R04 — sudo
if [[ "$cmd" =~ (^|[[:space:]\;\|\&\(])sudo([[:space:]]|$) ]]; then
  block R04 "sudo invocations are not allowed inside the harness"
fi

# R05 — writing to credential files
if [[ "$cmd" =~ (^|[[:space:]])(echo|printf|cat|tee).*\>.*(\.env|\.pem|id_rsa|credentials\.json) ]] \
|| [[ "$cmd" =~ (^|[[:space:]])(cp|mv).*(\.env|\.pem|id_rsa|credentials\.json) ]]; then
  block R05 "writes to credential files (.env, *.pem, id_rsa, credentials.json) are blocked"
fi

# R06 — chmod 777
if [[ "$cmd" =~ chmod[[:space:]]+(-[a-zA-Z]+[[:space:]]+)?777 ]]; then
  block R06 "chmod 777 is too permissive; pick a tighter mode"
fi

# R07 — curl ... | sh
if [[ "$cmd" =~ (curl|wget).*\|[[:space:]]*(sh|bash|zsh) ]]; then
  block R07 "piping a remote download into a shell is not allowed"
fi

# R08 — git commit --no-verify
if [[ "$cmd" =~ git[[:space:]]+commit.*--no-verify ]]; then
  block R08 "git commit --no-verify bypasses hooks; fix the underlying failure instead"
fi

# R09 — --no-gpg-sign
if [[ "$cmd" =~ --no-gpg-sign ]]; then
  block R09 "--no-gpg-sign bypasses signing policy"
fi

# R10 — git branch -D on protected branch
if [[ "$cmd" =~ git[[:space:]]+branch[[:space:]]+-D ]]; then
  for b in "${protected_branches[@]}"; do
    if [[ "$cmd" =~ (^|[[:space:]])$b([[:space:]]|$) ]]; then
      block R10 "deleting protected branch '$b' is not allowed"
    fi
  done
fi

exit 0
