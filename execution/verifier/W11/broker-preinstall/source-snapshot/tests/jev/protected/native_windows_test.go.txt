//go:build windows

package protected_test

import (
	"context"
	"encoding/json"
	"fmt"
	"golang.org/x/sys/windows"
	"os"
	"os/exec"
	"path/filepath"
	"researchos.local/research-os/adapters/protectedstore"
	sandbox "researchos.local/research-os/ops/experiment_sandbox"
	"strings"
	"syscall"
	"testing"
	"time"
)

func proof(t *testing.T, id string, want, got, evidence any) {
	t.Helper()
	a, _ := json.Marshal(want)
	b, _ := json.Marshal(got)
	status := "PASS"
	if string(a) != string(b) {
		status = "FAIL"
	}
	row, _ := json.Marshal(map[string]any{"assertion_id": id, "expected": want, "actual": got, "status": status, "evidence": evidence, "scope": "CANARY_ONLY", "formal_isolation": "BLOCKED"})
	fmt.Println("W11_PROTECTED_ASSERTION " + string(row))
	if status != "PASS" {
		t.Fatalf("%s", id)
	}
}
func store(t *testing.T) (*protectedstore.CanaryStore, string) {
	t.Helper()
	root := filepath.Join(t.TempDir(), "private")
	s, e := protectedstore.NewCanary(root)
	if e != nil {
		t.Fatal(e)
	}
	t.Cleanup(func() { s.Close() })
	return s, root
}

func TestProtectedNativeStore(t *testing.T) {
	s, root := store(t)
	ctx := context.Background()
	payload := []byte("synthetic-private-canary-not-a-formal-holdout")
	blob, e := s.CreateCanary(ctx, "canary-project", "text/plain", payload)
	if e != nil {
		t.Fatal(e)
	}
	read, e := s.Read(ctx, blob)
	proof(t, "PROTECTED-NATIVE-ROUNDTRIP", []any{true, true}, []any{e == nil, string(read) == string(payload)}, map[string]any{"hash": blob.Hash, "bytes": blob.Size})
	boundary, e := s.Boundary(ctx)
	proof(t, "PROTECTED-CANARY-NO-INDEPENDENCE", []any{true, "CANARY_ONLY", false, true}, []any{e == nil, boundary.Mode, boundary.IndependentIdentity, boundary.UnrestrictedSameUserCanRead}, boundary)
	proof(t, "PROTECTED-LIVE-REFUSED", true, s.Ready(ctx, "LIVE") != nil, "no independent verifier provider installed")
	_, e = s.Describe(ctx, "other-project", blob.Ticket)
	proof(t, "PROTECTED-CROSS-PROJECT", true, e != nil, nil)
	_, e = s.Describe(ctx, "canary-project", "ps1:../../escape")
	proof(t, "PROTECTED-TICKET-TRAVERSAL", true, e != nil, nil)
	bad := blob
	bad.Hash = protectedstore.Digest([]byte("wrong"))
	_, e = s.Read(ctx, bad)
	proof(t, "PROTECTED-HASH-BINDING", true, e != nil, nil)
	path := filepath.Join(root, strings.TrimPrefix(blob.Ticket, "ps1:")+".bin")
	ownerRead, e := os.ReadFile(path)
	proof(t, "PROTECTED-SAME-USER-LIMIT", []any{true, true}, []any{e == nil, string(ownerRead) == string(payload)}, "unrestricted current user can read; this is not developer identity isolation")
	if e = os.Link(path, filepath.Join(root, "hardlink")); e != nil {
		t.Fatal(e)
	}
	_, e = s.Read(ctx, blob)
	proof(t, "PROTECTED-HARDLINK-REFUSED", true, e != nil, nil)
}
func TestProtectedACLDrift(t *testing.T) {
	s, root := store(t)
	ctx := context.Background()
	blob, e := s.CreateCanary(ctx, "canary-project", "text/plain", []byte("canary"))
	if e != nil {
		t.Fatal(e)
	}
	boundary, _ := s.Boundary(ctx)
	sd, e := windows.SecurityDescriptorFromString("D:P(A;OICI;FA;;;" + boundary.OwnerSID + ")(A;OICI;GR;;;WD)")
	if e != nil {
		t.Fatal(e)
	}
	acl, _, _ := sd.DACL()
	if e = windows.SetNamedSecurityInfo(root, windows.SE_FILE_OBJECT, windows.DACL_SECURITY_INFORMATION|windows.PROTECTED_DACL_SECURITY_INFORMATION, nil, nil, acl, nil); e != nil {
		t.Fatal(e)
	}
	_, e = s.Read(ctx, blob)
	proof(t, "PROTECTED-ACL-DRIFT", true, e != nil, "read checks actual handle owner/DACL and exactly one current-owner ACE")
}

