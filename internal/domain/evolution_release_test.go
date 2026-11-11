//go:build windows

package domain

import (
	"context"
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"researchos.local/research-os/adapters/protectedstore"
	"researchos.local/research-os/ops/supervisor"
	"strings"
	"testing"
	"time"
)

func TestR2EvolutionReleaseHTTPIntentNativeReceiptProjection(t *testing.T) {
	e := evoSetupMode(t, "gain", true)
	private := prepareC20PrivateOperation(t, e, "multiply")
	_, record, acceptance := e.run("REGRESSION")
	if record["improved"] != true || private.verdict.Gain != true {
		t.Fatal("private same-sample objective benefit absent")
	}
	f := e.o.f
	ctx := context.Background()
	if err := f.s.BootstrapEvolutionReleaseFixture(ctx, f.project); err != nil {
		t.Fatal(err)
	}
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	h, err := evolutionHost(tx, f.project)
	_ = tx.Rollback()
	if err != nil {
		t.Fatal(err)
	}
	driver := releaseFixtureDriver()
	t.Cleanup(func() {
		j, err := supervisor.OpenReleaseJournal(releaseStateRoot(h))
		if err != nil {
			return
		}
		defer j.Close()
		state := j.State()
		if state.PID != 0 {
			_ = driver.Stop(supervisor.ProcessIdentity{PID: state.PID, CreatedNS: state.CreatedNS, ImageSHA256: state.ImageSHA256})
		}
	})
	request := Object{"action": "START_CANARY", "regression_acceptance_id": acceptance["id"], "canary_acceptance_id": nil, "rollback_verified_receipt_id": nil, "observation_deadline": time.Now().Add(time.Minute).UTC().Format(time.RFC3339Nano), "reason": "R2 exact native fixture admission"}
	sealed, err := f.s.SealEvolutionReleaseFixture(ctx, f.project, Str(e.x, "id"), request)
	if err != nil {
		t.Fatal(err)
	}
	againSealed, err := f.s.SealEvolutionReleaseFixture(ctx, f.project, Str(e.x, "id"), request)
	if err != nil || releasePlainDigest(againSealed) != releasePlainDigest(sealed) {
		t.Fatalf("same fixture admission must be idempotent: %+v %v", againSealed, err)
	}
	f.token = e.release
	x := f.expect(200, "POST", f.path("/system-candidates/"+Str(e.x, "id")+"/actions"), ID(), testTag(e.x), request)
	if x["status"] != "EVALUATING" {
		t.Fatalf("HTTP marked canary before actual process switch: %v", x["status"])
	}
	op, err := readReleaseOperation(f.db, f.project, sealed.Operation)
	if err != nil || op.Status != "PREPARED" || op.Admission != supervisor.ReleaseDigest(sealed) {
		t.Fatalf("HTTP intent not durable: %+v %v", op, err)
	}
	expired := sealed
	expired.ExpiresUTC = time.Now().Add(-time.Second).UTC()
	if currentErr := f.s.releaseAdmissionCurrent(ctx, expired); currentErr == nil || !strings.Contains(currentErr.Error(), "release admission expired before effect") {
		t.Fatalf("expired current admission not rejected: %v", currentErr)
	}
	if unchanged, readErr := readReleaseOperation(f.db, f.project, sealed.Operation); readErr != nil || unchanged.Status != "PREPARED" {
		t.Fatalf("expired check changed operation: %+v %v", unchanged, readErr)
	}
	if j, openErr := supervisor.OpenReleaseJournal(releaseStateRoot(h)); openErr != nil {
		t.Fatal(openErr)
	} else {
		phase := j.State().Phase
		_ = j.Close()
		if phase != "STABLE" {
			t.Fatalf("expired check changed stable process: %s", phase)
		}
	}
	goexe := os.Getenv("RESEARCHOS_GO")
	launcher := filepath.Join(t.TempDir(), "release_host.exe")
	build := exec.Command(goexe, "build", "-o", launcher, "../../ops/supervisor/release_host")
	if out, buildErr := build.CombinedOutput(); buildErr != nil {
		t.Fatalf("build separate release host: %v %s", buildErr, out)
	}
	var seq int
	var name, dbPath string
	if err = f.db.QueryRow("PRAGMA database_list").Scan(&seq, &name, &dbPath); err != nil {
		t.Fatal(err)
	}
	runHost := func() ([]byte, error) {
		cmd := exec.Command(launcher, "--db", dbPath, "--contracts", "../../spec/v2.0/contracts", "--migration", "../../migrations/sqlite/0002_domain.sql", "--private", private.root, "--project", f.project, "--operation", sealed.Operation)
		return cmd.CombinedOutput()
	}
	manifestPath := filepath.Join(releaseBackupPath(h, sealed.Operation), "manifest.json")
	manifest, err := os.ReadFile(manifestPath)
	if err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(manifestPath, []byte(`{"format":"tampered"}`), 0600); err != nil {
		t.Fatal(err)
	}
	if out, failed := runHost(); failed == nil || !strings.Contains(string(out), "BACKUP_MANIFEST_INVALID") {
		t.Fatalf("altered authority backup did not fail closed on manifest: %v %s", failed, out)
	}
	before, err := readReleaseOperation(f.db, f.project, sealed.Operation)
	if err != nil || before.Status != "PREPARED" {
		t.Fatalf("failed backup dispatched: %+v %v", before, err)
	}
	if err = os.WriteFile(manifestPath, manifest, 0600); err != nil {
		t.Fatal(err)
	}
	if err = private.store.Close(); err != nil {
		t.Fatal(err)
	}
	if err = releaseFixtureVerifier(f.s, h)(sealed); err == nil {
		t.Fatal("unavailable external private fixture store admitted")
	}
	reopened, err := protectedstore.OpenCanary(private.root)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = reopened.Close() })
	f.s.Protected = reopened
	tx, err = f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	accepted, err := load(tx, f.project, "AcceptanceReceipt", Str(acceptance, "id"))
	if err != nil {
		_ = tx.Rollback()
		t.Fatal(err)
	}
	frozen, present, err := evolutionHoldoutEntry(tx, f.project, Str(e.x, "id"), "HOLDOUT_FROZEN")
	_ = tx.Rollback()
	if err != nil || !present {
		t.Fatalf("private verifier identity missing: %v", err)
	}
	actors := []string{Str(accepted, "verifier_principal_id"), Str(frozen, "verifier_id"), Str(h, "release_principal")}
	if actors[0] == actors[1] || actors[0] == actors[2] || actors[1] == actors[2] {
		t.Fatalf("revoke negatives require distinct principals: %v", actors)
	}
	for _, actor := range actors {
		if _, err = f.db.Exec("UPDATE auth_principals SET revoked=1 WHERE id=?", actor); err != nil {
			t.Fatal(err)
		}
		if out, failed := runHost(); failed == nil {
			t.Fatalf("revoked actor %s dispatched: %s", actor, out)
		}
		if _, err = f.db.Exec("UPDATE auth_principals SET revoked=0 WHERE id=?", actor); err != nil {
			t.Fatal(err)
		}
		still, readErr := readReleaseOperation(f.db, f.project, sealed.Operation)
		if readErr != nil || still.Status != "PREPARED" {
			t.Fatalf("revoked actor changed dispatch: %+v %v", still, readErr)
		}
	}
	out, err := runHost()
	if err != nil {
		t.Fatalf("separate release host: %v %s", err, out)
	}
	var result Object
	if err = json.Unmarshal(out, &result); err != nil {
		t.Fatalf("release host receipt: %v %s", err, out)
	}
	if result["status"] != "PROJECTED" || result["candidate_status"] != "CANARY" {
		t.Fatalf("native receipt not projected: %+v", result)
	}
	j, err := supervisor.OpenReleaseJournal(releaseStateRoot(h))
	if err != nil {
		t.Fatal(err)
	}
	state := j.State()
	receipt, hash, err := supervisor.ReadFixtureReceipt(releaseStateRoot(h), j, driver, sealed.Operation)
	_ = j.Close()
	if err != nil || state.Phase != "CANARY" || state.Active != sealed.CandidateSHA256 || receipt.PID == 0 || hash != result["receipt_digest"] {
		t.Fatalf("raw process receipt invalid: %+v %v", receipt, err)
	}
	projected, err := readReleaseOperation(f.db, f.project, sealed.Operation)
	if err != nil || projected.Status != "PROJECTED" || projected.Revision < 1 || projected.Receipt.String != hash {
		t.Fatalf("domain projection changed: %+v %v", projected, err)
	}
	again, err := f.s.RunEvolutionReleaseFixtureOnce(ctx, f.project, sealed.Operation)
	if err != nil || again["receipt_digest"] != hash {
		t.Fatalf("lost ACK caused redispatch: %+v %v", again, err)
	}
	if _, err = os.Stat(filepath.Join(releaseStateRoot(h), "receipts", sealed.Operation+".json")); err != nil {
		t.Fatal(err)
	}
}

