package domain

import (
	"os"
	"path/filepath"
	"testing"
)

func TestPauseHandoffMetadataSeparatesThreePrograms(t *testing.T) {
	programs := pauseMigrationPrograms{Digest([]byte("source24")), Digest([]byte("control25")), Digest([]byte("backup25"))}
	zero := 0
	manifest := BackupManifest{ID: "fixture-backup", Format: "RESEARCHOS_BACKUP_V1", Migrations: upgradeVersions(24)}
	valid := pauseBackupHandoffBinding{Schema: pauseMigrationHandoffSchema, SourceBackupOperation: "create", ObservedBackupExit: &zero,
		BackupID: manifest.ID, SourceProgramSHA256: programs.Source, TargetProgramSHA256: programs.Control, RehearsalProgramSHA256: programs.Rehearsal}
	if err := pauseHandoffMetadata(valid, programs, manifest, manifest); err != nil {
		t.Fatal(err)
	}
	for _, mutation := range []string{"old-schema", "old-version", "future-version", "missing-exit", "failed-exit", "wrong-operation", "same-targets", "swapped-targets", "wrong-stdout", "purpose"} {
		t.Run(mutation, func(t *testing.T) {
			b, p, m, stdout := valid, programs, manifest, manifest
			switch mutation {
			case "old-schema":
				b.Schema = preparedPublicHandoffSchema
			case "old-version":
				m.Migrations = upgradeVersions(23)
			case "future-version":
				m.Migrations = upgradeVersions(25)
			case "missing-exit":
				b.ObservedBackupExit = nil
			case "failed-exit":
				one := 1
				b.ObservedBackupExit = &one
			case "wrong-operation":
				b.SourceBackupOperation = "upgrade-local"
			case "same-targets":
				p.Rehearsal, b.RehearsalProgramSHA256 = p.Control, p.Control
			case "swapped-targets":
				p.Control, p.Rehearsal = p.Rehearsal, p.Control
			case "wrong-stdout":
				stdout.ID = "other"
			case "purpose":
				m.Purpose = Object{"kind": "local-upgrade"}
			}
			if err := pauseHandoffMetadata(b, p, m, stdout); err == nil {
				t.Fatal("invalid handoff accepted", mutation)
			}
		})
	}
}

func TestPauseHandoffCurrentExecutableHasOneRole(t *testing.T) {
	current, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	root := t.TempDir()
	source, control := filepath.Join(root, "source24.fixture"), filepath.Join(root, "control25.fixture")
	if err = os.WriteFile(source, []byte("distinct source metadata only"), 0600); err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(control, []byte("distinct control metadata only"), 0600); err != nil {
		t.Fatal(err)
	}
	opt := PauseSchemaUpgradeOptions{Upgrade: LocalUpgradeOptions{SourceProgram: source, TargetProgram: control}, RehearsalProgram: current}
	if _, err = pauseMigrationProgramHashes(opt, false); err != nil {
		t.Fatal("current rehearsal identity rejected", err)
	}
	if _, err = pauseMigrationProgramHashes(opt, true); err == nil {
		t.Fatal("rehearsal program relabelled as control")
	}
}

func TestPauseHandoffRetainsOrdinaryPolicyAndStrictJSON(t *testing.T) {
	if !backupOrdinaryPublicPolicy(&backupPolicy{publicPauseUpgradeHandoff: true, format: "RESEARCHOS_BACKUP_V1"}) {
		t.Fatal("ordinary public backup validation lost")
	}
	for _, raw := range []string{`{"unexpected":true}`, `{} {}`} {
		var options PauseSchemaUpgradeOptions
		if err := pauseMigrationDecode([]byte(raw), &options); err == nil {
			t.Fatal("loose options accepted", raw)
		}
	}
}
