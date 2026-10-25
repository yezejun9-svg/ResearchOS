//go:build !windows

package domain

import (
	"context"
	"errors"
)

type backupSourceLease struct{}

func (*backupSourceLease) Check(string, string) error {
	return errors.New("NATIVE_WINDOWS_SOURCE_LEASE_REQUIRED")
}

func UpgradeLocalUnderSourceLease(context.Context, LocalUpgradeOptions, any) (RestoreReport, error) {
	return RestoreReport{Status: "FAILED"}, errors.New("NATIVE_WINDOWS_SOURCE_LEASE_REQUIRED")
}

func UpgradePreparedAbandonmentBackupUnderSourceLease(context.Context, PreparedBackupHandoffOptions, any) (RestoreReport, error) {
	return RestoreReport{Status: "FAILED"}, errors.New("NATIVE_WINDOWS_SOURCE_LEASE_REQUIRED")
}

func runGuardedUpgradeFixture(context.Context, LocalUpgradeOptions) (RestoreReport, error) {
	return RestoreReport{Status: "FAILED"}, errors.New("NATIVE_WINDOWS_SOURCE_LEASE_REQUIRED")
}
