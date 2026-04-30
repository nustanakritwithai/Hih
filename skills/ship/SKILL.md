---
name: ship
description: Stage changes, write a conventional commit, push to the current branch, and (on user request) open a pull request. Refuses to ship over open Blocks from /review or a dirty working tree of unrelated files.
allowed-tools: Read, Bash, Grep
---

# /ship — commit, push, PR

## When to use

- After `/review` returns clean.
- To push WIP for collaboration (in which case prefix the commit with `wip:`).

## Preconditions

- `/review` complete with zero Blocks.
- Working tree is staged with intentional changes only — review `git status`
  before staging.

## Steps

1. **Read the state.** Run in parallel:
   - `git status`
   - `git diff --staged`
   - `git diff`
   - `git log --oneline -5`
2. **Stage intentionally.** Add files by name. Never `git add -A` blindly —
   you'll grab editor cruft or local config.
3. **Write the commit message.** Conventional style:
   ```
   <type>(<scope>): <subject>

   <body explaining why, not what>
   ```
   Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `wip`.
   Subject ≤ 70 chars; imperative mood.
4. **Commit.** Use a heredoc so newlines survive:
   ```sh
   git commit -m "$(cat <<'EOF'
   <message>
   EOF
   )"
   ```
   Never `--no-verify`. If a hook fails, fix the underlying issue.
5. **Push.** `git push -u origin <current-branch>`. Retry up to 4× with
   exponential backoff (2s, 4s, 8s, 16s) on network errors only — not on
   policy errors.
6. **PR (only if asked).** `mcp__github__create_pull_request` with a title
   under 70 chars and a body containing Summary + Test plan.

## Exit conditions

- ✅ Push succeeded → state the branch and commit hash.
- ❌ Push rejected → diagnose; never force-push to a protected branch.

## Anti-patterns

- `git add -A` / `git add .` at repo root.
- `--amend` on a published commit.
- Force-push to `main`/`master`/`release`.
- Skipping verification with `--no-verify`.
- Opening a PR the user did not request.
