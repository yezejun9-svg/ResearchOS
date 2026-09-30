//go:build windows

package domain

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"researchos.local/research-os/adapters/protectedstore"
	"researchos.local/research-os/evaluation/evolution"
	"researchos.local/research-os/ops/supervisor"
)

// Journal entries are host-only durable bindings. They contain protected
// Artifact refs, never private bytes, and are not published as project events.
func evolutionHoldoutEntry(tx *sql.Tx, project, candidate, event string) (Object, bool, error) {
	rows, err := tx.Query("SELECT body,receipt_hash FROM evolution_journal WHERE project=? AND candidate=? AND event=?", project, candidate, event)
	if err != nil {
		return nil, false, err
	}
	defer rows.Close()
	var result Object
	count := 0
	for rows.Next() {
		var raw, hash string
		if err = rows.Scan(&raw, &hash); err != nil {
			return nil, false, err
		}
		result, err = Decode([]byte(raw))
		if err != nil || Hash(result) != hash || result["project_id"] != project || result["candidate_id"] != candidate || result["event"] != event || result["scope"] != evolution.Scope {
			return nil, false, Fail(422, "GATE_FAILED", "private holdout journal binding invalid")
		}
		count++
	}
	if err = rows.Err(); err != nil {
		return nil, false, err
	}
	if count > 1 {
		return nil, false, Fail(422, "GATE_FAILED", "duplicate private holdout host binding")
	}
	return result, count == 1, nil
}

func (s *Service) evolutionPrivateBytes(ctx context.Context, tx *sql.Tx, project string, ref Object) (Object, []byte, error) {
	if _, ok := s.Protected.(*protectedstore.CanaryStore); !ok {
		return nil, nil, Fail(503, "RESOURCE_UNAVAILABLE", "C20 private fixture store unavailable")
	}
	if ref["entity_type"] != "Artifact" {
		return nil, nil, Fail(422, "GATE_FAILED", "protected Artifact reference required")
	}
	if err := s.effective(tx, project, ref); err != nil {
		return nil, nil, err
	}
	a, err := version(tx, project, ref)
	if err != nil {
		return nil, nil, err
	}
	if a["access_class"] != "VERIFIER_ONLY" || a["measurement_mode"] != "FIXTURE" {
		return nil, nil, Fail(422, "GATE_FAILED", "private FIXTURE artifact required")
	}
	size, err := Num(a, "byte_size")
	if err != nil {
		return nil, nil, err
	}
	blob := protectedstore.Blob{Ticket: Str(a, "storage_key"), Project: project, Hash: Str(a, "content_hash"), Size: size, MediaType: Str(a, "media_type"), MeasurementMode: "FIXTURE"}
	if !blob.Valid() {
		return nil, nil, Fail(422, "GATE_FAILED", "private fixture descriptor invalid")
	}
	if err = s.protectedReady(ctx, "FIXTURE"); err != nil {
		return nil, nil, err
	}
	got, err := s.Protected.Describe(ctx, project, blob.Ticket)
	if err != nil || got != blob {
		return nil, nil, Fail(422, "GATE_FAILED", "private fixture descriptor changed")
	}
	raw, err := s.Protected.Read(ctx, blob)
	if err != nil || Digest(raw) != blob.Hash {
		return nil, nil, Fail(422, "GATE_FAILED", "private holdout body missing or altered")
	}
	return a, raw, nil
}

func decodeEvolutionHoldout(inputsRaw, labelsRaw []byte) (evolution.HoldoutInputs, evolution.HoldoutLabels, error) {
	var inputs evolution.HoldoutInputs
	var labels evolution.HoldoutLabels
	if err := json.Unmarshal(inputsRaw, &inputs); err != nil {
		return inputs, labels, err
	}
	if err := json.Unmarshal(labelsRaw, &labels); err != nil {
		return inputs, labels, err
	}
	return inputs, labels, evolution.ValidateHoldout(inputs, labels)
}

