//go:build windows

package supervisor

import (
    "path/filepath"
    "testing"
)

// Public synthetic journal state only; no executable or restore operation runs.
func TestIndependentRecoveryContextStateAlias(t *testing.T) {
    j, s := recoveryJournalFixture(t)
    directory, destination, err := RestoreContextPaths(s)
    if err != nil { t.Fatal(err) }
    original := releaseHash("original public context reference")
    s.Phase = "RECOVERING"
    s.RestoreContext = &ReleaseRestoreResult{Operation:s.Operation, Epoch:s.Epoch, SourceRoot:s.Data, Destination:destination, ContextPath:filepath.Join(directory,"context.json"), ContextSHA256:original, ManifestSHA256:s.Cutover.ManifestSHA256}
    if err = j.Append(s); err != nil { t.Fatal(err) }
    next := j.State()
    next.RestoreContext.ContextSHA256 = releaseHash("changed public context reference")
    if j.State().RestoreContext.ContextSHA256 != original {
        t.Error("State() leaked mutable RestoreContext alias: caller changed the committed in-memory reference without Append")
    }
    err = j.Append(next)
    if err == nil {
        t.Error("Append accepted replacement of the supposedly immutable bound context through a State() alias")
    }
    t.Logf("scope=PUBLIC_SYNTHETIC_JOURNAL_ONLY append_rejected=%v native_private_provider=NOT_RUN",err!=nil)
}
