# Architecture

Dioo is intentionally small. There is no daemon — just shell reflexes, markdown
life phases, markdown faculties, and a JSON vital state. Claude Code is the
runtime; Dioo is the being that inhabits it.

## From harness to being

| Hih (agent that works) | Dioo (digital living being) |
| ---------------------- | --------------------------- |
| harness.toml           | being.toml                  |
| setup → plan → work → review → ship | awaken → think → act → reflect → grow |
| worker, reviewer, scaffolder | hands, conscience, skeleton |
| guardrails             | reflexes (สัญชาตญาณป้องกันตัว) |
| (none)                 | **Life Engine** — identity, memory, continuity (`life_engine/`) |
| (none)                 | state/being.json + vitals.sh (legacy) |

## Layers

```
┌──────────────────────────────────────────────────────────┐
│                       Claude Code                        │
│                  (model + tool runtime)                  │
└────────────────┬─────────────────────────┬───────────────┘
                 │ tool calls              │ skill / faculty loads
                 ▼                         ▼
┌────────────────────────────┐ ┌──────────────────────────┐
│   hooks/  (reflexes)       │ │ skills/, faculties/      │
│   R01..R10                 │ │ life phase contracts     │
└────────────────────────────┘ └──────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────┐
│              being.toml + state/being.json               │
│   lifecycle, reflex toggles, vitals, episodic memory       │
└──────────────────────────────────────────────────────────┘
```

## Why shell reflexes?

- Zero install. Every dev box has bash.
- Reflexes must be fast (<10ms).
- Inspectable in one sitting.

## Why markdown phases/faculties?

- Claude Code natively loads them.
- Diffs are reviewable in PRs.
- No build step.

## Extending Dioo

- **Add a reflex:** new rule in `hooks/pretool.sh`, toggle in `being.toml`
  `[reflexes]`, test in `tests/run.sh`.
- **Add a life phase:** new `skills/<phase>/SKILL.md`, mirror under
  `.claude/skills/`, add to `being.toml` `[being] lifecycle`.
- **Add a faculty:** new `faculties/<name>.md`, mirror under `.claude/agents/`.
