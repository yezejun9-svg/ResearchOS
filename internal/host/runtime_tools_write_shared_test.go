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

	"researchos.local/research-os/internal/domain"
)

func TestRuntimeToolWritesUseSharedDurableIntentAndReplay(t *testing.T) {
	h, workspace, _ := runtimeToolFixture(t, AccessReadWrite)
	policy := runtimeToolPolicy()
	initial := []byte("old abc")
	if err := os.WriteFile(filepath.Join(workspace, "allowed.txt"), initial, 0o600); err != nil {
		t.Fatal(err)
	}
	write := runtimeToolTestRequest(workspace, AccessReadWrite, "write", domain.Object{
		"path": "allowed.txt", "content": "new abc", "expected_hash": domain.Digest(initial)}, policy)
	write.IntentKey = "runtime-tool/shared-write-effect"
	first, err := h.ExecuteRuntimeTool(context.Background(), write)
	if err != nil || first["details"] == nil {
		t.Fatalf("write: %v %v", first, err)
	}
	keyHash := strings.TrimPrefix(writeHash([]byte(write.IntentKey)), "sha256:")
	intentPath := filepath.Join(h.dir, "workspace-writes", "intents", "intent-"+keyHash+".json")
	raw, err := os.ReadFile(intentPath)
	if err != nil {
		t.Fatalf("shared journal intent missing: %v", err)
	}
	var intent workspaceWriteIntent
	if err := json.Unmarshal(raw, &intent); err != nil || intent.State != "APPLIED" || intent.ExpectedHash != domain.Digest(initial) || intent.AfterHash != domain.Digest([]byte("new abc")) {
		t.Fatalf("durable intent: %+v %v", intent, err)
	}
	if old, err := os.ReadFile(intent.PreimagePath); err != nil || string(old) != string(initial) {
		t.Fatalf("private preimage: %q %v", old, err)
	}
	if old, err := os.ReadFile(intent.BackupPath); err != nil || string(old) != string(initial) {
		t.Fatalf("native replace backup: %q %v", old, err)
	}
	if _, err := h.ExecuteRuntimeTool(context.Background(), write); err != nil {
		t.Fatalf("same effect key must observe applied proof: %v", err)
	}
	edit := runtimeToolTestRequest(workspace, AccessReadWrite, "edit", domain.Object{
		"path": "allowed.txt", "old_text": "abc", "new_text": "xyz", "expected_hash": domain.Digest([]byte("new abc"))}, policy)
	edit.IntentKey = "runtime-tool/shared-edit-effect"
	if _, err := h.ExecuteRuntimeTool(context.Background(), edit); err != nil {
		t.Fatalf("edit: %v", err)
	}
	if _, err := h.ExecuteRuntimeTool(context.Background(), edit); err != nil {
		t.Fatalf("edit replay must reconstruct from private preimage: %v", err)
	}
	if actual, err := os.ReadFile(filepath.Join(workspace, "allowed.txt")); err != nil || string(actual) != "new xyz" {
		t.Fatalf("edit result: %q %v", actual, err)
	}
}

func TestRuntimeToolExternalRaceStaysUnknownAndKeepsBothImages(t *testing.T) {
	h, workspace, _ := runtimeToolFixture(t, AccessReadWrite)
	target := filepath.Join(workspace, "allowed.txt")
	if err := os.WriteFile(target, []byte("before"), 0o600); err != nil {
		t.Fatal(err)
	}
	request := runtimeToolTestRequest(workspace, AccessReadWrite, "write", domain.Object{
		"path": "allowed.txt", "content": "candidate", "expected_hash": domain.Digest([]byte("before"))}, runtimeToolPolicy())
	request.IntentKey = "runtime-tool/external-race-effect"
	workspaceWriteBeforePublish = func(path string) error {
		if err := os.Rename(path, path+".external-old"); err != nil {
			return err
		}
		return os.WriteFile(path, []byte("external writer"), 0o600)
	}
	t.Cleanup(func() { workspaceWriteBeforePublish = nil })
	_, err := h.ExecuteRuntimeTool(context.Background(), request)
	var failure *domain.RuntimeToolFailure
	if errors.As(err, &failure) && failure.Outcome == "NOT_APPLIED" {
		t.Fatalf("external write race was downgraded to NOT_APPLIED: %v", err)
	}
	var writeErr *WorkspaceWriteError
	if !errors.As(err, &writeErr) || writeErr.Code != "EXTERNAL_WRITE_RACE" || writeErr.Outcome != "UNKNOWN" {
		t.Fatalf("external race must remain UNKNOWN: %v", err)
	}
	keyHash := strings.TrimPrefix(writeHash([]byte(request.IntentKey)), "sha256:")
	raw, err := os.ReadFile(filepath.Join(h.dir, "workspace-writes", "intents", "intent-"+keyHash+".json"))
	if err != nil {
		t.Fatal(err)
	}
	var intent workspaceWriteIntent
	if err := json.Unmarshal(raw, &intent); err != nil || intent.State != "EXTERNAL_RACE" {
		t.Fatalf("race intent: %+v %v", intent, err)
	}
	if b, err := os.ReadFile(intent.CandidatePath); err != nil || string(b) != "candidate" {
		t.Fatalf("candidate lost: %q %v", b, err)
	}
	if b, err := os.ReadFile(intent.BackupPath); err != nil || string(b) != "external writer" {
		t.Fatalf("external image lost: %q %v", b, err)
	}
	workspaceWriteBeforePublish = nil
	_, err = h.ExecuteRuntimeTool(context.Background(), request)
	if !errors.As(err, &writeErr) || writeErr.Code != "WRITE_RECOVERY_REQUIRED" || writeErr.Outcome != "UNKNOWN" {
		t.Fatalf("same unknown intent retried or reclassified: %v", err)
	}
}

