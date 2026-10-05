//go:build windows

package host

// Physical workspace writes shared by the CLI, Desktop and worker entrypoints.
// Caller authorization is revalidated under the path lock; this component owns
// the durable file intent and the Windows compare/replace evidence. In
// particular, a second hash before Rename is not a compare-and-swap.

import (
	"context"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path"
	"path/filepath"
	"runtime"
	"strings"
	"time"
	"unsafe"

	"golang.org/x/sys/windows"
)

const workspaceWriteLimit = 4 << 20 // protocol text is at most 1 Mi Unicode code points

type WorkspaceWriteInput struct {
	Root            *os.Root
	RootPath        string
	JournalRoot     string
	RelativePath    string
	IntentKey       string
	ScopeHash       string
	ExpectedHash    *string
	CreateIfMissing bool
	Content         []byte
	// Revalidate must check the current root binding, caller authority and
	// write scope. It is called again after native directory guards are held.
	Revalidate func(context.Context) error
}

type WorkspaceWriteResult struct {
	BeforeHash    string
	AfterHash     string
	CandidatePath string
	PreimagePath  string
	BackupPath    string
	IntentPath    string
	State         string
	Applied       bool
}

// Outcome is NOT_APPLIED only when no workspace target publication was tried.
// UNKNOWN includes ReplaceFileW's documented partial-failure cases. The caller
// must not turn an UNKNOWN into an ordinary retry with a new intent key.
type WorkspaceWriteError struct {
	Code    string
	Outcome string
	Cause   error
}

func (e *WorkspaceWriteError) Error() string {
	if e.Cause == nil {
		return e.Code
	}
	return e.Code + ": " + e.Cause.Error()
}
func (e *WorkspaceWriteError) Unwrap() error { return e.Cause }

type workspaceWriteIntent struct {
	Version       int    `json:"version"`
	KeyHash       string `json:"key_hash"`
	BodyHash      string `json:"body_hash"`
	ScopeHash     string `json:"scope_hash,omitempty"`
	RootIdentity  string `json:"root_identity"`
	RelativePath  string `json:"relative_path"`
	ExpectedHash  string `json:"expected_hash,omitempty"`
	AfterHash     string `json:"after_hash"`
	Create        bool   `json:"create"`
	CandidatePath string `json:"candidate_path"`
	PreimagePath  string `json:"preimage_path,omitempty"`
	BackupPath    string `json:"backup_path,omitempty"`
	StagePath     string `json:"stage_path"`
	State         string `json:"state"`
	ActualBefore  string `json:"actual_before_hash,omitempty"`
	ObservedAfter string `json:"observed_after_hash,omitempty"`
	LastError     string `json:"last_error,omitempty"`
}

var replaceFileProc = windows.NewLazySystemDLL("kernel32.dll").NewProc("ReplaceFileW")

// workspaceWriteBeforePublish is a deterministic test seam. Production leaves
// it nil. A test can run an unconstrained external editor in this exact gap.
var workspaceWriteBeforePublish func(string) error

func writeError(code, outcome string, cause error) error {
	return &WorkspaceWriteError{Code: code, Outcome: outcome, Cause: cause}
}

func writeHash(data []byte) string {
	sum := sha256.Sum256(data)
	return "sha256:" + hex.EncodeToString(sum[:])
}

func writeNonce() (string, error) {
	var nonce [16]byte
	if _, err := rand.Read(nonce[:]); err != nil {
		return "", err
	}
	return hex.EncodeToString(nonce[:]), nil
}

func validWriteHash(s string) bool {
	if len(s) != 71 || !strings.HasPrefix(s, "sha256:") {
		return false
	}
	_, err := hex.DecodeString(s[7:])
	return err == nil && s == strings.ToLower(s)
}

