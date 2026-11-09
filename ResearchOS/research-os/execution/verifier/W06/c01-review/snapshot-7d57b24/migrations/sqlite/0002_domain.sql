CREATE TABLE IF NOT EXISTS domain_objects (
 project TEXT NOT NULL, kind TEXT NOT NULL, id TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision>0),
 body TEXT NOT NULL CHECK(json_valid(body)), content_hash TEXT, immutable INTEGER NOT NULL DEFAULT 0,
 PRIMARY KEY(project,kind,id), UNIQUE(project,kind,id,revision)
);
CREATE TABLE IF NOT EXISTS domain_versions (
 project TEXT NOT NULL, kind TEXT NOT NULL, id TEXT NOT NULL, revision INTEGER NOT NULL,
 body TEXT NOT NULL CHECK(json_valid(body)), content_hash TEXT,
 PRIMARY KEY(project,kind,id,revision)
);
CREATE TABLE IF NOT EXISTS domain_refs (
 project TEXT NOT NULL, kind TEXT NOT NULL, id TEXT NOT NULL, revision INTEGER NOT NULL, field TEXT NOT NULL,
 target_project TEXT NOT NULL, target_kind TEXT NOT NULL, target_id TEXT NOT NULL, target_revision INTEGER NOT NULL,
 FOREIGN KEY(project,kind,id,revision) REFERENCES domain_versions(project,kind,id,revision) DEFERRABLE INITIALLY DEFERRED,
 FOREIGN KEY(target_project,target_kind,target_id,target_revision) REFERENCES domain_versions(project,kind,id,revision) DEFERRABLE INITIALLY DEFERRED,
 CHECK(target_project=project OR (target_project='' AND target_kind IN ('BudgetPolicy','RunPolicy')))
);
CREATE UNIQUE INDEX IF NOT EXISTS one_project_state ON domain_objects(project) WHERE kind='ProjectState';
CREATE UNIQUE INDEX IF NOT EXISTS artifact_content ON domain_objects(project,json_extract(body,'$.content_hash'),json_extract(body,'$.kind')) WHERE kind='Artifact';
CREATE UNIQUE INDEX IF NOT EXISTS no_progress_key ON domain_objects(project,json_extract(body,'$.key_hash')) WHERE kind='NoProgressRecord';
CREATE UNIQUE INDEX IF NOT EXISTS active_cycle ON domain_objects(project) WHERE kind='ResearchCycle' AND json_extract(body,'$.status') IN ('PLANNED','RUNNING');
CREATE UNIQUE INDEX IF NOT EXISTS active_run ON domain_objects(project,json_extract(body,'$.task_id')) WHERE kind='Run' AND json_extract(body,'$.status') IN ('QUEUED','STARTING','RUNNING','CANCEL_REQUESTED','RECONCILING');
CREATE UNIQUE INDEX IF NOT EXISTS evidence_snapshot ON domain_objects(project,json_extract(body,'$.canonical_url'),coalesce(json_extract(body,'$.upstream_revision'),''),json_extract(body,'$.snapshot_artifact_ref.content_hash')) WHERE kind='Evidence';
CREATE UNIQUE INDEX IF NOT EXISTS source_cursor ON domain_objects(project,json_extract(body,'$.source_id'),json_extract(body,'$.query_hash')) WHERE kind='SourceCursor';
CREATE UNIQUE INDEX IF NOT EXISTS active_request ON domain_objects(project,json_extract(body,'$.category'),coalesce(json_extract(body,'$.account_ref'),''),json_extract(body,'$.reason_code')) WHERE kind='ResourceRequest' AND json_extract(body,'$.status') IN ('OPEN','ACKNOWLEDGED');
CREATE UNIQUE INDEX IF NOT EXISTS release_sequence ON domain_objects(project,json_extract(body,'$.sequence')) WHERE kind='MilestoneRelease';
CREATE UNIQUE INDEX IF NOT EXISTS notification_dedup ON domain_objects(project,coalesce(json_extract(body,'$.release_id'),''),coalesce(json_extract(body,'$.resource_request_id'),''),json_extract(body,'$.recipient_id'),json_extract(body,'$.channel')) WHERE kind='Notification';
CREATE UNIQUE INDEX IF NOT EXISTS billing_event ON domain_objects(project,json_extract(body,'$.policy_id'),json_extract(body,'$.provider_event_id')) WHERE kind='BudgetLedgerEntry';
CREATE UNIQUE INDEX IF NOT EXISTS policy_scope ON domain_objects(kind,project,json_extract(body,'$.scope_type'),json_extract(body,'$.scope_id')) WHERE kind IN ('BudgetPolicy','RunPolicy');
CREATE TABLE IF NOT EXISTS outbox(project TEXT NOT NULL, sequence INTEGER NOT NULL, id TEXT NOT NULL UNIQUE, body TEXT NOT NULL, acknowledged INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(project,sequence));
CREATE TABLE IF NOT EXISTS idempotency(principal TEXT NOT NULL, project TEXT NOT NULL, operation TEXT NOT NULL, key TEXT NOT NULL, request_hash TEXT NOT NULL, status INTEGER NOT NULL, body BLOB NOT NULL, headers TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY(principal,project,operation,key));
CREATE TABLE IF NOT EXISTS auth_principals(id TEXT PRIMARY KEY, roles TEXT NOT NULL CHECK(json_valid(roles)), can_create_project INTEGER NOT NULL DEFAULT 0, revoked INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS auth_grants(principal TEXT NOT NULL REFERENCES auth_principals(id), project TEXT NOT NULL, task TEXT NOT NULL DEFAULT '', run TEXT NOT NULL DEFAULT '', restricted INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(principal,project,task,run));
CREATE TABLE IF NOT EXISTS auth_credentials(token_hash TEXT PRIMARY KEY, principal TEXT NOT NULL REFERENCES auth_principals(id), expires_at TEXT NOT NULL, revoked INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS uploaded_content(storage_key TEXT PRIMARY KEY, project TEXT NOT NULL, principal TEXT NOT NULL REFERENCES auth_principals(id), bytes BLOB NOT NULL, content_hash TEXT NOT NULL, expires_at TEXT NOT NULL, sealed INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS page_cursors(id TEXT PRIMARY KEY, principal TEXT NOT NULL, project TEXT NOT NULL, operation TEXT NOT NULL, grant_hash TEXT NOT NULL, body TEXT NOT NULL, expires_at TEXT NOT NULL);
CREATE TRIGGER IF NOT EXISTS versions_no_update BEFORE UPDATE ON domain_versions BEGIN SELECT RAISE(ABORT,'immutable version'); END;
CREATE TRIGGER IF NOT EXISTS versions_no_delete BEFORE DELETE ON domain_versions BEGIN SELECT RAISE(ABORT,'immutable version'); END;
CREATE TRIGGER IF NOT EXISTS objects_immutable BEFORE UPDATE ON domain_objects WHEN OLD.immutable=1 BEGIN SELECT RAISE(ABORT,'immutable receipt'); END;
CREATE TRIGGER IF NOT EXISTS artifact_immutable BEFORE UPDATE ON domain_objects WHEN OLD.kind='Artifact' AND (NEW.content_hash IS NOT OLD.content_hash OR json_extract(NEW.body,'$.storage_key') IS NOT json_extract(OLD.body,'$.storage_key') OR json_extract(NEW.body,'$.access_class') IS NOT json_extract(OLD.body,'$.access_class')) BEGIN SELECT RAISE(ABORT,'sealed content'); END;
CREATE TRIGGER IF NOT EXISTS content_immutable BEFORE UPDATE OF bytes,content_hash,project ON uploaded_content WHEN OLD.sealed=1 BEGIN SELECT RAISE(ABORT,'sealed bytes'); END;
CREATE TRIGGER IF NOT EXISTS content_no_delete BEFORE DELETE ON uploaded_content WHEN OLD.sealed=1 BEGIN SELECT RAISE(ABORT,'sealed bytes'); END;
CREATE TRIGGER IF NOT EXISTS artifact_metadata_immutable BEFORE UPDATE ON domain_objects WHEN OLD.kind='Artifact' AND json_remove(NEW.body,'$.revision','$.updated_at','$.validity') != json_remove(OLD.body,'$.revision','$.updated_at','$.validity') BEGIN SELECT RAISE(ABORT,'sealed metadata'); END;
CREATE TRIGGER IF NOT EXISTS outbox_immutable BEFORE UPDATE OF project,sequence,id,body ON outbox BEGIN SELECT RAISE(ABORT,'immutable event'); END;
CREATE TRIGGER IF NOT EXISTS outbox_no_delete BEFORE DELETE ON outbox BEGIN SELECT RAISE(ABORT,'durable event'); END;
CREATE TRIGGER IF NOT EXISTS idempotency_immutable BEFORE UPDATE ON idempotency BEGIN SELECT RAISE(ABORT,'immutable replay'); END;
