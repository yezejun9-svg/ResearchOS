//go:build windows

package main

import (
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"

	localworkspace "researchos.local/research-os/adapters/local_workspace"
	"researchos.local/research-os/internal/api"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/host"
	"researchos.local/research-os/internal/store"
)

// Real temporary Host/SID, public configuration journal and offline Session.
// The busy Task is produced through the public command and an explicitly
// synthetic refusing runtime port. No model, worker, user vault or probe runs.
func TestCLIModelConfigurationActualWindowsHost(t *testing.T) {
	ctx := context.Background()
	base := t.TempDir()
	db, e := store.Open(filepath.Join(base, "data", "researchos.sqlite"))
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	dir := configurationCLIEvidence(t)
	defer func() {
		path := filepath.Join(dir, "public-host.sqlite")
		if _, e := db.Exec("VACUUM INTO '" + strings.ReplaceAll(path, "'", "''") + "'"); e != nil {
			t.Error(e)
			return
		}
		raw, e := os.ReadFile(path)
		if e != nil {
			t.Error(e)
			return
		}
		t.Logf("CONFIGURE_HOST_CLOSED_DB path=%s sha256=%s", path, domain.Digest(raw))
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
	h, e := host.New(host.Config{DB: db, Dir: filepath.Join(base, "host"), ContractsDir: "../../spec/v2.0/contracts", MigrationFile: "../../migrations/sqlite/0002_domain.sql", SchemaDir: "../../internal/api/contracts"})
	if e != nil {
		t.Fatal(e)
	}
	owner, e := h.BootstrapOwner(ctx)
	if e != nil {
		t.Fatal(e)
	}
	var model string
	handler := api.HandlerWithConfigurationHost(db, t.TempDir(), svc, cliSessionBindingFixture{configuredRef: &model}, h.InstanceID(), localworkspace.NewAuthority(h), localworkspace.NewScanner(), h, h)
	server := httptest.NewServer(handler)
	defer server.Close()
	disc := doctorDiscovery(t, server.URL, base)
	config := filepath.Join(base, "config.json")
	exe := configurationCLIBinary(t)
	call := func(method, key string, project, session any, revision, epoch any, payload domain.Object) (domain.Object, []byte) {
		t.Helper()
		env := domain.Object{"protocol_version": clientProtocol, "command_id": key, "client_id": "configuration-cli", "project_id": project, "session_id": session, "expected_revision": revision, "writer_epoch": epoch, "method": method, "payload": payload}
		raw := domain.Bytes(env)
		req, e := http.NewRequest("POST", server.URL+v2CommandPath, bytes.NewReader(raw))
		if e != nil {
			t.Fatal(e)
		}
		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("Authorization", "Bearer "+owner.Session.Token)
		resp, e := server.Client().Do(req)
		if e != nil {
			t.Fatal(e)
		}
		body, e := io.ReadAll(resp.Body)
		resp.Body.Close()
		if e != nil {
			t.Fatal(e)
		}
		var reply domain.Object
		if e = json.Unmarshal(body, &reply); e != nil {
			t.Fatal(e)
		}
		id := domain.ID()
		configurationCLIWrite(t, dir, id+".request.json", raw)
		configurationCLIWrite(t, dir, id+".response.json", body)
		return reply, body
	}
	completed := func(reply domain.Object) domain.Object {
		t.Helper()
		if reply["status"] != "COMPLETED" {
			t.Fatalf("public operation: %s", domain.Bytes(reply))
		}
		return reply["result"].(map[string]any)
	}
	out, code := configurationCLIRun(t, exe, disc, config, owner.Session.Token, "config", "set-model", "--model", "fixture-provider/fixture-model", "--base-url", "https://fixture.invalid/v1", "--config-revision", "0")
	if code != 0 {
		t.Fatalf("actual default: %v", out)
	}
	model = out["model"].(string)
	workspace := filepath.Join(base, "workspace")
	if e = os.Mkdir(workspace, 0700); e != nil {
		t.Fatal(e)
	}
	if e = os.WriteFile(filepath.Join(workspace, "README.md"), []byte("# Owned public finite fixture\n"), 0600); e != nil {
		t.Fatal(e)
	}
	selected, e := h.HandleNative(domain.Bytes(domain.Object{"kind": host.KindWorkspaceChooseRequest, "client_id": "configuration-cli", "payload": domain.Object{"requested_path": workspace, "requested_access": host.AccessReadWrite}}), true, func(string) (string, error) { return workspace, nil })
	if e != nil {
		t.Fatal(e)
	}
	var native domain.Object
	if e = json.Unmarshal(selected, &native); e != nil {
		t.Fatal(e)
	}
	selection := native["payload"].(map[string]any)["selection_ref"]
	reply, _ := call("workspace.register", domain.ID(), nil, nil, nil, nil, domain.Object{"selection_ref": selection, "display_name": "owned fixture", "requested_access": host.AccessReadWrite})
	ref := completed(reply)["authorized_workspace_ref"]
	reply, _ = call("project.bootstrap", domain.ID(), nil, nil, nil, nil, domain.Object{"authorized_workspace_ref": ref, "display_name": "CLI configuration integration"})
	project := completed(reply)["project_id"].(string)
	raw, e := os.ReadFile(config)
	if e != nil {
		t.Fatal(e)
	}
	var cfg cliConfig
	if e = json.Unmarshal(raw, &cfg); e != nil {
		t.Fatal(e)
	}
	cfg.ProjectID = project
	cfg.WorkspaceRef = ref.(string)
	if e = os.WriteFile(config, domain.Bytes(cfg), 0600); e != nil {
		t.Fatal(e)
	}
	// Compiled CLI consumes the exact saved opaque ref. Its synthetic runtime
	// refuses execution, leaving the real Task BLOCKED and no Run/effect.
	_, code = configurationCLIRun(t, exe, disc, config, owner.Session.Token, "run", "Do not run any provider")
	if code == 0 {
		t.Fatal("synthetic runtime refusal reported execution completion")
	}
	var sid, storedModel, task string
	var revision, epoch int64
	if e = db.QueryRow(`SELECT id,model_ref,task_id,revision,writer_epoch FROM client_sessions WHERE project=?`, project).Scan(&sid, &storedModel, &task, &revision, &epoch); e != nil {
		t.Fatal(e)
	}
	if storedModel != model || task == "" {
		t.Fatal("compiled Session did not preserve configured reference/real blocked Task")
	}
	cfg.SessionID = sid
	cfg.Revision = revision
	cfg.WriterEpoch = epoch
	cfg.ConfirmedRun = "caller-only-claim"
	if e = os.WriteFile(config, domain.Bytes(cfg), 0600); e != nil {
		t.Fatal(e)
	}
	before, _ := os.ReadFile(config)
	out, code = configurationCLIRun(t, exe, disc, config, owner.Session.Token, "config", "set-model", "--model", "fixture-provider/other", "--base-url", "https://fixture.invalid/v1", "--config-revision", "1", "--settled")
	after, _ := os.ReadFile(config)
	if code != 1 || out["reason"] != "HOST_REJECTED:SESSION_BUSY" || !bytes.Equal(before, after) {
		t.Fatalf("actual busy ignored: %v %d", out, code)
	}
	// Explicit default must not rebind this busy existing Session.
	out, code = configurationCLIRun(t, exe, disc, config, owner.Session.Token, "config", "set-model", "--default", "--model", "fixture-provider/future", "--base-url", "https://fixture.invalid/v1", "--config-revision", "1")
	if code != 0 {
		t.Fatal("default blocked by unrelated Session", out)
	}
	var old string
	if e = db.QueryRow(`SELECT model_ref FROM client_sessions WHERE id=?`, sid).Scan(&old); e != nil || old != model {
		t.Fatal("default rebound existing Session", e)
	}
	cancelKey := domain.ID()
	cancelPayload := domain.Object{"action": "CANCEL", "target_id": task, "reason": "owned noRun fixture settlement"}
	reply, first := call("session.control", cancelKey, project, sid, revision, epoch, cancelPayload)
	completed(reply)
	_, replay := call("session.control", cancelKey, project, sid, revision, epoch, cancelPayload)
	if !bytes.Equal(first, replay) {
		t.Fatal("original cancellation replay changed bytes")
	}
	if e = db.QueryRow(`SELECT revision FROM client_sessions WHERE id=?`, sid).Scan(&revision); e != nil {
		t.Fatal(e)
	}
	raw, _ = os.ReadFile(config)
	json.Unmarshal(raw, &cfg)
	cfg.Revision = revision
	if e = os.WriteFile(config, domain.Bytes(cfg), 0600); e != nil {
		t.Fatal(e)
	}
	out, code = configurationCLIRun(t, exe, disc, config, owner.Session.Token, "config", "set-model", "--model", "fixture-provider/settled", "--base-url", "https://fixture.invalid/v1", "--config-revision", "2", "--settled")
	if code != 0 {
		t.Fatal("actual settled rebind", out)
	}
	if e = db.QueryRow(`SELECT model_ref FROM client_sessions WHERE id=?`, sid).Scan(&old); e != nil || old != out["model"] {
		t.Fatal("scoped configuration not bound", e)
	}
	var runs, effects int
	db.QueryRow(`SELECT count(*) FROM domain_objects WHERE kind='Run'`).Scan(&runs)
	db.QueryRow(`SELECT count(*) FROM resource_effects`).Scan(&effects)
	if runs != 0 || effects != 0 {
		t.Fatal("configuration fixture executed resource", runs, effects)
	}
	var command, body string
	if e = db.QueryRow(`SELECT key,body FROM idempotency WHERE operation='v2:host.configure' AND json_extract(body,'$.status')='COMPLETED' ORDER BY created_at DESC LIMIT 1`).Scan(&command, &body); e != nil {
		t.Fatal(e)
	}
	var headers string
	if e = db.QueryRow(`SELECT headers FROM idempotency WHERE key=?`, command).Scan(&headers); e != nil || !strings.Contains(headers, "raw_envelope_base64") {
		t.Fatal("original private journal proof absent", e)
	}
	var private domain.Object
	if e = json.Unmarshal([]byte(headers), &private); e != nil {
		t.Fatal(e)
	}
	original, e := base64.StdEncoding.DecodeString(private["raw_envelope_base64"].(string))
	if e != nil {
		t.Fatal(e)
	}
	for _, changed := range []bool{false, true} {
		requestRaw := original
		if changed {
			var value domain.Object
			if e = json.Unmarshal(original, &value); e != nil {
				t.Fatal(e)
			}
			value["payload"].(map[string]any)["model_id"] = "conflicting-original-command"
			requestRaw = domain.Bytes(value)
		}
		request, e := http.NewRequest("POST", server.URL+v2CommandPath, bytes.NewReader(requestRaw))
		if e != nil {
			t.Fatal(e)
		}
		request.Header.Set("Authorization", "Bearer "+owner.Session.Token)
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
		id := domain.ID()
		configurationCLIWrite(t, dir, id+".configure-replay.request.json", requestRaw)
		configurationCLIWrite(t, dir, id+".configure-replay.response.json", raw)
		if !changed && !bytes.Equal(raw, []byte(body)) {
			t.Fatal("configure replay changed original bytes")
		}
		if changed && response.StatusCode != 409 {
			t.Fatalf("changed original configure accepted: %d", response.StatusCode)
		}
	}
	t.Logf("CONFIGURE_ACTUAL_HOST instance=%s configuration_ref=%s task=%s runs=%d effects=%d sdk_calls=0 external_calls=0 paid_calls=0", h.InstanceID(), old, task, runs, effects)
}
