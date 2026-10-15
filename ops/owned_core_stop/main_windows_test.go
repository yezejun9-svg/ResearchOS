//go:build windows

package main

import (
	"context"
	"database/sql"
	"os"
	"os/exec"
	"path/filepath"
	"testing"
	"time"

	_ "modernc.org/sqlite"
	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/internal/store"
	"researchos.local/research-os/ops/supervisor"
)

func waitFixtureFile(t *testing.T, path string) {
	t.Helper()
	for deadline := time.Now().Add(6 * time.Second); time.Now().Before(deadline); time.Sleep(20 * time.Millisecond) {
		if _, e := os.Stat(path); e == nil {
			return
		}
	}
	t.Fatalf("fixture marker absent: %s", path)
}

func TestOwnedCoreControlledCrashWALAndLease(t *testing.T) {
	fixture := os.Getenv("RESEARCHOS_OWNED_STOP_FIXTURE_EXE")
	if fixture == "" {
		t.Fatal("built new owned fixture exe required; no skip")
	}
	root := filepath.Join(t.TempDir(), "data")
	if err := os.Mkdir(root, 0700); err != nil {
		t.Fatal(err)
	}
	dbPath := filepath.Join(root, "researchos.sqlite")
	db, err := sql.Open("sqlite", dbPath)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = db.Exec(`PRAGMA journal_mode=WAL;PRAGMA synchronous=FULL;CREATE TABLE stop_fixture_rows(id TEXT PRIMARY KEY,payload BLOB)`); err != nil {
		db.Close()
		t.Fatal(err)
	}
	if err = db.Close(); err != nil {
		t.Fatal(err)
	}
	out := t.TempDir()
	ready := filepath.Join(out, "ready")
	attempt := filepath.Join(out, "attempt")
	attempted := filepath.Join(out, "attempted")
	cmd := exec.Command(fixture, "--root", root, "--ready", ready, "--attempt", attempt, "--attempted", attempted)
	if err = cmd.Start(); err != nil {
		t.Fatal(err)
	}
	defer cmd.Wait()
	waitFixtureFile(t, ready)
	baseline, backupHash, err := store.OnlineOwnedStopBackup(context.Background(), dbPath, filepath.Join(out, "backup.sqlite"))
	if err != nil || backupHash == "" || baseline.Rows != 1 {
		t.Fatalf("WAL online backup failed: %+v %q %v", baseline, backupHash, err)
	}
	identity, err := supervisor.ObserveOwnedCoreReadOnly(uint32(cmd.Process.Pid))
	if err != nil {
		t.Fatal(err)
	}
	h, err := supervisor.OpenOwnedCoreRetained(identity)
	if err != nil {
		t.Fatal(err)
	}
	defer h.Close()
	barrier, err := store.AcquireOwnedStopBarrier(context.Background(), dbPath)
	if err != nil {
		t.Fatal(err)
	}
	defer barrier.Close()
	current, err := barrier.Census(context.Background())
	if err != nil || current != baseline {
		t.Fatalf("baseline differs before signal: %+v %v", current, err)
	}
	if err = os.WriteFile(attempt, []byte("go"), 0600); err != nil {
		t.Fatal(err)
	}
	waitFixtureFile(t, attempted)
	// The fixture has a deferred transaction attempting a write. The reserved
	// writer lock prevents its durable PREPARED/row commit before the crash.
	exit, err := h.TerminateOnceAndWait(5 * time.Second)
	if err != nil || exit.TerminateCalls != 1 || !exit.ExitObserved || exit.ExitCode != supervisor.OwnedCoreMaintenanceExitCode {
		t.Fatalf("exact controlled crash unavailable: %+v %v", exit, err)
	}
	if err = barrier.Close(); err != nil {
		t.Fatal(err)
	}
	lease, err := rt.AcquireDataRootLease(root)
	if err != nil {
		t.Fatalf("native exit did not release real root lease: %v", err)
	}
	defer lease.Close()
	if !lease.Held() {
		t.Fatal("poststop real lease not held")
	}
	post, err := store.ReadOwnedStopCensus(context.Background(), dbPath)
	if err != nil || post != baseline {
		t.Fatalf("committed WAL lost or in-flight row escaped: %+v %v", post, err)
	}
	read, err := sql.Open("sqlite", dbPath)
	if err != nil {
		t.Fatal(err)
	}
	defer read.Close()
	var committed, inflight int
	if err = read.QueryRow(`SELECT count(*) FROM stop_fixture_rows WHERE id='committed'`).Scan(&committed); err != nil {
		t.Fatal(err)
	}
	if err = read.QueryRow(`SELECT count(*) FROM stop_fixture_rows WHERE id='inflight'`).Scan(&inflight); err != nil {
		t.Fatal(err)
	}
	if committed != 1 || inflight != 0 {
		t.Fatalf("wrong crash durability: committed=%d inflight=%d", committed, inflight)
	}
}

func TestOwnedCoreCLIRequiresExactArguments(t *testing.T) {
	if got := run([]string{"commit", "--plan", "missing"}); got != 2 {
		t.Fatalf("commit accepted missing reviewed SHA: %d", got)
	}
	if got := run([]string{"preflight", "--input", "missing", "--operation-id", "a"}); got != 2 {
		t.Fatalf("preflight accepted missing new out: %d", got)
	}
	if got := run([]string{"inspect"}); got != 2 {
		t.Fatalf("inspect accepted missing plan: %d", got)
	}
}
