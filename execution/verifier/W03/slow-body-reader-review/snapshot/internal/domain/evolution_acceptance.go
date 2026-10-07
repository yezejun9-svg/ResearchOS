//go:build windows

package domain

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"researchos.local/research-os/evaluation/evolution"
	"researchos.local/research-os/ops/supervisor"
)

func evolutionRecord(tx *sql.Tx, project, id, phase string) (Object, error) {
	var raw, hash, state string
	if e := tx.QueryRow("SELECT body,receipt_hash,state FROM evolution_executions WHERE project=? AND candidate=? AND phase=?", project, id, phase).Scan(&raw, &hash, &state); e != nil {
		return nil, Fail(422, "GATE_FAILED", "trusted native execution record unavailable")
	}
	r, e := Decode([]byte(raw))
	if e != nil {
		return nil, e
	}
	if state != "RECORDED" || r["state"] != state || r["receipt_hash"] != hash || hash != Receipt(r) {
		return nil, Fail(422, "GATE_FAILED", "execution record not final or hash changed")
	}
	return r, nil
}
func (s *Service) evolutionRecordValid(tx *sql.Tx, project string, x, r Object) error {
	if r["project_id"] != project || r["candidate_id"] != x["id"] || r["plan_hash"] != Hash(evolutionPlan(x)) || r["baseline_hash"] != x["stable_artifact_ref"].(map[string]any)["content_hash"] || r["candidate_hash"] != x["candidate_artifact_ref"].(map[string]any)["content_hash"] || r["suite_hash"] != Digest(evolution.Bytes(evolution.Suite())) || r["policy_hash"] != Digest(evolution.Bytes(evolution.Policy())) || r["scope"] != evolution.Scope {
		return Fail(422, "GATE_FAILED", "frozen host/build/suite binding mismatch")
	}
	if _, e := s.evolutionCurrent(tx, project, x); e != nil {
		return e
	}
	if r["phase"] == "REGRESSION" {
		p, e := decodePair(r["pair"])
		if e != nil {
			return e
		}
		b, e := supervisor.Verify(p.Baseline, Str(r, "baseline_hash"))
		if e != nil {
			return e
		}
		c, e := supervisor.Verify(p.Candidate, Str(r, "candidate_hash"))
		if e != nil {
			return e
		}
		if p.Scope != evolution.Scope || p.SuiteHash != r["suite_hash"] || p.PolicyHash != r["policy_hash"] || !p.StablePreserved || Hash(b) != Hash(p.BaselineResult) || Hash(c) != Hash(p.CandidateResult) || r["required_passed"] != c.RequiredPassed || r["improved"] != evolution.Improved(b, c) {
			return Fail(422, "GATE_FAILED", "raw native outcomes differ from host derived verdict")
		}
		observation := r["observation"].(map[string]any)
		observations := Arr(observation, "observations")
		if len(observations) != 1 {
			return fmt.Errorf("one correctness metric required")
		}
		row := observations[0].(map[string]any)
		if Hash(row["case_ids"]) != Hash(evolutionIDs()) || Hash(row["baseline"]) != Hash(b.Values) || Hash(row["candidate"]) != Hash(c.Values) {
			return fmt.Errorf("paired metric values not derived from actual native outputs")
		}
	} else if r["phase"] == "CANARY" {
		var health supervisor.Invocation
		if e := json.Unmarshal(Bytes(r["stable_health"]), &health); e != nil {
			return e
		}
		result, e := supervisor.Verify(health, Str(r, "baseline_hash"))
		if e != nil || !result.RequiredPassed {
			return fmt.Errorf("real stable process health missing")
		}
		var restore RestoreReport
		if e = json.Unmarshal(Bytes(r["restore"]), &restore); e != nil {
			return e
		}
		var backup BackupManifest
		if e = json.Unmarshal(Bytes(r["backup_manifest"]), &backup); e != nil {
			return e
		}
		if restore.Status != "RESTORED_RECONCILIATION_REQUIRED" || restore.BackupID != backup.ID || Hash(restore.Before) != Hash(backup.Inventory) {
			return fmt.Errorf("actual W18 rollback receipt mismatch")
		}
		var canary supervisor.Invocation
		if e = json.Unmarshal(Bytes(r["canary"]), &canary); e != nil {
			return e
		}
		measured, err := supervisor.Verify(canary, Str(r, "candidate_hash"))
		regressed := err != nil || !measured.RequiredPassed
		if regressed != r["observed_regression"] || canary.BuildHash != r["candidate_hash"] || canary.RawHash != Digest([]byte(canary.Raw)) {
			return fmt.Errorf("canary observation changed")
		}
		observation := r["observation"].(map[string]any)
		if observation["restored_hash"] != r["baseline_hash"] || observation["backup_id"] != backup.ID || observation["inventory_hash"] != Hash(restore.Before) || observation["observed_regression"] != regressed || observation["health_raw_hash"] != health.RawHash || observation["canary_raw_hash"] != canary.RawHash {
			return fmt.Errorf("published rollback differs from host execution")
		}
	} else {
		return fmt.Errorf("unknown execution phase")
	}
	return nil
}
func (s *Service) verifyEvolutionObservation(snap Object, phase string) (string, string) {
	task := snap["task"].(map[string]any)
	run := snap["run"].(map[string]any)
	project := Str(task, "project_id")
	tx, e := s.DB.Begin()
	if e != nil {
		return "FAIL", e.Error()
	}
	defer tx.Rollback()
	var id string
	if e = tx.QueryRow("SELECT candidate FROM evolution_tasks WHERE project=? AND task=? AND phase=?", project, task["id"], phase).Scan(&id); e != nil {
		return "FAIL", "task not bound to evolution phase"
	}
	x, e := load(tx, project, "SystemCandidate", id)
	if e != nil {
		return "FAIL", e.Error()
	}
	record, e := evolutionRecord(tx, project, id, phase)
	if e != nil {
		return "FAIL", e.Error()
	}
	if record["run_id"] != run["id"] || Hash(record["lease_epoch"]) != Hash(run["lease_epoch"]) || record["executor_id"] != run["executor_principal_id"] || Hash(task["input_refs"]) != Hash(evolutionInputs(x)) {
		return "FAIL", "native execution run/epoch/input binding changed"
	}
	if e = evolutionCheckContract(task["acceptance_contract"].(map[string]any), phase); e != nil {
		return "FAIL", e.Error()
	}
	artifacts := Arr(snap, "artifacts")
	if len(artifacts) != 1 || Hash(snap["artifact_refs"]) != Hash([]any{record["artifact_ref"]}) {
		return "FAIL", "exact host sealed output required"
	}
	entry := artifacts[0].(map[string]any)
	raw, e := Decode(entry["bytes"].([]byte))
	if e != nil || Hash(raw) != Hash(record["observation"]) {
		return "FAIL", "caller report differs from immutable host observation"
	}
	if e = s.evolutionRecordValid(tx, project, x, record); e != nil {
		return "FAIL", e.Error()
	}
	return "PASS", string(Bytes(Object{"execution_hash": record["receipt_hash"], "phase": phase, "scope": evolution.Scope, "required_passed": record["required_passed"], "improved": record["improved"], "observation_verified": true, "release_authority": "NONE"}))
}
func (s *Service) evolutionAccepted(tx *sql.Tx, project string, x Object, phase, receiptID string) (Object, error) {
	if receiptID == "" {
		return nil, Fail(422, "GATE_FAILED", "independent acceptance required")
	}
	a, e := load(tx, project, "AcceptanceReceipt", receiptID)
	if e != nil {
		return nil, e
	}
	if a["verdict"] != "PASS" || a["measurement_mode"] != "FIXTURE" || a["receipt_hash"] != Receipt(a) {
		return nil, Fail(422, "GATE_FAILED", "valid independent fixture receipt required")
	}
	ref := a["subject_ref"].(map[string]any)
	if ref["entity_type"] != "Task" {
		return nil, Fail(422, "GATE_FAILED", "normal Task/Run acceptance required")
	}
	task, e := load(tx, project, "Task", Str(ref, "id"))
	if e != nil {
		return nil, e
	}
	if task["status"] != "ACCEPTED" || task["acceptance_id"] != a["id"] {
		return nil, Fail(422, "GATE_FAILED", "accepted task missing")
	}
	if e = s.acceptedTaskBinding(tx, project, task); e != nil {
		return nil, e
	}
	if e = s.taskContext(tx, project, task); e != nil {
		return nil, e
	}
	if e = retentionIndependent(tx, task, a); e != nil {
		return nil, e
	}
	var count int
	if e = tx.QueryRow("SELECT count(*) FROM evolution_tasks WHERE project=? AND task=? AND candidate=? AND phase=?", project, task["id"], x["id"], phase).Scan(&count); e != nil || count != 1 {
		return nil, Fail(422, "GATE_FAILED", "receipt belongs to another candidate or phase")
	}
	var author string
	if e = tx.QueryRow("SELECT creator FROM evolution_candidates WHERE project=? AND candidate=?", project, x["id"]).Scan(&author); e != nil {
		return nil, e
	}
	authorRoot, e := authorityRoot(tx, author)
	if e != nil {
		return nil, e
	}
	verifierRoot, e := authorityRoot(tx, Str(a, "verifier_principal_id"))
	if e != nil {
		return nil, e
	}
	if authorRoot == verifierRoot {
		return nil, Fail(403, "FORBIDDEN", "candidate author cannot verify own evolution")
	}
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, e
	}
	if Hash(state["policy_revision"]) != Hash(a["policy_revision"]) || len(Arr(state, "blocking_conflict_ids")) != 0 {
		return nil, Fail(422, "GATE_FAILED", "current policy or blocking conflict changed")
	}
	r, e := evolutionRecord(tx, project, Str(x, "id"), phase)
	if e != nil {
		return nil, e
	}
	if r["run_id"] != a["run_id"] || Hash(a["artifact_refs"]) != Hash([]any{r["artifact_ref"]}) {
		return nil, Fail(422, "GATE_FAILED", "independent receipt not bound to actual native run")
	}
	if e = s.evolutionRecordValid(tx, project, x, r); e != nil {
		return nil, e
	}
	return r, nil
}
