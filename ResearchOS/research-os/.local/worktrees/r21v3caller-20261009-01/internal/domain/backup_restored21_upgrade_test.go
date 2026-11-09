package domain

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"

	"researchos.local/research-os/internal/store"
)

// Public fixture construction follows the accepted H20 UpgradeLocal path.
// Program bytes remain fixture bytes, not a genuine historical release proof.
func restored21ReleaseFixture(t *testing.T, count int) string {
	t.Helper()
	root := upgradeTestRelease(t, 20)
	names := []string{"0021_research_pending_windows.sql", "next_v24_sessions.sql"}
	if count == 22 {
		names = append(names, "0022_client_command_queue.sql")
	}
	for _, name := range names {
		raw, err := os.ReadFile(filepath.Join("../../migrations/sqlite", name))
		if err != nil {
			t.Fatal(err)
		}
		if err = os.WriteFile(filepath.Join(root, "migrations/sqlite", name), raw, 0600); err != nil {
			t.Fatal(err)
		}
	}
	return root
}
func restored21Fixture(t *testing.T) (LocalUpgradeOptions, upgradeData) {
	t.Helper()
	prior, _ := history20Fixture(t)
	if _, err := UpgradeLocal(context.Background(), prior); err != nil {
		t.Fatal(err)
	}
	base := t.TempDir()
	opt := LocalUpgradeOptions{Source: filepath.Join(prior.Destination, "researchos.sqlite"), Snapshot: filepath.Join(base, "snapshot"), Destination: filepath.Join(base, "candidate"), KeyFile: prior.KeyFile, SourceRoot: restored21ReleaseFixture(t, 21), TargetRoot: restored21ReleaseFixture(t, 22), SourceProgram: prior.TargetProgram, TargetProgram: filepath.Join(base, "target.program"), Plan: Restored21SessionUpgradePlan}
	if err := os.WriteFile(opt.TargetProgram, []byte("PUBLIC_FIXTURE_MAINTENANCE22_PROGRAM_BYTES"), 0600); err != nil {
		t.Fatal(err)
	}
	before := history20Rows(t, opt.Source)
	if len(before["schema_migrations"]) != 21 {
		t.Fatal("H20 output not schema21")
	}
	if _, ok := before["client_sessions"]; ok {
		t.Fatal("H20 installed sessions")
	}
	return opt, before
}
func restored21FixtureProfiles(t *testing.T, opt LocalUpgradeOptions) ([][]byte, string, string, string) {
	t.Helper()
	_, sqls, err := upgradeQueueRelease(opt.TargetRoot, 22)
	if err != nil {
		t.Fatal(err)
	}
	contracts, err := LoadContracts(filepath.Join(opt.TargetRoot, "spec/v2.0/contracts"))
	if err != nil {
		t.Fatal(err)
	}
	a, b, c, err := upgradeRestored21Template(context.Background(), sqls, contracts)
	if err != nil {
		t.Fatal(err)
	}
	return sqls, a, b, c
}
func restored21Open(t *testing.T, path string) *sql.DB {
	t.Helper()
	db, err := store.Open(path)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { db.Close() })
	return db
}
func restored21AssertUnpublished(t *testing.T, opt LocalUpgradeOptions, before upgradeData) {
	t.Helper()
	for _, p := range []string{opt.Snapshot, opt.Destination} {
		if _, err := os.Stat(p); !os.IsNotExist(err) {
			t.Fatalf("unexpected published path %s: %v", p, err)
		}
	}
	for _, p := range []string{filepath.Join(opt.Destination, "restore-report.json"), filepath.Join(opt.Snapshot, "restore-report.json")} {
		if _, err := os.Stat(p); !os.IsNotExist(err) {
			t.Fatalf("rejected source published restore report %s: %v", p, err)
		}
	}
	if !reflect.DeepEqual(before, history20Rows(t, opt.Source)) {
		t.Fatal("source typed rows changed")
	}
}

