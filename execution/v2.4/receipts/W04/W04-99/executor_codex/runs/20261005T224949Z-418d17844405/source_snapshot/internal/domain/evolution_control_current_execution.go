//go:build windows

package domain

import (
	"context"
	"database/sql"
	"fmt"
	"researchos.local/research-os/evaluation/evolution"
	"researchos.local/research-os/ops/supervisor"
	"time"
)

func (s *Service) controlCurrentGate(tx *sql.Tx, h, x Object) (Object, error) {
	c, ok := h["current_control"].(map[string]any)
	if !ok {
		return nil, nil
	}
	a, err := s.currentControlSession(Str(c, "session_id"))
	if err != nil {
		return nil, err
	}
	// Immutable freeze fields are published before the native operation begins.
	if a.frozen == nil || a.frozen.Candidate != x["id"] || a.frozen.Plan != Hash(evolutionPlan(x)) {
		return nil, fmt.Errorf("CONTROL_CURRENT_G0_BINDING_REQUIRED")
	}
	if err = a.reservationCurrent(tx); err != nil {
		return nil, err
	}
	delta, err := a.validateCurrentRows(tx)
	if err != nil {
		return nil, err
	}
	return Object{"purpose": evolution.ControlCurrentPurpose, "profile": evolution.ControlCurrentProfile, "session_id": a.id, "b0_hash": a.b0.Generation, "g0_hash": a.g0.Generation, "owner_hash": Hash(a.owner), "plan_hash": a.frozen.Plan, "verifier_id": a.frozen.Verifier, "delta_hash": Hash(delta)}, nil
}

