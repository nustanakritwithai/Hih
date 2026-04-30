---
name: work
description: Execute an approved plan. One step at a time, with TodoWrite tracking progress, hooks enforcing safety, and tests run after every meaningful change. Stops and asks if reality diverges from the plan.
allowed-tools: Read, Edit, Write, Bash, Glob, Grep, TodoWrite
---

# /work — execute the plan

## When to use

- Immediately after `/plan` is approved.
- To resume a half-finished task: re-read the plan, then continue.

## Preconditions

- A plan exists and was approved.
- Working tree is clean OR the in-progress changes are intentional.

## Steps

1. **Mirror the plan into TodoWrite.** One todo per plan step.
2. **Promote one todo to `in_progress`.** Exactly one. Always.
3. **Edit, don't recreate.** Use `Edit` for existing files. `Write` only for
   new files the plan calls for.
4. **Run the verification.** After each step, run the test/lint/manual check
   from the plan's "Verify" line. If it fails:
   - Fix the root cause, don't paper over it.
   - If the fix changes the plan, stop and surface to the user.
5. **Mark complete and move on.** Mark the todo `completed` the instant the
   verification passes — don't batch.
6. **Diverge cleanly.** If you discover the plan is wrong, stop. Don't drift.
   Tell the user, propose a revised plan.

## Hook interactions

- A `pretool.sh` block is a hard stop. Do not work around it.
- A `postwrite.sh` secret-scan warning is a soft stop. Investigate before
  continuing.

## Exit conditions

- ✅ All todos complete, all checks pass → run `/review`.
- ❌ Any check still red → stay in `/work`.

## Anti-patterns

- Multiple todos in `in_progress`.
- Skipping verification "just for this one step".
- Adding scope ("while I'm here, let me also..."). The plan is the contract.
