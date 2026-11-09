CREATE TABLE IF NOT EXISTS runtime_observations (
 project TEXT NOT NULL, run TEXT NOT NULL, epoch INTEGER NOT NULL CHECK(epoch>0),
 receipt_hash TEXT NOT NULL, body TEXT NOT NULL CHECK(json_valid(body)), observed_at TEXT NOT NULL,
 PRIMARY KEY(project,run,epoch,receipt_hash)
);
CREATE TABLE IF NOT EXISTS runtime_uploads (
 storage_key TEXT PRIMARY KEY REFERENCES uploaded_content(storage_key),
 project TEXT NOT NULL, run TEXT NOT NULL, epoch INTEGER NOT NULL
);
CREATE TRIGGER IF NOT EXISTS runtime_observation_immutable BEFORE UPDATE ON runtime_observations BEGIN SELECT RAISE(ABORT,'immutable observation'); END;
CREATE TRIGGER IF NOT EXISTS runtime_observation_no_delete BEFORE DELETE ON runtime_observations BEGIN SELECT RAISE(ABORT,'durable observation'); END;
-- LOST is unresolved, so it must keep the task execution fence too.
DROP INDEX IF EXISTS active_run;
CREATE UNIQUE INDEX active_run ON domain_objects(project,json_extract(body,'$.task_id')) WHERE kind='Run' AND json_extract(body,'$.status') IN ('QUEUED','STARTING','RUNNING','CANCEL_REQUESTED','RECONCILING','LOST');