func (s *Service) evaluateCurrentControl(ctx context.Context, a *currentControlAuthority, req evolution.ControlCurrentRequest) (evolution.ControlCurrentReply, error) {
	var out evolution.ControlCurrentReply
	a.mu.Lock()
	if a.frozen == nil {
		a.mu.Unlock()
		return out, fmt.Errorf("CONTROL_CURRENT_G0_REQUIRED")
	}
	if a.evaluated {
		a.mu.Unlock()
		return s.completedCurrentEvaluation(ctx, a, req)
	}
	if a.evaluating {
		a.mu.Unlock()
		return out, fmt.Errorf("CONTROL_CURRENT_EVALUATION_UNKNOWN_INSPECTION_REQUIRED")
	}
	a.evaluating = true
	a.mu.Unlock()
	n := a.frozen
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return out, err
	}
	p, err := authenticate(tx, req.VerifierToken)
	if err != nil || p.ID != n.Verifier {
		tx.Rollback()
		return out, fmt.Errorf("CONTROL_CURRENT_VERIFIER_CHANGED")
	}
	run, err := currentRun(tx, p, a.project, n.Run)
	if err != nil {
		tx.Rollback()
		return out, err
	}
	worker, err := authenticate(tx, req.WorkerToken)
	if err != nil || worker.ID != n.Executor {
		tx.Rollback()
		return out, fmt.Errorf("CONTROL_CURRENT_EXECUTOR_CHANGED")
	}
	if err = runtimeLease(tx, worker, a.project, run, req.Lease); err != nil {
		tx.Rollback()
		return out, err
	}
	if err = validExecutorRun(tx, worker, a.project, run); err != nil {
		tx.Rollback()
		return out, err
	}
	if _, err = a.validateCurrentRows(tx); err != nil {
		tx.Rollback()
		return out, err
	}
	if err = a.reserveCurrentEvaluation(tx); err != nil {
		tx.Rollback()
		return out, err
	}
	if err = tx.Commit(); err != nil {
		return out, err
	}
	expiry, err := time.Parse(time.RFC3339Nano, Str(run, "lease_expires_at"))
	if err != nil {
		return out, err
	}
	runCtx, cancel := context.WithDeadline(ctx, expiry)
	defer cancel()
	done := make(chan struct{})
	defer close(done)
	go s.watchEvolutionLease(runCtx, cancel, done, a.project, n.Run, run)
	if _, err = s.EvaluateEvolutionHoldoutFixture(runCtx, req.VerifierToken, a.project, n.Candidate); err != nil {
		return out, err
	}
	record, err := s.ExecuteEvolutionFixture(runCtx, req.WorkerToken, req.ReleaseToken, a.project, n.Candidate, n.Run, req.Lease)
	if err != nil {
		return out, err
	}
	tx, err = s.DB.BeginTx(ctx, nil)
	if err != nil {
		return out, err
	}
	defer tx.Rollback()
	x, err := load(tx, a.project, "SystemCandidate", n.Candidate)
	if err != nil {
		return out, err
	}
	h, err := s.evolutionCurrent(tx, a.project, x)
	if err != nil {
		return out, err
	}
	// Recompute both native proofs before creating any terminal observation.
	// CheckControl checks all process receipts, identities, exit/drain/cleanup.
	if err = s.controlRecordValid(tx, a.project, x, h, record); err != nil {
		return out, err
	}
	runtime, err := load(tx, a.project, "RuntimeRegistration", Str(run, "runtime_id"))
	if err != nil {
		return out, err
	}
	spec := Object{"run_id": n.Run, "task_id": n.Task, "epoch": n.Epoch, "technical_hash": runtimeTechnicalHash(runtime), "capabilities": []any{"start"}}
	var fixture int
	if err = tx.QueryRow("SELECT count(*) FROM orchestration_fixtures WHERE project=? AND runtime=?", a.project, runtime["id"]).Scan(&fixture); err != nil {
		return out, err
	}
	if fixture != 1 || runtime["measurement_mode"] != "FIXTURE" {
		return out, fmt.Errorf("CONTROL_CURRENT_REGISTERED_FIXTURE_RUNTIME_REQUIRED")
	}
	// This is the existing registered fixture path. Its process evidence comes
	// from the two checked ControlProofs below, not a claimed LIVE dispatch.
	var publicProof, privateProof supervisor.ControlProof
	if err = evolution.StrictControlJSON(Bytes(record["control_proof"]), &publicProof); err != nil {
		return out, err
	}
	privateEntry, present, err := evolutionHoldoutEntry(tx, a.project, n.Candidate, "HOLDOUT_EVALUATED")
	if err != nil || !present {
		return out, fmt.Errorf("CONTROL_CURRENT_PRIVATE_TERMINAL_ABSENT")
	}
	_, privateRaw, err := s.evolutionPrivateBytes(ctx, tx, a.project, privateEntry["proof_ref"].(map[string]any))
	if err != nil {
		return out, err
	}
	if err = evolution.StrictControlJSON(privateRaw, &privateProof); err != nil {
		return out, err
	}
	ended, err := controlNativeEnd(publicProof, privateProof)
	if err != nil {
		return out, err
	}
	observation := Object{"spec": spec, "state": "SETTLED", "children_stopped": true, "queue_empty": true, "exit_code": 0, "ended": ended, "recorded_at": Now(), "protocol": Object{"settled": true}, "artifacts": record["runtime_artifacts"], "control_current_session": a.id, "control_g0_hash": a.g0.Generation, "control_execution_hash": record["receipt_hash"], "control_native_proof_hash": Hash(record["control_proof"]), "holdout_proof_hash": record["holdout_proof_hash"]}
	tx.Rollback()
	if err = s.ObserveRuntime(ctx, a.project, n.Run, n.Epoch, observation); err != nil {
		return out, err
	}
	tx, err = s.DB.BeginTx(ctx, nil)
	if err != nil {
		return out, err
	}
	defer tx.Rollback()
	if _, err = a.validateCurrentRows(tx); err != nil {
		return out, err
	}
	if err = evolutionJournal(tx, a.project, n.Candidate, n.Run, controlCurrentRecorded, a.reservationBody()); err != nil {
		return out, err
	}
	if err = tx.Commit(); err != nil {
		return out, err
	}
	a.mu.Lock()
	a.evaluated = true
	a.observationRef = copyObject(record["artifact_ref"].(map[string]any))
	out = controlCurrentReply(a, "EVALUATE")
	out.ObservationRef = a.observationRef
	a.mu.Unlock()
	return out, nil
}

