//go:build windows

package main

import (
	"flag"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestReleaseHostLeaseRejectsBothJournalNamespacesBeforeCanary(t *testing.T) {
	for _, namespace := range []string{"qualification-failure-maintenance", "runtime-verifier-replacements"} {
		t.Run(namespace, func(t *testing.T) {
			root := t.TempDir()
			database := filepath.Join(root, "researchos.sqlite")
			if err := os.WriteFile(database, []byte("disposable source"), 0600); err != nil {
				t.Fatal(err)
			}
			lease, err := openReleaseHostSourceLease(database)
			if err != nil || !lease.Held() {
				t.Fatalf("ordinary source lease: %v", err)
			}
			if err := lease.Close(); err != nil {
				t.Fatal(err)
			}
			if err := os.MkdirAll(filepath.Join(root, "host", namespace, "unexpected-operation"), 0700); err != nil {
				t.Fatal(err)
			}
			lease, gateErr := openReleaseHostSourceLease(database)
			if gateErr == nil || lease != nil {
				t.Fatal("pending or malformed namespace admitted release host")
			}
			private := filepath.Join(root, "never-opened-canary")
			oldArgs, oldFlags := os.Args, flag.CommandLine
			defer func() { os.Args, flag.CommandLine = oldArgs, oldFlags }()
			flag.CommandLine = flag.NewFlagSet("release_host_test", flag.ContinueOnError)
			os.Args = []string{"release_host", "-db", database, "-contracts", filepath.Join(root, "contracts"), "-migration", filepath.Join(root, "migration.sql"),
				"-private", private, "-project", "fixture", "-operation", "fixture"}
			if err := run(); err == nil || !strings.Contains(err.Error(), gateErr.Error()) {
				t.Fatalf("release host proceeded past early journal gate: %v", err)
			}
			if _, err := os.Lstat(private); !os.IsNotExist(err) {
				t.Fatalf("early gate opened Canary root: %v", err)
			}
		})
	}
}
