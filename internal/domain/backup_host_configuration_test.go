package domain

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"researchos.local/research-os/internal/store"
)

func TestBackupHostConfigurationFrozenSchemas(t *testing.T) {
	for _, pair := range [][2][]byte{{backupConfigurationProtocol, backupConfigurationDomain}, {append(append([]byte{}, backupConfigurationProtocol...), '\n'), backupConfigurationDomain}, {backupConfigurationProtocol, append(append([]byte{}, backupConfigurationDomain...), '\n')}} {
		doc, e := loadBackupConfigurationSchema(pair[0], pair[1])
		valid := Digest(pair[0]) == Digest(backupConfigurationProtocol) && Digest(pair[1]) == Digest(backupConfigurationDomain)
		if valid && (e != nil || doc == nil) {
			t.Fatal(e)
		}
		if !valid && e == nil {
			t.Fatal("valid JSON byte drift accepted")
		}
	}
	for _, pair := range [][2]string{{"../api/contracts/client.protocol.schema.json", "contracts/client.protocol.schema.json"}, {"../api/contracts/domain.schema.json", "contracts/client.protocol.domain.schema.json"}} {
		a, e := os.ReadFile(pair[0])
		if e != nil {
			t.Fatal(e)
		}
		b, e := os.ReadFile(pair[1])
		if e != nil || Digest(a) != Digest(b) {
			t.Fatal("mirror drift", e)
		}
	}
	db, _ := configurationDB(t, 23, true)
	if e := validateBackupHostConfiguration(db); e != nil {
		t.Fatal(e)
	}
	for _, version := range []int{13, 20, 21, 22} {
		old, _ := configurationDB(t, version, false)
		if e := validateBackupHostConfiguration(old); e != nil {
			t.Fatalf("legacy%d: %v", version, e)
		}
	}
}

func configurationBackupMutation(t *testing.T, db *sql.DB, query string, args ...any) {
	t.Helper()
	triggers, e := configurationBackupRows(db, `SELECT name,sql FROM sqlite_master WHERE type='trigger'`)
	if e != nil {
		t.Fatal(e)
	}
	if _, e = db.Exec(`PRAGMA foreign_keys=OFF`); e != nil {
		t.Fatal(e)
	}
	for _, r := range triggers {
		if _, e = db.Exec(`DROP TRIGGER "` + Str(r, "name") + `"`); e != nil {
			t.Fatal(e)
		}
	}
	if _, e = db.Exec(query, args...); e != nil {
		t.Fatal(e)
	}
	for _, r := range triggers {
		if _, e = db.Exec(Str(r, "sql")); e != nil {
			t.Fatal(e)
		}
	}
	if _, e = db.Exec(`PRAGMA foreign_keys=ON`); e != nil {
		t.Fatal(e)
	}
}

