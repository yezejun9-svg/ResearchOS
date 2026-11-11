//go:build windows

package domain

import (
	"bytes"
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"researchos.local/research-os/adapters/protectedstore"
	"researchos.local/research-os/evaluation/evolution"
	"researchos.local/research-os/ops/supervisor"
	"strings"
	"testing"
	"time"
)

type c20PrivateFixture struct {
	root, verifierToken string
	store               *protectedstore.CanaryStore
	inputs, labels      Object
	proof               Object
	verdict             supervisor.HoldoutVerdict
}

func prepareC20Private(t *testing.T, e *evolutionFixture) *c20PrivateFixture {
	return prepareC20PrivateOperation(t, e, "add")
}

func prepareC20PrivateOperation(t *testing.T, e *evolutionFixture, operation string) *c20PrivateFixture {
	t.Helper()
	f := e.o.f
	root := filepath.Join(t.TempDir(), "private-c20")
	if t.Name() == "TestW16C20" && os.Getenv("W16_PROTECTED_EVIDENCE_DIR") != "" {
		root = os.Getenv("W16_PROTECTED_EVIDENCE_DIR")
	}
	store, err := protectedstore.NewCanary(root)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { store.Close() })
	f.s.Protected = store
	verifier := Principal{ID: "c20-restricted-verifier", Roles: []string{"VERIFIER"}, Grants: []Grant{{ProjectID: f.project, Restricted: true}}}
	if err = f.s.ProvisionPrincipal(context.Background(), verifier); err != nil {
		t.Fatal(err)
	}
	token, err := f.s.IssueCredential(context.Background(), verifier.ID, 5*time.Minute)
	if err != nil {
		t.Fatal(err)
	}
	var nonce [16]byte
	if _, err = rand.Read(nonce[:]); err != nil {
		t.Fatal(err)
	}
	prefix := "private-" + hex.EncodeToString(nonce[:8])
	revision := evolution.HoldoutRevision
	if operation == "multiply" {
		revision = evolution.HoldoutReleaseRevision
	}
	inputs := evolution.HoldoutInputs{Revision: revision, Cases: []evolution.Case{
		{ID: prefix + "-a", Operation: operation, A: 31 + int(nonce[8]%31), B: -17 - int(nonce[9]%10)},
		{ID: prefix + "-b", Operation: operation, A: -52 - int(nonce[10]%25), B: 19 + int(nonce[11]%17)},
	}}
	labels := evolution.HoldoutLabels{Revision: revision}
	for _, c := range inputs.Cases {
		expected := c.A + c.B
		if operation == "multiply" {
			expected = c.A * c.B
		}
		labels.Labels = append(labels.Labels, evolution.HoldoutLabel{ID: c.ID, Expected: expected})
	}
	if err = evolution.ValidateHoldout(inputs, labels); err != nil {
		t.Fatal(err)
	}
	register := func(kind string, raw []byte) Object {
		blob, createErr := store.CreateCanary(context.Background(), f.project, "application/json", raw)
		if createErr != nil {
			t.Fatal(createErr)
		}
		metadata := Object{"run_id": nil, "kind": kind, "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE", "input_refs": Empty(), "source_refs": Empty()}
		a, registerErr := f.s.RegisterProtectedArtifact(context.Background(), token, f.project, blob.Ticket, metadata)
		if registerErr != nil {
			t.Fatal(registerErr)
		}
		return a
	}
	private := &c20PrivateFixture{root: root, store: store, verifierToken: token,
		inputs: register("DATASET", evolution.Bytes(inputs)), labels: register("DATASET", evolution.Bytes(labels))}
	if err = f.s.RegisterEvolutionHoldoutFixture(context.Background(), token, f.project, Str(e.x, "id"), Ref(private.inputs, "Artifact"), Ref(private.labels, "Artifact")); err != nil {
		t.Fatal(err)
	}
	evaluated, err := f.s.EvaluateEvolutionHoldoutFixture(context.Background(), token, f.project, Str(e.x, "id"))
	if err != nil {
		t.Fatal(err)
	}
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback()
	entry, present, err := evolutionHoldoutEntry(tx, f.project, Str(e.x, "id"), "HOLDOUT_EVALUATED")
	if err != nil || !present {
		t.Fatalf("private proof journal missing: %v", err)
	}
	private.proof, _, err = f.s.evolutionPrivateBytes(context.Background(), tx, f.project, entry["proof_ref"].(map[string]any))
	if err != nil {
		t.Fatal(err)
	}
	_, proofRaw, err := f.s.evolutionPrivateBytes(context.Background(), tx, f.project, entry["proof_ref"].(map[string]any))
	if err != nil {
		t.Fatal(err)
	}
	var proof supervisor.HoldoutProof
	if err = json.Unmarshal(proofRaw, &proof); err != nil {
		t.Fatal(err)
	}
	private.verdict, err = supervisor.CheckHoldout(proof, inputs, labels, Hash(evolutionPlan(e.x)), Digest(e.stable), Digest(e.candidate))
	if err != nil {
		t.Fatal(err)
	}
	if Hash(evaluated["summary"]) != Hash(evolutionHoldoutSummary(private.verdict)) {
		t.Fatal("trusted private summary differs from independently recomputed proof")
	}
	f.token = e.owner
	return private
}

