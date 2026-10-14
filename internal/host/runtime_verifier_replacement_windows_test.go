//go:build windows

package host

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"golang.org/x/sys/windows"
	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/internal/auth"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/verifier"
)

// These are isolated schema-24 fixtures, never a copied product data root.
type replacementFixture struct {
	Base, Root, Manifest, OldManifest, Plan string
	Old, New                                RuntimeVerifierInstallation
	Record                                  runtimeVerifierRegistration
	Input                                   RuntimeVerifierReplacementInput
}

func replacementNullACLForTest(t *testing.T, path string) {
	t.Helper()
	if e := windows.SetNamedSecurityInfo(path, windows.SE_FILE_OBJECT, windows.DACL_SECURITY_INFORMATION|windows.PROTECTED_DACL_SECURITY_INFORMATION, nil, nil, nil, nil); e != nil {
		t.Fatal(e)
	}
}
func replacementInheritedACLForTest(t *testing.T, path string) {
	t.Helper()
	sd, e := windows.GetNamedSecurityInfo(path, windows.SE_FILE_OBJECT, windows.DACL_SECURITY_INFORMATION)
	if e != nil {
		t.Fatal(e)
	}
	acl, _, e := sd.DACL()
	if e != nil {
		t.Fatal(e)
	}
	if e = windows.SetNamedSecurityInfo(path, windows.SE_FILE_OBJECT, windows.DACL_SECURITY_INFORMATION|windows.UNPROTECTED_DACL_SECURITY_INFORMATION, nil, nil, acl, nil); e != nil {
		t.Fatal(e)
	}
}
func replacementTestWrite(t *testing.T, path string, v any) []byte {
	t.Helper()
	raw, e := json.MarshalIndent(v, "", "  ")
	if e != nil {
		t.Fatal(e)
	}
	if e = os.WriteFile(path, raw, 0600); e != nil {
		t.Fatal(e)
	}
	if e = privateFile(path); e != nil {
		t.Fatal(e)
	}
	return raw
}
func newReplacementFixture(t *testing.T) replacementFixture {
	t.Helper()
	base := t.TempDir()
	root := filepath.Join(base, "data")
	host := filepath.Join(root, "host")
	for _, dir := range []string{root, host} {
		if e := os.Mkdir(dir, 0700); e != nil {
			t.Fatal(e)
		}
		if e := privateDir(dir); e != nil {
			t.Fatal(e)
		}
	}
	identity, e := auth.Current()
	if e != nil {
		t.Fatal(e)
	}
	h := &Host{dir: host, identity: identity}
	f := replacementFixture{Base: base, Root: root, Manifest: filepath.Join(base, "new-manifest.json"), OldManifest: filepath.Join(base, "old-manifest.json"), Plan: filepath.Join(base, "plan.json")}
	for i, target := range []*RuntimeVerifierInstallation{&f.Old, &f.New} {
		image := []byte(fmt.Sprintf("MZ-isolated-byte-validation-fixture-%d", i))
		path := filepath.Join(base, fmt.Sprintf("image%d.exe", i))
		if e = os.WriteFile(path, image, 0600); e != nil {
			t.Fatal(e)
		}
		if e = privateFile(path); e != nil {
			t.Fatal(e)
		}
		*target = RuntimeVerifierInstallation{Schema: "researchos.runtime-verifier-installation.v1", ServiceID: verifier.ServiceID, Protocol: verifier.Protocol, Executable: path, ExecutableHash: domain.Digest(image), SourceCommit: strings.Repeat(fmt.Sprint(i+1), 40), Arguments: []string{}}
	}
	replacementTestWrite(t, f.OldManifest, f.Old)
	manifest := replacementTestWrite(t, f.Manifest, f.New)
	serviceRoot := "local-verifier-root-" + strings.TrimPrefix(domain.Hash([]any{h.InstanceID(), verifier.ServiceID}), "sha256:")[:24]
	f.Record = runtimeVerifierRegistration{Schema: "researchos.runtime-verifier-registration.v1", OwnerHost: h.InstanceID(), OwnerPrincipal: "owner-fixture", ServiceRoot: serviceRoot, InstallHash: domain.Hash(f.Old), Installation: f.Old}
	record := replacementTestWrite(t, filepath.Join(host, "runtime-verifier-installation.json"), f.Record)
	replacementTestWrite(t, filepath.Join(host, stateFile), hostState{Version: 1, PrincipalRef: identity.Ref, PrincipalID: f.Record.OwnerPrincipal, HostInstanceID: h.InstanceID()})
	db, e := sql.Open("sqlite", filepath.Join(root, "researchos.sqlite"))
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	ddl := `CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY);CREATE TABLE auth_principals(id TEXT PRIMARY KEY,roles TEXT,revoked INTEGER,can_create_project INTEGER);CREATE TABLE orchestration_identity(principal TEXT PRIMARY KEY,root TEXT,parent TEXT);CREATE TABLE auth_grants(principal TEXT,project TEXT,task TEXT,run TEXT,restricted INTEGER);CREATE TABLE domain_objects(project TEXT,kind TEXT,id TEXT,body TEXT);CREATE TABLE resource_effects(project TEXT,run TEXT,effect_key TEXT,sequence INTEGER,body TEXT);CREATE TABLE runtime_dispatches(project TEXT,run TEXT,state TEXT);CREATE TABLE idempotency(project TEXT,operation TEXT,body TEXT);`
	if _, e = db.Exec(ddl); e != nil {
		t.Fatal(e)
	}
	for i := 1; i <= 24; i++ {
		if _, e = db.Exec("INSERT INTO schema_migrations VALUES(?)", i); e != nil {
			t.Fatal(e)
		}
	}
	if _, e = db.Exec(`INSERT INTO auth_principals VALUES(?, '["OWNER"]',0,1),(?, '["VERIFIER"]',0,0)`, f.Record.OwnerPrincipal, serviceRoot); e != nil {
		t.Fatal(e)
	}
	if _, e = db.Exec(`INSERT INTO orchestration_identity VALUES(?,?,NULL),(?,?,NULL)`, f.Record.OwnerPrincipal, f.Record.OwnerPrincipal, serviceRoot, serviceRoot); e != nil {
		t.Fatal(e)
	}
	for _, project := range []string{"project-a", "project-b"} {
		child := "local-verifier-" + strings.TrimPrefix(domain.Hash([]any{serviceRoot, project}), "sha256:")[:32]
		if _, e = db.Exec(`INSERT INTO auth_principals VALUES(?,'["VERIFIER"]',0,0)`, child); e != nil {
			t.Fatal(e)
		}
		if _, e = db.Exec(`INSERT INTO orchestration_identity VALUES(?,?,?)`, child, serviceRoot, serviceRoot); e != nil {
			t.Fatal(e)
		}
		if _, e = db.Exec(`INSERT INTO auth_grants VALUES(?,?,'','',0)`, child, project); e != nil {
			t.Fatal(e)
		}
	}
	if e = db.Close(); e != nil {
		t.Fatal(e)
	}
	f.Input = RuntimeVerifierReplacementInput{Action: "preflight", DataRoot: root, Manifest: f.Manifest, ExpectRecordSHA256: domain.Digest(record), ExpectManifestSHA256: domain.Digest(manifest), OperationID: strings.Repeat("a", 32), Out: f.Plan}
	return f
}
func (f replacementFixture) exec(t *testing.T, query string, args ...any) {
	t.Helper()
	db, e := sql.Open("sqlite", filepath.Join(f.Root, "researchos.sqlite"))
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	if _, e = db.Exec(query, args...); e != nil {
		t.Fatal(e)
	}
}
func (f replacementFixture) preflight(t *testing.T) RuntimeVerifierReplacementInput {
	t.Helper()
	before, e := os.ReadFile(filepath.Join(f.Root, "researchos.sqlite"))
	if e != nil {
		t.Fatal(e)
	}
	out, e := RuntimeVerifierReplacement(context.Background(), f.Input)
	if e != nil {
		t.Fatalf("preflight: %+v: %v", out, e)
	}
	if out.State != "PREFLIGHT" || out.Outcome != "NOT_APPLIED" {
		t.Fatal(out)
	}
	after, e := os.ReadFile(filepath.Join(f.Root, "researchos.sqlite"))
	if e != nil || !bytes.Equal(before, after) {
		t.Fatal("preflight mutated fixture DB")
	}
	if _, e = os.Stat(filepath.Join(f.Root, "host", replacementJournal)); !os.IsNotExist(e) {
		t.Fatal("preflight created product journal")
	}
	return RuntimeVerifierReplacementInput{Action: "commit", DataRoot: f.Root, Plan: f.Plan, ExpectPlanSHA256: out.PlanSHA256}
}
func replacementTestGate(root string) error {
	lease, e := rt.AcquireDataRootLease(root)
	if e != nil {
		return e
	}
	defer lease.Close()
	return RuntimeVerifierReplacementStartupGate(lease)
}

