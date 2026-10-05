//go:build windows

package host

import (
	"context"
	"errors"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"researchos.local/research-os/internal/domain"
)

func TestWorkspaceTreeReadAndContentUsePinnedRoot(t *testing.T) {
	h, workspace, binding := runtimeToolFixture(t, AccessReadWrite)
	for name, data := range map[string][]byte{
		"a.txt": []byte("é\n"), "b.txt": []byte("second"), "raw.bin": {0xff, 0x00},
	} {
		if err := os.WriteFile(filepath.Join(workspace, name), data, 0600); err != nil {
			t.Fatal(err)
		}
	}
	if err := os.Mkdir(filepath.Join(workspace, "nested"), 0700); err != nil {
		t.Fatal(err)
	}
	ctx := context.Background()
	// The domain WorkspaceBinding ref differs from the native pinned-root ref.
	workspaceRef := "wsref-domain-opaque"
	base := domain.Object{"workspace_ref": workspaceRef, "relative_path": ".", "cursor": nil, "limit": 2}
	first, err := h.WorkspaceTree(ctx, workspace, AccessReadWrite, base)
	if err != nil {
		t.Fatal(err)
	}
	items := first["entries"].([]any)
	if len(items) != 2 || first["next_cursor"] == nil || first["workspace_ref"] != workspaceRef {
		t.Fatalf("unexpected first tree page: %v", first)
	}
	second, err := h.WorkspaceTree(ctx, workspace, AccessReadWrite, domain.Object{
		"workspace_ref": workspaceRef, "relative_path": ".", "cursor": first["next_cursor"], "limit": 2})
	if err != nil || len(second["entries"].([]any)) != 2 || second["next_cursor"] != nil {
		t.Fatalf("unexpected final tree page: %v %v", second, err)
	}
	firstEntry := items[0].(domain.Object)
	if firstEntry["relative_path"] != "a.txt" || firstEntry["content_hash"] != domain.Digest([]byte("é\n")) || firstEntry["readable"] != true {
		t.Fatal(firstEntry)
	}
	read, err := h.WorkspaceRead(ctx, workspace, AccessReadWrite, domain.Object{
		"workspace_ref": workspaceRef, "relative_path": "a.txt", "max_bytes": 4})
	if err != nil || read["text"] != "é\n" || read["byte_size"] != 3 || read["editable"] != true {
		t.Fatalf("bounded UTF-8 read mismatch: %v %v", read, err)
	}
	if data, err := h.WorkspaceContent(ctx, workspace, AccessReadWrite, "raw.bin", 4); err != nil || len(data) != 2 || data[0] != 0xff {
		t.Fatalf("binary import content changed: %x %v", data, err)
	}
	if _, err := h.WorkspaceRead(ctx, workspace, AccessReadWrite, domain.Object{
		"workspace_ref": workspaceRef, "relative_path": "raw.bin", "max_bytes": 4}); err == nil || !strings.Contains(err.Error(), "UNSUPPORTED_CONTENT") {
		t.Fatalf("binary text read accepted: %v", err)
	}
	if _, err := h.WorkspaceRead(ctx, workspace, AccessReadWrite, domain.Object{
		"workspace_ref": workspaceRef, "relative_path": "a.txt", "max_bytes": 2}); err == nil || !strings.Contains(err.Error(), "CONTENT_TOO_LARGE") {
		t.Fatalf("truncated UTF-8 read accepted: %v", err)
	}
	if _, err := h.WorkspaceTree(ctx, workspace, AccessReadWrite, domain.Object{
		"workspace_ref": workspaceRef, "relative_path": ".", "cursor": first["next_cursor"], "limit": 1}); err != nil {
		t.Fatalf("same-directory cursor cannot continue with a new page size: %v", err)
	}
	if err := os.WriteFile(filepath.Join(workspace, "c.txt"), []byte("new"), 0600); err != nil {
		t.Fatal(err)
	}
	if _, err := h.WorkspaceTree(ctx, workspace, AccessReadWrite, domain.Object{
		"workspace_ref": workspaceRef, "relative_path": ".", "cursor": first["next_cursor"], "limit": 2}); err == nil || !strings.Contains(err.Error(), "CURSOR_INVALID") {
		t.Fatalf("changed directory reused a stale cursor: %v", err)
	}
	if err := h.RevokeWorkspace(binding.Ref); err != nil {
		t.Fatal(err)
	}
	if _, err := h.WorkspaceContent(ctx, workspace, AccessReadWrite, "a.txt", 4); !errors.Is(err, ErrRootRevoked) {
		t.Fatalf("revoked root still readable: %v", err)
	}
}

func TestWorkspaceDiffHeadIndexAndUntracked(t *testing.T) {
	h, workspace, _ := runtimeToolFixture(t, AccessReadWrite)
	git := func(args ...string) {
		t.Helper()
		cmd := exec.Command("git", args...)
		cmd.Dir = workspace
		if output, err := cmd.CombinedOutput(); err != nil {
			t.Fatalf("git %v: %v: %s", args, err, output)
		}
	}
	git("init", "-q")
	git("config", "user.email", "test@example.invalid")
	git("config", "user.name", "Test")
	if err := os.WriteFile(filepath.Join(workspace, "tracked.txt"), []byte("before\n"), 0600); err != nil {
		t.Fatal(err)
	}
	git("add", "tracked.txt")
	git("commit", "-qm", "baseline")
	if err := os.WriteFile(filepath.Join(workspace, "tracked.txt"), []byte("after\n"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(workspace, "new.txt"), []byte("new\n"), 0600); err != nil {
		t.Fatal(err)
	}
	request := domain.Object{"workspace_ref": "opaque", "base": "HEAD", "relative_path": nil, "max_bytes": 4096}
	result, full, err := h.WorkspaceDiff(context.Background(), workspace, AccessReadWrite, request)
	if err != nil {
		t.Fatal(err)
	}
	files := result["files"].([]any)
	if len(files) != 2 || result["total_files"] != 2 || !strings.Contains(string(full), "new.txt") || !strings.Contains(string(full), "tracked.txt") {
		t.Fatalf("unexpected HEAD diff: %v, %d bytes", result, len(full))
	}
	if files[0].(domain.Object)["status"] != "UNTRACKED" || files[1].(domain.Object)["status"] != "MODIFIED" {
		t.Fatalf("unexpected statuses: %v", files)
	}
	request["base"] = "INDEX"
	index, _, err := h.WorkspaceDiff(context.Background(), workspace, AccessReadWrite, request)
	if err != nil || index["base_revision"] == "" || index["total_files"] != 2 {
		t.Fatalf("unexpected INDEX diff: %v %v", index, err)
	}
	request["max_bytes"] = 1
	limited, all, err := h.WorkspaceDiff(context.Background(), workspace, AccessReadWrite, request)
	if err != nil || limited["truncated"] != true || len(all) == 0 {
		t.Fatalf("preview cap lost full diff: %v %d %v", limited, len(all), err)
	}
}

func TestWorkspacePathRejectsWindowsEscapes(t *testing.T) {
	for _, rel := range []string{`..\outside`, `\\server\share`, `C:\secret`, `a.txt:stream`,
		`dir/CON.txt`, `dir/LPT9`, `dir/a.`, `dir/a `, `dir/./a`, `dir//a`, `dir/a?b`} {
		if value, err := workspaceRelativePath(rel, false); err == nil {
			t.Fatalf("unsafe path %q accepted as %q", rel, value)
		}
	}
}
