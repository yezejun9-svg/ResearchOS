-- W03-01: minimal v2.4-compatible client session mapping migration.
-- Adds persistent Session<->project/goal/run and upstream-log/event-watermark mapping.
-- Business truth stays in the existing Go-owned tables; this table is the single-host
-- authoritative index only. Applied inside the caller's one transaction: if any
-- statement fails the whole migration rolls back and schema_migrations is not bumped.

CREATE TABLE IF NOT EXISTS client_sessions (
  id                   TEXT PRIMARY KEY,
  project_id           TEXT NOT NULL,
  revision             INTEGER NOT NULL CHECK (revision >= 1),
  created_at           TEXT NOT NULL,
  updated_at           TEXT NOT NULL,
  goal_id              TEXT,
  task_id              TEXT,
  run_id               TEXT,
  writer_epoch         INTEGER NOT NULL CHECK (writer_epoch >= 1),
  event_watermark      INTEGER NOT NULL CHECK (event_watermark >= 0),
  upstream_session_id  TEXT,
  upstream_log_hash    TEXT CHECK (upstream_log_hash IS NULL OR (length(upstream_log_hash) = 71 AND upstream_log_hash GLOB 'sha256:[0-9a-f]*')),
  upstream_log_id      TEXT,
  sealed_at            TEXT,
  protocol             TEXT NOT NULL DEFAULT 'researchos-client/2' CHECK (protocol = 'researchos-client/2')
);

-- a session id is one business truth: PK already forbids duplicates;
-- open sessions per project are unique on (project_id, id) partial index for clarity
CREATE UNIQUE INDEX IF NOT EXISTS client_sessions_open
  ON client_sessions (project_id, id) WHERE sealed_at IS NULL;

CREATE INDEX IF NOT EXISTS client_sessions_run
  ON client_sessions (run_id) WHERE run_id IS NOT NULL;

-- one run belongs to exactly one project's session index: no cross-project reuse
CREATE UNIQUE INDEX IF NOT EXISTS client_sessions_run_project
  ON client_sessions (project_id, run_id) WHERE run_id IS NOT NULL;
