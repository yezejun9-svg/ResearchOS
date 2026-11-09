//go:build !windows

package domain

import "fmt"

type preparedUpgradeRootLease struct{}

func acquirePreparedUpgradeRootLease(string) (*preparedUpgradeRootLease, error) {
	return nil, fmt.Errorf("PREPARED_UPGRADE_NATIVE_WINDOWS_LEASE_REQUIRED")
}
func (*preparedUpgradeRootLease) Check() error {
	return fmt.Errorf("PREPARED_UPGRADE_NATIVE_WINDOWS_LEASE_REQUIRED")
}
func (*preparedUpgradeRootLease) Close() error { return nil }
