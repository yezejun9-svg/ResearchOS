// Package localworkspace adapts the trusted local host boundary (internal/host) to the domain
// ports that workspace.register and project.bootstrap need (internal/domain). The domain cannot
// import the host - the host already imports the domain - so this package is the wiring a
// composition root installs, and it is also where the local directory is actually read.
//
// Nothing here mints an authorization. It only answers the domain's questions with what the OS and
// the host's own protected state already decided: which selection references are still single-use
// and unexpired, which directory a reference resolved to, and whether a bound root is still the
// same pinned object on the same volume.
package localworkspace

import (
	"context"
	"errors"
	"fmt"
	"path/filepath"

	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/host"
)

// Authority satisfies domain.WorkspaceAuthority over one host instance.
type Authority struct{ h *host.Host }

// NewAuthority binds the adapter to a host that has already verified the local OS principal.
func NewAuthority(h *host.Host) *Authority { return &Authority{h: h} }

// HostPrincipalRef exposes the verified local principal the selections are bound to, so a receipt
// can name the authority without revealing the raw SID.
func (a *Authority) HostPrincipalRef() string { return a.h.Identity().Ref }

// ConsumeSelection redeems a single-use selection reference through the host. The host checks the
// principal reference and the client identity itself, so a reference issued to another client of
// the same OS user is refused with the same error a replay would get.
func (a *Authority) ConsumeSelection(ctx context.Context, selectionRef, clientID, principalID string) (domain.WorkspaceSelection, error) {
	if a == nil || a.h == nil {
		return domain.WorkspaceSelection{}, errors.New("POLICY_DENIED: host authority is not installed")
	}
	if principalID == "" {
		return domain.WorkspaceSelection{}, fmt.Errorf("FORBIDDEN: a domain principal must be attributed to the choice")
	}
	rec, err := a.h.ConsumeSelection(selectionRef, clientID)
	if err != nil {
		return domain.WorkspaceSelection{}, err
	}
	return domain.WorkspaceSelection{RealPath: rec.RealPath, DisplayPath: rec.DisplayPath, Access: rec.Access,
		HostPrincipalRef: rec.PrincipalRef, ClientID: rec.ClientID}, nil
}

// ConfirmPath asks the host whether the directory is still an authorized, live, in-scope root.
// The probe is a relative path under the binding, which makes the host re-run its own per-access
// checks: revoked state, access containment, the pinned volume serial plus file index, and the
// reparse chain. A directory that was swapped underneath us therefore fails here rather than
// being accepted because it once registered successfully.
func (a *Authority) ConfirmPath(ctx context.Context, realPath, wantAccess string) error {
	if a == nil || a.h == nil {
		return errors.New("POLICY_DENIED: host authority is not installed")
	}
	if realPath == "" {
		return fmt.Errorf("PATH_OUT_OF_SCOPE: no directory to confirm")
	}
	want := host.AccessReadOnly
	if wantAccess == host.AccessReadWrite {
		want = host.AccessReadWrite
	}
	have := 0
	for _, r := range a.h.Roots() {
		if r.Revoked || samePath(r.RealPath, realPath) == false {
			if r.Revoked && samePath(r.RealPath, realPath) {
				have++ // an authorised-but-revoked root must never be treated as "no such directory"
			}
			continue
		}
		have++
		if want == host.AccessReadWrite && r.Access != host.AccessReadWrite {
			return fmt.Errorf("PATH_OUT_OF_SCOPE: the bound directory is read-only")
		}
		if _, err := a.h.ResolveWorkspace(r.Ref, workspaceProbePath, host.AccessReadOnly); err != nil {
			return err
		}
		return nil
	}
	if have > 0 {
		return fmt.Errorf("WORKSPACE_REVOKED: the authorized directory is revoked")
	}
	return fmt.Errorf("PATH_OUT_OF_SCOPE: no authorized root covers this directory")
}

// workspaceProbePath is a relative child that cannot exist. ResolveWorkspace never requires the
// child to be present; it validates scope, pinning and the reparse chain, which is exactly the
// confirmation this adapter needs before the domain mints or uses a reference.
const workspaceProbePath = ".researchos-authorization-probe"

func samePath(a, b string) bool {
	return filepath.Clean(a) == filepath.Clean(b)
}

var _ domain.WorkspaceAuthority = (*Authority)(nil)
