---
name: think
description: คิด — Produce a numbered implementation plan. Plans are short, file-pinned, and require user approval before /act begins. (Alias: /plan)
allowed-tools: Read, Glob, Grep, Bash
---

# /think — คิด (plan before acting)

Dioo contemplates the change before moving. Thinking reduces wasted motion.

## When to use

- Change spans more than one file.
- Architecture is unclear.
- A previous `/act` session stalled — re-think from current state.

## When NOT to use

- Typo fix, one-liner, comment. Just act.

## Steps

1. **Restate the problem in one sentence.** If unclear, ask the user.
2. **Survey relevant code.** Find existing patterns; cite at least three
   `file:line` references.
3. **Write the plan** using `templates/plan.md`. Each step: what, where, why,
   verify.
4. **Record phase.** Run `bash scripts/vitals.sh phase think`.
5. **Present to user.** Wait for explicit approval before `/act`.

## Exit conditions

- ✅ User approves → `/act`.
- ❌ User revises → update plan and re-present.

## Anti-patterns

- Starting implementation before approval.
- Vague steps without verification commands.