func TestBackupHostConfigurationCompleteHistoryRefusals(t *testing.T) {
	for name, query := range map[string]string{
		"historical_payload":  `UPDATE host_model_configurations SET canonical_config_json=json_set(canonical_config_json,'$.model_id','changed') WHERE config_revision=1`,
		"historical_scope":    `UPDATE host_model_configurations SET operation_scope_json=json_set(operation_scope_json,'$.client_id','changed') WHERE config_revision=1`,
		"historical_time":     `UPDATE host_model_configurations SET created_at='invalid' WHERE config_revision=1`,
		"missing_old_history": `DELETE FROM host_model_configurations WHERE config_revision=1`,
		"missing_head":        `DELETE FROM host_model_config_heads`,
		"head_old_revision":   `UPDATE host_model_config_heads SET current_revision=1,default_model_config_ref=(SELECT model_config_ref FROM host_model_configurations WHERE config_revision=1)`,
		"foreign_owner":       `UPDATE host_model_config_heads SET owner_host_ref='host-ffffffffffff'`,
		"missing_principal":   `DELETE FROM auth_principals`,
		"bad_principal":       `UPDATE auth_principals SET roles='null'`,
		"missing_receipt":     `DELETE FROM idempotency WHERE key='first'`,
		"wrong_request_hash":  `UPDATE idempotency SET request_hash='sha256:0000000000000000000000000000000000000000000000000000000000000000' WHERE key='first'`,
		"response_identity":   `UPDATE idempotency SET body=json_set(body,'$.command_id','other') WHERE key='first'`,
		"response_unknown":    `UPDATE idempotency SET body=json_set(body,'$.unknown',1) WHERE key='first'`,
		"response_projection": `UPDATE idempotency SET body=json_set(body,'$.result.model_id','other') WHERE key='first'`,
		"response_secret":     `UPDATE idempotency SET body=json_set(body,'$.result.api_key','synthetic-never-real') WHERE key='first'`,
		"response_verified":   `UPDATE idempotency SET body=json_set(body,'$.result.verified_at','2026-10-07T00:00:00Z') WHERE key='first'`,
		"ambiguous_legacy":    `INSERT INTO idempotency SELECT principal,'other-project','v2:host.status',key,request_hash,status,body,headers,created_at FROM idempotency WHERE key='first'`,
	} {
		t.Run(name, func(t *testing.T) {
			db, _ := configurationDB(t, 23, true)
			doc := configurationSchema(t)
			configurationCommit(t, db, doc, "first", 1)
			configurationCommit(t, db, doc, "second", 2)
			if e := validateBackupHostConfiguration(db); e != nil {
				t.Fatal(e)
			}
			configurationBackupMutation(t, db, query)
			if e := validateBackupHostConfiguration(db); e == nil {
				t.Fatal("corrupt history accepted")
			} else {
				t.Log(e)
			}
			contracts, e := LoadContracts("../../spec/v2.0/contracts")
			if e != nil {
				t.Fatal(e)
			}
			destination := filepath.Join(t.TempDir(), "invalid-backup")
			if _, e = (&Service{DB: db, Contracts: contracts}).CreateBackup(context.Background(), destination, backupTestKey(t)); e == nil {
				t.Fatal("public backup accepted corrupt configuration history")
			}
			if _, e = os.Stat(destination); !os.IsNotExist(e) {
				t.Fatal("corrupt backup published", e)
			}
		})
	}
}

func TestBackupHostConfigurationSchemaRefusals(t *testing.T) {
	for _, query := range []string{"DROP TABLE host_model_config_heads", "DROP TRIGGER host_config_no_update", "DROP INDEX client_identity_receipt_request", "CREATE INDEX unexpected_configuration_index ON host_model_configurations(principal)", "DELETE FROM schema_migrations WHERE version=12", "INSERT INTO schema_migrations(version) VALUES(24)"} {
		t.Run(strings.Fields(query)[0]+query, func(t *testing.T) {
			db, _ := configurationDB(t, 23, true)
			if _, e := db.Exec(query); e != nil {
				t.Fatal(e)
			}
			if e := validateBackupHostConfiguration(db); e == nil {
				t.Fatal("schema corruption accepted")
			}
		})
	}
}