func TestRuntimeVerifierReplacementCommitReverseAndOriginalGate(t *testing.T) {
	f := newReplacementFixture(t)
	in := f.preflight(t)
	before, _ := os.ReadFile(filepath.Join(f.Root, "researchos.sqlite"))
	stateBefore, _ := os.ReadFile(filepath.Join(f.Root, "host", stateFile))
	id, _ := auth.Current()
	var state hostState
	if e := json.Unmarshal(stateBefore, &state); e != nil {
		t.Fatal(e)
	}
	db, e := sql.Open("sqlite", filepath.Join(f.Root, "researchos.sqlite"))
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	h := &Host{db: db, dir: filepath.Join(f.Root, "host"), identity: id, state: &state}
	if _, _, e = h.ensureRuntimeVerifier(context.Background(), f.Record.OwnerPrincipal, "project-a", f.New); e == nil || !strings.Contains(e.Error(), "explicit administrator replacement") {
		t.Fatalf("original mismatch gate lost: %v", e)
	}
	result, e := RuntimeVerifierReplacement(context.Background(), in)
	if e != nil || result.State != "COMMITTED" || result.Outcome != "APPLIED" {
		t.Fatalf("commit: %+v %v", result, e)
	}
	if e = replacementTestGate(f.Root); e != nil {
		t.Fatal(e)
	}
	replace := replacementReplace
	replacementReplace = func(string, string, string) error { t.Fatal("repeat commit replayed ReplaceFile"); return nil }
	defer func() { replacementReplace = replace }()
	result, e = RuntimeVerifierReplacement(context.Background(), in)
	if e != nil || result.Outcome != "APPLIED" {
		t.Fatalf("repeat: %+v %v", result, e)
	}
	replacementReplace = replace
	if _, _, e = h.ensureRuntimeVerifier(context.Background(), f.Record.OwnerPrincipal, "project-a", f.New); e != nil {
		t.Fatalf("new installation original gate: %v", e)
	}
	if _, _, e = h.ensureRuntimeVerifier(context.Background(), f.Record.OwnerPrincipal, "project-a", f.Old); e == nil {
		t.Fatal("old installation unexpectedly accepted")
	}
	after, _ := os.ReadFile(filepath.Join(f.Root, "researchos.sqlite"))
	stateAfter, _ := os.ReadFile(filepath.Join(f.Root, "host", stateFile))
	if !bytes.Equal(before, after) || !bytes.Equal(stateBefore, stateAfter) {
		t.Fatal("DB/state mutated")
	}
	rollback := f.Input
	rollback.OperationID = strings.Repeat("b", 32)
	rollback.Out = filepath.Join(f.Base, "reverse.json")
	rollback.Manifest = f.OldManifest
	oldManifest, _ := os.ReadFile(f.OldManifest)
	rollback.ExpectManifestSHA256 = domain.Digest(oldManifest)
	rollback.ExpectRecordSHA256 = result.NewRecordSHA256
	rollback.RollbackOf = f.Input.OperationID
	reversed, e := RuntimeVerifierReplacement(context.Background(), rollback)
	if e != nil {
		t.Fatal(e)
	}
	reversed, e = RuntimeVerifierReplacement(context.Background(), RuntimeVerifierReplacementInput{Action: "commit", DataRoot: f.Root, Plan: rollback.Out, ExpectPlanSHA256: reversed.PlanSHA256})
	if e != nil || reversed.Outcome != "APPLIED" {
		t.Fatalf("reverse: %+v %v", reversed, e)
	}
	if e = replacementTestGate(f.Root); e != nil {
		t.Fatal(e)
	}
	current, _ := os.ReadFile(filepath.Join(f.Root, "host", "runtime-verifier-installation.json"))
	if domain.Digest(current) != f.Input.ExpectRecordSHA256 {
		t.Fatal("reverse did not restore exact canonical fixture bytes")
	}
}

