//go:build windows

package domain

import (
	"context"
	"os"
	"path/filepath"
	"testing"

	rt "researchos.local/research-os/adapters/runtime"
)

func TestBackupSourceLeaseSurvivesNormalizedAllPlanDispatch(t *testing.T) {
	base := t.TempDir()
	root := filepath.Join(base, "data")
	if err := os.Mkdir(root, 0700); err != nil {
		t.Fatal(err)
	}
	source := filepath.Join(root, "researchos.sqlite")
	if err := os.WriteFile(source, []byte("disposable source"), 0600); err != nil {
		t.Fatal(err)
	}
	lease, err := rt.AcquireDataRootLease(root)
	if err != nil {
		t.Fatal(err)
	}
	defer lease.Close()
	for _, plan := range []string{LocalUpgradePlan, FinalSchemaUpgradePlan, QueueSchemaUpgradePlan,
		ConfigurationSchemaUpgradePlan, PreparedAbandonmentSchemaUpgradePlan} {
		t.Run(plan, func(t *testing.T) {
			// Each typed plan borrows the same exact native source before the
			// downstream release/key inputs are inspected.
			opt := LocalUpgradeOptions{Plan: plan, Source: root + `\.\researchos.sqlite`}
			if _, err := UpgradeLocalUnderSourceLease(context.Background(), opt, lease); err == nil {
				t.Fatal("incomplete upgrade unexpectedly succeeded")
			}
			if !lease.Held() {
				t.Fatal("inner upgrade released outer data-root owner")
			}
			guard, err := checkedBackupSource(&opt, lease)
			if err != nil {
				t.Fatal(err)
			}
			if err := guard.Check(root, source); err != nil {
				t.Fatal(err)
			}
			if err := os.Rename(source, source+".moved"); err == nil {
				t.Fatal("borrow allowed source identity replacement")
			}
			if err := lease.Close(); err == nil {
				t.Fatal("outer owner closed during source borrow")
			}
			if err := guard.borrow.Release(); err != nil {
				t.Fatal(err)
			}
			if !lease.Held() {
				t.Fatal("borrow release closed outer owner")
			}
		})
	}
}

func TestBackupSourceLeaseNormalizedPathAndRootGuard(t *testing.T) {
	base := t.TempDir()
	root := filepath.Join(base, "data")
	for _, dir := range []string{root, filepath.Join(base, "key"), filepath.Join(base, "source-program"), filepath.Join(base, "target-program"), filepath.Join(base, "source-release"), filepath.Join(base, "target-release")} {
		if err := os.Mkdir(dir, 0700); err != nil {
			t.Fatal(err)
		}
	}
	file := func(path string) string {
		t.Helper()
		if err := os.WriteFile(path, []byte("disposable"), 0600); err != nil {
			t.Fatal(err)
		}
		return path
	}
	source := file(filepath.Join(root, "researchos.sqlite"))
	opt := LocalUpgradeOptions{Source: root + `\.\researchos.sqlite`,
		KeyFile:    file(filepath.Join(base, "key", "key.bin")),
		SourceRoot: filepath.Join(base, "source-release"), TargetRoot: filepath.Join(base, "target-release"),
		SourceProgram: file(filepath.Join(base, "source-program", "old.exe")),
		TargetProgram: file(filepath.Join(base, "target-program", "new.exe")),
		Snapshot:      filepath.Join(base, "snapshot"), Destination: filepath.Join(base, "destination")}
	lease, err := rt.AcquireDataRootLease(root)
	if err != nil {
		t.Fatal(err)
	}
	defer lease.Close()
	guard, err := checkedBackupSource(&opt, lease)
	if err != nil {
		t.Fatal(err)
	}
	defer guard.borrow.Release()
	if err := upgradePaths(&opt); err != nil || opt.Source != source {
		t.Fatalf("normalized guarded source: %q %v", opt.Source, err)
	}
	other := filepath.Join(base, "other")
	if err := os.Mkdir(other, 0700); err != nil {
		t.Fatal(err)
	}
	opt.Source = file(filepath.Join(other, "researchos.sqlite"))
	if err := upgradePaths(&opt); err == nil {
		t.Fatal("common normalized upgradePaths admitted a different source")
	}
}

func TestPreparedNestedSourceLeaseCloseKeepsOuterNativeOwner(t *testing.T) {
	root := t.TempDir()
	source := filepath.Join(root, "researchos.sqlite")
	if err := os.WriteFile(source, []byte("disposable source"), 0600); err != nil {
		t.Fatal(err)
	}
	lease, err := rt.AcquireDataRootLease(root)
	if err != nil {
		t.Fatal(err)
	}
	defer lease.Close()
	opt := LocalUpgradeOptions{Source: source}
	guard, err := checkedBackupSource(&opt, lease)
	if err != nil {
		t.Fatal(err)
	}
	defer guard.borrow.Release()
	for _, branch := range []string{"prepared-local", "prepared-handoff"} {
		t.Run(branch, func(t *testing.T) {
			inner, err := acquirePreparedUpgradeRootLease(guard.root, guard.source, guard)
			if err != nil || inner.Check() != nil {
				t.Fatalf("inherited prepared lease: %v", err)
			}
			if err := inner.Close(); err != nil {
				t.Fatal(err)
			}
			if inner.Check() == nil {
				t.Fatal("closed inner prepared lease remained valid")
			}
			if !lease.Held() || guard.Check(guard.root, guard.source) != nil {
				t.Fatal("inner prepared Close released outer native source owner")
			}
			if err := os.Rename(source, source+".moved"); err == nil {
				t.Fatal("inner prepared Close released native source guard")
			}
		})
	}
}
