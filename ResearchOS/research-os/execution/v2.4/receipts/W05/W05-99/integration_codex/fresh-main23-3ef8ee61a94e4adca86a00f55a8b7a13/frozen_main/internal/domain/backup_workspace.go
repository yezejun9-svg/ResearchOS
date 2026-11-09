package domain

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// Workspace contents are bounded rather than silently omitted. These limits cover the
// entire backup, not each workspace independently.
const (
	BackupWorkspaceMaxRoots     = 8
	BackupWorkspaceMaxFiles     = 4096
	BackupWorkspaceMaxDirs      = 4096
	BackupWorkspaceMaxPathBytes = 4096
	BackupWorkspaceMaxBytes     = 256 << 20
	BackupWorkspaceMaxFileBytes = 16 << 20
)

type BackupWorkspaceLimits struct {
	MaxFiles     int
	MaxDirs      int
	MaxBytes     int64
	MaxFileBytes int64
}

type BackupWorkspaceFile struct {
	Path string
	Data []byte
}

type BackupWorkspaceSnapshot struct {
	Directories []string
	Files       []BackupWorkspaceFile
}

// WorkspaceBackupSource must verify an existing Host root binding, current pin,
// revocation and OS ownership before reading any path. A database path alone is
// never permission to read a workspace.
type WorkspaceBackupSource interface {
	SnapshotWorkspace(context.Context, WorkspaceBinding, string, BackupWorkspaceLimits) (BackupWorkspaceSnapshot, error)
}

type WorkspaceRestoreRequest struct {
	AuthorizedRef string
	RealPath      string
	Access        string
	PrincipalID   string
}

type WorkspaceRestorePin struct {
	AuthorizedRef    string
	RealPath         string
	HostPrincipalRef string
}

// WorkspaceRestoreTarget runs only after the isolated restored data root has
// been published. It must bind a fresh Host root to each requested final path.
// The database remains RESTORE_PENDING until every pin has been verified.
type WorkspaceRestoreTarget func(context.Context, string, []WorkspaceRestoreRequest) ([]WorkspaceRestorePin, error)

type backupWorkspaceIndex struct {
	Format string                `json:"format"`
	Roots  []backupWorkspaceRoot `json:"roots"`
}

type backupWorkspaceRoot struct {
	Ref         string                `json:"ref"`
	SourcePath  string                `json:"source_path"`
	Access      string                `json:"access"`
	PrincipalID string                `json:"principal_id"`
	Directories []string              `json:"directories"`
	Files       []backupWorkspaceFile `json:"files"`
}

type backupWorkspaceFile struct {
	Path string `json:"path"`
	Blob string `json:"blob"`
	Hash string `json:"hash"`
	Size int    `json:"size"`
}

func (s *Service) CreateBackupWithWorkspaces(ctx context.Context, destination string, key []byte, source WorkspaceBackupSource) (BackupManifest, error) {
	if source == nil {
		return BackupManifest{}, fmt.Errorf("BACKUP_WORKSPACE_SOURCE_REQUIRED")
	}
	return s.createBackupPolicy(ctx, destination, key, nil, source)
}

func workspaceBackupBindings(db *sql.DB) ([]WorkspaceBinding, error) {
	rows, err := db.Query(`SELECT body FROM domain_objects WHERE project='' AND kind=? ORDER BY id`, KindWorkspaceBinding)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	bindings := []WorkspaceBinding{}
	for rows.Next() {
		var raw string
		if err := rows.Scan(&raw); err != nil {
			return nil, err
		}
		binding, err := decodeBinding(raw)
		if err != nil {
			return nil, err
		}
		if binding.Status == WorkspaceActive {
			bindings = append(bindings, *binding)
		} else if binding.Status != WorkspaceRevoked {
			return nil, fmt.Errorf("BACKUP_WORKSPACE_STATUS_INVALID")
		}
	}
	return bindings, rows.Err()
}

func backupWorkspaceBlobName(ref, rel string) string {
	return "workspace-" + strings.TrimPrefix(Digest([]byte(ref+"\x00"+rel)), "sha256:") + ".bin"
}

func backupWorkspaceDirectory(destination, ref string) string {
	return filepath.Join(destination, "workspaces", strings.TrimPrefix(Digest([]byte(ref)), "sha256:"))
}

func backupWorkspaceOverlaps(left, right string) bool {
	a, ea := filepath.Abs(left)
	b, eb := filepath.Abs(right)
	if ea != nil || eb != nil {
		return true
	}
	if strings.EqualFold(filepath.Clean(a), filepath.Clean(b)) {
		return true
	}
	for _, pair := range [][2]string{{a, b}, {b, a}} {
		rel, err := filepath.Rel(pair[0], pair[1])
		if err == nil && rel != ".." && !strings.HasPrefix(rel, ".."+string(filepath.Separator)) && !filepath.IsAbs(rel) {
			return true
		}
	}
	return false
}

