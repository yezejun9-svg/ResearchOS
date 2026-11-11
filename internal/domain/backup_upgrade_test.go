package domain

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"researchos.local/research-os/adapters/protectedstore"
	"researchos.local/research-os/internal/store"
)

// The fake is only reachable through this package's unexported test seam.
// All records and labels below are public fixtures; no installed service call.
type upgradeFake struct {
	summary                        protectedstore.SafeSummary
	reads, descriptions, refreshes int
	fail                           string
}

func (f *upgradeFake) Ready(context.Context, string) error {
	if f.fail == "missing" {
		return protectedstore.ErrUnavailable
	}
	return nil
}
func (f *upgradeFake) Boundary(context.Context) (protectedstore.Boundary, error) {
	b := protectedstore.Boundary{Mode: "INDEPENDENT_VERIFIER", OwnerSID: upgradeServiceSID, IndependentIdentity: true}
	if f.fail == "identity" {
		b.OwnerSID = "S-1-5-21-PUBLIC-FIXTURE-WRONG"
	}
	if f.fail == "same-user" {
		b.UnrestrictedSameUserCanRead = true
	}
	return b, nil
}
func (f *upgradeFake) Describe(_ context.Context, project, ticket string) (protectedstore.Blob, error) {
	f.descriptions++
	d := *f.summary.Frozen.Dataset
	d.Project = project
	if ticket != d.Ticket {
		return d, protectedstore.ErrNotFound
	}
	switch f.fail {
	case "hash":
		d.Hash = Digest([]byte("wrong public fixture"))
	case "size":
		d.Size++
	case "media":
		d.MediaType = "text/plain"
	case "mode":
		d.MeasurementMode = "FIXTURE"
	case "project":
		d.Project = "wrong"
	case "ticket":
		d.Ticket = "ps1:00000000000000000000000000000000"
	}
	return d, nil
}
func (f *upgradeFake) Read(context.Context, protectedstore.Blob) ([]byte, error) {
	f.reads++
	return nil, fmt.Errorf("TEST_PRIVATE_READ_FORBIDDEN")
}
func (f *upgradeFake) verifier() upgradeVerifier {
	return upgradeVerifier{provider: f, summary: func(context.Context) (protectedstore.SafeSummary, error) {
		f.refreshes++
		if f.fail == "late-change" && f.refreshes > 2 {
			return protectedstore.SafeSummary{}, protectedstore.ErrUnavailable
		}
		return f.summary, nil
	}}
}

func upgradeAssert(t *testing.T, id string, expected, actual any) {
	t.Helper()
	status := "PASS"
	if Hash(expected) != Hash(actual) {
		status = "FAIL"
	}
	fmt.Println("W17_UPGRADE_ASSERTION " + string(Bytes(Object{"assertion_id": id, "expected": expected, "actual": actual, "status": status, "scope": "PUBLIC_FIXTURE_NATIVE_FILES_ONLY", "private_body_read": false, "provider_calls": 0})))
	if status != "PASS" {
		t.Fatalf("%s: want %v got %v", id, expected, actual)
	}
}

func upgradeTestRelease(t *testing.T, count int) string {
	t.Helper()
	root := t.TempDir()
	for name := range upgradeMigrationHashes {
		if name[:4] > fmt.Sprintf("%04d", count) {
			continue
		}
		path := filepath.Join("migrations/sqlite", name)
		raw, e := os.ReadFile(filepath.Join("../..", path))
		if e != nil {
			t.Fatal(e)
		}
		if e = os.MkdirAll(filepath.Dir(filepath.Join(root, path)), 0700); e != nil {
			t.Fatal(e)
		}
		if e = os.WriteFile(filepath.Join(root, path), raw, 0600); e != nil {
			t.Fatal(e)
		}
	}
	for _, name := range []string{"domain.schema.json", "openapi.json"} {
		path := filepath.Join("spec/v2.0/contracts", name)
		raw, e := os.ReadFile(filepath.Join("../..", path))
		if e != nil {
			t.Fatal(e)
		}
		if e = os.MkdirAll(filepath.Dir(filepath.Join(root, path)), 0700); e != nil {
			t.Fatal(e)
		}
		if e = os.WriteFile(filepath.Join(root, path), raw, 0600); e != nil {
			t.Fatal(e)
		}
	}
	return root
}

