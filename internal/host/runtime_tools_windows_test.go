//go:build windows

package host

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"researchos.local/research-os/internal/domain"
)

func runtimeToolFixture(t *testing.T, access string) (*Host, string, *RootBinding) {
	t.Helper()
	base := t.TempDir()
	workspace := filepath.Join(base, "workspace")
	if err := os.Mkdir(workspace, 0700); err != nil {
		t.Fatal(err)
	}
	registry, err := openRootRegistry(filepath.Join(base, "host"))
	if err != nil {
		t.Fatal(err)
	}
	binding, err := registry.Register("selected-by-current-user", workspace, access, time.Now())
	if err != nil {
		t.Fatal(err)
	}
	return &Host{roots: registry}, workspace, binding
}

func runtimeToolPolicy() domain.Object {
	return domain.Object{"read_paths": []any{"allowed.txt"}, "write_paths": []any{"allowed.txt"}, "max_read_bytes": 8, "max_write_bytes": 64}
}

func runtimeToolCall(t *testing.T, host *Host, workspace, access, name string, args, policy domain.Object) domain.Object {
	t.Helper()
	result, err := host.ExecuteRuntimeTool(context.Background(), domain.RuntimeToolRequest{WorkspacePath: workspace, Access: access, Name: name, Arguments: args, Policy: policy})
	if err != nil {
		t.Fatal(err)
	}
	if result["details"] == nil || len(result["content"].([]any)) != 1 {
		t.Fatalf("invalid tool reply: %v", result)
	}
	return result["details"].(map[string]any)
}

func runtimeToolReject(t *testing.T, host *Host, workspace, access, name string, args, policy domain.Object) {
	t.Helper()
	if result, err := host.ExecuteRuntimeTool(context.Background(), domain.RuntimeToolRequest{WorkspacePath: workspace, Access: access, Name: name, Arguments: args, Policy: policy}); err == nil {
		t.Fatalf("unexpected tool success: %v", result)
	}
}

func TestRuntimeToolBoundReadWriteEditCAS(t *testing.T) {
	host, workspace, _ := runtimeToolFixture(t, AccessReadWrite)
	policy := runtimeToolPolicy()
	created := runtimeToolCall(t, host, workspace, AccessReadWrite, "write", domain.Object{"path": "allowed.txt", "content": "éabc", "expected_hash": nil}, policy)
	if created["content_hash"] != domain.Digest([]byte("éabc")) {
		t.Fatal(created)
	}
	read := runtimeToolCall(t, host, workspace, AccessReadWrite, "read", domain.Object{"path": "allowed.txt", "offset": 0, "limit": 3}, policy)
	if read["text"] != "éa" || read["next_offset"] != int64(3) || read["truncated"] != true || read["content_hash"] != created["content_hash"] {
		t.Fatal(read)
	}
	runtimeToolReject(t, host, workspace, AccessReadWrite, "read", domain.Object{"path": "allowed.txt", "offset": 1}, policy)
	runtimeToolReject(t, host, workspace, AccessReadWrite, "write", domain.Object{"path": "allowed.txt", "content": "replace", "expected_hash": nil}, policy)
	runtimeToolReject(t, host, workspace, AccessReadWrite, "write", domain.Object{"path": "allowed.txt", "content": "replace", "expected_hash": domain.Digest([]byte("stale"))}, policy)
	changed := runtimeToolCall(t, host, workspace, AccessReadWrite, "edit", domain.Object{"path": "allowed.txt", "old_text": "abc", "new_text": "XYZ", "expected_hash": created["content_hash"]}, policy)
	if changed["content_hash"] != domain.Digest([]byte("éXYZ")) {
		t.Fatal(changed)
	}
	runtimeToolReject(t, host, workspace, AccessReadWrite, "edit", domain.Object{"path": "allowed.txt", "old_text": "X", "new_text": "Q", "expected_hash": created["content_hash"]}, policy)
	runtimeToolReject(t, host, workspace, AccessReadWrite, "edit", domain.Object{"path": "allowed.txt", "old_text": "", "new_text": "Q", "expected_hash": changed["content_hash"]}, policy)
	data, err := os.ReadFile(filepath.Join(workspace, "allowed.txt"))
	if err != nil || string(data) != "éXYZ" {
		t.Fatalf("CAS replaced wrong bytes: %q %v", data, err)
	}
}

func TestRuntimeToolPermissionAndRevocation(t *testing.T) {
	host, workspace, binding := runtimeToolFixture(t, AccessReadOnly)
	if err := os.WriteFile(filepath.Join(workspace, "allowed.txt"), []byte("visible"), 0600); err != nil {
		t.Fatal(err)
	}
	policy := runtimeToolPolicy()
	if got := runtimeToolCall(t, host, workspace, AccessReadOnly, "read", domain.Object{"path": "allowed.txt"}, policy); got["text"] != "visible" {
		t.Fatal(got)
	}
	runtimeToolReject(t, host, workspace, AccessReadOnly, "write", domain.Object{"path": "allowed.txt", "content": "changed", "expected_hash": domain.Digest([]byte("visible"))}, policy)
	runtimeToolReject(t, host, workspace, AccessReadOnly, "read", domain.Object{"path": "../allowed.txt"}, policy)
	runtimeToolReject(t, host, workspace, AccessReadOnly, "read", domain.Object{"path": "not-allowed.txt"}, policy)
	runtimeToolReject(t, host, workspace, AccessReadOnly, "run_check", domain.Object{"path": "allowed.txt"}, policy)
	if err := host.RevokeWorkspace(binding.Ref); err != nil {
		t.Fatal(err)
	}
	runtimeToolReject(t, host, workspace, AccessReadOnly, "read", domain.Object{"path": "allowed.txt"}, policy)
}

func TestRuntimeToolRejectsUnboundAndReparsePaths(t *testing.T) {
	host, workspace, _ := runtimeToolFixture(t, AccessReadWrite)
	policy := runtimeToolPolicy()
	runtimeToolReject(t, host, t.TempDir(), AccessReadWrite, "write", domain.Object{"path": "allowed.txt", "content": "x", "expected_hash": nil}, policy)
	runtimeToolReject(t, host, workspace, AccessReadWrite, "write", domain.Object{"path": "allowed.txt", "content": strings.Repeat("x", 65), "expected_hash": nil}, policy)
	outside := filepath.Join(t.TempDir(), "outside.txt")
	if err := os.WriteFile(outside, []byte("outside"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink(outside, filepath.Join(workspace, "allowed.txt")); err == nil {
		runtimeToolReject(t, host, workspace, AccessReadWrite, "read", domain.Object{"path": "allowed.txt"}, policy)
		runtimeToolReject(t, host, workspace, AccessReadWrite, "write", domain.Object{"path": "allowed.txt", "content": "bad", "expected_hash": domain.Digest([]byte("outside"))}, policy)
	}
	data, err := os.ReadFile(outside)
	if err != nil || string(data) != "outside" {
		t.Fatalf("escaped file changed: %q %v", data, err)
	}
}
