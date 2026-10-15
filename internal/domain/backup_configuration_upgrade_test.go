package domain

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"researchos.local/research-os/adapters/protectedstore"
	"researchos.local/research-os/internal/store"
)

func configurationMigrationFiles(t *testing.T) []string {
	t.Helper()
	// Historical startup-guard tests retain their exact schema23 release even
	// when the current checkout also contains the independently pinned0024.
	root := configurationUpgradeReleaseFixture(t, 23)
	files, err := filepath.Glob(filepath.Join(root, "migrations/sqlite/[0-9][0-9][0-9][0-9]_*.sql"))
	if err != nil || len(files) != 23 {
		t.Fatalf("actual migration inputs: %d %v", len(files), err)
	}
	return files
}

func configurationUpgradeReleaseFixture(t *testing.T, n int) string {
	t.Helper()
	root := queueUpgradeReleaseFixture(t, 22)
	paths := []string{"internal/api/contracts/client.protocol.schema.json", "internal/api/contracts/domain.schema.json"}
	if n == 23 {
		paths = append(paths, "migrations/sqlite/0023_host_model_configuration.sql")
	}
	for _, path := range paths {
		raw, e := os.ReadFile(filepath.Join("../..", path))
		if e != nil {
			t.Fatal(e)
		}
		dest := filepath.Join(root, path)
		if e = os.MkdirAll(filepath.Dir(dest), 0700); e != nil {
			t.Fatal(e)
		}
		if e = os.WriteFile(dest, raw, 0600); e != nil {
			t.Fatal(e)
		}
	}
	if _, _, e := upgradeConfigurationRelease(root, n); e != nil {
		t.Fatal(e)
	}
	return root
}
func configurationUpgradeFixture(t *testing.T) (LocalUpgradeOptions, *fixture) {
	t.Helper()
	opt, f := queueUpgradeFixture(t)
	raw, e := os.ReadFile("../../migrations/sqlite/0022_client_command_queue.sql")
	if e != nil {
		t.Fatal(e)
	}
	add, e := os.ReadFile("../../migrations/sqlite/next_v24_sessions.sql")
	if e != nil {
		t.Fatal(e)
	}
	if e = upgradeQueueMigration(context.Background(), f.db, raw, add); e != nil {
		t.Fatal(e)
	}
	opt.SourceRoot = configurationUpgradeReleaseFixture(t, 22)
	opt.TargetRoot = configurationUpgradeReleaseFixture(t, 23)
	opt.Plan = ConfigurationSchemaUpgradePlan
	return opt, f
}

func configurationEvidenceSnapshot(t *testing.T, db *sql.DB, name string) {
	t.Helper()
	root := os.Getenv("RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR")
	if root == "" {
		root = t.TempDir()
	}
	dir := filepath.Join(root, t.Name())
	if e := os.MkdirAll(dir, 0700); e != nil {
		t.Fatal(e)
	}
	path := filepath.Join(dir, name+".sqlite")
	if _, e := db.Exec(`VACUUM INTO '` + strings.ReplaceAll(path, `'`, `''`) + `'`); e != nil {
		t.Fatal(e)
	}
	raw, e := os.ReadFile(path)
	if e != nil {
		t.Fatal(e)
	}
	t.Log("CONFIGURATION_SQLITE_SNAPSHOT " + string(Bytes(Object{"path": path, "sha256": Digest(raw), "closed_snapshot": true, "fixture_only": true})))
}

type configurationUpgradePort struct {
	workspace string
	admitErr  error
}

func (p configurationUpgradePort) ResolveGoalBinding(context.Context, *sql.Tx, string, string, string) (string, string, error) {
	return p.workspace, "fixture-unqualified-model", nil
}
func (p configurationUpgradePort) ValidateBinding(_ context.Context, _ *sql.Tx, _, _, workspace, model string) error {
	if workspace != p.workspace || model != "fixture-unqualified-model" {
		return fmt.Errorf("fixture binding mismatch")
	}
	return nil
}
func (p configurationUpgradePort) AdmitTurn(context.Context, *sql.Tx, string, string, Object) error {
	return p.admitErr
}

func configurationPublicCommand(t *testing.T, f *fixture, svc *ClientService, env *Envelope) *Response {
	t.Helper()
	decoded, e := DecodeEnvelope(Bytes(env))
	if e != nil {
		t.Fatal(e)
	}
	tx, e := f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	defer tx.Rollback()
	reply, _, e := svc.Execute(context.Background(), tx, decoded, f.owner)
	if e != nil {
		t.Fatal(e)
	}
	if e = tx.Commit(); e != nil {
		t.Fatal(e)
	}
	return reply
}