func upgradeFixture(t *testing.T, protected bool, seeds ...func(*fixture)) (LocalUpgradeOptions, *fixture, *upgradeFake) {
	t.Helper()
	oldRoot, targetRoot := upgradeTestRelease(t, 13), upgradeTestRelease(t, 14)
	dbpath := filepath.Join(t.TempDir(), "source.sqlite")
	db, e := store.Open(dbpath)
	if e != nil {
		t.Fatal(e)
	}
	t.Cleanup(func() { db.Close() })
	// Seed through the current fixture host. The separate copy below still
	// creates a pristine schema13 source for the exact 13->14 upgrade test.
	if e = store.Bootstrap(context.Background(), db, "../../migrations/sqlite/0001_bootstrap.sql"); e != nil {
		t.Fatal(e)
	}
	svc, e := New(db, filepath.Join(targetRoot, "spec/v2.0/contracts"), "../../migrations/sqlite/0002_domain.sql")
	if e != nil {
		t.Fatal(e)
	}
	owner := Principal{ID: "fixture-owner", Roles: []string{"OWNER", "PLANNER", "SCHEDULER", "EXECUTOR"}, CanCreateProject: true}
	if e = svc.ProvisionPrincipal(context.Background(), owner); e != nil {
		t.Fatal(e)
	}
	token, e := svc.IssueCredential(context.Background(), owner.ID, 15*time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	f := &fixture{s: svc, db: db, h: svc.Handler(), owner: owner.ID, token: token, t: t}
	body := projectBody()
	body["source_configs"] = []any{Object{"source_id": ID(), "kind": "GITHUB", "required": true, "enabled": true, "query": "repo:example/public-fixture", "allowed_origins": []any{"https://github.com", "https://api.github.com"}, "credential_ref": nil}}
	project := f.expect(201, "POST", "/v1/projects", ID(), "", body)
	f.project = Str(project, "project_id")
	fake := &upgradeFake{summary: qualificationSummary(t)}
	if protected {
		upgradeSeedQualifications(t, f, fake.summary)
	}
	for _, seed := range seeds {
		seed(f)
	}
	f.artifact(Object{"public": "sealed upgrade fixture"}, Empty())
	// Generate valid public business records with the current fixture host, then
	// populate a separately created, pristine schema13 fixture. No source schema
	// is downgraded and no migration/guard production path is bypassed.
	dbpath = upgradeCopyFixture13(t, f, oldRoot)
	keyfile := filepath.Join(t.TempDir(), "upgrade.key")
	if e = os.WriteFile(keyfile, backupTestKey(t), 0600); e != nil {
		t.Fatal(e)
	}
	program, e := os.Executable()
	if e != nil {
		t.Fatal(e)
	}
	opt := LocalUpgradeOptions{Source: dbpath, Snapshot: filepath.Join(t.TempDir(), "encrypted"), Destination: filepath.Join(t.TempDir(), "upgraded"), KeyFile: keyfile, SourceRoot: oldRoot, TargetRoot: targetRoot, SourceProgram: program, TargetProgram: program, Plan: LocalUpgradePlan}
	return opt, f, fake
}

func upgradeCopyFixture13(t *testing.T, f *fixture, root string) string {
	t.Helper()
	path := filepath.Join(t.TempDir(), "researchos.sqlite")
	target, e := store.Open(path)
	if e != nil {
		t.Fatal(e)
	}
	t.Cleanup(func() { target.Close() })
	_, sqls, e := upgradeRelease(root, 13)
	if e != nil {
		t.Fatal(e)
	}
	for i, raw := range sqls {
		if _, e = target.Exec(string(raw)); e != nil {
			t.Fatal(e)
		}
		if _, e = target.Exec("INSERT INTO schema_migrations(version) VALUES(?)", i+1); e != nil {
			t.Fatal(e)
		}
	}
	contracts, e := LoadContracts(filepath.Join(root, "spec/v2.0/contracts"))
	if e != nil {
		t.Fatal(e)
	}
	svc := &Service{DB: target, Contracts: contracts}
	wantSchema, _, e := upgradeTemplate(context.Background(), sqls, contracts)
	if e != nil {
		t.Fatal(e)
	}
	actualSchema, e := backupSchema(target)
	if e != nil || actualSchema != wantSchema {
		t.Fatal("historical schema13 differs from pinned template", e)
	}
	rows, e := upgradeRows(f.db)
	if e != nil {
		t.Fatal(e)
	}
	targetRows, e := upgradeRows(target)
	if e != nil {
		t.Fatal(e)
	}
	if _, e = target.Exec("PRAGMA foreign_keys=OFF"); e != nil {
		t.Fatal(e)
	}
	tx, e := target.Begin()
	if e != nil {
		t.Fatal(e)
	}
	defer tx.Rollback()
	for table, entries := range rows {
		if strings.HasPrefix(table, "remote_") {
			if len(entries) != 0 {
				t.Fatal("remote fixtures cannot be projected into13")
			}
			continue
		}
		if strings.HasPrefix(table, "retrieval_fts_") {
			continue
		}
		if _, exists := targetRows[table]; !exists {
			if len(entries) != 0 {
				t.Fatalf("newer fixture table %s is not empty; cannot project into schema13", table)
			}
			continue
		}
		if table == "schema_migrations" {
			if _, e = tx.Exec("DELETE FROM schema_migrations"); e != nil {
				t.Fatal(e)
			}
		}
		if table == "resource_write_lock" {
			if _, e = tx.Exec("DELETE FROM resource_write_lock"); e != nil {
				t.Fatal(e)
			}
		}
		for _, row := range entries {
			if table == "schema_migrations" {
				version, err := Num(row, "version")
				if err != nil {
					t.Fatal(err)
				}
				if version > 13 {
					continue
				}
			}
			cols, args, placeholders := []string{}, []any{}, []string{}
			for col, value := range row {
				cols = append(cols, `"`+col+`"`)
				args = append(args, value)
				placeholders = append(placeholders, "?")
			}
			if _, e = tx.Exec(`INSERT INTO "`+table+`" (`+strings.Join(cols, ",")+`) VALUES (`+strings.Join(placeholders, ",")+`)`, args...); e != nil {
				t.Fatal(table, e)
			}
		}
	}
	if e = tx.Commit(); e != nil {
		t.Fatal(e)
	}
	if _, e = target.Exec("PRAGMA foreign_keys=ON"); e != nil {
		t.Fatal(e)
	}
	var versions string
	if e = target.QueryRow("SELECT group_concat(version, ',') FROM (SELECT version FROM schema_migrations ORDER BY version)").Scan(&versions); e != nil || versions != "1,2,3,4,5,6,7,8,9,10,11,12,13" {
		t.Fatal("historical versions", versions, e)
	}
	actualSchema, e = backupSchema(target)
	if e != nil || actualSchema != wantSchema {
		t.Fatal("fixture copy changed historical schema", e)
	}
	f.db.Close()
	f.db, f.s, f.h = target, svc, svc.Handler()
	return path
}

func upgradeSeedQualifications(t *testing.T, f *fixture, summary protectedstore.SafeSummary) {
	t.Helper()
	ctx := context.Background()
	tx, e := f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	defer tx.Rollback()
	owner, e := authenticate(tx, f.token)
	if e != nil {
		t.Fatal(e)
	}
	raw, e := os.ReadFile("../../evaluation/development/jev-v2/dataset.json")
	if e != nil {
		t.Fatal(e)
	}
	u, e := f.s.upload(tx, owner, f.project, raw)
	if e != nil {
		t.Fatal(e)
	}
	dev, e := f.s.seal(tx, owner, f.project, Object{"run_id": nil, "kind": "REPORT", "evidence_kind": "OBSERVED", "measurement_mode": "LIVE", "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "application/json", "byte_size": len(raw), "input_refs": Empty(), "source_refs": Empty(), "produced_by": owner.ID, "access_class": "PROJECT"})
	if e != nil {
		t.Fatal(e)
	}
	d := summary.Frozen.Dataset
	private := Merge(Base(f.project), Object{"run_id": nil, "kind": "REPORT", "evidence_kind": "OBSERVED", "measurement_mode": "LIVE", "content_hash": d.Hash, "storage_key": d.Ticket, "media_type": d.MediaType, "byte_size": d.Size, "input_refs": Empty(), "source_refs": Empty(), "produced_by": owner.ID, "access_class": "VERIFIER_ONLY", "validity": "CURRENT", "sealed_at": Now()})
	if e = f.s.put(tx, "Artifact", private); e != nil {
		t.Fatal(e)
	}
	if e = tx.Commit(); e != nil {
		t.Fatal(e)
	}
	verifier := Principal{ID: "upgrade-independent-verifier", Roles: []string{"VERIFIER"}, Grants: []Grant{{ProjectID: f.project, Restricted: true}}}
	if e = f.s.ProvisionPrincipal(ctx, verifier); e != nil {
		t.Fatal(e)
	}
	for _, counts := range summary.Frozen.Keys {
		tx, e = f.db.Begin()
		if e != nil {
			t.Fatal(e)
		}
		scope, e := Decode(Bytes(counts.Scope))
		if e != nil {
			t.Fatal(e)
		}
		q, e := f.s.createQualification(tx, verifier, f.project, Object{"scope": scope, "dataset_artifact_ref": Ref(dev, "Artifact"), "holdout_artifact_ref": Ref(private, "Artifact"), "thresholds_hash": QualificationThresholdsHash(), "thresholds_frozen_at": summary.Frozen.FrozenAt, "total_case_count": 45, "holdout_case_count": 15, "label_basis": "OBJECTIVE", "measurement_mode": "LIVE", "expires_at": nil})
		if e != nil {
			t.Fatal(e)
		}
		state, e := singleton(tx, f.project, "ProjectState")
		if e != nil {
			t.Fatal(e)
		}
		proof := &preparedQualification{SubjectHash: Hash(q), PrincipalID: verifier.ID, Summary: summary}
		acceptance, e := f.s.acceptQualification(tx, verifier, f.project, Object{"subject_ref": Ref(q, "Qualification"), "contract_hash": qualificationContract(q), "policy_revision": state["policy_revision"], "measurement_mode": "LIVE", "run_id": nil}, proof)
		if e != nil {
			t.Fatal(e)
		}
		_, e = f.s.recordQualificationResult(tx, verifier, f.project, Str(q, "id"), Object{"requested_maximum_mode": "BOUNDED_AUTO", "acceptance_id": acceptance["id"], "test_receipt_refs": acceptance["artifact_refs"], "critical_false_accept_count": counts.CriticalFalseAccept, "false_accept_rate": float64(counts.FalseAccept) / float64(counts.Planned), "false_reject_rate": float64(counts.FalseReject) / float64(counts.PositiveLabelCount), "abstain_rate": float64(counts.Abstain) / float64(counts.Planned)}, proof)
		if e != nil {
			t.Fatal(e)
		}
		if e = tx.Commit(); e != nil {
			t.Fatal(e)
		}
	}
	// Preserve an additional historical protected version; no body was uploaded.
	if e = bump(private); e != nil {
		t.Fatal(e)
	}
	tx, e = f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	if e = f.s.put(tx, "Artifact", private); e != nil {
		t.Fatal(e)
	}
	if e = tx.Commit(); e != nil {
		t.Fatal(e)
	}
}

// Corrupt an offline fixture coherently: both copies, receipt hash and reference
// index agree. Rejection must come from evidence semantics, not a stale hash.
func upgradeReplaceReceipt(t *testing.T, f *fixture, q, receipt Object) {
	t.Helper()
	originalID := q["id"]
	var raw string
	if e := f.db.QueryRow("SELECT body FROM domain_versions WHERE project=? AND kind='Qualification' AND id=? AND revision=1", f.project, originalID).Scan(&raw); e != nil {
		t.Fatal(e)
	}
	draft, e := Decode([]byte(raw))
	if e != nil {
		t.Fatal(e)
	}
	q["id"] = ID()
	draft["id"] = q["id"]
	subject := receipt["subject_ref"].(map[string]any)
	if subject["id"] == originalID {
		subject["id"] = q["id"]
	}
	receipt["id"] = ID()
	q["acceptance_id"] = receipt["id"]
	receipt["receipt_hash"] = Receipt(receipt)
	for kind, o := range map[string]Object{"AcceptanceReceipt": receipt, "Qualification": q} {
		if e := f.s.Contracts.Validate(kind, o); e != nil {
			t.Fatal(e)
		}
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		for _, o := range []Object{draft, q} {
			if _, e := tx.Exec("INSERT INTO domain_versions(project,kind,id,revision,body) VALUES(?,'Qualification',?,?,?)", f.project, o["id"], o["revision"], string(Bytes(o))); e != nil {
				return e
			}
		}
		if _, e := tx.Exec("INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES(?,'Qualification',?,?,?,0)", f.project, q["id"], q["revision"], string(Bytes(q))); e != nil {
			return e
		}
		if e := f.s.put(tx, "AcceptanceReceipt", receipt); e != nil {
			return e
		}
		for _, pair := range [][2]any{{1, 1}, {q["revision"], 2}} {
			if _, e := tx.Exec("INSERT INTO domain_refs SELECT project,kind,?,?,field,target_project,target_kind,target_id,target_revision FROM domain_refs WHERE project=? AND kind='Qualification' AND id=? AND revision=?", q["id"], pair[0], f.project, originalID, pair[1]); e != nil {
				return e
			}
		}
		_, e := tx.Exec("UPDATE domain_refs SET target_id=? WHERE project=? AND kind='Qualification' AND id=? AND field='acceptance_id'", receipt["id"], f.project, q["id"])
		return e
	})
}

func TestW17UpgradeQualificationReceiptBinding(t *testing.T) {
	for _, scenario := range []string{"other-draft", "failed-subject", "nonadjacent-result", "inputs", "missing-check", "duplicate-check", "failed-check", "command", "check-evidence", "empty-executors", "wrong-executor", "registrar-verifier", "summary-author", "policy"} {
		t.Run(scenario, func(t *testing.T) {
			opt, f, fake := upgradeFixture(t, true)
			qs, e := backupObjects(f.db, "SELECT body FROM domain_objects WHERE kind='Qualification' ORDER BY id")
			if e != nil {
				t.Fatal(e)
			}
			q := qs[0]
			var raw string
			if e = f.db.QueryRow("SELECT body FROM domain_objects WHERE kind='AcceptanceReceipt' AND id=?", q["acceptance_id"]).Scan(&raw); e != nil {
				t.Fatal(e)
			}
			receipt, e := Decode([]byte(raw))
			if e != nil {
				t.Fatal(e)
			}
			check := Arr(receipt, "checks")[0].(map[string]any)
			switch scenario {
			case "other-draft":
				receipt["subject_ref"] = Ref(Merge(copyObject(qs[1]), Object{"revision": 1}), "Qualification")
			case "failed-subject":
				receipt["subject_ref"] = Ref(q, "Qualification")
			case "nonadjacent-result":
				q["revision"] = 3
			case "inputs":
				receipt["input_refs"] = []any{q["dataset_artifact_ref"], q["dataset_artifact_ref"]}
			case "missing-check":
				receipt["checks"] = Arr(receipt, "checks")[:2]
			case "duplicate-check":
				Arr(receipt, "checks")[1] = copyObject(check)
			case "failed-check":
				check["status"] = "FAIL"
			case "command":
				check["command_key"] = "test.unit"
			case "check-evidence":
				check["evidence_refs"] = []any{q["dataset_artifact_ref"]}
			case "empty-executors":
				receipt["executor_principal_ids"] = Empty()
			case "wrong-executor":
				receipt["executor_principal_ids"] = []any{"fixture-unrelated-author"}
			case "registrar-verifier":
				receipt["verifier_principal_id"] = f.owner
			case "summary-author":
				receipt["verifier_principal_id"] = "second-independent-verifier"
				if e = f.s.ProvisionPrincipal(context.Background(), Principal{ID: "second-independent-verifier", Roles: []string{"VERIFIER"}, Grants: []Grant{{ProjectID: f.project, Restricted: true}}}); e != nil {
					t.Fatal(e)
				}
			case "policy":
				receipt["policy_revision"] = 999
			}
			upgradeReplaceReceipt(t, f, q, receipt)
			before, e := upgradeRows(f.db)
			if e != nil {
				t.Fatal(e)
			}
			f.db.Close()
			_, e = upgradeLocal(context.Background(), opt, fake.verifier())
			if e == nil || !strings.Contains(e.Error(), "UPGRADE_QUALIFICATION_") {
				t.Fatalf("semantic pollution published: %v", e)
			}
			if _, e := os.Stat(opt.Destination); !os.IsNotExist(e) {
				t.Fatal("rejected destination published")
			}
			db, e := store.Open(opt.Source)
			if e != nil {
				t.Fatal(e)
			}
			after, e := upgradeRows(db)
			db.Close()
			if e != nil || Hash(before) != Hash(after) {
				t.Fatalf("source changed: %v", e)
			}
			upgradeAssert(t, "QUALIFICATION-RECEIPT-"+scenario, []any{true, 0}, []any{true, fake.reads})
		})
	}
}

func TestW17UpgradeQualificationHistoricalPolicy(t *testing.T) {
	opt, f, fake := upgradeFixture(t, true)
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		state, e := singleton(tx, f.project, "ProjectState")
		if e != nil {
			return e
		}
		state["policy_revision"] = 2
		if e = bump(state); e != nil {
			return e
		}
		if e = f.s.put(tx, "ProjectState", state); e != nil {
			return e
		}
		_, e = tx.Exec("UPDATE auth_credentials SET revoked=1")
		return e
	})
	f.db.Close()
	_, e := upgradeLocal(context.Background(), opt, fake.verifier())
	if e != nil {
		t.Fatal(e)
	}
	upgradeAssert(t, "QUALIFICATION-HISTORICAL-POLICY-NO-CREDENTIAL-AUTHORITY", 0, fake.reads)
}