func TestRestored21PublicUpgradeFromH20PreservesSource(t *testing.T) {
	restored21ReportHookControls(t)
	opt, before := restored21Fixture(t)
	report, err := UpgradeLocal(context.Background(), opt)
	if err != nil {
		t.Fatal(err)
	}
	if report.Status != "RESTORED_RECONCILIATION_REQUIRED" {
		t.Fatal(report.Status)
	}
	if !reflect.DeepEqual(before, history20Rows(t, opt.Source)) {
		t.Fatal("source changed")
	}
	after := history20Rows(t, filepath.Join(opt.Destination, "researchos.sqlite"))
	if err = upgradeRestored21RecoveryInvariant(before, after, opt.Destination); err != nil {
		t.Fatal(err)
	}
	if len(after["schema_migrations"]) != 22 || len(after["client_sessions"]) != 0 {
		t.Fatal("wrong target shape")
	}
	evidence, ok := report.Recovery["restored21_session_initialization"].(Object)
	if !ok || evidence["old_typed_rows_unchanged"] != true || evidence["restored_barriers_refreshed"] != false {
		t.Fatal("missing distinct session phase receipt")
	}
	persistedRaw, err := os.ReadFile(filepath.Join(opt.Destination, "restore-report.json"))
	if err != nil {
		t.Fatal(err)
	}
	var persisted RestoreReport
	if err = json.Unmarshal(persistedRaw, &persisted); err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(Bytes(report.Recovery), Bytes(persisted.Recovery)) {
		t.Fatal("returned and persisted Recovery differ")
	}
	_, _, _, target := restored21FixtureProfiles(t, opt)
	db := restored21Open(t, filepath.Join(opt.Destination, "researchos.sqlite"))
	got, err := backupSchema(db)
	if err != nil || got != target {
		t.Fatalf("target profile %s %v", got, err)
	}
}

func TestRestored21SessionPreservesTypedRowsAndRestoreFence(t *testing.T) {
	opt, _ := restored21Fixture(t)
	sqls, source, session, _ := restored21FixtureProfiles(t, opt)
	db := restored21Open(t, opt.Source)
	if _, err := db.Exec("INSERT INTO backup_restore_barriers(project,run,restored_at) VALUES('public-project','public-run','2026-01-01T00:00:00Z')"); err != nil {
		t.Fatal(err)
	}
	before, err := upgradeRows(db)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = upgradeRestored21Sessions(context.Background(), db, sqls[22], source, session); err != nil {
		t.Fatal(err)
	}
	after, err := upgradeRows(db)
	if err != nil {
		t.Fatal(err)
	}
	for table, rows := range before {
		if !reflect.DeepEqual(rows, after[table]) {
			t.Fatal("typed row drift", table)
		}
	}
	var count int
	if err = db.QueryRow("SELECT count(*) FROM sqlite_master WHERE type='trigger' AND name='backup_require_fresh_observation'").Scan(&count); err != nil || count != 1 {
		t.Fatal("Run restore fence lost", err)
	}
}

func TestRestored21RejectsForeignPartialSessionAndMissingFence(t *testing.T) {
	for _, shape := range []string{"foreign", "partial-session", "session-addon", "missing-restore-trigger"} {
		t.Run(shape, func(t *testing.T) {
			opt, _ := restored21Fixture(t)
			db, err := store.Open(opt.Source)
			if err != nil {
				t.Fatal(err)
			}
			raw := []byte("CREATE TABLE foreign_profile(id TEXT)")
			switch shape {
			case "partial-session":
				raw = []byte("CREATE TABLE client_sessions(id TEXT)")
			case "session-addon":
				raw, err = os.ReadFile("../../migrations/sqlite/next_v24_sessions.sql")
			case "missing-restore-trigger":
				raw = []byte("DROP TRIGGER backup_require_fresh_observation")
			}
			if err != nil {
				db.Close()
				t.Fatal(err)
			}
			_, err = db.Exec(string(raw))
			db.Close()
			if err != nil {
				t.Fatal(err)
			}
			before := history20Rows(t, opt.Source)
			_, err = UpgradeLocal(context.Background(), opt)
			if err == nil || err.Error() != "UPGRADE_SOURCE_SCHEMA" {
				t.Fatalf("wrong schema rejection: %v", err)
			}
			restored21AssertUnpublished(t, opt, before)
		})
	}
}

func TestRestored21SessionRollbackAfterActualDDL(t *testing.T) {
	opt, _ := restored21Fixture(t)
	sqls, source, _, _ := restored21FixtureProfiles(t, opt)
	db := restored21Open(t, opt.Source)
	before, err := upgradeRows(db)
	if err != nil {
		t.Fatal(err)
	}
	_, err = upgradeRestored21Sessions(context.Background(), db, sqls[22], source, "sha256:wrong-target-profile")
	if err == nil || err.Error() != "UPGRADE_RESTORED21_SESSION_SCHEMA" {
		t.Fatalf("expected post-DDL schema rejection, got %v", err)
	}
	after, err := upgradeRows(db)
	if err != nil {
		t.Fatal(err)
	}
	schema, err := backupSchema(db)
	if err != nil {
		t.Fatal(err)
	}
	if schema != source || !reflect.DeepEqual(before, after) {
		t.Fatal("session DDL survived rollback")
	}
}

