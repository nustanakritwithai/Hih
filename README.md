# Hih — Claude Code Harness

A structured development harness for [Claude Code](https://docs.anthropic.com/claude/docs/claude-code) that turns ad-hoc prompting into a disciplined loop:

> **Plan. Work. Review. Ship.**

Inspired by [Chachamaru127/claude-code-harness](https://github.com/Chachamaru127/claude-code-harness), this implementation focuses on the essentials: shell-based hooks, declarative guardrails, opinionated skills, and small specialized agents.

## What you get

| Layer        | Purpose                                                             |
| ------------ | ------------------------------------------------------------------- |
| **Skills**   | Five verbs (`setup`, `plan`, `work`, `review`, `ship`) as workflows |
| **Agents**   | `worker`, `reviewer`, `scaffolder` for delegated subtasks           |
| **Hooks**    | Pre-tool guardrails (R01–R10) that block destructive operations    |
| **Workflow** | A repeatable loop with checkpoints between stages                   |

## Quick start

```sh
# 1. Drop this directory into your project root (or use as a template)
cp -r hih/.claude your-project/.claude
cp    hih/CLAUDE.md your-project/CLAUDE.md

# 2. Run Claude Code in that project
cd your-project && claude

# 3. Drive the loop with slash skills
/setup     # bootstrap project conventions
/plan      # produce an implementation plan
/work      # implement against the plan
/review    # multi-perspective code review
/ship      # commit, push, open PR
```

## The five verbs

```
  ┌──────────┐   ┌────────┐   ┌────────┐   ┌──────────┐   ┌────────┐
  │  setup   │──▶│  plan  │──▶│  work  │──▶│  review  │──▶│  ship  │
  └──────────┘   └────────┘   └────────┘   └──────────┘   └────────┘
                      ▲                          │
                      └──── revise on failure ───┘
```

Each verb is a skill in `skills/<verb>/SKILL.md` with explicit inputs, outputs, and exit conditions.

## Guardrails

The pre-tool hook in `hooks/pretool.sh` enforces:

| ID  | Rule                                                  |
| --- | ----------------------------------------------------- |
| R01 | Block `rm -rf /`, `rm -rf ~`, `rm -rf .`              |
| R02 | Block `git push --force` to protected branches        |
| R03 | Block `git reset --hard` without explicit confirmation |
| R04 | Block `sudo` invocations                              |
| R05 | Block writes to `.env`, `*.pem`, `id_rsa`, credentials |
| R06 | Block `chmod 777`                                     |
| R07 | Block `curl ... \| sh` style remote execution         |
| R08 | Block `git commit --no-verify`                        |
| R09 | Block `--no-gpg-sign`                                 |
| R10 | Block destructive `git branch -D` on `main`/`master`  |

Failed checks print a diagnostic and exit non-zero; Claude sees the rejection and adjusts.

## Layout

```
.
├── CLAUDE.md                # project instructions Claude reads on start
├── harness.toml             # harness-level configuration
├── .claude/
│   ├── settings.json        # hooks, permissions, env
│   ├── agents/              # subagent definitions
│   └── skills/              # symlinked verbs (or copies)
├── hooks/                   # shell guardrails
├── skills/                  # five verb skills
├── agents/                  # agent definitions
├── scripts/                 # auxiliary utilities
├── templates/               # generation templates
├── workflows/default/       # default loop description
├── docs/                    # detailed guides
└── tests/                   # hook test suite
```

## License

MIT — see [LICENSE](./LICENSE).
