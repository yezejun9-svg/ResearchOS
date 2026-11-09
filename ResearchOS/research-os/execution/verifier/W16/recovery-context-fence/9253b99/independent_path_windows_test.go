//go:build windows

package domain

import (
    "context"
    "os"
    "path/filepath"
    "testing"
)

func TestIndependentRecoveryContextWriteBeforePathTrust(t *testing.T) {
    f := recoveryStorageSetup(t)
    outside := t.TempDir()
    recoveries := filepath.Join(filepath.Dir(f.state.Data),"release-state","recoveries")
    if err := os.Symlink(outside,recoveries); err != nil { t.Skipf("synthetic directory symlink unavailable: %v",err) }
    _, err := restoreEvolutionCutoverContext(context.Background(),f.state,f.lease,f.contracts,f.policy)
    if err == nil { t.Fatal("aliased recovery path was accepted") }
    created := filepath.Join(outside,f.state.Operation)
    info, statErr := os.Stat(created)
    wrote := statErr == nil && info.IsDir()
    t.Logf("scope=PUBLIC_SYNTHETIC_PATH_ONLY restore_rejected=%v outside_directory_created=%v native_control_private_provider=NOT_RUN",err!=nil,wrote)
    if wrote { t.Error("recovery created its operation directory through an untrusted parent alias before rejecting that path") }
}