func TestBackupHostConfigurationPublicRoundTrip(t *testing.T) {
	ctx := context.Background()
	db, _ := configurationDB(t, 23, true)
	doc := configurationSchema(t)
	first := configurationCommit(t, db, doc, "first", 1)
	configurationCommit(t, db, doc, "second", 2)
	raw := Bytes(Object{"protocol_version": ProtocolV2, "command_id": "ordinary-refusal", "client_id": "fixture", "project_id": nil, "session_id": nil, "expected_revision": nil, "writer_epoch": nil, "method": "host.status", "payload": Object{}})
	env, e := decodeClientIdentityEnvelope(doc, raw)
	if e != nil {
		t.Fatal(e)
	}
	tx, e := db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	identityRefusal(t, tx, doc, raw, env)
	if e = tx.Commit(); e != nil {
		t.Fatal(e)
	}
	contracts, e := LoadContracts("../../spec/v2.0/contracts")
	if e != nil {
		t.Fatal(e)
	}
	svc := &Service{DB: db, Contracts: contracts}
	key := backupTestKey(t)
	if _, e = svc.IssueCredential(ctx, configurationFixturePrincipal, 5*60*1000000000); e != nil {
		t.Fatal(e)
	}
	before, e := backupHostConfigurationState(db)
	if e != nil {
		t.Fatal(e)
	}
	configurationEvidenceSnapshot(t, db, "typed-source23")
	dir := filepath.Join(t.TempDir(), "backup")
	if _, e = svc.CreateBackup(ctx, dir, key); e != nil {
		t.Fatal(e)
	}
	dst := filepath.Join(t.TempDir(), "restored")
	if _, e = RestoreBackup(ctx, dir, dst, RestoreOptions{Key: key, SupportedMigrations: upgradeVersions(23), Contracts: contracts, DatabaseName: "researchos.sqlite"}); e != nil {
		t.Fatal(e)
	}
	restored, e := store.Open(filepath.Join(dst, "researchos.sqlite"))
	if e != nil {
		t.Fatal(e)
	}
	defer restored.Close()
	after, e := backupHostConfigurationState(restored)
	if e != nil || Hash(before) != Hash(after) {
		t.Fatal("typed history/original response changed", e)
	}
	configurationEvidenceSnapshot(t, restored, "typed-restored23")
	var live int
	if e = restored.QueryRow(`SELECT count(*) FROM auth_credentials WHERE revoked=0`).Scan(&live); e != nil || live != 0 {
		t.Fatal("auth not revoked", e)
	}
	tx, e = restored.Begin()
	if e != nil {
		t.Fatal(e)
	}
	r, e := readClientConfiguration(ctx, tx, doc, configurationFixtureOwner, configurationFixturePrincipal, first.Ref)
	tx.Rollback()
	if e != nil || r.ConfigHash != first.ConfigHash || clientConfigurationProjection(r)["verified_at"] != nil {
		t.Fatal("historical config rebound", e)
	}
	if _, e = (&Service{DB: restored, Contracts: contracts}).CreateBackup(ctx, filepath.Join(t.TempDir(), "rebackup"), key); e != nil {
		t.Fatal(e)
	}
	if _, e = restored.Exec(`UPDATE idempotency SET body=body`); e == nil || !strings.Contains(e.Error(), "immutable replay") {
		t.Fatalf("old immutable replay guard: %v", e)
	}
	t.Log("private storage fixture; public backup/restore/rebackup; historical refs stay unqualified; original response immutable")
}

func TestBackupHostConfigurationOtherMethodIdentity(t *testing.T) {
	for _, mutation := range []string{"valid", "principal", "identity_time", "identity_method", "original_project", "missing_result", "response_protocol", "unknown_field", "external_workspace"} {
		t.Run(mutation, func(t *testing.T) {
			db, _ := configurationDB(t, 23, true)
			doc := configurationSchema(t)
			raw := Bytes(Object{"protocol_version": ProtocolV2, "command_id": "host-status-original", "client_id": "fixture", "project_id": nil, "session_id": nil, "expected_revision": nil, "writer_epoch": nil, "method": "host.status", "payload": Object{}})
			env, e := decodeClientIdentityEnvelope(doc, raw)
			if e != nil {
				t.Fatal(e)
			}
			tx, e := db.Begin()
			if e != nil {
				t.Fatal(e)
			}
			if _, e = reserveClientCommandIdentity(context.Background(), tx, doc, configurationFixturePrincipal, raw, env); e != nil {
				t.Fatal(e)
			}
			response := &Response{ProtocolVersion: strptr(ProtocolV2), CommandID: env.CommandID, Method: env.Method, Status: strptr("COMPLETED"), Result: Object{"host_instance_id": "fixture-host", "core_build_id": "fixture-build", "protocol_versions": []any{ProtocolV2}, "host_state": "READY", "client_id": "fixture", "authenticated_principal_ref": configurationFixturePrincipal, "config_revision": 0, "model_configurations": Empty(), "credentials": Empty(), "workspaces": Empty(), "supported_methods": []any{"host.status"}, "operating_mode": "LOCAL_USER_HOST"}}
			if e = configurationReceipt(tx, configurationFixturePrincipal, env, response); e != nil {
				t.Fatal(e)
			}
			if e = tx.Commit(); e != nil {
				t.Fatal(e)
			}
			if e = validateBackupHostConfiguration(db); e != nil {
				t.Fatal(e)
			}
			if mutation == "valid" {
				return
			}
			query := map[string]string{"principal": `UPDATE idempotency SET body=json_set(body,'$.result.authenticated_principal_ref','foreign')`, "identity_time": `UPDATE client_command_identities SET created_at='invalid'`, "identity_method": `UPDATE client_command_identities SET method='provider.models',operation='v2:provider.models'`, "original_project": `UPDATE idempotency SET project='foreign'`, "missing_result": `UPDATE idempotency SET body=json_remove(body,'$.result.core_build_id')`, "response_protocol": `UPDATE idempotency SET body=json_set(body,'$.protocol_version','other')`, "unknown_field": `UPDATE idempotency SET body=json_set(body,'$.result.extra',1)`, "external_workspace": `UPDATE idempotency SET body=json_set(body,'$.result.workspaces',json('[{"authorized_workspace_ref":"forged"}]'))`}[mutation]
			configurationBackupMutation(t, db, query)
			if e = validateBackupHostConfiguration(db); e == nil {
				t.Fatal("unrelated method corrupt identity accepted")
			} else {
				t.Log(e)
			}
		})
	}
}

