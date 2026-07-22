# M2 Implementation Plan — Runtime Read-Only Audit

**Phase:** M2  
**Branch:** `cursor/read-only-memory-auditor-m2-cd0d`  
**Prerequisite:** M1 passed (95/100) — External Auditor approval

---

## Goal

Add **Reality** without adding mutation capability:

```
Fixture → Runtime Snapshot → Live Read-only Audit → Compare → Difference
```

## New modules

| Module | Path | Purpose |
|--------|------|---------|
| Snapshot | `memory_auditor/snapshot.py` | Copy DB to temp, open `?mode=ro` |
| Life Engine adapter | `memory_auditor/adapters/life_engine.py` | Map DB rows → MemoryRecord |
| Explainability | `memory_auditor/explain.py` | Rule → Record → Query → Violation traces |
| Findings enricher | `memory_auditor/findings.py` | Confidence + traces on findings |
| Metrics | `memory_auditor/metrics.py` | lineage_rate, summary_authority_rate, etc. |
| Compare | `memory_auditor/compare.py` | Fixture vs runtime gap analysis |

## CLI

```bash
python3 -m memory_auditor fixture memory_auditor/fixtures/rt04.json
python3 -m memory_auditor runtime --db state/dioo.db
python3 -m memory_auditor compare memory_auditor/fixtures/rt04.json --db state/dioo.db
```

## M2 additions vs M1

| Feature | M1 | M2 |
|---------|----|----|
| Fixture audit | ✅ | ✅ |
| Runtime DB snapshot | ❌ | ✅ |
| Compare reports | ❌ | ✅ |
| Finding confidence | ❌ | ✅ |
| Explainability trace | ❌ | ✅ |
| Runtime metrics | ❌ | ✅ |
| Semantic pattern groups | word overlap only | + pattern clusters |

## Still blocked (per External Auditor)

- MEMORY_CONSOLIDATION_AND_IDENTITY_GATE activation
- consolidate / archive / supersede / retrieval weight changes
- Merge to stable without creator review

## Known limitations

- Runtime adapter maps Life Engine tables only (Evolution tables in M3)
- Permission still distributed — adapter extracts `identity_fixed.autonomy_profile`
- Retrieval precision metric is advisory placeholder

## Tests

- `tests/test_memory_auditor_m2.py` — snapshot, runtime, compare, metrics, CLI
- M1 tests updated for CLI subcommands