func TestRuntimeVerifierReplacementReadonlyCensus(t *testing.T) {
	cases := []struct{ name, query string }{
		{"run", `INSERT INTO domain_objects VALUES('foreign-project','Run','r','{"status":"READY"}')`},
		{"effect", `INSERT INTO resource_effects VALUES('foreign-project','r','e',1,'{"state":"UNKNOWN"}')`},
		{"dispatch", `INSERT INTO runtime_dispatches VALUES('foreign-project','r','STARTED')`},
		{"missing-managed-run", `INSERT INTO idempotency VALUES('foreign-project','host:managed-runtime-qualification','{"run_ref":{"id":"missing"}}')`},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			f := newReplacementFixture(t)
			f.exec(t, c.query)
			before, _ := os.ReadFile(filepath.Join(f.Root, "researchos.sqlite"))
			out, e := RuntimeVerifierReplacement(context.Background(), f.Input)
			if e == nil || out.Outcome != "NOT_APPLIED" {
				t.Fatalf("census allowed: %+v %v", out, e)
			}
			after, _ := os.ReadFile(filepath.Join(f.Root, "researchos.sqlite"))
			if !bytes.Equal(before, after) {
				t.Fatal("rejection mutated DB")
			}
		})
	}
	t.Run("settled-unknown-cost-and-unconsumed-expired-request", func(t *testing.T) {
		f := newReplacementFixture(t)
		f.exec(t, `INSERT INTO domain_objects VALUES('other','Run','r','{"status":"SETTLED"}'),('other','BudgetLedgerEntry','l','{"run_id":"r","operation":"UNKNOWN","cost_kind":"UNKNOWN"}');INSERT INTO idempotency VALUES('other','host:qualification-confirmation','{"expires_at":"2000-01-01T00:00:00Z","issued_at":"1999-12-31T23:59:00Z"}')`)
		f.preflight(t)
	})
}

