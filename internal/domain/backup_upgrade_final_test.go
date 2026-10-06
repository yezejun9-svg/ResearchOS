package domain

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"researchos.local/research-os/internal/store"
)

func upgradeFinalFixture(t *testing.T) (LocalUpgradeOptions, *fixture, *upgradeFake) {
	t.Helper()
	opt, f, fake := upgradeFixture(t, true)
	opt.Plan, opt.TargetRoot = FinalSchemaUpgradePlan, upgradeTestRelease(t, 20)
	// Public legacy manual annotations, deliberately lacking independent review
	// authority; 0020 must preserve every old field and add only three NULLs.
	for i := 0; i < 2; i++ {
		_, e := f.db.Exec(`INSERT INTO research_candidate_reviews(project,cycle_id,evidence_id,profile_revision,context_target,outcome,reason,origin_summary_json,created_at) VALUES(?,?,?,1,'fixture','REJECT','public legacy annotation','{}',?)`, f.project, "public-legacy-cycle", fmt.Sprintf("public-legacy-evidence-%d", i), Now())
		if e != nil {
			t.Fatal(e)
		}
	}
	return opt, f, fake
}

func finalUpgradeAssert(t *testing.T, id string, expected, actual any) {
	t.Helper()
	status := "PASS"
	if Hash(expected) != Hash(actual) {
		status = "FAIL"
	}
	fmt.Println("W18_UPGRADE_ASSERTION " + string(Bytes(Object{"assertion_id": id, "expected": expected, "actual": actual, "status": status, "scope": "PUBLIC_FIXTURE_NATIVE_FILES_ONLY", "private_body_read": false, "external_provider_calls": 0})))
	if status != "PASS" {
		t.Fatalf("%s: want %v got %v", id, expected, actual)
	}
}

func TestW18FinalSchemaUpgrade(t *testing.T) {
	opt, f, fake := upgradeFinalFixture(t)
	ctx := context.Background()
	before, e := upgradeRows(f.db)
	if e != nil {
		t.Fatal(e)
	}
	_, e = New(f.db, filepath.Join(opt.TargetRoot, "spec/v2.0/contracts"), filepath.Join(opt.TargetRoot, "migrations/sqlite/0002_domain.sql"))
	finalUpgradeAssert(t, "POPULATED13-IMPLICIT-UPGRADE-REFUSED", true, e != nil && strings.Contains(e.Error(), "MIGRATION_PREBACKUP_REQUIRED"))
	f.db.Close()
	report, e := upgradeLocal(ctx, opt, fake.verifier())
	if e != nil {
		t.Fatal(e)
	}
	finalUpgradeAssert(t, "EXACT20-REPORT", "RESTORED_RECONCILIATION_REQUIRED", report.Status)
	db, e := store.Open(filepath.Join(opt.Destination, "researchos.sqlite"))
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	upgradeHistoricalFixtureService(t, db, opt.TargetRoot, 20, true)
	versions, e := backupMigrations(db)
	if e != nil {
		t.Fatal(e)
	}
	finalUpgradeAssert(t, "HISTORICAL20-SCHEMA-VALIDATED", upgradeVersions(20), versions)
	after, e := upgradeRows(db)
	if e != nil {
		t.Fatal(e)
	}
	if e = upgradeRecoveryInvariantForTarget(before, after, opt.Destination, 20); e != nil {
		t.Fatal(e)
	}
	finalUpgradeAssert(t, "FULL-HISTORY-RECOVERY-INVARIANT", true, true)
	var legacy, failed, credentials int
	for _, q := range []struct {
		query string
		value *int
	}{
		{"SELECT count(*) FROM research_candidate_reviews WHERE reviewer_id IS NULL AND review_task_ref IS NULL AND acceptance_ref IS NULL", &legacy},
		{"SELECT count(*) FROM domain_objects WHERE kind='Qualification' AND json_extract(body,'$.status')='FAILED' AND json_extract(body,'$.maximum_mode')='ADVISORY'", &failed},
		{"SELECT count(*) FROM auth_credentials WHERE revoked=0", &credentials},
	} {
		if e = db.QueryRow(q.query).Scan(q.value); e != nil {
			t.Fatal(e)
		}
	}
	finalUpgradeAssert(t, "LEGACY-NULL-AUTHORITY-FAILED-QUALIFICATIONS-REVOKED-CREDENTIALS", []int{2, 2, 0}, []int{legacy, failed, credentials})
	for table := range upgradeFinalTables {
		finalUpgradeAssert(t, "NEW-EMPTY-"+table, 0, len(after[table]))
	}
	// Mutations must be refused even when the surrounding recovery history is valid.
	for _, mutation := range []string{"authority", "legacy-history", "runtime-approval", "unexpected-table", "missing-table"} {
		changed, err := upgradeRows(db)
		if err != nil {
			t.Fatal(err)
		}
		switch mutation {
		case "authority":
			changed["research_candidate_reviews"][0]["reviewer_id"] = "fabricated"
		case "legacy-history":
			changed["research_candidate_reviews"][0]["reason"] = "rewritten"
		case "runtime-approval":
			changed["runtime_qualification_approvals"] = []Object{{"runtime": "fabricated"}}
		case "unexpected-table":
			changed["remote_unreviewed"] = []Object{}
		case "missing-table":
			delete(changed, "research_cycle_work")
		}
		finalUpgradeAssert(t, "REFUSE-"+mutation, true, upgradeRecoveryInvariantForTarget(before, changed, opt.Destination, 20) != nil)
	}
	source, e := store.Open(opt.Source)
	if e != nil {
		t.Fatal(e)
	}
	unchanged, e := upgradeRows(source)
	if e != nil {
		t.Fatal(e)
	}
	finalUpgradeAssert(t, "SOURCE13-LOGICALLY-UNCHANGED", Hash(before), Hash(unchanged))
	upgradeHistoricalFixtureService(t, source, opt.SourceRoot, 13, false)
	source.Close()
	manifestBytes, e := os.ReadFile(filepath.Join(opt.Snapshot, "manifest.json"))
	if e != nil {
		t.Fatal(e)
	}
	var manifest BackupManifest
	if e = json.Unmarshal(manifestBytes, &manifest); e != nil {
		t.Fatal(e)
	}
	plan := manifest.Purpose["plan"].(map[string]any)
	finalUpgradeAssert(t, "AUTHENTICATED-EXACT-PLAN", FinalSchemaUpgradePlan, plan["id"])
	finalUpgradeAssert(t, "AUTHENTICATED-ALL-SEVEN-SQL-HASHES", Hash(upgradeFinalSQLManifest()), Hash(plan["migration_sql_hashes"]))
	key, e := os.ReadFile(opt.KeyFile)
	if e != nil {
		t.Fatal(e)
	}
	defer clear(key)
	_, e = RestoreBackup(ctx, opt.Snapshot, filepath.Join(t.TempDir(), "ordinary-restore"), RestoreOptions{Key: key, Contracts: f.s.Contracts, SupportedMigrations: upgradeVersions(13)})
	finalUpgradeAssert(t, "ORDINARY-RESTORE-REFUSED", true, e != nil && strings.Contains(e.Error(), "BACKUP_MANIFEST_INVALID"))
	finalUpgradeAssert(t, "PRIVATE-READS-ZERO", 0, fake.reads)
	finalUpgradeAssert(t, "OPAQUE-REFERENCE-RECHECKS", true, fake.descriptions >= 3)
}

