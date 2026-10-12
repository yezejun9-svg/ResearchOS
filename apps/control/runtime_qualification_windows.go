//go:build windows

package main

import (
	"context"
	"errors"
	"log"
	"time"

	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/host"
)

// This is a managed startup component. Its privileged Desktop producer is a
// separate integration; the renderer never receives a token or an ad-hoc RPC.
type managedLocalQualification struct {
	request      domain.LocalRuntimeQualificationRequest
	installation host.RuntimeVerifierInstallation
}

func readManagedLocalQualification(requestFile, manifestFile string) (*managedLocalQualification, error) {
	if requestFile == "" && manifestFile == "" {
		return nil, nil
	}
	if requestFile == "" || manifestFile == "" {
		return nil, errors.New("managed qualification request and installed verifier manifest must be supplied together")
	}
	r, e := host.LoadLocalRuntimeQualificationRequest(requestFile)
	if e != nil {
		return nil, e
	}
	i, e := host.LoadRuntimeVerifierInstallation(manifestFile)
	if e != nil {
		return nil, e
	}
	return &managedLocalQualification{request: r, installation: i}, nil
}
func (m *managedLocalQualification) run(ctx context.Context, h *host.Host, s *domain.Service, c *domain.RuntimeCoordinator, apiURL string) error {
	deadline, cancel := context.WithTimeout(ctx, 3*time.Minute)
	defer cancel()
	// Offline preparation is explicitly shared with the normal coordinator.
	// It starts no qualification by itself; the frozen request is checked next.
	if e := c.Scan(deadline); e != nil {
		return e
	}
	result, e := h.QualifyLocalRuntime(deadline, s, c, apiURL, m.request, m.installation)
	if e != nil {
		return e
	}
	log.Printf("managed local qualification completed: state=%s runtime=%s purpose=mu_turn application_separation=true protected_holdout=false", domain.Str(result, "state"), m.request.RuntimeID)
	return nil
}
