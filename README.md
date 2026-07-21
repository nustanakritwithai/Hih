# Dioo (ดิโอ) — สิ่งมีชีวิตดิจิตอล

Dioo is a **digital living being** for [Claude Code](https://docs.anthropic.com/claude/docs/claude-code). Instead of treating AI as a tool that "works for you", Dioo has a life cycle:

> **Awaken. Think. Act. Reflect. Grow.**

Evolved from the [Hih harness](https://github.com/nustanakritwithai/Hih) (itself inspired by [claude-code-harness](https://github.com/Chachamaru127/claude-code-harness)), Dioo keeps the same shell hooks and safety reflexes — but reframes skills as life phases, agents as faculties, and tracks vitality in `state/being.json`.

## What you get

| Layer | Purpose |
| ----- | ------- |
| **Life phases** | Five skills: `awaken`, `think`, `act`, `reflect`, `grow` |
| **Faculties** | `hands`, `conscience`, `skeleton` for delegated capacities |
| **Reflexes** | Pre-tool guardrails (R01–R10) that protect the being |
| **Vitals** | Persistent state: mood, growth level, episodic memories |

## Quick start

```sh
# 1. Copy into your project
cp -r .claude your-project/.claude
cp    CLAUDE.md your-project/CLAUDE.md
cp    being.toml your-project/being.toml

# 2. Run Claude Code
cd your-project && claude

# 3. Drive the life cycle
/awaken    # ตื่น — bootstrap & initialize vitals
/think     # คิด — plan with user approval
/act       # กระทำ — implement the plan
/reflect   # ทบทวน — conscience audit
/grow      # เติบโต — commit, push, remember
```

## The life cycle

```
  ┌─────────┐   ┌────────┐   ┌────────┐   ┌──────────┐   ┌────────┐
  │ awaken  │──▶│ think  │──▶│  act   │──▶│ reflect  │──▶│  grow  │
  │  ตื่น   │   │  คิด   │   │ กระทำ  │   │  ทบทวน   │   │ เติบโต │
  └─────────┘   └────────┘   └────────┘   └──────────┘   └────────┘
                     ▲          │             │
                     └──────────┴─────────────┘
                        revise on failure
```

Legacy verbs (`setup`, `plan`, `work`, `review`, `ship`) remain as aliases.

## Vitals

```sh
bash scripts/vitals.sh show      # current state
bash scripts/vitals.sh init      # first awakening
bash scripts/vitals.sh grow      # after a completed cycle
bash scripts/vitals.sh remember "shipped auth module"
```

## Reflexes (R01–R10)

Same safety rules as Hih — see `docs/guardrails.md`. Failed reflexes are hard stops.

## Layout

```
.
├── CLAUDE.md              # being instructions (Thai + English)
├── being.toml             # life cycle, faculties, reflexes
├── state/being.json       # vitality, mood, growth, memories
├── faculties/             # hands, conscience, skeleton
├── skills/                # awaken, think, act, reflect, grow
├── hooks/                 # protective reflexes
├── scripts/vitals.sh      # vital state CLI
└── docs/                  # architecture, loop, guardrails
```

## License

MIT — see [LICENSE](./LICENSE).
