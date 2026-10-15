//go:build windows

package ownedcorestop

import (
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"researchos.local/research-os/internal/store"
)

func TestOwnedCoreStopFrozenSubjectRejectsOtherWork(t *testing.T) {
	in := Input{Schema: InputSchema, OperationID: strings.Repeat("a", 32), SourceRepository: filepath.Join(t.TempDir(), "source"), DataRoot: filepath.Join(t.TempDir(), "data"), CorePID: 1,
		Subject: store.OwnedStopSubject{Run: OldRun, Epoch: 1, DispatchKey: OldDispatch, RequestKey: OldRequest, Project: "fixture"}}
	if err := validateInput(in); err != nil {
		t.Fatal(err)
	}
	for _, bad := range []store.OwnedStopSubject{
		{Run: "another", Epoch: 1, DispatchKey: OldDispatch, RequestKey: OldRequest, Project: "fixture"},
		{Run: OldRun, Epoch: 2, DispatchKey: OldDispatch, RequestKey: OldRequest, Project: "fixture"},
		{Run: OldRun, Epoch: 1, DispatchKey: "another", RequestKey: OldRequest, Project: "fixture"},
		{Run: OldRun, Epoch: 1, DispatchKey: OldDispatch, RequestKey: "another", Project: "fixture"},
	} {
		in.Subject = bad
		if err := validateInput(in); err == nil {
			t.Fatalf("other work accepted: %+v", bad)
		}
	}
}

func TestOwnedCoreStopInvalidPreflightNeverCreatesOutput(t *testing.T) {
	base := t.TempDir()
	out := filepath.Join(base, "new-output")
	in := Input{Schema: InputSchema, OperationID: strings.Repeat("b", 32), SourceRepository: base, DataRoot: filepath.Join(base, "data"), CorePID: 1,
		Subject: store.OwnedStopSubject{Run: OldRun, Epoch: 1, DispatchKey: OldDispatch, RequestKey: "wrong", Project: "fixture"}}
	raw, err := json.Marshal(in)
	if err != nil {
		t.Fatal(err)
	}
	inputPath := filepath.Join(base, "input.json")
	if err := os.WriteFile(inputPath, raw, 0600); err != nil {
		t.Fatal(err)
	}
	if _, _, err := Preflight(context.Background(), inputPath, in.OperationID, out); err == nil {
		t.Fatal("wrong historical subject passed preflight")
	}
	if _, err := os.Stat(out); !os.IsNotExist(err) {
		t.Fatalf("invalid preflight created output: %v", err)
	}
}