func (p *c20PrivateFixture) resultPath() string {
	return filepath.Join(p.root, strings.TrimPrefix(Str(p.proof, "storage_key"), "ps1:")+".bin")
}

// Reopen through the protected provider after the evaluator has finished. The
// ordinary receipt records only the locator and hashes; private bytes stay in
// this dedicated store for independent fixture review.
func (p *c20PrivateFixture) verifyReopened(t *testing.T, e *evolutionFixture) {
	t.Helper()
	if err := p.store.Close(); err != nil {
		t.Fatal(err)
	}
	reopened, err := protectedstore.OpenCanary(p.root)
	if err != nil {
		t.Fatal(err)
	}
	defer reopened.Close()
	read := func(a Object) []byte {
		size, sizeErr := Num(a, "byte_size")
		if sizeErr != nil {
			t.Fatal(sizeErr)
		}
		b := protectedstore.Blob{Ticket: Str(a, "storage_key"), Project: e.o.f.project,
			Hash: Str(a, "content_hash"), Size: size, MediaType: Str(a, "media_type"), MeasurementMode: "FIXTURE"}
		raw, readErr := reopened.Read(context.Background(), b)
		if readErr != nil || Digest(raw) != b.Hash {
			t.Fatalf("reopened protected proof failed integrity: %v", readErr)
		}
		return raw
	}
	inputsRaw, labelsRaw, proofRaw := read(p.inputs), read(p.labels), read(p.proof)
	inputs, labels, err := decodeEvolutionHoldout(inputsRaw, labelsRaw)
	if err != nil {
		t.Fatal(err)
	}
	var proof supervisor.HoldoutProof
	if err = json.Unmarshal(proofRaw, &proof); err != nil {
		t.Fatal(err)
	}
	verdict, err := supervisor.CheckHoldout(proof, inputs, labels, Hash(evolutionPlan(e.x)), Digest(e.stable), Digest(e.candidate))
	if err != nil || Hash(evolutionHoldoutSummary(verdict)) != Hash(evolutionHoldoutSummary(p.verdict)) {
		t.Fatalf("reopened dual-rubric proof changed: %v", err)
	}
	e.save("C20-protected-locator", Object{"protected_store": p.root, "measurement_mode": "FIXTURE", "reopened_and_recomputed": true,
		"input_sha256": Digest(inputsRaw), "label_sha256": Digest(labelsRaw), "dual_rubric_raw_proof_sha256": Digest(proofRaw),
		"stable_build_sha256": Digest(e.stable), "candidate_build_sha256": Digest(e.candidate), "model_revision": "NONE"})
}

func TestW16C20PrivateProofMissing(t *testing.T) {
	e := evoSetup(t, "rubric_only")
	p := prepareC20Private(t, e)
	_, _, receipt := e.run("REGRESSION")
	if err := os.Remove(p.resultPath()); err != nil {
		t.Fatal(err)
	}
	denied := e.action("START_CANARY", receipt["id"], 422)
	evoAssert(t, "C20-PRIVATE-MISSING", true, denied != nil && e.x["status"] == "EVALUATING")
}

func TestW16C20PrivateProofTampered(t *testing.T) {
	e := evoSetup(t, "rubric_only")
	p := prepareC20Private(t, e)
	_, _, receipt := e.run("REGRESSION")
	if err := os.WriteFile(p.resultPath(), []byte(`{"forged":"better outcome"}`), 0600); err != nil {
		t.Fatal(err)
	}
	denied := e.action("START_CANARY", receipt["id"], 422)
	evoAssert(t, "C20-PRIVATE-TAMPER", true, denied != nil && e.x["status"] == "EVALUATING")
}

