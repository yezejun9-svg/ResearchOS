CREATE TABLE IF NOT EXISTS source_pages (
 project TEXT NOT NULL,
 cursor_id TEXT NOT NULL,
 source_id TEXT NOT NULL,
 query_hash TEXT NOT NULL,
 window_from TEXT NOT NULL,
 window_to TEXT NOT NULL,
 page_cursor_in TEXT NOT NULL DEFAULT '',
 page_cursor_out TEXT NOT NULL DEFAULT '',
 raw_artifact_id TEXT NOT NULL,
 item_refs_json TEXT NOT NULL CHECK(json_valid(item_refs_json) AND json_type(item_refs_json)='array'),
 complete INTEGER NOT NULL CHECK(complete IN (0,1)),
 fetched_at TEXT NOT NULL,
 cursor_kind TEXT NOT NULL DEFAULT 'SourceCursor' CHECK(cursor_kind='SourceCursor'),
 artifact_kind TEXT NOT NULL DEFAULT 'Artifact' CHECK(artifact_kind='Artifact'),
 PRIMARY KEY(project,cursor_id,window_from,window_to,page_cursor_in),
 FOREIGN KEY(project,cursor_kind,cursor_id) REFERENCES domain_objects(project,kind,id),
 FOREIGN KEY(project,artifact_kind,raw_artifact_id) REFERENCES domain_objects(project,kind,id),
 CHECK((complete=1 AND page_cursor_out='') OR (complete=0 AND page_cursor_out<>''))
);
CREATE TRIGGER IF NOT EXISTS source_pages_no_update BEFORE UPDATE ON source_pages
 BEGIN SELECT RAISE(ABORT,'immutable source page'); END;
CREATE TRIGGER IF NOT EXISTS source_pages_no_delete BEFORE DELETE ON source_pages
 BEGIN SELECT RAISE(ABORT,'immutable source page'); END;
