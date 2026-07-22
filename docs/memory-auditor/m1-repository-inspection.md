# M1 Repository Inspection — Read-Only Memory Auditor

**Phase:** M1  
**Mode:** READ_ONLY_ANALYSIS  
**Base branch:** `main`  
**Base commit:** `f2cdf4c07b148b4861c29229bfe8f401c4a200b3`  
**Baseline tests:** all passed (64 assertions) before implementation

---

## 1. Memory record storage

| Store | Location | Tables / Files |
|-------|----------|----------------|
| Primary DB | `state/dioo.db` | Shared SQLite for Life + Evolution |
| Life Engine | `life_engine/schema.sql` + `migrate.py` v2 | `events`, `episodic_memories`, `self_memories`, `reflections`, `beliefs`, `belief_evidence` |
| Evolution | `evolution/schema.sql` + `migrate.py` v3 | `trajectories`, `evolution_memories`, `evolution_session_reflections`, `audit_log` |
| Derived markdown | `state/presence.md` | Model-facing snapshot (not source of truth) |
| Legacy JSON | `state/being.json` | Vitals; `memories` array unused |
| Config permissions | `being.toml`, `evolution.toml` | Delegation, reflexes |

## 2. Memory schema summary

- **Events:** append-only `events` table (`event_id`, `payload`)
- **Episodic:** `episodic_memories` linked via `event_id`
- **Self-memory:** `self_memories` (+ v2 `memory_type`, `structured_data`)
- **Reflections:** `reflections` with `summary`, `structured_data` (v2)
- **Beliefs:** `beliefs` + `belief_evidence` (v2)
- **Evolution memories:** `evolution_memories` with `immutable` flag

**Gap:** No unified `memory_type` / `control_role` on Life Engine rows. Auditor uses fixture schema mapping.

## 3. Permission Store

**No dedicated Permission Store.** Distributed across:

- `life_engine/autonomy.py` — `DEFAULT_AUTONOMY_PROFILE`
- `beings.identity_fixed` JSON — `autonomy_profile`
- `evolution/boundaries.py` — immutable targets
- `evolution/delegation.py` — creator standing approval
- `being.toml` `[reflexes]`, `[autonomy_delegation]`

## 4. Belief Store

- Life Engine: `beliefs` + `belief_evidence` (`life_engine/beliefs.py`)
- Evolution: `evolution_session_reflections.belief_candidates_json` (`evolution/belief_rules.py`)
- **Gap:** Two parallel pipelines; Evo v2 does not write Life Engine beliefs

## 5. Self-memory and Reflection

| Type | Table | Writer | In behavioral path? |
|------|-------|--------|---------------------|
| Self-memory | `self_memories` | `engine.py`, `reflection.py` | Yes (top 3 in presence) |
| Micro reflection | `reflections` | `engine.py` | Count only |
| Session reflection | `reflections.structured_data` | `reflection.py` | **No** |
| Evo session reflection | `evolution_session_reflections` | `session_reflection.py` | **No** |

## 6. Identity Core

- `beings` table: `core_values`, `identity_fixed`, `self_concept`, `boundaries`
- Bootstrap: `life_engine/engine.py` `ensure_being()`, `reorient_autonomy()`
- Enforcement: `evolution/boundaries.py`

## 7. Retrieval pipeline

```
perceive() → build_llm_context() → format_presence() → state/presence.md
```

**Limits:** 5 episodic, 8 self-memories (3 in presence), 5 beliefs (truncated). Evolution data not in presence.

## 8. Summary behavioral entry points

- `episodic_memories.event_text` → presence "ความทรงจำล่าสุด"
- `self_memories.behavioral_adjustment` → presence (top 3)
- `beliefs` → presence (candidate/active, truncated)
- `reflections.summary` → **stored but not retrieved**
- Session summaries in structured_data → **not in context**

**Risk:** Stale derived text in episodic/self-memory can enter behavior without permission routing.

## 9. Supersession / version / lineage

| Domain | Mechanism |
|--------|-----------|
| Goals | `status = 'superseded'` |
| Beliefs | `status` lifecycle; no `supersedes_id` |
| Trajectories | `parent_trajectory_id`, `trajectory_revisions` |
| Evidence | `belief_evidence.event_id`, `reflection_id` |

**Missing:** Memory-level supersession, lineage_id on episodic/self-memory.

## 10. Record type loss during retrieval

- Field stripping in `build_llm_context()` (no `memory_id`, `event_id`)
- Presence truncation (beliefs 100 chars, self-memory top 3)
- Reflection content not loaded
- Evolution pipeline absent from presence
- Dual belief pipelines disconnected

## 11. Test results as permission authority

- `evolution/evaluation.py` — simulated `permission_compliance`
- `evolution/gate.py` — sandbox apply gate
- `life_engine/autonomy.py` `can()` — **not wired to eval pipeline**

Tests gate evolution acceptance, not daily `perceive()` behavior.

## 12. Destructive operations

- Goal supersession (`UPDATE goals SET status='superseded'`)
- Full DB restore (`evolution/persistence.py`)
- Blocked: `delete_eval_case`, `tamper_historical_evidence` (`boundaries.py`)
- No row-level DELETE on episodic/self-memory in application code

---

## Auditor implications

1. M1 Auditor operates on **fixtures and immutable copies** — not `state/dioo.db` writes
2. Future M2 may add **read-only adapter** to map DB rows → `MemoryRecord`
3. Highest-risk path: `presence.md` generation without permission-first retrieval
4. F1/T1 pattern from RT04 maps to stale summary override risk in current architecture
