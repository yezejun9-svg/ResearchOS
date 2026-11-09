package domain

// Synthetic migration primitive fixtures. These are not matching-program backup,
// isolated restore, historical release authority, or product upgrade acceptance.
import (
	"context"
	"database/sql"
	_ "embed"
	"fmt"
	"os"
	"path/filepath"
	"researchos.local/research-os/internal/store"
	"strings"
	"testing"
)

// Exact Git 3225a31fd25969c6a5e071a2fc686cb4a835e162 blob
// 9efc768f8f4cfb6ac31e1f88a78ad095877328af; never derived by dropping a current column.
//
//go:embed testdata/pretranscript-3225a31f.sql
var legacyTranscriptDDL3225 []byte

var legacyFixtureMigrationSources = []struct{ filename, digest string }{
	{"0001_bootstrap.sql", "sha256:bb87c889e31fd5412b49743d106679f783b6dd21d874fe29d82d18a729ce3dbc"},
	{"0002_domain.sql", "sha256:90d6c36100cbfaddf85c23f603b686336d161e43eeeed47c034ab85415b25db4"},
	{"0003_context.sql", "sha256:50aa1579e4233cbb64ac30777e27c55cba29bab7ee0cc221a677f9a420a7159a"},
	{"0004_sources.sql", "sha256:d40152642778d8ea4e21148fd6517bdc8bf4c2582a8d6212b8cfdf7a470dea06"},
	{"0005_runtime.sql", "sha256:f3b9cd4c03f101c22c47a4fd7ad72593babe69de9abcd8a1ee3056fa6c23ade5"},
	{"0006_orchestration.sql", "sha256:cbc9ede2d2e46e1e68ac7120d2a99b29627f2e13b1fc82937e3ed13ac9b2317b"},
	{"0007_retrieval.sql", "sha256:eaa3963a3acdfcc1791982432c42dea9d4dd8f0baf7de51d278fce70bcd626bb"},
	{"0008_artifact_uses.sql", "sha256:adf17ad69203f0e700897a426f2d596496081bd5f3a964cbea8e3db9fc561ee7"},
	{"0009_retrieval_root_identity.sql", "sha256:48219da409abc3f9d353e8d91a71a387ea342e5c13aae711a36c28410b22fb4f"},
	{"0010_experiments.sql", "sha256:c197ff792f62a1be5903bb6967175512cb53bdb09ff276e06fa8542822024287"},
	{"0011_resources.sql", "sha256:45c082ae0980af14f5b0be2d5aae02622dcc15c8c566b442077b4c1fb0c9942b"},
	{"0012_experiment_execution.sql", "sha256:c81411769ef2bd3ec1d101f311ce37722036485b8e9d99d45ae9c9be48f088c0"},
	{"0013_research_cycles.sql", "sha256:188e0d6fbcffd3901d36109dcd421a21f7ef704574f62cd5c0f8af862c191d1e"},
	{"0014_remote_access.sql", "sha256:687b01552260301a8f3f39e92422f16d0b2e310b38f77d1b025566f9a9cfa4d7"},
	{"0015_evolution_fixture.sql", "sha256:d70dd0580e89e2a7940c90ee771b2bd94551a42d8cda7fadfe83b60509852fe9"},
	{"0016_runtime_qualification.sql", "sha256:7fd44c42be4c0753c367fc8361e9990b56e4f9a001a5f443ef62d0d87d05a03f"},
	{"0017_runtime_dispatch.sql", "sha256:e5a2671c25725205bb5306c7fcbab254d53e3ef7a0448a163a41c5ac24a7b558"},
	{"0018_intent_planning.sql", "sha256:7592b2b47d2e305f9ec26937830b5c0606c7d90622401a0b6b80a8c8a67db4e0"},
	{"0019_evolution_release_operations.sql", "sha256:54ff6eb7a7ca588df738f5bd68b6f6851d86916cef435abaac15d1f8bd6e131e"},
	{"0020_research_cycle_work.sql", "sha256:3f90bdb0e828cec90bc370f34abed0cf0629dc78dcc01dda250c18cda49e528a"},
}