// RegisterEvolutionHoldoutFixture freezes independently labeled private inputs
// for exactly one candidate. It is a trusted local host method with no HTTP
// route; normal C09/C10/C12 development candidates remain unchanged.
func (s *Service) RegisterEvolutionHoldoutFixture(ctx context.Context, token, project, candidate string, inputsRef, labelsRef Object) error {
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	p, err := authenticate(tx, token)
	if err != nil {
		return err
	}
	if !protectedAllowed(p, project) {
		return Fail(403, "FORBIDDEN", "restricted independent C20 verifier required")
	}
	x, err := load(tx, project, "SystemCandidate", candidate)
	if err != nil {
		return err
	}
	if x["status"] != "EVALUATING" {
		return Fail(409, "STATE_CONFLICT", "freeze private holdout before regression")
	}
	h, err := s.evolutionCurrent(tx, project, x)
	if err != nil {
		return err
	}
	var author string
	if err = tx.QueryRow("SELECT creator FROM evolution_candidates WHERE project=? AND candidate=?", project, candidate).Scan(&author); err != nil {
		return err
	}
	authorRoot, err := authorityRoot(tx, author)
	if err != nil {
		return err
	}
	verifierRoot, err := authorityRoot(tx, p.ID)
	if err != nil {
		return err
	}
	if authorRoot == verifierRoot || p.ID == h["release_principal"] {
		return Fail(403, "FORBIDDEN", "candidate author or release actor cannot freeze own holdout")
	}
	_, exists, err := evolutionHoldoutEntry(tx, project, candidate, "HOLDOUT_FROZEN")
	if err != nil {
		return err
	}
	if exists {
		return Fail(409, "STATE_CONFLICT", "private holdout already frozen")
	}
	_, inputsRaw, err := s.evolutionPrivateBytes(ctx, tx, project, inputsRef)
	if err != nil {
		return err
	}
	_, labelsRaw, err := s.evolutionPrivateBytes(ctx, tx, project, labelsRef)
	if err != nil {
		return err
	}
	if _, _, err = decodeEvolutionHoldout(inputsRaw, labelsRaw); err != nil {
		return Fail(422, "GATE_FAILED", "private holdout labels are not objective and distinct")
	}
	entry := Object{"revision": evolution.HoldoutRevision, "verifier_id": p.ID, "input_ref": inputsRef, "labels_ref": labelsRef,
		"inputs_hash": Digest(inputsRaw), "labels_hash": Digest(labelsRaw), "plan_hash": Hash(evolutionPlan(x)),
		"stable_hash": x["stable_artifact_ref"].(map[string]any)["content_hash"], "candidate_hash": x["candidate_artifact_ref"].(map[string]any)["content_hash"],
		"public_suite_hash": Digest(evolution.Bytes(evolution.Suite())), "policy_hash": Digest(evolution.Bytes(evolution.Policy())), "model_revision": "NONE"}
	if err = evolutionJournal(tx, project, candidate, "", "HOLDOUT_FROZEN", entry); err != nil {
		return err
	}
	return tx.Commit()
}