func TestConfigurationUpgradeActiveQueueRecovery(t *testing.T) {
	opt, f := configurationUpgradeFixture(t)
	f.db.Close()
	recordPath := os.Getenv("RESEARCHOS_HISTORICAL22_ACTIVE_RECORD")
	expectedHash := os.Getenv("RESEARCHOS_HISTORICAL22_ACTIVE_RECORD_SHA256")
	if recordPath == "" || expectedHash == "" {
		t.Fatal("pinned historical22 active queue fixture record required")
	}
	recordRaw, e := os.ReadFile(recordPath)
	if e != nil || Digest(recordRaw) != expectedHash {
		t.Fatal("fixture record pin", e)
	}
	var record struct {
		DBPath             string `json:"db_path"`
		DBSHA              string `json:"db_sha256"`
		SchemaMin          int    `json:"schema_min"`
		SchemaMax          int    `json:"schema_max"`
		SchemaCount        int    `json:"schema_count"`
		Identities         int    `json:"identities_table_count"`
		Project            string `json:"project"`
		RunID              string `json:"run_id"`
		RunEpoch           int64  `json:"run_lease_epoch"`
		BeforeHash         string `json:"preupgrade_rows_hash"`
		ExternalDispatches int    `json:"external_dispatch_count"`
	}
	if e = json.Unmarshal(recordRaw, &record); e != nil {
		t.Fatal(e)
	}
	dbRaw, e := os.ReadFile(record.DBPath)
	if e != nil || Digest(dbRaw) != record.DBSHA || record.SchemaMin != 1 || record.SchemaMax != 22 || record.SchemaCount != 22 || record.Identities != 0 || record.ExternalDispatches != 0 || record.RunID == "" || record.Project == "" {
		t.Fatal("historical22 fixture bytes or claims", e)
	}
	// SQLite may checkpoint a database when opened. Keep the historical helper
	// output immutable and upgrade an exact per-test byte copy instead.
	opt.Source = filepath.Join(t.TempDir(), "historical22-source.sqlite")
	if e = os.WriteFile(opt.Source, dbRaw, 0600); e != nil {
		t.Fatal(e)
	}
	sourceDB, e := store.Open(opt.Source)
	if e != nil {
		t.Fatal(e)
	}
	var min, max, count, identities int
	if e = sourceDB.QueryRow(`SELECT min(version),max(version),count(*) FROM schema_migrations`).Scan(&min, &max, &count); e != nil || min != 1 || max != 22 || count != 22 {
		t.Fatal(min, max, count, e)
	}
	if e = sourceDB.QueryRow(`SELECT count(*) FROM sqlite_master WHERE type='table' AND name='client_command_identities'`).Scan(&identities); e != nil || identities != 0 {
		t.Fatal(identities, e)
	}
	before, e := upgradeRows(sourceDB)
	if e != nil || Hash(before) != record.BeforeHash {
		t.Fatal("historical22 row pin", e)
	}
	configurationEvidenceSnapshot(t, sourceDB, "source22")
	if e = sourceDB.Close(); e != nil {
		t.Fatal(e)
	}
	ctx := context.Background()
	report, e := UpgradeLocal(ctx, opt)
	if e != nil || report.Status != "RESTORED_RECONCILIATION_REQUIRED" {
		t.Fatal(report, e)
	}
	db, e := store.Open(filepath.Join(opt.Destination, "researchos.sqlite"))
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	after, e := upgradeRows(db)
	if e != nil {
		t.Fatal(e)
	}
	if e = upgradeConfigurationRecoveryInvariant(before, after, opt.Destination); e != nil {
		t.Fatal(e)
	}
	var status string
	var epoch int64
	if e = db.QueryRow(`SELECT json_extract(body,'$.status'),json_extract(body,'$.lease_epoch') FROM domain_objects WHERE kind='Run' AND id=?`, record.RunID).Scan(&status, &epoch); e != nil || status != "RECONCILING" || Hash(epoch) != Hash(record.RunEpoch) {
		t.Fatal(status, epoch, e)
	}
	var unknown, pending int
	if e = db.QueryRow(`SELECT count(*) FROM client_command_queue WHERE state='UNKNOWN'`).Scan(&unknown); e != nil {
		t.Fatal(e)
	}
	if e = db.QueryRow(`SELECT count(*) FROM client_control_requests WHERE state='RECONCILING'`).Scan(&pending); e != nil || unknown != 4 || pending != 1 {
		t.Fatal(unknown, pending, e)
	}
	if Hash(before["idempotency"]) != Hash(after["idempotency"]) || Hash(before["runtime_dispatches"]) != Hash(after["runtime_dispatches"]) {
		t.Fatal("original response or dispatch identity changed")
	}
	configurationEvidenceSnapshot(t, db, "restored23")
	for _, table := range []string{"client_sessions", "client_queue_fences", "client_command_queue", "client_control_requests", "client_control_receipts", "idempotency", "resource_effects", "domain_versions"} {
		changed := upgradeData{}
		for k, v := range after {
			changed[k] = v
		}
		changed[table] = nil
		if len(after[table]) == 0 {
			continue
		}
		if e = upgradeConfigurationRecoveryInvariant(before, changed, opt.Destination); e == nil {
			t.Fatal("lost history accepted: " + table)
		}
	}
	t.Log("actual public admission/ACK retained; unresolved queue -> UNKNOWN at same generation; active Run fenced at same epoch; no new dispatch; ACK finalization remains outside scope")
}

