//go:build windows

package host

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"
	"testing"
	"time"
)

// Only the test executable reads these variables. The shipped maintenance
// implementation has no environment bypass or crash-control interface.
func TestRuntimeVerifierReplacementCrashChild(t *testing.T) {
	if os.Getenv("REPLACEMENT_TEST_CHILD") != "1" {
		return
	}
	var in RuntimeVerifierReplacementInput
	raw, e := os.ReadFile(os.Getenv("REPLACEMENT_TEST_INPUT"))
	if e != nil {
		t.Fatal(e)
	}
	if e = json.Unmarshal(raw, &in); e != nil {
		t.Fatal(e)
	}
	replacementBoundary = func(boundary string) {
		if boundary == os.Getenv("REPLACEMENT_TEST_BOUNDARY") {
			if e := os.WriteFile(os.Getenv("REPLACEMENT_TEST_MARKER"), []byte(boundary), 0600); e != nil {
				panic(e)
			}
			for {
				time.Sleep(time.Second)
			}
		}
	}
	replacementReplace = func(target, stage, backup string) error {
		f, e := os.OpenFile(os.Getenv("REPLACEMENT_TEST_CALLS"), os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0600)
		if e != nil {
			return e
		}
		if _, e = f.WriteString("replace\n"); e != nil {
			f.Close()
			return e
		}
		if e = f.Sync(); e != nil {
			f.Close()
			return e
		}
		if e = f.Close(); e != nil {
			return e
		}
		return callReplaceFile(target, stage, backup)
	}
	if out, e := RuntimeVerifierReplacement(context.Background(), in); e != nil {
		t.Fatalf("child before boundary: %+v: %v", out, e)
	}
	t.Fatal("child did not reach requested boundary")
}

func TestRuntimeVerifierReplacementCrashRecovery(t *testing.T) {
	for _, boundary := range []string{"directory", "snapshots", "prepared", "stage", "publishing", "replaced", "before-committed", "committed"} {
		t.Run(boundary, func(t *testing.T) {
			f := newReplacementFixture(t)
			in := f.preflight(t)
			input := filepath.Join(f.Base, "input.json")
			replacementTestWrite(t, input, in)
			marker, calls := filepath.Join(f.Base, "boundary.txt"), filepath.Join(f.Base, "calls.txt")
			cmd := exec.Command(os.Args[0], "-test.run=^TestRuntimeVerifierReplacementCrashChild$", "-test.v")
			cmd.Dir = f.Base
			cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
			cmd.Env = []string{"REPLACEMENT_TEST_CHILD=1", "REPLACEMENT_TEST_INPUT=" + input, "REPLACEMENT_TEST_BOUNDARY=" + boundary, "REPLACEMENT_TEST_MARKER=" + marker, "REPLACEMENT_TEST_CALLS=" + calls}
			for _, key := range []string{"SystemRoot", "WINDIR", "TEMP", "TMP"} {
				if value := os.Getenv(key); value != "" {
					cmd.Env = append(cmd.Env, key+"="+value)
				}
			}
			var output bytes.Buffer
			cmd.Stdout = &output
			cmd.Stderr = &output
			if e := cmd.Start(); e != nil {
				t.Fatal(e)
			}
			done := make(chan error, 1)
			go func() { done <- cmd.Wait() }()
			deadline := time.Now().Add(20 * time.Second)
			for {
				if _, e := os.Stat(marker); e == nil {
					break
				}
				select {
				case e := <-done:
					t.Fatalf("child exited early: %v %s", e, output.String())
				default:
				}
				if time.Now().After(deadline) {
					cmd.Process.Kill()
					<-done
					t.Fatalf("boundary timeout: %s", output.String())
				}
				time.Sleep(10 * time.Millisecond)
			}
			if e := cmd.Process.Kill(); e != nil {
				t.Fatal(e)
			}
			e := <-done
			if e == nil || cmd.ProcessState.ExitCode() == 0 {
				t.Fatal("expected actual killed Windows process")
			}
			t.Logf("native crash boundary=%s pid=%d exit=%d argv=%q cwd=%q env_allowlist=SystemRoot,WINDIR,TEMP,TMP,test-only-inputs", boundary, cmd.Process.Pid, cmd.ProcessState.ExitCode(), cmd.Args, cmd.Dir)
			gate := replacementTestGate(f.Root)
			if boundary == "committed" {
				if gate != nil {
					t.Fatal(gate)
				}
			} else if gate == nil {
				t.Fatal("normal startup gate accepted unfinished transaction")
			}
			before, _ := os.ReadFile(calls)
			recover := in
			recover.Action = "recover"
			recover.OperationID = f.Input.OperationID
			recover.RecoveryAction = "inspect"
			out, e := RuntimeVerifierReplacement(context.Background(), recover)
			if e != nil {
				t.Fatalf("inspect: %+v %v", out, e)
			}
			applied := boundary == "replaced" || boundary == "before-committed" || boundary == "committed"
			if applied {
				recover.RecoveryAction = "complete"
				if len(before) == 0 {
					t.Fatal("missing actual ReplaceFile call")
				}
			} else {
				recover.RecoveryAction = "abort"
				if len(before) != 0 {
					t.Fatal("unexpected ReplaceFile before publish")
				}
			}
			original := replacementReplace
			replacementReplace = func(string, string, string) error {
				t.Fatal("recover replayed ReplaceFile")
				return fmt.Errorf("forbidden replay")
			}
			out, e = RuntimeVerifierReplacement(context.Background(), recover)
			replacementReplace = original
			if e != nil {
				t.Fatalf("recover: %+v %v", out, e)
			}
			if applied && out.State != "COMMITTED" {
				t.Fatal(out)
			}
			if !applied && out.State != "ABORTED" {
				t.Fatal(out)
			}
			after, _ := os.ReadFile(calls)
			if !bytes.Equal(before, after) {
				t.Fatal("recovery changed replace call count")
			}
			if e = replacementTestGate(f.Root); e != nil {
				t.Fatal(e)
			}
			again, e := RuntimeVerifierReplacement(context.Background(), recover)
			if e != nil || again.State != out.State {
				t.Fatalf("repeated recovery: %+v %v", again, e)
			}
		})
	}
}

