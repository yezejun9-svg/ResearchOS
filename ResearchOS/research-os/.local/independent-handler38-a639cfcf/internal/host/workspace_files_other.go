//go:build !windows

package host

import (
	"context"
	"errors"

	"researchos.local/research-os/internal/domain"
)

var errWorkspaceFilesUnsupported = errors.New("HOST_UNAVAILABLE: pinned workspace file access requires Windows")

func (h *Host) WorkspaceTree(context.Context, string, string, domain.Object) (domain.Object, error) {
	return nil, errWorkspaceFilesUnsupported
}

func (h *Host) WorkspaceRead(context.Context, string, string, domain.Object) (domain.Object, error) {
	return nil, errWorkspaceFilesUnsupported
}

func (h *Host) WorkspaceContent(context.Context, string, string, string, int64) ([]byte, error) {
	return nil, errWorkspaceFilesUnsupported
}

func (h *Host) WorkspaceDiff(context.Context, string, string, domain.Object) (domain.Object, []byte, error) {
	return nil, nil, errWorkspaceFilesUnsupported
}