// Historical fixture validation never starts or migrates the current product.
func upgradeHistoricalFixtureService(t *testing.T, db *sql.DB, root string, version int, restored bool) *Service {
	t.Helper()
	if (version != 13 && version != 14 && version != 20) || (!restored && version != 13) {
		t.Fatal("invalid explicit historical fixture case")
	}
	_, sqls, e := upgradeRelease(root, version)
	if e != nil {
		t.Fatal(e)
	}
	contracts, e := LoadContracts(filepath.Join(root, "spec/v2.0/contracts"))
	if e != nil {
		t.Fatal(e)
	}
	before, e := upgradeRows(db)
	if e != nil {
		t.Fatal(e)
	}
	versions, e := backupMigrations(db)
	if e != nil || Hash(versions) != Hash(upgradeVersions(version)) {
		t.Fatal("historical version mismatch", versions, e)
	}
	pre, post, e := upgradeTemplate(context.Background(), sqls, contracts)
	if e != nil {
		t.Fatal(e)
	}
	want := pre
	if restored {
		want = post
	}
	actual, e := backupSchema(db)
	if e != nil || actual != want {
		t.Fatal("historical schema mismatch", version, restored, e)
	}
	after, e := upgradeRows(db)
	if e != nil || Hash(before) != Hash(after) {
		t.Fatal("historical validation changed rows", e)
	}
	afterSchema, e := backupSchema(db)
	if e != nil || afterSchema != actual {
		t.Fatal("historical validation changed schema", e)
	}
	upgradeAssert(t, fmt.Sprintf("HISTORICAL%d-EXACT-SCHEMA-restored-%t", version, restored), true, true)
	return &Service{DB: db, Contracts: contracts}
}

