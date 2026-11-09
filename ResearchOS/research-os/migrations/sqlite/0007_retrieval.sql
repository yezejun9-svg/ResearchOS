CREATE TABLE IF NOT EXISTS retrieval_roots (
 project TEXT NOT NULL, id TEXT NOT NULL, path TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision>0),
 revoked INTEGER NOT NULL DEFAULT 0 CHECK(revoked IN (0,1)),
 PRIMARY KEY(project,id), UNIQUE(project,path)
);
CREATE TABLE IF NOT EXISTS retrieval_snapshots (
 project TEXT NOT NULL, artifact_id TEXT NOT NULL, root_id TEXT NOT NULL, relative_path TEXT NOT NULL,
 content_hash TEXT NOT NULL, root_revision INTEGER NOT NULL, status TEXT NOT NULL CHECK(status IN ('CURRENT','STALE','REVOKED')),
 PRIMARY KEY(project,root_id,relative_path,artifact_id),
 FOREIGN KEY(project,root_id) REFERENCES retrieval_roots(project,id)
);
CREATE INDEX IF NOT EXISTS retrieval_snapshot_path ON retrieval_snapshots(project,root_id,relative_path,status);
CREATE UNIQUE INDEX IF NOT EXISTS retrieval_one_current_path ON retrieval_snapshots(project,root_id,relative_path) WHERE status='CURRENT';
CREATE INDEX IF NOT EXISTS retrieval_snapshot_artifact ON retrieval_snapshots(project,artifact_id,status);
CREATE VIRTUAL TABLE IF NOT EXISTS retrieval_fts USING fts5(project UNINDEXED, artifact_id UNINDEXED, body, tokenize='unicode61');
CREATE TABLE IF NOT EXISTS retrieval_index (
 project TEXT NOT NULL, artifact_id TEXT NOT NULL, fts_rowid INTEGER NOT NULL UNIQUE,
 index_revision INTEGER NOT NULL CHECK(index_revision>0), content_hash TEXT NOT NULL,
 PRIMARY KEY(project,artifact_id)
);
CREATE TABLE IF NOT EXISTS evidence_origins (
 project TEXT NOT NULL, evidence_id TEXT NOT NULL, origin_id TEXT NOT NULL DEFAULT '',
 relation TEXT NOT NULL CHECK(relation IN ('ROOT','DERIVED')),
 basis_artifact_id TEXT NOT NULL, recorded_by TEXT NOT NULL REFERENCES auth_principals(id), recorded_at TEXT NOT NULL,
 PRIMARY KEY(project,evidence_id),
 CHECK((relation='ROOT' AND origin_id='') OR (relation='DERIVED' AND origin_id<>''))
);
CREATE TABLE IF NOT EXISTS retrieval_dedupe (
 principal TEXT NOT NULL, project TEXT NOT NULL, key TEXT NOT NULL, request_hash TEXT NOT NULL,
 PRIMARY KEY(principal,project,key)
);
