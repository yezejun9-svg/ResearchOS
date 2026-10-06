package host

import (
	"context"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"researchos.local/research-os/internal/domain"
)

// SnapshotWorkspace exports only a currently pinned, non-revoked root that the
// current OS principal originally authorized. It rejects, rather than skips,
// links, special files and any item outside the explicit resource bounds.
func (h *Host) SnapshotWorkspace(ctx context.Context, binding domain.WorkspaceBinding, destination string, limits domain.BackupWorkspaceLimits) (domain.BackupWorkspaceSnapshot, error) {
	var out domain.BackupWorkspaceSnapshot
	if _, err := h.reverify(); err != nil {
		return out, err
	}
	if h.boundPrincipal() == "" || h.boundPrincipal() != binding.PrincipalID || binding.Status != domain.WorkspaceActive {
		return out, fmt.Errorf("BACKUP_WORKSPACE_OWNER_DENIED")
	}
	if limits.MaxFiles < 0 || limits.MaxDirs < 0 || limits.MaxBytes < 0 || limits.MaxFileBytes < 1 || limits.MaxFileBytes > domain.BackupWorkspaceMaxFileBytes {
		return out, fmt.Errorf("BACKUP_WORKSPACE_LIMIT_INVALID")
	}
	var pinned *RootBinding
	for _, root := range h.roots.List() {
		if root.Revoked || !strings.EqualFold(filepath.Clean(root.RealPath), filepath.Clean(binding.RealPath)) {
			continue
		}
		if binding.Access == AccessReadWrite && root.Access != AccessReadWrite {
			return out, fmt.Errorf("BACKUP_WORKSPACE_ACCESS_MISMATCH")
		}
		if pinned != nil {
			return out, fmt.Errorf("BACKUP_WORKSPACE_AMBIGUOUS_ROOT")
		}
		pinned = root
	}
	if pinned == nil {
		return out, fmt.Errorf("BACKUP_WORKSPACE_ROOT_NOT_PINNED")
	}
	// A restored workspace lives under its new data root by design. Allow only
	// that exact, currently pinned ref and path; every other data-root overlap
	// remains recursive/unsafe, as does any backup output inside the workspace.
	dataRoot := filepath.Dir(h.dir)
	if backupPathsOverlap(binding.RealPath, destination) ||
		(backupPathsOverlap(binding.RealPath, dataRoot) && !backupRestoredWorkspacePath(dataRoot, binding.AuthorizedRef, pinned)) {
		return out, fmt.Errorf("BACKUP_WORKSPACE_RECURSION: workspace intersects data root or backup output")
	}
	vol, id, _, err := fileIdentity(pinned.RealPath)
	if err != nil || vol != pinned.VolumeID || id != pinned.FileID {
		return out, fmt.Errorf("BACKUP_WORKSPACE_PIN_CHANGED")
	}
	if reparse, err := chainHasReparsePoint(pinned.RealPath); err != nil || reparse {
		return out, fmt.Errorf("BACKUP_WORKSPACE_ROOT_REPARSE")
	}
	root, err := os.OpenRoot(pinned.RealPath)
	if err != nil {
		return out, err
	}
	defer root.Close()
	out.Directories = []string{}
	out.Files = []domain.BackupWorkspaceFile{}
	var total int64
	err = filepath.WalkDir(pinned.RealPath, func(path string, entry os.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if err := ctx.Err(); err != nil {
			return err
		}
		if path == pinned.RealPath {
			return nil
		}
		rel, err := filepath.Rel(pinned.RealPath, path)
		if err != nil {
			return err
		}
		rel = filepath.ToSlash(rel)
		if len(rel) > domain.BackupWorkspaceMaxPathBytes || CheckRelativePath(rel) != nil || rel != NormalizeRelative(rel) {
			return fmt.Errorf("BACKUP_WORKSPACE_PATH_INVALID: %s", rel)
		}
		if _, err := h.roots.Resolve(pinned.Ref, rel, AccessReadOnly); err != nil {
			return fmt.Errorf("BACKUP_WORKSPACE_PATH_CHANGED %s: %w", rel, err)
		}
		if reparse, err := chainHasReparsePoint(path); err != nil || reparse {
			return fmt.Errorf("BACKUP_WORKSPACE_REPARSE: %s", rel)
		}
		info, err := entry.Info()
		if err != nil {
			return err
		}
		if info.IsDir() {
			if len(out.Directories) >= limits.MaxDirs {
				return fmt.Errorf("BACKUP_WORKSPACE_DIRECTORY_LIMIT: unbacked item %s", rel)
			}
			out.Directories = append(out.Directories, rel)
			return nil
		}
		if !info.Mode().IsRegular() {
			return fmt.Errorf("BACKUP_WORKSPACE_SPECIAL_FILE: %s", rel)
		}
		if len(out.Files) >= limits.MaxFiles || info.Size() > limits.MaxFileBytes || info.Size() > limits.MaxBytes-total {
			return fmt.Errorf("BACKUP_WORKSPACE_LIMIT: unbacked item %s", rel)
		}
		if err := runtimeToolPlainPath(root, rel, false); err != nil {
			return err
		}
		file, err := root.Open(rel)
		if err != nil {
			return err
		}
		before, err := file.Stat()
		if err != nil {
			file.Close()
			return err
		}
		data, readErr := io.ReadAll(io.LimitReader(file, limits.MaxFileBytes+1))
		after, statErr := file.Stat()
		closeErr := file.Close()
		if readErr != nil || statErr != nil || closeErr != nil {
			return fmt.Errorf("BACKUP_WORKSPACE_READ_FAILED: %s", rel)
		}
		current, err := root.Lstat(rel)
		if err != nil || !current.Mode().IsRegular() || !os.SameFile(before, after) || !os.SameFile(after, current) ||
			before.Size() != after.Size() || before.ModTime() != after.ModTime() || int64(len(data)) != after.Size() {
			return fmt.Errorf("BACKUP_WORKSPACE_FILE_CHANGED: %s", rel)
		}
		if len(data) > int(limits.MaxFileBytes) || int64(len(data)) > limits.MaxBytes-total {
			return fmt.Errorf("BACKUP_WORKSPACE_LIMIT: unbacked item %s", rel)
		}
		total += int64(len(data))
		out.Files = append(out.Files, domain.BackupWorkspaceFile{Path: rel, Data: data})
		return nil
	})
	if err != nil {
		return domain.BackupWorkspaceSnapshot{}, err
	}
	return out, nil
}

