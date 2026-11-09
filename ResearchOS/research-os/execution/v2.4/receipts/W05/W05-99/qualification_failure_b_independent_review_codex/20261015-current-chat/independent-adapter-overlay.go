//go:build windows

package runtime

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

func TestQualificationRejectionReceiptPrivateCreateNew(t *testing.T) {
	private := t.TempDir()
	if _, err := PrivateDirectory(private); err != nil {
		t.Fatal(err)
	}
	first := []byte(`{"schema":"first-gate","outcome":"NO_EFFECT"}`)
	if err := PersistQualificationRejection(private, first); err != nil {
		t.Fatal(err)
	}
	if err := PersistQualificationRejection(private, []byte(`{"replaced":true}`)); err == nil {
		t.Fatal("immutable receipt overwritten")
	}
	got, err := os.ReadFile(filepath.Join(private, qualificationRejectionFile))
	if err != nil || string(got) != string(first) {
		t.Fatalf("create-new receipt changed: %v", err)
	}
	permissive := t.TempDir()
	if err := PersistQualificationRejection(permissive, first); err == nil {
		t.Fatal("permissive DACL accepted")
	}
	if _, err := os.Stat(filepath.Join(permissive, qualificationRejectionFile)); !os.IsNotExist(err) {
		t.Fatal("rejected DACL wrote receipt")
	}
	if err := PersistQualificationRejection(private, nil); err == nil {
		t.Fatal("empty receipt accepted")
	}
	if err := PersistQualificationRejection(private, make([]byte, 64*1024+1)); err == nil {
		t.Fatal("oversized receipt accepted")
	}
}

func TestQualificationRejectionReparseAncestorRefused(t *testing.T) {
	private := t.TempDir()
	if _, err := PrivateDirectory(private); err != nil {
		t.Fatal(err)
	}
	link := filepath.Join(t.TempDir(), "dispatch-link")
	if err := os.Symlink(private, link); err != nil {
		quote := func(path string) string { return `'` + strings.ReplaceAll(path, `'`, `''`) + `'` }
		command := `New-Item -ItemType Junction -Path ` + quote(link) + ` -Target ` + quote(private) + ` -ErrorAction Stop | Out-Null`
		if output, junctionErr := exec.Command("powershell", "-NoProfile", "-NonInteractive", "-Command", command).CombinedOutput(); junctionErr != nil {
			t.Fatalf("cannot create reparse ancestor: symlink=%v junction=%v output=%s", err, junctionErr, output)
		}
	}
	if err := PersistQualificationRejection(link, []byte(`{"outcome":"NO_EFFECT"}`)); err == nil {
		t.Fatal("reparse ancestor accepted")
	}
	if _, err := os.Stat(filepath.Join(private, qualificationRejectionFile)); !os.IsNotExist(err) {
		t.Fatal("reparse denial wrote target receipt")
	}
}

func TestBridgeCancelKeepsFirstCause(t *testing.T) {
	w := &Bridge{directory: t.TempDir(), cancel: func() {}, journal: BridgeJournal{State: "STARTED"}}
	w.Cancel("qualification first dispatch gate denied TOOL")
	w.Cancel("protocol reconciliation failed")
	j := w.Read()
	if !j.Cancelled || j.Reason != "qualification first dispatch gate denied TOOL" {
		t.Fatalf("first cause lost: %+v", j)
	}
	if _, err := ReadBridgeTerminal(w.Directory(), "missing-manifest"); err == nil {
		t.Fatal("cancel-only journal accepted as terminal")
	}
}

func TestIndependentQualificationProtectedWorldWritableDirectoryRejected(t *testing.T) {
 private := t.TempDir()
 if _, err := PrivateDirectory(private); err != nil { t.Fatal(err) }
 output, err := exec.Command("icacls", private, "/grant", "*S-1-1-0:(OI)(CI)F").CombinedOutput()
 t.Logf("icacls output=%s err=%v", output, err)
 if err != nil { t.Fatal(err) }
 output, err = exec.Command("icacls", private).CombinedOutput()
 t.Logf("actual fixture DACL=%s err=%v", output, err)
 if err != nil { t.Fatal(err) }
 err = PersistQualificationRejection(private, []byte("{\"outcome\":\"NO_EFFECT\"}"))
 if err == nil { t.Fatal("protected DACL containing current SID AND Everyone full access was accepted and receipt persisted") }
}