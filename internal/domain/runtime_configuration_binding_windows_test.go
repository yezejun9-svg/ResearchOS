//go:build windows

package domain

import (
	"bytes"
	"context"
	"crypto/x509"
	"database/sql"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"researchos.local/research-os/internal/store"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

func TestHandlerRuntimeStoredProfileExactMapping(t *testing.T) {
	f := contextFixture(t)
	s := &ClientService{Doc: configurationSchema(t), Domain: f.s, ConfigurationAuthority: handlerMetadataFixture{f.owner}}
	credential := "cred-fixture-api_key-1234567890-12345678-12345678"
	env := handlerDefaultEnvelope(1)
	env.Payload = Bytes(Object{"config_revision": 1, "provider_id": "fixture-provider", "base_url": "https://fixture.invalid/v1/", "model_id": "fixture-model", "credential_ref": credential})
	r, _ := handlerCommand(t, f, s, env)
	if deref(r.Status) != "COMPLETED" {
		t.Fatal(string(Bytes(r)))
	}
	ref := Str(r.Result, "model_config_ref")
	config := modelFixtureConfig("https://fixture.invalid/v1/chat/completions")
	config["ref"] = ref
	config["provider"] = "fixture-provider"
	profile := Object{"model_config": config}
	runtime := Object{"id": "runtime-fixture"}
	route := RuntimeProviderRoute{ID: Str(config, "route"), ProjectID: f.project, RuntimeID: "runtime-fixture", Purpose: "mu_turn", Capability: "MODEL", Endpoint: Str(config, "endpoint"), CredentialRef: credential, CredentialRevision: credential, ModelConfig: config}
	c := &RuntimeCoordinator{service: f.s, config: RuntimeCoordinatorConfig{ClientSchema: s.Doc, ConfigurationAuthority: s.ConfigurationAuthority, Providers: []RuntimeProviderRoute{route}}}
	check := func(profile Object) error {
		tx, e := f.db.Begin()
		if e != nil {
			t.Fatal(e)
		}
		defer tx.Rollback()
		return c.matchStoredClientConfiguration(tx, f.project, ref, runtime, profile)
	}
	if e := check(profile); e != nil {
		t.Fatal(e)
	}
	for _, field := range []string{"ref", "api", "provider", "model", "endpoint", "route"} {
		t.Run("profile-"+field, func(t *testing.T) {
			bad := cloneObject(config)
			bad[field] = "different"
			if e := check(Object{"model_config": bad}); e == nil {
				t.Fatal("different profile accepted")
			}
		})
	}
	for _, field := range []string{"credential-ref", "credential-revision", "endpoint", "model-hash", "project", "runtime", "capability"} {
		t.Run("route-"+field, func(t *testing.T) {
			bad := route
			switch field {
			case "credential-ref":
				bad.CredentialRef = "different"
			case "credential-revision":
				bad.CredentialRevision = "different"
			case "endpoint":
				bad.Endpoint = "https://different.invalid"
			case "model-hash":
				bad.ModelConfig = cloneObject(config)
				bad.ModelConfig["model"] = "different"
			case "project":
				bad.ProjectID = "different"
			case "runtime":
				bad.RuntimeID = "different"
			case "capability":
				bad.Capability = "TOOL"
			}
			c.config.Providers = []RuntimeProviderRoute{bad}
			if e := check(profile); e == nil {
				t.Fatal("different route accepted")
			}
			c.config.Providers = []RuntimeProviderRoute{route}
		})
	}
	c.config.Providers = []RuntimeProviderRoute{route, route}
	if e := check(profile); e == nil {
		t.Fatal("duplicate MODEL routes accepted")
	}
	c.config.Providers = []RuntimeProviderRoute{route}
	c.config.ConfigurationAuthority = nil
	if e := check(profile); e == nil {
		t.Fatal("missing authority accepted")
	}
	c.config.ConfigurationAuthority = s.ConfigurationAuthority
	configurationBackupMutation(t, f.db, `DELETE FROM host_model_configurations WHERE model_config_ref=?`, ref)
	if e := check(profile); e == nil {
		t.Fatal("known typed config fell back to legacy after row deletion")
	}
	var effects int
	if e := f.db.QueryRow(`SELECT count(*) FROM resource_effects`).Scan(&effects); e != nil || effects != 0 {
		t.Fatalf("mapping check caused effects=%d %v", effects, e)
	}
}

func TestHandlerRuntimeStoredLocalProfileExactMapping(t *testing.T) {
	f := contextFixture(t)
	s := &ClientService{Doc: configurationSchema(t), Domain: f.s, ConfigurationAuthority: handlerMetadataFixture{f.owner}}
	env := handlerDefaultEnvelope(1)
	env.Payload = Bytes(Object{"config_revision": 1, "provider_id": "ollama", "base_url": "http://127.0.0.1:11434/v1", "model_id": "qwen3:4b-instruct", "credential_ref": nil})
	saved, _ := handlerCommand(t, f, s, env)
	if deref(saved.Status) != "COMPLETED" {
		t.Fatal(string(Bytes(saved)))
	}
	ref := Str(saved.Result, "model_config_ref")
	config := modelFixtureConfig("http://127.0.0.1:11434/v1/chat/completions")
	config["ref"], config["provider"], config["model"] = ref, "ollama", "qwen3:4b-instruct"
	profile := Object{"model_config": config, "credential_revision": "none"}
	runtime := Object{"id": "runtime-local"}
	route := RuntimeProviderRoute{ID: Str(config, "route"), ProjectID: f.project, RuntimeID: "runtime-local", Purpose: "mu_turn", Capability: "MODEL", Endpoint: Str(config, "endpoint"), CredentialRevision: "none", ModelConfig: config}
	c := &RuntimeCoordinator{service: f.s, config: RuntimeCoordinatorConfig{ClientSchema: s.Doc, ConfigurationAuthority: s.ConfigurationAuthority, Providers: []RuntimeProviderRoute{route}}}
	check := func() error {
		tx, err := f.db.Begin()
		if err != nil {
			t.Fatal(err)
		}
		defer tx.Rollback()
		return c.matchStoredClientConfiguration(tx, f.project, ref, runtime, profile)
	}
	if err := check(); err != nil {
		t.Fatal(err)
	}
	for _, mutate := range []func(){
		func() { c.config.Providers[0].CredentialRef = "fake" },
		func() { c.config.Providers[0].CredentialRevision = "fake" },
		func() { c.config.Providers[0].BearerToken = "secret" },
		func() { c.config.Providers[0].Endpoint = "http://127.0.0.1:11435/v1/chat/completions" },
	} {
		c.config.Providers[0] = route
		mutate()
		if err := check(); err == nil {
			t.Fatal("unbound or credentialed local route accepted")
		}
	}
	c.config.Providers[0] = route
	profile["credential_revision"] = "fake"
	if err := check(); err == nil {
		t.Fatal("fake profile credential revision accepted")
	}
}

func TestLiveModelCredentialBoundary(t *testing.T) {
	c := &RuntimeCoordinator{config: RuntimeCoordinatorConfig{ModelCredential: func(context.Context, RuntimeProviderRoute) ([]byte, error) { return nil, nil }}}
	profile := Object{"credential_revision": "none"}
	local := RuntimeProviderRoute{Capability: "MODEL", Endpoint: "http://127.0.0.1:11434/v1/chat/completions", MeasurementMode: "LIVE", CredentialRevision: "none"}
	if !c.liveModelCredentialBound(local, profile) {
		t.Fatal("credential-free local LIVE route rejected")
	}
	if !providerEndpointAllowed(local) {
		t.Fatal("strict local LIVE endpoint rejected")
	}
	for _, change := range []func(*RuntimeProviderRoute){
		func(p *RuntimeProviderRoute) { p.CredentialRef = "cred-fake" },
		func(p *RuntimeProviderRoute) { p.CredentialRevision = "cred-fake" },
		func(p *RuntimeProviderRoute) { p.BearerToken = "inherited-secret" },
		func(p *RuntimeProviderRoute) { p.Endpoint = "http://localhost:11434/v1/chat/completions" },
		func(p *RuntimeProviderRoute) { p.Endpoint = "http://192.168.1.1:11434/v1/chat/completions" },
	} {
		bad := local
		change(&bad)
		if c.liveModelCredentialBound(bad, profile) && providerEndpointAllowed(bad) {
			t.Fatal("credentialed or unbound local LIVE route accepted")
		}
	}
	for _, endpoint := range []string{"http://localhost:11434/v1/chat/completions", "http://192.168.1.1:11434/v1/chat/completions", "http://0.0.0.0:11434/v1/chat/completions", "http://127.1:11434/v1/chat/completions", "http://user@127.0.0.1:11434/v1/chat/completions", "http://127.0.0.1:11434/v1/chat/completions?x=1"} {
		bad := local
		bad.Endpoint = endpoint
		if providerEndpointAllowed(bad) {
			t.Errorf("unbound LIVE endpoint accepted: %s", endpoint)
		}
	}
	profile["credential_revision"] = "other"
	if c.liveModelCredentialBound(local, profile) {
		t.Fatal("profile revision mismatch accepted")
	}
	remote := RuntimeProviderRoute{Capability: "MODEL", Endpoint: "https://fixture.invalid/v1/chat/completions", MeasurementMode: "LIVE", CredentialRef: "cred-live", CredentialRevision: "cred-live"}
	if !c.liveModelCredentialBound(remote, profile) {
		t.Fatal("existing protected HTTPS LIVE route rejected")
	}
	if !providerEndpointAllowed(remote) {
		t.Fatal("existing HTTPS LIVE endpoint rejected")
	}
	remote.CredentialRef = ""
	if c.liveModelCredentialBound(remote, profile) {
		t.Fatal("unprotected HTTPS LIVE route accepted")
	}
}

func cloneObject(in Object) Object { out, _ := Decode(Bytes(in)); return out }

func TestHandlerRuntimeTaskNeedsExactSession(t *testing.T) {
	f := contextFixture(t)
	s, _, _ := handlerTypedSession(t, f, "config-client")
	c := &RuntimeCoordinator{service: f.s, config: RuntimeCoordinatorConfig{ClientSchema: s.Doc, ConfigurationAuthority: s.ConfigurationAuthority}}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		if e := c.validateTaskSessionConfiguration(context.Background(), tx, f.project, Object{"id": "unassociated"}); e == nil {
			t.Fatal("unassociated task accepted")
		}
		return nil
	})
}

