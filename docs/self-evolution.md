# Self-Evolution Engine

Evidence-driven self-development for Dioo. Phase E1 adds observation, evaluation, failure analysis, and proposals — **not** autonomous production changes.

## Quick start

```bash
bash scripts/evolution.sh init
bash scripts/evolution.sh seed-baseline
bash scripts/evolution.sh run-baseline
bash scripts/evolution.sh dashboard
bash scripts/evolution.sh record "implement feature X" --status success
```

## Modules

| Module | Purpose |
|--------|---------|
| `engine.py` | Orchestrates trajectory → evaluate → failure → proposal cycle |
| `trajectory.py` | Append-only task trajectory recorder |
| `evaluation.py` | 12-dimension evaluator with pass gate |
| `diagnosis.py` | Failure categorization, fingerprinting, aggregation |
| `proposals.py` | Improvement proposals + failure-to-eval conversion |
| `boundaries.py` | Immutable targets and blocked actions |
| `audit.py` | Append-only audit log |
| `persistence.py` | Snapshots, recovery, rollback test, corruption check |
| `dashboard.py` | Status dashboard |
| `redaction.py` | Secret redaction before persistence |
| `config.py` | Loads `evolution.toml` feature flags and budgets |

## CLI commands

| Command | Description |
|---------|-------------|
| `init` | Apply schema + seed skill registry |
| `dashboard` | Human + JSON status |
| `seed-baseline` | Load 20 cases from `evals/baseline/cases.json` |
| `run-baseline` | Execute baseline suite |
| `record <objective>` | Record trajectory and evaluate |
| `snapshot` | Stable DB snapshot |
| `snapshot-candidate` | Candidate snapshot |
| `recover <id>` | Restore from snapshot |
| `rollback-test` | Verify restore integrity |
| `reflect-session` | Session reflection v2 (E2) |
| `evaluate-belief` | Belief candidate rules v2 (E2) |
| `experiment-start` | Start sandbox experiment (E2) |
| `experiment-run` | Run experiment comparison (E2) |
| `budget-status` | Daily budget usage (E2) |
| `check-corruption` | Health check |
| `check-boundary <action>` | Test immutable boundary |

## Configuration

`evolution.toml` — feature flags, budgets, thresholds. Dioo cannot modify thresholds or budgets at runtime.

## Tests

```bash
bash tests/test_evolution_e1.sh
bash scripts/check.sh   # includes life engine + evolution
```