func backupRestoredWorkspacePath(dataRoot, authorizedRef string, pinned *RootBinding) bool {
	if pinned == nil || pinned.Ref == "" || pinned.Ref != authorizedRef {
		return false
	}
	actual, err := filepath.Abs(pinned.RealPath)
	if err != nil {
		return false
	}
	expected, err := filepath.Abs(domain.BackupWorkspaceDestination(dataRoot, pinned.Ref))
	return err == nil && strings.EqualFold(filepath.Clean(actual), filepath.Clean(expected))
}

func backupPathsOverlap(left, right string) bool {
	a, ea := filepath.Abs(left)
	b, eb := filepath.Abs(right)
	if ea != nil || eb != nil {
		return true
	}
	a, b = filepath.Clean(a), filepath.Clean(b)
	if strings.EqualFold(a, b) {
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

// PinRestoredWorkspace creates a new Host root record after the data root has
// reached its final path. It does not inherit the old host's private roots file.
func (h *Host) PinRestoredWorkspace(ctx context.Context, request domain.WorkspaceRestoreRequest) (domain.WorkspaceRestorePin, error) {
	var pin domain.WorkspaceRestorePin
	if _, err := h.reverify(); err != nil {
		return pin, err
	}
	if h.boundPrincipal() == "" || request.PrincipalID != h.boundPrincipal() {
		return pin, fmt.Errorf("RESTORE_WORKSPACE_OWNER_DENIED")
	}
	dataRoot := filepath.Dir(h.dir)
	expected := domain.BackupWorkspaceDestination(dataRoot, request.AuthorizedRef)
	if request.AuthorizedRef == "" || request.RealPath != expected || (request.Access != AccessReadOnly && request.Access != AccessReadWrite) {
		return pin, fmt.Errorf("RESTORE_WORKSPACE_PATH_DENIED")
	}
	if reparse, err := chainHasReparsePoint(request.RealPath); err != nil || reparse {
		return pin, fmt.Errorf("RESTORE_WORKSPACE_REPARSE")
	}
	root, err := h.roots.Register(request.AuthorizedRef, request.RealPath, request.Access, h.nowUTC())
	if err != nil {
		return pin, err
	}
	if _, err := h.roots.Resolve(root.Ref, "__researchos_pin_probe__", AccessReadOnly); err != nil {
		// Resolve checks the pin; it need not open the absent probe path.
		_ = h.roots.Revoke(root.Ref)
		return pin, err
	}
	if err := ctx.Err(); err != nil {
		_ = h.roots.Revoke(root.Ref)
		return pin, err
	}
	return domain.WorkspaceRestorePin{AuthorizedRef: request.AuthorizedRef,
		RealPath: root.RealPath, HostPrincipalRef: h.identity.Ref}, nil
}
