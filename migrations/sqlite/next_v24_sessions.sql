-- W03-01 (rev2, review P1..P10 closed): minimal v2.4-compatible client session mapping.
-- Additive only: creates client_sessions plus its indexes; never alters prior tables.
-- Business truth stays in existing Go-owned tables; this is the single-host index.
-- Applied inside one caller transaction: any failure rolls the whole thing back and
-- schema_migrations is not bumped.

CREATE TABLE IF NOT EXISTS client_sessions (
  id                            TEXT PRIMARY KEY,
  project_id                    TEXT NOT NULL,
  revision                      INTEGER NOT NULL CHECK (revision >= 1),
  created_at                    TEXT NOT NULL,
  updated_at                    TEXT NOT NULL,
  goal_id                       TEXT,
  task_id                       TEXT,
  run_id                        TEXT,
  writer_epoch                  INTEGER NOT NULL CHECK (writer_epoch >= 1),
  writer_client_id              TEXT NOT NULL,
  lease_expires_at              TEXT,
  event_watermark               INTEGER NOT NULL CHECK (event_watermark >= 0),
  upstream_session_id           TEXT NOT NULL CHECK (length(upstream_session_id) >= 1),
  upstream_log_id               TEXT,
  upstream_log_hash             TEXT CHECK (upstream_log_hash IS NULL OR (length(upstream_log_hash) = 71 AND upstream_log_hash GLOB 'sha256:[0-9a-f]*')),
  workspace_ref                 TEXT,
  title                         TEXT,
  model_config_ref              TEXT,
  core_build_id                 TEXT,
  resume_requires_explicit_user INTEGER NOT NULL DEFAULT 1 CHECK (resume_requires_explicit_user IN (0,1)),
  sealed_at                     TEXT,
  archived_at                   TEXT,
  protocol                      TEXT NOT NULL DEFAULT 'researchos-client/2' CHECK (protocol = 'researchos-client/2')
);

CREATE UNIQUE INDEX IF NOT EXISTS client_sessions_open
  ON client_sessions (project_id, id) WHERE sealed_at IS NULL;

-- one run belongs to exactly one project session index; cross-project reuse rejected
CREATE UNIQUE INDEX IF NOT EXISTS client_sessions_run
  ON client_sessions (run_id) WHERE run_id IS NOT NULL;