// Explicit bounded workspace fixture; no user filesystem authority is inferred
// from a database path. Only this test's originally chosen empty root is read.
type handlerBackupWorkspace struct{ path, principal string }

func (w handlerBackupWorkspace) ConsumeSelection(_ context.Context, selection, client, principal string) (WorkspaceSelection, error) {
	if selection != "handler-selection" || client != "config-client" || principal != w.principal {
		return WorkspaceSelection{}, fmt.Errorf("foreign synthetic selection")
	}
	return WorkspaceSelection{RealPath: w.path, DisplayPath: w.path, Access: "READ_ONLY", HostPrincipalRef: "SYNTHETIC-METADATA", ClientID: client}, nil
}
func (w handlerBackupWorkspace) ConfirmPath(_ context.Context, path, access string) error {
	if path != w.path || access != "READ_ONLY" {
		return fmt.Errorf("foreign synthetic root")
	}
	_, e := os.Stat(path)
	return e
}
func (w handlerBackupWorkspace) Scan(_ context.Context, path string) (LocalInventoryScan, error) {
	if path != w.path {
		return LocalInventoryScan{}, fmt.Errorf("foreign synthetic scan")
	}
	return LocalInventoryScan{Environment: "handler-public-backup-fixture", Entries: []LocalInventoryEntry{}, Failures: []LocalInventoryFileFailure{}}, nil
}

func (w handlerBackupWorkspace) SnapshotWorkspace(_ context.Context, b WorkspaceBinding, _ string, _ BackupWorkspaceLimits) (BackupWorkspaceSnapshot, error) {
	if b.RealPath != w.path || b.PrincipalID != w.principal {
		return BackupWorkspaceSnapshot{}, fmt.Errorf("foreign fixture workspace")
	}
	entries, e := os.ReadDir(w.path)
	if e != nil {
		return BackupWorkspaceSnapshot{}, e
	}
	if len(entries) != 0 {
		return BackupWorkspaceSnapshot{}, fmt.Errorf("fixture root not empty")
	}
	return BackupWorkspaceSnapshot{Directories: []string{}, Files: []BackupWorkspaceFile{}}, nil
}

