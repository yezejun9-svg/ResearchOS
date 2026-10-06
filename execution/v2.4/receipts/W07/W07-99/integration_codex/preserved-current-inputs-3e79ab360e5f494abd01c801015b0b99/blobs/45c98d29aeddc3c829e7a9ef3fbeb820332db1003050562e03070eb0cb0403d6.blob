//go:build windows

package supervisor

import (
	"context"
	"errors"
	"os"
	"path/filepath"
	"testing"
)

// This deterministic driver isolates the exact state/receipt failure: the
// started identity remains alive while its required readiness proof fails.
type readinessFenceDriver struct {
	current            ProcessIdentity
	starts, readyCalls int
	reject             bool
}

func (d *readinessFenceDriver) Start(image, token, data string) (ProcessIdentity, error) {
	_, hash, e := exactImage(image)
	if e != nil {
		return ProcessIdentity{}, e
	}
	d.starts++
	d.current = ProcessIdentity{PID: uint32(100 + d.starts), CreatedNS: int64(1000 + d.starts), ImageSHA256: hash}
	return d.current, nil
}
func (d *readinessFenceDriver) Alive(p ProcessIdentity) (bool, error) {
	return p == d.current && p.PID != 0, nil
}
func (d *readinessFenceDriver) Stop(p ProcessIdentity) error {
	if p != d.current {
		return errors.New("identity changed")
	}
	d.current = ProcessIdentity{}
	return nil
}
func (d *readinessFenceDriver) Drain(context.Context, ProcessIdentity, string) (string, error) {
	return releaseHash("drained"), nil
}
func (d *readinessFenceDriver) Ready(context.Context, ProcessIdentity, string) error {
	d.readyCalls++
	if d.reject {
		return errors.New("PRIVATE_READY_UNAVAILABLE")
	}
	return nil
}
func (d *readinessFenceDriver) Compatible(context.Context, ReleaseState) error { return nil }

func TestReleaseReadyFailureCannotProduceReceiptOrReplay(t *testing.T) {
	root := t.TempDir()
	stablePath := filepath.Join(root, "stable.exe")
	candidatePath := filepath.Join(root, "candidate.exe")
	if e := os.WriteFile(stablePath, []byte("state-machine-stable"), 0600); e != nil {
		t.Fatal(e)
	}
	if e := os.WriteFile(candidatePath, []byte("state-machine-candidate"), 0600); e != nil {
		t.Fatal(e)
	}
	_, stable, _ := exactImage(stablePath)
	_, candidate, _ := exactImage(candidatePath)
	j, e := OpenReleaseJournal(filepath.Join(root, "journal"))
	if e != nil {
		t.Fatal(e)
	}
	defer j.Close()
	initial := ReleaseState{Epoch: 1, Phase: "STABLE", Operation: "bootstrap", Active: stable, ActivePath: stablePath, LastGood: stable, LastGoodPath: stablePath, Data: root, PID: 11, CreatedNS: 22, ImageSHA256: stable}
	if e = j.Append(initial); e != nil {
		t.Fatal(e)
	}
	d := &readinessFenceDriver{current: processIn(initial), reject: true}
	engine, e := NewReleaseEngine(j, d, d, func(ReleaseAdmission) error { return nil })
	if e != nil {
		t.Fatal(e)
	}
	a := fixtureAdmission(initial, candidate)
	if _, e = engine.PrepareFixture(a, candidatePath); e != nil {
		t.Fatal(e)
	}
	if _, e = engine.SwitchFixture(context.Background(), a.Operation); e == nil {
		t.Fatal("missing private READY admitted")
	}
	state := j.State()
	if state.Phase != "RECOVERING" || processIn(state) != d.current || state.PID == 0 || d.starts != 1 {
		t.Fatalf("unready started identity not fenced: %+v starts=%d", state, d.starts)
	}
	if alive, _ := d.Alive(processIn(state)); !alive {
		t.Fatal("counterexample process must remain alive")
	}
	if _, _, e = WriteFixtureReceipt(j.root, j, d); e == nil {
		t.Fatal("unready alive process produced projection receipt")
	}
	if _, e = engine.SwitchFixture(context.Background(), a.Operation); e == nil {
		t.Fatal("uncertain start replayed")
	}
	if _, e = engine.Reconcile(); e == nil || d.starts != 1 {
		t.Fatal("reconcile retried start")
	}
	// Historical CANARY records created before this fix also require a fresh
	// readiness proof at the common receipt boundary, including existing bytes.
	state.Phase = "CANARY"
	if e = j.Append(state); e != nil {
		t.Fatal(e)
	}
	calls := d.readyCalls
	if _, _, e = WriteFixtureReceipt(j.root, j, d); e == nil || d.readyCalls != calls+1 {
		t.Fatal("historical CANARY bypassed fresh readiness")
	}
	if _, e = os.Stat(releaseReceiptFile(j.root, a.Operation)); !os.IsNotExist(e) {
		t.Fatal("failed readiness left a receipt")
	}
	d.reject = false
	if _, _, e = WriteFixtureReceipt(j.root, j, d); e != nil {
		t.Fatal(e)
	}
	d.reject = true
	if _, _, e = ReadFixtureReceipt(j.root, j, d, a.Operation); e == nil {
		t.Fatal("old receipt bypassed current readiness")
	}
	if _, _, e = WriteFixtureReceipt(j.root, j, d); e == nil {
		t.Fatal("existing receipt write bypassed current readiness")
	}
	if d.starts != 1 {
		t.Fatal("receipt path relaunched child")
	}
	t.Logf("deterministic state-machine check: alive identity retained in RECOVERING after READY failure; starts=%d; new and existing CANARY receipts revalidate readiness; no projection receipt on rejection", d.starts)
}
