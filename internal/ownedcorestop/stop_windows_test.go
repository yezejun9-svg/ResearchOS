//go:build windows

package ownedcorestop

import (
	"context"
	"database/sql"
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"researchos.local/research-os/internal/store"
	"researchos.local/research-os/ops/supervisor"
)

func TestOwnedCoreStopFrozenSubjectRejectsOtherWork(t *testing.T) {
	in := Input{Schema: InputSchema, OperationID: strings.Repeat("a", 32), SourceRepository: filepath.Join(t.TempDir(), "source"), DataRoot: filepath.Join(t.TempDir(), "data"), CorePID: 1,
		Subject: store.OwnedStopSubject{Run: OldRun, Epoch: 1, DispatchKey: OldDispatch, RequestKey: OldRequest, Project: "fixture"}}
	if err := validateInput(in); err != nil {
		t.Fatal(err)
	}
	for _, bad := range []store.OwnedStopSubject{
		{Run: "another", Epoch: 1, DispatchKey: OldDispatch, RequestKey: OldRequest, Project: "fixture"},
		{Run: OldRun, Epoch: 2, DispatchKey: OldDispatch, RequestKey: OldRequest, Project: "fixture"},
		{Run: OldRun, Epoch: 1, DispatchKey: "another", RequestKey: OldRequest, Project: "fixture"},
		{Run: OldRun, Epoch: 1, DispatchKey: OldDispatch, RequestKey: "another", Project: "fixture"},
	} {
		in.Subject = bad
		if err := validateInput(in); err == nil {
			t.Fatalf("other work accepted: %+v", bad)
		}
	}
}

func TestOwnedCoreStopPostflightRealLeaseBlocksLogicalDrift(t *testing.T) {
	fixture := os.Getenv("RESEARCHOS_OWNED_STOP_FIXTURE_EXE")
	if fixture == "" {
		t.Fatal("new owned fixture exe required")
	}
	base := t.TempDir()
	root := filepath.Join(base, "data")
	if err := os.Mkdir(root, 0700); err != nil {
		t.Fatal(err)
	}
	dbPath := filepath.Join(root, "researchos.sqlite")
	db, err := sql.Open("sqlite", dbPath)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = db.Exec(`PRAGMA journal_mode=WAL;CREATE TABLE stop_fixture_rows(id TEXT PRIMARY KEY,payload BLOB)`); err != nil {
		db.Close()
		t.Fatal(err)
	}
	if err = db.Close(); err != nil {
		t.Fatal(err)
	}
	markers := filepath.Join(base, "markers")
	if err = os.Mkdir(markers, 0700); err != nil {
		t.Fatal(err)
	}
	ready := filepath.Join(markers, "ready")
	cmd := exec.Command(fixture, "--root", root, "--ready", ready, "--attempt", filepath.Join(markers, "never-attempt"), "--attempted", filepath.Join(markers, "never-attempted"))
	if err = cmd.Start(); err != nil {
		t.Fatal(err)
	}
	defer func() { _ = cmd.Process.Kill(); _ = cmd.Wait() }()
	found := false
	for deadline := time.Now().Add(6 * time.Second); time.Now().Before(deadline); time.Sleep(20 * time.Millisecond) {
		if _, e := os.Stat(ready); e == nil {
			found = true
			break
		}
	}
	if !found {
		t.Fatal("fixture ready missing")
	}
	baseline, err := store.ReadOwnedStopCensus(context.Background(), dbPath)
	if err != nil || baseline.Rows != 1 {
		t.Fatalf("committed baseline: %+v %v", baseline, err)
	}
	id, err := supervisor.ObserveOwnedCoreReadOnly(uint32(cmd.Process.Pid))
	if err != nil {
		t.Fatal(err)
	}
	h, err := supervisor.OpenOwnedCoreRetained(id)
	if err != nil {
		t.Fatal(err)
	}
	defer h.Close()
	exit, err := h.TerminateOnceAndWait(5 * time.Second)
	if err != nil || !exit.ExitObserved || exit.TerminateCalls != 1 {
		t.Fatalf("native fixture exit: %+v %v", exit, err)
	}
	db, err = sql.Open("sqlite", dbPath)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = db.Exec(`INSERT INTO stop_fixture_rows VALUES('poststop-drift',x'ff')`); err != nil {
		db.Close()
		t.Fatal(err)
	}
	if err = db.Close(); err != nil {
		t.Fatal(err)
	}
	out := filepath.Join(base, "postflight")
	if err = createPrivateOutput(out, root); err != nil {
		t.Fatal(err)
	}
	plan := Plan{OperationID: strings.Repeat("c", 32), OutputDir: out, Input: Input{DataRoot: root}, Baseline: baseline}
	plan.Host.Database = dbPath
	result, err := finishAfterNativeExit(context.Background(), plan, strings.Repeat("d", 64), exit)
	if err != nil {
		t.Fatal(err)
	}
	if result.State != "STOP_OBSERVED_MAINTENANCE_BLOCKED" || result.Postflight == nil || result.Postflight.Rows != 2 || *result.Postflight == baseline {
		t.Fatalf("poststop logical drift escaped maintenance block: %+v", result)
	}
	if _, err := os.Stat(filepath.Join(out, "POSTFLIGHT.json")); err != nil {
		t.Fatalf("durable blocked receipt missing: %v", err)
	}
}

func TestOwnedCoreStopInvalidPreflightNeverCreatesOutput(t *testing.T) {
	base := t.TempDir()
	out := filepath.Join(base, "new-output")
	in := Input{Schema: InputSchema, OperationID: strings.Repeat("b", 32), SourceRepository: base, DataRoot: filepath.Join(base, "data"), CorePID: 1,
		Subject: store.OwnedStopSubject{Run: OldRun, Epoch: 1, DispatchKey: OldDispatch, RequestKey: "wrong", Project: "fixture"}}
	raw, err := json.Marshal(in)
	if err != nil {
		t.Fatal(err)
	}
	inputPath := filepath.Join(base, "input.json")
	if err := os.WriteFile(inputPath, raw, 0600); err != nil {
		t.Fatal(err)
	}
	if _, _, err := Preflight(context.Background(), inputPath, in.OperationID, out); err == nil {
		t.Fatal("wrong historical subject passed preflight")
	}
	if _, err := os.Stat(out); !os.IsNotExist(err) {
		t.Fatalf("invalid preflight created output: %v", err)
	}
}
