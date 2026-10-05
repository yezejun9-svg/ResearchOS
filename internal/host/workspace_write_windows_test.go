//go:build windows

package host

import (
	"context"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"testing"

	"golang.org/x/sys/windows"
)

func writeFixture(t *testing.T) (*os.Root, string, string) {
	t.Helper()
	base := t.TempDir()
	workspace := filepath.Join(base, "workspace")
	journal := filepath.Join(base, "journal")
	if err := os.MkdirAll(workspace, 0o700); err != nil {
		t.Fatal(err)
	}
	root, err := os.OpenRoot(workspace)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { root.Close() })
	return root, workspace, journal
}

func writeInput(root *os.Root, rootPath, journal, rel, key string, expected *string, content string) WorkspaceWriteInput {
	return WorkspaceWriteInput{Root: root, RootPath: rootPath, JournalRoot: journal, RelativePath: rel,
		IntentKey: key, ExpectedHash: expected, CreateIfMissing: expected == nil, Content: []byte(content),
		Revalidate: func(context.Context) error { return nil }}
}

func writeErrorCode(t *testing.T, err error, code, outcome string) {
	t.Helper()
	var classified *WorkspaceWriteError
	if !errors.As(err, &classified) || classified.Code != code || classified.Outcome != outcome {
		t.Fatalf("wanted %s/%s, got %v", code, outcome, err)
	}
}

func TestWorkspaceWriteExistingCreateAndIntentReplay(t *testing.T) {
	root, rootPath, journal := writeFixture(t)
	if err := os.WriteFile(filepath.Join(rootPath, "file.txt"), []byte("original"), 0o600); err != nil {
		t.Fatal(err)
	}
	expected := writeHash([]byte("original"))
	input := writeInput(root, rootPath, journal, "file.txt", "project/session/command-1", &expected, "candidate")
	result, err := WriteWorkspaceFile(context.Background(), input)
	if err != nil || !result.Applied || result.State != "APPLIED" {
		t.Fatalf("physical replace failed: %+v %v", result, err)
	}
	before, err := os.ReadFile(result.PreimagePath)
	if err != nil || string(before) != "original" {
		t.Fatalf("original private preimage: %q %v", before, err)
	}
	actualBackup, err := os.ReadFile(result.BackupPath)
	if err != nil || string(actualBackup) != "original" {
		t.Fatalf("ReplaceFile backup: %q %v", actualBackup, err)
	}
	actual, err := os.ReadFile(filepath.Join(rootPath, "file.txt"))
	if err != nil || string(actual) != "candidate" {
		t.Fatalf("published candidate: %q %v", actual, err)
	}
	replayed, err := WriteWorkspaceFile(context.Background(), input)
	if err != nil || !replayed.Applied || replayed.IntentPath != result.IntentPath {
		t.Fatalf("same intent replay must observe original write: %+v %v", replayed, err)
	}
	wrong := input
	wrong.Content = []byte("different")
	_, err = WriteWorkspaceFile(context.Background(), wrong)
	writeErrorCode(t, err, "INTENT_KEY_CONFLICT", "NOT_APPLIED")
	stale := writeInput(root, rootPath, journal, "file.txt", "project/session/command-stale", &expected, "bad")
	_, err = WriteWorkspaceFile(context.Background(), stale)
	writeErrorCode(t, err, "CONTENT_CONFLICT", "NOT_APPLIED")
	created := writeInput(root, rootPath, journal, "new.txt", "project/session/create", nil, "new bytes")
	createdResult, err := WriteWorkspaceFile(context.Background(), created)
	if err != nil || !createdResult.Applied || createdResult.BeforeHash != "" {
		t.Fatalf("create only missing: %+v %v", createdResult, err)
	}
	if _, err := os.Stat(createdResult.IntentPath); err != nil {
		t.Fatalf("create intent missing: %v", err)
	}
	var createIntent workspaceWriteIntent
	rawCreate, err := os.ReadFile(createdResult.IntentPath)
	if err != nil || json.Unmarshal(rawCreate, &createIntent) != nil {
		t.Fatalf("create intent unreadable: %v", err)
	}
	if _, err := os.Lstat(createIntent.StagePath); !errors.Is(err, os.ErrNotExist) {
		t.Fatalf("staging hardlink remained after create: %v", err)
	}
	_, err = WriteWorkspaceFile(context.Background(), created)
	if err != nil {
		t.Fatalf("create replay should not recreate: %v", err)
	}
	otherCreate := created
	otherCreate.IntentKey = "project/session/second-create"
	_, err = WriteWorkspaceFile(context.Background(), otherCreate)
	writeErrorCode(t, err, "CONTENT_CONFLICT", "NOT_APPLIED")
}