// BackupWorkspaceDestination is the one final location accepted by Host pinning.
func BackupWorkspaceDestination(destination, ref string) string {
	return backupWorkspaceDirectory(destination, ref)
}

func backupWorkspaceRelative(rel string) bool {
	if rel == "" || len(rel) > BackupWorkspaceMaxPathBytes || strings.Contains(rel, "\\") || strings.Contains(rel, ":") || filepath.ToSlash(filepath.Clean(filepath.FromSlash(rel))) != rel {
		return false
	}
	if !filepath.IsLocal(filepath.FromSlash(rel)) || rel == "." || strings.HasPrefix(rel, "../") {
		return false
	}
	for _, part := range strings.Split(rel, "/") {
		if part == "" || part == "." || part == ".." {
			return false
		}
	}
	return true
}

func backupWorkspaceFiles(ctx context.Context, db *sql.DB, source WorkspaceBackupSource, destination string) (map[string][]byte, int, error) {
	bindings, err := workspaceBackupBindings(db)
	if err != nil {
		return nil, 0, err
	}
	if len(bindings) == 0 {
		return nil, 0, nil
	}
	if source == nil {
		return nil, 0, fmt.Errorf("BACKUP_WORKSPACE_SOURCE_REQUIRED: %d active workspace(s)", len(bindings))
	}
	if len(bindings) > BackupWorkspaceMaxRoots {
		return nil, 0, fmt.Errorf("BACKUP_WORKSPACE_ROOT_LIMIT: %d", len(bindings))
	}
	files := map[string][]byte{}
	index := backupWorkspaceIndex{Format: "RESEARCHOS_WORKSPACE_SNAPSHOT_V1", Roots: []backupWorkspaceRoot{}}
	remainingFiles, remainingDirs, remainingBytes := BackupWorkspaceMaxFiles, BackupWorkspaceMaxDirs, int64(BackupWorkspaceMaxBytes)
	for _, b := range bindings {
		if err := ctx.Err(); err != nil {
			return nil, 0, err
		}
		if b.AuthorizedRef == "" || b.RealPath == "" || b.PrincipalID == "" || b.Access != "READ_ONLY" && b.Access != "READ_WRITE" {
			return nil, 0, fmt.Errorf("BACKUP_WORKSPACE_BINDING_INVALID")
		}
		snapshot, err := source.SnapshotWorkspace(ctx, b, destination, BackupWorkspaceLimits{MaxFiles: remainingFiles, MaxDirs: remainingDirs, MaxBytes: remainingBytes, MaxFileBytes: BackupWorkspaceMaxFileBytes})
		if err != nil {
			return nil, 0, fmt.Errorf("BACKUP_WORKSPACE_SNAPSHOT_FAILED %s: %w", b.AuthorizedRef, err)
		}
		if len(snapshot.Files) > remainingFiles || len(snapshot.Directories) > remainingDirs {
			return nil, 0, fmt.Errorf("BACKUP_WORKSPACE_FILE_LIMIT %s", b.AuthorizedRef)
		}
		root := backupWorkspaceRoot{Ref: b.AuthorizedRef, SourcePath: b.RealPath, Access: b.Access, PrincipalID: b.PrincipalID,
			Directories: append([]string{}, snapshot.Directories...), Files: []backupWorkspaceFile{}}
		seen := map[string]bool{}
		for _, dir := range root.Directories {
			if !backupWorkspaceRelative(dir) || seen[dir] {
				return nil, 0, fmt.Errorf("BACKUP_WORKSPACE_DIRECTORY_INVALID %s", b.AuthorizedRef)
			}
			seen[dir] = true
		}
		for _, file := range snapshot.Files {
			if !backupWorkspaceRelative(file.Path) || seen[file.Path] || len(file.Data) > BackupWorkspaceMaxFileBytes || int64(len(file.Data)) > remainingBytes {
				return nil, 0, fmt.Errorf("BACKUP_WORKSPACE_FILE_INVALID_OR_LIMIT %s %s", b.AuthorizedRef, file.Path)
			}
			seen[file.Path] = true
			blob := backupWorkspaceBlobName(b.AuthorizedRef, file.Path)
			if _, exists := files[blob]; exists {
				return nil, 0, fmt.Errorf("BACKUP_WORKSPACE_BLOB_COLLISION")
			}
			files[blob] = file.Data
			root.Files = append(root.Files, backupWorkspaceFile{Path: file.Path, Blob: blob, Hash: Digest(file.Data), Size: len(file.Data)})
			remainingFiles--
			remainingBytes -= int64(len(file.Data))
		}
		sort.Strings(root.Directories)
		sort.Slice(root.Files, func(i, j int) bool { return root.Files[i].Path < root.Files[j].Path })
		remainingDirs -= len(root.Directories)
		index.Roots = append(index.Roots, root)
	}
	files["workspace-index.json"] = Bytes(index)
	return files, len(index.Roots), nil
}