// Child process deliberately uses only old schema22 SQL and the SQLite driver,
// not New, the new preflight, or any schema23-specific behavior.
func TestConfigurationUpgradeLegacySQLChild(t *testing.T) {
	path := os.Getenv("RESEARCHOS_CONFIGURATION_LEGACY_SQL_PATH")
	if path == "" {
		// Normal suite execution verifies the legacy statement against an exact
		// numbered22 fixture; subprocess runs below exercise the native lock.
		db, _ := configurationDB(t, 22, true)
		var version int
		if e := db.QueryRow(`SELECT max(version) FROM schema_migrations`).Scan(&version); e != nil || version != 22 {
			t.Fatal(version, e)
		}
		if _, e := db.Exec(`UPDATE resource_write_lock SET value=value WHERE id=1`); e != nil {
			t.Fatal(e)
		}
		return
	}
	db, e := sql.Open("sqlite", path)
	if e != nil {
		fmt.Println("open", e)
		os.Exit(2)
	}
	defer db.Close()
	db.SetMaxOpenConns(1)
	if _, e = db.Exec(`PRAGMA busy_timeout=100`); e != nil {
		fmt.Println("timeout", e)
		os.Exit(2)
	}
	if os.Getenv("RESEARCHOS_CONFIGURATION_LEGACY_SQL_MODE") == "read" {
		var version int
		e = db.QueryRow(`SELECT max(version) FROM schema_migrations`).Scan(&version)
		fmt.Println("legacy-read", version, e)
	} else {
		_, e = db.Exec(`UPDATE resource_write_lock SET value=value WHERE id=1`)
		fmt.Println("legacy-write", e)
	}
	if e != nil {
		os.Exit(11)
	}
	os.Exit(0)
}

func TestConfigurationUpgradeLegacyWriterLock(t *testing.T) {
	opt, f := configurationUpgradeFixture(t)
	fake := &upgradeFake{summary: qualificationSummary(t)}
	upgradeSeedQualifications(t, f, fake.summary)
	f.db.Close()
	program, e := os.Executable()
	if e != nil {
		t.Fatal(e)
	}
	raw, e := os.ReadFile(program)
	if e != nil {
		t.Fatal(e)
	}
	attempt := func(mode string) (int, string) {
		cmd := exec.Command(program, "-test.run=^TestConfigurationUpgradeLegacySQLChild$")
		cmd.Env = append(os.Environ(), "RESEARCHOS_CONFIGURATION_LEGACY_SQL_PATH="+opt.Source, "RESEARCHOS_CONFIGURATION_LEGACY_SQL_MODE="+mode)
		output, e := cmd.CombinedOutput()
		exit := 0
		if e != nil {
			if failure, ok := e.(*exec.ExitError); ok {
				exit = failure.ExitCode()
			} else {
				t.Fatal(e)
			}
		}
		t.Log("LEGACY_SQL_PROCESS " + string(Bytes(Object{"argv": cmd.Args, "mode": mode, "exit": exit, "stdout": string(output), "binary_hash": Digest(raw)})))
		return exit, string(output)
	}
	if code, _ := attempt("read"); code != 0 {
		t.Fatal("legacy source read before lock")
	}
	if code, _ := attempt("write"); code != 0 {
		t.Fatal("legacy source write before lock")
	}
	checks := 0
	v := fake.verifier()
	v.summary = func(context.Context) (protectedstore.SafeSummary, error) {
		checks++
		read, _ := attempt("read")
		write, _ := attempt("write")
		if write != 11 {
			return protectedstore.SafeSummary{}, fmt.Errorf("legacy writer escaped held upgrade lock: %d", write)
		}
		t.Logf("refresh=%d read_exit=%d write_exit=%d destination_still_absent", checks, read, write)
		if _, e := os.Stat(opt.Destination); !os.IsNotExist(e) {
			return protectedstore.SafeSummary{}, fmt.Errorf("early publication")
		}
		return fake.summary, nil
	}
	report, e := upgradeLocal(context.Background(), opt, v)
	if e != nil || report.Status != "RESTORED_RECONCILIATION_REQUIRED" {
		t.Fatal(report, e)
	}
	if checks < 3 || fake.reads != 0 {
		t.Fatal("missing lock phases or protected read", checks, fake.reads)
	}
	if code, _ := attempt("read"); code != 0 {
		t.Fatal("legacy source reopen read after lock")
	}
	if code, _ := attempt("write"); code != 0 {
		t.Fatal("legacy source reopen write after lock")
	}
	t.Log("source lock spans all coordinator protected refresh phases until prepublication; after close old SQL22 writer can reopen: explicit single-writer cutover remains required")
}

