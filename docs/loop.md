# The loop, in practice

A worked example of one full pass through `setup → plan → work → review → ship`.

## Scenario

> "Add a `/healthz` endpoint that returns the build SHA and uptime."

## /setup (skipped — already done in this repo)

`CLAUDE.md` already records: Node 20, pnpm, Vitest, ESLint, Prettier.

## /plan

```
Plan: /healthz endpoint

Problem: ops needs a liveness check that also identifies the deployed SHA.

Branch: feat/healthz

Context:
- src/server.ts:34 — Express app wiring; existing routes registered here.
- src/build-info.ts:1 — already exposes BUILD_SHA from the bundler define.
- tests/server.test.ts:12 — pattern for route tests.

Steps:
1. Add a health module
   - What: export a handler that returns { sha, uptimeSec }.
   - Where: src/health.ts (new).
   - Why: keeps server.ts thin.
   - Verify: import and call it in a unit test, expect both fields.

2. Wire it into the server
   - What: app.get('/healthz', healthHandler).
   - Where: src/server.ts:34.
   - Why: matches existing route registration pattern.
   - Verify: vitest tests/server.test.ts -t healthz.

Considered alternatives:
- Inline the handler in server.ts — rejected; would grow with more health checks.
```

User says "go".

## /work

TodoWrite:
1. ⏳ Add `src/health.ts`
2. ⬜ Wire in `src/server.ts`
3. ⬜ Add `tests/server.test.ts` case

Step 1: write the file, run vitest on the new test, green. Mark done.
Step 2: edit `server.ts:34`, run integration test, green. Mark done.
Step 3: covered by step 2's test. Remove from list.

## /review

Spawn 4 reviewers in parallel:
- **security**: no findings.
- **performance**: Note — `process.uptime()` is fine; no issue.
- **quality**: Should — `uptimeSec` should be an integer, not float.
- **accessibility**: not applicable.

Apply the Should fix (`Math.floor`). Re-run tests. Green.

## /ship

```sh
git add src/health.ts src/server.ts tests/server.test.ts
git commit -m "feat(server): add /healthz endpoint with sha and uptime"
git push -u origin feat/healthz
```

Done. PR opened on user request.