func TestW18FinalSchemaActiveRecovery(t *testing.T) { upgradeActiveRecovery(t, FinalSchemaUpgradePlan) }

func TestW18FinalSchemaRefusals(t *testing.T) {
	for _, failure := range []string{"unknown-plan", "target19", "target21", "changed20", "source-gap", "wrong-schema", "service-identity", "descriptor-hash", "late-service-change", "open-owner"} {
		t.Run(failure, func(t *testing.T) {
			opt, f, fake := upgradeFinalFixture(t)
			switch failure {
			case "unknown-plan":
				opt.Plan = "schema13-to21-research-runtime-v1"
			case "target19":
				opt.TargetRoot = upgradeTestRelease(t, 19)
			case "target21":
				if e := os.WriteFile(filepath.Join(opt.TargetRoot, "migrations/sqlite/0021_unreviewed.sql"), []byte("SELECT 1;"), 0600); e != nil {
					t.Fatal(e)
				}
			case "changed20":
				p := filepath.Join(opt.TargetRoot, "migrations/sqlite/0020_research_cycle_work.sql")
				raw, e := os.ReadFile(p)
				if e != nil {
					t.Fatal(e)
				}
				if e = os.WriteFile(p, append(raw, []byte("\n-- changed")...), 0600); e != nil {
					t.Fatal(e)
				}
			case "source-gap":
				if _, e := f.db.Exec("DELETE FROM schema_migrations WHERE version=9"); e != nil {
					t.Fatal(e)
				}
			case "wrong-schema":
				if _, e := f.db.Exec("CREATE TABLE unreviewed_source(x)"); e != nil {
					t.Fatal(e)
				}
			case "service-identity":
				fake.fail = "identity"
			case "descriptor-hash":
				fake.fail = "hash"
			case "late-service-change":
				fake.fail = "late-change"
			}
			before, e := upgradeRows(f.db)
			if e != nil {
				t.Fatal(e)
			}
			if failure != "open-owner" {
				f.db.Close()
			}
			_, e = upgradeLocal(context.Background(), opt, fake.verifier())
			finalUpgradeAssert(t, "REFUSAL-"+failure, true, e != nil)
			if failure == "open-owner" {
				f.db.Close()
			}
			if _, err := os.Stat(opt.Destination); !os.IsNotExist(err) {
				t.Fatal("refused target published")
			}
			db, e := store.Open(opt.Source)
			if e != nil {
				t.Fatal(e)
			}
			after, e := upgradeRows(db)
			db.Close()
			if e != nil {
				t.Fatal(e)
			}
			finalUpgradeAssert(t, "REFUSAL-PRESERVES-SOURCE-"+failure, Hash(before), Hash(after))
			finalUpgradeAssert(t, "REFUSAL-NO-PRIVATE-READ-"+failure, 0, fake.reads)
			if failure == "late-service-change" {
				if _, e = os.Stat(filepath.Join(opt.Snapshot, "manifest.json")); e != nil {
					t.Fatal(e)
				}
			}
		})
	}
}

