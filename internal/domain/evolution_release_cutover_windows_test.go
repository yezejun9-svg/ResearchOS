//go:build windows

package domain

import (
	"context"
	"os"
	"path/filepath"
	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/internal/store"
	"researchos.local/research-os/ops/supervisor"
	"testing"
	"time"
)

// This test qualifies snapshot mechanics using the existing calculator fixture.
// It does not admit, switch, or claim business improvement for actual control.
func TestReleaseCutoverEncryptedSnapshotMechanism(t *testing.T) {
	e := evoSetupMode(t, "gain", true)
	private := prepareC20PrivateOperation(t, e, "multiply")
	_, _, accepted := e.run("REGRESSION")
	f := e.o.f
	ctx := context.Background()
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	h, err := evolutionHost(tx, f.project)
	tx.Rollback()
	if err != nil {
		t.Fatal(err)
	}
	data := releaseFixtureData(h)
	lease, err := rt.AcquireDataRootLease(data)
	if err != nil {
		t.Fatal(err)
	}
	defer lease.Close()
	dbPath := filepath.Join(data, "researchos.sqlite")
	if _, err = f.db.Exec("VACUUM INTO ?", dbPath); err != nil {
		t.Fatal(err)
	}
	if err = f.db.Close(); err != nil {
		t.Fatal(err)
	}
	db, err := store.Open(dbPath)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	f.db = db
	f.s.DB = db
	state := supervisor.ReleaseState{Epoch: 1, Operation: "bootstrap", Phase: "STABLE", Active: releaseArtifactDigest(e.x["stable_artifact_ref"].(map[string]any)["content_hash"]), Data: data}
	request := Object{"action": "START_CANARY", "regression_acceptance_id": accepted["id"], "canary_acceptance_id": nil, "rollback_verified_receipt_id": nil, "observation_deadline": time.Now().Add(2 * time.Minute).UTC().Format(time.RFC3339Nano), "reason": "cutover snapshot mechanism only"}
	sealed, err := f.s.HandleReleaseFixture(ctx, "FIXTURE_SEAL", data, supervisor.ReleasePrivateMessage{Project: f.project, Candidate: Str(e.x, "id"), Request: Bytes(request), Snapshot: &state})
	if err != nil {
		t.Fatal(err)
	}
	a := *sealed.Admission
	f.token = e.release
	f.expect(200, "POST", f.path("/system-candidates/"+Str(e.x, "id")+"/actions"), ID(), testTag(e.x), request)
	state.Operation = a.Operation
	state.Epoch++
	state.Phase = "PREPARED"
	state.Admission = releasePlainDigest(a)
	state.AdmissionBundle = &a
	// A revoked actor cannot consume the prepared effect, even with old admission.
	actor := Str(accepted, "verifier_principal_id")
	if _, err = db.Exec("UPDATE auth_principals SET revoked=1 WHERE id=?", actor); err != nil {
		t.Fatal(err)
	}
	if _, err = f.s.HandleReleaseFixture(ctx, "FIXTURE_DISPATCH", data, supervisor.ReleasePrivateMessage{Snapshot: &state, Admission: &a}); err == nil {
		t.Fatal("revoked actor dispatched")
	}
	op, err := readReleaseOperation(db, f.project, a.Operation)
	if err != nil || op.Status != "PREPARED" {
		t.Fatalf("revoked attempt consumed effect: %+v %v", op, err)
	}
	if _, err = db.Exec("UPDATE auth_principals SET revoked=0 WHERE id=?", actor); err != nil {
		t.Fatal(err)
	}
	// This business write occurs after admission backup/seal and must survive.
	f.token = e.owner
	late := f.expect(201, "POST", "/v1/projects", ID(), "", projectBody())
	lateID := Str(late, "project_id")
	var lateBody string
	if err = db.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='ProjectProfile'", lateID).Scan(&lateBody); err != nil {
		t.Fatal(err)
	}
	if _, err = f.s.HandleReleaseFixture(ctx, "FIXTURE_DISPATCH", data, supervisor.ReleasePrivateMessage{Snapshot: &state, Admission: &a}); err != nil {
		t.Fatal(err)
	}
	if _, err = f.s.HandleReleaseFixture(ctx, "FIXTURE_DISPATCH", data, supervisor.ReleasePrivateMessage{Snapshot: &state, Admission: &a}); err == nil {
		t.Fatal("lost dispatch ACK replayed CAS")
	}
	state.Phase = "DRAIN_UNKNOWN"
	snap, err := f.s.HandleReleaseFixture(ctx, "FIXTURE_CUTOVER", data, supervisor.ReleasePrivateMessage{Snapshot: &state, Admission: &a})
	if err != nil {
		t.Fatal(err)
	}
	state.Cutover = snap.Cutover
	if state.Cutover == nil || state.Cutover.ManifestSHA256 == a.BackupReceiptSHA256 {
		t.Fatal("cutover reused pre-intent admission backup")
	}
	if _, err = f.s.HandleReleaseFixture(ctx, "FIXTURE_CUTOVER", data, supervisor.ReleasePrivateMessage{Snapshot: &state, Admission: &a}); err == nil {
		t.Fatal("snapshot unknown outcome resubmitted")
	}
	if _, err = os.Stat(filepath.Join(state.Cutover.Directory, "state.sqlite.enc")); err != nil {
		t.Fatal(err)
	}
	// Close the sole online writer; offline recovery must own that exact root.
	if err = db.Close(); err != nil {
		t.Fatal(err)
	}
	if err = lease.Close(); err != nil {
		t.Fatal(err)
	}
	if _, err = RestoreEvolutionCutover(ctx, state, lease, "../../spec/v2.0/contracts", private.root); err == nil {
		t.Fatal("closed lease restored authority")
	}
	offline, err := rt.AcquireDataRootLease(data)
	if err != nil {
		t.Fatal(err)
	}
	defer offline.Close()
	if extra, err := rt.AcquireDataRootLease(data); err == nil {
		extra.Close()
		t.Fatal("offline restore accepted a second writer")
	}
	before, err := os.ReadFile(dbPath)
	if err != nil {
		t.Fatal(err)
	}
	destination, err := RestoreEvolutionCutover(ctx, state, offline, "../../spec/v2.0/contracts", private.root)
	if err != nil {
		t.Fatal(err)
	}
	after, err := os.ReadFile(dbPath)
	if err != nil || Digest(after) != Digest(before) {
		t.Fatal("failed authority DB was overwritten")
	}
	restored, err := store.Open(filepath.Join(destination, "researchos.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	defer restored.Close()
	var got string
	if err = restored.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='ProjectProfile'", lateID).Scan(&got); err != nil || got != lateBody {
		t.Fatalf("post-seal business write missing: %v", err)
	}
	restoredOp, err := readReleaseOperation(restored, f.project, a.Operation)
	if err != nil || restoredOp.Status != "DISPATCHED" {
		t.Fatalf("restore lost nonreplay fence: %+v %v", restoredOp, err)
	}
	var active int
	if err = restored.QueryRow("SELECT count(*) FROM auth_credentials WHERE revoked=0").Scan(&active); err != nil || active != 0 {
		t.Fatalf("snapshot credentials revived: %d %v", active, err)
	}
	var copies int
	if err = restored.QueryRow("SELECT count(*) FROM uploaded_content WHERE storage_key GLOB 'ps1:*'").Scan(&copies); err != nil || copies != 0 {
		t.Fatalf("protected bytes copied to authority: %d %v", copies, err)
	}
	t.Logf("scope=SNAPSHOT_MECHANISM_EXISTING_CALCULATOR_PROOF; admission=%s cutover=%s root=%s destination=%s post-seal-project=%s body-hash=%s DISPATCHED preserved; all credentials revoked; private refs verified; failed DB preserved; no external action dispatched; actual-control business proof UNAVAILABLE", a.BackupReceiptSHA256, state.Cutover.ManifestSHA256, data, destination, lateID, Digest([]byte(lateBody)))
}