func TestRestored21RepeatedSessionInstallRejectedWithoutReplay(t *testing.T) {
	opt, _ := restored21Fixture(t)
	sqls, source, session, _ := restored21FixtureProfiles(t, opt)
	db := restored21Open(t, opt.Source)
	if _, err := upgradeRestored21Sessions(context.Background(), db, sqls[22], source, session); err != nil {
		t.Fatal(err)
	}
	before, err := upgradeRows(db)
	if err != nil {
		t.Fatal(err)
	}
	_, err = upgradeRestored21Sessions(context.Background(), db, sqls[22], source, session)
	if err == nil || err.Error() != "UPGRADE_RESTORED21_SOURCE_SCHEMA" {
		t.Fatal("repeat accepted", err)
	}
	after, err := upgradeRows(db)
	if err != nil {
		t.Fatal(err)
	}
	if !reflect.DeepEqual(before, after) {
		t.Fatal("repeat changed ledger or rows")
	}
}

func TestRestored21SessionReadyStillRejectedByOldQueuePlan(t *testing.T) {
	opt, _ := restored21Fixture(t)
	sqls, source, session, _ := restored21FixtureProfiles(t, opt)
	db, err := store.Open(opt.Source)
	if err != nil {
		t.Fatal(err)
	}
	_, err = upgradeRestored21Sessions(context.Background(), db, sqls[22], source, session)
	db.Close()
	if err != nil {
		t.Fatal(err)
	}
	before := history20Rows(t, opt.Source)
	opt.Plan = QueueSchemaUpgradePlan
	_, err = UpgradeLocal(context.Background(), opt)
	if err == nil || err.Error() != "UPGRADE_SOURCE_SCHEMA" {
		t.Fatal("old queue profile changed", err)
	}
	restored21AssertUnpublished(t, opt, before)
}

func TestRestored21MatchingSnapshotCorrectAndWrongKey(t *testing.T) {
	opt, _ := restored21Fixture(t)
	if _, err := UpgradeLocal(context.Background(), opt); err != nil {
		t.Fatal(err)
	}
	raw, err := os.ReadFile(filepath.Join(opt.Snapshot, "manifest.json"))
	if err != nil {
		t.Fatal(err)
	}
	var m BackupManifest
	if err = json.Unmarshal(raw, &m); err != nil {
		t.Fatal(err)
	}
	plan, ok := m.Purpose["plan"].(map[string]any)
	if !ok || plan["id"] != Restored21SessionUpgradePlan {
		t.Fatal("wrong snapshot purpose")
	}
	key, err := os.ReadFile(opt.KeyFile)
	if err != nil {
		t.Fatal(err)
	}
	defer clear(key)
	policy := &backupPolicy{format: localUpgradeFormat, databaseName: "researchos.sqlite", purpose: m.Purpose}
	verified, files, err := readBackupPolicy(opt.Snapshot, key, policy)
	if err != nil || len(files["state.sqlite"]) == 0 || !reflect.DeepEqual(verified.Migrations, upgradeVersions(21)) {
		t.Fatal("matching key/profile rejected", err)
	}
	wrong := bytes.Clone(key)
	defer clear(wrong)
	wrong[0] ^= 1
	_, files, err = readBackupPolicy(opt.Snapshot, wrong, policy)
	if err == nil || err.Error() != "BACKUP_MANIFEST_INVALID" || files != nil {
		t.Fatal("wrong key accepted", err)
	}
}

func TestRestored21RejectsSessionReleaseHashDriftBeforeSnapshot(t *testing.T) {
	opt, before := restored21Fixture(t)
	if err := os.WriteFile(filepath.Join(opt.TargetRoot, "migrations/sqlite/next_v24_sessions.sql"), []byte("SELECT 1;"), 0600); err != nil {
		t.Fatal(err)
	}
	_, err := UpgradeLocal(context.Background(), opt)
	if err == nil || err.Error() != "UPGRADE_SESSION_SCHEMA_HASH" {
		t.Fatal("release drift accepted", err)
	}
	restored21AssertUnpublished(t, opt, before)
}