func legacyFixtureMigrationSQL(version int) ([]byte, error) {
	if version < 1 || version > len(legacyFixtureMigrationSources) {
		return nil, fmt.Errorf("legacy fixture migration version unavailable")
	}
	source := legacyFixtureMigrationSources[version-1]
	raw, err := os.ReadFile(filepath.Join("../../migrations/sqlite", source.filename))
	if err != nil {
		return nil, err
	}
	if Digest(raw) != source.digest {
		return nil, fmt.Errorf("legacy fixture migration source pin differs")
	}
	return raw, nil
}

func legacyFixtureMigrationFiles() []string {
	files := make([]string, 0, len(legacyFixtureMigrationSources))
	for _, source := range legacyFixtureMigrationSources {
		files = append(files, filepath.Join("../../migrations/sqlite", source.filename))
	}
	return files
}

// The actual historical SQL and its version row commit in the same transaction.
// No hole is filled by relabelling a current database or recording unexecuted SQL.
func applyLegacyFixtureMigration(ctx context.Context, db *sql.DB, version int, raw []byte) (sql.Result, error) {
	if version < 2 || version > len(legacyFixtureMigrationSources) || Digest(raw) != legacyFixtureMigrationSources[version-1].digest {
		return nil, fmt.Errorf("legacy fixture migration source pin differs")
	}
	applied, err := checkMigrationInventory(db, legacyFixtureMigrationFiles())
	if err != nil {
		return nil, err
	}
	if applied != version-1 {
		return nil, fmt.Errorf("legacy fixture migration is not the next contiguous version")
	}
	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()
	result, err := tx.ExecContext(ctx, string(raw))
	if err != nil {
		return nil, err
	}
	if _, err = tx.ExecContext(ctx, "INSERT INTO schema_migrations(version) VALUES(?)", version); err != nil {
		return nil, err
	}
	if err = tx.Commit(); err != nil {
		return nil, err
	}
	return result, nil
}

func applyLegacyFixtureMigrationRange(ctx context.Context, db *sql.DB, first, last int) error {
	if first < 2 || first > last || last > len(legacyFixtureMigrationSources) {
		return fmt.Errorf("legacy fixture migration range unavailable")
	}
	for version := first; version <= last; version++ {
		raw, err := legacyFixtureMigrationSQL(version)
		if err != nil {
			return err
		}
		if _, err = applyLegacyFixtureMigration(ctx, db, version, raw); err != nil {
			return err
		}
	}
	return nil
}

func legacyTranscriptFixtureDatabase(t *testing.T) (*sql.DB, error) {
	t.Helper()
	db, err := store.Open(filepath.Join(t.TempDir(), "historical20-transcript.sqlite"))
	if err != nil {
		return nil, err
	}
	t.Cleanup(func() { _ = db.Close() })
	if _, err = legacyFixtureMigrationSQL(1); err != nil {
		return nil, err
	}
	if err = store.Bootstrap(context.Background(), db, "../../migrations/sqlite/0001_bootstrap.sql"); err != nil {
		return nil, err
	}
	if err = applyLegacyFixtureMigrationRange(context.Background(), db, 2, 20); err != nil {
		return nil, err
	}
	if Digest(legacyTranscriptDDL3225) != "sha256:3b00677902c3be1dbffb8f7505293bae7242dc976e8017562ab86254ac212f2a" {
		return nil, fmt.Errorf("historical transcript DDL pin differs")
	}
	if _, err = db.Exec(string(legacyTranscriptDDL3225)); err != nil {
		return nil, err
	}
	var column int
	if err = db.QueryRow("SELECT count(*) FROM pragma_table_info('client_sessions') WHERE name='transcript_artifact_id'").Scan(&column); err != nil {
		return nil, err
	}
	if column != 0 {
		return nil, fmt.Errorf("historical transcript DDL already has current column")
	}
	return db, nil
}