func TestConfigurationUpgradeFrozen22ProgramLock(t *testing.T) {
	program, root, target := os.Getenv("RESEARCHOS_CONFIGURATION_OLD_CONTROL"), os.Getenv("RESEARCHOS_CONFIGURATION_OLD_ROOT"), os.Getenv("RESEARCHOS_CONFIGURATION_TARGET_PROGRAM")
	if program == "" || root == "" || target == "" {
		t.Fatal("explicit source22/target23 compiled programs and frozen source22 root required")
	}
	raw, e := os.ReadFile(program)
	if e != nil || Digest(raw) != "sha256:0cba028c2f8222bef5000a292b1d52346eb534f026f0ee34b4bf55e8a6f033e6" {
		t.Fatal("frozen source22 binary mismatch", e)
	}
	if _, _, e = upgradeConfigurationRelease(root, 22); e != nil {
		t.Fatal(e)
	}
	opt, f := configurationUpgradeFixture(t)
	fake := &upgradeFake{summary: qualificationSummary(t)}
	upgradeSeedQualifications(t, f, fake.summary)
	f.db.Close()
	// The original control program uses this fixed product database basename.
	renamed := filepath.Join(filepath.Dir(opt.Source), "researchos.sqlite")
	if e = os.Rename(opt.Source, renamed); e != nil {
		t.Fatal(e)
	}
	opt.Source = renamed
	opt.SourceRoot = root
	opt.SourceProgram = program
	opt.TargetProgram = target
	attempts := 0
	write := func() (int, string) {
		attempts++
		credential := filepath.Join(t.TempDir(), "ephemeral-fixture-credential.json")
		cmd := exec.Command(program, "-issue-credential", f.owner, "-credential-file", credential)
		cmd.Dir = root
		cmd.Env = append(os.Environ(), "RESEARCHOS_DATA_DIR="+filepath.Dir(opt.Source))
		var stdout, stderr bytes.Buffer
		cmd.Stdout = &stdout
		cmd.Stderr = &stderr
		start := Now()
		err := cmd.Run()
		exit := 0
		if err != nil {
			if x, ok := err.(*exec.ExitError); ok {
				exit = x.ExitCode()
			} else {
				t.Fatal(err)
			}
		}
		record := Object{"actualargv": cmd.Args, "cwd": root, "source_commit": "396287cc5427eb125aaedb8a2b7fadf63e6b9322", "binary_hash": Digest(raw), "exit": exit, "started_at": start, "ended_at": Now(), "stdout": stdout.String(), "stderr": stderr.String(), "credential_bytes_read": false}
		t.Log("FROZEN22_PRODUCT_INVOCATION " + string(Bytes(record)))
		if evidence := os.Getenv("RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR"); evidence != "" {
			dir := filepath.Join(evidence, t.Name())
			if e = os.MkdirAll(dir, 0700); e != nil {
				t.Fatal(e)
			}
			prefix := filepath.Join(dir, fmt.Sprintf("old22-%02d", attempts))
			for suffix, data := range map[string][]byte{".stdout": stdout.Bytes(), ".stderr": stderr.Bytes(), ".invocation.json": Bytes(record)} {
				if e = os.WriteFile(prefix+suffix, data, 0600); e != nil {
					t.Fatal(e)
				}
			}
		}
		return exit, stderr.String()
	}
	if code, output := write(); code != 0 {
		t.Fatalf("genuine frozen22 program cannot access matched22 fixture: %d %s", code, output)
	}
	checks := 0
	v := fake.verifier()
	v.summary = func(context.Context) (protectedstore.SafeSummary, error) {
		checks++
		code, output := write()
		if code == 0 || !(strings.Contains(output, "locked") || strings.Contains(output, "SQLITE_BUSY")) {
			return protectedstore.SafeSummary{}, fmt.Errorf("frozen22 writer not refused by SQLite lock: %d %s", code, output)
		}
		if _, e = os.Stat(opt.Destination); !os.IsNotExist(e) {
			return protectedstore.SafeSummary{}, fmt.Errorf("early publication")
		}
		return fake.summary, nil
	}
	report, e := upgradeLocal(context.Background(), opt, v)
	if e != nil || report.Status != "RESTORED_RECONCILIATION_REQUIRED" {
		t.Fatal(report, e)
	}
	if checks < 3 || fake.reads != 0 {
		t.Fatal("incomplete lock phases", checks, fake.reads)
	}
	if code, output := write(); code != 0 {
		t.Fatal("frozen22 program cannot reopen original after lock release", code, output)
	}
	t.Logf("genuine frozen22 administration wrote before/after lock; %d native attempts refused during snapshot/restore/prepublication; all credentials ephemeral fixture only, values never read; original remains reusable so single-writer cutover is required", checks)
}