func (s *Service) sealCurrentControl(ctx context.Context, a *currentControlAuthority, req evolution.ControlCurrentRequest) (evolution.ControlCurrentReply, error) {
	a.mu.Lock()
	defer a.mu.Unlock()
	var out evolution.ControlCurrentReply
	if a.frozen == nil || !a.evaluated {
		return out, fmt.Errorf("CONTROL_CURRENT_NATIVE_EVALUATION_REQUIRED")
	}
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return out, err
	}
	defer tx.Rollback()
	p, err := authenticate(tx, req.VerifierToken)
	if err != nil || p.ID != a.frozen.Verifier {
		return out, fmt.Errorf("CONTROL_CURRENT_VERIFIER_CHANGED")
	}
	if err = a.currentEvaluationJournal(tx, controlCurrentRecorded); err != nil {
		return out, err
	}
	if a.sealed != nil {
		if err = a.currentOwner(tx); err != nil {
			return out, err
		}
		if err = a.independentVerifier(tx, p.ID, a.frozen); err != nil {
			return out, err
		}
		hash, e := evolution.ControlDatabaseHash(tx)
		if e != nil || hash != a.sealed.G1Hash {
			return out, fmt.Errorf("CONTROL_CURRENT_SEALED_GENERATION_STALE")
		}
		return *a.sealed, nil
	}
	delta, err := a.validateCurrentRows(tx)
	if err != nil {
		return out, err
	}
	x, err := load(tx, a.project, "SystemCandidate", a.frozen.Candidate)
	if err != nil {
		return out, err
	}
	if x["status"] != "REJECTED" || x["regression_acceptance_id"] != req.AcceptanceID {
		return out, fmt.Errorf("CONTROL_CURRENT_NORMAL_NONGAIN_GATE_REQUIRED")
	}
	record, err := s.evolutionAccepted(tx, a.project, x, "REGRESSION", req.AcceptanceID)
	if err != nil {
		return out, err
	}
	if record["improved"] != false {
		return out, fmt.Errorf("CONTROL_CURRENT_NONGAIN_PROFILE")
	}
	acceptance, err := load(tx, a.project, "AcceptanceReceipt", req.AcceptanceID)
	if err != nil {
		return out, err
	}
	if acceptance["verifier_principal_id"] != a.frozen.Verifier {
		return out, fmt.Errorf("CONTROL_CURRENT_ACCEPTANCE_VERIFIER")
	}
	exp, err := load(tx, a.project, "Experiment", a.frozen.Experiment)
	if err != nil || exp["status"] != "COMPLETED" || exp["acceptance_id"] != req.AcceptanceID {
		return out, fmt.Errorf("CONTROL_CURRENT_EXPERIMENT_ACCEPTANCE")
	}
	g1, err := evolution.ControlDatabaseHash(tx)
	if err != nil {
		return out, err
	}
	tx.Rollback()
	raw, err := controlCurrentSnapshot(ctx, s.DB)
	if err != nil {
		return out, err
	}
	snapshot, err := controlSavePrivateSnapshot(ctx, a.store, a.project, a.id, "G1", raw)
	if err != nil {
		return out, err
	}
	if snapshot.Generation != g1 {
		return out, fmt.Errorf("CONTROL_CURRENT_SEAL_MOVED")
	}
	proof := Object{"purpose": evolution.ControlCurrentPurpose, "profile": evolution.ControlCurrentProfile, "session_id": a.id, "project_id": a.project, "owner": a.owner, "source_provenance": a.provenance, "b0": a.b0, "g0": a.g0, "g1": snapshot, "preparation_delta": a.preparationDelta, "evaluation_delta": delta, "acceptance_ref": Ref(acceptance, "AcceptanceReceipt"), "execution_hash": record["receipt_hash"], "private_verifier_id": a.frozen.Verifier, "positive_gain": false, "normal_release_authorized": false, "os_service_qualified": false, "created_at": time.Now().UTC().Format(time.RFC3339Nano)}
	blob, err := a.store.CreateCanary(ctx, a.project, "application/vnd.researchos.control-current-proof", Bytes(proof))
	if err != nil {
		return out, err
	}
	tx, err = s.DB.BeginTx(ctx, nil)
	if err != nil {
		return out, err
	}
	defer tx.Rollback()
	if err = a.currentOwner(tx); err != nil {
		return out, err
	}
	hash, err := evolution.ControlDatabaseHash(tx)
	if err != nil || hash != g1 {
		return out, fmt.Errorf("CONTROL_CURRENT_FINAL_GENERATION_MOVED")
	}
	out = controlCurrentReply(a, "SEAL")
	out.G1Hash = g1
	out.DeltaHash = Hash(delta)
	out.ProofHash = blob.Hash
	out.ProofRef = Object{"ticket": blob.Ticket, "content_hash": blob.Hash, "byte_size": blob.Size, "measurement_mode": "FIXTURE", "access_class": "RESTRICTED"}
	out.Current = true
	out.Summary = Object{"normal_acceptance_consumed": true, "nongain_gate": "REJECTED", "positive_gain": false, "g0_to_g1_delta_count": len(delta), "source_snapshot_hash": a.b0.Hash, "projection_snapshot_hash": a.binding.SnapshotHash}
	a.sealed = &out
	return out, nil
}
