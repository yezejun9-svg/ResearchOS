//go:build windows

package runtime

import (
	"golang.org/x/sys/windows"
	"os"
	"os/user"
	"path/filepath"
	"testing"
)

func TestIndependentB2GuardNamespaceSwap(t *testing.T) {
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
	heldID := guard.ids[len(guard.ids)-1]
	moved := directory + "-held"
	if err := os.Rename(directory, moved); err != nil {
		t.Logf("native no-delete guard prevented namespace change: %v", err)
		return
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
	defer replacement.Close()
	newID := replacement.ids[len(replacement.ids)-1]
	if heldID == newID {
		t.Fatal("namespace mutation did not change selected file identity")
	}
	checkErr := guard.Check()
	path := filepath.Join(directory, qualificationRejectionFile)
	file, err := qualificationOpenSource(path, guard.current, true)
	if err != nil {
		t.Fatal(err)
	}
	raw := []byte("{\"replacement_namespace\":true}")
	if _, err := file.file.Write(raw); err != nil {
		t.Fatal(err)
	}
	if err := file.file.Sync(); err != nil {
		t.Fatal(err)
	}
	fileCheck := file.Check()
	if err := file.file.Close(); err != nil {
		t.Fatal(err)
	}
	oldBytes, oldErr := os.ReadFile(filepath.Join(moved, qualificationRejectionFile))
	newBytes, newErr := os.ReadFile(path)
	if !os.IsNotExist(oldErr) || newErr != nil || string(newBytes) != string(raw) || len(oldBytes) != 0 {
		t.Fatalf("namespace cut not realized: old=%v new=%v", oldErr, newErr)
	}
	t.Logf("held native directory id=%+v replacement id=%+v; write+flush landed only in replacement namespace; guard.Check=%v file.Check=%v", heldID, newID, checkErr, fileCheck)
	if checkErr == nil && fileCheck == nil {
		t.Fatal("original directory guard accepted replacement pathname identity")
	}
}

func TestIndependentB2FileHandlesRetainContent(t *testing.T) {
	directory := t.TempDir()
	if _, err := PrivateDirectory(directory); err != nil {
		t.Fatal(err)
	}
	current, err := user.Current()
	if err != nil {
		t.Fatal(err)
	}
	sid, err := windows.StringToSid(current.Uid)
	if err != nil {
		t.Fatal(err)
	}
	guard, err := qualificationGuardDirectory(directory, true)
	if err != nil {
		t.Fatal(err)
	}
	defer guard.Close()
	path := filepath.Join(directory, "fact.json")
	f, err := qualificationOpenSource(path, sid, true)
	if err != nil {
		t.Fatal(err)
	}
	raw := []byte("{\"continuous\":true}")
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
		t.Fatalf("native read/write/flush continuity: %s %v", got, err)
	}
	t.Log("native writer/read handles blocked competing writes and file delete/rename; original bytes and identity survived write+flush+read")
}
