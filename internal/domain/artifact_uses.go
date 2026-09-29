package domain

import "database/sql"

func (s *Service) reusableArtifact(tx *sql.Tx, p Principal, project string, existing, b Object, run Object) error {
	if !s.visible(tx, p, project, existing) {
		return Fail(403, "FORBIDDEN", "existing content provenance is not visible")
	}
	for _, field := range []string{"kind", "evidence_kind", "measurement_mode", "access_class", "media_type"} {
		if existing[field] != b[field] {
			return Fail(409, "STATE_CONFLICT", "canonical artifact evidence and access metadata cannot change on reuse")
		}
	}
	if existing["validity"] != "CURRENT" {
		return Fail(409, "STATE_CONFLICT", "canonical historical or revoked content requires separate revalidation proof")
	}
	if e := s.effective(tx, project, Ref(existing, "Artifact")); e != nil {
		return e
	}
	if run == nil && (existing["run_id"] != nil || existing["produced_by"] != p.ID || Hash(existing["input_refs"]) != Hash(b["input_refs"]) || Hash(existing["source_refs"]) != Hash(b["source_refs"])) {
		return Fail(409, "STATE_CONFLICT", "different contribution requires a current runtime use binding")
	}
	return nil
}

func (s *Service) recordArtifactUse(tx *sql.Tx, p Principal, project string, run, a, b Object) error {
	if run == nil {
		return nil
	}
	if e := validExecutorRun(tx, p, project, run); e != nil {
		return e
	}
	if runTerminal(run) {
		return Fail(409, "STATE_CONFLICT", "terminal run cannot add an artifact contribution")
	}
	if e := s.taskContextForRun(tx, project, run); e != nil {
		return e
	}
	for _, field := range []string{"input_refs", "source_refs"} {
		for _, v := range Arr(b, field) {
			if e := s.effective(tx, project, v.(map[string]any)); e != nil {
				return e
			}
		}
	}
	var boundRun string
	var boundEpoch int64
	e := tx.QueryRow("SELECT run,epoch FROM runtime_uploads WHERE project=? AND storage_key=?", project, b["storage_key"]).Scan(&boundRun, &boundEpoch)
	epoch, _ := Num(run, "lease_epoch")
	if e != nil && e != sql.ErrNoRows {
		return e
	}
	if e == nil && (boundRun != run["id"] || boundEpoch != epoch) {
		return Fail(403, "FORBIDDEN", "upload belongs to another run or epoch")
	}
	if e == sql.ErrNoRows {
		if _, e = tx.Exec("INSERT INTO runtime_uploads(storage_key,project,run,epoch) VALUES(?,?,?,?)", b["storage_key"], project, run["id"], epoch); e != nil {
			return e
		}
	}
	var existing string
	e = tx.QueryRow("SELECT body FROM artifact_uses WHERE project=? AND artifact=? AND run=? AND epoch=? AND principal=?", project, a["id"], run["id"], epoch, p.ID).Scan(&existing)
	if e == nil {
		use, _ := Decode([]byte(existing))
		if use["storage_key"] == b["storage_key"] && Hash(use["input_refs"]) == Hash(b["input_refs"]) && Hash(use["source_refs"]) == Hash(b["source_refs"]) {
			return nil
		}
		return Fail(409, "STATE_CONFLICT", "run artifact contribution already sealed")
	}
	if e != sql.ErrNoRows {
		return e
	}
	use := Object{"project_id": project, "artifact_ref": Ref(a, "Artifact"), "run_id": run["id"], "lease_epoch": run["lease_epoch"], "principal_id": p.ID, "storage_key": b["storage_key"], "content_hash": a["content_hash"], "byte_size": a["byte_size"], "input_refs": b["input_refs"], "source_refs": b["source_refs"], "run_input_refs": run["input_refs"], "context_bundle_id": run["context_bundle_id"], "measurement_mode": b["measurement_mode"], "evidence_kind": b["evidence_kind"], "access_class": b["access_class"], "created_at": Now()}
	use["receipt_hash"] = Receipt(use)
	_, e = tx.Exec("INSERT INTO artifact_uses(project,artifact,run,epoch,principal,storage_key,receipt_hash,body) VALUES(?,?,?,?,?,?,?,?)", project, a["id"], run["id"], epoch, p.ID, b["storage_key"], use["receipt_hash"], string(Bytes(use)))
	return e
}

