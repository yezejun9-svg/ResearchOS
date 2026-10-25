//go:build windows

package main

import (
	"os"
	"path/filepath"
	"testing"
)

func TestBackupSourceLeaseRejectsBothJournalNamespacesBeforeKeyOrOutput(t *testing.T) {
	for _, namespace := range []string{"qualification-failure-maintenance", "runtime-verifier-replacements"} {
		t.Run(namespace, func(t *testing.T) {
			root := t.TempDir()
			database := filepath.Join(root, "researchos.sqlite")
			if err := os.WriteFile(database, []byte("disposable source"), 0600); err != nil {
				t.Fatal(err)
			}
			owner, err := openBackupSourceLease(database)
			if err != nil || !owner.native.Held() {
				t.Fatalf("ordinary source lease: %v", err)
			}
			if err := owner.Close(); err != nil {
				t.Fatal(err)
			}
			if err := os.MkdirAll(filepath.Join(root, "host", namespace, "unexpected-operation"), 0700); err != nil {
				t.Fatal(err)
			}
			owner, gateErr := openBackupSourceLease(database)
			if gateErr == nil || owner != nil {
				t.Fatal("pending or malformed namespace admitted an ordinary source lease")
			}
			key := filepath.Join(root, "never-read.key")
			out := filepath.Join(root, "never-created")
			oldArgs := os.Args
			defer func() { os.Args = oldArgs }()
			os.Args = []string{"backup", "create", "--db", database, "--key-file", key, "--out", out, "--root", root}
			if err := run(); err == nil || err.Error() != gateErr.Error() {
				t.Fatalf("backup proceeded past early journal gate: %v", err)
			}
			for _, path := range []string{key, out} {
				if _, err := os.Lstat(path); !os.IsNotExist(err) {
					t.Fatalf("early gate wrote %s: %v", path, err)
				}
			}
		})
	}
}
