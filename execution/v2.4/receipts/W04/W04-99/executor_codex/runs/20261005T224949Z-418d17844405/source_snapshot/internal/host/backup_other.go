//go:build !windows

package host

import (
	"context"
	"fmt"

	"researchos.local/research-os/internal/domain"
)

func (h *Host) SnapshotWorkspace(context.Context, domain.WorkspaceBinding, string, domain.BackupWorkspaceLimits) (domain.BackupWorkspaceSnapshot, error) {
	return domain.BackupWorkspaceSnapshot{}, fmt.Errorf("BACKUP_WORKSPACE_WINDOWS_REQUIRED")
}

func (h *Host) PinRestoredWorkspace(context.Context, domain.WorkspaceRestoreRequest) (domain.WorkspaceRestorePin, error) {
	return domain.WorkspaceRestorePin{}, fmt.Errorf("RESTORE_WORKSPACE_WINDOWS_REQUIRED")
}