func TestWorkspaceWriteExternalRenameRacePreservesBothImages(t *testing.T) {
	root, rootPath, journal := writeFixture(t)
	target := filepath.Join(rootPath, "race.txt")
	if err := os.WriteFile(target, []byte("expected image"), 0o600); err != nil {
		t.Fatal(err)
	}
	expected := writeHash([]byte("expected image"))
	input := writeInput(root, rootPath, journal, "race.txt", "project/session/race", &expected, "our candidate")
	workspaceWriteBeforePublish = func(path string) error {
		if err := os.Rename(path, path+".external-old"); err != nil {
			return err
		}
		return os.WriteFile(path, []byte("external editor image"), 0o600)
	}
	t.Cleanup(func() { workspaceWriteBeforePublish = nil })
	result, err := WriteWorkspaceFile(context.Background(), input)
	writeErrorCode(t, err, "EXTERNAL_WRITE_RACE", "UNKNOWN")
	if result.State != "EXTERNAL_RACE" || result.Applied {
		t.Fatalf("race must not claim applied: %+v", result)
	}
	backup, err := os.ReadFile(result.BackupPath)
	if err != nil || string(backup) != "external editor image" {
		t.Fatalf("actual external file must survive: %q %v", backup, err)
	}
	candidate, err := os.ReadFile(result.CandidatePath)
	if err != nil || string(candidate) != "our candidate" {
		t.Fatalf("content-addressed candidate must survive: %q %v", candidate, err)
	}
	preimage, err := os.ReadFile(result.PreimagePath)
	if err != nil || string(preimage) != "expected image" {
		t.Fatalf("first preimage must survive: %q %v", preimage, err)
	}
	raw, err := os.ReadFile(result.IntentPath)
	if err != nil {
		t.Fatal(err)
	}
	var intent workspaceWriteIntent
	if err := json.Unmarshal(raw, &intent); err != nil || intent.State != "EXTERNAL_RACE" || intent.ActualBefore != writeHash(backup) {
		t.Fatalf("durable race receipt: %+v %v", intent, err)
	}
	_, err = WriteWorkspaceFile(context.Background(), input)
	writeErrorCode(t, err, "WRITE_RECOVERY_REQUIRED", "UNKNOWN")
}

func TestWorkspaceWritePendingCannotBeReplayedOrRetried(t *testing.T) {
	root, rootPath, journal := writeFixture(t)
	target := filepath.Join(rootPath, "pending.txt")
	if err := os.WriteFile(target, []byte("before"), 0o600); err != nil {
		t.Fatal(err)
	}
	expected := writeHash([]byte("before"))
	input := writeInput(root, rootPath, journal, "pending.txt", "project/session/pending", &expected, "after")
	calls := 0
	workspaceWriteBeforePublish = func(string) error {
		calls++
		return errors.New("stopped after durable intent, before publication")
	}
	t.Cleanup(func() { workspaceWriteBeforePublish = nil })
	first, err := WriteWorkspaceFile(context.Background(), input)
	writeErrorCode(t, err, "WRITE_RECOVERY_REQUIRED", "UNKNOWN")
	if first.State != "PENDING" || first.Applied || calls != 1 {
		t.Fatalf("first attempt incorrectly claimed publication: %+v calls=%d", first, calls)
	}
	second, err := WriteWorkspaceFile(context.Background(), input)
	writeErrorCode(t, err, "WRITE_RECOVERY_REQUIRED", "UNKNOWN")
	if second.IntentPath != first.IntentPath || calls != 1 {
		t.Fatalf("pending intent was retried: %+v calls=%d", second, calls)
	}
	if got, err := os.ReadFile(target); err != nil || string(got) != "before" {
		t.Fatalf("pending target changed: %q %v", got, err)
	}
}