func TestW17UpgradeProtectedNative(t *testing.T) {
	ctx := context.Background()
	opt, f, fake := upgradeFixture(t, true)
	key, e := os.ReadFile(opt.KeyFile)
	if e != nil {
		t.Fatal(e)
	}
	_, e = f.s.CreateBackup(ctx, filepath.Join(t.TempDir(), "ordinary"), key)
	upgradeAssert(t, "ORDINARY-PROTECTED-CREATE-REJECTED", true, e != nil && strings.Contains(e.Error(), "PROTECTED_BACKUP_REQUIRES_W17"))
	before, e := upgradeRows(f.db)
	if e != nil {
		t.Fatal(e)
	}
	_, e = New(f.db, filepath.Join(opt.TargetRoot, "spec/v2.0/contracts"), filepath.Join(opt.TargetRoot, "migrations/sqlite/0002_domain.sql"))
	upgradeAssert(t, "POPULATED13-STARTUP-GUARD", true, e != nil && strings.Contains(e.Error(), "MIGRATION_PREBACKUP_REQUIRED"))
	if e = f.db.Close(); e != nil {
		t.Fatal(e)
	}
	report, e := upgradeLocal(ctx, opt, fake.verifier())
	if e != nil {
		t.Fatal(e)
	}
	upgradeAssert(t, "PROTECTED-UPGRADE-REPORT", "RESTORED_RECONCILIATION_REQUIRED", report.Status)
	upgradeAssert(t, "NO-PRIVATE-READ", 0, fake.reads)
	upgradeAssert(t, "DESCRIPTOR-RECHECKED", true, fake.descriptions >= 3)
	upgraded, e := store.Open(filepath.Join(opt.Destination, "researchos.sqlite"))
	if e != nil {
		t.Fatal(e)
	}
	defer upgraded.Close()
	upgradeHistoricalFixtureService(t, upgraded, opt.TargetRoot, 14, true)
	versions, e := backupMigrations(upgraded)
	if e != nil {
		t.Fatal(e)
	}
	upgradeAssert(t, "HISTORICAL14-SCHEMA-VALIDATED", upgradeVersions(14), versions)
	var qualificationCount, privateVersions, credentials int
	upgraded.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='Qualification' AND json_extract(body,'$.status')='FAILED' AND json_extract(body,'$.maximum_mode')='ADVISORY'").Scan(&qualificationCount)
	upgraded.QueryRow("SELECT count(*) FROM domain_versions WHERE kind='Artifact' AND json_extract(body,'$.access_class')='VERIFIER_ONLY'").Scan(&privateVersions)
	upgraded.QueryRow("SELECT count(*) FROM auth_credentials WHERE revoked=0").Scan(&credentials)
	upgradeAssert(t, "IDS-HISTORY-QUALIFICATIONS-CREDENTIALS", []int{2, 2, 0}, []int{qualificationCount, privateVersions, credentials})
	source, e := store.Open(opt.Source)
	if e != nil {
		t.Fatal(e)
	}
	after, e := upgradeRows(source)
	if e != nil {
		t.Fatal(e)
	}
	upgradeAssert(t, "ORIGINAL13-UNCHANGED", Hash(before), Hash(after))
	upgradeHistoricalFixtureService(t, source, opt.SourceRoot, 13, false)
	source.Close()
	_, e = RestoreBackup(ctx, opt.Snapshot, filepath.Join(t.TempDir(), "foreign"), RestoreOptions{Key: key, Contracts: f.s.Contracts, SupportedMigrations: upgradeVersions(13)})
	upgradeAssert(t, "ORDINARY-FOREIGN-RESTORE-REJECTED", true, e != nil && strings.Contains(e.Error(), "BACKUP_MANIFEST_INVALID"))
	entries, e := os.ReadDir(opt.Snapshot)
	if e != nil {
		t.Fatal(e)
	}
	for _, entry := range entries {
		raw, e := os.ReadFile(filepath.Join(opt.Snapshot, entry.Name()))
		if e != nil {
			t.Fatal(e)
		}
		if strings.Contains(entry.Name(), "portable") || bytes.Contains(raw, []byte(fake.summary.Frozen.Dataset.Ticket)) || bytes.Contains(raw, []byte(qualificationPrivateCanary)) || bytes.Contains(raw, key) {
			t.Fatal("private descriptor/body/key or portable export in package", entry.Name())
		}
	}
	upgradeAssert(t, "OPAQUE-ENCRYPTED-PACKAGE", true, true)
}

