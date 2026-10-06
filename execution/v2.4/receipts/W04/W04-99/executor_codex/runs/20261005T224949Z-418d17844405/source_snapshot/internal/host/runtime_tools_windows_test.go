//go:build windows

package host

import (
	"context"
	"encoding/json"
	"errors"
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
	return &Host{roots: registry, dir: filepath.Join(base, "host")}, workspace, binding
}

func runtimeToolTestRequest(workspace, access, name string, args, policy domain.Object) domain.RuntimeToolRequest {
	return domain.RuntimeToolRequest{WorkspacePath: workspace, Access: access, Name: name, Arguments: args, Policy: policy,
		IntentKey:  "test/" + domain.Hash(domain.Object{"workspace": workspace, "name": name, "arguments": args}),
		Revalidate: func(context.Context) error { return nil }}
}

func runtimeToolPolicy() domain.Object {
	return domain.Object{"read_paths": []any{"allowed.txt"}, "write_paths": []any{"allowed.txt"}, "max_read_bytes": 8, "max_write_bytes": 64}
}

func runtimeToolCall(t *testing.T, host *Host, workspace, access, name string, args, policy domain.Object) domain.Object {
	t.Helper()
	result, err := host.ExecuteRuntimeTool(context.Background(), runtimeToolTestRequest(workspace, access, name, args, policy))
	if err != nil {
		t.Fatal(err)
	}
	if result["details"] == nil || len(result["content"].([]any)) != 1 {
		t.Fatalf("invalid tool reply: %v", result)
	}
	if name == "read" {
		if _, duplicated := result["details"].(map[string]any)["text"]; duplicated {
			t.Fatal("read text duplicated in details")
		}
		var visible domain.Object
		part := result["content"].([]any)[0].(domain.Object)
		if err := json.Unmarshal([]byte(part["text"].(string)), &visible); err != nil {
			t.Fatal(err)
		}
		return visible
	}
	return result["details"].(map[string]any)
}

func runtimeToolReject(t *testing.T, host *Host, workspace, access, name string, args, policy domain.Object) {
	t.Helper()
	if result, err := host.ExecuteRuntimeTool(context.Background(), runtimeToolTestRequest(workspace, access, name, args, policy)); err == nil {
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
	if read["text"] != "éa" || read["next_offset"] != float64(3) || read["truncated"] != true || read["content_hash"] != created["content_hash"] {
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

func TestRuntimeToolFailureOutcomeAtHostBoundary(t *testing.T) {
	host, workspace, _ := runtimeToolFixture(t, AccessReadWrite)
	policy := runtimeToolPolicy()
	for _, tc := range []struct {
		name string
		args domain.Object
	}{
		{"read", domain.Object{"path": "allowed.txt"}}, // Missing file has no effect.
		{"write", domain.Object{"path": "forbidden.txt", "content": "x", "expected_hash": nil}},
	} {
		_, err := host.ExecuteRuntimeTool(context.Background(), runtimeToolTestRequest(workspace, AccessReadWrite, tc.name, tc.args, policy))
		var failure *domain.RuntimeToolFailure
		if !errors.As(err, &failure) || failure.Outcome != "NOT_APPLIED" {
			t.Fatalf("%s: expected NOT_APPLIED host witness, got %v", tc.name, err)
		}
	}
	if err := os.WriteFile(filepath.Join(workspace, "allowed.txt"), []byte("old"), 0600); err != nil {
		t.Fatal(err)
	}
	_, err := host.ExecuteRuntimeTool(context.Background(), runtimeToolTestRequest(workspace, AccessReadWrite, "write", domain.Object{"path": "allowed.txt", "content": "new", "expected_hash": domain.Digest([]byte("stale"))}, policy))
	var failure *domain.RuntimeToolFailure
	if !errors.As(err, &failure) || failure.Outcome != "NOT_APPLIED" {
		t.Fatalf("stale CAS should be NOT_APPLIED, got %v", err)
	}
	if data, err := os.ReadFile(filepath.Join(workspace, "allowed.txt")); err != nil || string(data) != "old" {
		t.Fatalf("stale CAS modified target: %q %v", data, err)
	}
}

func TestRuntimeToolReadPagesEncodedTextWithinBridgeFrame(t *testing.T) {
	for _, tc := range []struct {
		name, text string
	}{
		{"multibyte", strings.Repeat("中文", 17000)},
		{"escaped", strings.Repeat("\"\\\n<>&", 16000)},
	} {
		t.Run(tc.name, func(t *testing.T) {
			host, workspace, _ := runtimeToolFixture(t, AccessReadWrite)
			data := []byte(tc.text)
			if err := os.WriteFile(filepath.Join(workspace, "allowed.txt"), data, 0600); err != nil {
				t.Fatal(err)
			}
			policy := runtimeToolPolicy()
			policy["max_read_bytes"] = 65536
			var offset int64
			var got strings.Builder
			for page := 0; page < 20; page++ {
				reply, err := host.ExecuteRuntimeTool(context.Background(), domain.RuntimeToolRequest{WorkspacePath: workspace, Access: AccessReadWrite, Name: "read", Arguments: domain.Object{"path": "allowed.txt", "offset": offset}, Policy: policy})
				if err != nil {
					t.Fatal(err)
				}
				if len(domain.Bytes(reply)) > runtimeToolReplyLimit {
					t.Fatalf("payload exceeds read frame budget: %d", len(domain.Bytes(reply)))
				}
				frame := domain.Object{"sequence": 123, "key": "task:run:1:tool:1", "state": "CONFIRMED", "payload": reply}
				if len(domain.Bytes(frame)) > 64<<10 {
					t.Fatalf("reply exceeds actual bridge frame: %d", len(domain.Bytes(frame)))
				}
				metadata := reply["details"].(domain.Object)
				if _, duplicate := metadata["text"]; duplicate {
					t.Fatal("read text duplicated in details")
				}
				part := reply["content"].([]any)[0].(domain.Object)
				var visible domain.Object
				if err := json.Unmarshal([]byte(part["text"].(string)), &visible); err != nil {
					t.Fatal(err)
				}
				next := int64(visible["next_offset"].(float64))
				if visible["content_hash"] != domain.Digest(data) || visible["text"] == nil || next != metadata["next_offset"] {
					t.Fatalf("page metadata mismatch: %v", visible)
				}
				got.WriteString(visible["text"].(string))
				if next <= offset || next > int64(len(data)) {
					t.Fatalf("page did not advance: %d -> %d", offset, next)
				}
				offset = next
				if visible["truncated"] == false {
					if got.String() != tc.text || offset != int64(len(data)) {
						t.Fatalf("paginated bytes differ: got %d, want %d", got.Len(), len(data))
					}
					return
				}
			}
			t.Fatal("read did not finish pagination")
		})
	}
}