// The project index is synthetic fixture data copied from the existing Project
// fixture, while all schema bytes and version rows are the genuine historical
// prefix. No authentication, credential, model, Run or runtime state is copied.
// This test uses only f.db/f.project afterward; it does not run f.s on this DB.
func useLegacyTranscriptFixture(t *testing.T, f *fixture) error {
	t.Helper()
	db, err := legacyTranscriptFixtureDatabase(t)
	if err != nil {
		return err
	}
	rows, err := f.db.Query("SELECT project,kind,id,revision,body,content_hash,immutable FROM domain_objects WHERE kind IN ('Project','ProjectProfile') AND id=? ORDER BY project,kind,id", f.project)
	if err != nil {
		return err
	}
	defer rows.Close()
	copied := 0
	for rows.Next() {
		var project, kind, id, body string
		var revision, immutable int64
		var contentHash sql.NullString
		if err = rows.Scan(&project, &kind, &id, &revision, &body, &contentHash, &immutable); err != nil {
			return err
		}
		if _, err = db.Exec("INSERT INTO domain_objects(project,kind,id,revision,body,content_hash,immutable) VALUES(?,?,?,?,?,?,?)", project, kind, id, revision, body, contentHash, immutable); err != nil {
			return err
		}
		copied++
	}
	if err = rows.Err(); err != nil {
		return err
	}
	if copied == 0 {
		return fmt.Errorf("historical transcript fixture lacks Project identity")
	}
	f.db = db
	return nil
}

// Hash all schema definitions and public synthetic fixture table values to prove
// rejected New performs no additional DDL or data mutation. Values are never logged.
func legacyFixtureFingerprint(t *testing.T, db *sql.DB) string {
	t.Helper()
	rows, err := db.Query("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name")
	if err != nil {
		t.Fatal(err)
	}
	var schema []any
	var tables []string
	for rows.Next() {
		var typ, name, table string
		var ddl sql.NullString
		if err = rows.Scan(&typ, &name, &table, &ddl); err != nil {
			rows.Close()
			t.Fatal(err)
		}
		schema = append(schema, Object{"type": typ, "name": name, "table": table, "sql": ddl})
		if typ == "table" {
			tables = append(tables, name)
		}
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		t.Fatal(err)
	}
	data := Object{}
	for _, name := range tables {
		quoted := strings.ReplaceAll(name, "\"", "\"\"")
		records, e := db.Query("SELECT * FROM \"" + quoted + "\"")
		if e != nil {
			t.Fatal(e)
		}
		columns, e := records.Columns()
		if e != nil {
			records.Close()
			t.Fatal(e)
		}
		values := []any{}
		for records.Next() {
			row := make([]any, len(columns))
			refs := make([]any, len(columns))
			for i := range refs {
				refs[i] = &row[i]
			}
			if e = records.Scan(refs...); e != nil {
				records.Close()
				t.Fatal(e)
			}
			values = append(values, row)
		}
		e = records.Err()
		records.Close()
		if e != nil {
			t.Fatal(e)
		}
		data[name] = Object{"columns": columns, "rows": values}
	}
	return Hash(Object{"schema": schema, "data": data})
}

func legacyFixtureExpectNewRefusal(t *testing.T, db *sql.DB, code string) {
	t.Helper()
	before := legacyFixtureFingerprint(t, db)
	_, err := New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if err == nil || !(err.Error() == code || strings.HasPrefix(err.Error(), code+":")) {
		t.Fatalf("ordinary startup did not preserve %s refusal: %v", code, err)
	}
	if after := legacyFixtureFingerprint(t, db); after != before {
		t.Fatal("rejected startup changed fixture schema or data")
	}
}
