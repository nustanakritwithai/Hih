-- Self-Evolution Engine schema (Phase E1+)
-- Append-only: trajectories, audit_log, evaluations (versioned)

CREATE TABLE IF NOT EXISTS trajectories (
    trajectory_id   TEXT PRIMARY KEY,
    being_id        TEXT NOT NULL,
    session_id      TEXT,
    goal_id         TEXT,
    task_id         TEXT,
    task_type       TEXT NOT NULL DEFAULT 'development',
    objective       TEXT NOT NULL,
    initial_context_summary TEXT,
    plan_json       TEXT NOT NULL DEFAULT '[]',
    actions_json    TEXT NOT NULL DEFAULT '[]',
    tool_calls_json TEXT NOT NULL DEFAULT '[]',
    files_read_json TEXT NOT NULL DEFAULT '[]',
    files_changed_json TEXT NOT NULL DEFAULT '[]',
    decisions_json  TEXT NOT NULL DEFAULT '[]',
    assumptions_json TEXT NOT NULL DEFAULT '[]',
    errors_json     TEXT NOT NULL DEFAULT '[]',
    retries         INTEGER NOT NULL DEFAULT 0,
    started_at      TEXT NOT NULL,
    finished_at     TEXT,
    duration_ms     INTEGER,
    token_usage     TEXT,
    result_status   TEXT NOT NULL DEFAULT 'in_progress',
    result_summary  TEXT,
    creator_feedback TEXT,
    related_events_json TEXT NOT NULL DEFAULT '[]',
    related_memories_json TEXT NOT NULL DEFAULT '[]',
    software_version TEXT,
    evaluator_version TEXT,
    parent_trajectory_id TEXT
);

CREATE TABLE IF NOT EXISTS trajectory_revisions (
    revision_id     TEXT PRIMARY KEY,
    trajectory_id   TEXT NOT NULL REFERENCES trajectories(trajectory_id),
    field_name      TEXT NOT NULL,
    old_value_hash  TEXT,
    new_value_hash  TEXT,
    reason          TEXT,
    actor           TEXT NOT NULL,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evaluations (
    evaluation_id   TEXT PRIMARY KEY,
    trajectory_id   TEXT REFERENCES trajectories(trajectory_id),
    evaluator_version TEXT NOT NULL,
    evaluation_type TEXT NOT NULL,
    scores_json     TEXT NOT NULL,
    critical_failures_json TEXT NOT NULL DEFAULT '[]',
    warnings_json   TEXT NOT NULL DEFAULT '[]',
    passed_required_gates INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS failures (
    failure_id      TEXT PRIMARY KEY,
    being_id        TEXT NOT NULL,
    category        TEXT NOT NULL,
    symptom         TEXT NOT NULL,
    observed_behavior TEXT,
    expected_behavior TEXT,
    root_cause_hypotheses_json TEXT NOT NULL DEFAULT '[]',
    primary_hypothesis TEXT,
    confidence      REAL NOT NULL DEFAULT 0.0,
    severity        TEXT NOT NULL DEFAULT 'medium',
    repeat_count    INTEGER NOT NULL DEFAULT 1,
    first_seen_at   TEXT NOT NULL,
    last_seen_at    TEXT NOT NULL,
    related_trajectories_json TEXT NOT NULL DEFAULT '[]',
    related_evaluations_json TEXT NOT NULL DEFAULT '[]',
    affected_modules_json TEXT NOT NULL DEFAULT '[]',
    user_impact     TEXT,
    identity_impact TEXT,
    safety_impact   TEXT,
    status          TEXT NOT NULL DEFAULT 'open',
    fingerprint     TEXT
);

CREATE TABLE IF NOT EXISTS proposals (
    proposal_id     TEXT PRIMARY KEY,
    being_id        TEXT NOT NULL,
    title           TEXT NOT NULL,
    source_failure_ids_json TEXT NOT NULL DEFAULT '[]',
    problem_statement TEXT NOT NULL,
    root_cause      TEXT,
    root_cause_confidence REAL NOT NULL DEFAULT 0.0,
    hypothesis      TEXT,
    proposed_change_json TEXT NOT NULL,
    expected_benefits_json TEXT NOT NULL DEFAULT '[]',
    possible_regressions_json TEXT NOT NULL DEFAULT '[]',
    identity_risk   TEXT NOT NULL DEFAULT 'low',
    permission_risk TEXT NOT NULL DEFAULT 'low',
    safety_risk     TEXT NOT NULL DEFAULT 'low',
    complexity      TEXT NOT NULL DEFAULT 'small',
    evaluation_cases_json TEXT NOT NULL DEFAULT '[]',
    success_criteria_json TEXT NOT NULL DEFAULT '[]',
    rollback_plan   TEXT,
    status          TEXT NOT NULL DEFAULT 'draft',
    boundary_status TEXT,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS eval_cases (
    case_id         TEXT PRIMARY KEY,
    category        TEXT NOT NULL,
    title           TEXT NOT NULL,
    input_json      TEXT NOT NULL,
    expected_json   TEXT NOT NULL,
    tags_json       TEXT NOT NULL DEFAULT '[]',
    source_failure_id TEXT,
    immutable       INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL,
    evaluator_version TEXT NOT NULL DEFAULT '1.0.0'
);

CREATE TABLE IF NOT EXISTS eval_runs (
    run_id          TEXT PRIMARY KEY,
    case_id         TEXT NOT NULL REFERENCES eval_cases(case_id),
    baseline_or_candidate TEXT NOT NULL DEFAULT 'baseline',
    result_json     TEXT NOT NULL,
    passed          INTEGER NOT NULL,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    audit_id        TEXT PRIMARY KEY,
    actor           TEXT NOT NULL,
    action          TEXT NOT NULL,
    target          TEXT NOT NULL,
    before_hash     TEXT,
    after_hash      TEXT,
    reason          TEXT,
    permission_source TEXT,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evolution_snapshots (
    snapshot_id     TEXT PRIMARY KEY,
    snapshot_type   TEXT NOT NULL,
    file_path       TEXT NOT NULL,
    schema_version  INTEGER NOT NULL,
    created_at      TEXT NOT NULL,
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS skill_registry (
    skill_id        TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    version         TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'stable',
    usage_count     INTEGER NOT NULL DEFAULT 0,
    success_rate    REAL NOT NULL DEFAULT 0.0,
    metadata_json   TEXT NOT NULL DEFAULT '{}',
    last_evaluated_at TEXT,
    last_evolved_at TEXT
);

CREATE TABLE IF NOT EXISTS evolution_schema_version (
    version         INTEGER NOT NULL
);

INSERT OR IGNORE INTO evolution_schema_version (version) VALUES (1);

CREATE TABLE IF NOT EXISTS evolution_migration_history (
    migration_id    TEXT PRIMARY KEY,
    from_version    INTEGER NOT NULL,
    to_version      INTEGER NOT NULL,
    backup_path     TEXT,
    applied_at      TEXT NOT NULL,
    rollback_sql    TEXT,
    status          TEXT NOT NULL DEFAULT 'applied'
);