func TestW17UpgradeExclusiveLock(t *testing.T) {
	opt, f, _ := upgradeFixture(t, false)
	// Existing open WAL owner must make the administrative upgrade fail closed.
	_, e := upgradeOpenExclusive(context.Background(), opt.Source)
	upgradeAssert(t, "OPEN-OWNER-REJECTED", true, e != nil)
	f.db.Close()
	locked, e := upgradeOpenExclusive(context.Background(), opt.Source)
	if e != nil {
		t.Fatal(e)
	}
	defer locked.Close()
	other, e := store.Open(opt.Source)
	if other != nil {
		other.Close()
	}
	upgradeAssert(t, "SECOND-CONNECTION-EXCLUDED", true, e != nil)
}

func TestW17UpgradeActiveRecovery(t *testing.T) {
	upgradeActiveRecovery(t, LocalUpgradePlan)
}

func upgradeActiveRecovery(t *testing.T, plan string) {
	ctx := context.Background()
	var pending *runtimeFixture
	var orchestration *orchestrationFixture
	var local Object
	var originalSource string
	const effectKey = "public-upgrade-effect"
	opt, f, fake := upgradeFixture(t, true, func(f *fixture) {
		req := f.requirement()
		goal := f.expect(201, "POST", f.path("/goals"), ID(), f.stateTag(), Object{"title": "Upgrade fixture", "original_intent": "Preserve verified history", "scope": "PROJECT", "requirement_refs": []any{Ref(req, "Requirement")}, "problem_ids": []any{"orchestration-problem"}, "deliverables": []any{"verified JSON"}, "acceptance_contract": orchestrationContract()})
		goal = f.expect(200, "POST", f.path("/goals/"+Str(goal, "id")+"/actions"), ID(), testTag(goal), Object{"action": "ACTIVATE", "reason": "public fixture"})
		rt := f.expect(201, "POST", f.path("/runtimes"), ID(), f.stateTag(), Object{"name": "public upgrade observer", "adapter": "fixture", "adapter_revision": "1", "capabilities": []any{"fixture"}, "platform": "windows-amd64", "measurement_mode": "FIXTURE", "credential_ref": nil})
		if e := f.s.RegisterOrchestrationFixture(ctx, f.project, Str(rt, "id")); e != nil {
			t.Fatal(e)
		}
		orchestration = &orchestrationFixture{f, goal, req, rt, f.token}
		completed := orchestration.claim(orchestration.task("accepted-before-upgrade", Empty(), Empty()))
		a := orchestration.report(completed, []byte(`{"result":"verified"}`))
		acceptance := orchestration.acceptance(completed, a)
		f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(completed.task), acceptance)
		pending = orchestration.claim(orchestration.task("pending-upgrade", Empty(), Empty()))
		resourceCheckpoint(pending, Object{"next": "continue-after-upgrade"})
		pending.observe(pending.observation("LOST", false))
		f.token = orchestration.owner
		policy := f.expect(200, "GET", f.path("/goals/"+Str(goal, "id")+"/budget-policy"), "", "", nil)
		if _, e := f.s.PrepareEffect(ctx, f.token, f.project, Str(pending.run, "id"), effectKey, Object{"fixture": "not dispatched"}, budgetRequest(pending, Str(policy, "id"), "RESERVE", effectKey, dollars("1.00"), "UPPER_BOUND", nil)); e != nil {
			t.Fatal(e)
		}
		originalSource = t.TempDir()
		if e := os.WriteFile(filepath.Join(originalSource, "original.txt"), []byte("sealed native source"), 0600); e != nil {
			t.Fatal(e)
		}
		root, e := f.s.RegisterLocalRoot(ctx, f.token, f.project, originalSource)
		if e != nil {
			t.Fatal(e)
		}
		local, e = f.s.CaptureLocalSnapshot(ctx, f.token, f.project, root, "original.txt")
		if e != nil {
			t.Fatal(e)
		}
	})
	if plan == FinalSchemaUpgradePlan {
		opt.Plan, opt.TargetRoot = plan, upgradeTestRelease(t, 20)
	}
	f.db.Close()
	report, e := upgradeLocal(ctx, opt, fake.verifier())
	if e != nil {
		t.Fatal(e)
	}
	upgradeAssert(t, "REAL-FENCE-COUNTS", []any{1, 1}, []any{report.Recovery["active_runs_fenced"], report.Recovery["effects_requiring_reconciliation"]})
	db, e := store.Open(filepath.Join(opt.Destination, "researchos.sqlite"))
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	version := 14
	switch plan {
	case LocalUpgradePlan:
	case FinalSchemaUpgradePlan:
		version = 20
	default:
		t.Fatal("unknown historical plan")
	}
	svc := upgradeHistoricalFixtureService(t, db, opt.TargetRoot, version, true)
	resume := svc.ResumeCheckpoint
	if version == 14 {
		resume = func(ctx context.Context, token, project, runID, key string, expectedRevision int64) (Object, error) {
			upgradeHistoricalFixtureService(t, db, opt.TargetRoot, 14, true)
			return svc.upgradeHistorical14ResumeCheckpoint(ctx, token, project, runID, key, expectedRevision)
		}
	}
	var costs, cursors int
	db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='BudgetLedgerEntry'").Scan(&costs)
	db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='SourceCursor'").Scan(&cursors)
	upgradeAssert(t, "COSTS-CURSORS-PRESERVED", true, costs > 0 && cursors > 0)
	if e = os.WriteFile(filepath.Join(originalSource, "original.txt"), []byte("changed original"), 0600); e != nil {
		t.Fatal(e)
	}
	tx, e := db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	raw, found, e := readLocalSnapshot(tx, f.project, Str(local, "id"))
	tx.Rollback()
	if e != nil {
		t.Fatal(e)
	}
	upgradeAssert(t, "SOURCE-RELOCATED-SEALED-BYTES", true, found && Digest(raw) == local["content_hash"])
	token, e := svc.IssueCredential(ctx, f.owner, time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	f.s, f.db, f.h, f.token = svc, db, svc.Handler(), token
	orchestration.owner = token
	current := f.read("runs", Str(pending.run, "id"))
	pending.run = current
	rev, _ := Num(current, "revision")
	_, resumeErr := resume(ctx, token, f.project, Str(current, "id"), "before-effect-reconcile", rev)
	_, dispatchErr := svc.BeginEffect(ctx, token, f.project, Str(current, "id"), effectKey)
	upgradeAssert(t, "UNKNOWN-EFFECT-BLOCKS-REPLAY", true, resumeErr != nil && dispatchErr != nil)
	if e = svc.ObserveEffect(ctx, f.project, Str(current, "id"), effectKey, "NOT_APPLIED", Object{"public_fixture": "query original idempotency key; absent"}); e != nil {
		t.Fatal(e)
	}
	_, resumeErr = resume(ctx, token, f.project, Str(current, "id"), "before-fresh-observation", rev)
	upgradeAssert(t, "OLD-OBSERVATION-REJECTED", true, resumeErr != nil)
	pending.observe(pending.observation("LOST", false))
	continued, e := resume(ctx, token, f.project, Str(current, "id"), "after-fresh-observation", rev)
	if e != nil {
		t.Fatal(e)
	}
	upgradeAssert(t, "FRESH-OBSERVATION-SAME-RUN", current["id"], continued["run"].(map[string]any)["id"])
	upgradeAssert(t, "FENCE-NO-PRIVATE-READ", 0, fake.reads)
}

