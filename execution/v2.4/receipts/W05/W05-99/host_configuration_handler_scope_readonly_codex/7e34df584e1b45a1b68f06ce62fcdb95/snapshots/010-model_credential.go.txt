//go:build windows

package host

import (
	"context"
	"errors"

	"researchos.local/research-os/internal/domain"
)

// ModelCredential is installed only into the trusted coordinator. It is never
// reachable through either native or ordinary client protocol dispatch.
func (h *Host) ModelCredential(ctx context.Context, route domain.RuntimeProviderRoute) ([]byte, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	if route.CredentialRef == "" || route.CredentialRevision != route.CredentialRef {
		return nil, ErrUnknownCredential
	}
	record, err := h.vault.record(route.CredentialRef)
	if err != nil {
		return nil, err
	}
	if record.Revoked || record.Provider != domain.Str(route.ModelConfig, "provider") {
		return nil, errors.New("model credential provider or revision differs from protected record")
	}
	return h.openCredentialForProvider(route.CredentialRef)
}