func backupDecodeWorkspaceIndex(files map[string][]byte) (backupWorkspaceIndex, error) {
	var index backupWorkspaceIndex
	if len(files["workspace-index.json"]) == 0 {
		return index, nil
	}
	if err := json.Unmarshal(files["workspace-index.json"], &index); err != nil || index.Format != "RESEARCHOS_WORKSPACE_SNAPSHOT_V1" || len(index.Roots) > BackupWorkspaceMaxRoots {
		return index, fmt.Errorf("RESTORE_WORKSPACE_INDEX_INVALID")
	}
	return index, nil
}

func backupWorkspaceRestorePaths(files map[string][]byte, backupDirectory, destination string) error {
	index, err := backupDecodeWorkspaceIndex(files)
	if err != nil {
		return err
	}
	if len(index.Roots) == 0 {
		return nil
	}
	if backupWorkspaceOverlaps(backupDirectory, destination) {
		return fmt.Errorf("RESTORE_WORKSPACE_BACKUP_DIRECTORY_OVERLAP")
	}
	for _, root := range index.Roots {
		if backupWorkspaceOverlaps(root.SourcePath, destination) || backupWorkspaceOverlaps(root.SourcePath, backupDirectory) {
			return fmt.Errorf("RESTORE_WORKSPACE_SOURCE_DIRECTORY_OVERLAP")
		}
	}
	return nil
}

func backupPrepareWorkspaces(ctx context.Context, db *sql.DB, files map[string][]byte, stage, destination string) ([]WorkspaceRestoreRequest, error) {
	bindings, err := workspaceBackupBindings(db)
	if err != nil {
		return nil, err
	}
	index, err := backupDecodeWorkspaceIndex(files)
	if err != nil {
		return nil, err
	}
	if len(bindings) != len(index.Roots) {
		return nil, fmt.Errorf("RESTORE_WORKSPACE_INVENTORY_MISMATCH")
	}
	byRef := map[string]WorkspaceBinding{}
	for _, b := range bindings {
		byRef[b.AuthorizedRef] = b
	}
	requests := []WorkspaceRestoreRequest{}
	usedBlobs := map[string]bool{"workspace-index.json": true}
	count, dirCount, total := 0, 0, int64(0)
	for _, root := range index.Roots {
		b, ok := byRef[root.Ref]
		if !ok || b.RealPath != root.SourcePath || b.Access != root.Access || b.PrincipalID != root.PrincipalID || len(root.Files) > BackupWorkspaceMaxFiles || len(root.Directories) > BackupWorkspaceMaxDirs {
			return nil, fmt.Errorf("RESTORE_WORKSPACE_BINDING_MISMATCH")
		}
		delete(byRef, root.Ref)
		stageRoot := backupWorkspaceDirectory(stage, root.Ref)
		if err := os.MkdirAll(stageRoot, 0700); err != nil {
			return nil, err
		}
		seen := map[string]bool{}
		for _, rel := range root.Directories {
			if !backupWorkspaceRelative(rel) || seen[rel] {
				return nil, fmt.Errorf("RESTORE_WORKSPACE_DIRECTORY_INVALID")
			}
			seen[rel] = true
			dirCount++
			if dirCount > BackupWorkspaceMaxDirs {
				return nil, fmt.Errorf("RESTORE_WORKSPACE_DIRECTORY_LIMIT")
			}
			if err := os.MkdirAll(filepath.Join(stageRoot, filepath.FromSlash(rel)), 0700); err != nil {
				return nil, err
			}
		}
		for _, file := range root.Files {
			if !backupWorkspaceRelative(file.Path) || seen[file.Path] || file.Blob != backupWorkspaceBlobName(root.Ref, file.Path) || usedBlobs[file.Blob] {
				return nil, fmt.Errorf("RESTORE_WORKSPACE_FILE_INVALID")
			}
			seen[file.Path], usedBlobs[file.Blob] = true, true
			raw, exists := files[file.Blob]
			if !exists || len(raw) != file.Size || Digest(raw) != file.Hash || len(raw) > BackupWorkspaceMaxFileBytes {
				return nil, fmt.Errorf("RESTORE_WORKSPACE_FILE_HASH")
			}
			count++
			total += int64(len(raw))
			if count > BackupWorkspaceMaxFiles || total > BackupWorkspaceMaxBytes {
				return nil, fmt.Errorf("RESTORE_WORKSPACE_LIMIT")
			}
			path := filepath.Join(stageRoot, filepath.FromSlash(file.Path))
			if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
				return nil, err
			}
			if err := backupWrite(path, raw); err != nil {
				return nil, err
			}
		}
		requests = append(requests, WorkspaceRestoreRequest{AuthorizedRef: root.Ref,
			RealPath: backupWorkspaceDirectory(destination, root.Ref), Access: root.Access, PrincipalID: root.PrincipalID})
	}
	for name := range files {
		if strings.HasPrefix(name, "workspace-") && !usedBlobs[name] {
			return nil, fmt.Errorf("RESTORE_WORKSPACE_UNREFERENCED_BLOB")
		}
	}
	if len(byRef) != 0 {
		return nil, fmt.Errorf("RESTORE_WORKSPACE_MISSING_ROOT")
	}
	if len(requests) == 0 {
		return requests, nil
	}
	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()
	svc := &Service{DB: db}
	for _, request := range requests {
		b := bFromMap(request.AuthorizedRef, bindings)
		record := b.record()
		record["real_path"] = request.RealPath
		record["display_path"] = request.RealPath
		record["status"] = "RESTORE_PENDING"
		record["host_principal_ref"] = ""
		record["revision"] = b.Revision + 1
		if err := svc.putOpaque(ctx, tx, "", KindWorkspaceBinding, b.AuthorizedRef, record); err != nil {
			return nil, err
		}
		if b.ProjectID != nil {
			var raw string
			if err := tx.QueryRowContext(ctx, `SELECT body FROM domain_objects WHERE project=? AND kind='Project' AND id=?`, *b.ProjectID, *b.ProjectID).Scan(&raw); err != nil {
				return nil, fmt.Errorf("RESTORE_PROJECT_BINDING_MISSING: %w", err)
			}
			project, err := Decode([]byte(raw))
			if err != nil {
				return nil, err
			}
			if Str(project, "authorized_workspace_ref") == b.AuthorizedRef {
				if Str(project, "real_path") != b.RealPath {
					return nil, fmt.Errorf("RESTORE_PROJECT_SOURCE_PATH_MISMATCH")
				}
				revision, err := Num(project, "revision")
				if err != nil {
					return nil, err
				}
				project["real_path"] = request.RealPath
				project["revision"] = revision + 1
				if err := svc.putOpaque(ctx, tx, *b.ProjectID, "Project", *b.ProjectID, project); err != nil {
					return nil, err
				}
			}
		}
	}
	if err := tx.Commit(); err != nil {
		return nil, err
	}
	return requests, nil
}

