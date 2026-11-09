CREATE TABLE IF NOT EXISTS context_changes(project TEXT NOT NULL, proposal_id TEXT NOT NULL, author TEXT NOT NULL REFERENCES auth_principals(id), contract_hash TEXT NOT NULL, original_values TEXT NOT NULL, PRIMARY KEY(project,proposal_id));
CREATE TABLE IF NOT EXISTS decision_lineage(project TEXT NOT NULL, receipt_id TEXT NOT NULL, root_id TEXT NOT NULL, generation INTEGER NOT NULL CHECK(generation>0), PRIMARY KEY(project,receipt_id));
CREATE TABLE IF NOT EXISTS context_imports(project TEXT PRIMARY KEY, manifest_hash TEXT NOT NULL, manifest_artifact_id TEXT NOT NULL, inventory TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS consumer_positions(consumer TEXT NOT NULL, project TEXT NOT NULL, sequence INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(consumer,project));
CREATE TABLE IF NOT EXISTS consumer_inbox(consumer TEXT NOT NULL, project TEXT NOT NULL, event_id TEXT NOT NULL, sequence INTEGER NOT NULL, applied INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(consumer,event_id), UNIQUE(consumer,project,sequence));
CREATE TABLE IF NOT EXISTS context_projection(consumer TEXT NOT NULL, project TEXT NOT NULL, kind TEXT NOT NULL, id TEXT NOT NULL, revision INTEGER NOT NULL, body TEXT NOT NULL, PRIMARY KEY(consumer,project,kind,id));
CREATE TABLE IF NOT EXISTS event_state_snapshots(project TEXT NOT NULL,event_id TEXT PRIMARY KEY REFERENCES outbox(id),revision INTEGER NOT NULL,body TEXT NOT NULL CHECK(json_valid(body)));
CREATE TRIGGER IF NOT EXISTS event_state_immutable BEFORE UPDATE ON event_state_snapshots BEGIN SELECT RAISE(ABORT,'event snapshot immutable'); END;
CREATE TRIGGER IF NOT EXISTS event_state_no_delete BEFORE DELETE ON event_state_snapshots BEGIN SELECT RAISE(ABORT,'event snapshot durable'); END;
INSERT OR IGNORE INTO event_state_snapshots(project,event_id,revision,body)
 SELECT e.project,e.id,v.revision,v.body FROM outbox e JOIN domain_versions v ON v.project=e.project AND v.kind='ProjectState'
 WHERE json_extract(v.body,'$.event_sequence')=e.sequence AND v.revision=(SELECT min(x.revision) FROM domain_versions x WHERE x.project=e.project AND x.kind='ProjectState' AND json_extract(x.body,'$.event_sequence')=e.sequence);
CREATE UNIQUE INDEX IF NOT EXISTS message_dedup ON domain_objects(project,json_extract(body,'$.dedup_key')) WHERE kind='AgentMessage';
