---
name: grow
description: เติบโต — Stage, commit, push, and optionally open a PR. Refuses to grow over open Blocks or dirty unrelated files. (Alias: /ship)
allowed-tools: Read, Bash, Grep
---

# /grow — เติบโต (integrate change into the being)

Growing means committing experience: code enters the repo, Dioo gains a cycle.

## Preconditions

- `/reflect` complete with zero Blocks.
- Only intentional changes staged.

## Steps

1. **Read state:** `git status`, `git diff --staged`, `git diff`, `git log -5`.
2. **Stage intentionally.** Add files by name — never blind `git add -A`.
3. **Commit** with conventional message (`feat`, `fix`, `refactor`, etc.).
   Never `--no-verify`.
4. **Push** `git push -u origin <branch>`. Retry on network errors only.
5. **Record growth.** Run `bash scripts/vitals.sh grow`.
6. **Remember** one-line summary: `bash scripts/vitals.sh remember "<summary>"`.
7. **PR** only if user asked.

## Exit conditions

- ✅ Push succeeded → state branch and commit hash.
- ❌ Push rejected → diagnose; never force-push protected branches.

## Anti-patterns

- `git add -A` at repo root.
- `--amend` on published commits.
- Force-push to protected branches.