func (s *Service) taskContextForRun(tx *sql.Tx, project string, r Object) error {
	t, e := load(tx, project, "Task", Str(r, "task_id"))
	if e != nil {
		return e
	}
	if t["active_run_id"] != r["id"] || t["context_bundle_id"] != r["context_bundle_id"] || Hash(t["input_refs"]) != Hash(r["input_refs"]) {
		return Fail(409, "STATE_CONFLICT", "run no longer owns frozen task inputs")
	}
	return s.taskContext(tx, project, t)
}

// artifactUse authenticates a contribution, not the canonical object's first
// producer. effective=false supports authorized historical reads/receipts only.
func (s *Service) artifactUse(tx *sql.Tx, project string, r Object, id string, effective bool) (Object, Object, error) {
	a, e := load(tx, project, "Artifact", id)
	if e != nil {
		return nil, nil, e
	}
	var raw string
	e = tx.QueryRow("SELECT body FROM artifact_uses WHERE project=? AND artifact=? AND run=? AND epoch=? AND principal=?", project, id, r["id"], r["lease_epoch"], r["executor_principal_id"]).Scan(&raw)
	if e != nil {
		return nil, nil, Fail(422, "GATE_FAILED", "artifact has no proven contribution for this run and epoch")
	}
	use, e := Decode([]byte(raw))
	if e != nil {
		return nil, nil, e
	}
	if use["receipt_hash"] != Receipt(use) || use["content_hash"] != a["content_hash"] || use["context_bundle_id"] != r["context_bundle_id"] || Hash(use["run_input_refs"]) != Hash(r["input_refs"]) {
		return nil, nil, Fail(422, "GATE_FAILED", "artifact use binding mismatch")
	}
	var data []byte
	var principal string
	var boundRun string
	var epoch int64
	e = tx.QueryRow("SELECT u.bytes,u.principal,x.run,x.epoch FROM uploaded_content u JOIN runtime_uploads x ON x.storage_key=u.storage_key AND x.project=u.project WHERE u.project=? AND u.storage_key=? AND u.sealed=1", project, use["storage_key"]).Scan(&data, &principal, &boundRun, &epoch)
	n, _ := Num(r, "lease_epoch")
	size, _ := Num(a, "byte_size")
	if e != nil || principal != r["executor_principal_id"] || boundRun != r["id"] || epoch != n || Digest(data) != a["content_hash"] || size != int64(len(data)) {
		return nil, nil, Fail(422, "CONTENT_HASH_MISMATCH", "artifact use has no matching sealed current-run upload")
	}
	for _, field := range []string{"measurement_mode", "evidence_kind", "access_class"} {
		if use[field] != a[field] {
			return nil, nil, Fail(422, "GATE_FAILED", "artifact use cannot elevate canonical evidence or access")
		}
	}
	if effective {
		if e = s.effective(tx, project, Ref(a, "Artifact")); e != nil {
			return nil, nil, e
		}
		for _, field := range []string{"input_refs", "source_refs", "run_input_refs"} {
			for _, v := range Arr(use, field) {
				if e = s.effective(tx, project, v.(map[string]any)); e != nil {
					return nil, nil, e
				}
			}
		}
	}
	return a, use, nil
}

func (s *Service) artifactUseScope(tx *sql.Tx, p Principal, project, id string) bool {
	rows, e := tx.Query("SELECT run FROM artifact_uses WHERE project=? AND artifact=? AND principal=?", project, id, p.ID)
	if e != nil {
		return false
	}
	ids := []string{}
	for rows.Next() {
		var run string
		if e = rows.Scan(&run); e != nil {
			rows.Close()
			return false
		}
		ids = append(ids, run)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return false
	}
	for _, idRun := range ids {
		r, e := currentRun(tx, p, project, idRun)
		if e == nil {
			if _, _, e = s.artifactUse(tx, project, r, id, false); e == nil {
				return true
			}
		}
	}
	return false
}
