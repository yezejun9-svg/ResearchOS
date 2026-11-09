//go:build windows

package main

import (
	"os"
	"path/filepath"
	"testing"
)

// These user-mode fake cases check fixed operation shape, not Native policy.
func TestHelperFixedOperationsAreNarrow(t *testing.T) {
	root := t.TempDir()
	source := filepath.Join(root, "S")
	working := filepath.Join(root, "QW")
	denied := filepath.Join(root, "D")
	for _, dir := range []string{source, working, denied} {
		if err := os.Mkdir(dir, 0700); err != nil {
			t.Fatal(err)
		}
	}
	if err := os.WriteFile(filepath.Join(source, "allow.txt"), []byte("synthetic-allow"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(denied, "denied.txt"), []byte("synthetic-denied"), 0600); err != nil {
		t.Fatal(err)
	}
	read := readSource(filepath.Join(source, "allow.txt"))
	if !read.Opened || read.Errno != 0 || read.Bytes != len("synthetic-allow") || len(read.Digest) != 71 {
		t.Fatal("source read shape", read)
	}
	read = deniedRead(filepath.Join(denied, "denied.txt"))
	if !read.Opened || read.Errno != 0 || read.Digest != "" {
		t.Fatal("denied read must never emit contents", read)
	}
	missing := openWin(filepath.Join(working, "missing.txt"), false, "working_write_open")
	if missing.Opened || missing.Errno == 0 {
		t.Fatal("missing file misreported as write access", missing)
	}
	created := openWin(filepath.Join(working, "create-denied.txt"), true, "working_create")
	if !created.Opened || created.Errno != 0 {
		t.Fatal("create operation shape", created)
	}
	if _, err := os.Stat(filepath.Join(working, "create-denied.txt")); err != nil {
		t.Fatal("successful create evidence erased", err)
	}
}