func validateWorkspaceWrite(in WorkspaceWriteInput) (string, error) {
	if in.Root == nil || in.Revalidate == nil || in.IntentKey == "" || len(in.IntentKey) > 1024 {
		return "", writeError("INVALID_REQUEST", "NOT_APPLIED", errors.New("root, authorization callback and bounded intent key required"))
	}
	if in.ScopeHash != "" && !validWriteHash(in.ScopeHash) {
		return "", writeError("INVALID_REQUEST", "NOT_APPLIED", errors.New("scope hash must be sha256 digest"))
	}
	if in.CreateIfMissing != (in.ExpectedHash == nil) || in.ExpectedHash != nil && !validWriteHash(*in.ExpectedHash) {
		return "", writeError("INVALID_REQUEST", "NOT_APPLIED", errors.New("create/expected hash contract mismatch"))
	}
	if len(in.Content) > workspaceWriteLimit {
		return "", writeError("CONTENT_TOO_LARGE", "NOT_APPLIED", errors.New("write exceeds 4 MiB byte boundary"))
	}
	if err := CheckRelativePath(in.RelativePath); err != nil || in.RelativePath != NormalizeRelative(in.RelativePath) || path.Clean(in.RelativePath) != in.RelativePath || strings.Contains(in.RelativePath, "\\") {
		return "", writeError("PATH_OUT_OF_SCOPE", "NOT_APPLIED", errors.New("canonical relative path required"))
	}
	for _, part := range strings.Split(in.RelativePath, "/") {
		if part == "" || part == "." || part == ".." || strings.TrimRight(part, " .") != part || strings.Contains(part, ":") {
			return "", writeError("PATH_OUT_OF_SCOPE", "NOT_APPLIED", errors.New("unsafe Windows path component"))
		}
	}
	rootPath, err := filepath.Abs(in.RootPath)
	if err != nil || !strings.EqualFold(filepath.Clean(rootPath), filepath.Clean(in.Root.Name())) || !localWindowsPath(rootPath) {
		return "", writeError("PATH_OUT_OF_SCOPE", "NOT_APPLIED", errors.New("root handle and local path mismatch"))
	}
	journal, err := filepath.Abs(in.JournalRoot)
	if err != nil || !localWindowsPath(journal) {
		return "", writeError("INVALID_REQUEST", "NOT_APPLIED", errors.New("trusted local journal required"))
	}
	return rootPath, nil
}