func TestW16C20PrivateVerifierRevoked(t *testing.T) {
	e := evoSetup(t, "rubric_only")
	prepareC20Private(t, e)
	_, _, receipt := e.run("REGRESSION")
	if err := e.o.f.s.RevokePrincipal(context.Background(), "c20-restricted-verifier"); err != nil {
		t.Fatal(err)
	}
	denied := e.action("START_CANARY", receipt["id"], 403)
	evoAssert(t, "C20-PRIVATE-REVOKED", true, denied != nil && e.x["status"] == "EVALUATING")
}

func TestW16C20PrivateVerifierGrantRemoved(t *testing.T) {
	e := evoSetup(t, "rubric_only")
	prepareC20Private(t, e)
	_, _, receipt := e.run("REGRESSION")
	if _, err := e.o.f.db.Exec("DELETE FROM auth_grants WHERE principal=? AND project=?", "c20-restricted-verifier", e.o.f.project); err != nil {
		t.Fatal(err)
	}
	denied := e.action("START_CANARY", receipt["id"], 403)
	evoAssert(t, "C20-PRIVATE-GRANT-REMOVED", true, denied != nil && e.x["status"] == "EVALUATING")
}

func TestW16C20PrivateRemoteVerifier(t *testing.T) {
	e := evoSetup(t, "rubric_only")
	prepareC20Private(t, e)
	_, _, receipt := e.run("REGRESSION")
	// A paired device's effective grants are always non-restricted. Even if its
	// stored principal row retained a VERIFIER role/restricted grant, it cannot
	// act as the frozen private verifier when a proof is consumed.
	device := Object{"id": "c20-restricted-verifier", "role": "VERIFIER", "status": "ACTIVE"}
	if _, err := e.o.f.db.Exec("INSERT INTO remote_devices(id,owner,body) VALUES(?,?,?)", device["id"], e.o.f.owner, string(Bytes(device))); err != nil {
		t.Fatal(err)
	}
	denied := e.action("START_CANARY", receipt["id"], 403)
	evoAssert(t, "C20-PRIVATE-REMOTE-DENIED", true, denied != nil && e.x["status"] == "EVALUATING")
}

func c20PrivateConclude(t *testing.T, e *evolutionFixture, p *c20PrivateFixture, record Object) {
	t.Helper()
	if p.verdict.Total != 2 || !p.verdict.OutcomesEqual || p.verdict.Gain || p.verdict.BaselineCorrect != p.verdict.CandidateCorrect {
		t.Fatal("private objective outcomes do not demonstrate zero gain")
	}
	for _, row := range p.verdict.Rows {
		if row.CandidateScore <= row.BaselineScore || row.CandidateRubric == row.BaselineRubric || row.InputHash == "" {
			t.Fatal("dual-rubric raw row or per-question input version missing")
		}
	}
	if Hash(record["holdout_summary"]) != Hash(evolutionHoldoutSummary(p.verdict)) || record["holdout_proof_hash"] != p.proof["content_hash"] {
		t.Fatal("normal regression result did not bind verified private outcome")
	}
	public := Bytes(record["observation"])
	for _, private := range []string{Str(p.inputs, "storage_key"), Str(p.labels, "storage_key"), Str(p.proof, "storage_key")} {
		if bytes.Contains(public, []byte(private)) {
			t.Fatal("private protected ref entered public observation")
		}
	}
	// This benefit table comes from the private raw AppContainer receipts. It
	// publishes only aggregate counts; per-question inputs/labels stay private.
	table := Object{"measurement_mode": "FIXTURE", "model_revision": "NONE", "old_rubric": p.verdict.Rows[0].BaselineRubric,
		"new_rubric": p.verdict.Rows[0].CandidateRubric, "old_score": p.verdict.Rows[0].BaselineScore,
		"new_score": p.verdict.Rows[0].CandidateScore, "baseline_correct": p.verdict.BaselineCorrect,
		"candidate_correct": p.verdict.CandidateCorrect, "frozen_case_count": p.verdict.Total,
		"outcome_gain": p.verdict.Gain, "real_world_gain": "NOT_ESTABLISHED", "project_closed": false,
		"private_proof_sha256": p.proof["content_hash"], "experiment_outcome": e.experiment["outcome"]}
	e.save("C20-private-benefit", table)
	fmt.Println("C20_PRIVATE_BENEFIT " + string(Bytes(table)))
}