func TestW17UpgradeLocalNegatives(t *testing.T) {
	for _, failure := range []string{"wrong-plan", "extra-migration", "sql-hash", "contract-hash", "wrong-schema", "already14", "key-alias", "destination-alias", "host-copy", "unknown-ticket", "fixture-mode"} {
		t.Run(failure, func(t *testing.T) {
			opt, f, fake := upgradeFixture(t, true)
			switch failure {
			case "wrong-plan":
				opt.Plan = "schema13-to15"
			case "extra-migration":
				os.WriteFile(filepath.Join(opt.TargetRoot, "migrations/sqlite/0015_extra.sql"), []byte("SELECT 1"), 0600)
			case "sql-hash":
				os.WriteFile(filepath.Join(opt.TargetRoot, "migrations/sqlite/0014_remote_access.sql"), []byte("SELECT 1"), 0600)
			case "contract-hash":
				os.WriteFile(filepath.Join(opt.SourceRoot, "spec/v2.0/contracts/openapi.json"), []byte("{}"), 0600)
			case "wrong-schema":
				if _, e := f.db.Exec("CREATE TABLE unexpected_upgrade_fixture(x)"); e != nil {
					t.Fatal(e)
				}
			case "already14":
				if _, e := f.db.Exec("INSERT INTO schema_migrations(version) VALUES(14)"); e != nil {
					t.Fatal(e)
				}
			case "key-alias":
				alias := filepath.Join(t.TempDir(), "alias.key")
				if e := os.Link(opt.Source, alias); e != nil {
					t.Fatal(e)
				}
				opt.KeyFile = alias
			case "destination-alias":
				opt.Destination = filepath.Join(filepath.Dir(opt.Source), "new-target")
			case "host-copy":
				if _, e := f.db.Exec("INSERT INTO uploaded_content(storage_key,project,principal,bytes,content_hash,expires_at,sealed) VALUES(?,?,?,?,?,?,1)", fake.summary.Frozen.Dataset.Ticket, f.project, f.owner, []byte("PUBLIC FIXTURE WRONG COPY"), Digest([]byte("PUBLIC FIXTURE WRONG COPY")), Now()); e != nil {
					t.Fatal(e)
				}
			case "unknown-ticket", "fixture-mode":
				artifacts, e := backupObjects(f.db, "SELECT body FROM domain_objects WHERE kind='Artifact' AND json_extract(body,'$.access_class')='VERIFIER_ONLY'")
				if e != nil {
					t.Fatal(e)
				}
				a := copyObject(artifacts[0])
				a["id"] = ID()
				a["revision"] = 1
				a["kind"] = "LOG"
				if failure == "unknown-ticket" {
					a["storage_key"] = "ps1:00000000000000000000000000000000"
				} else {
					a["measurement_mode"] = "FIXTURE"
				}
				sourceTx(t, f.db, func(tx *sql.Tx) error { return f.s.put(tx, "Artifact", a) })
			}
			before, e := upgradeRows(f.db)
			if e != nil {
				t.Fatal(e)
			}
			f.db.Close()
			_, e = upgradeLocal(context.Background(), opt, fake.verifier())
			upgradeAssert(t, "LOCAL-REJECT-"+failure, true, e != nil)
			if _, err := os.Stat(opt.Destination); !os.IsNotExist(err) {
				t.Fatal("failed upgrade published target", err)
			}
			db, err := store.Open(opt.Source)
			if err != nil {
				t.Fatal(err)
			}
			after, err := upgradeRows(db)
			db.Close()
			if err != nil {
				t.Fatal(err)
			}
			upgradeAssert(t, "LOCAL-REJECTION-SOURCE-STABLE-"+failure, Hash(before), Hash(after))
		})
	}
}

