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
	schemas, err := pauseMigrationTemplate(context.Background(), sqls, contracts)
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
	for _, mutation := range []string{"sql", "source-schema", "target-schema", "stale-rows", "version", "trigger"} {
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
