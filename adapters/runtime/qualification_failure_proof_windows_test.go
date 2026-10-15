//go:build windows

package runtime

import (
	"errors"
	"os"
	"os/exec"
	"os/user"
	"path/filepath"
	"strings"
	"testing"

	"golang.org/x/sys/windows"
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

func TestQualificationProtectedEveryoneDACLRefusedWithoutRepair(t *testing.T) {
	directory := t.TempDir()
	current, err := user.Current()
	if err != nil {
		t.Fatal(err)
	}
	sd, err := windows.SecurityDescriptorFromString("O:" + current.Uid + "D:P(A;;FA;;;" + current.Uid + ")(A;;FA;;;WD)")
	if err != nil {
		t.Fatal(err)
	}
	acl, _, err := sd.DACL()
	if err != nil {
		t.Fatal(err)
	}
	if err := windows.SetNamedSecurityInfo(directory, windows.SE_FILE_OBJECT, windows.DACL_SECURITY_INFORMATION|windows.PROTECTED_DACL_SECURITY_INFORMATION, nil, nil, acl, nil); err != nil {
		t.Fatal(err)
	}
	if err := PersistQualificationRejection(directory, []byte(`{"outcome":"NO_EFFECT"}`)); err == nil {
		t.Fatal("protected Everyone grant accepted")
	}
	if _, err := os.Stat(filepath.Join(directory, qualificationRejectionFile)); !os.IsNotExist(err) {
		t.Fatal("rejected protected ACL wrote a receipt")
	}
	if _, err := qualificationGuardDirectory(directory, true); err == nil {
		t.Fatal("DACL was silently repaired")
	}
}

func TestQualificationProtectedInheritedEveryoneDACLAndFileRefused(t *testing.T) {
	current, err := user.Current()
	if err != nil {
		t.Fatal(err)
	}
	set := func(path, sddl string) {
		t.Helper()
		sd, err := windows.SecurityDescriptorFromString(sddl)
		if err != nil {
			t.Fatal(err)
		}
		acl, _, err := sd.DACL()
		if err != nil {
			t.Fatal(err)
		}
		if err := windows.SetNamedSecurityInfo(path, windows.SE_FILE_OBJECT, windows.DACL_SECURITY_INFORMATION|windows.PROTECTED_DACL_SECURITY_INFORMATION, nil, nil, acl, nil); err != nil {
			t.Fatal(err)
		}
	}
	t.Run("inherited_directory", func(t *testing.T) {
		directory := t.TempDir()
		set(directory, "O:"+current.Uid+"D:P(A;;FA;;;"+current.Uid+")(A;ID;FA;;;WD)")
		if err := PersistQualificationRejection(directory, []byte(`{"outcome":"NO_EFFECT"}`)); err == nil {
			t.Fatal("inherited Everyone directory ACE accepted")
		}
	})
	t.Run("direct_source_file", func(t *testing.T) {
		directory := t.TempDir()
		if _, err := PrivateDirectory(directory); err != nil {
			t.Fatal(err)
		}
		key := "model-key"
		name := "effect-" + strings.TrimPrefix(Hash([]byte(key)), "sha256:") + ".json"
		path := filepath.Join(directory, name)
		if err := os.WriteFile(path, []byte(`{"version":1}`), 0600); err != nil {
			t.Fatal(err)
		}
		set(path, "O:"+current.Uid+"D:P(A;;FA;;;"+current.Uid+")(A;;FA;;;WD)")
		if _, err := ReadQualificationModelFact(directory, key); err == nil {
			t.Fatal("unsafe original Host source ACL accepted")
		}
	})
}

func TestQualificationPersistenceWriteAndSyncFailureConservative(t *testing.T) {
	for _, stage := range []string{"write", "sync"} {
		t.Run(stage, func(t *testing.T) {
			directory := t.TempDir()
			if _, err := PrivateDirectory(directory); err != nil {
				t.Fatal(err)
			}
			write := (*os.File).Write
			sync := (*os.File).Sync
			if stage == "write" {
				write = func(*os.File, []byte) (int, error) { return 0, errors.New("injected write failure") }
			} else {
				sync = func(*os.File) error { return errors.New("injected sync failure") }
			}
			if err := persistQualificationRejection(directory, []byte(`{"outcome":"NO_EFFECT"}`), write, sync); err == nil {
				t.Fatal("persistence failure accepted")
			}
			if err := PersistQualificationRejection(directory, []byte(`{"forged":true}`)); err == nil {
				t.Fatal("faulted create-new receipt was replaced")
			}
		})
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
