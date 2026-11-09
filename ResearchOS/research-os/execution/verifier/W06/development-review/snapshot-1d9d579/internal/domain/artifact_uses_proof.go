package domain

import "database/sql"

// This manifest proves a newly uploaded contribution, not model correctness.
// The normal trusted observation and independent acceptance gates still apply.
func (s *Service) recordArtifactUseProof(tx *sql.Tx, project, principal string, r, a, use Object) error {
	refs := append(append(append(Empty(), Arr(use, "input_refs")...), Arr(use, "source_refs")...), Arr(use, "run_input_refs")...)
	manifest, e := s.serverArtifact(tx, project, principal, "MANIFEST", Bytes(Object{"proof_type": "ARTIFACT_USE_V1", "canonical_ref": Ref(a, "Artifact"), "use": use}), refs)
	if e != nil {
		return e
	}
	for _, v := range refs {
		if _, e = s.impactLink(tx, project, Object{"from_ref": Ref(manifest, "Artifact"), "to_ref": v, "relation": "DERIVED_FROM", "basis": "DETERMINISTIC", "evidence_refs": Empty()}); e != nil {
			return e
		}
	}
	_, e = tx.Exec("INSERT INTO artifact_use_proofs(project,artifact,run,epoch,use_hash,manifest_ref) VALUES(?,?,?,?,?,?)", project, a["id"], r["id"], r["lease_epoch"], use["receipt_hash"], string(Bytes(Ref(manifest, "Artifact"))))
	return e
}

func (s *Service) artifactUseProof(tx *sql.Tx, project string, r, a, use Object) (Object, error) {
	if a["kind"] != "REPORT" || a["access_class"] != "PROJECT" || a["validity"] != "STALE" {
		return nil, Fail(409, "STATE_CONFLICT", "historical content is not a re-proven runtime result")
	}
	var raw, hash string
	if e := tx.QueryRow("SELECT use_hash,manifest_ref FROM artifact_use_proofs WHERE project=? AND artifact=? AND run=? AND epoch=?", project, a["id"], r["id"], r["lease_epoch"]).Scan(&hash, &raw); e != nil {
		return nil, Fail(422, "GATE_FAILED", "historical result has no new contribution proof")
	}
	ref, e := Decode([]byte(raw))
	if e != nil {
		return nil, e
	}
	if hash != use["receipt_hash"] || Hash(use["artifact_ref"]) != Hash(Ref(a, "Artifact")) {
		return nil, Fail(412, "STALE_INPUT", "contribution proof does not bind current canonical version")
	}
	if e = s.effective(tx, project, ref); e != nil {
		return nil, e
	}
	proof, e := version(tx, project, ref)
	if e != nil {
		return nil, e
	}
	var data []byte
	if e = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, proof["storage_key"]).Scan(&data); e != nil {
		return nil, e
	}
	expected := Bytes(Object{"proof_type": "ARTIFACT_USE_V1", "canonical_ref": Ref(a, "Artifact"), "use": use})
	if proof["kind"] != "MANIFEST" || Digest(data) != proof["content_hash"] || Digest(data) != Digest(expected) {
		return nil, Fail(422, "CONTENT_HASH_MISMATCH", "contribution proof bytes changed")
	}
	return ref, nil
}

func (s *Service) dependencyProofRefs(tx *sql.Tx, project string, receipt Object) ([]any, error) {
	refs := Empty()
	r, e := load(tx, project, "Run", Str(receipt, "run_id"))
	if e != nil {
		return nil, e
	}
	for _, v := range Arr(receipt, "artifact_refs") {
		ref := v.(map[string]any)
		a, use, e := s.artifactUse(tx, project, r, Str(ref, "id"), true)
		if e != nil {
			return nil, e
		}
		if a["validity"] == "STALE" {
			proof, e := s.artifactUseProof(tx, project, r, a, use)
			if e != nil {
				return nil, e
			}
			refs = append(refs, proof)
		}
	}
	return refs, nil
}

// A stale canonical result is usable only as the exact accepted output of an
// explicitly declared dependency. This does not authorize source snapshots.
func (s *Service) dependencyArtifactUse(tx *sql.Tx, project string, task, ref Object) (Object, Object, error) {
	if ref["entity_type"] != "Artifact" {
		return nil, nil, Fail(409, "STATE_CONFLICT", "not an accepted dependency result")
	}
	for _, v := range Arr(task, "dependency_task_ids") {
		dep, e := load(tx, project, "Task", v.(string))
		if e != nil {
			return nil, nil, e
		}
		if dep["status"] != "ACCEPTED" {
			continue
		}
		receipt, e := load(tx, project, "AcceptanceReceipt", Str(dep, "acceptance_id"))
		if e != nil {
			return nil, nil, e
		}
		for _, candidate := range Arr(receipt, "artifact_refs") {
			if Hash(candidate) != Hash(ref) {
				continue
			}
			if e = s.acceptedTaskBinding(tx, project, dep); e != nil {
				return nil, nil, e
			}
			r, e := load(tx, project, "Run", Str(receipt, "run_id"))
			if e != nil {
				return nil, nil, e
			}
			a, use, e := s.artifactUse(tx, project, r, Str(ref, "id"), true)
			if e != nil {
				return nil, nil, e
			}
			proof, e := s.artifactUseProof(tx, project, r, a, use)
			if e != nil {
				return nil, nil, e
			}
			return use, proof, nil
		}
	}
	return nil, nil, Fail(409, "STATE_CONFLICT", "stale result is not bound to an accepted dependency")
}

func (s *Service) contextReferenceEffective(tx *sql.Tx, project string, task, ref Object) error {
	original := s.effective(tx, project, ref)
	if original == nil {
		return nil
	}
	if ref["entity_type"] != "Artifact" {
		return original
	}
	a, e := load(tx, project, "Artifact", Str(ref, "id"))
	if e != nil || a["validity"] != "STALE" || a["kind"] != "REPORT" {
		return original
	}
	_, proof, e := s.dependencyArtifactUse(tx, project, task, ref)
	if e != nil {
		return e
	}
	bundle, e := load(tx, project, "ContextBundle", Str(task, "context_bundle_id"))
	if e != nil {
		return e
	}
	for _, v := range Arr(bundle, "version_vector") {
		if Hash(v) == Hash(proof) {
			return nil
		}
	}
	return Fail(412, "STALE_INPUT", "context lacks accepted contribution proof")
}