func TestConfigurationUpgradePostSnapshotFaults(t *testing.T) {
	for _, fault := range []string{"semantic", "program_drift"} {
		t.Run(fault, func(t *testing.T) {
			opt, f := configurationUpgradeFixture(t)
			fake := &upgradeFake{summary: qualificationSummary(t)}
			upgradeSeedQualifications(t, f, fake.summary)
			before, e := upgradeRows(f.db)
			if e != nil {
				t.Fatal(e)
			}
			f.db.Close()
			original, e := os.ReadFile(opt.TargetProgram)
			if e != nil {
				t.Fatal(e)
			}
			copyProgram := filepath.Join(t.TempDir(), "candidate.exe")
			if e = os.WriteFile(copyProgram, original, 0700); e != nil {
				t.Fatal(e)
			}
			opt.TargetProgram = copyProgram
			injected := false
			v := fake.verifier()
			v.summary = func(context.Context) (protectedstore.SafeSummary, error) {
				if _, e := os.Stat(filepath.Join(opt.Snapshot, "manifest.json")); e == nil {
					injected = true
					if fault == "semantic" {
						return protectedstore.SafeSummary{}, fmt.Errorf("injected semantic dependency unavailable after stable snapshot")
					}
					if e = os.WriteFile(copyProgram, append(original, 0), 0700); e != nil {
						return protectedstore.SafeSummary{}, e
					}
				}
				return fake.summary, nil
			}
			_, e = upgradeLocal(context.Background(), opt, v)
			if e == nil || !injected {
				t.Fatal("fault did not reach isolated restore", e)
			}
			t.Log(e)
			if _, e = os.Stat(filepath.Join(opt.Snapshot, "manifest.json")); e != nil {
				t.Fatal("authenticated snapshot lost", e)
			}
			if _, e = os.Stat(opt.Destination); !os.IsNotExist(e) {
				t.Fatal("failed candidate published", e)
			}
			db, e := store.Open(opt.Source)
			if e != nil {
				t.Fatal(e)
			}
			defer db.Close()
			after, e := upgradeRows(db)
			if e != nil || Hash(before) != Hash(after) {
				t.Fatal("failed upgrade mutated source", e)
			}
			if fake.reads != 0 {
				t.Fatal("protected bytes read")
			}
			configurationEvidenceSnapshot(t, db, "unchanged-source22")
		})
	}
}

func TestConfigurationUpgradeNativeCLI(t *testing.T) {
	opt, f := configurationUpgradeFixture(t)
	program := os.Getenv("RESEARCHOS_CONFIGURATION_TARGET_PROGRAM")
	old := os.Getenv("RESEARCHOS_CONFIGURATION_OLD_CONTROL")
	root := os.Getenv("RESEARCHOS_CONFIGURATION_OLD_ROOT")
	if program == "" || old == "" || root == "" {
		t.Fatal("explicit matching binaries required")
	}
	opt.SourceRoot = root
	opt.SourceProgram = old
	opt.TargetProgram = program
	before, e := upgradeRows(f.db)
	if e != nil {
		t.Fatal(e)
	}
	configurationEvidenceSnapshot(t, f.db, "source22")
	f.db.Close()
	cmd := exec.Command(program, "upgrade-local", "--db", opt.Source, "--backup", opt.Snapshot, "--out", opt.Destination, "--key-file", opt.KeyFile, "--source-root", opt.SourceRoot, "--root", opt.TargetRoot, "--source-program", old, "--target-program", program, "--plan", ConfigurationSchemaUpgradePlan)
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	start := Now()
	err := cmd.Run()
	exit := 0
	if err != nil {
		if x, ok := err.(*exec.ExitError); ok {
			exit = x.ExitCode()
		} else {
			t.Fatal(err)
		}
	}
	cwd, e := os.Getwd()
	if e != nil {
		t.Fatal(e)
	}
	record := Object{"actualargv": cmd.Args, "cwd": cwd, "started_at": start, "ended_at": Now(), "exit": exit, "stdout": stdout.String(), "stderr": stderr.String()}
	t.Log("CONFIGURATION_NATIVE_CLI " + string(Bytes(record)))
	if evidence := os.Getenv("RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR"); evidence != "" {
		dir := filepath.Join(evidence, t.Name())
		if e = os.MkdirAll(dir, 0700); e != nil {
			t.Fatal(e)
		}
		for name, data := range map[string][]byte{"native.stdout": stdout.Bytes(), "native.stderr": stderr.Bytes(), "native.invocation.json": Bytes(record)} {
			if e = os.WriteFile(filepath.Join(dir, name), data, 0600); e != nil {
				t.Fatal(e)
			}
		}
	}
	if exit != 0 || !bytes.Contains(stdout.Bytes(), []byte("RESTORED_RECONCILIATION_REQUIRED")) {
		t.Fatal(exit, stderr.String())
	}
	db, e := store.Open(filepath.Join(opt.Destination, "researchos.sqlite"))
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	after, e := upgradeRows(db)
	if e != nil {
		t.Fatal(e)
	}
	if e = upgradeConfigurationRecoveryInvariant(before, after, opt.Destination); e != nil {
		t.Fatal(e)
	}
	configurationEvidenceSnapshot(t, db, "restored23")
}

