//go:build windows

package main

import (
	"bytes"
	"context"
	"encoding/json"
	"golang.org/x/sys/windows"
	"net"
	"os"
	"os/exec"
	"path/filepath"
	"researchos.local/research-os/adapters/protectedstore"
	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/ops/supervisor"
	"testing"
	"time"
)

func TestPersistentActualControlHostClosedQualification(t *testing.T) {
	repo, e := filepath.Abs(filepath.Join("..", "..", ".."))
	if e != nil {
		t.Fatal(e)
	}
	goexe := os.Getenv("RESEARCHOS_GO")
	if goexe == "" {
		t.Fatal("pinned RESEARCHOS_GO required")
	}
	base := t.TempDir()
	root := filepath.Join(base, "host")
	web := filepath.Join(base, "web")
	private := filepath.Join(base, "private")
	if e = os.MkdirAll(web, 0700); e != nil {
		t.Fatal(e)
	}
	if e = os.WriteFile(filepath.Join(web, "index.html"), []byte("fixture"), 0600); e != nil {
		t.Fatal(e)
	}
	p, e := protectedstore.NewCanary(private)
	if e != nil {
		t.Fatal(e)
	}
	if e = p.Close(); e != nil {
		t.Fatal(e)
	}
	control := filepath.Join(base, "control.exe")
	host := filepath.Join(base, "release_host.exe")
	for path, pkg := range map[string]string{control: "./apps/control", host: "./ops/supervisor/release_host"} {
		build := exec.Command(goexe, "build", "-trimpath", "-buildvcs=false", "-o", path, pkg)
		build.Dir = repo
		if raw, err := build.CombinedOutput(); err != nil {
			t.Fatalf("build %s: %v %s", pkg, err, raw)
		}
	}
	listener, e := net.Listen("tcp", "127.0.0.1:0")
	if e != nil {
		t.Fatal(e)
	}
	address := listener.Addr().String()
	listener.Close()
	ctx, cancel := context.WithTimeout(context.Background(), 40*time.Second)
	defer cancel()
	cmd := exec.CommandContext(ctx, host, "--control", control, "--root", root, "--work-dir", repo, "--web-dir", web, "--listen", address, "--private", private, "--contracts", filepath.Join(repo, "spec", "v2.0", "contracts"))
	cmd.Dir = repo
	cmd.SysProcAttr = &windows.SysProcAttr{CreationFlags: windows.CREATE_NO_WINDOW}
	stdin, e := cmd.StdinPipe()
	if e != nil {
		t.Fatal(e)
	}
	stdout, e := cmd.StdoutPipe()
	if e != nil {
		t.Fatal(e)
	}
	var stderr bytes.Buffer
	cmd.Stderr = &stderr
	if e = cmd.Start(); e != nil {
		t.Fatal(e)
	}
	done := false
	defer func() {
		stdin.Close()
		if !done {
			cancel()
			_ = cmd.Wait()
		}
		t.Logf("host stderr=%s", stderr.String())
	}()
	decoder := json.NewDecoder(stdout)
	type response struct {
		Status string                  `json:"status"`
		Error  string                  `json:"error"`
		State  supervisor.ReleaseState `json:"state"`
	}
	var ready response
	if e = decoder.Decode(&ready); e != nil {
		t.Fatalf("host startup: %v", e)
	}
	if ready.Status != "HOST_READY" || ready.State.Phase != "STABLE" || ready.State.PID == 0 {
		t.Fatalf("host startup binding: %+v", ready)
	}
	child := supervisor.ProcessIdentity{PID: ready.State.PID, CreatedNS: ready.State.CreatedNS, ImageSHA256: ready.State.ImageSHA256}
	// Keep this new test child's original observed handle solely for failure cleanup.
	h, e := windows.OpenProcess(windows.PROCESS_QUERY_LIMITED_INFORMATION|windows.SYNCHRONIZE|windows.PROCESS_TERMINATE, false, child.PID)
	if e != nil {
		t.Fatal(e)
	}
	var created, exit, kernel, user windows.Filetime
	if e = windows.GetProcessTimes(h, &created, &exit, &kernel, &user); e != nil || created.Nanoseconds() != child.CreatedNS {
		windows.CloseHandle(h)
		t.Fatal("new child original handle changed")
	}
	defer func() {
		if wait, _ := windows.WaitForSingleObject(h, 0); wait == windows.WAIT_TIMEOUT {
			_ = windows.TerminateProcess(h, 1)
			_, _ = windows.WaitForSingleObject(h, 5000)
		}
		windows.CloseHandle(h)
	}()
	if lease, err := rt.AcquireDataRootLease(filepath.Join(root, "data")); err == nil {
		lease.Close()
		t.Fatal("second authority writer acquired active root")
	}
	encoder := json.NewEncoder(stdin)
	call := func(c command) response {
		t.Helper()
		if e := encoder.Encode(c); e != nil {
			t.Fatal(e)
		}
		var r response
		if e := decoder.Decode(&r); e != nil {
			t.Fatal(e)
		}
		return r
	}
	status := call(command{Action: "status"})
	if status.Error != "" || status.State.PID != child.PID {
		t.Fatalf("persistent host lost slot: %+v", status)
	}
	denied := call(command{Action: "seal", Project: "unregistered", Candidate: "no-business-proof", Request: json.RawMessage(`{"action":"START_CANARY"}`)})
	if denied.Error == "" || denied.State.Phase != "STABLE" || denied.State.PID != child.PID {
		t.Fatalf("qualification gate opened: %+v", denied)
	}
	stopped := call(command{Action: "stop"})
	if stopped.Error != "" || stopped.State.Phase != "STOPPED" || stopped.State.PID != 0 {
		t.Fatalf("normal stop failed: %+v", stopped)
	}
	stdin.Close()
	if e = cmd.Wait(); e != nil {
		t.Fatal(e)
	}
	done = true
	if wait, e := windows.WaitForSingleObject(h, 0); e != nil || wait != windows.WAIT_OBJECT_0 {
		t.Fatalf("original child normal exit not observed: %d %v", wait, e)
	}
	lease, e := rt.AcquireDataRootLease(filepath.Join(root, "data"))
	if e != nil {
		t.Fatal(e)
	}
	lease.Close()
	// A restarted host gets no inherited child capability and cannot re-launch.
	j, e := supervisor.OpenReleaseJournal(filepath.Join(root, "release-state"))
	if e != nil {
		t.Fatal(e)
	}
	defer j.Close()
	seq := j.Sequence()
	driver := &supervisor.ControlFixtureDriver{Journal: j}
	if e = driver.ShutdownFixture(context.Background()); e == nil {
		t.Fatal("restart manufactured stop capability")
	}
	if j.Sequence() != seq || j.State().Phase != "STOPPED" {
		t.Fatal("restart replayed effect")
	}
	t.Logf("actual control host pid=%d child=%+v; private seal denied=%q; second writer refused; normal exit+lease release; restart no replay; ACTUAL_CONTROL_BEHAVIOR_PROOF=UNAVAILABLE", cmd.Process.Pid, child, denied.Error)
}