func TestRuntimeToolWriteRequiresEffectIdentityAndRevalidation(t *testing.T) {
	h, workspace, _ := runtimeToolFixture(t, AccessReadWrite)
	request := runtimeToolTestRequest(workspace, AccessReadWrite, "write", domain.Object{
		"path": "allowed.txt", "content": "secret", "expected_hash": nil}, runtimeToolPolicy())
	request.IntentKey = ""
	_, err := h.ExecuteRuntimeTool(context.Background(), request)
	var failure *domain.RuntimeToolFailure
	if !errors.As(err, &failure) || failure.Outcome != "NOT_APPLIED" {
		t.Fatalf("missing effect key must refuse before mutation: %v", err)
	}
	request.IntentKey = "runtime-tool/identity-required"
	request.Revalidate = nil
	_, err = h.ExecuteRuntimeTool(context.Background(), request)
	if !errors.As(err, &failure) || failure.Outcome != "NOT_APPLIED" {
		t.Fatalf("missing current authority must refuse before mutation: %v", err)
	}
	if _, err := os.Stat(filepath.Join(workspace, "allowed.txt")); !errors.Is(err, os.ErrNotExist) {
		t.Fatalf("refused write created target: %v", err)
	}
}

func TestRuntimeToolSameEffectKeyDifferentPolicyScopeConflicts(t *testing.T) {
	h, workspace, _ := runtimeToolFixture(t, AccessReadWrite)
	request := runtimeToolTestRequest(workspace, AccessReadWrite, "write", domain.Object{
		"path": "allowed.txt", "content": "same bytes", "expected_hash": nil}, runtimeToolPolicy())
	request.IntentKey = "runtime-tool/fixed-effect-key"
	if _, err := h.ExecuteRuntimeTool(context.Background(), request); err != nil {
		t.Fatalf("first effect: %v", err)
	}
	changed := request
	changed.Policy = runtimeToolPolicy()
	changed.Policy["max_read_bytes"] = int64(9)
	_, err := h.ExecuteRuntimeTool(context.Background(), changed)
	var writeErr *WorkspaceWriteError
	if !errors.As(err, &writeErr) || writeErr.Code != "COMMAND_ID_CONFLICT" || writeErr.Outcome != "NOT_APPLIED" {
		t.Fatalf("same effect key with different frozen policy reused intent: %v", err)
	}
}

func TestRuntimeToolRevokedAfterIntentIsUnknown(t *testing.T) {
	h, workspace, _ := runtimeToolFixture(t, AccessReadWrite)
	target := filepath.Join(workspace, "allowed.txt")
	if err := os.WriteFile(target, []byte("before"), 0o600); err != nil {
		t.Fatal(err)
	}
	request := runtimeToolTestRequest(workspace, AccessReadWrite, "write", domain.Object{
		"path": "allowed.txt", "content": "after", "expected_hash": domain.Digest([]byte("before"))}, runtimeToolPolicy())
	request.IntentKey = "runtime-tool/revoked-after-intent"
	revoked := false
	request.Revalidate = func(context.Context) error {
		if revoked {
			return errors.New("runtime lease revoked")
		}
		return nil
	}
	workspaceWriteBeforePublish = func(string) error { revoked = true; return nil }
	t.Cleanup(func() { workspaceWriteBeforePublish = nil })
	_, err := h.ExecuteRuntimeTool(context.Background(), request)
	var failure *domain.RuntimeToolFailure
	if errors.As(err, &failure) && failure.Outcome == "NOT_APPLIED" {
		t.Fatalf("durable pending intent downgraded to NOT_APPLIED: %v", err)
	}
	var writeErr *WorkspaceWriteError
	if !errors.As(err, &writeErr) || writeErr.Outcome != "UNKNOWN" || writeErr.Code != "WRITE_RECOVERY_REQUIRED" {
		t.Fatalf("revocation after pending must be UNKNOWN: %v", err)
	}
	if actual, err := os.ReadFile(target); err != nil || string(actual) != "before" {
		t.Fatalf("revoked target changed: %q %v", actual, err)
	}
}