func TestConfigurationUpgradeNumberedOnlyAndMalformedRefusal(t *testing.T) {
	opt, f := configurationUpgradeFixture(t)
	f.db.Close()
	db, path := configurationDB(t, 22, false)
	before, e := backupSchema(db)
	if e != nil {
		t.Fatal(e)
	}
	db.Close()
	opt.Source = path
	if _, e = UpgradeLocal(context.Background(), opt); e == nil || !strings.Contains(e.Error(), "UPGRADE_SOURCE_SCHEMA") {
		t.Fatal("numbered-only22 did not fail exact schema", e)
	}
	if _, e = os.Stat(opt.Snapshot); !os.IsNotExist(e) {
		t.Fatal("numbered-only source produced snapshot", e)
	}
	again, e := store.Open(path)
	if e != nil {
		t.Fatal(e)
	}
	defer again.Close()
	after, e := backupSchema(again)
	if e != nil || before != after {
		t.Fatal("source was repaired", e)
	}
	for _, ddl := range []string{`CREATE TABLE unrelated(x TEXT)`, `CREATE TABLE schema_migrations(version TEXT);INSERT INTO schema_migrations VALUES('1')`, `CREATE TABLE schema_migrations(version INTEGER)`, `CREATE TABLE schema_migrations(version INTEGER);INSERT INTO schema_migrations VALUES(1),(1)`} {
		t.Run(fmt.Sprint(len(ddl)), func(t *testing.T) {
			d, e := store.Open(filepath.Join(t.TempDir(), "bad.sqlite"))
			if e != nil {
				t.Fatal(e)
			}
			defer d.Close()
			if _, e = d.Exec(ddl); e != nil {
				t.Fatal(e)
			}
			schema, e := backupSchema(d)
			if e != nil {
				t.Fatal(e)
			}
			if _, e = New(d, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql"); e == nil {
				t.Fatal("malformed inventory accepted")
			}
			current, e := backupSchema(d)
			if e != nil || schema != current {
				t.Fatal("refused after domain DDL", e)
			}
		})
	}
}

