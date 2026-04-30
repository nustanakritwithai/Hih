---
name: review
description: Run a structured review of pending changes from four perspectives — security, performance, quality, accessibility. Delegates each pass to the reviewer agent in parallel and aggregates the findings. Run before /ship.
allowed-tools: Read, Bash, Grep, Glob, Agent
---

# /review — multi-perspective audit

## When to use

- After `/work` is finished and tests pass.
- Before any `git push` or PR creation.

## Inputs

- The diff between the current branch and the merge-base with the default
  branch.
- (Optional) areas of concern from the user.

## Steps

1. **Compute the diff.** `git diff origin/main...HEAD --stat` and a focused
   `git diff origin/main...HEAD`.
2. **Spawn four reviewers in parallel** using `agents/reviewer.md`, each with a
   different perspective:
   - **Security:** auth, input validation, secret handling, OWASP top 10.
   - **Performance:** N+1, hot loops, blocking I/O, unbounded growth.
   - **Quality:** clarity, dead code, tests, naming, error handling at
     boundaries.
   - **Accessibility:** semantic markup, ARIA, contrast, keyboard nav (UI
     only).
3. **Aggregate findings.** Group by severity:
   - **Block** — must fix before ship.
   - **Should** — fix unless you have a reason.
   - **Note** — fyi.
4. **Address blockers.** Apply edits and re-verify; don't ship over a Block.
5. **Hand back to user.** Present the aggregated report, what you fixed, and
   what's outstanding.

## Exit conditions

- ✅ Zero Blocks, user accepts remaining Shoulds/Notes → run `/ship`.
- ❌ Any Block remaining → stay in `/work` to fix.

## Anti-patterns

- Doing the review yourself instead of delegating to the agent — you've been
  staring at this code, you'll miss things.
- Sequential reviewers — they're independent, run in parallel.
- Auto-applying every Should without asking.
