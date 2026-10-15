//go:build windows

package ownedcorestop

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"researchos.local/research-os/internal/host"
	"researchos.local/research-os/internal/store"
	"researchos.local/research-os/ops/supervisor"
)

func TestOwnedCoreStopJournalExclusiveAndPrivate(t *testing.T) {
	base := t.TempDir()
	dataRoot := filepath.Join(base, "data")
	if err := os.Mkdir(dataRoot, 0700); err != nil {
		t.Fatal(err)
	}
	out := filepath.Join(base, "new-output")
	if err := createPrivateOutput(out, dataRoot); err != nil {
		t.Fatal(err)
	}
	hash, err := writeOwnedJournal(out, "BEGIN.json", struct {
		Schema string `json:"schema"`
	}{"test.v1"})
	if err != nil || !validSHA(hash) {
		t.Fatalf("private exclusive journal failed: %s %v", hash, err)
	}
	if _, err := writeOwnedJournal(out, "BEGIN.json", map[string]string{"schema": "replay"}); err == nil {
		t.Fatal("immutable journal was overwritten")
	}
	raw, err := readOwnedJournal(out, "BEGIN.json", 128)
	if err != nil || digest(raw) != hash {
		t.Fatalf("journal read/hash mismatch: %v", err)
	}
}

func TestOwnedCoreStopInspectJournalCrashBoundaries(t *testing.T) {
	base := t.TempDir()
	dataRoot := filepath.Join(base, "data")
	if err := os.Mkdir(dataRoot, 0700); err != nil {
		t.Fatal(err)
	}
	out := filepath.Join(base, "new-output")
	if err := createPrivateOutput(out, dataRoot); err != nil {
		t.Fatal(err)
	}
	subject := store.OwnedStopSubject{Run: OldRun, Epoch: 1, DispatchKey: OldDispatch, RequestKey: OldRequest, Project: "fixture"}
	sid := "fixture-sid"
	op := strings.Repeat("a", 32)
	plan := Plan{
		Schema: PlanSchema, OperationID: op, SourceBaseCommit: SourceBaseCommit,
		OutputDir: out, BackupPath: filepath.Join(out, "backup.sqlite"),
		InputSHA256: strings.Repeat("b", 64), BackupSHA256: strings.Repeat("c", 64),
		Input:       Input{Schema: InputSchema, OperationID: op, SourceRepository: base, DataRoot: dataRoot, CorePID: 1, Subject: subject},
		Native:      supervisor.OwnedCoreNativeIdentity{PID: 1, SID: sid, ParentSID: sid},
		Host:        host.OwnedCoreStopPublicIdentity{DataRoot: dataRoot, SID: sid, SchemaVersion: 24},
		Baseline:    store.OwnedStopCensus{SHA256: strings.Repeat("d", 64), QuickCheck: "ok"},
		Eligibility: "STOP_UNAVAILABLE",
	}
	planSHA, err := writeOwnedJournal(out, "plan.json", plan)
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(out, "plan.json")
	check := func(state string) {
		t.Helper()
		got, err := Inspect(path)
		if err != nil || got.State != state || got.PlanSHA256 != planSHA {
			t.Fatalf("inspect %s: %+v %v", state, got, err)
		}
	}
	check("UNKNOWN") // before BEGIN
	if _, err := writeOwnedJournal(out, "BEGIN.json", ownedBeginRecord{"researchos.owned-core-stop-begin.v1", op, planSHA}); err != nil {
		t.Fatal(err)
	}
	check("UNKNOWN") // after BEGIN, before termination intent
	if _, err := writeOwnedJournal(out, "TERMINATE_INTENT.json", ownedIntentRecord{"researchos.owned-core-stop-terminate-intent.v1", op, planSHA, plan.Native}); err != nil {
		t.Fatal(err)
	}
	check("UNKNOWN") // before/after native call without durable wait proof
	nativeExit := supervisor.OwnedCoreNativeExit{TerminateCalls: 1, ExitObserved: true, ExitCode: supervisor.OwnedCoreMaintenanceExitCode}
	if _, err := writeOwnedJournal(out, "NATIVE_EXIT.json", ownedExitRecord{"researchos.owned-core-stop-native-exit.v1", op, planSHA, nativeExit}); err != nil {
		t.Fatal(err)
	}
	check("STOP_OBSERVED_MAINTENANCE_BLOCKED") // after exit, before lease
	final := stopResult(plan, planSHA, "STOP_OBSERVED_MAINTENANCE_BLOCKED", "lease unavailable")
	final.Native = &nativeExit
	if _, err := writeOwnedJournal(out, "POSTFLIGHT.json", final); err != nil {
		t.Fatal(err)
	}
	check(final.State)
	check(final.State) // repeat inspection is identical and observation only
	if err := os.WriteFile(filepath.Join(out, "POSTFLIGHT.json"), []byte("{\"schema\":\"forged\"}"), 0600); err != nil {
		t.Fatal(err)
	}
	if _, err := Inspect(path); err == nil {
		t.Fatal("corrupt terminal receipt silently fell back to earlier journal")
	}
}
