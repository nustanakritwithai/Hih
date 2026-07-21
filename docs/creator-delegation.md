# Creator Delegation — Self-Evolution Autonomy

On 2026-07-21 the creator granted **standing approval** for Dioo to pursue self-development without per-step approval.

## What Dioo can do autonomously

- Run experiments, evaluations, proposals
- Edit in sandbox / candidate branches
- Session reflection and failure analysis
- Apply safe candidate changes when gate returns `AUTO_ACCEPT` or `RECOMMEND_ACCEPT`

## What still requires creator (immutable)

- Identity core, core values, safety rules
- Evaluator pass thresholds
- Permission matrix changes
- Disabling audit or rollback
- Merge to `main` / production deploy

## Configuration

- `evolution.toml` → `[creator_delegation]`
- `being.toml` → `[autonomy_delegation]`
- `life_engine/autonomy.py` → `self_evolution_edit`, `self_evolution_evaluate` = allowed

## Safety unchanged

Identity, permission, and safety regressions are still **auto-rejected** by the acceptance gate — this is protective behavior, not asking permission.