func localWindowsPath(p string) bool {
	return len(filepath.VolumeName(p)) == 2 && filepath.VolumeName(p)[1] == ':' &&
		!strings.HasPrefix(p, `\\`) && !strings.HasPrefix(p, `\\?\`) && filepath.IsAbs(p)
}

func writeJournalDirs(root string) (string, error) {
	if reparse, err := chainHasReparsePoint(root); err != nil || reparse {
		return "", fmt.Errorf("journal path reparse check: %v", err)
	}
	dir := filepath.Join(root, "workspace-writes")
	for _, p := range []string{root, dir, filepath.Join(dir, "locks"), filepath.Join(dir, "candidates"), filepath.Join(dir, "preimages"), filepath.Join(dir, "intents")} {
		if err := os.MkdirAll(p, 0o700); err != nil {
			return "", err
		}
		if reparse, err := chainHasReparsePoint(p); err != nil || reparse {
			return "", fmt.Errorf("journal directory reparse check: %v", err)
		}
		if err := privateDir(p); err != nil {
			return "", err
		}
	}
	return dir, nil
}

func lockWorkspaceWrite(ctx context.Context, p string) (func(), error) {
	f, err := os.OpenFile(p, os.O_CREATE|os.O_RDWR, 0o600)
	if err != nil {
		return nil, err
	}
	if err := privateFile(p); err != nil {
		f.Close()
		return nil, err
	}
	h := windows.Handle(f.Fd())
	var overlapped windows.Overlapped
	for {
		if err := ctx.Err(); err != nil {
			f.Close()
			return nil, err
		}
		err = windows.LockFileEx(h, windows.LOCKFILE_EXCLUSIVE_LOCK|windows.LOCKFILE_FAIL_IMMEDIATELY, 0, 1, 0, &overlapped)
		if err == nil {
			return func() { _ = windows.UnlockFileEx(h, 0, 1, 0, &overlapped); _ = f.Close() }, nil
		}
		if !errors.Is(err, windows.ERROR_LOCK_VIOLATION) {
			f.Close()
			return nil, err
		}
		time.Sleep(15 * time.Millisecond)
	}
}

func writeImmutablePrivate(dir, name string, content []byte) (string, error) {
	p := filepath.Join(dir, name)
	if old, err := os.ReadFile(p); err == nil {
		if writeHash(old) != writeHash(content) {
			return "", errors.New("immutable journal bytes differ")
		}
		return p, nil
	} else if !errors.Is(err, os.ErrNotExist) {
		return "", err
	}
	tmp, err := os.CreateTemp(dir, name+".tmp-")
	if err != nil {
		return "", err
	}
	defer os.Remove(tmp.Name())
	if _, err = tmp.Write(content); err != nil {
		tmp.Close()
		return "", err
	}
	if err = tmp.Sync(); err != nil {
		tmp.Close()
		return "", err
	}
	if err = tmp.Close(); err != nil {
		return "", err
	}
	if err = privateFile(tmp.Name()); err != nil {
		return "", err
	}
	from, err := windows.UTF16PtrFromString(tmp.Name())
	if err != nil {
		return "", err
	}
	to, err := windows.UTF16PtrFromString(p)
	if err != nil {
		return "", err
	}
	if err = windows.MoveFileEx(from, to, windows.MOVEFILE_WRITE_THROUGH); err != nil {
		old, readErr := os.ReadFile(p)
		if readErr != nil || writeHash(old) != writeHash(content) {
			return "", err
		}
	}
	return p, nil
}

func persistWorkspaceIntent(dir, name string, v workspaceWriteIntent) error {
	raw, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return err
	}
	tmp, err := os.CreateTemp(dir, name+".tmp-")
	if err != nil {
		return err
	}
	defer os.Remove(tmp.Name())
	if _, err = tmp.Write(raw); err != nil {
		tmp.Close()
		return err
	}
	if err = tmp.Sync(); err != nil {
		tmp.Close()
		return err
	}
	if err = tmp.Close(); err != nil {
		return err
	}
	if err = privateFile(tmp.Name()); err != nil {
		return err
	}
	from, err := windows.UTF16PtrFromString(tmp.Name())
	if err != nil {
		return err
	}
	to, err := windows.UTF16PtrFromString(filepath.Join(dir, name))
	if err != nil {
		return err
	}
	return windows.MoveFileEx(from, to, windows.MOVEFILE_REPLACE_EXISTING|windows.MOVEFILE_WRITE_THROUGH)
}

func writeIntentResult(v workspaceWriteIntent, p string) WorkspaceWriteResult {
	return WorkspaceWriteResult{BeforeHash: v.ExpectedHash, AfterHash: v.AfterHash, CandidatePath: v.CandidatePath,
		PreimagePath: v.PreimagePath, BackupPath: v.BackupPath, IntentPath: p, State: v.State, Applied: v.State == "APPLIED"}
}

// This read-only lookup runs before authorization so an already durable
// physical outcome cannot be reclassified as NOT_APPLIED when the lease or
// root is revoked. It grants no right to publish or replay the write.
func priorWorkspaceWriteIntent(journalRoot, key string) (workspaceWriteIntent, string, bool, error) {
	var intent workspaceWriteIntent
	if key == "" || len(key) > 1024 || journalRoot == "" {
		return intent, "", false, nil
	}
	journal, err := filepath.Abs(journalRoot)
	if err != nil || !localWindowsPath(journal) {
		return intent, "", false, errors.New("trusted local journal unavailable")
	}
	keyHash := strings.TrimPrefix(writeHash([]byte(key)), "sha256:")
	p := filepath.Join(journal, "workspace-writes", "intents", "intent-"+keyHash+".json")
	if reparse, e := chainHasReparsePoint(p); e != nil || reparse {
		return intent, p, true, errors.New("intent journal path is unavailable or reparse")
	}
	f, err := os.Open(p)
	if errors.Is(err, os.ErrNotExist) {
		return intent, p, false, nil
	}
	if err != nil {
		return intent, p, true, err
	}
	defer f.Close()
	raw, err := io.ReadAll(io.LimitReader(f, 64<<10))
	if err != nil || len(raw) >= 64<<10 || json.Unmarshal(raw, &intent) != nil || intent.Version != 1 || intent.KeyHash != keyHash {
		return intent, p, true, errors.New("durable intent cannot be trusted")
	}
	return intent, p, true, nil
}

func intentBodyHash(rootIdentity, rel, expected, after string, create bool, scopeHash string) string {
	raw, _ := json.Marshal([]any{rootIdentity, strings.ToLower(rel), expected, after, create, scopeHash})
	return writeHash(raw)
}

// WriteWorkspaceFile has no business permission of its own. The caller binds
// the project/session/task before invoking it and supplies Revalidate for the
// current root pin and authority while this physical path is locked.
func WriteWorkspaceFile(ctx context.Context, in WorkspaceWriteInput) (out WorkspaceWriteResult, err error) {
	prior, priorPath, priorExists, priorErr := priorWorkspaceWriteIntent(in.JournalRoot, in.IntentKey)
	if priorErr != nil {
		return out, writeError("WRITE_RECOVERY_REQUIRED", "UNKNOWN", priorErr)
	}
	defer func() {
		if err == nil || !priorExists || prior.State == "CONFLICT" {
			return
		}
		var classified *WorkspaceWriteError
		if errors.As(err, &classified) && classified.Outcome == "NOT_APPLIED" {
			if prior.State == "APPLIED" && (classified.Code == "COMMAND_ID_CONFLICT" || classified.Code == "INTENT_KEY_CONFLICT") {
				return // Different requested body was not applied; old proof remains.
			}
			out = writeIntentResult(prior, priorPath)
			err = writeError(classified.Code, "UNKNOWN", classified)
		}
	}()
	rootPath, err := validateWorkspaceWrite(in)
	if err != nil {
		return out, err
	}
	if err := in.Revalidate(ctx); err != nil {
		return out, writeError("POLICY_DENIED", "NOT_APPLIED", err)
	}
	journal, err := writeJournalDirs(in.JournalRoot)
	if err != nil {
		return out, writeError("JOURNAL_UNAVAILABLE", "NOT_APPLIED", err)
	}
	volume, fileID, _, err := fileIdentity(rootPath)
	if err != nil {
		return out, writeError("WORKSPACE_REVOKED", "NOT_APPLIED", err)
	}
	rootIdentity := fmt.Sprintf("%s:%016x", volume, fileID)
	keyHash := strings.TrimPrefix(writeHash([]byte(in.IntentKey)), "sha256:")
	pathHash := strings.TrimPrefix(writeHash([]byte(rootIdentity+"|"+strings.ToLower(in.RelativePath))), "sha256:")
	unlockKey, err := lockWorkspaceWrite(ctx, filepath.Join(journal, "locks", "intent-"+keyHash+".lock"))
	if err != nil {
		return out, writeError("LOCK_UNAVAILABLE", "NOT_APPLIED", err)
	}
	defer unlockKey()
	unlockPath, err := lockWorkspaceWrite(ctx, filepath.Join(journal, "locks", "path-"+pathHash+".lock"))
	if err != nil {
		return out, writeError("LOCK_UNAVAILABLE", "NOT_APPLIED", err)
	}
	defer unlockPath()
	if err := in.Revalidate(ctx); err != nil {
		return out, writeError("POLICY_DENIED", "NOT_APPLIED", err)
	}
	absolute := filepath.Join(rootPath, filepath.FromSlash(in.RelativePath))
	guards, err := guardWriteDirectories(filepath.Dir(absolute))
	if err != nil {
		return out, writeError("PATH_OUT_OF_SCOPE", "NOT_APPLIED", err)
	}
	defer closeWriteGuards(guards)
	vol2, id2, _, err := fileIdentity(rootPath)
	if err != nil || vol2 != volume || id2 != fileID {
		return out, writeError("WORKSPACE_REVOKED", "NOT_APPLIED", errors.New("root identity changed while locking path"))
	}
	if err := in.Revalidate(ctx); err != nil {
		return out, writeError("POLICY_DENIED", "NOT_APPLIED", err)
	}
	expected := ""
	if in.ExpectedHash != nil {
		expected = *in.ExpectedHash
	}
	after := writeHash(in.Content)
	bodyHash := intentBodyHash(rootIdentity, in.RelativePath, expected, after, in.CreateIfMissing, in.ScopeHash)
	intentDir := filepath.Join(journal, "intents")
	intentName := "intent-" + keyHash + ".json"
	intentPath := filepath.Join(intentDir, intentName)
	if raw, readErr := os.ReadFile(intentPath); readErr == nil {
		var previous workspaceWriteIntent
		if json.Unmarshal(raw, &previous) != nil || previous.Version != 1 || previous.KeyHash != keyHash {
			return out, writeError("INTENT_KEY_CONFLICT", "NOT_APPLIED", errors.New("intent key was used for different bytes or scope"))
		}
		if previous.ScopeHash != in.ScopeHash {
			return out, writeError("COMMAND_ID_CONFLICT", "NOT_APPLIED", errors.New("intent key was used for a different request scope"))
		}
		if previous.BodyHash != bodyHash {
			return out, writeError("INTENT_KEY_CONFLICT", "NOT_APPLIED", errors.New("intent key was used for different bytes or scope"))
		}
		out = writeIntentResult(previous, intentPath)
		if previous.State != "APPLIED" {
			return out, writeError("WRITE_RECOVERY_REQUIRED", "UNKNOWN", errors.New("persistent intent is not safely replayable"))
		}
		guard, openErr := openWriteTarget(absolute)
		if openErr != nil {
			return out, writeError("EXTERNAL_WRITE_RACE", "UNKNOWN", openErr)
		}
		data, readErr := readGuardedBytes(guard)
		guard.Close()
		if readErr != nil || writeHash(data) != previous.AfterHash {
			return out, writeError("EXTERNAL_WRITE_RACE", "UNKNOWN", errors.New("applied target has since changed"))
		}
		return out, nil
	} else if !errors.Is(readErr, os.ErrNotExist) {
		return out, writeError("JOURNAL_UNAVAILABLE", "NOT_APPLIED", readErr)
	}
	if err := runtimeToolPlainPath(in.Root, in.RelativePath, in.CreateIfMissing); err != nil {
		return out, writeError("PATH_OUT_OF_SCOPE", "NOT_APPLIED", err)
	}
	candidate, err := writeImmutablePrivate(filepath.Join(journal, "candidates"), "candidate-"+after[7:]+".bin", in.Content)
	if err != nil {
		return out, writeError("JOURNAL_UNAVAILABLE", "NOT_APPLIED", err)
	}
	var guard *os.File
	preimage := ""
	if in.CreateIfMissing {
		if _, statErr := in.Root.Lstat(in.RelativePath); statErr == nil {
			return out, writeError("CONTENT_CONFLICT", "NOT_APPLIED", errors.New("create target already exists"))
		} else if !errors.Is(statErr, os.ErrNotExist) {
			return out, writeError("PATH_OUT_OF_SCOPE", "NOT_APPLIED", statErr)
		}
	} else {
		guard, err = openWriteTarget(absolute)
		if err != nil {
			return out, writeError("EXTERNAL_WRITE_RACE", "NOT_APPLIED", err)
		}
		defer guard.Close()
		old, readErr := readGuardedBytes(guard)
		if readErr != nil {
			return out, writeError("CONTENT_TOO_LARGE", "NOT_APPLIED", readErr)
		}
		if writeHash(old) != expected {
			return out, writeError("CONTENT_CONFLICT", "NOT_APPLIED", errors.New("expected bytes are stale"))
		}
		preimage, err = writeImmutablePrivate(filepath.Join(journal, "preimages"), "before-"+keyHash+".bin", old)
		if err != nil {
			return out, writeError("JOURNAL_UNAVAILABLE", "NOT_APPLIED", err)
		}
	}
	nonce, err := writeNonce()
	if err != nil {
		return out, writeError("JOURNAL_UNAVAILABLE", "NOT_APPLIED", err)
	}
	parent := path.Dir(in.RelativePath)
	stageRel := path.Join(parent, ".researchos-stage-"+nonce+".tmp")
	backupRel := path.Join(parent, ".researchos-backup-"+nonce+".bin")
	intent := workspaceWriteIntent{Version: 1, KeyHash: keyHash, BodyHash: bodyHash, ScopeHash: in.ScopeHash, RootIdentity: rootIdentity,
		RelativePath: in.RelativePath, ExpectedHash: expected, AfterHash: after, Create: in.CreateIfMissing,
		CandidatePath: candidate, PreimagePath: preimage, StagePath: filepath.Join(rootPath, filepath.FromSlash(stageRel)),
		State: "PENDING"}
	if !in.CreateIfMissing {
		intent.BackupPath = filepath.Join(rootPath, filepath.FromSlash(backupRel))
	}
	if err := persistWorkspaceIntent(intentDir, intentName, intent); err != nil {
		return out, writeError("JOURNAL_UNAVAILABLE", "NOT_APPLIED", err)
	}
	out = writeIntentResult(intent, intentPath)
	stage, err := in.Root.OpenFile(stageRel, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0o600)
	if err != nil {
		return out, writeError("WRITE_RECOVERY_REQUIRED", "UNKNOWN", err)
	}
	if _, err = stage.Write(in.Content); err == nil {
		err = stage.Sync()
	}
	closeErr := stage.Close()
	if err == nil {
		err = closeErr
	}
	if err != nil {
		return out, writeError("WRITE_RECOVERY_REQUIRED", "UNKNOWN", err)
	}
	if ctx.Err() != nil {
		return out, writeError("WRITE_RECOVERY_REQUIRED", "UNKNOWN", ctx.Err())
	}
	if workspaceWriteBeforePublish != nil {
		if err := workspaceWriteBeforePublish(absolute); err != nil {
			return out, writeError("WRITE_RECOVERY_REQUIRED", "UNKNOWN", err)
		}
	}
	if err := in.Revalidate(ctx); err != nil {
		return out, writeError("WRITE_RECOVERY_REQUIRED", "UNKNOWN", err)
	}
	if in.CreateIfMissing {
		if err := in.Root.Link(stageRel, in.RelativePath); err != nil {
			intent.State, intent.LastError = "CONFLICT", err.Error()
			_ = persistWorkspaceIntent(intentDir, intentName, intent)
			out = writeIntentResult(intent, intentPath)
			return out, writeError("CONTENT_CONFLICT", "NOT_APPLIED", err)
		}
		// Link publishes complete bytes only when the name was absent. Remove
		// the staging alias before accepting success: otherwise later edits to
		// that alias would mutate the newly created target outside this lock.
		if err := in.Root.Remove(stageRel); err != nil {
			intent.State, intent.LastError = "UNKNOWN", "published create retained writable staging alias: "+err.Error()
			_ = persistWorkspaceIntent(intentDir, intentName, intent)
			out = writeIntentResult(intent, intentPath)
			return out, writeError("WRITE_RECOVERY_REQUIRED", "UNKNOWN", err)
		}
	} else {
		if err := callReplaceFile(absolute, intent.StagePath, intent.BackupPath); err != nil {
			intent.State, intent.LastError = "UNKNOWN", err.Error()
			_ = persistWorkspaceIntent(intentDir, intentName, intent)
			out = writeIntentResult(intent, intentPath)
			return out, writeError("WRITE_RECOVERY_REQUIRED", "UNKNOWN", err)
		}
		// Backup is the actual file ReplaceFileW took, not a second pre-write
		// hash of a name that an external process could have swapped.
		actual, backupErr := readWriteFile(in.Root, backupRel)
		if backupErr != nil {
			intent.State, intent.LastError = "UNKNOWN", backupErr.Error()
			_ = persistWorkspaceIntent(intentDir, intentName, intent)
			out = writeIntentResult(intent, intentPath)
			return out, writeError("WRITE_RECOVERY_REQUIRED", "UNKNOWN", backupErr)
		}
		intent.ActualBefore = writeHash(actual)
		if intent.ActualBefore != expected {
			intent.State, intent.LastError = "EXTERNAL_RACE", "actual replaced bytes differed from expected hash"
			_ = persistWorkspaceIntent(intentDir, intentName, intent)
			out = writeIntentResult(intent, intentPath)
			return out, writeError("EXTERNAL_WRITE_RACE", "UNKNOWN", errors.New(intent.LastError))
		}
	}
	newGuard, err := openWriteTarget(absolute)
	if err != nil {
		intent.State, intent.LastError = "UNKNOWN", err.Error()
		_ = persistWorkspaceIntent(intentDir, intentName, intent)
		out = writeIntentResult(intent, intentPath)
		return out, writeError("WRITE_RECOVERY_REQUIRED", "UNKNOWN", err)
	}
	actualAfter, err := readGuardedBytes(newGuard)
	newGuard.Close()
	if err != nil || writeHash(actualAfter) != after {
		intent.State, intent.LastError = "EXTERNAL_RACE", "published bytes changed before readback"
		_ = persistWorkspaceIntent(intentDir, intentName, intent)
		out = writeIntentResult(intent, intentPath)
		return out, writeError("EXTERNAL_WRITE_RACE", "UNKNOWN", errors.New(intent.LastError))
	}
	intent.ObservedAfter, intent.State = after, "APPLIED"
	if err := persistWorkspaceIntent(intentDir, intentName, intent); err != nil {
		return out, writeError("WRITE_RECOVERY_REQUIRED", "UNKNOWN", err)
	}
	return writeIntentResult(intent, intentPath), nil
}

func guardWriteDirectories(parent string) ([]windows.Handle, error) {
	volume := filepath.VolumeName(parent)
	base := volume + string(filepath.Separator)
	rel, err := filepath.Rel(base, parent)
	if err != nil || rel == ".." || strings.HasPrefix(rel, ".."+string(filepath.Separator)) {
		return nil, errors.New("directory escaped local volume")
	}
	var handles []windows.Handle
	current := base
	for _, part := range strings.Split(rel, string(filepath.Separator)) {
		if part == "." || part == "" {
			continue
		}
		current = filepath.Join(current, part)
		wide, err := windows.UTF16PtrFromString(current)
		if err != nil {
			closeWriteGuards(handles)
			return nil, err
		}
		h, err := windows.CreateFile(wide, windows.FILE_READ_ATTRIBUTES,
			windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE, nil, windows.OPEN_EXISTING,
			windows.FILE_FLAG_BACKUP_SEMANTICS|windows.FILE_FLAG_OPEN_REPARSE_POINT, 0)
		if err != nil {
			closeWriteGuards(handles)
			return nil, err
		}
		var info windows.ByHandleFileInformation
		if err = windows.GetFileInformationByHandle(h, &info); err != nil || info.FileAttributes&fileAttributeReparsePoint != 0 || info.FileAttributes&windows.FILE_ATTRIBUTE_DIRECTORY == 0 {
			windows.CloseHandle(h)
			closeWriteGuards(handles)
			return nil, errors.New("directory chain contains reparse point or non-directory")
		}
		handles = append(handles, h)
	}
	return handles, nil
}

func closeWriteGuards(handles []windows.Handle) {
	for i := len(handles) - 1; i >= 0; i-- {
		_ = windows.CloseHandle(handles[i])
	}
}

func openWriteTarget(name string) (*os.File, error) {
	wide, err := windows.UTF16PtrFromString(name)
	if err != nil {
		return nil, err
	}
	h, err := windows.CreateFile(wide, windows.GENERIC_READ, windows.FILE_SHARE_READ|windows.FILE_SHARE_DELETE,
		nil, windows.OPEN_EXISTING, windows.FILE_FLAG_OPEN_REPARSE_POINT, 0)
	if err != nil {
		return nil, err
	}
	var info windows.ByHandleFileInformation
	if err = windows.GetFileInformationByHandle(h, &info); err != nil || info.FileAttributes&fileAttributeReparsePoint != 0 || info.FileAttributes&windows.FILE_ATTRIBUTE_DIRECTORY != 0 {
		windows.CloseHandle(h)
		return nil, errors.New("target is a reparse point or non-file")
	}
	return os.NewFile(uintptr(h), name), nil
}

func readGuardedBytes(f *os.File) ([]byte, error) {
	info, err := f.Stat()
	if err != nil || !info.Mode().IsRegular() || info.Size() > workspaceWriteLimit {
		return nil, errors.New("target is not a bounded regular file")
	}
	if _, err := f.Seek(0, io.SeekStart); err != nil {
		return nil, err
	}
	data, err := io.ReadAll(io.LimitReader(f, workspaceWriteLimit+1))
	if err != nil || len(data) > workspaceWriteLimit {
		return nil, errors.New("target read exceeded bounded file size")
	}
	return data, nil
}

func readWriteFile(root *os.Root, rel string) ([]byte, error) {
	f, err := root.Open(rel)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	return readGuardedBytes(f)
}

func callReplaceFile(target, stage, backup string) error {
	a, err := windows.UTF16PtrFromString(target)
	if err != nil {
		return err
	}
	b, err := windows.UTF16PtrFromString(stage)
	if err != nil {
		return err
	}
	c, err := windows.UTF16PtrFromString(backup)
	if err != nil {
		return err
	}
	value, _, callErr := replaceFileProc.Call(uintptr(unsafe.Pointer(a)), uintptr(unsafe.Pointer(b)), uintptr(unsafe.Pointer(c)), 0, 0, 0)
	runtime.KeepAlive(a)
	runtime.KeepAlive(b)
	runtime.KeepAlive(c)
	if value == 0 {
		return callErr
	}
	return nil
}