func TestConfigurationUpgradePublicRoundTrip(t *testing.T) {
	opt, f := configurationUpgradeFixture(t)
	before, e := upgradeRows(f.db)
	if e != nil {
		t.Fatal(e)
	}
	f.db.Close()
	report, e := UpgradeLocal(context.Background(), opt)
	if e != nil {
		t.Fatal(e)
	}
	if report.Status != "RESTORED_RECONCILIATION_REQUIRED" {
		t.Fatal(report)
	}
	source, e := store.Open(opt.Source)
	if e != nil {
		t.Fatal(e)
	}
	sourceRows, e := upgradeRows(source)
	source.Close()
	if e != nil || Hash(sourceRows) != Hash(before) {
		t.Fatal("source changed", e)
	}
	target, e := store.Open(filepath.Join(opt.Destination, "researchos.sqlite"))
	if e != nil {
		t.Fatal(e)
	}
	defer target.Close()
	after, e := upgradeRows(target)
	if e != nil {
		t.Fatal(e)
	}
	if e = upgradeConfigurationRecoveryInvariant(before, after, opt.Destination); e != nil {
		t.Fatal(e)
	}
	for table := range upgradeConfigurationTables {
		if len(after[table]) != 0 {
			t.Fatal("invented configuration")
		}
	}
	if _, e = New(target, filepath.Join(opt.TargetRoot, "spec/v2.0/contracts"), filepath.Join(opt.TargetRoot, "migrations/sqlite/0002_domain.sql")); e != nil {
		t.Fatal(e)
	}
	var path string
	if e = target.QueryRow(`SELECT json_extract(body,'$.real_path') FROM domain_objects WHERE kind='WorkspaceBinding'`).Scan(&path); e != nil {
		t.Fatal(e)
	}
	key, e := os.ReadFile(opt.KeyFile)
	if e != nil {
		t.Fatal(e)
	}
	backup := filepath.Join(t.TempDir(), "ordinary23")
	svc := &Service{DB: target, Contracts: f.s.Contracts}
	if _, e = svc.CreateBackupWithWorkspaces(context.Background(), backup, key, queueUpgradeWorkspace{path}); e != nil {
		t.Fatal(e)
	}
	restore := filepath.Join(t.TempDir(), "round23")
	var rebound string
	pin := func(_ context.Context, _ string, requests []WorkspaceRestoreRequest) ([]WorkspaceRestorePin, error) {
		pins := []WorkspaceRestorePin{}
		for _, r := range requests {
			rebound = r.RealPath
			pins = append(pins, WorkspaceRestorePin{AuthorizedRef: r.AuthorizedRef, RealPath: r.RealPath, HostPrincipalRef: "fixture-restored-user"})
		}
		return pins, nil
	}
	if _, e = RestoreBackup(context.Background(), backup, restore, RestoreOptions{Key: key, SupportedMigrations: upgradeVersions(23), Contracts: f.s.Contracts, DatabaseName: "researchos.sqlite", WorkspaceTarget: pin}); e != nil {
		t.Fatal(e)
	}
	round, e := store.Open(filepath.Join(restore, "researchos.sqlite"))
	if e != nil {
		t.Fatal(e)
	}
	defer round.Close()
	if rebound == "" || rebound == path {
		t.Fatal("workspace isolation missing")
	}
	if _, e = (&Service{DB: round, Contracts: f.s.Contracts}).CreateBackupWithWorkspaces(context.Background(), filepath.Join(t.TempDir(), "rebackup23"), key, queueUpgradeWorkspace{rebound}); e != nil {
		t.Fatal(e)
	}
	if _, e = round.Exec(`UPDATE idempotency SET body=body`); e == nil || !strings.Contains(e.Error(), "immutable replay") {
		t.Fatalf("immutable replay trigger %v", e)
	}
	t.Log("public matched22+session fence -> fixed23; source unchanged, workspace identity retained; public23 restore/rebackup uses new isolated workspace")
}

func TestConfigurationUpgradeReleaseAndMigrationRefusals(t *testing.T) {
	for _, path := range []string{"migrations/sqlite/0022_client_command_queue.sql", "migrations/sqlite/0023_host_model_configuration.sql", "migrations/sqlite/next_v24_sessions.sql", "internal/api/contracts/client.protocol.schema.json", "internal/api/contracts/domain.schema.json"} {
		t.Run(path, func(t *testing.T) {
			root := configurationUpgradeReleaseFixture(t, 23)
			p := filepath.Join(root, path)
			raw, e := os.ReadFile(p)
			if e != nil {
				t.Fatal(e)
			}
			if e = os.WriteFile(p, append(raw, '\n'), 0600); e != nil {
				t.Fatal(e)
			}
			if _, _, e = upgradeConfigurationRelease(root, 23); e == nil {
				t.Fatal("changed release accepted")
			}
		})
	}
	for _, bad := range []string{"DROP TRIGGER client_session_epoch_no_regression", "DROP INDEX client_sessions_run", "DELETE FROM schema_migrations WHERE version=22"} {
		t.Run(bad, func(t *testing.T) {
			opt, f := configurationUpgradeFixture(t)
			if _, e := f.db.Exec(bad); e != nil {
				t.Fatal(e)
			}
			before, e := upgradeRows(f.db)
			if e != nil {
				t.Fatal(e)
			}
			f.db.Close()
			if _, e = UpgradeLocal(context.Background(), opt); e == nil {
				t.Fatal("bad source accepted")
			}
			if _, e = os.Stat(opt.Snapshot); !os.IsNotExist(e) {
				t.Fatal("snapshot created before exact source gate", e)
			}
			if _, e = os.Stat(opt.Destination); !os.IsNotExist(e) {
				t.Fatal("target published", e)
			}
			db, e := store.Open(opt.Source)
			if e != nil {
				t.Fatal(e)
			}
			defer db.Close()
			after, e := upgradeRows(db)
			if e != nil || Hash(before) != Hash(after) {
				t.Fatal("source modified", e)
			}
		})
	}
	db, _ := configurationDB(t, 22, true)
	if _, e := db.Exec(`CREATE TRIGGER fixture_refuse23 BEFORE INSERT ON schema_migrations WHEN NEW.version=23 BEGIN SELECT RAISE(ABORT,'injected migration failure'); END`); e != nil {
		t.Fatal(e)
	}
	before, e := upgradeRows(db)
	if e != nil {
		t.Fatal(e)
	}
	schema, e := backupSchema(db)
	if e != nil {
		t.Fatal(e)
	}
	raw, e := os.ReadFile("../../migrations/sqlite/0023_host_model_configuration.sql")
	if e != nil {
		t.Fatal(e)
	}
	if e = upgradeConfigurationMigration(context.Background(), db, raw); e == nil {
		t.Fatal("fault accepted")
	}
	after, e := upgradeRows(db)
	if e != nil || Hash(before) != Hash(after) {
		t.Fatal("failed tx data drift", e)
	}
	current, e := backupSchema(db)
	if e != nil || current != schema {
		t.Fatal("failed tx DDL committed", e)
	}
	t.Log(fmt.Sprintf("fault rollback preserved %d tables and exact schema", len(before)))
}