func TestW18FinalSchemaRollback(t *testing.T) {
	opt, f, fake := upgradeFinalFixture(t)
	f.db.Close()
	if _, e := upgradeLocal(context.Background(), opt, fake.verifier()); e != nil {
		t.Fatal(e)
	}
	raw, e := os.ReadFile(filepath.Join(opt.Snapshot, "manifest.json"))
	if e != nil {
		t.Fatal(e)
	}
	var manifest BackupManifest
	if e = json.Unmarshal(raw, &manifest); e != nil {
		t.Fatal(e)
	}
	key, e := os.ReadFile(opt.KeyFile)
	if e != nil {
		t.Fatal(e)
	}
	defer clear(key)
	guard := &upgradeProtection{ctx: context.Background(), verifier: fake.verifier()}
	policy := &backupPolicy{format: localUpgradeFormat, databaseName: "researchos.sqlite", purpose: manifest.Purpose, validate: guard.refresh, allowProtected: guard.artifact}
	_, sqls, e := upgradeRelease(opt.TargetRoot, 20)
	if e != nil {
		t.Fatal(e)
	}
	target := filepath.Join(t.TempDir(), "failed20")
	_, e = restoreBackupPolicy(context.Background(), opt.Snapshot, target, RestoreOptions{Key: key, SupportedMigrations: upgradeVersions(13), Contracts: f.s.Contracts, Migration: func(ctx context.Context, db *sql.DB) error {
		if _, err := db.Exec("CREATE TABLE research_cycle_work(public_collision_fixture)"); err != nil {
			return err
		}
		err := upgradeFinalMigration(ctx, db, sqls[13:])
		var partial int
		if queryErr := db.QueryRow("SELECT count(*) FROM sqlite_master WHERE name IN ('remote_devices','runtime_dispatches','intent_plan_bindings','research_monitor_cycles')").Scan(&partial); queryErr != nil {
			return queryErr
		}
		finalUpgradeAssert(t, "LATE20-FAILURE-ROLLS-BACK-14-THROUGH20", 0, partial)
		versions, queryErr := backupMigrations(db)
		if queryErr != nil {
			return queryErr
		}
		finalUpgradeAssert(t, "LATE20-FAILURE-RESTORES-13-MARKERS", upgradeVersions(13), versions)
		return err
	}}, policy)
	finalUpgradeAssert(t, "MIGRATION-FAILURE-REFUSED", true, e != nil && strings.Contains(e.Error(), "MIGRATION_FAILED"))
	if _, e = os.Stat(target); !os.IsNotExist(e) {
		t.Fatal("failed target published")
	}
	after, e := os.ReadFile(filepath.Join(opt.Snapshot, "manifest.json"))
	if e != nil {
		t.Fatal(e)
	}
	finalUpgradeAssert(t, "ENCRYPTED-SNAPSHOT-RETAINED", Digest(raw), Digest(after))
	rollback := filepath.Join(t.TempDir(), "rollback13")
	_, e = restoreBackupPolicy(context.Background(), opt.Snapshot, rollback, RestoreOptions{Key: key, SupportedMigrations: upgradeVersions(13), Contracts: f.s.Contracts}, policy)
	if e != nil {
		t.Fatal(e)
	}
	db, e := store.Open(filepath.Join(rollback, "researchos.sqlite"))
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	upgradeHistoricalFixtureService(t, db, opt.SourceRoot, 13, true)
	versions, e := backupMigrations(db)
	if e != nil {
		t.Fatal(e)
	}
	finalUpgradeAssert(t, "RETAINED-BACKUP-HISTORICAL13-SCHEMA-VALIDATED", upgradeVersions(13), versions)
	finalUpgradeAssert(t, "ROLLBACK-NO-PRIVATE-READ", 0, fake.reads)
}
