-- Life Engine MVP schema for Dioo
-- Model-independent, versioned persistence for digital being continuity.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS beings (
    being_id        TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    origin          TEXT,
    core_values     TEXT NOT NULL DEFAULT '[]',      -- JSON array
    identity_fixed  TEXT NOT NULL DEFAULT '{}',    -- JSON object
    self_concept    TEXT NOT NULL DEFAULT '[]',    -- JSON array (developable)
    boundaries      TEXT NOT NULL DEFAULT '{}'     -- JSON object
);

CREATE TABLE IF NOT EXISTS state_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    being_id        TEXT NOT NULL REFERENCES beings(being_id),
    captured_at     TEXT NOT NULL,
    cognitive       TEXT NOT NULL DEFAULT '{}',    -- JSON
    social          TEXT NOT NULL DEFAULT '{}',
    activity        TEXT NOT NULL DEFAULT '{}',
    continuity      TEXT NOT NULL DEFAULT '{}'   -- time, focus, followups
);

CREATE TABLE IF NOT EXISTS events (
    event_id        TEXT PRIMARY KEY,
    being_id        TEXT NOT NULL REFERENCES beings(being_id),
    event_type      TEXT NOT NULL,
    timestamp       TEXT NOT NULL,
    payload         TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS episodic_memories (
    memory_id       TEXT PRIMARY KEY,
    being_id        TEXT NOT NULL REFERENCES beings(being_id),
    event_id        TEXT REFERENCES events(event_id),
    timestamp       TEXT NOT NULL,
    event_text      TEXT NOT NULL,
    interpretation  TEXT,
    importance      REAL NOT NULL DEFAULT 0.5,
    participants    TEXT NOT NULL DEFAULT '[]',
    emotional_tags  TEXT NOT NULL DEFAULT '[]',
    recall_weight   REAL NOT NULL DEFAULT 1.0
);

CREATE TABLE IF NOT EXISTS self_memories (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    being_id        TEXT NOT NULL REFERENCES beings(being_id),
    observation     TEXT NOT NULL,
    evidence_count  INTEGER NOT NULL DEFAULT 1,
    confidence      REAL NOT NULL DEFAULT 0.5,
    behavioral_adjustment TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS relationships (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    being_id        TEXT NOT NULL REFERENCES beings(being_id),
    person_id       TEXT NOT NULL,
    relationship_type TEXT,
    trust           REAL NOT NULL DEFAULT 0.5,
    familiarity     REAL NOT NULL DEFAULT 0.3,
    mutual_understanding REAL NOT NULL DEFAULT 0.3,
    interaction_count INTEGER NOT NULL DEFAULT 0,
    shared_topics   TEXT NOT NULL DEFAULT '[]',
    preferences     TEXT NOT NULL DEFAULT '{}',
    unresolved_tensions TEXT NOT NULL DEFAULT '[]',
    updated_at      TEXT NOT NULL,
    UNIQUE(being_id, person_id)
);

CREATE TABLE IF NOT EXISTS goals (
    goal_id         TEXT PRIMARY KEY,
    being_id        TEXT NOT NULL REFERENCES beings(being_id),
    goal_text       TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'active',
    priority        REAL NOT NULL DEFAULT 0.5,
    source          TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS concerns (
    concern_id      TEXT PRIMARY KEY,
    being_id        TEXT NOT NULL REFERENCES beings(being_id),
    concern_text    TEXT NOT NULL,
    urgency         REAL NOT NULL DEFAULT 0.5,
    related_beliefs TEXT NOT NULL DEFAULT '[]',
    next_review_at  TEXT,
    status          TEXT NOT NULL DEFAULT 'open',
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reflections (
    reflection_id   TEXT PRIMARY KEY,
    being_id        TEXT NOT NULL REFERENCES beings(being_id),
    level           TEXT NOT NULL,                 -- micro | session | daily | long_term
    timestamp       TEXT NOT NULL,
    lessons         TEXT NOT NULL DEFAULT '[]',
    belief_updates  TEXT NOT NULL DEFAULT '[]',
    self_updates    TEXT NOT NULL DEFAULT '[]',
    relationship_updates TEXT NOT NULL DEFAULT '[]',
    pending_concerns TEXT NOT NULL DEFAULT '[]',
    summary         TEXT
);

CREATE TABLE IF NOT EXISTS schema_version (
    version         INTEGER NOT NULL
);

INSERT OR IGNORE INTO schema_version (version) VALUES (1);
