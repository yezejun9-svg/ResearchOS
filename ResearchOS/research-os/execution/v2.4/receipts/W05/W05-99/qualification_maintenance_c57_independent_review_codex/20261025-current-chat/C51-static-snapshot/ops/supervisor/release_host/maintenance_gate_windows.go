//go:build windows

package main

import (
	"errors"
	"os"
	"path/filepath"

	rt "researchos.local/research-os/adapters/runtime"
	hostboundary "researchos.local/research-os/internal/host"
)

func openReleaseHostSourceLease(database string) (*rt.DataRootLease, error) {
	if !filepath.IsAbs(database) || filepath.Clean(database) != database ||
		filepath.Base(database) != "researchos.sqlite" {
		return nil, errors.New("RELEASE_HOST_FIXTURE_DATABASE_REQUIRED")
	}
	info, err := os.Lstat(database)
	if err != nil || !info.Mode().IsRegular() {
		return nil, errors.New("RELEASE_HOST_EXISTING_DATABASE_REQUIRED")
	}
	lease, err := rt.AcquireDataRootLease(filepath.Dir(database))
	if err != nil {
		return nil, err
	}
	if err := lease.CheckMaintenanceReady(database); err != nil {
		_ = lease.Close()
		return nil, err
	}
	if err := hostboundary.RuntimeVerifierReplacementStartupGate(lease); err != nil {
		_ = lease.Close()
		return nil, err
	}
	return lease, nil
}