func TestW17UpgradeMigrationRollback(t *testing.T) {
	opt, f, fake := upgradeFixture(t, true)
	f.db.Close()
	if _, e := upgradeLocal(context.Background(), opt, fake.verifier()); e != nil {
		t.Fatal(e)
	}
	manifestBytes, e := os.ReadFile(filepath.Join(opt.Snapshot, "manifest.json"))
	if e != nil {
		t.Fatal(e)
	}
	var manifest BackupManifest
	if e = json.Unmarshal(manifestBytes, &manifest); e != nil {
		t.Fatal(e)
	}
	key, e := os.ReadFile(opt.KeyFile)
	if e != nil {
		t.Fatal(e)
	}
	defer clear(key)
	guard := &upgradeProtection{ctx: context.Background(), verifier: fake.verifier()}
	policy := &backupPolicy{format: localUpgradeFormat, purpose: manifest.Purpose, validate: guard.refresh, allowProtected: guard.artifact}
	target := filepath.Join(t.TempDir(), "failed-migration")
	sqlBytes, e := os.ReadFile(filepath.Join(opt.TargetRoot, "migrations/sqlite/0014_remote_access.sql"))
	if e != nil {
		t.Fatal(e)
	}
	_, e = restoreBackupPolicy(context.Background(), opt.Snapshot, target, RestoreOptions{Key: key, SupportedMigrations: upgradeVersions(13), Contracts: f.s.Contracts, Migration: func(ctx context.Context, db *sql.DB) error {
		// A real SQL failure after the first CREATE must roll back its transaction.
		if _, err := db.Exec("CREATE TABLE remote_devices(public_collision_fixture)"); err != nil {
			return err
		}
		err := upgradeMigration(ctx, db, sqlBytes)
		var partiallyCreated int
		if queryErr := db.QueryRow("SELECT count(*) FROM sqlite_master WHERE name='remote_challenges'").Scan(&partiallyCreated); queryErr != nil {
			return queryErr
		}
		upgradeAssert(t, "SQL-TRANSACTION-ROLLED-BACK", 0, partiallyCreated)
		return err
	}}, policy)
	upgradeAssert(t, "REAL-MIGRATION-FAILURE", true, e != nil && strings.Contains(e.Error(), "MIGRATION_FAILED"))
	if _, err := os.Stat(target); !os.IsNotExist(err) {
		t.Fatal("failed migration published")
	}
	after, e := os.ReadFile(filepath.Join(opt.Snapshot, "manifest.json"))
	if e != nil {
		t.Fatal(e)
	}
	upgradeAssert(t, "STABLE-ENCRYPTED-PACKAGE-RETAINED", Digest(manifestBytes), Digest(after))
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	_, e = restoreBackupPolicy(ctx, opt.Snapshot, filepath.Join(t.TempDir(), "cancelled"), RestoreOptions{Key: key, SupportedMigrations: upgradeVersions(13), Contracts: f.s.Contracts}, policy)
	upgradeAssert(t, "CANCELLED-RESTORE-REJECTED", true, e != nil)
}

func TestW17UpgradeDescriptorNegatives(t *testing.T) {
	for _, failure := range []string{"missing", "identity", "same-user", "hash", "size", "media", "mode", "project", "ticket", "late-change"} {
		t.Run(failure, func(t *testing.T) {
			opt, f, fake := upgradeFixture(t, true)
			before, e := upgradeRows(f.db)
			if e != nil {
				t.Fatal(e)
			}
			f.db.Close()
			fake.fail = failure
			_, e = upgradeLocal(context.Background(), opt, fake.verifier())
			upgradeAssert(t, "DESCRIPTOR-REJECT-"+failure, true, e != nil)
			if _, err := os.Stat(opt.Destination); !os.IsNotExist(err) {
				t.Fatal("failed upgrade published target")
			}
			db, err := store.Open(opt.Source)
			if err != nil {
				t.Fatal(err)
			}
			after, err := upgradeRows(db)
			db.Close()
			if err != nil {
				t.Fatal(err)
			}
			upgradeAssert(t, "NEGATIVE-SOURCE-UNCHANGED-"+failure, Hash(before), Hash(after))
			upgradeAssert(t, "NEGATIVE-NO-READ-"+failure, 0, fake.reads)
			if failure == "late-change" {
				if _, err = os.Stat(filepath.Join(opt.Snapshot, "manifest.json")); err != nil {
					t.Fatal("stable encrypted snapshot lost", err)
				}
			}
		})
	}
}

// Real process boundary validating an explicitly selected historical fixture schema.
func TestW17UpgradeChild(t *testing.T) {
	if os.Getenv("RESEARCHOS_UPGRADE_CHILD") != "1" {
		return
	}
	db, e := store.Open(os.Getenv("RESEARCHOS_UPGRADE_DB"))
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	root := os.Getenv("RESEARCHOS_UPGRADE_ROOT")
	version, restored := 0, false
	switch os.Getenv("RESEARCHOS_UPGRADE_CASE") {
	case "original13":
		version = 13
	case "new14":
		version, restored = 14, true
	default:
		t.Fatal("explicit historical child case required")
	}
	upgradeHistoricalFixtureService(t, db, root, version, restored)
	var count int
	if e = db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='ProjectProfile'", os.Getenv("RESEARCHOS_UPGRADE_PROJECT")).Scan(&count); e != nil || count != 1 {
		t.Fatal("same project not restored", count, e)
	}
}