func TestConfigurationUpgradeHostOnlyStartupGuard(t *testing.T) {
	for _, name := range []string{"auth_principals", "auth_credentials", "idempotency", "client_sessions", "client_command_queue", "runtime_dispatches", "domain_versions", "opaque_future_authority", "client_command_identities", "host_model_configurations", "host_model_config_heads"} {
		t.Run(name, func(t *testing.T) {
			db, err := sql.Open("sqlite", ":memory:")
			if err != nil {
				t.Fatal(err)
			}
			defer db.Close()
			db.SetMaxOpenConns(1)
			if _, err = db.Exec(`CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY); INSERT INTO schema_migrations VALUES(1); CREATE TABLE domain_objects(id TEXT); CREATE TABLE "` + name + `"(marker TEXT); INSERT INTO "` + name + `" VALUES('public-fixture')`); err != nil {
				t.Fatal(err)
			}
			before, err := backupSchema(db)
			if err != nil {
				t.Fatal(err)
			}
			err = CheckMigrationSafety(db, configurationMigrationFiles(t))
			if err == nil || !strings.Contains(err.Error(), "MIGRATION_PREBACKUP_REQUIRED") {
				t.Fatalf("host-only source accepted: %v", err)
			}
			after, _ := backupSchema(db)
			if before != after {
				t.Fatal("preflight changed schema")
			}
		})
	}
}

func TestConfigurationUpgradeFutureBeforeDomainDDL(t *testing.T) {
	for _, versions := range []string{"1,24", "1,3", "0,1", "1,2,99"} {
		t.Run(versions, func(t *testing.T) {
			db, err := store.Open(filepath.Join(t.TempDir(), "future.sqlite"))
			if err != nil {
				t.Fatal(err)
			}
			defer db.Close()
			if _, err = db.Exec(`CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY)`); err != nil {
				t.Fatal(err)
			}
			for _, v := range strings.Split(versions, ",") {
				if _, err = db.Exec("INSERT INTO schema_migrations VALUES(?)", v); err != nil {
					t.Fatal(err)
				}
			}
			before, _ := backupSchema(db)
			if _, err = New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql"); err == nil {
				t.Fatal("future/gapped inventory accepted")
			}
			after, _ := backupSchema(db)
			if before != after {
				t.Fatal("future refusal occurred after domain DDL")
			}
		})
	}
}

func TestConfigurationUpgradeFreshAndAdditiveGuard(t *testing.T) {
	ctx := context.Background()
	// This historical guard verifies release23 even when Main has SQL24.
	root := configurationUpgradeReleaseFixture(t, 23)
	db, err := store.Open(filepath.Join(t.TempDir(), "empty.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	if err = store.Bootstrap(ctx, db, filepath.Join(root, "migrations/sqlite/0001_bootstrap.sql")); err != nil {
		t.Fatal(err)
	}
	if _, err = New(db, filepath.Join(root, "spec/v2.0/contracts"), filepath.Join(root, "migrations/sqlite/0002_domain.sql")); err != nil {
		t.Fatal(err)
	}
	if _, err = db.Exec(`INSERT INTO auth_principals(id,roles) VALUES('fixture-owner','["OWNER"]')`); err != nil {
		t.Fatal(err)
	}
	if err = CheckMigrationSafety(db, configurationMigrationFiles(t)); err != nil {
		t.Fatalf("exact current populated source: %v", err)
	}
	if _, err = db.Exec("DROP TRIGGER client_session_epoch_no_regression"); err != nil {
		t.Fatal(err)
	}
	if err = CheckMigrationSafety(db, configurationMigrationFiles(t)); err == nil {
		t.Fatal("missing session fence silently installed")
	}
	// Real source22 with only numbered SQL is not a matched current22 schema.
	old, _ := configurationDB(t, 22, false)
	files := configurationMigrationFiles(t)[:22]
	if err = CheckMigrationSafety(old, files); err == nil {
		t.Fatal("numbered-only source22 accepted")
	}
	_ = os.Getenv("RESEARCHOS_GO") // The recorded runner supplies explicit pinned tools.
}