func bFromMap(ref string, bindings []WorkspaceBinding) WorkspaceBinding {
	for _, b := range bindings {
		if b.AuthorizedRef == ref {
			return b
		}
	}
	panic("verified workspace binding missing")
}

func backupActivateWorkspaces(ctx context.Context, db *sql.DB, requests []WorkspaceRestoreRequest, pins []WorkspaceRestorePin) error {
	if len(requests) != len(pins) {
		return fmt.Errorf("RESTORE_WORKSPACE_PIN_COUNT")
	}
	byRef := map[string]WorkspaceRestorePin{}
	for _, pin := range pins {
		if pin.AuthorizedRef == "" || pin.HostPrincipalRef == "" || byRef[pin.AuthorizedRef].AuthorizedRef != "" {
			return fmt.Errorf("RESTORE_WORKSPACE_PIN_INVALID")
		}
		byRef[pin.AuthorizedRef] = pin
	}
	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	svc := &Service{DB: db}
	for _, request := range requests {
		pin, ok := byRef[request.AuthorizedRef]
		if !ok || pin.RealPath != request.RealPath {
			return fmt.Errorf("RESTORE_WORKSPACE_PIN_PATH_MISMATCH")
		}
		b, err := svc.binding(ctx, tx, request.AuthorizedRef)
		if err != nil || b.Status != "RESTORE_PENDING" || b.RealPath != request.RealPath || b.Access != request.Access || b.PrincipalID != request.PrincipalID {
			return fmt.Errorf("RESTORE_WORKSPACE_PENDING_MISMATCH")
		}
		record := b.record()
		record["status"] = WorkspaceActive
		record["host_principal_ref"] = pin.HostPrincipalRef
		record["revision"] = b.Revision + 1
		if err := svc.putOpaque(ctx, tx, "", KindWorkspaceBinding, b.AuthorizedRef, record); err != nil {
			return err
		}
	}
	return tx.Commit()
}
