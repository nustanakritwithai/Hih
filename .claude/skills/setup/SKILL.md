---
name: setup
description: Bootstrap a project for the Hih harness. Detects the language stack, captures conventions in CLAUDE.md, ensures dev dependencies are present, and confirms hooks are wired. Run this once per repo, or after a major dependency change.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# /setup — bootstrap the harness

## When to use

- First time using Hih in a repo.
- Stack changed (e.g. switched from CRA to Vite, added a Python service).
- `CLAUDE.md` is missing or stale.

## Inputs

- The repository root.
- (Optional) user note about constraints to capture.

## Steps

1. **Inventory the stack.** Detect package managers and frameworks by checking
   for `package.json`, `pnpm-lock.yaml`, `pyproject.toml`, `go.mod`,
   `Cargo.toml`, `Gemfile`, `composer.json`. Record findings.
2. **Read existing conventions.** If `CLAUDE.md`, `.editorconfig`,
   `.prettierrc`, `eslint.config.*`, `ruff.toml`, `pyproject.toml [tool.*]`
   exist, summarize them.
3. **Verify dev tooling.** For each detected stack, list the test command,
   linter, and formatter. If any are missing, propose adding them — do NOT
   install without user approval.
4. **Wire hooks.** Confirm `.claude/settings.json` references `hooks/*.sh` and
   that the scripts are executable. Run `bash hooks/pretool.sh "echo ok"` as a
   smoke test.
5. **Update CLAUDE.md.** Append (don't overwrite) a `## Conventions` section
   capturing: test command, lint command, format command, build command,
   target runtime, branch naming, commit style.
6. **Print a checklist.** End with a green/red status of each step.

## Exit conditions

- ✅ All four checks pass → recommend `/plan`.
- ❌ Any check fails → state which one and stop. Do not silently proceed.

## Anti-patterns

- Installing dependencies without confirmation.
- Overwriting an existing `CLAUDE.md`.
- Inferring stack details from file names alone — read the actual config.
