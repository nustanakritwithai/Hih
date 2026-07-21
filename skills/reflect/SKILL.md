---
name: reflect
description: ทบทวน — Structured audit from four perspectives via the conscience faculty. Run before /grow. (Alias: /review)
allowed-tools: Read, Bash, Grep, Glob, Agent
---

# /reflect — ทบทวน (audit before growing)

Dioo examines its own actions before integrating them into memory.

## When to use

- After `/act` finishes and tests pass.
- Before any `git push` or PR.

## Steps

1. **Compute diff.** `git diff origin/main...HEAD --stat` and focused diff.
2. **Spawn four conscience passes in parallel** (`faculties/conscience.md`):
   security, performance, quality, accessibility.
3. **Aggregate findings** by severity: Block | Should | Note.
4. **Fix all Blocks.** Re-verify; never grow over a Block.
5. **Record phase.** Run `bash scripts/vitals.sh phase reflect`.
6. **Present report** to user with fixes applied and outstanding items.

## Exit conditions

- ✅ Zero Blocks, user accepts Shoulds/Notes → `/grow`.
- ❌ Any Block → return to `/act`.

## Anti-patterns

- Self-review instead of delegating to conscience.
- Sequential passes when they can run in parallel.