func TestRestored21QueueLedgerFailureRollsBackQueueDDL(t *testing.T) {
	opt, _ := restored21Fixture(t)
	sqls, source, session, _ := restored21FixtureProfiles(t, opt)
	db := restored21Open(t, opt.Source)
	if _, err := upgradeRestored21Sessions(context.Background(), db, sqls[22], source, session); err != nil {
		t.Fatal(err)
	}
	// Internal fixed migration rollback control; not public coordinator failure evidence.
	if _, err := db.Exec("CREATE TRIGGER fixture_reject_22 BEFORE INSERT ON schema_migrations WHEN NEW.version=22 BEGIN SELECT RAISE(ABORT,'fixture ledger failure'); END"); err != nil {
		t.Fatal(err)
	}
	before, err := upgradeRows(db)
	if err != nil {
		t.Fatal(err)
	}
	schema, err := backupSchema(db)
	if err != nil {
		t.Fatal(err)
	}
	err = upgradeQueueMigration(context.Background(), db, sqls[21], sqls[22])
	if err == nil || !strings.Contains(err.Error(), "fixture ledger failure") {
		t.Fatal("queue transaction did not fail", err)
	}
	after, err := upgradeRows(db)
	if err != nil {
		t.Fatal(err)
	}
	now, err := backupSchema(db)
	if err != nil {
		t.Fatal(err)
	}
	if schema != now || !reflect.DeepEqual(before, after) {
		t.Fatal("queue failure changed committed session profile")
	}
}

// These pure report-hook controls share the existing public-success parent;
// they add no test2json parent/leaf and perform no fixture database operations.
func restored21ReportHookControls(t *testing.T) {
	t.Helper()
	digest := Digest([]byte("PUBLIC_REPORT_HOOK_FIXTURE"))
	valid := Object{"source_schema_hash": digest, "session_schema_hash": digest, "before_rows_hash": digest, "after_rows_hash": digest, "numbered_ledger_unchanged": true, "old_typed_rows_unchanged": true, "client_sessions_created_empty": true, "restore_fence_preserved": true, "restored_barriers_refreshed": false, "external_actions_dispatched": 0}
	for _, name := range []string{"wrong-plan", "wrong-format", "missing-field", "extra-field", "wrong-type", "wrong-hash", "nonzero-actions"} {
		evidence := Object{}
		for key, value := range valid {
			evidence[key] = value
		}
		purpose := Object{"plan": Object{"id": Restored21SessionUpgradePlan}, "scope": "PUBLIC_REPORT_HOOK_FIXTURE"}
		policy := &backupPolicy{format: localUpgradeFormat, purpose: purpose, restored21SessionEvidence: evidence}
		switch name {
		case "wrong-plan":
			purpose["plan"] = Object{"id": QueueSchemaUpgradePlan}
		case "wrong-format":
			policy.format = "RESEARCHOS_BACKUP_V1"
		case "missing-field":
			delete(evidence, "before_rows_hash")
		case "extra-field":
			evidence["unapproved_field"] = true
		case "wrong-type":
			evidence["old_typed_rows_unchanged"] = "true"
		case "wrong-hash":
			evidence["source_schema_hash"] = "sha256:wrong"
		case "nonzero-actions":
			evidence["external_actions_dispatched"] = 1
		}
		purposeBefore := Bytes(purpose)
		recovery := Object{"existing": true}
		before := Bytes(recovery)
		err := upgradeRestored21PublishEvidence(policy, recovery)
		expected := "RESTORE_RESTORED21_REPORT_EVIDENCE_INVALID"
		if name == "wrong-plan" || name == "wrong-format" {
			expected = "RESTORE_RESTORED21_REPORT_POLICY_MISMATCH"
		}
		if err == nil || err.Error() != expected || !bytes.Equal(before, Bytes(recovery)) || !bytes.Equal(purposeBefore, Bytes(purpose)) {
			t.Fatalf("invalid report hook changed authenticated purpose or recovery: %s %v", name, err)
		}
	}
	oldPurpose := Object{"plan": Object{"id": QueueSchemaUpgradePlan}}
	recovery := Object{"existing": true}
	before := Bytes(recovery)
	if err := upgradeRestored21PublishEvidence(&backupPolicy{format: localUpgradeFormat, purpose: oldPurpose}, recovery); err != nil || !bytes.Equal(before, Bytes(recovery)) {
		t.Fatal("old-plan nil hook changed report", err)
	}
	purpose := Object{"plan": Object{"id": Restored21SessionUpgradePlan}}
	purposeBefore := Bytes(purpose)
	if err := upgradeRestored21PublishEvidence(&backupPolicy{format: localUpgradeFormat, purpose: purpose, restored21SessionEvidence: valid}, recovery); err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(Bytes(valid), Bytes(recovery["restored21_session_initialization"])) || !bytes.Equal(purposeBefore, Bytes(purpose)) {
		t.Fatal("valid hook changed purpose or evidence")
	}
}