func TestHandlerRejectedSessionPublicBackupReplay(t *testing.T) {
	f := setup(t)
	doc := configurationSchema(t)
	port := handlerBackupWorkspace{t.TempDir(), f.owner}
	owner := Principal{ID: f.owner, Roles: []string{"OWNER"}, CanCreateProject: true}
	b, e := f.s.RegisterWorkspace(context.Background(), owner, port, doc, RegisterWorkspaceInput{SelectionRef: "handler-selection", DisplayName: "Public backup fixture", RequestedAccess: "READ_ONLY", CommandID: ID(), ClientID: "config-client"})
	if e != nil {
		t.Fatal(e)
	}
	project, e := f.s.BootstrapProject(context.Background(), owner, port, doc, port, BootstrapProjectInput{AuthorizedWorkspaceRef: Str(b, "authorized_workspace_ref"), DisplayName: "Public backup fixture", ClientID: "config-client", CommandID: ID(), MeasurementMode: "FIXTURE"})
	if e != nil {
		t.Fatal(e)
	}
	f.project = Str(project, "project_id")
	s := &ClientService{Doc: doc, Domain: f.s, ConfigurationAuthority: handlerMetadataFixture{f.owner}, Host: ClientHostInfo{InstanceID: configurationFixtureOwner, CoreBuildID: "fixture", LeaseTTL: time.Hour}}
	configured, _ := handlerCommand(t, f, s, handlerDefaultEnvelope(1))
	if deref(configured.Status) != "COMPLETED" {
		t.Fatal(string(Bytes(configured)))
	}
	created, _ := handlerCommand(t, f, s, &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("config-client"), ProjectID: &f.project, Method: strptr("session.create"), Payload: Bytes(Object{"workspace_ref": Str(b, "authorized_workspace_ref"), "model_config_ref": Str(configured.Result, "model_config_ref"), "title": "offline backup"})})
	if deref(created.Status) != "COMPLETED" {
		t.Fatal(string(Bytes(created)))
	}
	sid := deref(created.SessionID)
	unknown := "absent-session-" + ID()
	env := handlerDefaultEnvelope(2)
	env.ProjectID, env.SessionID, env.ExpectedRevision, env.WriterEpoch = &f.project, &unknown, revPtr(1), revPtr(1)
	r, _ := handlerCommand(t, f, s, env)
	if deref(r.Status) != "REJECTED" || deref(r.SessionID) != unknown || deref(r.ErrorCode) != "NOT_FOUND" {
		t.Fatalf("original refusal: %s", Bytes(r))
	}
	original := string(Bytes(r))
	// A different project with a real Session is also a legal original refusal;
	// its original request scope must survive backup and exact replay.
	foreign := *env
	foreign.CommandID, foreign.SessionID, foreign.ProjectID = strptr(ID()), &sid, strptr("foreign-project")
	r, _ = handlerCommand(t, f, s, &foreign)
	if deref(r.Status) != "REJECTED" || deref(r.SessionID) != sid {
		t.Fatal(string(Bytes(r)))
	}
	scoped := handlerDefaultEnvelope(2)
	scoped.ProjectID = &f.project
	scoped.SessionID = &sid
	scoped.ExpectedRevision = revPtr(1)
	scoped.WriterEpoch = revPtr(1)
	scopedReply, _ := handlerCommand(t, f, s, scoped)
	if deref(scopedReply.Status) != "COMPLETED" {
		t.Fatal(string(Bytes(scopedReply)))
	}
	for revision := int64(3); revision <= 201; revision++ {
		saved, _ := handlerCommand(t, f, s, handlerDefaultEnvelope(revision))
		if deref(saved.Status) != "COMPLETED" {
			t.Fatal(string(Bytes(saved)))
		}
	}
	status, _ := handlerCommand(t, f, s, &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("config-client"), Method: strptr("host.status"), Payload: Bytes(Object{})})
	if deref(status.Status) != "COMPLETED" || len(Arr(status.Result, "model_configurations")) != 100 {
		t.Fatal("public backup did not cover full history outside bounded status")
	}
	var historicalConfigs int
	f.db.QueryRow(`SELECT count(*) FROM host_model_configurations`).Scan(&historicalConfigs)
	if historicalConfigs != 201 {
		t.Fatal("history was pruned")
	}
	if e := validateBackupHostConfiguration(f.db); e != nil {
		t.Fatal(e)
	}
	key := backupTestKey(t)
	dir := filepath.Join(t.TempDir(), "backup")
	var root string
	if e := f.db.QueryRow(`SELECT json_extract(body,'$.real_path') FROM domain_objects WHERE kind='WorkspaceBinding'`).Scan(&root); e != nil {
		t.Fatal(e)
	}
	if _, e := f.s.CreateBackupWithWorkspaces(context.Background(), dir, key, handlerBackupWorkspace{root, f.owner}); e != nil {
		t.Fatal(e)
	}
	dst := filepath.Join(t.TempDir(), "restore")
	var rebound string
	pin := func(_ context.Context, _ string, requests []WorkspaceRestoreRequest) ([]WorkspaceRestorePin, error) {
		pins := []WorkspaceRestorePin{}
		for _, request := range requests {
			if request.PrincipalID != f.owner {
				return nil, fmt.Errorf("foreign restored principal")
			}
			rebound = request.RealPath
			pins = append(pins, WorkspaceRestorePin{AuthorizedRef: request.AuthorizedRef, RealPath: request.RealPath, HostPrincipalRef: "SYNTHETIC-RESTORED-METADATA"})
		}
		return pins, nil
	}
	if _, e := RestoreBackup(context.Background(), dir, dst, RestoreOptions{Key: key, SupportedMigrations: upgradeVersions(23), Contracts: f.s.Contracts, DatabaseName: "researchos.sqlite", WorkspaceTarget: pin}); e != nil {
		t.Fatal(e)
	}
	db, e := store.Open(filepath.Join(dst, "researchos.sqlite"))
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	configurationEvidenceSnapshot(t, f.db, "handler-legal-refusals-source")
	configurationEvidenceSnapshot(t, db, "handler-legal-refusals-restored")
	for _, request := range []*Envelope{env, &foreign} {
		tx, e := db.Begin()
		if e != nil {
			t.Fatal(e)
		}
		response, replay, e := s.Execute(context.Background(), tx, handlerDecode(t, request), f.owner)
		if e != nil {
			tx.Rollback()
			t.Fatal(e)
		}
		if !replay || deref(response.SessionID) != deref(request.SessionID) || (request == env && string(Bytes(response)) != original) {
			tx.Rollback()
			t.Fatal("restored original replay differs")
		}
		if e = tx.Commit(); e != nil {
			t.Fatal(e)
		}
	}
	if rebound == "" || rebound == root {
		t.Fatal("restored workspace not isolated")
	}
	if _, e = (&Service{DB: db, Contracts: f.s.Contracts}).CreateBackupWithWorkspaces(context.Background(), filepath.Join(t.TempDir(), "rebackup"), key, handlerBackupWorkspace{rebound, f.owner}); e != nil {
		t.Fatal(e)
	}
}

