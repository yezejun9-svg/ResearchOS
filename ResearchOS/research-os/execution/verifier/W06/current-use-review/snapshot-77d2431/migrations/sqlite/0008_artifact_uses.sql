-- Canonical Artifact identity remains UNIQUE(project,content_hash,kind).
-- Each new runtime contribution proves its own upload and immutable provenance.
CREATE TABLE artifact_uses (
 project TEXT NOT NULL, artifact TEXT NOT NULL, run TEXT NOT NULL,
 epoch INTEGER NOT NULL CHECK(epoch>0), principal TEXT NOT NULL REFERENCES auth_principals(id),
 storage_key TEXT NOT NULL REFERENCES uploaded_content(storage_key),
 receipt_hash TEXT NOT NULL, body TEXT NOT NULL CHECK(json_valid(body)),
 PRIMARY KEY(project,artifact,run,epoch,principal), UNIQUE(storage_key)
);
CREATE TRIGGER artifact_uses_immutable BEFORE UPDATE ON artifact_uses BEGIN SELECT RAISE(ABORT,'immutable artifact use'); END;
CREATE TRIGGER artifact_uses_durable BEFORE DELETE ON artifact_uses BEGIN SELECT RAISE(ABORT,'durable artifact use'); END;