func TestR2PreparedCandidateFrozenBeforeDispatch(t *testing.T) {
	e := evoSetupMode(t, "gain", true)
	prepareC20PrivateOperation(t, e, "multiply")
	_, record, acceptance := e.run("REGRESSION")
	if record["improved"] != true {
		t.Fatal("R2 fixture requires accepted objective benefit")
	}
	f := e.o.f
	ctx := context.Background()
	if err := f.s.BootstrapEvolutionReleaseFixture(ctx, f.project); err != nil {
		t.Fatal(err)
	}
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	h, err := evolutionHost(tx, f.project)
	_ = tx.Rollback()
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() {
		j, openErr := supervisor.OpenReleaseJournal(releaseStateRoot(h))
		if openErr != nil {
			return
		}
		defer j.Close()
		state := j.State()
		if state.PID != 0 {
			_ = releaseFixtureDriver().Stop(supervisor.ProcessIdentity{PID: state.PID, CreatedNS: state.CreatedNS, ImageSHA256: state.ImageSHA256})
		}
	})
	request := Object{"action": "START_CANARY", "regression_acceptance_id": acceptance["id"], "canary_acceptance_id": nil, "rollback_verified_receipt_id": nil, "observation_deadline": time.Now().Add(time.Minute).UTC().Format(time.RFC3339Nano), "reason": "R2 freeze race"}
	sealed, err := f.s.SealEvolutionReleaseFixture(ctx, f.project, Str(e.x, "id"), request)
	if err != nil {
		t.Fatal(err)
	}
	f.token = e.release
	x := f.expect(200, "POST", f.path("/system-candidates/"+Str(e.x, "id")+"/actions"), ID(), testTag(e.x), request)
	if x["status"] != "EVALUATING" {
		t.Fatal("HTTP intent should only prepare")
	}
	frozen := f.expect(200, "POST", f.path("/system-candidates/"+Str(e.x, "id")+"/actions"), ID(), testTag(x), Object{"action": "FREEZE", "regression_acceptance_id": nil, "canary_acceptance_id": nil, "rollback_verified_receipt_id": nil, "observation_deadline": nil, "reason": "freeze after PREPARED before effect"})
	if frozen["status"] != "FROZEN" {
		t.Fatal("candidate freeze failed")
	}
	if err = releaseFixtureVerifier(f.s, h)(sealed); err == nil {
		t.Fatal("frozen candidate retained supervisor admission")
	}
	if _, err = f.s.RunEvolutionReleaseFixtureOnce(ctx, f.project, sealed.Operation); err == nil {
		t.Fatal("frozen candidate dispatched")
	}
	o, err := readReleaseOperation(f.db, f.project, sealed.Operation)
	if err != nil || o.Status != "PREPARED" {
		t.Fatalf("frozen candidate changed release operation: %+v %v", o, err)
	}
	j, err := supervisor.OpenReleaseJournal(releaseStateRoot(h))
	if err != nil {
		t.Fatal(err)
	}
	phase := j.State().Phase
	_ = j.Close()
	if phase != "STABLE" {
		t.Fatalf("frozen candidate changed native process: %s", phase)
	}
}
