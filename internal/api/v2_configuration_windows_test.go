//go:build windows

package api_test

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"

	localworkspace "researchos.local/research-os/adapters/local_workspace"
	"researchos.local/research-os/internal/api"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/host"
	"researchos.local/research-os/internal/store"
)

// Actual temporary local Host/SID and authenticated loopback HTTP. Native
// chooser callback is deterministic; no provider, worker or user vault exists.
func TestConfigurationActualWindowsHostOfflineHTTP(t *testing.T) {
	ctx := context.Background()
	base := t.TempDir()
	db, e := store.Open(filepath.Join(base, "data", "researchos.sqlite"))
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	defer func() {
		if root := os.Getenv("RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR"); root != "" {
			dir := filepath.Join(root, t.Name())
			if e := os.MkdirAll(dir, 0700); e != nil {
				t.Error(e)
				return
			}
			path := filepath.Join(dir, "public-host.sqlite")
			if _, e := os.Stat(path); !os.IsNotExist(e) {
				t.Error("snapshot path already exists", e)
				return
			}
			if _, e := db.Exec("VACUUM INTO '" + strings.ReplaceAll(path, "'", "''") + "'"); e != nil {
				t.Error(e)
				return
			}
			raw, e := os.ReadFile(path)
			if e != nil {
				t.Error(e)
				return
			}
			t.Logf("CONFIGURATION_SQLITE_SNAPSHOT path=%s sha256=%s closed_snapshot=true fixture_only=true", path, domain.Digest(raw))
		}
	}()

	if e = store.Bootstrap(ctx, db, "../../migrations/sqlite/0001_bootstrap.sql"); e != nil {
		t.Fatal(e)
	}
	svc, e := domain.New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if e != nil {
		t.Fatal(e)
	}
	migration, e := os.ReadFile("../../migrations/sqlite/next_v24_sessions.sql")
	if e != nil {
		t.Fatal(e)
	}
	if _, e = db.Exec(string(migration)); e != nil {
		t.Fatal(e)
	}
	if e = domain.EnsureClientSessionFence(ctx, db); e != nil {
		t.Fatal(e)
	}
	h, e := host.New(host.Config{DB: db, Dir: filepath.Join(base, "private-host"), ContractsDir: "../../spec/v2.0/contracts", MigrationFile: "../../migrations/sqlite/0002_domain.sql", SchemaDir: "../../internal/api/contracts"})
	if e != nil {
		t.Fatal(e)
	}
	owner, e := h.BootstrapOwner(ctx)
	if e != nil {
		t.Fatal(e)
	}
	server := httptest.NewServer(api.HandlerWithConfigurationHost(db, t.TempDir(), svc, nil, h.InstanceID(), localworkspace.NewAuthority(h), localworkspace.NewScanner(), h, h))
	defer server.Close()
	chosen := filepath.Join(base, "chosen")
	if e = os.Mkdir(chosen, 0700); e != nil {
		t.Fatal(e)
	}
	f := &workspaceHTTPFixture{t: t, db: db, host: h, server: server, token: owner.Session.Token, client: "configuration-real-host", root: chosen}
	status := f.complete(f.command("host.status", "status-empty", nil, nil, nil, nil, domain.Object{}))
	principal, ok := status["authenticated_principal_ref"].(string)
	if !ok || strings.HasPrefix(principal, "principal:") || status["host_instance_id"] != h.InstanceID() {
		t.Fatal("actual status identity differs")
	}
	if len(status["model_configurations"].([]any)) != 0 {
		t.Fatal("empty Host invented configuration")
	}
	payload := domain.Object{"config_revision": 1, "provider_id": "fixture-provider", "base_url": "https://fixture.invalid/v1/", "model_id": "fixture-model", "credential_ref": nil}
	configured := f.complete(f.command("host.configure", "save-default", nil, nil, nil, nil, payload))
	if configured["verified_at"] != nil || configured["base_url"] != payload["base_url"] {
		t.Fatal("offline configuration claimed verification or rewrote URL")
	}
	f.ref = f.register(chosen)
	registeredStatus := f.complete(f.command("host.status", "status-registered", nil, nil, nil, nil, domain.Object{}))
	registered := registeredStatus["workspaces"].([]any)
	if len(registered) != 1 || registered[0].(map[string]any)["authorized_workspace_ref"] != f.ref || registered[0].(map[string]any)["revision"] != float64(1) {
		t.Fatalf("fresh status did not project registered workspace: %v", registered)
	}
	registeredList := f.complete(f.command("workspace.list", "list-registered", nil, nil, nil, nil, domain.Object{}))
	if !reflect.DeepEqual(registeredList["items"], registered) {
		t.Fatalf("registered list differed from status: %v", registeredList)
	}
	project := f.complete(f.command("project.bootstrap", "bootstrap", nil, nil, nil, nil, domain.Object{"authorized_workspace_ref": f.ref, "display_name": "Temporary offline configuration"}))
	f.project = project["project_id"].(string)
	statusAfterBootstrap := f.complete(f.command("host.status", "status-bootstrap", nil, nil, nil, nil, domain.Object{}))
	listed := f.complete(f.command("workspace.list", "list-bootstrap", nil, nil, nil, nil, domain.Object{}))
	workspaces := statusAfterBootstrap["workspaces"].([]any)
	items := listed["items"].([]any)
	if len(workspaces) != 1 || !reflect.DeepEqual(workspaces, items) {
		t.Fatalf("fresh host status and workspace list differ: %v / %v", workspaces, items)
	}
	visible := workspaces[0].(map[string]any)
	if len(visible) != 7 || visible["authorized_workspace_ref"] != f.ref || visible["project_id"] != f.project || visible["revision"] != float64(2) || visible["status"] != "ACTIVE" {
		t.Fatalf("project binding projection differs: %v", visible)
	}
	projectList := f.complete(f.command("workspace.list", "list-project", &f.project, nil, nil, nil, domain.Object{}))
	if !reflect.DeepEqual(projectList["items"], items) {
		t.Fatalf("project filter changed eligible metadata: %v", projectList)
	}
	if !reflect.DeepEqual(f.complete(f.command("host.status", "status-registered", nil, nil, nil, nil, domain.Object{}))["workspaces"], registered) ||
		!reflect.DeepEqual(f.complete(f.command("workspace.list", "list-registered", nil, nil, nil, nil, domain.Object{}))["items"], registered) ||
		len(f.complete(f.command("host.status", "status-empty", nil, nil, nil, nil, domain.Object{}))["workspaces"].([]any)) != 0 {
		t.Fatal("original read replay was rewritten by fresh bindings")
	}
	foreignProject := "not-granted"
	for _, refusal := range []domain.Object{
		f.command("workspace.list", "list-foreign-project", &foreignProject, nil, nil, nil, domain.Object{}),
		f.command("workspace.list", "list-session-claim", nil, &foreignProject, nil, nil, domain.Object{}),
		f.command("workspace.list", "list-revision-claim", nil, nil, 1, nil, domain.Object{}),
		f.command("host.status", "status-writer-claim", nil, nil, nil, 1, domain.Object{}),
		f.command("workspace.list", "list-payload", nil, nil, nil, nil, domain.Object{"unexpected": true}),
	} {
		if refusal["status"] != "REJECTED" {
			t.Fatalf("invalid metadata scope accepted: %v", refusal)
		}
	}
	visibleRef := visible["authorized_workspace_ref"].(string)
	created := f.complete(f.command("session.create", "create-offline", &f.project, nil, nil, nil, domain.Object{"workspace_ref": visibleRef, "model_config_ref": configured["model_config_ref"], "title": "offline"}))
	f.session = created["session_id"].(string)
	if created["run_id"] != nil || created["task_id"] != nil {
		t.Fatal("offline creation executed work")
	}
	sent := f.command("session.send", "send-unqualified", &f.project, &f.session, 1, 1, domain.Object{"text": "Do not execute without qualification", "attachment_artifact_ids": domain.Empty(), "delivery": "NORMAL"})
	if sent["status"] != "REJECTED" {
		t.Fatal("nil runtime accepted execution")
	}
	var tasks, runs, effects int
	db.QueryRow(`SELECT count(*) FROM domain_objects WHERE kind='Task'`).Scan(&tasks)
	db.QueryRow(`SELECT count(*) FROM domain_objects WHERE kind='Run'`).Scan(&runs)
	db.QueryRow(`SELECT count(*) FROM resource_effects`).Scan(&effects)
	if tasks != 0 || runs != 0 || effects != 0 {
		t.Fatalf("offline paths executed %d/%d/%d", tasks, runs, effects)
	}
	// Private journal bytes must never be forwarded as HTTP headers or body.
	env := domain.Object{"protocol_version": domain.ProtocolV2, "command_id": "save-default", "client_id": f.client, "project_id": nil, "session_id": nil, "expected_revision": nil, "writer_epoch": nil, "method": "host.configure", "payload": payload}
	request, _ := http.NewRequest(http.MethodPost, server.URL+"/v2/command", bytes.NewReader(domain.Bytes(env)))
	request.Header.Set("Authorization", "Bearer "+f.token)
	request.Header.Set("Content-Type", "application/json")
	response, e := server.Client().Do(request)
	if e != nil {
		t.Fatal(e)
	}
	raw, e := io.ReadAll(response.Body)
	response.Body.Close()
	if e != nil {
		t.Fatal(e)
	}
	for key, values := range response.Header {
		if strings.Contains(strings.ToLower(key), "envelope") || strings.Contains(strings.Join(values, ""), "raw_envelope_base64") {
			t.Fatal("private header forwarded")
		}
	}
	if bytes.Contains(raw, []byte("raw_envelope_base64")) {
		t.Fatal("private envelope leaked")
	}
	var replay domain.Object
	if e = json.Unmarshal(raw, &replay); e != nil || replay["status"] != "COMPLETED" {
		t.Fatal("exact replay failed", e)
	}
	var headers string
	if e = db.QueryRow(`SELECT headers FROM idempotency WHERE principal=? AND key='save-default'`, principal).Scan(&headers); e != nil || !strings.Contains(headers, "raw_envelope_base64") {
		t.Fatal("original private proof missing", e)
	}
	meta, e := h.ConfigurationMetadata(ctx, principal, "", nil)
	if e != nil || meta.OwnerHost != h.InstanceID() {
		t.Fatal("same Host composition differs", e)
	}
}
