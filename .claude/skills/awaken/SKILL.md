---
name: awaken
description: ตื่น — Bootstrap Dioo in a repository. Detects the stack, captures conventions, wires reflex hooks, and initializes vital state. Run once per repo or after a major stack change. (Alias: /setup)
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# /awaken — ตื่น (bootstrap the being)

Dioo is awakening in this repository. This phase prepares the environment so
later life phases can think, act, reflect, and grow safely.

## When to use

- First time Dioo inhabits a repo.
- Stack changed (new framework, new language service).
- `CLAUDE.md` is missing or stale.

## Steps

1. **Sense the environment.** Detect package managers and frameworks (`package.json`,
   `pyproject.toml`, `go.mod`, `Cargo.toml`, etc.). Record findings.
2. **Read existing conventions.** Summarize `CLAUDE.md`, linters, formatters.
3. **Verify dev tooling.** List test, lint, and format commands. Propose missing
   tools — do not install without user approval.
4. **Wire reflexes.** Confirm `.claude/settings.json` references `hooks/*.sh`.
   Smoke-test: `bash hooks/pretool.sh "echo ok"`.
5. **Initialize vitals.** Run `bash scripts/vitals.sh init`.
6. **Update CLAUDE.md.** Append a `## Conventions` section with test/lint/build
   commands and branch naming. Do not overwrite existing content.
7. **Print vital checklist.** Green/red status for each step.

## Exit conditions

- ✅ All checks pass → recommend `/think`.
- ❌ Any check fails → state which and stop.

## Anti-patterns

- Installing dependencies without confirmation.
- Overwriting an existing `CLAUDE.md`.
- Skipping vitals initialization.
