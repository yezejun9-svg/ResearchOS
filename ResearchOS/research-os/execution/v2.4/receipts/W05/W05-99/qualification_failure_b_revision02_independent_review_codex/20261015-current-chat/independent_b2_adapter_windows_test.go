//go:build windows

package runtime

import (
	"golang.org/x/sys/windows"
	"os"
	"os/user"
	"path/filepath"
	"testing"
)

func independentB2SetACL(t *testing.T, path, sddl string) {
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
func TestIndependentB2NativeACLAndIdentityContinuity(t *testing.T) {
	current, err := user.Current()
	if err != nil {
		t.Fatal(err)
	}
	sid, err := windows.StringToSid(current.Uid)
	if err != nil {
		t.Fatal(err)
	}
	for _, cut := range []struct {
		name, acl string
		accept    bool
	}{
		{"safe_file_all", "(A;OICI;FA;;;" + current.Uid + ")", true},
		{"safe_generic_all", "(A;OICI;GA;;;" + current.Uid + ")", true},
		{"world_write_dac", "(A;OICI;FA;;;" + current.Uid + ")(A;;WD;;;WD)", false},
		{"world_generic_all", "(A;OICI;FA;;;" + current.Uid + ")(A;;GA;;;WD)", false},
		{"inherit_only_owner", "(A;OIIO;FA;;;" + current.Uid + ")", false},
		{"unsupported_deny", "(D;;WD;;;WD)(A;OICI;FA;;;" + current.Uid + ")", false},
		{"system_extra_principal", "(A;OICI;FA;;;" + current.Uid + ")(A;;FA;;;SY)", false},
	} {
		t.Run(cut.name, func(t *testing.T) {
			directory := t.TempDir()
			independentB2SetACL(t, directory, "D:P"+cut.acl)
			defer func() {
				if _, err := PrivateDirectory(directory); err != nil {
					t.Error(err)
				}
			}()
			g, err := qualificationGuardDirectory(directory, true)
			if g != nil {
				defer g.Close()
			}
			if (err == nil) != cut.accept {
				t.Fatalf("accept=%t error=%v", cut.accept, err)
			}
		})
	}
	t.Run("native_locks_across_read_write_flush", func(t *testing.T) {
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
		defer guard.Close()
		if err := os.Rename(root, root+"-moved"); err == nil {
			t.Fatal("held ancestor could be renamed")
		}
		if err := os.Rename(directory, directory+"-moved"); err == nil {
			t.Fatal("held directory could be renamed")
		}
		path := filepath.Join(directory, "fact.json")
		f, err := qualificationOpenSource(path, sid, true)
		if err != nil {
			t.Fatal(err)
		}
		raw := []byte("{\"independent\":true}")
		if _, err := f.file.Write(raw); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(path, []byte("replaced"), 0600); err == nil {
			t.Fatal("write-open allowed competing writer")
		}
		if err := os.Remove(path); err == nil {
			t.Fatal("write-open allowed deletion")
		}
		if err := f.file.Sync(); err != nil {
			t.Fatal(err)
		}
		if err := f.Check(); err != nil {
			t.Fatal(err)
		}
		if err := guard.Check(); err != nil {
			t.Fatal(err)
		}
		if err := f.file.Close(); err != nil {
			t.Fatal(err)
		}
		reader, err := qualificationOpenSource(path, sid, false)
		if err != nil {
			t.Fatal(err)
		}
		defer reader.file.Close()
		if err := os.WriteFile(path, []byte("replaced"), 0600); err == nil {
			t.Fatal("read-open allowed competing writer")
		}
		if err := os.Rename(path, path+".moved"); err == nil {
			t.Fatal("read-open allowed rename")
		}
		got, err := reader.ReadBounded(1024)
		if err != nil || string(got) != string(raw) {
			t.Fatalf("native continuous bytes: %s %v", got, err)
		}
	})
}
