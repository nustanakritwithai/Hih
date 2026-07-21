# Self-Evolution E2 — Implementation Plan

## Scope (Phase E2)

| Feature | Module | Status |
|---------|--------|--------|
| Schema migration v2 | `evolution/migrate.py` | Done |
| Budget enforcement | `evolution/budget.py` | Done |
| Belief rules v2 | `evolution/belief_rules.py` | Done |
| Session reflection v2 | `evolution/session_reflection.py` | Done |
| Sandbox experiments | `evolution/sandbox.py` | Done |
| Candidate branches | `candidate_branches` table | Done |

## Deferred to E3

- Verifier (producer ≠ verifier separation)
- Comparison engine + acceptance gate
- Evolution memory (separate from episodic/self-memory)

## New tables (schema v2)

- `experiments` — sandbox runs with baseline vs candidate comparison
- `candidate_branches` — max 3 active branches
- `budget_usage` — daily experiment/reflection counters
- `evolution_session_reflections` — v2 reflections with evidence links

## Feature flags (`evolution.toml`)

E2 features enabled on this branch. E3 flags remain `false`.

## Budget limits

When exceeded → `PAUSED_BUDGET_LIMIT`. Dioo cannot raise budgets.

## Branch strategy

- **Base:** `cursor/self-evolution-e1-cd0d`
- **E2 branch:** `cursor/self-evolution-e2-cd0d`
