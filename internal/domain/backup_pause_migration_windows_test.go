//go:build windows

package domain

import (
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"researchos.local/research-os/internal/store"
)

// This exercises the public backup/restore implementation with API fixture
// producer evidence. It does not qualify a historical producer executable.
func TestPauseMigrationPublicBackupRehearsalPreservesOriginal(t *testing.T) {
	u, f, run := preparedUpgradePublicFixture(t)
	_, oldSQL, err := preparedUpgradeRelease(u.TargetRoot, 24)
	if err != nil {
		t.Fatal(err)
	}
	oldSchemas, err := preparedUpgradeTemplate(context.Background(), oldSQL, f.s.Contracts)
	if err != nil {
		t.Fatal(err)
	}
	before23, err := preparedUpgradeSnapshot(f.db)
	if err != nil {
		t.Fatal(err)
	}
	if err = preparedUpgradeRehearseDDL(context.Background(), f.db, oldSQL[23], before23, oldSchemas.Source23, oldSchemas.Original24); err != nil {
		t.Fatal(err)
	}
	before, err := preparedUpgradeSnapshot(f.db)
	if err != nil {
		t.Fatal(err)
	}
	u.SourceRoot, u.TargetRoot, u.Plan = u.TargetRoot, pauseMigrationTestRelease(t), PauseSchemaUpgradePlan
	bindings, err := workspaceBackupBindings(f.db)
	if err != nil || len(bindings) != 1 {
		t.Fatal(bindings, err)
	}
	key, err := os.ReadFile(u.KeyFile)
	if err != nil {
		t.Fatal(err)
	}
	defer clear(key)
	manifest, err := f.s.CreateBackupWithWorkspaces(context.Background(), u.Snapshot, key, queueUpgradeWorkspace{bindings[0].RealPath})
	if err != nil {
		t.Fatal(err)
	}
	evidence := t.TempDir()
	u.SourceProgram, u.TargetProgram = filepath.Join(evidence, "old-backup.fixture"), filepath.Join(evidence, "new-control.fixture")
	if err = os.WriteFile(u.SourceProgram, []byte("API fixture source only"), 0600); err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(u.TargetProgram, []byte("API fixture control only"), 0600); err != nil {
		t.Fatal(err)
	}
	current, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	opt := PauseSchemaUpgradeOptions{Upgrade: u, RehearsalProgram: current, HandoffBindingFile: filepath.Join(evidence, "binding.json")}
	programs, err := pauseMigrationProgramHashes(opt, false)
	if err != nil {
		t.Fatal(err)
	}
	pin := func(name string, raw []byte) preparedHandoffFileRef {
		path := filepath.Join(evidence, name)
		if err := os.WriteFile(path, raw, 0600); err != nil {
			t.Fatal(err)
		}
		return preparedHandoffFileRef{Path: path, SHA256: Digest(raw), Bytes: int64(len(raw))}
	}
	manifestRaw, err := os.ReadFile(filepath.Join(u.Snapshot, "manifest.json"))
	if err != nil {
		t.Fatal(err)
	}
	exit := 0
	binding := pauseBackupHandoffBinding{Schema: pauseMigrationHandoffSchema, SourceDatabase: u.Source, BackupDirectory: u.Snapshot,
		SourceProgramSHA256: programs.Source, TargetProgramSHA256: programs.Control, RehearsalProgramSHA256: programs.Rehearsal,
		BackupManifestSHA256: Digest(manifestRaw), BackupManifestBytes: int64(len(manifestRaw)), BackupID: manifest.ID,
		SourceBackupOperation: "create", ObservedBackupExit: &exit,
		ProducerStdout: pin("stdout.json", Bytes(manifest)), ProducerObservation: pin("observation.json", []byte(`{"proof_level":"API_FIXTURE_ONLY"}`))}
	raw := Bytes(binding)
	if err = os.WriteFile(opt.HandoffBindingFile, raw, 0600); err != nil {
		t.Fatal(err)
	}
	opt.HandoffBindingSHA256 = Digest(raw)
	if err = f.db.Close(); err != nil {
		t.Fatal(err)
	}
	report, err := UpgradePauseSchemaBackup(context.Background(), opt)
	if err != nil || report.Status != "RESTORED_RECONCILIATION_REQUIRED" {
		t.Fatal(report, err)
	}
	original, err := store.Open(u.Source)
	if err != nil {
		t.Fatal(err)
	}
	defer original.Close()
	after, err := preparedUpgradeSnapshot(original)
	if err != nil || Hash(after) != Hash(before) {
		t.Fatal("original changed", err)
	}
	if err = preparedUpgradeVersions(original, 24); err != nil {
		t.Fatal(err)
	}
	restored, err := store.Open(filepath.Join(u.Destination, "researchos.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	defer restored.Close()
	if err = preparedUpgradeVersions(restored, 25); err != nil {
		t.Fatal(err)
	}
	var status string
	if err = restored.QueryRow(`SELECT json_extract(body,'$.status') FROM domain_objects WHERE kind='Run' AND id=?`, run["id"]).Scan(&status); err != nil || status != "RECONCILING" {
		t.Fatal(status, err)
	}
	var live int
	if err = restored.QueryRow(`SELECT count(*) FROM auth_credentials WHERE revoked=0`).Scan(&live); err != nil || live != 0 {
		t.Fatal(live, err)
	}
	var receipt pauseMigrationReceipt
	raw, err = os.ReadFile(filepath.Join(u.Destination, pauseMigrationReceiptName))
	if err != nil || json.Unmarshal(raw, &receipt) != nil {
		t.Fatal("receipt", err)
	}
	if !receipt.OriginalUnchanged || !receipt.RollbackVerified || !receipt.NewPauseTablesEmpty || !receipt.ExistingRowsUnchanged || receipt.OriginalRowsHash != Hash(before) || receipt.PostRestoreRowsHash == receipt.OriginalRowsHash || receipt.RestoreDelta["auth_credentials"] == nil || receipt.RestoreDelta["domain_objects"] == nil {
		t.Fatal("restore separation", string(raw))
	}
	afterDDL, err := preparedUpgradeSnapshot(restored)
	if err != nil || receipt.PostDDLRowsHash != Hash(afterDDL) {
		t.Fatal("published copy differs", err)
	}
	if err = backupPauseSchema(restored); err != nil {
		t.Fatal(err)
	}
	for _, table := range []string{"runtime_pause_activations", "runtime_pause_acknowledgements", "runtime_pause_resumptions"} {
		if row, ok := afterDDL[table]; ok && len(row.Rows) != 0 {
			t.Fatal("new pause rows", table)
		}
	}
}
