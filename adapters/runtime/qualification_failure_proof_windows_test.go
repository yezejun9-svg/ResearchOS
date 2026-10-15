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

func TestQualificationDirectoryGuardBindsFinalNamespace(t *testing.T) {
	root := t.TempDir()
	directory := filepath.Join(root, "dispatch")
	if err := os.Mkdir(directory, 0700); err != nil {
		t.Fatal(err)
	}
	if _, err := PrivateDirectory(directory); err != nil {
		t.Fatal(err)
	}
	guard, err := qualificationGuardDirectory(directory, true)
	if err != nil {
		t.Fatal(err)
	}
	heldID := guard.ids[len(guard.ids)-1]
	moved := directory + "-held"
	if err := os.Rename(directory, moved); err == nil {
		guard.Close()
		t.Fatal("selected directory was renamed while its native guard was held")
	}
	path := filepath.Join(directory, qualificationRejectionFile)
	f, err := qualificationOpenSource(path, guard.current, true)
	if err != nil {
		guard.Close()
		t.Fatal(err)
	}
	raw := []byte(`{"original_namespace":true}`)
	if _, err := f.file.Write(raw); err != nil {
		t.Fatal(err)
	}
	if err := f.file.Sync(); err != nil {
		t.Fatal(err)
	}
	if err := errors.Join(f.Check(), guard.Check(), f.file.Close()); err != nil {
		guard.Close()
		t.Fatal(err)
	}
	guard.Close()
	if err := os.Rename(directory, moved); err != nil {
		t.Fatalf("directory remained locked after guard close: %v", err)
	}
	if err := os.Mkdir(directory, 0700); err != nil {
		t.Fatal(err)
	}
	if _, err := PrivateDirectory(directory); err != nil {
		t.Fatal(err)
	}
	replacement, err := qualificationGuardDirectory(directory, true)
	if err != nil {
		t.Fatal(err)
	}
	newID := replacement.ids[len(replacement.ids)-1]
	replacement.Close()
	if heldID == newID {
		t.Fatal("replacement did not change native directory identity")
	}
	oldBytes, oldErr := os.ReadFile(filepath.Join(moved, qualificationRejectionFile))
	if oldErr != nil || string(oldBytes) != string(raw) {
		t.Fatalf("write/flush missed retained original directory: %v", oldErr)
	}
	if _, err := os.Stat(path); !os.IsNotExist(err) {
		t.Fatal("replacement directory inherited a receipt from the original namespace")
	}
}

func TestQualificationSourceFileHandleBlocksCompetingChange(t *testing.T) {
	directory := t.TempDir()
	if _, err := PrivateDirectory(directory); err != nil {
		t.Fatal(err)
	}
	guard, err := qualificationGuardDirectory(directory, true)
	if err != nil {
		t.Fatal(err)
	}
	defer guard.Close()
	path := filepath.Join(directory, "fact.json")
	f, err := qualificationOpenSource(path, guard.current, true)
	if err != nil {
		t.Fatal(err)
	}
	raw := []byte(`{"continuous":true}`)
	if _, err := f.file.Write(raw); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte("changed"), 0600); err == nil {
		t.Fatal("write-open allowed a competing writer")
	}
	if err := os.Remove(path); err == nil {
		t.Fatal("write-open allowed deletion")
	}
	if err := f.file.Sync(); err != nil {
		t.Fatal(err)
	}
	if err := errors.Join(f.Check(), guard.Check(), f.file.Close()); err != nil {
		t.Fatal(err)
	}
	reader, err := qualificationOpenSource(path, guard.current, false)
	if err != nil {
		t.Fatal(err)
	}
	defer reader.file.Close()
	if err := os.WriteFile(path, []byte("changed"), 0600); err == nil {
		t.Fatal("read-open allowed a competing writer")
	}
	if err := os.Rename(path, path+".moved"); err == nil {
		t.Fatal("read-open allowed rename")
	}
	got, err := reader.ReadBounded(1024)
	if err != nil || string(got) != string(raw) {
		t.Fatalf("write/flush/read changed original bytes: %s %v", got, err)
	}
}

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