// EvaluateEvolutionHoldoutFixture runs before the ordinary regression Task.
// The private raw result is registered through the existing protected path.
func (s *Service) EvaluateEvolutionHoldoutFixture(ctx context.Context, token, project, candidate string) (Object, error) {
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()
	p, err := authenticate(tx, token)
	if err != nil {
		return nil, err
	}
	if !protectedAllowed(p, project) {
		return nil, Fail(403, "FORBIDDEN", "restricted independent C20 verifier required")
	}
	x, err := load(tx, project, "SystemCandidate", candidate)
	if err != nil {
		return nil, err
	}
	if x["status"] != "EVALUATING" {
		return nil, Fail(409, "STATE_CONFLICT", "private holdout evaluation phase changed")
	}
	if _, err = s.evolutionCurrent(tx, project, x); err != nil {
		return nil, err
	}
	frozen, present, err := evolutionHoldoutEntry(tx, project, candidate, "HOLDOUT_FROZEN")
	if err != nil || !present {
		return nil, Fail(422, "GATE_FAILED", "frozen private holdout unavailable")
	}
	if frozen["verifier_id"] != p.ID || frozen["plan_hash"] != Hash(evolutionPlan(x)) {
		return nil, Fail(403, "FORBIDDEN", "private holdout verifier or plan changed")
	}
	_, evaluated, err := evolutionHoldoutEntry(tx, project, candidate, "HOLDOUT_EVALUATED")
	if err != nil {
		return nil, err
	}
	if evaluated {
		return nil, Fail(409, "STATE_CONFLICT", "private holdout already evaluated")
	}
	inputsRef, labelsRef := frozen["input_ref"].(map[string]any), frozen["labels_ref"].(map[string]any)
	_, inputsRaw, err := s.evolutionPrivateBytes(ctx, tx, project, inputsRef)
	if err != nil {
		return nil, err
	}
	_, labelsRaw, err := s.evolutionPrivateBytes(ctx, tx, project, labelsRef)
	if err != nil {
		return nil, err
	}
	inputs, labels, err := decodeEvolutionHoldout(inputsRaw, labelsRaw)
	if err != nil || frozen["inputs_hash"] != Digest(inputsRaw) || frozen["labels_hash"] != Digest(labelsRaw) {
		return nil, Fail(422, "GATE_FAILED", "frozen private holdout changed")
	}
	_, stable, err := s.evolutionBytes(tx, project, x["stable_artifact_ref"].(map[string]any))
	if err != nil {
		return nil, err
	}
	_, trial, err := s.evolutionBytes(tx, project, x["candidate_artifact_ref"].(map[string]any))
	if err != nil {
		return nil, err
	}
	if err = tx.Rollback(); err != nil {
		return nil, err
	}
	proof, err := supervisor.EvaluateHoldout(ctx, stable, trial, inputs, Digest(labelsRaw), Hash(evolutionPlan(x)))
	if err != nil {
		return nil, err
	}
	verdict, err := supervisor.CheckHoldout(proof, inputs, labels, Hash(evolutionPlan(x)), Digest(stable), Digest(trial))
	if err != nil {
		return nil, err
	}
	store := s.Protected.(*protectedstore.CanaryStore)
	raw := Bytes(proof)
	blob, err := store.CreateCanary(ctx, project, "application/json", raw)
	if err != nil {
		return nil, err
	}
	metadata := Object{"run_id": nil, "kind": "REPORT", "evidence_kind": "OBSERVED", "measurement_mode": "FIXTURE",
		"input_refs": []any{inputsRef, labelsRef}, "source_refs": []any{x["stable_artifact_ref"], x["candidate_artifact_ref"]}}
	artifact, err := s.RegisterProtectedArtifact(ctx, token, project, blob.Ticket, metadata)
	if err != nil {
		return nil, err
	}
	safe := evolutionHoldoutSummary(verdict)
	tx, err = s.DB.BeginTx(ctx, nil)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()
	current, err := load(tx, project, "SystemCandidate", candidate)
	if err != nil || Hash(evolutionPlan(current)) != Hash(evolutionPlan(x)) || current["status"] != "EVALUATING" {
		return nil, Fail(422, "GATE_FAILED", "candidate changed during private evaluation")
	}
	_, evaluated, err = evolutionHoldoutEntry(tx, project, candidate, "HOLDOUT_EVALUATED")
	if err != nil || evaluated {
		return nil, Fail(409, "STATE_CONFLICT", "private evaluation already bound")
	}
	if err = evolutionJournal(tx, project, candidate, "", "HOLDOUT_EVALUATED", Object{"proof_ref": Ref(artifact, "Artifact"), "proof_hash": Digest(raw), "summary_hash": Hash(safe), "plan_hash": Hash(evolutionPlan(x)), "verifier_id": p.ID}); err != nil {
		return nil, err
	}
	if err = tx.Commit(); err != nil {
		return nil, err
	}
	return Object{"status": "PRIVATE_FIXTURE_RECORDED", "proof_sha256": Digest(raw), "summary": safe, "model_revision": "NONE"}, nil
}

