//go:build windows

package domain

import (
	"context"
	"path/filepath"
	"testing"
	"time"

	rt "researchos.local/research-os/adapters/runtime"
)

func TestRuntimeDrainLeaseAndScanFence(t *testing.T) {
	f := setup(t)
	var seq int
	var name, path string
	if e := f.db.QueryRow("PRAGMA database_list").Scan(&seq, &name, &path); e != nil {
		t.Fatal(e)
	}
	root := filepath.Dir(path)
	lease, e := rt.AcquireDataRootLease(root)
	if e != nil {
		t.Fatal(e)
	}
	defer lease.Close()
	config := RuntimeCoordinatorConfig{DataRoot: root, APIURL: "http://127.0.0.1:1"}
	bad := config
	bad.Routes = []RuntimeCoordinatorRoute{{CommandID: "fixture", Executable: "relative.exe"}}
	if _, e = f.s.NewRuntimeCoordinatorWithLease(context.Background(), bad, lease); e == nil {
		t.Fatal("invalid constructor accepted")
	}
	c, e := f.s.NewRuntimeCoordinatorWithLease(context.Background(), config, lease)
	if e != nil {
		t.Fatalf("failed constructor retained borrow: %v", e)
	}
	if _, e = f.s.NewRuntimeCoordinatorWithLease(context.Background(), config, lease); e == nil {
		t.Fatal("second coordinator borrowed same lease")
	}
	if e = lease.Close(); e == nil {
		t.Fatal("owner closed lease while coordinator borrowed")
	}
	c.scanMu.Lock()
	result := make(chan error, 1)
	go func() { _, err := c.QuiesceForRelease(context.Background()); result <- err }()
	select {
	case err := <-result:
		if err == nil {
			t.Fatal("busy scan quiesced")
		}
	case <-time.After(200 * time.Millisecond):
		c.scanMu.Unlock()
		t.Fatal("quiesce waited for scan mutex")
	}
	c.scanMu.Unlock()
	if _, e = c.QuiesceForRelease(context.Background()); e != nil {
		t.Fatal(e)
	}
	if !c.quiesced {
		t.Fatal("scan fence missing")
	}
	c.ResumeAfterReleaseAbort()
	if c.quiesced {
		t.Fatal("abort failed to resume scans")
	}
	if e = c.Close(); e != nil {
		t.Fatal(e)
	}
	if l, e := rt.AcquireDataRootLease(root); e == nil {
		l.Close()
		t.Fatal("coordinator Close released owner OS lock before database close")
	}
	if e = f.db.Close(); e != nil {
		t.Fatal(e)
	}
	if e = lease.Close(); e != nil {
		t.Fatal(e)
	}
	l, e := rt.AcquireDataRootLease(root)
	if e != nil {
		t.Fatal("lease remained after DB and owner close", e)
	}
	l.Close()
	t.Log("single borrower; failed constructor returns borrow; busy scan immediate refusal; coordinator close retains DB owner lock")
}