func TestRuntimeVerifierReplacementReadonlyWALObservation(t *testing.T) {
	f := newReplacementFixture(t)
	db, e := sql.Open("sqlite", filepath.Join(f.Root, "researchos.sqlite"))
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	if _, e = db.Exec("PRAGMA journal_mode=WAL"); e != nil {
		t.Fatal(e)
	}
	if _, e = db.Exec(`INSERT INTO domain_objects VALUES('other','Run','settled','{"status":"SETTLED"}')`); e != nil {
		t.Fatal(e)
	}
	before := map[string]string{}
	for _, name := range []string{"researchos.sqlite", "researchos.sqlite-wal", "researchos.sqlite-shm"} {
		raw, e := os.ReadFile(filepath.Join(f.Root, name))
		if e != nil {
			t.Fatal(e)
		}
		before[name] = domain.Digest(raw)
	}
	if _, e = RuntimeVerifierReplacement(context.Background(), f.Input); e != nil {
		t.Fatal(e)
	}
	for _, name := range []string{"researchos.sqlite", "researchos.sqlite-wal", "researchos.sqlite-shm"} {
		raw, e := os.ReadFile(filepath.Join(f.Root, name))
		if e != nil {
			t.Fatal(e)
		}
		after := domain.Digest(raw)
		t.Logf("readonly WAL observation file=%s before=%s after=%s changed=%t", name, before[name], after, before[name] != after)
		if name != "researchos.sqlite-shm" && before[name] != after {
			t.Fatal("readonly changed database/WAL bytes")
		}
	}
	var n int
	if e = db.QueryRow("SELECT count(*) FROM domain_objects").Scan(&n); e != nil || n != 1 {
		t.Fatal("logical fixture state changed", e, n)
	}
}

