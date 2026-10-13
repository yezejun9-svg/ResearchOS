package domain

import (
	"context"
	"database/sql"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func pauseMigrationTestRelease(t *testing.T) string {
	t.Helper()
	root := preparedUpgradeTestRelease(t, 24)
	if err := os.WriteFile(filepath.Join(root, "migrations/sqlite/0025_runtime_pause_activations.sql"), backupPauseSQL, 0600); err != nil {
		t.Fatal(err)
	}
	return root
}

func pauseMigrationStageTestOptions(t *testing.T) PauseSchemaUpgradeOptions {
	t.Helper()
	root := t.TempDir()
	for _, name := range []string{"source", "key", "backup", "release24", "release25", "stage"} {
		if err := os.Mkdir(filepath.Join(root, name), 0700); err != nil {
			t.Fatal(err)
		}
	}
	u := LocalUpgradeOptions{Plan: PauseSchemaUpgradePlan,
		Source: filepath.Join(root, "source", "source.sqlite"), KeyFile: filepath.Join(root, "key", "key"),
		Snapshot: filepath.Join(root, "backup"), SourceRoot: filepath.Join(root, "release24"),
		TargetRoot: filepath.Join(root, "release25"), Destination: filepath.Join(root, "stage", "rehearsal")}
	for _, path := range []string{u.Source, u.KeyFile} {
		if err := os.WriteFile(path, []byte("stage boundary fixture"), 0600); err != nil {
			t.Fatal(err)
		}
	}
	return PauseSchemaUpgradeOptions{Upgrade: u}
}

func TestPauseMigrationStageIgnoresAmbientTemp(t *testing.T) {
	for _, mode := range []string{"missing", "empty", "hostile"} {
		t.Run(mode, func(t *testing.T) {
			opt := pauseMigrationStageTestOptions(t)
			parent := filepath.Dir(opt.Upgrade.Destination)
			hostile := filepath.Join(t.TempDir(), "must-not-exist", "foreign-temp")
			root := pauseMigrationTestRelease(t)
			_, sqls, err := pauseMigrationRelease(root, 25)
			if err != nil {
				t.Fatal(err)
			}
			contracts, err := LoadContracts(filepath.Join(root, "spec/v2.0/contracts"))
			if err != nil {
				t.Fatal(err)
			}
			for _, key := range []string{"TEMP", "TMP", "TMPDIR"} {
				t.Setenv(key, "")
				if mode == "missing" {
					if err := os.Unsetenv(key); err != nil {
						t.Fatal(err)
					}
				} else if mode == "hostile" {
					t.Setenv(key, hostile)
				}
			}
			for _, existing := range []bool{false, true} {
				if existing {
					if err := os.Mkdir(opt.Upgrade.Destination, 0700); err != nil {
						t.Fatal(err)
					}
				}
				stage, err := pauseMigrationTemplateStage(opt, parent)
				if err != nil || filepath.Dir(stage) != parent {
					t.Fatal("stage escaped explicit destination parent", stage, err)
				}
				if err := os.Remove(stage); err != nil {
					t.Fatal(err)
				}
				schemas, err := pauseMigrationTemplate(context.Background(), opt, parent, sqls, contracts)
				if err != nil || schemas.Source24 == "" || schemas.Original25 == "" || schemas.Restored25 == "" {
					t.Fatal("full template under explicit parent", schemas, err)
				}
				stages, err := filepath.Glob(filepath.Join(parent, ".researchos-backup-stage-*"))
				if err != nil || len(stages) != 0 {
					t.Fatal("template stage was not removed", stages, err)
				}
			}
			if _, err := os.Stat(hostile); !os.IsNotExist(err) {
				t.Fatal("ambient hostile directory was touched", err)
			}
		})
	}
}

func TestPauseMigrationStageRejectsBeforeFilesystemStaging(t *testing.T) {
	for _, mutation := range []string{"missing-parent", "relative-parent", "mismatched-parent", "missing-destination", "relative-destination", "query", "fragment", "nonexistent-parent", "parent-is-file", "destination-is-file", "source-overlap", "key-overlap", "backup-overlap", "release-overlap", "ancestor-overlap", "relative-source", "source-fragment", "missing-source"} {
		t.Run(mutation, func(t *testing.T) {
			opt := pauseMigrationStageTestOptions(t)
			parent := filepath.Dir(opt.Upgrade.Destination)
			root := filepath.Dir(parent)
			switch mutation {
			case "missing-parent":
				parent = ""
			case "relative-parent":
				parent = "stage"
			case "mismatched-parent":
				parent = root
			case "missing-destination":
				opt.Upgrade.Destination = ""
			case "relative-destination":
				opt.Upgrade.Destination = filepath.Join("stage", "rehearsal")
			case "query", "fragment":
				suffix := "?query"
				if mutation == "fragment" {
					suffix = "#fragment"
				}
				opt.Upgrade.Destination += suffix
			case "nonexistent-parent":
				parent = filepath.Join(root, "missing")
				opt.Upgrade.Destination = filepath.Join(parent, "rehearsal")
			case "parent-is-file":
				parent = opt.Upgrade.KeyFile
				opt.Upgrade.Destination = filepath.Join(parent, "rehearsal")
			case "destination-is-file":
				if err := os.WriteFile(opt.Upgrade.Destination, []byte("not a directory"), 0600); err != nil {
					t.Fatal(err)
				}
			case "source-overlap":
				parent = filepath.Dir(opt.Upgrade.Source)
				opt.Upgrade.Destination = filepath.Join(parent, "rehearsal")
			case "key-overlap":
				parent = filepath.Dir(opt.Upgrade.KeyFile)
				opt.Upgrade.Destination = filepath.Join(parent, "rehearsal")
			case "backup-overlap":
				parent = opt.Upgrade.Snapshot
				opt.Upgrade.Destination = filepath.Join(parent, "rehearsal")
			case "release-overlap":
				parent = opt.Upgrade.TargetRoot
				opt.Upgrade.Destination = filepath.Join(parent, "rehearsal")
			case "ancestor-overlap":
				parent = root
				opt.Upgrade.Destination = filepath.Join(parent, "rehearsal")
			case "relative-source":
				opt.Upgrade.Source = "source.sqlite"
			case "source-fragment":
				opt.Upgrade.Source += "#fragment"
			case "missing-source":
				opt.Upgrade.Source = filepath.Join(root, "missing.sqlite")
			}
			var before []string
			if err := filepath.WalkDir(root, func(path string, _ os.DirEntry, err error) error { before = append(before, path); return err }); err != nil {
				t.Fatal(err)
			}
			if stage, err := pauseMigrationTemplateStage(opt, parent); err == nil || stage != "" {
				t.Fatal("invalid stage binding accepted", stage, err)
			}
			var after []string
			if err := filepath.WalkDir(root, func(path string, _ os.DirEntry, err error) error { after = append(after, path); return err }); err != nil {
				t.Fatal(err)
			}
			if strings.Join(before, "\n") != strings.Join(after, "\n") {
				t.Fatal("rejected staging mutated filesystem", before, after)
			}
		})
	}
}

func pauseMigrationTestDB(t *testing.T) (*sql.DB, []byte, pauseMigrationSchemas) {
	t.Helper()
	db, oldSQL, oldSchemas := preparedUpgradeTestDB(t)
	before, err := preparedUpgradeSnapshot(db)
	if err != nil {
		t.Fatal(err)
	}
	if err = preparedUpgradeRehearseDDL(context.Background(), db, oldSQL, before, oldSchemas.Source23, oldSchemas.Original24); err != nil {
		t.Fatal(err)
	}
	// A populated immutable old proof is ordinary old history to the new DDL.
	for _, statement := range []string{
		`UPDATE domain_objects SET body=json_set(body,'$.status','FAILED','$.failure_count',9007199254740993) WHERE kind IN ('Run','Task')`,
		`INSERT INTO runtime_prepared_abandonments VALUES('p','t','r','runtime',1,'fixture-dispatch','fixture-manifest','owner','proof','{}','FAILED_NOT_DISPATCHED_ACCOUNTING_UNKNOWN',0,'now')`,
	} {
		if _, err = db.Exec(statement); err != nil {
			t.Fatal(err)
		}
	}
	root := pauseMigrationTestRelease(t)
	_, sqls, err := pauseMigrationRelease(root, 25)
	if err != nil {
		t.Fatal(err)
	}
	contracts, err := LoadContracts(filepath.Join(root, "spec/v2.0/contracts"))
	if err != nil {
		t.Fatal(err)
	}
	stageOpt := pauseMigrationStageTestOptions(t)
	schemas, err := pauseMigrationTemplate(context.Background(), stageOpt, filepath.Dir(stageOpt.Upgrade.Destination), sqls, contracts)
	if err != nil {
		t.Fatal(err)
	}
	return db, sqls[24], schemas
}

func TestPauseMigrationDDLRetainsEveryOldRowAndProof(t *testing.T) {
	db, raw, schemas := pauseMigrationTestDB(t)
	before, err := preparedUpgradeSnapshot(db)
	if err != nil {
		t.Fatal(err)
	}
	if err = pauseMigrationRehearseDDL(context.Background(), db, raw, before, schemas.Source24, schemas.Original25); err != nil {
		t.Fatal(err)
	}
	after, err := preparedUpgradeSnapshot(db)
	if err != nil {
		t.Fatal(err)
	}
	if err = pauseMigrationRowsUnchanged(before, after); err != nil {
		t.Fatal(err)
	}
	if err = backupPauseSchema(db); err != nil {
		t.Fatal(err)
	}
	if len(after["runtime_prepared_abandonments"].Rows) != 1 {
		t.Fatal("old proof lost")
	}
	var failureCount int64
	if err = db.QueryRow(`SELECT json_extract(body,'$.failure_count') FROM domain_objects WHERE kind='Task'`).Scan(&failureCount); err != nil || failureCount != 9007199254740993 {
		t.Fatal("failure history changed", failureCount, err)
	}
	if err = pauseMigrationRehearseDDL(context.Background(), db, raw, after, schemas.Source24, schemas.Original25); err == nil {
		t.Fatal("second migration accepted")
	}
}

func TestPauseMigrationRejectsAndRollsBack(t *testing.T) {
	for _, mutation := range []string{"sql", "source-schema", "target-schema", "stale-rows", "version", "future-version", "extra-table", "trigger"} {
		t.Run(mutation, func(t *testing.T) {
			db, raw, schemas := pauseMigrationTestDB(t)
			before, err := preparedUpgradeSnapshot(db)
			if err != nil {
				t.Fatal(err)
			}
			tx, err := db.Begin()
			if err != nil {
				t.Fatal(err)
			}
			source, target := schemas.Source24, schemas.Original25
			switch mutation {
			case "sql":
				raw = append(append([]byte(nil), raw...), '\n')
			case "source-schema":
				source = "wrong"
			case "target-schema":
				target = "wrong"
			case "stale-rows":
				_, err = tx.Exec(`UPDATE auth_credentials SET revoked=1`)
			case "version":
				_, err = tx.Exec(`DELETE FROM schema_migrations WHERE version=24`)
			case "future-version":
				_, err = tx.Exec(`INSERT INTO schema_migrations(version) VALUES(25)`)
			case "extra-table":
				_, err = tx.Exec(`CREATE TABLE unexpected_source(x)`)
			case "trigger":
				_, err = tx.Exec(`DROP TRIGGER runtime_prepared_abandonments_immutable`)
			}
			if err != nil {
				t.Fatal(err)
			}
			if err = pauseMigrationDDL(context.Background(), tx, raw, before, source, target); err == nil {
				t.Fatal("bad migration accepted", mutation)
			}
			if err = tx.Rollback(); err != nil {
				t.Fatal(err)
			}
			after, err := preparedUpgradeSnapshot(db)
			if err != nil || Hash(after) != Hash(before) {
				t.Fatal("failed attempt changed original", err)
			}
			current, err := preparedUpgradeSchema(db)
			if err != nil || current != schemas.Source24 {
				t.Fatal("rollback changed schema", err)
			}
		})
	}
}

func TestPauseMigrationReleaseAndOldPlanRemainExact(t *testing.T) {
	root := pauseMigrationTestRelease(t)
	if _, _, err := pauseMigrationRelease(root, 25); err != nil {
		t.Fatal(err)
	}
	if _, _, err := preparedUpgradeRelease(root, 25); err == nil {
		t.Fatal("old release gate widened")
	}
	if _, err := UpgradeLocal(context.Background(), LocalUpgradeOptions{Plan: PauseSchemaUpgradePlan}); err == nil || !strings.Contains(err.Error(), "UPGRADE_PLAN_UNSUPPORTED") {
		t.Fatal("new plan entered source-matching old local route", err)
	}
	if _, err := pauseMigrationPath(filepath.Join(t.TempDir(), "source#alias.sqlite"), false); err == nil {
		t.Fatal("URI fragment path accepted")
	}
	if err := os.WriteFile(filepath.Join(root, "migrations/sqlite/0026_extra.sql"), []byte("SELECT 1;"), 0600); err != nil {
		t.Fatal(err)
	}
	if _, _, err := pauseMigrationRelease(root, 25); err == nil {
		t.Fatal("extra release migration accepted")
	}
}