func TestHandlerRejectedOriginalProofBackupTampering(t *testing.T) {
	for _, mutation := range []string{"response-SID", "request-SID", "request-payload", "journal-hash", "identity-project", "success-without-session", "remove-original", "noncanonical-base64"} {
		t.Run(mutation, func(t *testing.T) {
			f := contextFixture(t)
			s, _, _ := handlerTypedSession(t, f, "config-client")
			env := handlerDefaultEnvelope(2)
			env.ProjectID = &f.project
			env.SessionID = strptr("missing-session")
			env.ExpectedRevision = revPtr(1)
			env.WriterEpoch = revPtr(1)
			r, _ := handlerCommand(t, f, s, env)
			if deref(r.Status) != "REJECTED" {
				t.Fatal(string(Bytes(r)))
			}
			if e := validateBackupHostConfiguration(f.db); e != nil {
				t.Fatal(e)
			}
			switch mutation {
			case "response-SID":
				configurationBackupMutation(t, f.db, `UPDATE idempotency SET body=json_set(body,'$.session_id','other') WHERE key=?`, *env.CommandID)
			case "journal-hash":
				configurationBackupMutation(t, f.db, `UPDATE idempotency SET request_hash=? WHERE key=?`, Digest([]byte("different")), *env.CommandID)
			case "identity-project":
				configurationBackupMutation(t, f.db, `UPDATE client_command_identities SET project='other' WHERE command_id=?`, *env.CommandID)
			case "success-without-session":
				configurationBackupMutation(t, f.db, `UPDATE idempotency SET body=json_set(body,'$.status','COMPLETED','$.error',NULL,'$.error_code',NULL) WHERE key=?`, *env.CommandID)
			case "remove-original":
				configurationBackupMutation(t, f.db, `UPDATE idempotency SET headers='{}' WHERE key=?`, *env.CommandID)
			default:
				var h string
				f.db.QueryRow(`SELECT headers FROM idempotency WHERE key=?`, *env.CommandID).Scan(&h)
				request, _, e := readClientCommandEnvelope(s.Doc, h)
				if e != nil {
					t.Fatal(e)
				}
				if mutation == "request-SID" {
					request.env.SessionID = strptr("other")
				} else if mutation == "request-payload" {
					request.env.Payload = Bytes(Object{"config_revision": 2, "provider_id": "fixture-provider", "base_url": "https://fixture.invalid/v1", "model_id": "different", "credential_ref": nil})
				}
				altered := handlerDecode(t, request.env)
				h, e = writeClientCommandEnvelope(s.Doc, altered)
				if e != nil {
					t.Fatal(e)
				}
				if mutation == "noncanonical-base64" {
					h = " " + h
				}
				configurationBackupMutation(t, f.db, `UPDATE idempotency SET headers=? WHERE key=?`, h, *env.CommandID)
			}
			if e := validateBackupHostConfiguration(f.db); e == nil {
				t.Fatal("modified original proof accepted")
			}
			destination := filepath.Join(t.TempDir(), "refused")
			if _, e := f.s.CreateBackup(context.Background(), destination, backupTestKey(t)); e == nil {
				t.Fatal("corrupt backup published")
			}
			if _, e := os.Stat(destination); !os.IsNotExist(e) {
				t.Fatal("failed backup left published directory", e)
			}
		})
	}
}