func TestRuntimeVerifierReplacementIdentityAndInputs(t *testing.T) {
	for _, c := range []struct{ name, query string }{
		{"owner-revoked", `UPDATE auth_principals SET revoked=1 WHERE id='owner-fixture'`},
		{"multiple-owner", `INSERT INTO auth_principals VALUES('second','["OWNER"]',0,1)`},
		{"owner-lineage", `DELETE FROM orchestration_identity WHERE principal='owner-fixture'`},
		{"root-role", `UPDATE auth_principals SET roles='["VERIFIER","EXECUTOR"]' WHERE id LIKE 'local-verifier-root-%'`},
		{"root-grant", `INSERT INTO auth_grants SELECT id,'extra','','',0 FROM auth_principals WHERE id LIKE 'local-verifier-root-%'`},
		{"second-child-parent", `UPDATE orchestration_identity SET parent='foreign' WHERE principal IN (SELECT principal FROM auth_grants WHERE project='project-b')`},
		{"second-child-root", `UPDATE orchestration_identity SET root='foreign' WHERE principal IN (SELECT principal FROM auth_grants WHERE project='project-b')`},
		{"second-child-grant", `UPDATE auth_grants SET restricted=1 WHERE project='project-b'`},
		{"missing-child-principal", `DELETE FROM auth_principals WHERE id IN (SELECT principal FROM auth_grants WHERE project='project-b')`},
		{"schema-drift", `DELETE FROM schema_migrations WHERE version=24`},
		{"missing-table", `DROP TABLE resource_effects`},
	} {
		t.Run(c.name, func(t *testing.T) {
			f := newReplacementFixture(t)
			f.exec(t, c.query)
			if _, e := RuntimeVerifierReplacement(context.Background(), f.Input); e == nil {
				t.Fatal("identity/schema drift allowed")
			}
		})
	}
	for _, name := range []string{"state-ref", "state-host", "state-owner", "state-version", "raw-record", "canonical-as-raw", "manifest-duplicate", "manifest-unknown", "manifest-trailing", "manifest-oversize", "manifest-service", "manifest-protocol", "manifest-commit", "manifest-args", "image-drift", "manifest-acl", "registration-acl", "manifest-owner"} {
		t.Run(name, func(t *testing.T) {
			f := newReplacementFixture(t)
			switch name {
			case "state-ref", "state-host", "state-owner", "state-version":
				path := filepath.Join(f.Root, "host", stateFile)
				raw, _ := os.ReadFile(path)
				var state hostState
				json.Unmarshal(raw, &state)
				switch name {
				case "state-ref":
					state.PrincipalRef = "foreign"
				case "state-host":
					state.HostInstanceID = "foreign"
				case "state-owner":
					state.PrincipalID = "foreign"
				case "state-version":
					state.Version = 2
				}
				replacementTestWrite(t, path, state)
			case "raw-record":
				f.Input.ExpectRecordSHA256 = "sha256:" + strings.Repeat("0", 64)
			case "canonical-as-raw":
				f.Input.ExpectRecordSHA256 = domain.Hash(f.Record)
			case "manifest-duplicate", "manifest-unknown", "manifest-trailing", "manifest-oversize":
				raw, _ := os.ReadFile(f.Manifest)
				switch name {
				case "manifest-duplicate":
					raw = append([]byte(`{"schema":"duplicate",`), raw[1:]...)
				case "manifest-unknown":
					raw = append([]byte(`{"extra":1,`), raw[1:]...)
				case "manifest-trailing":
					raw = append(raw, []byte("{}")...)
				case "manifest-oversize":
					raw = bytes.Repeat([]byte(" "), (64<<10)+1)
				}
				os.WriteFile(f.Manifest, raw, 0600)
				f.Input.ExpectManifestSHA256 = domain.Digest(raw)
			case "manifest-service", "manifest-protocol", "manifest-commit", "manifest-args":
				v := f.New
				switch name {
				case "manifest-service":
					v.ServiceID = "bad"
				case "manifest-protocol":
					v.Protocol = "bad"
				case "manifest-commit":
					v.SourceCommit = "bad"
				case "manifest-args":
					v.Arguments = []string{"evil"}
				}
				raw := replacementTestWrite(t, f.Manifest, v)
				f.Input.ExpectManifestSHA256 = domain.Digest(raw)
			case "image-drift":
				os.WriteFile(f.New.Executable, []byte("MZchanged"), 0600)
			case "manifest-acl", "registration-acl":
				path := f.Manifest
				if name == "registration-acl" {
					path = filepath.Join(f.Root, "host", "runtime-verifier-installation.json")
				}
				sid, _ := currentSIDString()
				sd, _ := windows.SecurityDescriptorFromString("D:P(A;;FA;;;" + sid + ")(A;;FR;;;WD)")
				acl, _, _ := sd.DACL()
				if e := windows.SetNamedSecurityInfo(path, windows.SE_FILE_OBJECT, windows.DACL_SECURITY_INFORMATION|windows.PROTECTED_DACL_SECURITY_INFORMATION, nil, nil, acl, nil); e != nil {
					t.Fatal(e)
				}
			case "manifest-owner":
				sid, e := windows.StringToSid("S-1-5-32-544")
				if e != nil {
					t.Fatal(e)
				}
				e = windows.SetNamedSecurityInfo(f.Manifest, windows.SE_FILE_OBJECT, windows.OWNER_SECURITY_INFORMATION, sid, nil, nil, nil)
				if e != nil {
					t.Skipf("foreign owner fixture requires WRITE_OWNER: %v", e)
				}
			}
			if _, e := RuntimeVerifierReplacement(context.Background(), f.Input); e == nil {
				t.Fatal("bad identity/input accepted")
			}
		})
	}
}