func evolutionHoldoutSummary(v supervisor.HoldoutVerdict) Object {
	return Object{"revision": evolution.HoldoutRevision, "measurement_mode": "FIXTURE", "model_revision": "NONE", "total": v.Total,
		"baseline_correct": v.BaselineCorrect, "candidate_correct": v.CandidateCorrect, "outcomes_equal": v.OutcomesEqual, "gain": v.Gain}
}

// A nil summary means this legacy public development candidate has no C20
// private fixture. For a registered C20 candidate, every absent or altered
// private result blocks normal acceptance and START_CANARY.
func (s *Service) evolutionHoldoutVerdict(ctx context.Context, tx *sql.Tx, project string, x Object) (Object, string, error) {
	id := Str(x, "id")
	frozen, present, err := evolutionHoldoutEntry(tx, project, id, "HOLDOUT_FROZEN")
	if err != nil || !present {
		return nil, "", err
	}
	evaluated, present, err := evolutionHoldoutEntry(tx, project, id, "HOLDOUT_EVALUATED")
	if err != nil || !present {
		return nil, "", Fail(422, "GATE_FAILED", "private holdout result missing")
	}
	if frozen["revision"] != evolution.HoldoutRevision || frozen["model_revision"] != "NONE" || frozen["plan_hash"] != Hash(evolutionPlan(x)) || frozen["stable_hash"] != x["stable_artifact_ref"].(map[string]any)["content_hash"] || frozen["candidate_hash"] != x["candidate_artifact_ref"].(map[string]any)["content_hash"] || frozen["public_suite_hash"] != Digest(evolution.Bytes(evolution.Suite())) || frozen["policy_hash"] != Digest(evolution.Bytes(evolution.Policy())) || evaluated["plan_hash"] != frozen["plan_hash"] || evaluated["verifier_id"] != frozen["verifier_id"] {
		return nil, "", Fail(422, "GATE_FAILED", "private holdout version or candidate binding changed")
	}
	_, inputsRaw, err := s.evolutionPrivateBytes(ctx, tx, project, frozen["input_ref"].(map[string]any))
	if err != nil {
		return nil, "", err
	}
	_, labelsRaw, err := s.evolutionPrivateBytes(ctx, tx, project, frozen["labels_ref"].(map[string]any))
	if err != nil {
		return nil, "", err
	}
	_, proofRaw, err := s.evolutionPrivateBytes(ctx, tx, project, evaluated["proof_ref"].(map[string]any))
	if err != nil {
		return nil, "", err
	}
	if frozen["inputs_hash"] != Digest(inputsRaw) || frozen["labels_hash"] != Digest(labelsRaw) || evaluated["proof_hash"] != Digest(proofRaw) {
		return nil, "", Fail(422, "GATE_FAILED", "private holdout frozen bytes changed")
	}
	inputs, labels, err := decodeEvolutionHoldout(inputsRaw, labelsRaw)
	if err != nil {
		return nil, "", Fail(422, "GATE_FAILED", "private holdout objective labels invalid")
	}
	var proof supervisor.HoldoutProof
	if err = json.Unmarshal(proofRaw, &proof); err != nil {
		return nil, "", Fail(422, "GATE_FAILED", "private holdout proof invalid")
	}
	verdict, err := supervisor.CheckHoldout(proof, inputs, labels, Hash(evolutionPlan(x)), Str(x["stable_artifact_ref"].(map[string]any), "content_hash"), Str(x["candidate_artifact_ref"].(map[string]any), "content_hash"))
	if err != nil {
		return nil, "", Fail(422, "GATE_FAILED", fmt.Sprintf("private holdout raw process result invalid: %v", err))
	}
	summary := evolutionHoldoutSummary(verdict)
	if evaluated["summary_hash"] != Hash(summary) {
		return nil, "", Fail(422, "GATE_FAILED", "private holdout outcome changed")
	}
	return summary, Digest(proofRaw), nil
}
