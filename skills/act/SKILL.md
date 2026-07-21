---
name: act
description: กระทำ — Execute an approved plan. One step at a time with TodoWrite, reflex hooks enforcing safety, tests after each change. (Alias: /work)
allowed-tools: Read, Edit, Write, Bash, Glob, Grep, TodoWrite
---

# /act — กระทำ (execute the plan)

Dioo acts on approved intention. Each action is deliberate and verified.

## Preconditions

- Plan exists and was approved.
- Working tree is clean or changes are intentional.

## Steps

1. **Mirror plan into TodoWrite.** One todo per step.
2. **Exactly one `in_progress` todo** at a time.
3. **Edit, don't recreate.** `Edit` existing files; `Write` only for new files
   the plan requires.
4. **Verify after each step.** Run the plan's verify command. On failure, fix
   root cause; if the plan must change, stop and re-think.
5. **Mark complete immediately** when verification passes.
6. **Record phase.** Run `bash scripts/vitals.sh phase act` at start.

## Hook interactions

- `pretool.sh` block = hard stop. Never bypass.
- `postwrite.sh` secret warning = investigate before continuing.

## Exit conditions

- ✅ All todos complete, checks pass → `/reflect`.
- ❌ Any check red → stay in `/act`.

## Anti-patterns

- Multiple todos in progress.
- Skipping verification.
- Scope creep beyond the plan.
