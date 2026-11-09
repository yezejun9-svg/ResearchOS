-- Earlier registered roots have no handle identity and cannot remain trusted.
-- Owners must register those roots again; no old body can be read through them.
ALTER TABLE retrieval_roots ADD COLUMN root_identity TEXT NOT NULL DEFAULT '';
UPDATE retrieval_roots SET revoked=1, revision=revision+1 WHERE root_identity='';
-- A deduplicated Artifact may have several file origins. Reviewed evidence
-- stays bound to the exact source location that justified the annotation.
ALTER TABLE evidence_origins ADD COLUMN basis_root_id TEXT NOT NULL DEFAULT '';
ALTER TABLE evidence_origins ADD COLUMN basis_relative_path TEXT NOT NULL DEFAULT '';
