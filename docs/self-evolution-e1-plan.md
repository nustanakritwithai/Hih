# Self-Evolution E1 — Architecture Audit & Implementation Plan

## 1. Current architecture (audit)

### Reusable components

| Layer | Path | Reuse for E1 |
|-------|------|--------------|
| Life Engine | `life_engine/` | Identity, goals, beliefs, session reflection (Level 3) — **unchanged** |
| SQLite store | `state/dioo.db` | Shared DB; evolution tables appended via `evolution/schema.sql` |
| Reflexes | `hooks/` | Safety boundaries (R01–R10) — complementary to `evolution/boundaries.py` |
| Runtime protocol | `CLAUDE.md`, `skills/live/` | Dioo identity + `/live` — **not modified** |
| CLI pattern | `scripts/life.sh` | Mirrored by `scripts/evolution.sh` |

### Risks to Identity, Memory, Autonomy

| Risk | Mitigation in E1 |
|------|------------------|
| Identity drift via self-modification | `boundaries.py` blocks identity core, thresholds, permission matrix |
| Memory corruption / loss on restart | Snapshots (`persistence.py`), shared `dioo.db`, rollback test |
| Unbounded autonomous loops | Budget caps in `evolution.toml`; no sandbox loop in E1 |
| Evaluator gaming | Dioo cannot lower pass threshold (`BLOCKED_REQUIRES_CREATOR`) |
| Secret leakage in trajectories | `redaction.py` before persistence |
| Production merge without creator | `merge_stable_branch` blocked |

## 2. Implementation order (Phase E1 scope)

Steps 1–11 from directive §26 are implemented in E1. Steps 12–17 are **deferred to E2/E3** (feature flags `false`).

| Step | Module | Status |
|------|--------|--------|
| 1–2 | Audit + this plan | Done |
| 3 | `evolution/schema.sql` + migration history | Done |
| 4 | `evolution/boundaries.py` | Done |
| 5 | `evolution/trajectory.py` | Done |
| 6 | `evolution/evaluation.py` (12 dimensions) | Done |
| 7 | `evals/baseline/cases.json` (20 cases) | Done |
| 8 | `evolution/diagnosis.py` | Done |
| 9 | `evolution/proposals.py` | Done |
| 10 | Failure-to-eval in `proposals.py` | Done |
| 11 | Session reflection v2 | **E2** (`session_reflection_v2=false`) |
| 12 | Belief candidate rules v2 | **E2** |
| 13 | Sandbox experiments | **E2** |
| 14 | Verifier separation | **E3** |
| 15 | Comparison + acceptance gate | **E3** |
| 16 | Evolution memory | **E3** |
| 17 | `evolution/dashboard.py` | Done |
| 18–19 | `tests/test_evolution_e1.sh` + `scripts/check.sh` | Done |
| 20 | `docs/self-evolution-e1-report.md` | Done |

## 3. Persistence & recovery (§25)

| Capability | Implementation |
|------------|----------------|
| Stable snapshot | `evolution snapshot` → `state/snapshots/stable_*.db` |
| Candidate snapshot | `evolution snapshot-candidate` |
| Pre-migration backup | `PersistenceManager.backup_before_migration()` |
| Recovery | `evolution recover <snapshot_id>` |
| Rollback test | `evolution rollback-test` |
| Corruption detection | `evolution check-corruption` |
| Schema version | `evolution_schema_version` table |
| Migration history | `evolution_migration_history` table |

Restart must preserve Life Engine data (identity, goals, trajectories, evaluations, failures, proposals, audit) — all in `state/dioo.db` with snapshot restore.

## 4. Feature flags (default safe)

See `evolution.toml`. E2/E3 systems disabled until creator enables them.

## 5. Budget controls (§28)

Configured in `evolution.toml`. Exceeding budget → `PAUSED_BUDGET_LIMIT` (enforced in E2 experiment runner).

## 6. Branch strategy

- **Stable base:** `cursor/digital-living-being-cd0d` (Life Engine Level 3)
- **E1 branch:** `cursor/self-evolution-e1-cd0d`
- No direct edits to stable/main; no auto-merge
