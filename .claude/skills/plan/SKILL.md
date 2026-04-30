---
name: plan
description: Produce a numbered implementation plan for a feature, bug fix, or refactor. Plans are short, file-pinned, and require user approval before /work begins. Use this any time the change touches more than one file or introduces a new abstraction.
allowed-tools: Read, Glob, Grep, Bash
---

# /plan — design before you cut

## When to use

- The change spans more than one file.
- Architecture is unclear (where should this live, what existing pattern do we
  follow).
- A previous `/work` session got stuck — re-plan from the new state.

## When NOT to use

- A typo fix, a one-liner, a comment addition. Just do it.

## Inputs

- A clear problem statement from the user.
- The current branch and working tree.

## Steps

1. **Restate the problem in one sentence.** If you can't, ask the user.
2. **Survey the relevant code.** Use `Grep`/`Glob` to find existing patterns to
   follow. Cite at least three concrete file:line references.
3. **Write the plan.** Use the template in `templates/plan.md`. Each step is:
   - **What:** the change in one line.
   - **Where:** absolute file paths.
   - **Why:** the reason; a rule, contract, or test that justifies it.
   - **Verify:** how you'll know it worked (test name, assertion, manual check).
4. **Call out tradeoffs.** A short "Considered alternatives" section listing
   what you rejected and why.
5. **Stop and request approval.** Do not invoke `/work` without an explicit
   user "go".

## Exit conditions

- ✅ User approves → record the plan and run `/work`.
- ⚠️  User wants edits → revise and re-present.
- ❌ Plan reveals the task is bigger than expected → tell the user and
   propose a smaller first slice.

## Anti-patterns

- Plans longer than one screen. If it's that big, slice it.
- Vague verbs ("improve", "refactor", "clean up"). Replace with concrete
  edits.
- Skipping the "Verify" line. If you can't say how you'll know, you can't
  ship.
