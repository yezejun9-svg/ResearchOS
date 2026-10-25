//go:build windows

package main

import (
	"context"
	"errors"
	"os"
	"path/filepath"
	"strings"

	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/internal/domain"
	hostboundary "researchos.local/research-os/internal/host"
)

type backupSourceOwner struct{ native *rt.DataRootLease }

func openBackupSourceLease(source string) (*backupSourceOwner, error) {
	if source == "" || strings.ContainsAny(source, "?\x00") {
		return nil, errors.New("BACKUP_SOURCE_PATH_REQUIRED")
	}
	abs, err := filepath.Abs(source)
	if err != nil {
		return nil, err
	}
	if filepath.Base(abs) != "researchos.sqlite" {
		return nil, errors.New("BACKUP_SOURCE_DATABASE_NAME")
	}
	info, err := os.Lstat(abs)
	if err != nil || !info.Mode().IsRegular() {
		return nil, errors.New("BACKUP_SOURCE_REGULAR_FILE_REQUIRED")
	}
	root := filepath.Dir(abs)
	lease, err := rt.AcquireDataRootLease(root)
	if err != nil {
		return nil, err
	}
	if err := lease.CheckMaintenanceReady(abs); err != nil {
		_ = lease.Close()
		return nil, err
	}
	if err := hostboundary.RuntimeVerifierReplacementStartupGate(lease); err != nil {
		_ = lease.Close()
		return nil, err
	}
	return &backupSourceOwner{native: lease}, nil
}

func (o *backupSourceOwner) Close() error {
	if o == nil || o.native == nil {
		return errors.New("BACKUP_SOURCE_LEASE_REQUIRED")
	}
	return o.native.Close()
}

func (o *backupSourceOwner) UpgradeLocal(ctx context.Context, opt domain.LocalUpgradeOptions) (domain.RestoreReport, error) {
	if o == nil {
		return domain.RestoreReport{Status: "FAILED"}, errors.New("BACKUP_SOURCE_LEASE_REQUIRED")
	}
	return domain.UpgradeLocalUnderSourceLease(ctx, opt, o.native)
}

func (o *backupSourceOwner) UpgradePrepared(ctx context.Context, opt domain.PreparedBackupHandoffOptions) (domain.RestoreReport, error) {
	if o == nil {
		return domain.RestoreReport{Status: "FAILED"}, errors.New("BACKUP_SOURCE_LEASE_REQUIRED")
	}
	return domain.UpgradePreparedAbandonmentBackupUnderSourceLease(ctx, opt, o.native)
}