func TestHandlerNewIdentityRequiresOriginalHeader(t *testing.T) {
	for _, method := range []string{"default", "scoped", "create"} {
		t.Run(method, func(t *testing.T) {
			f := setup(t)
			doc := configurationSchema(t)
			port := handlerBackupWorkspace{t.TempDir(), f.owner}
			owner := Principal{ID: f.owner, Roles: []string{"OWNER"}, CanCreateProject: true}
			b, e := f.s.RegisterWorkspace(context.Background(), owner, port, doc, RegisterWorkspaceInput{SelectionRef: "handler-selection", DisplayName: "Header fixture", RequestedAccess: "READ_ONLY", CommandID: ID(), ClientID: "config-client"})
			if e != nil {
				t.Fatal(e)
			}
			project, e := f.s.BootstrapProject(context.Background(), owner, port, doc, port, BootstrapProjectInput{AuthorizedWorkspaceRef: Str(b, "authorized_workspace_ref"), DisplayName: "Header fixture", ClientID: "config-client", CommandID: ID(), MeasurementMode: "FIXTURE"})
			if e != nil {
				t.Fatal(e)
			}
			f.project = Str(project, "project_id")
			defer configurationEvidenceSnapshot(t, f.db, "new-identity-header-"+method)
			svc := &ClientService{Doc: doc, Domain: f.s, ConfigurationAuthority: handlerMetadataFixture{f.owner}, Host: ClientHostInfo{InstanceID: configurationFixtureOwner, CoreBuildID: "fixture", LeaseTTL: time.Hour}}
			original := handlerDefaultEnvelope(1)
			saved, _ := handlerCommand(t, f, svc, original)
			if deref(saved.Status) != "COMPLETED" {
				t.Fatal(string(Bytes(saved)))
			}
			create := &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("config-client"), ProjectID: &f.project, Method: strptr("session.create"), Payload: Bytes(Object{"workspace_ref": Str(b, "authorized_workspace_ref"), "model_config_ref": Str(saved.Result, "model_config_ref"), "title": "offline header"})}
			created, _ := handlerCommand(t, f, svc, create)
			if deref(created.Status) != "COMPLETED" {
				t.Fatal(string(Bytes(created)))
			}
			if method == "create" {
				original = create
			}
			if method == "scoped" {
				sid := deref(created.SessionID)
				original = handlerDefaultEnvelope(2)
				original.ProjectID = &f.project
				original.SessionID = &sid
				original.ExpectedRevision = revPtr(1)
				original.WriterEpoch = revPtr(1)
				r, _ := handlerCommand(t, f, svc, original)
				if deref(r.Status) != "COMPLETED" {
					t.Fatal(string(Bytes(r)))
				}
			}
			key := backupTestKey(t)
			if _, e = f.s.CreateBackupWithWorkspaces(context.Background(), filepath.Join(t.TempDir(), "valid"), key, port); e != nil {
				t.Fatal("positive public backup", e)
			}
			configurationBackupMutation(t, f.db, `UPDATE idempotency SET headers='{}' WHERE key=?`, *original.CommandID)
			tx, e := f.db.Begin()
			if e != nil {
				t.Fatal(e)
			}
			_, _, replayErr := svc.Execute(context.Background(), tx, handlerDecode(t, original), f.owner)
			tx.Rollback()
			if replayErr == nil {
				t.Error("new command lost original header but replay was accepted")
			}
			if _, e = f.s.CreateBackupWithWorkspaces(context.Background(), filepath.Join(t.TempDir(), "corrupt"), key, port); e == nil {
				t.Error("public backup accepted new identity without original header")
			}
		})
	}
}
