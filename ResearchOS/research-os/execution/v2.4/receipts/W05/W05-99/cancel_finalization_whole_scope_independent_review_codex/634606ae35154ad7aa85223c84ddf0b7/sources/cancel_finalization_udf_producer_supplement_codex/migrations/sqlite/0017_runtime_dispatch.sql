-- One launch fact per existing Run epoch. This is not a schedulable Task queue.
CREATE TABLE runtime_dispatches (
    project TEXT NOT NULL, run TEXT NOT NULL, epoch INTEGER NOT NULL,
    dispatch_key TEXT NOT NULL UNIQUE,
    manifest TEXT NOT NULL, manifest_hash TEXT NOT NULL,
    state TEXT NOT NULL CHECK(state IN ('PREPARED','STARTED','OBSERVED','UNKNOWN')),
    worker TEXT NOT NULL DEFAULT '', journal_locator TEXT NOT NULL DEFAULT '',
    identity TEXT NOT NULL DEFAULT '{}',
    observation_sequence INTEGER NOT NULL DEFAULT 0,
    observation_hash TEXT NOT NULL DEFAULT '',
    prepared_at TEXT NOT NULL, updated_at TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    PRIMARY KEY(project,run,epoch)
);
CREATE TRIGGER runtime_dispatch_manifest_frozen
BEFORE UPDATE OF project,run,epoch,dispatch_key,manifest,manifest_hash,prepared_at
ON runtime_dispatches BEGIN SELECT RAISE(ABORT,'dispatch identity immutable'); END;
CREATE TRIGGER runtime_dispatch_no_delete BEFORE DELETE ON runtime_dispatches
BEGIN SELECT RAISE(ABORT,'dispatch launch fact retained'); END;
