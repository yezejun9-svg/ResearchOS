//go:build windows

package runtime

import (
	"context"
	"encoding/json"
	"fmt"
	"golang.org/x/sys/windows"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func assertRuntime(t *testing.T, id string, want, got any, evidence any) {
	t.Helper()
	a, _ := json.Marshal(want)
	b, _ := json.Marshal(got)
	status := "PASS"
	if string(a) != string(b) {
		status = "FAIL"
	}
	row, _ := json.Marshal(map[string]any{"assertion_id": id, "expected": want, "actual": got, "status": status, "evidence": evidence})
	fmt.Println("W05_ASSERTION " + string(row))
	if status == "FAIL" {
		t.Fatal(id, string(row))
	}
}
func ps(script, dir string) Command {
	return Command{Executable: filepath.Join(os.Getenv("SystemRoot"), "System32", "WindowsPowerShell", "v1.0", "powershell.exe"), Args: []string{"-NoProfile", "-NonInteractive", "-Command", script}, Directory: dir}
}
func spec(t *testing.T, commands ...Command) Spec {
	return Spec{RunID: t.Name(), TaskID: "qualification", Epoch: 1, Commands: commands, Environment: Environment(""), Lease: 10 * time.Second, Timeout: 10 * time.Second}
}
func wait(t *testing.T, w *Worker) Journal {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	j, e := w.Wait(ctx)
	if e != nil {
		t.Fatal(e)
	}
	return j
}
func TestW05Protocol(t *testing.T) {
	good := []byte("{\"type\":\"thread.started\",\"thread_id\":\"x\"}\n{\"type\":\"turn.completed\",\"usage\":{\"input_tokens\":1}}\n")
	assertRuntime(t, "W05-G01-SETTLED", true, Parse(good, 0).Settled, nil)
	assertRuntime(t, "W05-G01-FAKE-SUCCESS", false, Parse([]byte("{\"type\":\"agent_end\"}\n"), 0).Settled, nil)
	assertRuntime(t, "W05-G01-DUPLICATE", Parse(good, 0), Parse(append(good, good...), 0), nil)
	assertRuntime(t, "W05-G01-TOOL-FAILED", "tool_failed", Parse(append([]byte("{\"type\":\"item.completed\",\"item\":{\"exit_code\":7}}\n"), good...), 0).Failure, nil)
	assertRuntime(t, "W05-G01-REDACTION", false, strings.Contains(string(Redact([]byte(`{"access_token":"secret","text":"Bearer abcd"}`))), "secret"), nil)
}

func TestW05ProtocolTransientReconnect(t *testing.T) {
	retry := "{\"type\":\"error\",\"message\":\"Reconnecting... 2/5 (stream disconnected before completion: 远程主机强迫关闭了一个现有的连接。 (os error 10054))\"}\n"
	complete := "{\"type\":\"item.completed\",\"item\":{\"type\":\"agent_message\",\"text\":\"{\\\"total\\\":425}\"}}\n{\"type\":\"turn.completed\"}\n"
	for _, test := range []struct{ name, stdout, stderr, failure string }{
		{"recovered", retry + complete, "", ""},
		{"unfinished", retry, "", "missing_settled"},
		{"retry_after_completion", complete + retry, "", "missing_settled"},
		{"repeated_retry_after_completion", retry + complete + retry, "", "missing_settled"},
		{"replayed_recovered_transcript", retry + complete + retry + complete, "", ""},
		{"terminal", retry + "{\"type\":\"turn.failed\"}\n" + complete, "", "request_failed"},
		{"unknown_error", "{\"type\":\"error\",\"message\":\"access denied\"}\n" + retry + complete, "", "request_failed"},
		{"malformed_diagnostic", "{\"type\":\"error\",\"message\":\"Reconnecting... access denied\"}\n" + complete, "", "request_failed"},
		{"tool_failure", "{\"type\":\"item.completed\",\"item\":{\"exit_code\":7}}\n" + retry + complete, "", "tool_failed"},
		{"policy_rejection", retry + complete, "Rejected: blocked by policy", "tool_permission_denied"},
	} {
		t.Run(test.name, func(t *testing.T) {
			got := ParseStreams([]byte(test.stdout), []byte(test.stderr), 0)
			if got.Failure != test.failure || got.Settled != (test.failure == "") {
				t.Fatalf("want failure %q; got %+v", test.failure, got)
			}
			if test.failure == "" && string(got.Result) != `{"total":425}` {
				t.Fatalf("lost structured result: %s", got.Result)
			}
		})
	}
}
func TestW05WindowsTreeCancel(t *testing.T) {
	dir := t.TempDir()
	script := `$p=Start-Process -FilePath $env:COMSPEC -ArgumentList '/c ping -n 40 127.0.0.1 > nul' -PassThru -WindowStyle Hidden; $p.Id | Set-Content child.pid; Start-Sleep -Seconds 40`
	w, e := Start(filepath.Join(dir, "journal"), spec(t, ps(script, dir), ps("'should never launch' | Set-Content forbidden.txt", dir)))
	if e != nil {
		t.Fatal(e)
	}
	deadline := time.Now().Add(6 * time.Second)
	for time.Now().Before(deadline) {
		if _, e = os.Stat(filepath.Join(dir, "child.pid")); e == nil {
			break
		}
		time.Sleep(30 * time.Millisecond)
	}
	w.mu.Lock()
	ids, e := jobPIDs(w.job)
	w.mu.Unlock()
	if e != nil {
		t.Fatal(e)
	}
	assertRuntime(t, "W05-G01-NESTED-JOB-TREE", true, len(ids) >= 2, ids)
	assertRuntime(t, "W05-G01-STALE-CANCEL", true, w.Cancel(2, "stale") != nil, nil)
	if e = w.Cancel(1, "pending_queue_cancel"); e != nil {
		t.Fatal(e)
	}
	j := wait(t, w)
	assertRuntime(t, "W05-G01-CANCELLED", "CANCELLED", j.State, j)
	assertRuntime(t, "W05-G01-QUEUE", true, j.QueueEmpty && j.ChildrenStopped && j.Launched == 1 && j.Pending == 0, j)
	_, e = os.Stat(filepath.Join(dir, "forbidden.txt"))
	assertRuntime(t, "W05-G01-NO-LATE-LAUNCH", true, os.IsNotExist(e), nil)
	j2, e := Reconcile(filepath.Join(dir, "journal"))
	if e != nil {
		t.Fatal(e)
	}
	assertRuntime(t, "W05-G01-RECONCILE-CANCEL", "CANCELLED", j2.State, j2)
}
func TestW05WindowsTimeout(t *testing.T) {
	dir := t.TempDir()
	s := spec(t, ps("Start-Sleep -Seconds 30", dir))
	s.Timeout = 200 * time.Millisecond
	w, e := Start(filepath.Join(dir, "journal"), s)
	if e != nil {
		t.Fatal(e)
	}
	j := wait(t, w)
	assertRuntime(t, "W05-G01-TIMEOUT", true, j.State == "CANCELLED" && j.ChildrenStopped && j.Reason == "request_timeout", j)
}
func TestW05CrashHelper(t *testing.T) {
	if os.Getenv("W05_CRASH_HELPER") == "" {
		t.Skip("subprocess helper")
	}
	dir := os.Getenv("W05_CRASH_HELPER")
	w, e := Start(filepath.Join(dir, "journal"), spec(t, ps("Start-Sleep -Seconds 40", dir)))
	if e != nil {
		t.Fatal(e)
	}
	for w.Read().PID == 0 {
		time.Sleep(20 * time.Millisecond)
	}
	os.WriteFile(filepath.Join(dir, "ready"), []byte("ready"), 0600)
	time.Sleep(time.Minute)
}
func TestW05WindowsWorkerCrash(t *testing.T) {
	dir := t.TempDir()
	exe, e := os.Executable()
	if e != nil {
		t.Fatal(e)
	}
	c := exec.Command(exe, "-test.run=^TestW05CrashHelper$")
	c.Env = append(os.Environ(), "W05_CRASH_HELPER="+dir)
	if e = c.Start(); e != nil {
		t.Fatal(e)
	}
	defer c.Process.Kill()
	deadline := time.Now().Add(6 * time.Second)
	for time.Now().Before(deadline) {
		if _, e = os.Stat(filepath.Join(dir, "ready")); e == nil {
			break
		}
		time.Sleep(30 * time.Millisecond)
	}
	if e != nil {
		t.Fatal("helper failed", e)
	}
	c.Process.Kill()
	c.Wait()
	time.Sleep(200 * time.Millisecond)
	j, e := Reconcile(filepath.Join(dir, "journal"))
	if e != nil {
		t.Fatal(e)
	}
	assertRuntime(t, "W05-G01-CRASH-UNKNOWN", true, j.State == "UNKNOWN" && j.ChildrenStopped && j.QueueEmpty, j)
	_, e = Start(filepath.Join(dir, "journal"), spec(t, ps("exit 0", dir)))
	assertRuntime(t, "W05-G01-NO-BLIND-RETRY", true, e != nil, nil)
}

func TestW05WindowsFailureStopsQueue(t *testing.T) {
	dir := t.TempDir()
	s := spec(t, ps(`'{"type":"turn.failed"}'`, dir), ps(`'{"type":"turn.completed"}'`, dir))
	s.Model = "fixture-protocol"
	w, e := Start(filepath.Join(dir, "journal"), s)
	if e != nil {
		t.Fatal(e)
	}
	j := wait(t, w)
	assertRuntime(t, "W05-G01-FAILED-QUEUE", true, j.State == "FAILED" && j.Launched == 1 && !j.Protocol.Settled, j)
}

func TestW05WindowsJournalFailureCancel(t *testing.T) {
	dir := t.TempDir()
	journal := filepath.Join(dir, "journal")
	w, e := Start(journal, spec(t, ps("Start-Sleep -Seconds 30", dir)))
	if e != nil {
		t.Fatal(e)
	}
	for w.Read().PID == 0 {
		time.Sleep(10 * time.Millisecond)
	}
	// A real filesystem fault: the atomic-save staging path becomes a directory.
	if e = os.Mkdir(filepath.Join(journal, "journal.json.next"), 0700); e != nil {
		t.Fatal(e)
	}
	e = w.Cancel(1, "journal failure injection")
	j := wait(t, w)
	assertRuntime(t, "W05-G01-CANCEL-WRITE-FAIL", true, e != nil && j.ChildrenStopped && j.State == "UNKNOWN", j)
}

func TestW05WindowsMissingOutput(t *testing.T) {
	dir := t.TempDir()
	s := spec(t, ps(`'{"type":"turn.completed"}'`, dir))
	s.Model = "fixture-protocol"
	s.Outputs = []string{"missing.txt"}
	w, e := Start(filepath.Join(dir, "journal"), s)
	if e != nil {
		t.Fatal(e)
	}
	j := wait(t, w)
	assertRuntime(t, "W05-G01-MISSING-OUTPUT", true, j.Protocol.Settled && j.State == "FAILED" && j.Reason == "output_missing", j)
}

func TestW05WindowsToolPolicyFailure(t *testing.T) {
	dir := t.TempDir()
	s := spec(t, ps(`[Console]::Error.WriteLine('exec_command failed: rejected: blocked by policy'); '{"type":"turn.completed"}'`, dir), ps(`'{"type":"turn.completed"}'`, dir))
	s.Model = "fixture-protocol"
	w, e := Start(filepath.Join(dir, "journal"), s)
	if e != nil {
		t.Fatal(e)
	}
	j := wait(t, w)
	assertRuntime(t, "W05-G01-TOOL-POLICY-FAILURE", true, j.State == "FAILED" && j.Launched == 1 && j.Protocol.ToolFailed && j.Protocol.Failure == "tool_permission_denied", j)
}

func TestW05WindowsUnconfirmedInspection(t *testing.T) {
	dir := t.TempDir()
	name := "Local\\ResearchOS-denied-" + fmt.Sprint(time.Now().UnixNano())
	job, e := newJob(name)
	if e != nil {
		t.Fatal(e)
	}
	defer closeJob(job)
	sd, e := windows.SecurityDescriptorFromString("D:P")
	if e != nil {
		t.Fatal(e)
	}
	acl, _, e := sd.DACL()
	if e != nil {
		t.Fatal(e)
	}
	if e = windows.SetSecurityInfo(job, windows.SE_KERNEL_OBJECT, windows.DACL_SECURITY_INFORMATION|windows.PROTECTED_DACL_SECURITY_INFORMATION, nil, nil, acl, nil); e != nil {
		t.Fatal(e)
	}
	j := Journal{Job: name, PID: 0xffffffff, Created: 1, State: "RUNNING", Spec: Spec{RunID: "denied", TaskID: "inspection", Epoch: 1}}
	if e = save(filepath.Join(dir, "journal.json"), j); e != nil {
		t.Fatal(e)
	}
	actual, e := Reconcile(dir)
	if e != nil {
		t.Fatal(e)
	}
	assertRuntime(t, "W05-G01-INSPECTION-UNKNOWN", true, actual.State == "UNKNOWN" && !actual.ChildrenStopped, actual)
}