func TestWorkspaceWriteReplayDetectsMissingAppliedTarget(t *testing.T) {
	root, rootPath, journal := writeFixture(t)
	input := writeInput(root, rootPath, journal, "removed.txt", "project/session/removed", nil, "published")
	result, err := WriteWorkspaceFile(context.Background(), input)
	if err != nil || !result.Applied {
		t.Fatalf("create: %+v %v", result, err)
	}
	if err := os.Remove(filepath.Join(rootPath, "removed.txt")); err != nil {
		t.Fatal(err)
	}
	replay, err := WriteWorkspaceFile(context.Background(), input)
	writeErrorCode(t, err, "EXTERNAL_WRITE_RACE", "UNKNOWN")
	if replay.IntentPath != result.IntentPath || !replay.Applied {
		t.Fatalf("lost original applied proof: %+v", replay)
	}
	if _, err := os.Stat(filepath.Join(rootPath, "removed.txt")); !errors.Is(err, os.ErrNotExist) {
		t.Fatalf("replay recreated missing target: %v", err)
	}
}

func TestWorkspaceWriteOpenExternalWriterFailsBeforeIntent(t *testing.T) {
	root, rootPath, journal := writeFixture(t)
	target := filepath.Join(rootPath, "editor.txt")
	if err := os.WriteFile(target, []byte("before"), 0o600); err != nil {
		t.Fatal(err)
	}
	wide, err := windows.UTF16PtrFromString(target)
	if err != nil {
		t.Fatal(err)
	}
	writer, err := windows.CreateFile(wide, windows.GENERIC_WRITE, windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE|windows.FILE_SHARE_DELETE,
		nil, windows.OPEN_EXISTING, windows.FILE_ATTRIBUTE_NORMAL, 0)
	if err != nil {
		t.Fatal(err)
	}
	defer windows.CloseHandle(writer)
	expected := writeHash([]byte("before"))
	input := writeInput(root, rootPath, journal, "editor.txt", "project/session/editor", &expected, "after")
	_, err = WriteWorkspaceFile(context.Background(), input)
	writeErrorCode(t, err, "EXTERNAL_WRITE_RACE", "NOT_APPLIED")
	if got, err := os.ReadFile(target); err != nil || string(got) != "before" {
		t.Fatalf("external writer target changed: %q %v", got, err)
	}
}

func TestWorkspaceWriteCreateRaceKeepsExternalFile(t *testing.T) {
	root, rootPath, journal := writeFixture(t)
	target := filepath.Join(rootPath, "new-race.txt")
	input := writeInput(root, rootPath, journal, "new-race.txt", "project/session/create-race", nil, "our candidate")
	workspaceWriteBeforePublish = func(string) error { return os.WriteFile(target, []byte("external creator"), 0o600) }
	t.Cleanup(func() { workspaceWriteBeforePublish = nil })
	result, err := WriteWorkspaceFile(context.Background(), input)
	writeErrorCode(t, err, "CONTENT_CONFLICT", "NOT_APPLIED")
	if result.State != "CONFLICT" || result.Applied {
		t.Fatalf("create race claimed publication: %+v", result)
	}
	if got, err := os.ReadFile(target); err != nil || string(got) != "external creator" {
		t.Fatalf("external creator bytes lost: %q %v", got, err)
	}
	if got, err := os.ReadFile(result.CandidatePath); err != nil || string(got) != "our candidate" {
		t.Fatalf("candidate missing: %q %v", got, err)
	}
	_, err = WriteWorkspaceFile(context.Background(), input)
	writeErrorCode(t, err, "WRITE_RECOVERY_REQUIRED", "UNKNOWN")
}

func TestWorkspaceWriteRevocationBeforePublishKeepsTarget(t *testing.T) {
	root, rootPath, journal := writeFixture(t)
	target := filepath.Join(rootPath, "revoke.txt")
	if err := os.WriteFile(target, []byte("before"), 0o600); err != nil {
		t.Fatal(err)
	}
	expected := writeHash([]byte("before"))
	input := writeInput(root, rootPath, journal, "revoke.txt", "project/session/revoke", &expected, "after")
	revoked := false
	input.Revalidate = func(context.Context) error {
		if revoked {
			return errors.New("revoked")
		}
		return nil
	}
	workspaceWriteBeforePublish = func(string) error { revoked = true; return nil }
	t.Cleanup(func() { workspaceWriteBeforePublish = nil })
	result, err := WriteWorkspaceFile(context.Background(), input)
	writeErrorCode(t, err, "WRITE_RECOVERY_REQUIRED", "UNKNOWN")
	if result.State != "PENDING" || result.Applied {
		t.Fatalf("revoked write claimed publication: %+v", result)
	}
	if got, err := os.ReadFile(target); err != nil || string(got) != "before" {
		t.Fatalf("revoked target changed: %q %v", got, err)
	}
}