func TestHandlerPendingOriginalTranscript(t *testing.T) {
	f := contextFixture(t)
	doc, sid := transcriptSession(t, f, 70)
	s, env := transcriptSend(t, f, doc, sid)
	var workspace, model string
	if e := f.db.QueryRow(`SELECT workspace_ref,model_config_ref FROM client_sessions WHERE id=?`, sid).Scan(&workspace, &model); e != nil {
		t.Fatal(e)
	}
	p := &handlerPendingPort{t: t, s: s, workspace: workspace, model: model}
	s.SessionRuntime = p
	r, _ := handlerCommand(t, f, s, env)
	if deref(r.Status) != "COMPLETED" || p.calls != 1 || p.proofErr != nil {
		t.Fatalf("pending history proof: %s calls=%d err=%v", Bytes(r), p.calls, p.proofErr)
	}
	configurationEvidenceSnapshot(t, f.db, "handler-pending-original-transcript")
}

var handlerTLSRootsOnce sync.Once

// Execute only in its own explicitly configured process. This is local TLS and
// actual SDK evidence; the metadata/credential ports are synthetic fixtures.
func TestHandlerTLSActualSDKConfiguredSession(t *testing.T) {
	if os.Getenv("RESEARCHOS_HANDLER_TLS_CHILD") != t.Name() {
		exe, e := os.Executable()
		if e != nil {
			t.Fatal(e)
		}
		command := exec.Command(exe, "-test.run=^TestHandlerTLSActualSDKConfiguredSession$", "-test.v", "-test.timeout=180s")
		debug := []string{}
		for _, entry := range strings.Split(os.Getenv("GODEBUG"), ",") {
			if entry != "" && !strings.HasPrefix(entry, "x509usefallbackroots=") {
				debug = append(debug, entry)
			}
		}
		for _, entry := range os.Environ() {
			if !strings.HasPrefix(entry, "GODEBUG=") && !strings.HasPrefix(entry, "RESEARCHOS_HANDLER_TLS_CHILD=") {
				command.Env = append(command.Env, entry)
			}
		}
		command.Env = append(command.Env, "GODEBUG="+strings.Join(append(debug, "x509usefallbackroots=1"), ","), "RESEARCHOS_HANDLER_TLS_CHILD="+t.Name())
		var stdout, stderr bytes.Buffer
		command.Stdout = &stdout
		command.Stderr = &stderr
		started := time.Now().UTC()
		e = command.Run()
		exit := 0
		if e != nil {
			exit = -1
			if status, ok := e.(*exec.ExitError); ok {
				exit = status.ExitCode()
			}
		}
		if evidence := os.Getenv("RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR"); evidence != "" {
			dir := filepath.Join(evidence, t.Name(), "tls-child")
			if err := os.MkdirAll(dir, 0700); err != nil {
				t.Fatal(err)
			}
			binary, err := os.ReadFile(exe)
			if err != nil {
				t.Fatal(err)
			}
			cwd, err := os.Getwd()
			if err != nil {
				t.Fatal(err)
			}
			files := map[string][]byte{"stdout.raw": stdout.Bytes(), "stderr.raw": stderr.Bytes(), "invocation.json": Bytes(Object{"actualargv": command.Args, "cwd": cwd, "started_at": started.Format(time.RFC3339Nano), "ended_at": time.Now().UTC().Format(time.RFC3339Nano), "exit": exit, "binary_sha256": Digest(binary), "case": t.Name(), "measurement_mode": "FIXTURE", "external_calls": 0, "paid_calls": 0})}
			for name, data := range files {
				f, err := os.OpenFile(filepath.Join(dir, name), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
				if err != nil {
					t.Fatal(err)
				}
				_, err = f.Write(data)
				closed := f.Close()
				if err != nil {
					t.Fatal(err)
				}
				if closed != nil {
					t.Fatal(closed)
				}
			}
		}
		raw := append(append([]byte{}, stdout.Bytes()...), stderr.Bytes()...)
		t.Logf("HANDLER_TLS_ISOLATED_CHILD argv=%q exit=%d output=%s", command.Args, exit, raw)
		if e != nil {
			t.Fatal(e)
		}
		if !bytes.Contains(raw, []byte("=== RUN   "+t.Name())) || !bytes.Contains(raw, []byte("--- PASS: "+t.Name())) {
			t.Fatal("exact TLS child did not execute its case")
		}
		return
	}
	exact := false
	for _, arg := range os.Args[1:] {
		if arg == "-test.run=^TestHandlerTLSActualSDKConfiguredSession$" {
			exact = true
		}
	}
	if !exact || !strings.Contains(os.Getenv("GODEBUG"), "x509usefallbackroots=1") {
		t.Fatal("TLS child requires exact isolated case and normal fallback trust")
	}
	f := contextFixture(t)
	var calls atomic.Int32
	ordinaryStarted, ordinaryRelease := make(chan struct{}), make(chan struct{})
	var releaseOnce sync.Once
	release := func() { releaseOnce.Do(func() { close(ordinaryRelease) }) }
	defer release()
	server := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/v1/chat/completions" {
			t.Errorf("unexpected local provider path %s", r.URL.Path)
			w.WriteHeader(400)
			return
		}
		if r.Header.Get("Authorization") != "Bearer handler-synthetic-model-token" {
			w.WriteHeader(403)
			return
		}
		var body Object
		if json.NewDecoder(r.Body).Decode(&body) != nil || body["model"] != "fixture-model" {
			w.WriteHeader(400)
			return
		}
		n := calls.Add(1)
		if n > 2 {
			t.Error("unexpected extra SDK request")
			w.WriteHeader(429)
			return
		}
		if n == 2 {
			close(ordinaryStarted)
			select {
			case <-ordinaryRelease:
			case <-r.Context().Done():
				return
			}
		}
		w.Header().Set("Content-Type", "text/event-stream")
		fmt.Fprint(w, "data: {\"id\":\"handler-tls-response\",\"object\":\"chat.completion.chunk\",\"created\":1,\"model\":\"fixture-model\",\"choices\":[{\"index\":0,\"delta\":{\"role\":\"assistant\",\"content\":\"bounded TLS fixture response\"},\"finish_reason\":null}]}\n\n")
		fmt.Fprint(w, "data: {\"choices\":[{\"index\":0,\"delta\":{},\"finish_reason\":\"stop\"}]}\n\ndata: [DONE]\n\n")
	}))
	defer func() { release(); server.Close() }()
	cert := server.Certificate()
	pool := x509.NewCertPool()
	pool.AddCert(cert)
	if _, e := cert.Verify(x509.VerifyOptions{Roots: x509.NewCertPool(), DNSName: "127.0.0.1"}); e == nil {
		t.Fatal("empty trust pool accepted certificate")
	}
	if _, e := cert.Verify(x509.VerifyOptions{Roots: pool, DNSName: "wrong.invalid"}); e == nil {
		t.Fatal("wrong hostname accepted")
	}
	handlerTLSRootsOnce.Do(func() { x509.SetFallbackRoots(pool) })
	t.Logf("HANDLER_TLS_FIXTURE cert_sha256=%s provider_scope=numeric-loopback paid_calls=0", Digest(cert.Raw))
	if evidence := os.Getenv("RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR"); evidence != "" {
		if e := os.MkdirAll(evidence, 0700); e != nil {
			t.Fatal(e)
		}
		file, e := os.OpenFile(filepath.Join(evidence, "handler-tls-public-cert.der"), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
		if e != nil {
			t.Fatal(e)
		}
		_, e = file.Write(cert.Raw)
		closeErr := file.Close()
		if e != nil {
			t.Fatal(e)
		}
		if closeErr != nil {
			t.Fatal(closeErr)
		}
	}
	credential := "cred-fixture-api_key-1234567890-12345678-12345678"
	s := &ClientService{Doc: configurationSchema(t), Domain: f.s, ConfigurationAuthority: handlerMetadataFixture{f.owner}, Host: ClientHostInfo{InstanceID: configurationFixtureOwner, CoreBuildID: "handler-tls", LeaseTTL: time.Hour}}
	configure := handlerDefaultEnvelope(1)
	configure.Payload = Bytes(Object{"config_revision": 1, "provider_id": "openai", "base_url": server.URL + "/v1", "model_id": "fixture-model", "credential_ref": credential})
	saved, _ := handlerCommand(t, f, s, configure)
	if deref(saved.Status) != "COMPLETED" {
		t.Fatal(string(Bytes(saved)))
	}
	config := modelFixtureConfig(server.URL + "/v1/chat/completions")
	config["ref"] = Str(saved.Result, "model_config_ref")
	node, bundle := os.Getenv("RESEARCHOS_NODE"), os.Getenv("RESEARCHOS_MU_BUNDLE")
	if node == "" || bundle == "" {
		t.Fatal("explicit pinned Node and SDK bundle required")
	}
	actualNode, e := filepath.EvalSymlinks(node)
	if e != nil {
		t.Fatal(e)
	}
	requestedNode, e := os.ReadFile(node)
	if e != nil {
		t.Fatal(e)
	}
	node = actualNode
	binary, e := os.ReadFile(node)
	if e != nil {
		t.Fatal(e)
	}
	if Digest(binary) != Digest(requestedNode) {
		t.Fatal("Node alias differs from resolved pinned executable")
	}
	t.Logf("HANDLER_NODE_IDENTITY actual_path=%s sha256=%s", node, Digest(binary))
	bundleRaw, e := os.ReadFile(bundle)
	if e != nil {
		t.Fatal(e)
	}
	c, route, r := handlerTLSCoordinatorFixture(t, f, func(profile Object) (string, string) {
		profile["backend"], profile["model"], profile["model_config"] = runtimeMuBackend, config["model"], config
		profile["build_hash"], profile["bundle_hash"] = Digest(binary), Digest(bundleRaw)
		profile["argv"] = []any{"--preserve-symlinks-main", "--preserve-symlinks", "{bundle}", "{manifest}"}
		profile["effect_routes"] = []any{Object{"id": config["route"], "capability": "MODEL", "credential_revision": credential, "upper_bound": dollars("1")}}
		profile["model_qualification"] = Object{"route": config["route"], "model_config_hash": Hash(config), "max_calls": 1}
		profile["timeout_seconds"] = 60
		return node, bundle
	})
	c.config.ClientSchema = s.Doc
	c.config.ConfigurationAuthority = s.ConfigurationAuthority
	c.config.ModelCredential = func(_ context.Context, p RuntimeProviderRoute) ([]byte, error) {
		if p.CredentialRef != credential || p.CredentialRevision != credential {
			return nil, fmt.Errorf("synthetic credential mismatch")
		}
		return []byte("handler-synthetic-model-token"), nil
	}
	provider := RuntimeProviderRoute{ID: Str(config, "route"), ProjectID: f.project, RuntimeID: route.RuntimeID, Purpose: "runtime_qualification", Capability: "MODEL", CredentialRef: credential, CredentialRevision: credential, Endpoint: Str(config, "endpoint"), UpperBound: dollars("1"), MeasurementMode: "FIXTURE", ModelConfig: config}
	c.config.Providers = []RuntimeProviderRoute{provider}
	qualifyNativeCoordinator(t, c, route, r)
	if calls.Load() != 1 {
		t.Fatalf("qualification requests=%d", calls.Load())
	}
	workspace := t.TempDir()
	c.config.WorkspaceAuthority = muWorkspaceFixture{workspace}
	binding := WorkspaceBinding{AuthorizedRef: "handler-tls-workspace", DisplayName: "TLS fixture", DisplayPath: workspace, RealPath: workspace, Access: "READ_ONLY", ProjectID: &f.project, Revision: 1, Status: WorkspaceActive, PrincipalID: f.owner, ClientID: "tls-client", HostPrincipalRef: "EXPLICIT-SYNTHETIC-FIXTURE", CreatedAt: Now()}
	if _, e = f.db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('',?,?,1,?,0)`, KindWorkspaceBinding, binding.AuthorizedRef, string(Bytes(binding))); e != nil {
		t.Fatal(e)
	}
	provider.Purpose = "mu_turn"
	c.config.Providers = append(c.config.Providers, provider)
	if e = f.s.AuthorizeRuntimePurpose(context.Background(), r.ownerToken, f.project, route.RuntimeID, "mu_turn", time.Now().Add(30*time.Minute)); e != nil {
		t.Fatal(e)
	}
	route.ExecutorID = ID()
	if e = f.s.ProvisionPrincipal(context.Background(), Principal{ID: route.ExecutorID, Roles: []string{"EXECUTOR"}, Grants: []Grant{{ProjectID: f.project}}}); e != nil {
		t.Fatal(e)
	}
	route.ExecutorToken, e = f.s.IssueCredential(context.Background(), route.ExecutorID, 15*time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	c.config.Routes = []RuntimeCoordinatorRoute{route}
	r.executor = route.ExecutorID
	s.SessionRuntime = c
	created, _ := handlerCommand(t, f, s, &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("tls-client"), ProjectID: &f.project, Method: strptr("session.create"), Payload: Bytes(Object{"workspace_ref": binding.AuthorizedRef, "model_config_ref": config["ref"], "title": "typed TLS SDK"})})
	if deref(created.Status) != "COMPLETED" {
		t.Fatal(string(Bytes(created)))
	}
	result, _ := handlerCommand(t, f, s, &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("tls-client"), ProjectID: &f.project, SessionID: created.SessionID, ExpectedRevision: revPtr(1), WriterEpoch: revPtr(1), Method: strptr("session.send"), Payload: Bytes(Object{"text": "one bounded local response", "attachment_artifact_ids": Empty(), "delivery": "NORMAL"})})
	if deref(result.Status) != "COMPLETED" {
		t.Fatal(string(Bytes(result)))
	}
	if e = c.Scan(context.Background()); e != nil {
		t.Fatal(e)
	}
	select {
	case <-ordinaryStarted:
	case <-time.After(45 * time.Second):
		t.Fatal("ordinary SDK request did not reach the local causal barrier")
	}
	busy := queueClientEnvelope(t, f, "tls-client", deref(created.SessionID), "host.configure", Object{"config_revision": 2, "provider_id": "openai", "base_url": server.URL + "/v1", "model_id": "fixture-model", "credential_ref": credential})
	busyReply, _ := handlerCommand(t, f, s, busy)
	if deref(busyReply.Status) != "REJECTED" || deref(busyReply.ErrorCode) != "SESSION_BUSY" {
		t.Fatalf("active actual SDK Run was rebound: %s", Bytes(busyReply))
	}
	t.Log("C09_ACTUAL_ACTIVE_RUN rejected while the second local SDK request remained blocked")
	release()
	c.workers.Wait()
	select {
	case e := <-c.errors:
		t.Fatal(e)
	default:
	}
	var taskID string
	if e = f.db.QueryRow(`SELECT task_id FROM client_sessions WHERE id=?`, deref(created.SessionID)).Scan(&taskID); e != nil {
		t.Fatal(e)
	}
	task := f.read("tasks", taskID)
	if task["status"] != "EXECUTION_REPORTED" {
		t.Fatalf("ordinary typed turn not reported: %s", Bytes(task))
	}
	var deltas, ends int
	f.db.QueryRow(`SELECT count(*) FROM outbox WHERE project=? AND json_extract(body,'$.session_id')=? AND json_extract(body,'$.payload.role')='ASSISTANT' AND json_extract(body,'$.payload.phase')='DELTA'`, f.project, deref(created.SessionID)).Scan(&deltas)
	f.db.QueryRow(`SELECT count(*) FROM outbox WHERE project=? AND json_extract(body,'$.session_id')=? AND json_extract(body,'$.payload.role')='ASSISTANT' AND json_extract(body,'$.payload.phase')='END'`, f.project, deref(created.SessionID)).Scan(&ends)
	if calls.Load() != 2 || deltas < 1 || ends != 1 {
		t.Fatalf("SDK/durable journal mismatch calls=%d deltas=%d ends=%d", calls.Load(), deltas, ends)
	}
	oldRun := f.read("runs", Str(task, "active_run_id"))
	handlerSettledRunNegativeClones(t, f, s, deref(created.SessionID), oldRun, server.URL+"/v1", credential)
	oldRunHash := Hash(oldRun)
	var effectsBefore int
	f.db.QueryRow(`SELECT count(*) FROM resource_effects`).Scan(&effectsBefore)
	// Same settings, new immutable ref: the former qualified profile cannot
	// silently supply the new default's authority.
	configure.CommandID = strptr(ID())
	configure.Payload = Bytes(Object{"config_revision": 2, "provider_id": "openai", "base_url": server.URL + "/v1", "model_id": "fixture-model", "credential_ref": credential})
	second, _ := handlerCommand(t, f, s, configure)
	if deref(second.Status) != "COMPLETED" {
		t.Fatal(string(Bytes(second)))
	}
	tx, e := f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	_, _, bindingErr := c.ResolveGoalBinding(context.Background(), tx, f.owner, f.project, "tls-client")
	tx.Rollback()
	if bindingErr == nil {
		t.Fatal("new default silently reused old qualified profile")
	}
	var rev, epoch int64
	f.db.QueryRow(`SELECT revision,writer_epoch FROM client_sessions WHERE id=?`, deref(created.SessionID)).Scan(&rev, &epoch)
	configure.CommandID = strptr(ID())
	configure.ClientID = strptr("tls-client")
	configure.ProjectID = &f.project
	configure.SessionID = created.SessionID
	configure.ExpectedRevision = &rev
	configure.WriterEpoch = &epoch
	configure.Payload = Bytes(Object{"config_revision": 3, "provider_id": "openai", "base_url": server.URL + "/v1", "model_id": "fixture-model", "credential_ref": credential})
	rebound, _ := handlerCommand(t, f, s, configure)
	if deref(rebound.Status) != "COMPLETED" {
		t.Fatalf("settled actual Run cannot rebind: %s", Bytes(rebound))
	}
	if Hash(f.read("runs", Str(oldRun, "id"))) != oldRunHash {
		t.Fatal("configuration altered existing Run")
	}
	var effectsAfter int
	f.db.QueryRow(`SELECT count(*) FROM resource_effects`).Scan(&effectsAfter)
	if effectsAfter != effectsBefore || calls.Load() != 2 {
		t.Fatal("save/binding check dispatched a provider effect")
	}
	configurationEvidenceSnapshot(t, f.db, "handler-typed-tls-sdk")
}

// These controls fork the actual settled two-call fixture. Only each explicitly
// identified unresolved fact is injected; no provider or worker is run again.
func handlerSettledRunNegativeClones(t *testing.T, original *fixture, service *ClientService, sid string, run Object, endpoint, credential string) {
	t.Helper()
	for _, variant := range []string{"RUNNING", "PAUSED", "LOST", "children", "queue", "settlement", "STARTED", "UNKNOWN"} {
		path := filepath.Join(t.TempDir(), "state.sqlite")
		if _, e := original.db.Exec(`VACUUM INTO ?`, path); e != nil {
			t.Fatal(e)
		}
		db, e := store.Open(path)
		if e != nil {
			t.Fatal(e)
		}
		func() {
			defer db.Close()
			f := *original
			f.db = db
			domain := *original.s
			domain.DB = db
			f.s = &domain
			s := *service
			s.Domain, s.SessionRuntime = &domain, nil
			bad := cloneObject(run)
			switch variant {
			case "RUNNING", "PAUSED", "LOST":
				bad["status"] = variant
			case "children":
				bad["children_stopped"] = false
			case "queue":
				bad["queue_empty"] = false
			case "settlement":
				bad["runtime_settled_at"] = nil
			case "STARTED", "UNKNOWN":
				sourceTx(t, db, func(tx *sql.Tx) error {
					key := "injected-configuration-settlement-" + variant
					if e := effectAppend(tx, f.project, Str(run, "id"), key, Object{"state": "CONFIRMED"}); e != nil {
						return e
					}
					return effectAppend(tx, f.project, Str(run, "id"), key, Object{"state": variant})
				})
			}
			if _, e := db.Exec(`UPDATE domain_objects SET body=? WHERE project=? AND kind='Run' AND id=?`, string(Bytes(bad)), f.project, Str(run, "id")); e != nil {
				t.Fatal(e)
			}
			env := queueClientEnvelope(t, &f, "tls-client", sid, "host.configure", Object{"config_revision": 2, "provider_id": "openai", "base_url": endpoint, "model_id": "fixture-model", "credential_ref": credential})
			r, _ := handlerCommand(t, &f, &s, env)
			if deref(r.Status) != "REJECTED" || deref(r.ErrorCode) != "SESSION_BUSY" {
				t.Fatalf("C09 injected %s accepted: %s", variant, Bytes(r))
			}
			var configurations, journals, identities int
			if e := db.QueryRow(`SELECT count(*) FROM host_model_configurations`).Scan(&configurations); e != nil {
				t.Fatal(e)
			}
			if e := db.QueryRow(`SELECT count(*) FROM idempotency WHERE key=?`, deref(env.CommandID)).Scan(&journals); e != nil {
				t.Fatal(e)
			}
			if e := db.QueryRow(`SELECT count(*) FROM client_command_identities WHERE command_id=?`, deref(env.CommandID)).Scan(&identities); e != nil {
				t.Fatal(e)
			}
			if configurations != 1 || journals != 1 || identities != 1 {
				t.Fatalf("C09 %s rejection counts configs=%d journals=%d identities=%d", variant, configurations, journals, identities)
			}
			t.Logf("C09_INJECTED_SETTLEMENT variant=%s request=%s response=%s", variant, Bytes(env), Bytes(r))
			configurationEvidenceSnapshot(t, db, "handler-settlement-"+strings.ToLower(variant))
		}()
	}
}

// Local clone of the original fixture producer, taking the already configured
// fixture so the profile is sealed only after its real config ref exists.
func handlerTLSCoordinatorFixture(t *testing.T, f *fixture, program func(Object) (string, string)) (*RuntimeCoordinator, RuntimeCoordinatorRoute, *runtimeFixture) {
	t.Helper()
	effect, checkpoint := false, false
	flags := []string{}
	req := f.requirement()
	exe, e := os.Executable()
	if e != nil {
		t.Fatal(e)
	}
	binary, e := os.ReadFile(exe)
	if e != nil {
		t.Fatal(e)
	}
	registration := f.expect(201, "POST", f.path("/runtimes"), ID(), f.stateTag(), Object{"name": "native coordinator fixture", "adapter": "codex-cli", "adapter_revision": runtimeBridgeRevision, "capabilities": []any{"start", "context_rebuild"}, "platform": "windows-amd64", "measurement_mode": "FIXTURE", "credential_ref": nil})
	argv := []any{"-test.run=^TestRuntimeCoordinatorChild$", "--", "--coordinator-child"}
	if effect {
		argv = append(argv, "--effect")
	}
	if checkpoint {
		argv = append(argv, "--checkpoint")
	}
	timeoutSeconds := 15
	for _, flag := range flags {
		argv = append(argv, flag)
		if flag == "--wait-heartbeat" {
			timeoutSeconds = 25
		}
	}
	argv = append(argv, "{manifest}")
	profileBody := Object{"runtime_id": registration["id"], "technical_hash": runtimeTechnicalHash(registration), "adapter": registration["adapter"], "adapter_revision": runtimeBridgeRevision, "platform": "windows-amd64", "build_hash": Digest(binary), "sandbox": runtimeSandboxProfile, "credential_revision": "none", "backend": "native-offline", "model": "none", "command_id": "native-fixture", "argv": argv, "effect_routes": []any{Object{"id": "fixture-echo", "capability": "fixture.echo", "credential_revision": "test-v1", "upper_bound": dollars("1")}}, "permissions": Object{"network": "none", "environment": "staging-only", "capabilities": Empty(), "process_limit": 1, "memory_mib": 256}, "timeout_seconds": timeoutSeconds, "outputs": []any{"result.json"}}
	bundleFile := ""
	if program != nil {
		exe, bundleFile = program(profileBody)
	}
	profile := f.artifact(profileBody, Empty())
	contract := orchestrationContract()
	if profileBody["backend"] == runtimeMuBackend {
		contract = clientTurnContract()
	}
	goal := f.expect(201, "POST", f.path("/goals"), ID(), f.stateTag(), Object{"title": "runtime qualification", "original_intent": "verify native coordinator", "scope": "PROJECT", "requirement_refs": []any{Ref(req, "Requirement")}, "problem_ids": []any{"runtime"}, "deliverables": []any{"receipt"}, "acceptance_contract": contract})
	goal = f.expect(200, "POST", f.path("/goals/"+Str(goal, "id")+"/actions"), ID(), testTag(goal), Object{"action": "ACTIVATE", "reason": "approved native fixture"})
	task := f.expect(201, "POST", f.path("/tasks"), ID(), testTag(goal), Object{"goal_id": goal["id"], "title": "runtime qualification", "task_type": "runtime_qualification", "stage": "verification", "dependency_task_ids": Empty(), "requirement_refs": []any{Ref(req, "Requirement")}, "input_refs": []any{Ref(profile, "Artifact")}, "acceptance_contract": contract, "origin_problem_id": "runtime", "candidate_id": "runtime", "stop_policy": Object{"wall_time_seconds": 60, "max_attempts": 1, "max_parallel_runs": 1, "stop_conditions": []any{"no progress"}}})
	f.bundle(task)
	task = f.read("tasks", Str(task, "id"))
	executor := ID()
	scheduler := ID()
	for _, p := range []Principal{{ID: executor, Roles: []string{"EXECUTOR"}, Grants: []Grant{{ProjectID: f.project, TaskID: Str(task, "id")}}}, {ID: scheduler, Roles: []string{"SCHEDULER"}, Grants: []Grant{{ProjectID: f.project}}}} {
		if e = f.s.ProvisionPrincipal(context.Background(), p); e != nil {
			t.Fatal(e)
		}
	}
	if e = f.s.RegisterRuntimeQualificationPlan(context.Background(), f.token, f.project, Str(task, "id"), Str(registration, "id"), Ref(profile, "Artifact"), []any{"start", "context_rebuild"}, time.Hour, ""); e != nil {
		t.Fatal(e)
	}
	run, lease, e := f.s.BeginRuntimeQualification(context.Background(), f.token, f.project, Str(task, "id"), Str(registration, "id"), executor)
	if e != nil {
		t.Fatal(e)
	}
	executorToken, e := f.s.IssueCredential(context.Background(), executor, 15*time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	schedulerToken, e := f.s.IssueCredential(context.Background(), scheduler, 15*time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	server, _ := fixtureHTTPServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/__researchos_fixture_readiness__" {
			w.WriteHeader(404)
			return
		}
		f.h.ServeHTTP(w, r)
	}))
	t.Cleanup(server.Close)
	var dbPath string
	var seq int
	var name string
	if e = f.db.QueryRow("PRAGMA database_list").Scan(&seq, &name, &dbPath); e != nil {
		t.Fatal(e)
	}
	route := RuntimeCoordinatorRoute{ProjectID: f.project, RuntimeID: Str(registration, "id"), ExecutorID: executor, ExecutorToken: executorToken, CommandID: Str(profileBody, "command_id"), Executable: exe, BundleFile: bundleFile}
	c, e := f.s.NewRuntimeCoordinator(context.Background(), RuntimeCoordinatorConfig{DataRoot: filepath.Dir(dbPath), APIURL: server.URL, SchedulerToken: schedulerToken, Routes: []RuntimeCoordinatorRoute{route}})
	if e != nil {
		t.Fatal(e)
	}
	t.Cleanup(func() { c.Close() })
	return c, route, &runtimeFixture{f: f, ownerToken: f.token, executor: executor, lease: lease, run: run, task: task, registration: registration}
}

func TestHandlerOriginalTaskProofAfterQueuedInput(t *testing.T) {
	for _, mutation := range []string{"none", "request-hash", "wrong-task", "missing-producer"} {
		t.Run(mutation, func(t *testing.T) {
			f, s, client, sid := queueClientFixture(t)
			defer configurationEvidenceSnapshot(t, f.db, "original-task-after-queued-input")
			for _, delivery := range []string{"STEER", "FOLLOW_UP"} {
				env := queueClientEnvelope(t, f, client, sid, "session.send", Object{"text": "same original Task input", "attachment_artifact_ids": Empty(), "delivery": delivery})
				reply, _ := goalCommand(t, f, s, env)
				if deref(reply.Status) != "COMPLETED" {
					t.Fatal(string(Bytes(reply)))
				}
			}
			// Deliberate corruption of this test's synthetic database. These controls
			// do not claim that mutable queue tables are tamper-proof.
			if mutation == "request-hash" {
				if _, e := f.db.Exec(`UPDATE client_command_queue SET request_hash='sha256:different'`); e != nil {
					t.Fatal(e)
				}
			}
			if mutation == "wrong-task" {
				if _, e := f.db.Exec(`UPDATE client_command_queue SET task_id='unrelated-task'`); e != nil {
					t.Fatal(e)
				}
			}
			if mutation == "missing-producer" {
				configurationBackupMutation(t, f.db, `DELETE FROM idempotency WHERE operation='v2:goal.start'`)
			}
			sourceTx(t, f.db, func(tx *sql.Tx) error {
				tasks, e := s.originalSessionTasks(context.Background(), tx, f.owner, f.project, sid)
				if mutation != "none" {
					if e == nil {
						t.Fatal("corrupt queue substituted original Task authority")
					}
					return nil
				}
				if e != nil {
					t.Fatal("accepted queued message was mistaken for a new Task producer", e)
				}
				if len(tasks) != 1 {
					t.Fatalf("original Task count=%d", len(tasks))
				}
				var original string
				if e = tx.QueryRow(`SELECT task_id FROM client_sessions WHERE id=?`, sid).Scan(&original); e != nil {
					return e
				}
				if Str(tasks[0], "id") != original {
					t.Fatal("queue substituted an unrelated Task")
				}
				return nil
			})
		})
	}
}

func TestHandlerPreSDKCancelledQueueCanRebind(t *testing.T) {
	for _, mutation := range []string{"none", "from-sending", "wrong-task", "missing-control", "other-control-session", "prior-receipt"} {
		t.Run(mutation, func(t *testing.T) {
			f, s, client, sid := queueClientFixture(t)
			defer configurationEvidenceSnapshot(t, f.db, "presdk-cancel-rebind")
			queued, _ := goalCommand(t, f, s, queueClientEnvelope(t, f, client, sid, "session.send", Object{"text": "never sent to SDK", "attachment_artifact_ids": Empty(), "delivery": "FOLLOW_UP"}))
			if deref(queued.Status) != "COMPLETED" {
				t.Fatal(string(Bytes(queued)))
			}
			var goal string
			if e := f.db.QueryRow(`SELECT goal_id FROM client_sessions WHERE id=?`, sid).Scan(&goal); e != nil {
				t.Fatal(e)
			}
			cancelled, _ := goalCommand(t, f, s, queueClientEnvelope(t, f, client, sid, "session.control", Object{"action": "CANCEL", "target_id": goal, "reason": "actual preSDK cancellation fixture"}))
			if deref(cancelled.Status) != "COMPLETED" || cancelled.Result["settled"] != true {
				t.Fatal(string(Bytes(cancelled)))
			}
			var state, kind, raw string
			if e := f.db.QueryRow(`SELECT q.state,r.kind,r.body FROM client_command_queue q JOIN client_control_receipts r ON r.receipt_id=q.last_receipt_id`).Scan(&state, &kind, &raw); e != nil {
				t.Fatal(e)
			}
			if state != "DROPPED" || kind != "CANCEL_FENCE" {
				t.Fatalf("actual cancellation producer %s %s", state, kind)
			}
			t.Logf("actual producer state=%s kind=%s body=%s", state, kind, raw)
			if mutation == "from-sending" || mutation == "wrong-task" {
				b, e := Decode([]byte(raw))
				if e != nil {
					t.Fatal(e)
				}
				if mutation == "from-sending" {
					b["from"] = "SENDING"
				} else {
					b["task_id"] = "foreign-task"
				}
				bad := Bytes(b)
				configurationBackupMutation(t, f.db, `UPDATE client_control_receipts SET body=?,body_hash=? WHERE kind='CANCEL_FENCE'`, string(bad), Digest(bad))
			}
			if mutation == "missing-control" {
				configurationBackupMutation(t, f.db, `DELETE FROM client_control_requests`)
			}
			if mutation == "other-control-session" {
				configurationBackupMutation(t, f.db, `UPDATE client_control_requests SET session_id='other-session'`)
			}
			if mutation == "prior-receipt" {
				configurationBackupMutation(t, f.db, `UPDATE client_control_receipts SET previous_receipt_id=receipt_id WHERE kind='CANCEL_FENCE'`)
			}
			env := queueClientEnvelope(t, f, client, sid, "host.configure", Object{"config_revision": 2, "provider_id": "fixture-provider", "base_url": "https://fixture.invalid/v1", "model_id": "next", "credential_ref": nil})
			reply, _ := handlerCommand(t, f, s, env)
			if mutation == "none" {
				if deref(reply.Status) != "COMPLETED" {
					t.Fatalf("real preSDK cancellation incorrectly remains busy: %s", Bytes(reply))
				}
			} else if deref(reply.Status) != "REJECTED" {
				t.Fatalf("forged preSDK cancellation proof accepted: %s", Bytes(reply))
			}
		})
	}
}
