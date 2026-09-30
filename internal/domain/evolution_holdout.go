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

// The frozen verifier identity is rechecked at every proof binding and use.
// A historical verifier ID cannot outlive its current restricted grant or
// acquire authority through the candidate author/release actor's identity.
func (s *Service) evolutionHoldoutVerifierCurrent(tx *sql.Tx, project string, x Object, verifierID string) error {
	var rolesRaw string
	if err := tx.QueryRow("SELECT roles FROM auth_principals WHERE id=? AND revoked=0", verifierID).Scan(&rolesRaw); err != nil {
		return Fail(403, "FORBIDDEN", "private holdout verifier no longer active")
	}
	p := Principal{ID: verifierID}
	if err := json.Unmarshal([]byte(rolesRaw), &p.Roles); err != nil {
		return err
	}
	rows, err := tx.Query("SELECT project,task,run,restricted FROM auth_grants WHERE principal=?", verifierID)
	if err != nil {
		return err
	}
	for rows.Next() {
		var g Grant
		if err = rows.Scan(&g.ProjectID, &g.TaskID, &g.RunID, &g.Restricted); err != nil {
			rows.Close()
			return err
		}
		p.Grants = append(p.Grants, g)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return err
	}
	if err = constrainRemotePrincipal(tx, &p); err != nil {
		return err
	}
	if !protectedAllowed(p, project) {
		return Fail(403, "FORBIDDEN", "restricted private holdout verifier grant required")
	}
	var author string
	if err = tx.QueryRow("SELECT creator FROM evolution_candidates WHERE project=? AND candidate=?", project, x["id"]).Scan(&author); err != nil {
		return err
	}
	h, err := s.evolutionCurrent(tx, project, x)
	if err != nil {
		return err
	}
	verifierRoot, err := authorityRoot(tx, verifierID)
	if err != nil {
		return err
	}
	authorRoot, err := authorityRoot(tx, author)
	if err != nil {
		return err
	}
	releaseRoot, err := authorityRoot(tx, Str(h, "release_principal"))
	if err != nil {
		return err
	}
	if verifierRoot == authorRoot || verifierRoot == releaseRoot {
		return Fail(403, "FORBIDDEN", "private holdout verifier is not independent")
	}
	return nil
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
	if err = s.evolutionHoldoutVerifierCurrent(tx, project, x, p.ID); err != nil {
		return err
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
	inputs, _, err := decodeEvolutionHoldout(inputsRaw, labelsRaw)
	if err != nil {
		return Fail(422, "GATE_FAILED", "private holdout labels are not objective and distinct")
	}
	if inputs.Revision == evolution.HoldoutReleaseRevision {
		h, hostErr := s.evolutionCurrent(tx, project, x)
		if hostErr != nil {
			return hostErr
		}
		if h["release_mechanism"] != releaseFixtureMechanism || h["os_service_qualified"] != false {
			return Fail(422, "GATE_FAILED", "R2 private revision requires explicit native fixture host")
		}
	}
	entry := Object{"revision": inputs.Revision, "verifier_id": p.ID, "input_ref": inputsRef, "labels_ref": labelsRef,
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
	if err = s.evolutionHoldoutVerifierCurrent(tx, project, x, p.ID); err != nil {
		return nil, err
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
	if err != nil || frozen["revision"] != inputs.Revision || frozen["inputs_hash"] != Digest(inputsRaw) || frozen["labels_hash"] != Digest(labelsRaw) {
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
	if err = s.evolutionHoldoutVerifierCurrent(tx, project, current, p.ID); err != nil {
		return nil, err
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
	return Object{"revision": v.Revision, "measurement_mode": "FIXTURE", "model_revision": "NONE", "total": v.Total,
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
	if !evolution.ValidHoldoutRevision(Str(frozen, "revision")) || frozen["model_revision"] != "NONE" || frozen["plan_hash"] != Hash(evolutionPlan(x)) || frozen["stable_hash"] != x["stable_artifact_ref"].(map[string]any)["content_hash"] || frozen["candidate_hash"] != x["candidate_artifact_ref"].(map[string]any)["content_hash"] || frozen["public_suite_hash"] != Digest(evolution.Bytes(evolution.Suite())) || frozen["policy_hash"] != Digest(evolution.Bytes(evolution.Policy())) || evaluated["plan_hash"] != frozen["plan_hash"] || evaluated["verifier_id"] != frozen["verifier_id"] {
		return nil, "", Fail(422, "GATE_FAILED", "private holdout version or candidate binding changed")
	}
	if frozen["revision"] == evolution.HoldoutReleaseRevision {
		h, hostErr := s.evolutionCurrent(tx, project, x)
		if hostErr != nil {
			return nil, "", hostErr
		}
		if h["release_mechanism"] != releaseFixtureMechanism || h["os_service_qualified"] != false {
			return nil, "", Fail(422, "GATE_FAILED", "R2 private revision host changed")
		}
	}
	if err = s.evolutionHoldoutVerifierCurrent(tx, project, x, Str(frozen, "verifier_id")); err != nil {
		return nil, "", err
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
	if inputs.Revision != frozen["revision"] {
		return nil, "", Fail(422, "GATE_FAILED", "private holdout revision differs from frozen binding")
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
