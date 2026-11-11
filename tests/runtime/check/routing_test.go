package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

// These tests never call main, boot, a provider, or the old suite's scratch cleanup.
func TestRuntimeExactRoutes(t *testing.T) {
	rows := []runtimeRouteRow{
		{"W05", "W05-01", "", runtimeServed, true},
		{"W05", "W05-02", "", runtimeServed, true},
		{"W05", "W05-G01", "", runtimeFixture, true},
		{"W12", "", "C11", runtimeFixture, true},
		{"W05", "W05-G02", "", runtimeV24Live, true},
		{"W05", "W05-H08", "", runtimeV24Live, true},
		{"W05", "W05-P01", "", runtimeV24Live, true},
		{"W05", "W05-U02", "", runtimeV24Live, true},
		{"W05", "", "A04", runtimeV24Live, true},
		{"W12", "W05-G01", "", "", false},
		{"W12", "W05-G02", "", "", false},
		{"W12", "", "A04", "", false},
		{"W05", "", "C11", "", false},
		{"W05", "W05-01", "A04", "", false},
		{"W05", "W05-G02", "A04", "", false},
		{"W12", "W05-G01", "C11", "", false},
		{"W05", "W99-DOES-NOT-EXIST", "", "", false},
		{"W12", "", "", "", false},
		{"W05", "", "", "", false},
		{"", "", "A04", "", false},
		{"", "W05-01", "", "", false},
		{"", "", "", "", false},
	}
	for _, row := range rows {
		t.Run(row.task+"/"+row.check+"/"+row.caseID, func(t *testing.T) {
			got, err := selectRuntimeRoute(row.task, row.check, row.caseID)
			if (err == nil) != row.valid || got != row.want {
				t.Fatalf("route=%s err=%v; want=%s valid=%t", got, err, row.want, row.valid)
			}
		})
	}
}

func TestRuntimeLockedPython(t *testing.T) {
	root := t.TempDir()
	lockDir := filepath.Join(root, "execution", "toolchains")
	if err := os.MkdirAll(lockDir, 0700); err != nil {
		t.Fatal(err)
	}
	tool := filepath.Join(root, "python.exe")
	content := []byte("inert test bytes; never executed")
	if err := os.WriteFile(tool, content, 0600); err != nil {
		t.Fatal(err)
	}
	sum := sha256.Sum256(content)
	digest := hex.EncodeToString(sum[:])
	writeLock := func(value any) {
		t.Helper()
		raw, err := json.Marshal(value)
		if err != nil {
			t.Fatal(err)
		}
		if err = os.WriteFile(filepath.Join(lockDir, "locked.json"), raw, 0600); err != nil {
			t.Fatal(err)
		}
	}
	pythonLock := func(path, hash string) any {
		return map[string]any{"tools": map[string]any{"python": map[string]string{"path": path, "sha256": hash}}}
	}
	for _, tc := range []struct {
		name  string
		value any
		good  bool
	}{
		{"valid", pythonLock(tool, digest), true},
		{"missing-tool", map[string]any{"tools": map[string]any{}}, false},
		{"relative-path", pythonLock("python.exe", digest), false},
		{"missing-binary", pythonLock(filepath.Join(root, "absent.exe"), digest), false},
		{"directory", pythonLock(root, digest), false},
		{"bad-digest", pythonLock(tool, "bad"), false},
		{"mismatched-digest", pythonLock(tool, string(make([]byte, 64))), false},
		{"wrong-digest", pythonLock(tool, "0000000000000000000000000000000000000000000000000000000000000000"), false},
	} {
		t.Run(tc.name, func(t *testing.T) {
			writeLock(tc.value)
			got, err := lockedPython(root)
			if (err == nil) != tc.good {
				t.Fatalf("got=%q err=%v", got, err)
			}
			if tc.good && got != tool {
				t.Fatalf("unlocked tool %q", got)
			}
		})
	}
	writeLock(pythonLock(tool, digest))
	t.Setenv("RESEARCHOS_PYTHON", filepath.Join(root, "untrusted.exe"))
	cmd, err := runtimePythonCommand(root, "ops/ci/runtime_v24.py", "live")
	if err != nil {
		t.Fatal(err)
	}
	if cmd.Path != tool || cmd.Dir != root || len(cmd.Args) != 6 || cmd.Args[3] != filepath.Join(root, "ops", "ci", "runtime_v24.py") || cmd.Args[5] != "live" {
		t.Fatalf("incorrect locked command: %#v", cmd)
	}
	fixture, err := runtimePythonCommand(root, "ops/ci/runtime.py", "fixture")
	if err != nil || fixture.Path != tool || fixture.Args[3] != filepath.Join(root, "ops", "ci", "runtime.py") || fixture.Args[5] != "fixture" {
		t.Fatalf("incorrect fixture command: %#v err=%v", fixture, err)
	}
	if err := os.WriteFile(filepath.Join(lockDir, "locked.json"), []byte("{"), 0600); err != nil {
		t.Fatal(err)
	}
	if _, err = lockedPython(root); err == nil {
		t.Fatal("malformed lock accepted")
	}
	if err := os.Remove(filepath.Join(lockDir, "locked.json")); err != nil {
		t.Fatal(err)
	}
	if _, err = lockedPython(root); err == nil {
		t.Fatal("missing lock accepted")
	}
}
