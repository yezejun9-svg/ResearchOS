//go:build windows

package domain

import (
	"context"
	"crypto/rand"
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"researchos.local/research-os/evaluation/evolution"
	"researchos.local/research-os/ops/supervisor"
	"time"
)

func evolutionInputs(x Object) []any {
	return []any{x["candidate_artifact_ref"], x["stable_artifact_ref"], x["baseline_suite_ref"], x["changed_paths_manifest_ref"], x["rollback_plan_ref"]}
}
func evolutionIDs() []any {
	ids := Empty()
	for _, c := range evolution.Suite() {
		ids = append(ids, c.Input.ID)
	}
	return ids
}
func evolutionExpected(phase string) Object {
	return Object{"suite_hash": Digest(evolution.Bytes(evolution.Suite())), "phase": phase, "scope": evolution.Scope}
}
func evolutionCheckContract(c Object, phase string) error {
	return evolutionCheckContractFor(c, phase, evolutionIDs(), evolutionExpected(phase))
}

func evolutionCheckContractFor(c Object, phase string, ids []any, hostExpected Object) error {
	checks := Arr(c, "checks")
	expectedCount := 1
	if phase == "REGRESSION" {
		expectedCount = 2
	}
	if len(checks) != expectedCount || c["require_independent_verifier"] != true || c["version_policy"] != "EXACT" || c["contract_hash"] != contractDigest(c) {
		return Fail(422, "GATE_FAILED", "exact independent evolution contract required")
	}
	seen := map[string]bool{}
	for _, v := range checks {
		check := v.(map[string]any)
		key := Str(check, "command_key")
		if seen[key] || check["required"] != true || check["kind"] != "DETERMINISTIC" || check["rubric_ref"] != nil || check["qualification_id"] != nil {
			return Fail(422, "GATE_FAILED", "all trusted checks mandatory")
		}
		seen[key] = true
		expected, e := Decode([]byte(Str(check, "expected")))
		if e != nil {
			return e
		}
		if key == "experiments.paired-mean-v1" && phase == "REGRESSION" {
			if Hash(expected) != Hash(Object{"expected_case_ids": ids}) {
				return Fail(422, "GATE_FAILED", "candidate changed required or negative cases")
			}
		} else if key == "evolution.regression-v1" && phase == "REGRESSION" || key == "evolution.canary-v1" && phase == "CANARY" {
			if Hash(expected) != Hash(hostExpected) {
				return Fail(422, "GATE_FAILED", "trusted evolution suite binding required")
			}
		} else {
			return Fail(422, "GATE_FAILED", "unknown evolution check")
		}
	}
	return nil
}
func (s *Service) IsolateEvolutionFixture(ctx context.Context, token, project, id string) (Object, error) {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	p, e := resourcePrincipal(tx, token, project, "SCHEDULER")
	if e != nil {
		return nil, e
	}
	x, e := load(tx, project, "SystemCandidate", id)
	if e != nil {
		return nil, e
	}
	if x["status"] != "DRAFT" {
		return nil, Fail(409, "STATE_CONFLICT", "isolate once before evaluation")
	}
	h, e := s.evolutionCurrent(tx, project, x)
	if e != nil {
		return nil, e
	}
	_, binary, e := s.evolutionBytes(tx, project, x["candidate_artifact_ref"].(map[string]any))
	if e != nil {
		return nil, e
	}
	path := filepath.Join(Str(h, "root"), id)
	if e = os.Mkdir(path, 0700); e != nil {
		return nil, e
	}
	committed := false
	defer func() {
		if !committed {
			os.RemoveAll(path)
		}
	}()
	if e = os.WriteFile(filepath.Join(path, "candidate.exe"), binary, 0600); e != nil {
		return nil, e
	}
	x["status"] = "ISOLATED"
	if e = bump(x); e != nil {
		return nil, e
	}
	if e = s.put(tx, "SystemCandidate", x); e != nil {
		return nil, e
	}
	if e = evolutionJournal(tx, project, id, "", "ISOLATED", Object{"workspace_id": x["isolated_workspace_id"], "path": path, "build_hash": Digest(binary), "host_pid": os.Getpid(), "scope": evolution.Scope}); e != nil {
		return nil, e
	}
	if e = s.event(tx, project, "SystemCandidate", x, p.ID, ID(), "PROJECT_UPDATED"); e != nil {
		return nil, e
	}
	if e = tx.Commit(); e != nil {
		return nil, e
	}
	committed = true
	return x, nil
}
func (s *Service) BindEvolutionTask(ctx context.Context, token, project, id, taskID, phase string) error {
	if phase != "REGRESSION" && phase != "CANARY" {
		return fmt.Errorf("unknown phase")
	}
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	if _, e = resourcePrincipal(tx, token, project, "SCHEDULER"); e != nil {
		return e
	}
	x, e := load(tx, project, "SystemCandidate", id)
	if e != nil {
		return e
	}
	if phase == "REGRESSION" && x["status"] != "EVALUATING" || phase == "CANARY" && x["status"] != "CANARY" {
		return Fail(409, "STATE_CONFLICT", "candidate phase not admitted")
	}
	h, e := s.evolutionCurrent(tx, project, x)
	if e != nil {
		return e
	}
	t, e := load(tx, project, "Task", taskID)
	if e != nil {
		return e
	}
	if t["active_run_id"] != nil || Hash(t["input_refs"]) != Hash(evolutionInputs(x)) {
		return Fail(422, "GATE_FAILED", "bind exact candidate inputs before claim")
	}
	if e = s.evolutionHostContract(tx, project, h, t["acceptance_contract"].(map[string]any), phase); e != nil {
		return e
	}
	if phase == "REGRESSION" {
		experiment, e := load(tx, project, "Experiment", Str(x, "experiment_id"))
		if e != nil {
			return e
		}
		if Hash(t["acceptance_contract"]) != Hash(experiment["acceptance_contract"]) {
			return Fail(422, "GATE_FAILED", "same frozen experiment contract required")
		}
	}
	_, e = tx.Exec("INSERT INTO evolution_tasks(project,task,candidate,phase) VALUES(?,?,?,?)", project, taskID, id, phase)
	if e != nil {
		return e
	}
	return tx.Commit()
}
func evolutionJournal(tx *sql.Tx, project, id, run, event string, body Object) error {
	b := Merge(Object{"project_id": project, "candidate_id": id, "run_id": run, "event": event, "at": Now(), "scope": evolution.Scope}, body)
	_, e := tx.Exec("INSERT INTO evolution_journal(project,candidate,run,event,body,receipt_hash) VALUES(?,?,?,?,?,?)", project, id, run, event, string(Bytes(b)), Hash(b))
	return e
}
func (s *Service) evolutionJournal(ctx context.Context, project, id, run, event string, body Object) error {
	tx, e := s.DB.BeginTx(context.WithoutCancel(ctx), nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	if e = evolutionJournal(tx, project, id, run, event, body); e != nil {
		return e
	}
	return tx.Commit()
}

// ExecuteEvolutionFixture executes only sealed, host-registered binaries. Every
// phase has one durable reservation; a lost result cannot trigger redispatch.
func (s *Service) ExecuteEvolutionFixture(ctx context.Context, workerToken, releaseToken, project, id, runID string, lease Object) (Object, error) {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	p, e := authenticate(tx, workerToken)
	if e != nil {
		return nil, e
	}
	r, e := currentRun(tx, p, project, runID)
	if e != nil {
		return nil, e
	}
	if e = runtimeLease(tx, p, project, r, lease); e != nil {
		return nil, e
	}
	if r["status"] != "RUNNING" {
		return nil, Fail(409, "STATE_CONFLICT", "heartbeat before invocation")
	}
	x, e := load(tx, project, "SystemCandidate", id)
	if e != nil {
		return nil, e
	}
	h, e := s.evolutionCurrent(tx, project, x)
	if e != nil {
		return nil, e
	}
	release, e := resourcePrincipal(tx, releaseToken, project, "SCHEDULER")
	if e != nil {
		return nil, e
	}
	if release.ID != h["release_principal"] || !release.HasRole("RELEASE_SERVICE") {
		return nil, Fail(403, "FORBIDDEN", "registered release host credential required")
	}
	var phase string
	if e = tx.QueryRow("SELECT phase FROM evolution_tasks WHERE project=? AND candidate=? AND task=?", project, id, r["task_id"]).Scan(&phase); e != nil {
		return nil, Fail(422, "GATE_FAILED", "run has no candidate binding")
	}
	if phase == "REGRESSION" && x["status"] != "EVALUATING" || phase == "CANARY" && x["status"] != "CANARY" {
		return nil, Fail(409, "STATE_CONFLICT", "candidate not admitted")
	}
	t, e := load(tx, project, "Task", Str(r, "task_id"))
	if e != nil {
		return nil, e
	}
	if Hash(t["input_refs"]) != Hash(evolutionInputs(x)) || Hash(r["input_refs"]) != Hash(t["input_refs"]) {
		return nil, Fail(422, "GATE_FAILED", "current run input binding mismatch")
	}
	if e = s.evolutionHostContract(tx, project, h, t["acceptance_contract"].(map[string]any), phase); e != nil {
		return nil, e
	}
	if e = s.taskContextForRun(tx, project, r); e != nil {
		return nil, e
	}
	experiment, e := load(tx, project, "Experiment", Str(x, "experiment_id"))
	if e != nil {
		return nil, e
	}
	if phase == "REGRESSION" {
		var count int
		if e = tx.QueryRow("SELECT count(*) FROM experiment_runs WHERE project=? AND experiment=? AND run=?", project, experiment["id"], runID).Scan(&count); e != nil || count != 1 || experiment["status"] != "RUNNING" {
			return nil, Fail(422, "GATE_FAILED", "existing W10 experiment run required")
		}
	}
	if phase == "CANARY" {
		if _, e = s.evolutionAccepted(tx, project, x, "REGRESSION", Str(x, "regression_acceptance_id")); e != nil {
			return nil, e
		}
		deadline, err := time.Parse(time.RFC3339Nano, Str(x, "observation_deadline"))
		if err != nil || !deadline.After(time.Now()) {
			return nil, Fail(409, "STATE_CONFLICT", "canary observation deadline expired")
		}
	}
	_, stable, e := s.evolutionBytes(tx, project, x["stable_artifact_ref"].(map[string]any))
	if e != nil {
		return nil, e
	}
	_, candidate, e := s.evolutionBytes(tx, project, x["candidate_artifact_ref"].(map[string]any))
	if e != nil {
		return nil, e
	}
	goal, e := load(tx, project, "Goal", Str(t, "goal_id"))
	if e != nil {
		return nil, e
	}
	expiry, e := time.Parse(time.RFC3339Nano, Str(r, "lease_expires_at"))
	if e != nil {
		return nil, e
	}
	if phase == "CANARY" {
		deadline, _ := time.Parse(time.RFC3339Nano, Str(x, "observation_deadline"))
		if deadline.Before(expiry) {
			expiry = deadline
		}
	}
	caseIDs, e := s.evolutionHostCaseIDs(tx, project, h)
	if e != nil {
		return nil, e
	}
	if controlHost(h) {
		if _, _, e = s.evolutionHoldoutVerdict(ctx, tx, project, x); e != nil {
			return nil, e
		}
	}
	record := Object{"project_id": project, "candidate_id": id, "run_id": runID, "lease_epoch": r["lease_epoch"], "phase": phase, "plan_hash": Hash(evolutionPlan(x)), "suite_hash": evolutionSuiteHash(h), "policy_hash": evolutionPolicyHash(h), "baseline_hash": Digest(stable), "candidate_hash": Digest(candidate), "scope": evolution.Scope, "executor_id": p.ID, "host_pid": os.Getpid(), "started_at": Now(), "state": "RESERVED", "improved": false, "required_passed": false}
	if _, e = tx.Exec("INSERT INTO evolution_executions(project,candidate,phase,run,epoch,state,body) VALUES(?,?,?,?,?,'RESERVED',?)", project, id, phase, runID, r["lease_epoch"], string(Bytes(record))); e != nil {
		return nil, Fail(409, "STATE_CONFLICT", "phase already reserved; reconcile instead of retry")
	}
	if e = tx.Commit(); e != nil {
		return nil, e
	}
	runCtx, cancel := context.WithDeadline(ctx, expiry)
	defer cancel()
	done := make(chan struct{})
	defer close(done)
	go s.watchEvolutionLease(runCtx, cancel, done, project, runID, r)
	if phase == "REGRESSION" {
		pair, err := s.evaluateEvolutionRegression(runCtx, project, x, h, stable, candidate, record)
		if err != nil {
			return nil, s.finishEvolutionFixture(ctx, workerToken, project, x, r, record, err)
		}
		record["improved"], record["required_passed"] = pair.Improved, pair.CandidateResult.RequiredPassed
		proofTx, err := s.DB.BeginTx(runCtx, nil)
		if err != nil {
			return nil, s.finishEvolutionFixture(ctx, workerToken, project, x, r, record, err)
		}
		holdout, proofHash, holdoutErr := s.evolutionHoldoutVerdict(runCtx, proofTx, project, x)
		proofTx.Rollback()
		if holdoutErr != nil {
			return nil, s.finishEvolutionFixture(ctx, workerToken, project, x, r, record, holdoutErr)
		}
		if holdout != nil {
			record["holdout_summary"], record["holdout_proof_hash"] = holdout, proofHash
			record["improved"] = pair.Improved && holdout["gain"] == true
		}
		base, cand := Empty(), Empty()
		for _, v := range pair.BaselineResult.Values {
			base = append(base, v)
		}
		for _, v := range pair.CandidateResult.Values {
			cand = append(cand, v)
		}
		observation := Object{"experiment_id": experiment["id"], "preregistration_hash": experiment["preregistration_hash"], "evolution_id": id, "phase": phase, "observations": []any{Object{"metric_id": "correctness", "case_ids": caseIDs, "baseline": base, "candidate": cand}}}
		results, outcome, err := recomputeExperiment(experiment, observation)
		if err != nil {
			return nil, s.finishEvolutionFixture(ctx, workerToken, project, x, r, record, err)
		}
		observation["results"], observation["outcome"] = results, outcome
		record["observation"] = observation
	} else {
		if err := s.runEvolutionCanary(runCtx, releaseToken, project, x, r, h, goal, stable, candidate, record); err != nil {
			return nil, s.finishEvolutionFixture(ctx, workerToken, project, x, r, record, err)
		}
	}
	record["state"] = "RECORDED"
	if e = s.finishEvolutionFixture(ctx, workerToken, project, x, r, record, nil); e != nil {
		return nil, e
	}
	return record, nil
}
func (s *Service) watchEvolutionLease(ctx context.Context, cancel context.CancelFunc, done <-chan struct{}, project, run string, original Object) {
	t := time.NewTicker(25 * time.Millisecond)
	defer t.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-done:
			return
		case <-t.C:
			var status, expiry string
			var epoch int64
			e := s.DB.QueryRow("SELECT json_extract(body,'$.status'),json_extract(body,'$.lease_epoch'),json_extract(body,'$.lease_expires_at') FROM domain_objects WHERE project=? AND kind='Run' AND id=?", project, run).Scan(&status, &epoch, &expiry)
			want, _ := Num(original, "lease_epoch")
			end, te := time.Parse(time.RFC3339Nano, expiry)
			if e != nil || te != nil || epoch != want || status != "RUNNING" || !time.Now().Before(end) {
				cancel()
				return
			}
		}
	}
}
func (s *Service) finishEvolutionFixture(ctx context.Context, token, project string, x, r, record Object, cause error) error {
	tx, e := s.DB.BeginTx(context.WithoutCancel(ctx), nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	record["finished_at"] = Now()
	if cause != nil {
		record["state"] = "FAILED"
		record["error"] = cause.Error()
	}
	current, e := load(tx, project, "Run", Str(r, "id"))
	if e != nil {
		return e
	}
	p, e := authenticate(tx, token)
	if e == nil {
		e = validExecutorRun(tx, p, project, current)
	}
	if e != nil || current["status"] != "RUNNING" || Hash(current["lease_epoch"]) != Hash(r["lease_epoch"]) {
		record["state"] = "FAILED"
		record["error"] = "run ownership changed"
		cause = Fail(409, "STATE_CONFLICT", "run ownership changed")
	}
	if record["state"] == "RECORDED" {
		raw := Bytes(record["observation"])
		u, e := s.runtimeUpload(tx, p, project, raw)
		if e != nil {
			return e
		}
		a, e := s.runtimeSeal(tx, p, project, Object{"run_id": r["id"], "kind": "REPORT", "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE", "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "application/json", "byte_size": len(raw), "input_refs": r["input_refs"], "source_refs": Empty(), "produced_by": p.ID, "access_class": "PROJECT"})
		if e != nil {
			return e
		}
		record["artifact_ref"] = Ref(a, "Artifact")
		record["artifact_id"] = a["id"]
		record["runtime_artifacts"] = []any{Object{"path": "evolution-observation.json", "content_hash": a["content_hash"], "byte_size": a["byte_size"]}}
		if e = s.event(tx, project, "Artifact", a, p.ID, ID(), "PROJECT_UPDATED"); e != nil {
			return e
		}
	}
	if record["phase"] == "CANARY" || cause != nil {
		candidate, e := load(tx, project, "SystemCandidate", Str(x, "id"))
		if e != nil {
			return e
		}
		if !evolutionTerminal(candidate) {
			candidate["status"] = "FROZEN"
			candidate["freeze_reason"] = "bounded fixture trial ended or failed; no automatic retry or LIVE promotion"
			if e = bump(candidate); e != nil {
				return e
			}
			if e = s.put(tx, "SystemCandidate", candidate); e != nil {
				return e
			}
			if e = s.event(tx, project, "SystemCandidate", candidate, "evolution-host", ID(), "PROJECT_UPDATED"); e != nil {
				return e
			}
		}
	}
	record["receipt_hash"] = Receipt(record)
	res, e := tx.Exec("UPDATE evolution_executions SET state=?,body=?,receipt_hash=? WHERE project=? AND candidate=? AND phase=? AND state='RESERVED'", record["state"], string(Bytes(record)), record["receipt_hash"], project, x["id"], record["phase"])
	if e != nil {
		return e
	}
	n, e := res.RowsAffected()
	if e != nil || n != 1 {
		return fmt.Errorf("execution finalization fence changed")
	}
	if e = evolutionJournal(tx, project, Str(x, "id"), Str(r, "id"), "EXECUTION_FINAL", Object{"phase": record["phase"], "state": record["state"], "execution_hash": record["receipt_hash"]}); e != nil {
		return e
	}
	if e = tx.Commit(); e != nil {
		return e
	}
	return cause
}

func (s *Service) runEvolutionCanary(ctx context.Context, releaseToken, project string, x, r, h, goal Object, stable, candidate []byte, record Object) error {
	id, runID := Str(x, "id"), Str(r, "id")
	key := "w16-canary-" + runID
	cost := Object{"policy_id": goal["budget_policy_id"], "run_id": runID, "operation": "RESERVE", "money": Object{"amount": "0", "currency": "USD"}, "provider_request_id": key, "provider_event_id": key, "reservation_id": nil, "cost_basis": "UPPER_BOUND", "occurred_at": Now()}
	if _, e := s.PrepareEffect(ctx, releaseToken, project, runID, key, Object{"candidate_id": id, "plan_hash": record["plan_hash"], "scope": evolution.Scope}, cost); e != nil {
		return e
	}
	if _, e := s.BeginEffect(ctx, releaseToken, project, runID, key); e != nil {
		return e
	}
	work := filepath.Join(Str(h, "root"), id, "trial-"+runID)
	if e := os.Mkdir(work, 0700); e != nil {
		return e
	}
	recoveryKey := make([]byte, 32)
	if _, e := rand.Read(recoveryKey); e != nil {
		return e
	}
	defer clear(recoveryKey)
	if e := os.WriteFile(filepath.Join(work, "recovery.key"), recoveryKey, 0600); e != nil {
		return e
	}
	backupPath := filepath.Join(work, "backup")
	manifest, e := s.CreateBackup(ctx, backupPath, recoveryKey)
	if e != nil {
		return e
	}
	record["backup_manifest"] = manifest
	if e = s.evolutionJournal(ctx, project, id, runID, "BACKUP_VERIFIED", Object{"backup_path": backupPath, "backup_id": manifest.ID, "inventory_hash": Hash(manifest.Inventory), "migrations": manifest.Migrations}); e != nil {
		return e
	}
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	var state string
	var active string
	if e = tx.QueryRow("SELECT state,active_hash FROM evolution_slots WHERE project=?", project).Scan(&state, &active); e != nil {
		return e
	}
	if state != "STABLE" || active != Digest(stable) {
		return Fail(409, "STATE_CONFLICT", "single active fixture slot occupied")
	}
	if _, e = tx.Exec("UPDATE evolution_slots SET active_hash=?,candidate=?,epoch=epoch+1,state='CANARY' WHERE project=?", Digest(candidate), id, project); e != nil {
		return e
	}
	if e = evolutionJournal(tx, project, id, runID, "SLOT_CANARY", Object{"old_hash": Digest(stable), "new_hash": Digest(candidate), "backup_path": backupPath}); e != nil {
		return e
	}
	if e = tx.Commit(); e != nil {
		return e
	}
	observed := supervisor.Invoke(ctx, candidate, "CANARY", nil)
	record["canary"] = observed
	measured, err := supervisor.Verify(observed, Digest(candidate))
	record["observed_regression"] = err != nil || !measured.RequiredPassed
	// Every development trial is finite and returns to the previous stable build.
	// A successful fixture trial never acquires LIVE promotion authority.
	if e = s.evolutionJournal(ctx, project, id, runID, "ROLLBACK_STARTED", Object{"observed_regression": record["observed_regression"], "raw_hash": observed.RawHash, "threshold": 0, "actual_required_failure": err != nil || !measured.RequiredPassed, "self_score_authority": "NONE"}); e != nil {
		return e
	}
	restoredPath := filepath.Join(work, "restored")
	restored, e := RestoreBackup(context.WithoutCancel(ctx), backupPath, restoredPath, RestoreOptions{Key: recoveryKey, SupportedMigrations: manifest.Migrations, Contracts: s.Contracts})
	if e != nil {
		return e
	}
	record["restore"] = restored
	// Opening/readback is done by W18. Start the exact previous binary again and
	// independently verify the frozen health suite after the actual data restore.
	health := supervisor.Invoke(context.WithoutCancel(ctx), stable, "HEALTH", nil)
	record["stable_health"] = health
	result, e := supervisor.Verify(health, Digest(stable))
	if e != nil || !result.RequiredPassed {
		return fmt.Errorf("stable native health failed after restore: %v", e)
	}
	if restored.Status != "RESTORED_RECONCILIATION_REQUIRED" || Hash(restored.Before) != Hash(manifest.Inventory) {
		return fmt.Errorf("rollback restored data not bound to backup")
	}
	tx, e = s.DB.BeginTx(context.WithoutCancel(ctx), nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	res, e := tx.Exec("UPDATE evolution_slots SET active_hash=stable_hash,candidate=NULL,epoch=epoch+1,state='STABLE' WHERE project=? AND candidate=? AND state='CANARY'", project, id)
	if e != nil {
		return e
	}
	if n, err := res.RowsAffected(); err != nil || n != 1 {
		return fmt.Errorf("fixture rollback slot fence changed: %v", err)
	}
	if e = evolutionJournal(tx, project, id, runID, "SLOT_STABLE", Object{"active_hash": Digest(stable), "restored_path": restoredPath, "restored_inventory_hash": Hash(restored.Before), "health_raw_hash": health.RawHash, "health_pid": health.Receipt.PID}); e != nil {
		return e
	}
	if e = tx.Commit(); e != nil {
		return e
	}
	if e = s.ObserveEffect(context.WithoutCancel(ctx), project, runID, key, "CONFIRMED", Object{"trial": "ROLLED_BACK", "stable_hash": Digest(stable), "backup_id": manifest.ID, "health_hash": health.RawHash}); e != nil {
		return e
	}
	record["observation"] = Object{"evolution_id": id, "phase": "CANARY", "scope": evolution.Scope, "restored_hash": Digest(stable), "backup_id": manifest.ID, "inventory_hash": Hash(restored.Before), "observed_regression": record["observed_regression"], "native_stable_healthy": true, "active_candidate_after": nil, "canary_raw_hash": observed.RawHash, "health_raw_hash": health.RawHash}
	return nil
}

func decodePair(v any) (supervisor.Pair, error) {
	var p supervisor.Pair
	e := json.Unmarshal(Bytes(v), &p)
	return p, e
}