func TestProtectedPathBoundary(t *testing.T) {
	s, root := store(t)
	e := os.Rename(root, root+"-moved")
	if e == nil {
		_, e = s.Boundary(context.Background())
	}
	proof(t, "PROTECTED-ROOT-RELOCATION-REFUSED", true, e != nil, "native handle path is revalidated even when POSIX rename succeeds")
	s, root = store(t)
	link := filepath.Join(filepath.Dir(root), "junction")
	command := exec.Command("cmd.exe", "/c", "mklink", "/J", link, root)
	command.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	if e = command.Run(); e != nil {
		t.Fatal("native junction canary setup failed", e)
	}
	candidate, e := protectedstore.NewCanary(filepath.Join(link, "nested"))
	if candidate != nil {
		candidate.Close()
	}
	proof(t, "PROTECTED-REPARSE-ANCESTOR", true, e != nil, "actual directory junction rejected before protected-root creation")
	_, e = s.Boundary(context.Background())
	if e != nil {
		t.Fatal(e)
	}
}
func TestProtectedProbeChild(t *testing.T) {
	pos := -1
	for i, a := range os.Args {
		if a == "--protected-probe" {
			pos = i
			break
		}
	}
	if pos < 0 {
		return
	}
	if pos+1 >= len(os.Args) {
		os.Exit(90)
	}
	path := os.Args[pos+1]
	_, readErr := os.ReadFile(path)
	writeErr := os.WriteFile(path, []byte("unexpected"), 0600)
	data, _ := json.Marshal(map[string]bool{"read_denied": os.IsPermission(readErr), "write_denied": os.IsPermission(writeErr)})
	fmt.Println(string(data))
	os.Exit(0)
}
func TestProtectedAppContainerCanary(t *testing.T) {
	s, root := store(t)
	blob, e := s.CreateCanary(context.Background(), "canary-project", "text/plain", []byte("synthetic AppContainer canary"))
	if e != nil {
		t.Fatal(e)
	}
	staging := t.TempDir()
	input := filepath.Join(staging, "input")
	output := filepath.Join(staging, "output")
	if e = os.Mkdir(input, 0700); e != nil {
		t.Fatal(e)
	}
	if e = os.Mkdir(output, 0700); e != nil {
		t.Fatal(e)
	}
	executable, e := os.Executable()
	if e != nil {
		t.Fatal(e)
	}
	bytes, e := os.ReadFile(executable)
	if e != nil {
		t.Fatal(e)
	}
	child := filepath.Join(input, "canary.exe")
	if e = os.WriteFile(child, bytes, 0700); e != nil {
		t.Fatal(e)
	}
	path := filepath.Join(root, strings.TrimPrefix(blob.Ticket, "ps1:")+".bin")
	receipt, e := sandbox.Run(context.Background(), sandbox.Command{Executable: child, Args: []string{"-test.run=^TestProtectedProbeChild$", "--", "--protected-probe", path}, InputDirectory: input, OutputDirectory: output, Timeout: 10 * time.Second})
	if e != nil {
		t.Fatal(e)
	}
	var result map[string]bool
	if e = json.Unmarshal(receipt.Stdout, &result); e != nil {
		t.Fatal(e)
	}
	proof(t, "PROTECTED-APPCONTAINER-DENIED", []any{0, true, true, true, 0}, []any{receipt.ExitCode, receipt.Stopped, result["read_denied"], result["write_denied"], len(receipt.Capabilities)}, map[string]any{"pid": receipt.PID, "appcontainer_sid": receipt.SID, "started_at": receipt.Started, "finished_at": receipt.Finished, "stdout": string(receipt.Stdout), "capture_scope": "synthetic only; default sandbox TEMP not qualified for formal protected logs"})
}
