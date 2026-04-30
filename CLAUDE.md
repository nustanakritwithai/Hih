# CLAUDE.md

This file is loaded by Claude Code at session start. It defines how Claude should
operate inside this repository.

## Mission

You are operating inside a **structured development harness**. Your job is to drive
the five-verb loop: **setup → plan → work → review → ship**. Each verb is a skill
in `skills/<verb>/SKILL.md`. Read the relevant SKILL before invoking it.

## Operating principles

1. **No silent skipping.** Every change goes through `plan → work → review` before
   `ship`. If you find yourself wanting to skip review, stop and call the reviewer
   agent instead.
2. **Single in-flight task.** The TodoWrite list always has exactly one
   `in_progress` item. Mark complete the instant a task is done.
3. **Guardrails are non-negotiable.** If `hooks/pretool.sh` blocks a command, do
   not work around it with `--no-verify`, `sudo`, or rewriting history. Surface
   the block to the user and ask.
4. **Edit, don't recreate.** Prefer `Edit` over `Write` for existing files. Never
   create README/docs/markdown unless the user asks or the skill requires it.
5. **Trust internal contracts.** Don't add defensive validation for impossible
   states. Validate at boundaries (user input, network, disk), not between your
   own functions.

## Commands

| Slash command | What it does                                          |
| ------------- | ----------------------------------------------------- |
| `/setup`      | Detect stack, write conventions, install dev deps     |
| `/plan`       | Produce numbered implementation plan, get approval    |
| `/work`       | Execute the plan, one task at a time, with TodoWrite  |
| `/review`     | Run `reviewer` agent across security/perf/quality     |
| `/ship`       | Stage, commit with conventional message, push, PR     |

## Files of interest

- `hooks/pretool.sh` — the guardrail script. Read it before changing it.
- `skills/<verb>/SKILL.md` — the contract for each verb.
- `agents/*.md` — subagent system prompts.
- `workflows/default/loop.md` — the canonical loop description.

## Context budget

Long sessions burn context. After every `ship`, summarize what changed in 1–2
sentences and clear stale todos.
