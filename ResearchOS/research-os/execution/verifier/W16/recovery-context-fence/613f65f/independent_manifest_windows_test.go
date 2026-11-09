//go:build windows

package domain

import (
    "os"
    "path/filepath"
    "testing"

    "researchos.local/research-os/ops/supervisor"
)

// Uses only this change's public synthetic encrypted-backup fixture.
func TestIndependentRecoveryContextManifestBytes(t *testing.T) {
    f := recoveryStorageSetup(t)
    r := f.restore(t)
    if _, err := supervisor.ValidateReleaseRestoreResult(f.state,r); err != nil { t.Fatal(err) }
    manifest := filepath.Join(f.state.Cutover.Directory,"manifest.json")
    original, err := os.ReadFile(manifest)
    if err != nil { t.Fatal(err) }
    for _, change := range []struct{name string; raw []byte}{
        {"reencoded",append([]byte("\n  "),original...)},
        {"invalid",[]byte("{}\n")},
    } {
        t.Run(change.name,func(t *testing.T) {
            if err := os.WriteFile(manifest,change.raw,0600); err != nil { t.Fatal(err) }
            _, err := supervisor.ValidateReleaseRestoreResult(f.state,r)
            if err == nil { t.Error("changed persisted source manifest was accepted by ValidateReleaseRestoreResult") }
            t.Logf("scope=PUBLIC_SYNTHETIC_STORAGE_ONLY manifest_raw_changed=%v validation_rejected=%v native_private_provider=NOT_RUN",Digest(change.raw)!=Digest(original),err!=nil)
        })
    }
}
