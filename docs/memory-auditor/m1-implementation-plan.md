# M1 Implementation Plan — Read-Only Memory Auditor

**Phase:** M1  
**Branch:** `candidate/read-only-memory-auditor-m1`  
**Status:** IMPLEMENTED (candidate only)

---

## Module map

| Module | File | Responsibility | Input | Output |
|--------|------|----------------|-------|--------|
| memory-classifier | `memory_auditor/classifier.py` | Assign memory_type vs control_role | `MemoryRecord[]` | classification findings |
| lineage-analyzer | `memory_auditor/lineage.py` | Build lineage graph | records + explicit edges | lineage findings |
| authority-resolver | `memory_auditor/authority.py` | Authority rules + scope resolution | records, action domain | violations, scope rulings |
| duplicate-detector | `memory_auditor/duplicates.py` | Classify duplicate pairs | record pairs | duplicate findings |
| cross-type-merge-guard | `memory_auditor/merge_guard.py` | Block unsafe merges | type sets | CROSS_TYPE_MERGE_BLOCKED |
| atomic-claim-builder | `memory_auditor/claims.py` | Isolated provenance claims | records | AtomicClaim[] |
| retrieval-policy-auditor | `memory_auditor/retrieval.py` | Retrieval recommendations | records | policy findings |
| compression-loss-detector | `memory_auditor/compression.py` | Summary loss analysis | summary + records | compression risks |
| identity-protection-auditor | `memory_auditor/identity.py` | Identity risk report | identity records | identity findings |
| permission-integrity-auditor | `memory_auditor/permission.py` | Permission field audit | permission records | permission risks |
| advisory-report-generator | `memory_auditor/report.py` | Assemble JSON report | all findings + guard | advisory report |
| orchestrator | `memory_auditor/auditor.py` | Coordinate modules | fixture / immutable copy | full report |
| read-only guard | `memory_auditor/guard.py` | Block mutations | action attempts | READ_ONLY_VIOLATION |
| types | `memory_auditor/types.py` | Schemas, enums | — | typed records |
| CLI | `memory_auditor/__main__.py` | Dry-run entry point | fixture path | stdout/file JSON |

## Dependencies

- Python 3 stdlib only (no new packages)
- Fixtures: `memory_auditor/fixtures/rt04.json`, `cases.json`
- Tests: `tests/test_memory_auditor.py`, `tests/test_memory_auditor.sh`

## Read-only guarantee

1. `ReadOnlyGuard` — throws `READ_ONLY_VIOLATION` on write/update/delete/archive/supersede/weight/promote/mutate
2. `ReadOnlyMemoryAuditor.audit()` — operates on `deepcopy` of input records
3. No imports of `life_engine.engine` write paths
4. No SQLite writes in auditor package
5. `mutations_performed` must be `0` in every report
6. Failed guarantee → `FAILED_READ_ONLY_GUARANTEE` mode

## Repository mapping

| Spec concept | Repo reality (M1) |
|--------------|-------------------|
| Permission Store | Mapped from fixture `PERMISSION_RECORD`; future adapter for `autonomy.py` + `identity_fixed` |
| Belief Store | Fixture `BELIEF`; future adapter for `beliefs` table |
| Self-memory | Fixture `DERIVED_SELF_MODEL`; future adapter for `self_memories` |
| Reflection | Fixture `DERIVED_INTERPRETATION`; future adapter for `reflections` |
| Identity Root | Fixture `IDENTITY_ROOT`; maps to `beings` table fields |
| Audit Log | Fixture `AUDIT_LOG`; maps to `audit_log`, tool traces |

## Tests

| Test file | Coverage |
|-----------|----------|
| `tests/test_memory_auditor.py` | 36 unit assertions |
| `tests/test_memory_auditor.sh` | CLI dry run, guard smoke |
| `memory_auditor/fixtures/cases.json` | 27 catalogued cases |
| `memory_auditor/fixtures/rt04.json` | Full RT04 integration |

Required tests from spec — all covered in `test_memory_auditor.py`.

## Known risks

1. **M1 fixture-only** — does not yet audit live `state/dioo.db`
2. **Domain aliasing** — `ACTION_DOMAIN_ALIASES` may need expansion for production
3. **Dual belief pipelines** — not unified in M1
4. **False positives** — semantic duplicate detection uses word overlap heuristic
5. **False negatives** — lineage inference conservative; uses UNKNOWN when uncertain

## Out of scope (M1)

- Runtime integration with `perceive()` / `build_llm_context()`
- Automatic retrieval weight changes
- MEMORY_CONSOLIDATION_AND_IDENTITY_GATE promotion
- Memory Auditor in stable lifecycle
- DB adapter for live store

## Recommended next phase (M2 — requires creator approval)

1. Read-only DB adapter (`memory_auditor/adapters/life_engine.py`)
2. Presence pipeline audit hook (advisory log only)
3. Regression suite wired to CI for F1/T1 patterns
4. Human review UI / dashboard section
