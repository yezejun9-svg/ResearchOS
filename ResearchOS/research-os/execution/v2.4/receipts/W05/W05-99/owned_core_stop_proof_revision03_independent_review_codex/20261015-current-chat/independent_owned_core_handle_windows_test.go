//go:build windows

package supervisor

import (
	"context"
	"errors"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
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

func TestOwnedCoreFixtureParent(t *testing.T) {
	if os.Getenv("RESEARCHOS_OWNED_PARENT_CHILD") != "yes" {
		return
	}
	cmd := exec.Command(os.Args[0], "-test.run=^TestOwnedCoreFixtureChild$")
	cmd.Env = append(os.Environ(), "RESEARCHOS_OWNED_CORE_CHILD=yes")
	if err := cmd.Start(); err != nil {
		t.Fatal(err)
	}
	defer func() { _ = cmd.Process.Kill(); _ = cmd.Wait() }()
	if err := os.WriteFile(os.Getenv("RESEARCHOS_OWNED_CHILD_PID_FILE"), []byte(strconv.Itoa(cmd.Process.Pid)), 0600); err != nil {
		t.Fatal(err)
	}
	time.Sleep(12 * time.Second)
}

func TestOwnedCoreAndParentImageAncestorsRetained(t *testing.T) {
	base := t.TempDir()
	imageDir := filepath.Join(base, "image", "nested")
	if err := os.MkdirAll(imageDir, 0700); err != nil {
		t.Fatal(err)
	}
	source, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	input, err := os.Open(source)
	if err != nil {
		t.Fatal(err)
	}
	defer input.Close()
	copyPath := filepath.Join(imageDir, "parent.exe")
	output, err := os.Create(copyPath)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = io.Copy(output, input); err != nil {
		output.Close()
		t.Fatal(err)
	}
	if err = output.Close(); err != nil {
		t.Fatal(err)
	}
	alias := filepath.Join(imageDir, "alias.exe")
	if err = os.Link(copyPath, alias); err != nil {
		t.Fatalf("new fixture hardlink cut unavailable: %v", err)
	}
	if image, e := ownedNativeImage(copyPath); e == nil {
		image.Close()
		t.Fatal("hardlink image alias accepted")
	}
	if err = os.Remove(alias); err != nil {
		t.Fatal(err)
	}
	linkDir := filepath.Join(base, "image-link")
	if err = os.Symlink(imageDir, linkDir); err != nil {
		if output, e := exec.Command("cmd", "/c", "mklink", "/J", linkDir, imageDir).CombinedOutput(); e != nil {
			t.Logf("REPARSE_CUT_UNAVAILABLE symlink=%v junction=%v output=%q", err, e, output)
		} else {
			err = nil
		}
	}
	if err == nil {
		if image, e := ownedNativeImage(filepath.Join(linkDir, "parent.exe")); e == nil {
			image.Close()
			t.Fatal("reparse image ancestor accepted")
		}
	}
	pidFile := filepath.Join(base, "child.pid")
	parent := exec.Command(copyPath, "-test.run=^TestOwnedCoreFixtureParent$")
	parent.Env = append(os.Environ(), "RESEARCHOS_OWNED_PARENT_CHILD=yes", "RESEARCHOS_OWNED_CHILD_PID_FILE="+pidFile)
	if err = parent.Start(); err != nil {
		t.Fatal(err)
	}
	defer func() { _ = parent.Process.Kill(); _ = parent.Wait() }()
	var childPID uint64
	for until := time.Now().Add(5 * time.Second); time.Now().Before(until); time.Sleep(20 * time.Millisecond) {
		if raw, e := os.ReadFile(pidFile); e == nil {
			childPID, err = strconv.ParseUint(string(raw), 10, 32)
			if err != nil {
				t.Fatal(err)
			}
			break
		}
	}
	if childPID == 0 {
		t.Fatal("owned fixture child PID unavailable")
	}
	childProcess, err := os.FindProcess(int(childPID))
	if err != nil {
		t.Fatal(err)
	}
	defer childProcess.Kill()
	id, err := ObserveOwnedCoreReadOnly(uint32(childPID))
	if err != nil {
		t.Fatal(err)
	}
	if id.ParentPID != uint32(parent.Process.Pid) || id.ImagePath != copyPath || id.ParentImagePath != copyPath {
		t.Fatalf("actual Core/parent fixture images differ: %+v", id)
	}
	h, err := OpenOwnedCoreRetained(id)
	if err != nil {
		t.Fatal(err)
	}
	defer h.Close()
	if len(h.core.image.ancestors) < 2 || len(h.parent.image.ancestors) < 2 || h.core.image.final.index != id.ImageIndex || h.parent.image.final.index != id.ParentImageIndex {
		t.Fatal("Core and parent image ancestors were not retained")
	}
	if err = os.Rename(imageDir, filepath.Join(base, "swapped")); err == nil {
		t.Fatal("retained image ancestor allowed directory swap")
	}
	if file, e := os.OpenFile(copyPath, os.O_WRONLY, 0); e == nil {
		file.Close()
		t.Fatal("retained image allowed write-sharing")
	}
	wrong := id
	wrong.ParentCreatedNS++
	if other, e := OpenOwnedCoreRetained(wrong); e == nil {
		other.Close()
		t.Fatal("wrong parent identity accepted")
	}
	if err = h.verifyRetained(); err != nil {
		t.Fatal(err)
	}
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

func TestOwnedCoreExpiredGrantBoundaryMakesZeroNativeCalls(t *testing.T) {
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
	h.terminate = func(windows.Handle, uint32) error { called++; return nil }
	before := time.Now().Add(-time.Second)
	exit, err := h.TerminateOnceAndWaitUntil(time.Second, before, before)
	if err == nil || exit.TerminateCalls != 0 || called != 0 || h.terminateCalls != 0 {
		t.Fatalf("expired signal boundary allowed call: %+v calls=%d err=%v", exit, called, err)
	}
	if _, err = ObserveOwnedCoreReadOnly(uint32(core.Process.Pid)); err != nil {
		t.Fatalf("zero-call target died: %v", err)
	}
}

func TestOwnedCoreCallerCancellationAtFinalNativeBoundary(t *testing.T) {
	for _, mode := range []string{"already canceled", "earlier caller deadline", "canceled by prewait"} {
		t.Run(mode, func(t *testing.T) {
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
			ctx, cancel := context.WithCancel(context.Background())
			if mode == "earlier caller deadline" {
				ctx, cancel = context.WithDeadline(context.Background(), time.Now().Add(10*time.Millisecond))
			}
			defer cancel()
			if mode == "already canceled" {
				cancel()
			}
			if mode == "canceled by prewait" {
				h.wait = func(handle windows.Handle, ms uint32) (uint32, error) {
					if ms == 0 {
						cancel()
					}
					return windows.WaitForSingleObject(handle, ms)
				}
			}
			if mode == "earlier caller deadline" {
				h.wait = func(handle windows.Handle, ms uint32) (uint32, error) {
					if ms == 0 {
						time.Sleep(20 * time.Millisecond)
					}
					return windows.WaitForSingleObject(handle, ms)
				}
			}
			calls := 0
			h.terminate = func(windows.Handle, uint32) error { calls++; return nil }
			exit, err := h.TerminateOnceAndWaitUntilContext(ctx, time.Second, time.Now().Add(time.Minute), time.Now().Add(time.Minute))
			if err == nil || exit.TerminateCalls != 0 || calls != 0 || h.terminateCalls != 0 {
				t.Fatalf("canceled/deadline native signal occurred: %+v calls=%d err=%v", exit, calls, err)
			}
			if _, err = ObserveOwnedCoreReadOnly(uint32(core.Process.Pid)); err != nil {
				t.Fatalf("zero-call Core disappeared: %v", err)
			}
		})
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

func TestIndependentUnsafeImageACLRejected(t *testing.T) {
 for _, cut := range []string{"ancestor", "image"} {
  t.Run(cut,func(t *testing.T) {
   base:=t.TempDir(); imageDir:=filepath.Join(base,"image","nested")
   if err:=os.MkdirAll(imageDir,0700);err!=nil { t.Fatal(err) }
   source,err:=os.Executable();if err!=nil {t.Fatal(err)}
   raw,err:=os.ReadFile(source);if err!=nil {t.Fatal(err)}
   imagePath:=filepath.Join(imageDir,"parent.exe")
   if err=os.WriteFile(imagePath,raw,0700);err!=nil {t.Fatal(err)}
   target:=imageDir;if cut=="image" {target=imagePath}
   sd,err:=windows.SecurityDescriptorFromString("D:P(A;;FA;;;WD)");if err!=nil {t.Fatal(err)}
   acl,_,err:=sd.DACL();if err!=nil {t.Fatal(err)}
   if err=windows.SetNamedSecurityInfo(target,windows.SE_FILE_OBJECT,windows.DACL_SECURITY_INFORMATION|windows.PROTECTED_DACL_SECURITY_INFORMATION,nil,nil,acl,nil);err!=nil {t.Fatal(err)}
   observedSD,err:=windows.GetNamedSecurityInfo(target,windows.SE_FILE_OBJECT,windows.OWNER_SECURITY_INFORMATION|windows.DACL_SECURITY_INFORMATION);if err!=nil {t.Fatal(err)}
   t.Logf("OWN_FIXTURE target=%s initial_security=%s cut=%s explicit_Everyone_FULL_ACCESS=true",target,observedSD.String(),cut)
   pidFile:=filepath.Join(base,"child.pid")
   parent:=exec.Command(imagePath,"-test.run=^TestOwnedCoreFixtureParent$")
   parent.Env=append(os.Environ(),"RESEARCHOS_OWNED_PARENT_CHILD=yes","RESEARCHOS_OWNED_CHILD_PID_FILE="+pidFile)
   if err=parent.Start();err!=nil {t.Fatal(err)}
   defer func(){_ = parent.Process.Kill();_ = parent.Wait()}()
   var childPID uint64
   for until:=time.Now().Add(5*time.Second);time.Now().Before(until);time.Sleep(20*time.Millisecond) {
    if raw,e:=os.ReadFile(pidFile);e==nil {childPID,err=strconv.ParseUint(string(raw),10,32);if err!=nil {t.Fatal(err)};break}
   }
   if childPID==0 {t.Fatal("owned child missing")}
   child,err:=os.FindProcess(int(childPID));if err!=nil {t.Fatal(err)};defer child.Kill()
   id,err:=ObserveOwnedCoreReadOnly(uint32(childPID));if err!=nil {t.Logf("unsafe initial ACL refused at observe: %v",err);return}
   if id.ImagePath!=imagePath || id.ParentImagePath!=imagePath {t.Fatal("unexpected fixture path")}
   h,err:=OpenOwnedCoreRetained(id);if err!=nil {t.Logf("unsafe initial ACL refused at retained open: %v",err);return};defer h.Close()
   if err=h.verifyRetained();err!=nil {t.Logf("unsafe initial ACL refused at retained verification: %v",err);return}
   if cut=="ancestor" {
    wide,e:=windows.UTF16PtrFromString(imageDir);if e!=nil {t.Fatal(e)}
    wh,e:=windows.CreateFile(wide,windows.GENERIC_WRITE,windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE|windows.FILE_SHARE_DELETE,nil,windows.OPEN_EXISTING,windows.FILE_FLAG_BACKUP_SEMANTICS|windows.FILE_FLAG_OPEN_REPARSE_POINT,0)
    t.Logf("retained_ancestor_generic_write_handle_open err=%v",e);if e==nil {_=windows.CloseHandle(wh)}
   }
   t.Errorf("UNSAFE_INITIAL_ACL_ACCEPTED: actual Core and parent image chain retained and verified with Everyone FULL_ACCESS on %s; native_signal_count=0",cut)
  })
 }
}