func TestW17UpgradeCLI(t *testing.T) {
	goexe := os.Getenv("RESEARCHOS_GO")
	if goexe == "" {
		t.Fatal("RESEARCHOS_GO required")
	}
	opt, f, _ := upgradeFixture(t, false)
	f.db.Close()
	control := filepath.Join(t.TempDir(), "control.exe")
	if historical := os.Getenv("RESEARCHOS_HISTORICAL_SCHEMA14_CONTROL"); historical != "" {
		const artifactHash = "sha256:aeda2d5eff0028529eaa53e9f5cc91fbcd668842577315eb744bd5f066834032"
		artifact, err := os.ReadFile(historical)
		if err != nil {
			t.Fatalf("historical schema14 artifact read: %v", err)
		}
		if Digest(artifact) != artifactHash {
			t.Fatal("historical schema14 artifact hash mismatch")
		}
		goBytes, err := os.ReadFile(goexe)
		if err != nil || Digest(goBytes) != "sha256:d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490" {
			t.Fatal("historical schema14 requires the actual locked Go executable")
		}
		if err = os.WriteFile(control, artifact, 0700); err != nil {
			t.Fatal(err)
		}
		staged, err := os.ReadFile(control)
		if err != nil || Digest(staged) != artifactHash {
			t.Fatal("historical schema14 staged artifact hash mismatch")
		}
		metadata, err := exec.Command(goexe, "version", "-m", control).CombinedOutput()
		if err != nil {
			t.Fatalf("historical schema14 buildinfo: %v %s", err, metadata)
		}
		metadataLines := strings.Split(string(metadata), "\n")
		if len(metadataLines) == 0 || strings.TrimSuffix(metadataLines[0], "\r") != control+": go1.27.1" {
			t.Fatal("historical schema14 Go version mismatch")
		}
		for _, expected := range []string{
			"\tpath\tresearchos.local/research-os/apps/control",
			"\tbuild\tGOOS=windows",
			"\tbuild\tGOARCH=amd64",
			"\tbuild\tvcs.revision=09a6a5ecfba40c1596a3ec46be25c34ba1f2fce0",
			"\tbuild\tvcs.modified=true",
		} {
			matches := 0
			for _, line := range metadataLines[1:] {
				if strings.TrimSuffix(line, "\r") == expected {
					matches++
				}
			}
			if matches != 1 {
				t.Fatalf("historical schema14 buildinfo mismatch: %s", expected)
			}
		}
		t.Logf("HISTORICAL_SCHEMA14_PROFILE artifact=%s staged=%s buildinfo=%s", artifactHash, control, metadata)
	} else {
		build := exec.Command(goexe, "build", "-o", control, "./apps/control")
		build.Dir = "../.."
		if output, err := build.CombinedOutput(); err != nil {
			t.Fatalf("build control: %v %s", err, output)
		}
	}
	opt.TargetProgram = control
	guard := exec.Command(control, "-issue-credential", f.owner, "-credential-file", filepath.Join(t.TempDir(), "must-not-exist.json"))
	guard.Dir = opt.TargetRoot
	guard.Env = append(os.Environ(), "RESEARCHOS_DATA_DIR="+filepath.Dir(opt.Source))
	guardOutput, guardError := guard.CombinedOutput()
	upgradeAssert(t, "REAL-PROGRAM-13-STARTUP-REJECTED", true, guardError != nil && bytes.Contains(guardOutput, []byte("MIGRATION_PREBACKUP_REQUIRED")))
	// The production CLI is tested with a public-only database, so it must make
	// no call to the actual protected service. Protected success is the separate
	// native fixture test above, never a fake-provider CLI switch.
	cmd := exec.Command(goexe, "run", "./ops/backup", "upgrade-local", "--db", opt.Source, "--backup", opt.Snapshot, "--out", opt.Destination, "--key-file", opt.KeyFile, "--source-root", opt.SourceRoot, "--root", opt.TargetRoot, "--source-program", opt.SourceProgram, "--target-program", opt.TargetProgram, "--plan", opt.Plan)
	cmd.Dir = "../.."
	raw, e := cmd.CombinedOutput()
	if e != nil {
		t.Fatalf("CLI failed: %v %s", e, raw)
	}
	upgradeAssert(t, "REAL-CLI-UPGRADE", true, bytes.Contains(raw, []byte("RESTORED_RECONCILIATION_REQUIRED")))
	for _, entry := range []struct{ db, root, label string }{{filepath.Join(opt.Destination, "researchos.sqlite"), opt.TargetRoot, "new14"}, {opt.Source, opt.SourceRoot, "original13"}} {
		child := exec.Command(os.Args[0], "-test.run=^TestW17UpgradeChild$", "-test.v")
		child.Env = append(os.Environ(), "RESEARCHOS_UPGRADE_CASE="+entry.label, "RESEARCHOS_UPGRADE_CHILD=1", "RESEARCHOS_UPGRADE_DB="+entry.db, "RESEARCHOS_UPGRADE_ROOT="+entry.root, "RESEARCHOS_UPGRADE_PROJECT="+f.project)
		output, err := child.CombinedOutput()
		if err != nil {
			t.Fatalf("%s child: %v %s", entry.label, err, output)
		}
		upgradeAssert(t, "NEW-PROCESS-HISTORICAL-SCHEMA-VALIDATED-"+entry.label, true, bytes.Contains(output, []byte("PASS")))
	}
	// Real product process and authenticated HTTP after the normal local reissue.
	credential := filepath.Join(t.TempDir(), "fresh-fixture-credential.json")
	issue := exec.Command(control, "-issue-credential", f.owner, "-credential-file", credential)
	issue.Dir = opt.TargetRoot
	issue.Env = append(os.Environ(), "RESEARCHOS_DATA_DIR="+opt.Destination)
	if output, err := issue.CombinedOutput(); err != nil {
		t.Fatalf("fresh local credential: %v %s", err, output)
	}
	credentialBytes, err := os.ReadFile(credential)
	if err != nil {
		t.Fatal(err)
	}
	credentials, err := Decode(credentialBytes)
	if err != nil {
		t.Fatal(err)
	}
	web := t.TempDir()
	if err = os.WriteFile(filepath.Join(web, "index.html"), []byte("<!doctype html><title>public fixture</title>"), 0600); err != nil {
		t.Fatal(err)
	}
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	address := listener.Addr().String()
	listener.Close()
	server := exec.Command(control)
	server.Dir = opt.TargetRoot
	server.Env = append(os.Environ(), "RESEARCHOS_DATA_DIR="+opt.Destination, "RESEARCHOS_WEB_DIR="+web, "RESEARCHOS_LISTEN="+address)
	var log bytes.Buffer
	server.Stdout, server.Stderr = &log, &log
	if err = server.Start(); err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { server.Process.Kill(); server.Wait() })
	client := &http.Client{Timeout: time.Second}
	ready := false
	for deadline := time.Now().Add(5 * time.Second); time.Now().Before(deadline); {
		response, err := client.Get("http://" + address + "/healthz")
		if err == nil {
			response.Body.Close()
			if response.StatusCode == 200 {
				ready = true
				break
			}
		}
		time.Sleep(50 * time.Millisecond)
	}
	if !ready {
		server.Process.Kill()
		server.Wait()
		t.Fatalf("new control did not become ready: %s", log.Bytes())
	}
	request, err := http.NewRequest("GET", "http://"+address+"/v1/projects/"+f.project+"/state", nil)
	if err != nil {
		t.Fatal(err)
	}
	request.Header.Set("Authorization", "Bearer "+Str(credentials, "token"))
	response, err := client.Do(request)
	if err != nil {
		t.Fatal(err)
	}
	defer response.Body.Close()
	var state Object
	if err = json.NewDecoder(response.Body).Decode(&state); err != nil {
		t.Fatal(err)
	}
	upgradeAssert(t, "REAL-PRODUCT-14-AUTHENTICATED-READ", []any{200, f.project}, []any{response.StatusCode, state["project_id"]})
}
