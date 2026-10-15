//go:build windows

package supervisor

import (
	"errors"
	"os"
	"os/exec"
	"strings"
	"testing"
	"time"

	"golang.org/x/sys/windows"
)

func TestOwnedCoreFixtureChild(t *testing.T) {
	if os.Getenv("RESEARCHOS_OWNED_CORE_CHILD") != "yes" {
		return
	}
	time.Sleep(12 * time.Second)
}

func TestOwnedCoreTerminateFailureIsSingleUnknownAttempt(t *testing.T) {
	core := ownedCoreChild(t)
	defer func() { _ = core.Process.Kill(); _ = core.Wait() }()
	id, err := ObserveOwnedCoreReadOnly(uint32(core.Process.Pid))
	if err != nil {
		t.Fatal(err)
	}
	h, err := OpenOwnedCoreRetained(id)
	if err != nil {
		t.Fatal(err)
	}
	defer h.Close()
	called := 0
	h.terminate = func(windows.Handle, uint32) error { called++; return errors.New("injected native failure") }
	exit, err := h.TerminateOnceAndWait(time.Second)
	if err == nil || exit.TerminateCalls != 1 || exit.ExitObserved || called != 1 {
		t.Fatalf("one-call failure was not UNKNOWN: %+v calls=%d err=%v", exit, called, err)
	}
	if again, err := h.TerminateOnceAndWait(time.Second); err == nil || again.TerminateCalls != 0 || called != 1 {
		t.Fatalf("native failure retried: %+v calls=%d err=%v", again, called, err)
	}
	if _, err := ObserveOwnedCoreReadOnly(uint32(core.Process.Pid)); err != nil {
		t.Fatalf("injected failure affected target before cleanup: %v", err)
	}
}

func TestOwnedCoreWaitDeadlineNeverRetriesSignal(t *testing.T) {
	core := ownedCoreChild(t)
	defer func() { _ = core.Wait() }()
	id, err := ObserveOwnedCoreReadOnly(uint32(core.Process.Pid))
	if err != nil {
		t.Fatal(err)
	}
	h, err := OpenOwnedCoreRetained(id)
	if err != nil {
		t.Fatal(err)
	}
	defer h.Close()
	waits := 0
	h.wait = func(handle windows.Handle, ms uint32) (uint32, error) {
		waits++
		if waits == 2 {
			return uint32(windows.WAIT_TIMEOUT), nil
		}
		return windows.WaitForSingleObject(handle, ms)
	}
	exit, err := h.TerminateOnceAndWait(time.Second)
	if err == nil || exit.TerminateCalls != 1 || exit.ExitObserved || waits != 2 {
		t.Fatalf("deadline not reported UNKNOWN: %+v waits=%d err=%v", exit, waits, err)
	}
	if again, err := h.TerminateOnceAndWait(time.Second); err == nil || again.TerminateCalls != 0 || waits != 2 {
		t.Fatalf("deadline retried signal/wait: %+v waits=%d err=%v", again, waits, err)
	}
}

func ownedCoreChild(t *testing.T) *exec.Cmd {
	t.Helper()
	exe, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	cmd := exec.Command(exe, "-test.run=^TestOwnedCoreFixtureChild$")
	cmd.Env = append(os.Environ(), "RESEARCHOS_OWNED_CORE_CHILD=yes")
	if err = cmd.Start(); err != nil {
		t.Fatal(err)
	}
	return cmd
}

func TestOwnedCoreRetainedHandleSingleChildAndUnrelatedSurvives(t *testing.T) {
	core := ownedCoreChild(t)
	unrelated := ownedCoreChild(t)
	defer func() { _ = core.Wait(); _ = unrelated.Wait() }()
	observed, err := ObserveOwnedCoreReadOnly(uint32(core.Process.Pid))
	if err != nil {
		t.Fatal(err)
	}
	if observed.PID != uint32(core.Process.Pid) || observed.CreatedNS == 0 || observed.SID == "" || observed.ParentPID != uint32(os.Getpid()) || observed.ImageIndex == 0 || observed.ParentImageIndex == 0 {
		t.Fatalf("incomplete retained identity: %+v", observed)
	}
	wrong := observed
	wrong.CreatedNS++
	if h, e := OpenOwnedCoreRetained(wrong); e == nil {
		h.Close()
		t.Fatal("PID reuse identity accepted")
	}
	wrong = observed
	wrong.ImageSHA256 = strings.Repeat("0", 64)
	if h, e := OpenOwnedCoreRetained(wrong); e == nil {
		h.Close()
		t.Fatal("replacement image identity accepted")
	}
	h, err := OpenOwnedCoreRetained(observed)
	if err != nil {
		t.Fatal(err)
	}
	defer h.Close()
	if h.Identity() != observed {
		t.Fatal("retained identity changed")
	}
	exit, err := h.TerminateOnceAndWait(5 * time.Second)
	if err != nil || exit.TerminateCalls != 1 || !exit.ExitObserved || exit.ExitCode != OwnedCoreMaintenanceExitCode || exit.BeforeSignal {
		t.Fatalf("single exact termination failed: %+v %v", exit, err)
	}
	if second, e := h.TerminateOnceAndWait(time.Second); e == nil || second.TerminateCalls != 0 {
		t.Fatalf("second termination accepted: %+v %v", second, e)
	}
	other, e := ObserveOwnedCoreReadOnly(uint32(unrelated.Process.Pid))
	if e != nil || other.PID != uint32(unrelated.Process.Pid) {
		t.Fatalf("same-console unrelated child lost: %+v %v", other, e)
	}
}
