package domain

import (
	"database/sql"
	"encoding/json"
)

// A checkpoint is copied from its already verified previous-epoch upload, not
// re-labelled as a newly observed result. Canonical content remains immutable.
func (s *Service) carryCheckpoint(tx *sql.Tx, project, actor string, run, artifact, oldUse Object) error {
	executor := Principal{ID: Str(run, "executor_principal_id")}
	var roles string
	var revoked int
	if e := tx.QueryRow("SELECT roles,revoked FROM auth_principals WHERE id=?", executor.ID).Scan(&roles, &revoked); e != nil {
		return e
	}
	if e := json.Unmarshal([]byte(roles), &executor.Roles); e != nil {
		return e
	}
	if revoked != 0 || !executor.HasRole("EXECUTOR") {
		return Fail(403, "FORBIDDEN", "resumed executor revoked")
	}
	var grants int
	if e := tx.QueryRow("SELECT count(*) FROM auth_grants WHERE principal=? AND project=? AND task=? AND run=?", executor.ID, project, run["task_id"], run["id"]).Scan(&grants); e != nil {
		return e
	}
	if grants != 1 {
		return Fail(403, "FORBIDDEN", "current execution grant required")
	}
	executor.Grants = []Grant{{ProjectID: project, TaskID: Str(run, "task_id"), RunID: Str(run, "id")}}
	var content []byte
	if e := tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, oldUse["storage_key"]).Scan(&content); e != nil {
		return e
	}
	u, e := s.upload(tx, executor, project, content)
	if e != nil {
		return e
	}
	b := Object{"run_id": run["id"], "produced_by": executor.ID, "storage_key": u["storage_key"], "content_hash": u["content_hash"], "byte_size": u["byte_size"], "input_refs": oldUse["input_refs"], "source_refs": oldUse["source_refs"]}
	for _, k := range []string{"kind", "evidence_kind", "measurement_mode", "media_type", "access_class"} {
		b[k] = artifact[k]
	}
	carried, e := s.seal(tx, executor, project, b)
	if e != nil {
		return e
	}
	if carried["id"] != artifact["id"] {
		return Fail(422, "GATE_FAILED", "checkpoint identity changed")
	}
	_, e = tx.Exec("INSERT INTO resource_checkpoint_carries(project,run,epoch,body) VALUES(?,?,?,?)", project, run["id"], run["lease_epoch"], string(Bytes(Object{"actor": actor, "artifact_ref": Ref(artifact, "Artifact"), "from_use_receipt_hash": oldUse["receipt_hash"], "from_epoch": oldUse["lease_epoch"], "to_epoch": run["lease_epoch"], "new_upload_key": u["storage_key"], "reason": "CHECKPOINT_CARRY_NOT_NEW_RESULT", "at": Now()})))
	return e
}
