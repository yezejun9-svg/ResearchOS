//go:build windows

package domain

import (
	"context"
	"fmt"
	"path/filepath"
	"strings"

	"researchos.local/research-os/adapters/protectedstore"
	runtimeadapter "researchos.local/research-os/adapters/runtime"
)

type backupSourceLease struct {
	borrow       *runtimeadapter.DataRootSourceBorrow
	root, source string
}

func (l *backupSourceLease) Check(root, source string) error {
	if l == nil || l.borrow == nil || !strings.EqualFold(l.root, root) ||
		!strings.EqualFold(l.source, source) || !strings.EqualFold(filepath.Dir(source), root) {
		return fmt.Errorf("UPGRADE_SOURCE_LEASE_IDENTITY")
	}
	return l.borrow.Check(source)
}

func checkedBackupSource(opt *LocalUpgradeOptions, lease *runtimeadapter.DataRootLease) (*backupSourceLease, error) {
	if lease == nil {
		return nil, fmt.Errorf("UPGRADE_SOURCE_LEASE_REQUIRED")
	}
	source, err := upgradePath(opt.Source, true)
	if err != nil {
		return nil, err
	}
	opt.Source = source
	root := filepath.Dir(source)
	borrow, err := lease.BorrowMaintenanceSource(source)
	if err != nil {
		return nil, err
	}
	guard := &backupSourceLease{borrow: borrow, root: root, source: source}
	if err := guard.Check(root, source); err != nil {
		_ = borrow.Release()
		return nil, err
	}
	opt.sourceLease = guard
	return guard, nil
}

func concreteUpgradeVerifier() upgradeVerifier {
	return upgradeVerifier{
		provider: &protectedstore.FrozenProvider{},
		summary: func(ctx context.Context) (protectedstore.SafeSummary, error) {
			if err := ctx.Err(); err != nil {
				return protectedstore.SafeSummary{}, err
			}
			return protectedstore.QueryFrozenService("aggregate")
		},
	}
}

func UpgradeLocalUnderSourceLease(ctx context.Context, opt LocalUpgradeOptions, lease *runtimeadapter.DataRootLease) (report RestoreReport, err error) {
	report = RestoreReport{Status: "FAILED"}
	switch opt.Plan {
	case LocalUpgradePlan, FinalSchemaUpgradePlan, QueueSchemaUpgradePlan,
		ConfigurationSchemaUpgradePlan, PreparedAbandonmentSchemaUpgradePlan:
	default:
		return report, fmt.Errorf("UPGRADE_PLAN_UNSUPPORTED")
	}
	guard, err := checkedBackupSource(&opt, lease)
	if err != nil {
		return report, err
	}
	defer func() {
		if releaseErr := guard.borrow.Release(); err == nil && releaseErr != nil {
			err = releaseErr
		}
	}()
	return upgradeLocal(ctx, opt, concreteUpgradeVerifier())
}

func UpgradePreparedAbandonmentBackupUnderSourceLease(ctx context.Context, handoff PreparedBackupHandoffOptions, lease *runtimeadapter.DataRootLease) (report RestoreReport, err error) {
	report = RestoreReport{Status: "FAILED"}
	if handoff.Upgrade.Plan != PreparedAbandonmentSchemaUpgradePlan {
		return report, fmt.Errorf("PREPARED_UPGRADE_PLAN_UNSUPPORTED")
	}
	guard, err := checkedBackupSource(&handoff.Upgrade, lease)
	if err != nil {
		return report, err
	}
	defer func() {
		if releaseErr := guard.borrow.Release(); err == nil && releaseErr != nil {
			err = releaseErr
		}
	}()
	return upgradePreparedAbandonmentBackup(ctx, handoff, preparedUpgradeConcreteVerifier())
}

// Package-private fixture driver. Production callers supply their own held
// outer lease to the typed adapter; this helper is used by historical tests.
func runGuardedUpgradeFixture(ctx context.Context, opt LocalUpgradeOptions) (report RestoreReport, err error) {
	lease, err := runtimeadapter.AcquireDataRootLease(filepath.Dir(opt.Source))
	if err != nil {
		return RestoreReport{Status: "FAILED"}, err
	}
	defer func() {
		if closeErr := lease.Close(); err == nil && closeErr != nil {
			err = closeErr
		}
	}()
	return UpgradeLocalUnderSourceLease(ctx, opt, lease)
}