func TestRuntimeVerifierReplacementJournalCorruptionAndReparse(t *testing.T) {
	for _, kind := range []string{"event", "orphan-temp", "backup", "plan-conflict", "null-dacl", "inherited-acl", "hardlink"} {
		t.Run(kind, func(t *testing.T) {
			f := newReplacementFixture(t)
			in := f.preflight(t)
			if _, e := RuntimeVerifierReplacement(context.Background(), in); e != nil {
				t.Fatal(e)
			}
			dir := filepath.Join(f.Root, "host", replacementJournal, f.Input.OperationID)
			switch kind {
			case "event":
				os.WriteFile(filepath.Join(dir, "0003-committed.json"), []byte(`{"state":"COMMITTED"}`), 0600)
			case "orphan-temp":
				os.WriteFile(filepath.Join(dir, "orphan.tmp"), []byte("orphan"), 0600)
			case "backup":
				os.WriteFile(filepath.Join(dir, "actual-backup.bin"), []byte("third"), 0600)
			case "plan-conflict":
				path := filepath.Join(dir, "plan.json")
				raw, _ := os.ReadFile(path)
				os.WriteFile(path, append(raw, ' '), 0600)
			case "null-dacl":
				replacementNullACLForTest(t, filepath.Join(dir, "plan.json"))
			case "inherited-acl":
				replacementInheritedACLForTest(t, filepath.Join(dir, "plan.json"))
			case "hardlink":
				if e := os.Link(filepath.Join(dir, "plan.json"), filepath.Join(f.Base, "alias.json")); e != nil {
					t.Fatal(e)
				}
			}
			if replacementTestGate(f.Root) == nil {
				t.Fatal("corrupt journal accepted startup")
			}
		})
	}
	t.Run("junction", func(t *testing.T) {
		f := newReplacementFixture(t)
		link := filepath.Join(f.Base, "junction")
		cmd := exec.Command("cmd.exe", "/c", "mklink", "/J", link, f.Root)
		cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
		raw, e := cmd.CombinedOutput()
		if e != nil {
			t.Fatalf("real junction fixture failed: %v %s", e, raw)
		}
		defer os.Remove(link)
		in := f.Input
		in.DataRoot = link
		if _, e = RuntimeVerifierReplacement(context.Background(), in); e == nil {
			t.Fatal("junction accepted")
		}
	})
	t.Run("raw-hash-whitespace", func(t *testing.T) {
		f := newReplacementFixture(t)
		path := filepath.Join(f.Root, "host", "runtime-verifier-installation.json")
		raw, _ := os.ReadFile(path)
		raw = append(raw, []byte(strings.Repeat(" ", 3))...)
		os.WriteFile(path, raw, 0600)
		if _, e := RuntimeVerifierReplacement(context.Background(), f.Input); e == nil {
			t.Fatal("canonical equivalent raw drift accepted")
		}
	})
}
