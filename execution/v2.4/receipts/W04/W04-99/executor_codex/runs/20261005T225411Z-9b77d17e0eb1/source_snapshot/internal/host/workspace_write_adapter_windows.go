//go:build windows

package host

import (
	"context"
	"researchos.local/research-os/internal/domain"
)

func (h *Host) WorkspaceWrite(ctx context.Context, in domain.ClientWorkspaceWriteInput) (domain.ClientWorkspaceWriteResult, error) {
	var result domain.ClientWorkspaceWriteResult
	if in.Access != AccessReadWrite || in.Revalidate == nil || in.IntentKey == "" || in.ScopeHash == "" {
		return result, toolDenied("current bound workspace write authority required")
	}
	binding, root, err := h.workspaceRoot(in.WorkspacePath, in.Access)
	if err != nil {
		return result, err
	}
	defer root.Close()
	rel, err := workspaceRelativePath(in.RelativePath, false)
	if err != nil {
		return result, err
	}
	proof, err := WriteWorkspaceFile(ctx, WorkspaceWriteInput{Root: root, RootPath: binding.RealPath, JournalRoot: h.dir, RelativePath: rel, IntentKey: in.IntentKey, ScopeHash: in.ScopeHash, ExpectedHash: in.ExpectedHash, CreateIfMissing: in.CreateIfMissing, Content: in.Content,
		Revalidate: func(checkCtx context.Context) error {
			if _, e := h.ResolveWorkspace(binding.Ref, rel, AccessReadWrite); e != nil {
				return e
			}
			return in.Revalidate(checkCtx)
		}})
	if err != nil {
		return result, err
	}
	if proof.BeforeHash != "" {
		result.BeforeHash = &proof.BeforeHash
	}
	result.AfterHash = proof.AfterHash
	return result, nil
}