func TestRuntimeVerifierReplacementLeaseMissingPathsAndPlan(t *testing.T) {
	f := newReplacementFixture(t)
	lease, e := rt.AcquireDataRootLease(f.Root)
	if e != nil {
		t.Fatal(e)
	}
	if _, e = RuntimeVerifierReplacement(context.Background(), f.Input); e == nil {
		t.Fatal("active Core lease accepted")
	}
	lease.Close()
	in := f.preflight(t)
	plan, _ := os.ReadFile(f.Plan)
	os.WriteFile(f.Plan, append(plan, ' '), 0600)
	if _, e = RuntimeVerifierReplacement(context.Background(), in); e == nil {
		t.Fatal("changed plan accepted")
	}
	os.WriteFile(f.Plan, plan, 0600)
	stale := f.Input
	stale.OperationID = strings.Repeat("c", 32)
	stale.Out = filepath.Join(f.Base, "stale.json")
	out, e := RuntimeVerifierReplacement(context.Background(), stale)
	if e != nil {
		t.Fatal(e)
	}
	if _, e = RuntimeVerifierReplacement(context.Background(), in); e != nil {
		t.Fatal(e)
	}
	if _, e = RuntimeVerifierReplacement(context.Background(), RuntimeVerifierReplacementInput{Action: "commit", DataRoot: f.Root, Plan: stale.Out, ExpectPlanSHA256: out.PlanSHA256}); e == nil {
		t.Fatal("stale plan accepted")
	}
	for _, path := range []string{"missing", "host/host_state.json", "host/runtime-verifier-installation.json", "researchos.sqlite"} {
		t.Run(path, func(t *testing.T) {
			f := newReplacementFixture(t)
			if path == "missing" {
				f.Input.DataRoot = filepath.Join(f.Base, "absent")
			} else {
				if e := os.Remove(filepath.Join(f.Root, filepath.FromSlash(path))); e != nil {
					t.Fatal(e)
				}
			}
			if _, e := RuntimeVerifierReplacement(context.Background(), f.Input); e == nil {
				t.Fatal("missing input accepted")
			}
			if path == "missing" {
				if _, e := os.Stat(f.Input.DataRoot); !os.IsNotExist(e) {
					t.Fatal("created missing root")
				}
			}
		})
	}
	for _, path := range []string{"relative", `\\server\share\data`, f.Root + `\..\data`} {
		in := f.Input
		in.DataRoot = path
		if _, e := RuntimeVerifierReplacement(context.Background(), in); e == nil {
			t.Fatal("noncanonical root accepted")
		}
	}
}

func TestRuntimeVerifierReplacementExternalRenameUnknown(t *testing.T) {
	f := newReplacementFixture(t)
	in := f.preflight(t)
	original := replacementReplace
	defer func() { replacementReplace = original }()
	external := []byte("external-third-party-image")
	replacementReplace = func(target, stage, backup string) error {
		if e := os.Rename(target, target+".external-old"); e != nil {
			return e
		}
		if e := os.WriteFile(target, external, 0600); e != nil {
			return e
		}
		if e := privateFile(target); e != nil {
			return e
		}
		return callReplaceFile(target, stage, backup)
	}
	result, e := RuntimeVerifierReplacement(context.Background(), in)
	if e == nil || result.Outcome != "UNKNOWN" {
		t.Fatalf("race mislabeled: %+v %v", result, e)
	}
	dir := filepath.Join(f.Root, "host", replacementJournal, f.Input.OperationID)
	backup, _ := os.ReadFile(filepath.Join(dir, "actual-backup.bin"))
	old, _ := os.ReadFile(filepath.Join(dir, "old-registration.bin"))
	candidate, _ := os.ReadFile(filepath.Join(dir, "new-registration.bin"))
	current, _ := os.ReadFile(filepath.Join(f.Root, "host", "runtime-verifier-installation.json"))
	if !bytes.Equal(backup, external) || domain.Digest(old) != f.Input.ExpectRecordSHA256 || !bytes.Equal(current, candidate) {
		t.Fatalf("race evidence images not preserved: err=%v backup=%q old=%s candidate=%d current=%q", e, backup, domain.Digest(old), len(candidate), current)
	}
	if replacementTestGate(f.Root) == nil {
		t.Fatal("startup accepted UNKNOWN")
	}
	for _, action := range []string{"inspect", "complete", "abort"} {
		recover := in
		recover.Action = "recover"
		recover.OperationID = f.Input.OperationID
		recover.RecoveryAction = action
		if _, e := RuntimeVerifierReplacement(context.Background(), recover); e == nil {
			t.Fatal("ambiguous recovery guessed")
		}
	}
}
