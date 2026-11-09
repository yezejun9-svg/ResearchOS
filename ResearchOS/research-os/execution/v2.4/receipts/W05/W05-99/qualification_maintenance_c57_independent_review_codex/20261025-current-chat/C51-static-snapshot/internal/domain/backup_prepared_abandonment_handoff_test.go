package domain

// New boundary tests are source only in this handoff. These metadata fixtures
// neither execute old/current binaries nor prove historical producer identity.
import (
    "strings"
    "testing"
)

func preparedHandoffMetadataFixture() (preparedBackupHandoffBinding, string, string, BackupManifest) {
    source, target := Digest([]byte("metadata-old")), Digest([]byte("metadata-new"))
    zero := 0
    m := BackupManifest{ID: "metadata-backup", Format: "RESEARCHOS_BACKUP_V1", Migrations: upgradeVersions(23)}
    b := preparedBackupHandoffBinding{Schema: preparedPublicHandoffSchema,
        SourceBackupOperation: "create", ObservedBackupExit: &zero, BackupID: m.ID,
        SourceProgramSHA256: source, TargetProgramSHA256: target}
    return b, source, target, m
}

func TestPreparedHandoffMetadataRequiresDistinctObservedPrograms(t *testing.T) {
    tests := []struct {
        name string
        mutate func(*preparedBackupHandoffBinding, *string, *string, *BackupManifest, *BackupManifest)
        want string
    }{
        {"missing-exit", func(b *preparedBackupHandoffBinding, _, _ *string, _, _ *BackupManifest) { b.ObservedBackupExit = nil }, "OBSERVATION_REQUIRED"},
        {"failed-exit", func(b *preparedBackupHandoffBinding, _, _ *string, _, _ *BackupManifest) { one := 1; b.ObservedBackupExit = &one }, "OBSERVATION_REQUIRED"},
        {"wrong-operation", func(b *preparedBackupHandoffBinding, _, _ *string, _, _ *BackupManifest) { b.SourceBackupOperation = "upgrade-local" }, "OBSERVATION_REQUIRED"},
        {"wrong-schema", func(b *preparedBackupHandoffBinding, _, _ *string, _, _ *BackupManifest) { b.Schema = "other" }, "OBSERVATION_REQUIRED"},
        {"same-binary", func(b *preparedBackupHandoffBinding, source, target *string, _, _ *BackupManifest) { *target = *source; b.TargetProgramSHA256 = *source }, "DISTINCT_PROGRAM_PINS"},
        {"swapped-program", func(_ *preparedBackupHandoffBinding, source, target *string, _, _ *BackupManifest) { *source, *target = *target, *source }, "DISTINCT_PROGRAM_PINS"},
        {"malformed-digest", func(b *preparedBackupHandoffBinding, source, _ *string, _, _ *BackupManifest) { *source = "sha256:short"; b.SourceProgramSHA256 = *source }, "DISTINCT_PROGRAM_PINS"},
        {"wrong-backup", func(b *preparedBackupHandoffBinding, _, _ *string, _, _ *BackupManifest) { b.BackupID = "other" }, "BACKUP_IDENTITY"},
        {"schema22", func(_ *preparedBackupHandoffBinding, _, _ *string, m, out *BackupManifest) { m.Migrations = upgradeVersions(22); *out = *m }, "BACKUP_IDENTITY"},
        {"local-upgrade-format", func(_ *preparedBackupHandoffBinding, _, _ *string, m, out *BackupManifest) { m.Format = localUpgradeFormat; *out = *m }, "BACKUP_IDENTITY"},
        {"purpose-injection", func(_ *preparedBackupHandoffBinding, _, _ *string, m, out *BackupManifest) { m.Purpose = Object{"plan": "other"}; *out = *m }, "BACKUP_IDENTITY"},
        {"wrong-stdout", func(_ *preparedBackupHandoffBinding, _, _ *string, _ *BackupManifest, out *BackupManifest) { out.ID = "another-output" }, "PRODUCER_STDOUT_MISMATCH"},
    }
    for _, test := range tests {
        t.Run(test.name, func(t *testing.T) {
            b, source, target, m := preparedHandoffMetadataFixture()
            out := m
            test.mutate(&b, &source, &target, &m, &out)
            err := preparedHandoffMetadata(b, source, target, m, out)
            if err == nil || !strings.Contains(err.Error(), test.want) { t.Fatalf("got %v; want refusal %s", err, test.want) }
        })
    }
    b, source, target, m := preparedHandoffMetadataFixture()
    if err := preparedHandoffMetadata(b, source, target, m, m); err != nil { t.Fatal(err) }
}

func TestPreparedHandoffKeepsOrdinaryPublicBackupPolicy(t *testing.T) {
    if !backupOrdinaryPublicPolicy(nil) { t.Fatal("ordinary backup lost public checks") }
    if backupOrdinaryPublicPolicy(&backupPolicy{format: localUpgradeFormat}) { t.Fatal("old local policy changed") }
    if !backupOrdinaryPublicPolicy(&backupPolicy{format: "RESEARCHOS_BACKUP_V1", publicPreparedAbandonmentHandoff: true}) {
        t.Fatal("handoff must require portable and queue sidecar validation")
    }
}

func TestPreparedHandoffDigestRequiresCompleteLowercaseSHA256(t *testing.T) {
    for _, value := range []string{"", strings.Repeat("0", 64), "sha256:"+strings.Repeat("0", 63),
        "sha256:"+strings.Repeat("0", 65), "sha256:"+strings.Repeat("G", 64), "sha256:"+strings.Repeat("A", 64)} {
        if preparedHandoffDigest(value) { t.Fatalf("accepted malformed pin %q", value) }
    }
    if !preparedHandoffDigest(Digest([]byte("pin"))) { t.Fatal("valid pin rejected") }
}

