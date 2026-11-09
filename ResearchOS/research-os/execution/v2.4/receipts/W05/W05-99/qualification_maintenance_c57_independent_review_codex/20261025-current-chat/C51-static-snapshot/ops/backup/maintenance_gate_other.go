//go:build !windows

package main

import (
	"context"
	"errors"

	"researchos.local/research-os/internal/domain"
)

type backupSourceOwner struct{}

var errBackupNative = errors.New("NATIVE_WINDOWS_SOURCE_LEASE_REQUIRED")

func openBackupSourceLease(string) (*backupSourceOwner, error) { return nil, errBackupNative }
func (*backupSourceOwner) Close() error                        { return errBackupNative }
func (*backupSourceOwner) UpgradeLocal(context.Context, domain.LocalUpgradeOptions) (domain.RestoreReport, error) {
	return domain.RestoreReport{Status: "FAILED"}, errBackupNative
}
func (*backupSourceOwner) UpgradePrepared(context.Context, domain.PreparedBackupHandoffOptions) (domain.RestoreReport, error) {
	return domain.RestoreReport{Status: "FAILED"}, errBackupNative
}
