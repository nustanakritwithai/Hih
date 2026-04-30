# Architecture

Hih is intentionally small. There is no daemon, no compiled engine — just shell
hooks, markdown skills, and markdown agents. Claude Code is the runtime.

## Layers

```
┌──────────────────────────────────────────────────────────┐
│                       Claude Code                        │
│                  (model + tool runtime)                  │
└────────────────┬─────────────────────────┬───────────────┘
                 │ tool calls              │ skill / agent loads
                 ▼                         ▼
┌────────────────────────────┐ ┌──────────────────────────┐
│   hooks/  (shell scripts)  │ │ skills/, agents/         │
│   guardrails R01..R10      │ │ markdown contracts       │
└────────────────────────────┘ └──────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────┐
│                       harness.toml                       │
│   declarative config: protected branches, rule toggles   │
└──────────────────────────────────────────────────────────┘
```

## Why shell?

- Zero install. Every dev box has bash.
- Hooks must be fast. A 5-line shell script runs in <10ms.
- Inspectable. A reviewer can read every guardrail in one sitting.

## Why markdown skills/agents?

- Claude Code natively loads them.
- Diffs are reviewable in PRs.
- No build step.

## Extending the harness

- **Add a guardrail:** new rule ID + matcher in `hooks/pretool.sh`, toggle in
  `harness.toml`, test in `tests/pretool.bats` (or add a plain `tests/run.sh`
  case).
- **Add a verb:** new `skills/<verb>/SKILL.md`, mirror under `.claude/skills/`,
  add to `harness.toml` `[harness] loop`.
- **Add an agent:** new `agents/<name>.md`, mirror under `.claude/agents/`.
