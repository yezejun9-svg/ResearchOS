//go:build windows

package main

// Real CLI + native Host + production HTTP API + original coordinator + pinned Mu.
// The only model is a loopback FIXTURE; no LIVE provider is qualified.
import (
	"bytes"
	"context"
	"crypto/x509"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	localworkspace "researchos.local/research-os/adapters/local_workspace"
	"researchos.local/research-os/internal/api"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/host"
	"researchos.local/research-os/internal/store"
	"runtime"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

type queueCLIPermissionProfile struct {
	server                                   *httptest.Server
	calls                                    atomic.Int32
	host                                     *host.Host
	modelRef, configHash, project, runtimeID string
}

const queueCLISyntheticCredential = "cred-fixture-api_key-1234567890-12345678-12345678"

// The real Host supplies SID/workspace/native authority. This explicit injected
// fixture supplies only its one synthetic model metadata/credential tuple.
func (p *queueCLIPermissionProfile) ConfigurationMetadata(ctx context.Context, principal, provider string, ref *string) (domain.ClientConfigurationMetadata, error) {
	m, e := p.host.ConfigurationMetadata(ctx, principal, "", nil)
	if e != nil {
		return m, e
	}
	if ref != nil {
		if provider != "openai" || *ref != queueCLISyntheticCredential {
			return domain.ClientConfigurationMetadata{}, domain.Fail(403, "CREDENTIAL_MISSING", "synthetic model metadata mismatch")
		}
		m.Credential = &domain.ClientCredentialMetadata{Ref: *ref, Provider: provider, Kind: "API_KEY", Status: "AVAILABLE", CheckedAt: domain.Now()}
	}
	return m, nil
}
func (p *queueCLIPermissionProfile) modelCredential(ctx context.Context, route domain.RuntimeProviderRoute) ([]byte, error) {
	if e := ctx.Err(); e != nil {
		return nil, e
	}
	if p.modelRef == "" || route.ProjectID != p.project || route.RuntimeID != p.runtimeID || route.Capability != "MODEL" || (route.Purpose != "mu_turn" && route.Purpose != "runtime_qualification") || route.ID != "w0599-loopback-model" || route.CredentialRef != queueCLISyntheticCredential || route.CredentialRevision != queueCLISyntheticCredential || route.Endpoint != p.server.URL+"/v1/chat/completions" || domain.Str(route.ModelConfig, "ref") != p.modelRef || domain.Str(route.ModelConfig, "provider") != "openai" || domain.Hash(route.ModelConfig) != p.configHash {
		return nil, domain.Fail(403, "CREDENTIAL_MISSING", "synthetic route tuple mismatch")
	}
	return []byte("permission-loopback-fixture"), nil
}

var queueCLITLSRootsOnce sync.Once

func queueCLIInstallTLSFixture(t *testing.T, server *httptest.Server) {
	t.Helper()
	if !strings.Contains(os.Getenv("GODEBUG"), "x509usefallbackroots=1") || os.Getenv("RESEARCHOS_CLI_TLS_CHILD") != t.Name() {
		t.Fatal("TLS fixture requires its isolated exact-case process")
	}
	cert := server.Certificate()
	pool := x509.NewCertPool()
	pool.AddCert(cert)
	if _, e := cert.Verify(x509.VerifyOptions{Roots: x509.NewCertPool(), DNSName: "127.0.0.1"}); e == nil {
		t.Fatal("untrusted TLS certificate accepted")
	}
	if _, e := cert.Verify(x509.VerifyOptions{Roots: pool, DNSName: "wrong.invalid"}); e == nil {
		t.Fatal("wrong TLS hostname accepted")
	}
	queueCLITLSRootsOnce.Do(func() { x509.SetFallbackRoots(pool) })
	t.Logf("CLI_TLS_FIXTURE cert_sha256=%s measurement_mode=FIXTURE external_calls=0 paid_calls=0", domain.Digest(cert.Raw))
	if evidence := os.Getenv("RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR"); evidence != "" {
		dir := filepath.Join(evidence, t.Name())
		if e := os.MkdirAll(dir, 0700); e != nil {
			t.Fatal(e)
		}
		f, e := os.OpenFile(filepath.Join(dir, "tls-public-cert.der"), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
		if e != nil {
			t.Fatal(e)
		}
		_, e = f.Write(cert.Raw)
		closeErr := f.Close()
		if e != nil {
			t.Fatal(e)
		}
		if closeErr != nil {
			t.Fatal(closeErr)
		}
	}
}
func queueCLIExactTLSChild(t *testing.T) bool {
	t.Helper()
	if os.Getenv("RESEARCHOS_CLI_TLS_CHILD") == t.Name() {
		return false
	}
	exe, e := os.Executable()
	if e != nil {
		t.Fatal(e)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 240*time.Second)
	defer cancel()
	argv := []string{"-test.v", "-test.timeout=180s", "-test.run=^" + regexp.QuoteMeta(t.Name()) + "$"}
	command := exec.CommandContext(ctx, exe, argv...)
	debug := []string{}
	for _, part := range strings.Split(os.Getenv("GODEBUG"), ",") {
		if part != "" && !strings.HasPrefix(part, "x509usefallbackroots=") {
			debug = append(debug, part)
		}
	}
	debug = append(debug, "x509usefallbackroots=1")
	for _, item := range os.Environ() {
		if !strings.HasPrefix(item, "GODEBUG=") && !strings.HasPrefix(item, "RESEARCHOS_CLI_TLS_CHILD=") {
			command.Env = append(command.Env, item)
		}
	}
	command.Env = append(command.Env, "GODEBUG="+strings.Join(debug, ","), "RESEARCHOS_CLI_TLS_CHILD="+t.Name())
	started := time.Now().UTC()
	var stdout, stderr bytes.Buffer
	command.Stdout = &stdout
	command.Stderr = &stderr
	err := command.Run()
	exit := 0
	if err != nil {
		exit = -1
		var ee *exec.ExitError
		if errors.As(err, &ee) {
			exit = ee.ExitCode()
		}
	}
	if evidence := os.Getenv("RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR"); evidence != "" {
		dir := filepath.Join(evidence, t.Name(), "tls-child")
		if e = os.MkdirAll(dir, 0700); e != nil {
			t.Fatal(e)
		}
		cwd, _ := os.Getwd()
		binary, e := os.ReadFile(exe)
		if e != nil {
			t.Fatal(e)
		}
		records := map[string][]byte{"stdout.raw": stdout.Bytes(), "stderr.raw": stderr.Bytes(), "invocation.json": domain.Bytes(domain.Object{"actualargv": append([]string{exe}, argv...), "cwd": cwd, "started_at": started.Format(time.RFC3339Nano), "ended_at": time.Now().UTC().Format(time.RFC3339Nano), "exit": exit, "binary_sha256": domain.Digest(binary), "case": t.Name(), "measurement_mode": "FIXTURE", "external_calls": 0, "paid_calls": 0})}
		for name, raw := range records {
			f, e := os.OpenFile(filepath.Join(dir, name), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
			if e != nil {
				t.Fatal(e)
			}
			_, e = f.Write(raw)
			ce := f.Close()
			if e != nil {
				t.Fatal(e)
			}
			if ce != nil {
				t.Fatal(ce)
			}
		}
	}
	t.Logf("CLI_TLS_CHILD actual_exit=%d case=%s\n%s\n%s", exit, t.Name(), stdout.String(), stderr.String())
	if err != nil || !strings.Contains(stdout.String(), "=== RUN   "+t.Name()+"\n") || !strings.Contains(stdout.String(), "--- PASS:") {
		t.Fatalf("actual TLS child failed or ran no case: %v", err)
	}
	return true
}

const queueCLIFixtureModelRef = "w0599-local-model-fixture-v1"

type queueCLISwitchableHandler struct {
	mu sync.RWMutex
	h  http.Handler
}

func (s *queueCLISwitchableHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	s.mu.RLock()
	h := s.h
	s.mu.RUnlock()
	h.ServeHTTP(w, r)
}

func (s *queueCLISwitchableHandler) swap(h http.Handler) {
	s.mu.Lock()
	s.h = h
	s.mu.Unlock()
}

type queueCLIFixtureAPI struct {
	client               *http.Client
	base, token, project string
}

func (a queueCLIFixtureAPI) call(ctx context.Context, method, path, tag string, body any, want int) (domain.Object, error) {
	var raw []byte
	if body != nil {
		if value, ok := body.([]byte); ok {
			raw = value
		} else {
			raw = domain.Bytes(body)
		}
	}
	req, err := http.NewRequestWithContext(ctx, method, a.base+path, bytes.NewReader(raw))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bearer "+a.token)
	if method != http.MethodGet {
		req.Header.Set("Idempotency-Key", domain.ID())
	}
	if tag != "" {
		req.Header.Set("If-Match", tag)
	}
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	response, err := a.client.Do(req)
	if err != nil {
		return nil, err
	}
	defer response.Body.Close()
	data, err := io.ReadAll(io.LimitReader(response.Body, 4<<20))
	if err != nil {
		return nil, err
	}
	var result domain.Object
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, fmt.Errorf("fixture %s %s invalid JSON: %w", method, path, err)
	}
	if response.StatusCode != want {
		return nil, fmt.Errorf("fixture %s %s HTTP %d expected %d: %s", method, path, response.StatusCode, want, data)
	}
	return result, nil
}

func (a queueCLIFixtureAPI) path(tail string) string { return "/v1/projects/" + a.project + tail }

func (a queueCLIFixtureAPI) stateTag(ctx context.Context) (string, error) {
	state, err := a.call(ctx, http.MethodGet, a.path("/state"), "", nil, 200)
	if err != nil {
		return "", err
	}
	revision, err := domain.Num(state, "revision")
	if err != nil {
		return "", err
	}
	return `"r` + strconv.FormatInt(revision, 10) + `"`, nil
}

func queueCLIFixtureTag(value domain.Object) (string, error) {
	revision, err := domain.Num(value, "revision")
	if err != nil {
		return "", err
	}
	return `"r` + strconv.FormatInt(revision, 10) + `"`, nil
}

func (a queueCLIFixtureAPI) postState(ctx context.Context, path string, body any, want int) (domain.Object, error) {
	tag, err := a.stateTag(ctx)
	if err != nil {
		return nil, err
	}
	return a.call(ctx, http.MethodPost, path, tag, body, want)
}

func (a queueCLIFixtureAPI) postSubject(ctx context.Context, path string, subject domain.Object, body any, want int) (domain.Object, error) {
	tag, err := queueCLIFixtureTag(subject)
	if err != nil {
		return nil, err
	}
	return a.call(ctx, http.MethodPost, path, tag, body, want)
}

func queueCLIFixtureContract() domain.Object {
	contract := domain.Object{"contract_revision": 1, "checks": []any{domain.Object{
		"check_id": "fixture-scope", "kind": "DETERMINISTIC", "required": true,
		"expected":    "Actual loopback fixture; no external provider",
		"command_key": "w0599.fixture-scope", "rubric_ref": nil, "qualification_id": nil,
		"not_applicable_reason": nil,
	}}, "require_independent_verifier": true, "version_policy": "EXACT", "frozen_at": domain.Now()}
	contract["contract_hash"] = domain.Hash(contract)
	return contract
}

// queueCLIFixtureModelProfile creates real domain objects and an immutable runtime
// binding. With permission configured it qualifies the actual pinned Mu worker
// against the local model fixture before admitting the CLI's original Task.
func queueCLIFixtureModelProfile(ctx context.Context, svc *domain.Service, h *host.Host, client *http.Client, base, token, project, dataDir string, permission *queueCLIPermissionProfile) (*domain.RuntimeCoordinator, error) {
	a := queueCLIFixtureAPI{client: client, base: base, token: token, project: project}
	reg, err := a.postState(ctx, a.path("/runtimes"), domain.Object{
		"name": "W05-99 desktop loopback Mu profile", "adapter": "codex-cli",
		"adapter_revision": "windows-appcontainer-v1", "capabilities": []any{"start", "context_rebuild"},
		"platform": "windows-amd64", "measurement_mode": "FIXTURE", "credential_ref": nil,
	}, 201)
	if err != nil {
		return nil, err
	}
	executorID, schedulerID := "w0599-executor-"+domain.ID(), "w0599-scheduler-"+domain.ID()
	if err := svc.ProvisionPrincipal(ctx, domain.Principal{ID: executorID, Roles: []string{"EXECUTOR"}, Grants: []domain.Grant{{ProjectID: project}}}); err != nil {
		return nil, err
	}
	if err := svc.ProvisionPrincipal(ctx, domain.Principal{ID: schedulerID, Roles: []string{"SCHEDULER"}, Grants: []domain.Grant{{ProjectID: project}}}); err != nil {
		return nil, err
	}
	executorToken, err := svc.IssueCredential(ctx, executorID, 15*time.Minute)
	if err != nil {
		return nil, err
	}
	schedulerToken, err := svc.IssueCredential(ctx, schedulerID, 15*time.Minute)
	if err != nil {
		return nil, err
	}
	producer := queueCLIFixtureAPI{client: client, base: base, token: executorToken, project: project}
	exe, err := os.Executable()
	if err != nil {
		return nil, err
	}
	exeBytes, err := os.ReadFile(exe)
	if err != nil {
		return nil, err
	}
	bundle := filepath.Join(dataDir, "loopback-model-bundle.mjs")
	bundleBytes := []byte("// Inert W05-99 metadata. Never executed.\n")
	if err := os.WriteFile(bundle, bundleBytes, 0600); err != nil {
		return nil, err
	}
	config := domain.Object{"ref": queueCLIFixtureModelRef, "api": "openai-completions", "provider": "w0599-fixture", "model": "loopback-local-model", "endpoint": "http://127.0.0.1:1/v1/chat/completions", "route": "w0599-loopback-model", "max_output_tokens": 64, "max_calls": 1, "tools": domain.Empty()}
	profile := domain.Object{
		"runtime_id": reg["id"], "technical_hash": domain.Hash([]any{reg["adapter"], reg["adapter_revision"], reg["capabilities"], reg["platform"], reg["measurement_mode"], reg["credential_ref"]}),
		"adapter": reg["adapter"], "adapter_revision": reg["adapter_revision"], "platform": "windows-amd64",
		"build_hash": domain.Digest(exeBytes), "sandbox": "appcontainer-zero-capabilities-v1", "credential_revision": "none",
		"backend": "mu-sdk-broker-v1", "model": config["model"], "command_id": "w0599-loopback-mu-fixture",
		"argv": []any{"{bundle}", "{manifest}"}, "bundle_hash": domain.Digest(bundleBytes),
		"model_config": config, "model_qualification": domain.Object{"route": config["route"], "model_config_hash": domain.Hash(config), "max_calls": 1},
		"effect_routes":   []any{domain.Object{"id": config["route"], "capability": "MODEL", "credential_revision": "none", "upper_bound": domain.Object{"amount": "1", "currency": "USD"}}},
		"permissions":     domain.Object{"network": "none", "environment": "staging-only", "capabilities": domain.Empty(), "process_limit": 1, "memory_mib": 256},
		"timeout_seconds": 15, "outputs": []any{"result.json"},
		"tool_policy": domain.Object{"max_calls": 1, "read_paths": []any{"source.txt"}, "write_paths": []any{"source.txt"}, "max_read_bytes": 4096, "max_write_bytes": 4096},
	}
	if permission != nil {
		exe, bundle, err = permission.configure(config, profile)
		if err != nil {
			return nil, err
		}
	}
	if permission != nil {
		setup := &v2Context{clientID: "queue-cli-fixture", credential: token, baseURL: base, commandID: domain.ID()}
		configuredRef, err := cliPostConfigurationFixture(setup, map[string]any{"config_revision": 1, "provider_id": config["provider"], "base_url": strings.TrimSuffix(domain.Str(config, "endpoint"), "/chat/completions"), "model_id": config["model"], "credential_ref": queueCLISyntheticCredential})
		if err != nil {
			return nil, fmt.Errorf("actual typed fixture configure: %w", err)
		}
		config["ref"] = configuredRef
		permission.modelRef = domain.Str(config, "ref")
		permission.configHash = domain.Hash(config)
		permission.project = project
		permission.runtimeID = domain.Str(reg, "id")
		profile["model_qualification"] = domain.Object{"route": config["route"], "model_config_hash": domain.Hash(config), "max_calls": 1}
		for _, value := range profile["effect_routes"].([]any) {
			route := value.(map[string]any)
			if route["capability"] == "MODEL" {
				route["credential_revision"] = queueCLISyntheticCredential
			}
		}
	}
	raw := domain.Bytes(profile)
	upload, err := producer.call(ctx, http.MethodPost, a.path("/content"), "", raw, 201)
	if err != nil {
		return nil, err
	}
	artifact, err := producer.postState(ctx, a.path("/artifacts"), domain.Object{
		"run_id": nil, "kind": "REPORT", "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE",
		"content_hash": upload["content_hash"], "storage_key": upload["storage_key"],
		"media_type": "application/json", "byte_size": len(raw), "input_refs": domain.Empty(), "source_refs": domain.Empty(),
		"produced_by": executorID, "access_class": "PROJECT",
	}, 201)
	if err != nil {
		return nil, err
	}
	profileRef := domain.Ref(artifact, "Artifact")
	req, err := a.postState(ctx, a.path("/requirements"), domain.Object{
		"requirement_key": "W05-99-DESKTOP-WORKSPACE-FIXTURE", "text": "Verify a bounded desktop workspace write without executing a provider",
		"basis": "USER_STATED", "source_refs": domain.Empty(), "rationale": "W05-99 temporary fixture",
		"supersedes_id": nil, "acceptance_check_ids": domain.Empty(),
	}, 201)
	if err != nil {
		return nil, err
	}
	req, err = a.postSubject(ctx, a.path("/requirements/"+domain.Str(req, "id")+"/actions"), req,
		domain.Object{"action": "ACCEPT", "reason": "W05-99 fixture", "source_validation_refs": domain.Empty()}, 200)
	if err != nil {
		return nil, err
	}
	contract := queueCLIFixtureContract()
	if permission != nil {
		contract = queueCLIPermissionContract()
	}
	goal, err := a.postState(ctx, a.path("/goals"), domain.Object{
		"title": "W05-99 loopback runtime qualification plan", "original_intent": "Establish a frozen write boundary without dispatch",
		"scope": "PROJECT", "requirement_refs": []any{domain.Ref(req, "Requirement")},
		"problem_ids": []any{"w0599-write-fixture"}, "deliverables": []any{"Loopback fixture only"}, "acceptance_contract": contract,
	}, 201)
	if err != nil {
		return nil, err
	}
	goal, err = a.postSubject(ctx, a.path("/goals/"+domain.Str(goal, "id")+"/actions"), goal,
		domain.Object{"action": "ACTIVATE", "reason": "W05-99 fixture"}, 200)
	if err != nil {
		return nil, err
	}
	task, err := a.postSubject(ctx, a.path("/tasks"), goal, domain.Object{
		"goal_id": goal["id"], "title": "W05-99 frozen runtime metadata", "task_type": "runtime_qualification",
		"stage": "verification", "dependency_task_ids": domain.Empty(), "requirement_refs": []any{domain.Ref(req, "Requirement")},
		"input_refs": []any{profileRef}, "acceptance_contract": contract, "origin_problem_id": "w0599-write-fixture",
		"candidate_id": "w0599-write-fixture", "stop_policy": domain.Object{"wall_time_seconds": 60, "max_attempts": 1,
			"max_parallel_runs": 1, "stop_conditions": []any{"no progress"}},
	}, 201)
	if err != nil {
		return nil, err
	}
	state, err := a.call(ctx, http.MethodGet, a.path("/state"), "", nil, 200)
	if err != nil {
		return nil, err
	}
	stateRevision, err := domain.Num(state, "revision")
	if err != nil {
		return nil, err
	}
	schedulerAPI := queueCLIFixtureAPI{client: client, base: base, token: schedulerToken, project: project}
	_, err = schedulerAPI.postSubject(ctx, a.path("/context-bundles"), state,
		domain.Object{"task_id": task["id"], "expected_project_state_revision": stateRevision}, 201)
	if err != nil {
		return nil, err
	}
	if err := svc.RegisterRuntimeQualificationPlan(ctx, token, project, domain.Str(task, "id"), domain.Str(reg, "id"), profileRef, []any{"start", "context_rebuild"}, time.Hour, ""); err != nil {
		return nil, err
	}
	doc, err := api.ClientProtocolDocument()
	if err != nil {
		return nil, err
	}
	authority := localworkspace.NewAuthority(h)
	coordinatorConfig := domain.RuntimeCoordinatorConfig{
		DataRoot: dataDir, APIURL: base, SchedulerToken: schedulerToken,
		Routes: []domain.RuntimeCoordinatorRoute{{ProjectID: project, RuntimeID: domain.Str(reg, "id"), ExecutorID: executorID,
			ExecutorToken: executorToken, CommandID: "w0599-loopback-mu-fixture", Executable: exe, BundleFile: bundle}},
		WorkspaceAuthority: authority, RunTool: h.ExecuteRuntimeTool, ClientSchema: doc,
	}
	if permission != nil {
		coordinatorConfig.Providers = permission.providers(project, domain.Str(reg, "id"), config)
		coordinatorConfig.ConfigurationAuthority = permission
		coordinatorConfig.ModelCredential = permission.modelCredential
	}
	coordinator, err := svc.NewRuntimeCoordinator(ctx, coordinatorConfig)
	if err != nil {
		return nil, err
	}
	if coordinator == nil {
		return nil, errors.New("fixture coordinator unavailable")
	}
	if permission != nil {
		if err := queueCLIQualifyPermissionProfile(ctx, svc, coordinator, coordinatorConfig.Routes[0], a, producer, task, reg, executorID, token); err != nil {
			coordinator.Close()
			return nil, err
		}
	}
	return coordinator, nil
}

func (p *queueCLIPermissionProfile) configure(config, profile domain.Object) (string, string, error) {
	node, bundle := os.Getenv("RESEARCHOS_NODE"), os.Getenv("RESEARCHOS_MU_BUNDLE")
	if node == "" || bundle == "" {
		return "", "", errors.New("explicit locked RESEARCHOS_NODE and immutable RESEARCHOS_MU_BUNDLE required")
	}
	node, err := filepath.EvalSymlinks(node)
	if err != nil {
		return "", "", err
	}
	binary, err := os.ReadFile(node)
	if err != nil {
		return "", "", err
	}
	raw, err := os.ReadFile(bundle)
	if err != nil {
		return "", "", err
	}
	config["provider"], config["model"], config["endpoint"] = "openai", "fixture-model", p.server.URL+"/v1/chat/completions"
	config["max_calls"], config["max_output_tokens"] = 4, 512
	config["tools"] = domain.Empty()
	profile["build_hash"], profile["bundle_hash"], profile["model"] = domain.Digest(binary), domain.Digest(raw), config["model"]
	profile["argv"] = []any{"--preserve-symlinks-main", "--preserve-symlinks", "{bundle}", "{manifest}"}
	profile["model_qualification"] = domain.Object{"route": config["route"], "model_config_hash": domain.Hash(config), "max_calls": 1}
	profile["effect_routes"] = append(domain.Arr(profile, "effect_routes"), domain.Object{"id": config["route"], "capability": "TOOL", "credential_revision": "local-tools-v1", "upper_bound": domain.Object{"amount": "0", "currency": "USD"}})
	profile["tool_policy"] = domain.Object{"max_calls": 1, "read_paths": []any{"source.txt"}, "write_paths": []any{"source.txt"}, "max_read_bytes": 4096, "max_write_bytes": 4096, "user_confirmation_tools": []any{"write"}}
	profile["timeout_seconds"] = 180
	return node, bundle, nil
}

func (p *queueCLIPermissionProfile) providers(project, runtime string, config domain.Object) []domain.RuntimeProviderRoute {
	model := domain.RuntimeProviderRoute{ID: domain.Str(config, "route"), ProjectID: project, RuntimeID: runtime, Purpose: "runtime_qualification", Capability: "MODEL", CredentialRef: queueCLISyntheticCredential, CredentialRevision: queueCLISyntheticCredential, Endpoint: domain.Str(config, "endpoint"), UpperBound: domain.Object{"amount": "1", "currency": "USD"}, MeasurementMode: "FIXTURE", ModelConfig: config}
	turn := model
	turn.Purpose = "mu_turn"
	tool := turn
	tool.Capability = "TOOL"
	tool.CredentialRevision = "local-tools-v1"
	tool.UpperBound = domain.Object{"amount": "0", "currency": "USD"}
	tool.BearerToken = ""
	tool.Endpoint = ""
	tool.ModelConfig = nil
	return []domain.RuntimeProviderRoute{model, turn, tool}
}

func queueCLIPermissionContract() domain.Object {
	c := domain.Object{"contract_revision": 1, "checks": []any{domain.Object{"check_id": "mu-turn-output", "kind": "DETERMINISTIC", "required": true, "expected": "Bounded Mu response with exact user-message provenance and reconciled model/tool effects; execution is not independent acceptance", "command_key": "mu.turn-output-v1", "rubric_ref": nil, "qualification_id": nil, "not_applicable_reason": nil}}, "require_independent_verifier": true, "version_policy": "EXACT", "frozen_at": domain.Now()}
	c["contract_hash"] = domain.Hash(c)
	return c
}

func queueCLIQualifyPermissionProfile(ctx context.Context, s *domain.Service, c *domain.RuntimeCoordinator, route domain.RuntimeCoordinatorRoute, a, producer queueCLIFixtureAPI, task, reg domain.Object, executor, ownerToken string) error {
	run, lease, err := s.BeginRuntimeQualification(ctx, ownerToken, a.project, domain.Str(task, "id"), domain.Str(reg, "id"), executor)
	if err != nil {
		return err
	}
	if err = c.RunAdmitted(ctx, route, run, lease); err != nil {
		return err
	}
	task, err = a.call(ctx, http.MethodGet, a.path("/tasks/"+domain.Str(task, "id")), "", nil, 200)
	if err != nil {
		return err
	}
	run, err = a.call(ctx, http.MethodGet, a.path("/runs/"+domain.Str(run, "id")), "", nil, 200)
	if err != nil {
		return err
	}
	if task["status"] != "EXECUTION_REPORTED" || len(domain.Arr(run, "result_artifact_ids")) == 0 {
		return errors.New("loopback SDK qualification did not settle with actual output")
	}
	artifact, err := a.call(ctx, http.MethodGet, a.path("/artifacts/"+domain.Arr(run, "result_artifact_ids")[0].(string)), "", nil, 200)
	if err != nil {
		return err
	}
	verifier := "w0599-fixture-verifier-" + domain.ID()
	if err = s.ProvisionPrincipal(ctx, domain.Principal{ID: verifier, Roles: []string{"VERIFIER"}, Grants: []domain.Grant{{ProjectID: a.project}}}); err != nil {
		return err
	}
	verifierToken, err := s.IssueCredential(ctx, verifier, 15*time.Minute)
	if err != nil {
		return err
	}
	v := a
	v.token = verifierToken
	state, err := a.call(ctx, http.MethodGet, a.path("/state"), "", nil, 200)
	if err != nil {
		return err
	}
	contract := task["acceptance_contract"].(map[string]any)
	checks := domain.Empty()
	for _, value := range domain.Arr(contract, "checks") {
		check := value.(map[string]any)
		checks = append(checks, domain.Object{"check_id": check["check_id"], "status": "NOT_RUN", "evidence_refs": domain.Empty(), "command_key": check["command_key"], "actual": "request actual deterministic service computation for FIXTURE runtime", "exit_code": nil, "started_at": nil, "finished_at": nil})
	}
	receipt, err := v.postSubject(ctx, a.path("/acceptances"), task, domain.Object{"subject_ref": domain.Ref(task, "Task"), "run_id": run["id"], "contract_hash": contract["contract_hash"], "input_refs": task["input_refs"], "artifact_refs": []any{domain.Ref(artifact, "Artifact")}, "checks": checks, "verdict": "PASS", "executor_principal_ids": []any{executor}, "independence_basis": "DETERMINISTIC_SERVICE", "blocking_conflict_ids": domain.Empty(), "qualification_ids": domain.Empty(), "policy_revision": state["policy_revision"], "measurement_mode": "FIXTURE", "reason": "Actual deterministic loopback SDK fixture qualification; no LIVE resource"}, 201)
	if err != nil {
		return err
	}
	if receipt["verdict"] != "PASS" {
		return errors.New("actual FIXTURE qualification rejected")
	}
	var logRaw string
	if err = s.DB.QueryRowContext(ctx, "SELECT body FROM domain_objects WHERE project=? AND kind='Artifact' AND json_extract(body,'$.run_id')=? AND json_extract(body,'$.kind')='LOG'", a.project, run["id"]).Scan(&logRaw); err != nil {
		return err
	}
	log, err := domain.Decode([]byte(logRaw))
	if err != nil {
		return err
	}
	reg, err = v.postSubject(ctx, a.path("/runtimes/"+domain.Str(reg, "id")+"/qualify"), reg, domain.Object{"qualification_ids": []any{receipt["id"]}, "supports_resume": false, "resume_evidence_ref": nil, "receipt_artifact_ref": domain.Ref(log, "Artifact")}, 200)
	if err != nil {
		return err
	}
	if reg["status"] != "AVAILABLE" {
		return errors.New("FIXTURE runtime unavailable")
	}
	return s.AuthorizeRuntimePurpose(ctx, ownerToken, a.project, route.RuntimeID, "mu_turn", time.Now().Add(30*time.Minute))
}

func TestCLIActualMuInteractiveDurableQueue(t *testing.T)  { testCLIActualQueue(t, "consume") }
func TestCLIActualMuInteractiveCancelUnknown(t *testing.T) { testCLIActualQueue(t, "cancel") }
func TestCLIActualGoalCancelBeforeRun(t *testing.T)        { testCLIActualQueue(t, "noRun") }
func testCLIActualQueue(t *testing.T, mode string) {
	if queueCLIExactTLSChild(t) {
		return
	}
	if os.Getenv("RESEARCHOS_NODE") == "" || os.Getenv("RESEARCHOS_MU_BUNDLE") == "" {
		t.Fatal("actual pinned Node and current built Mu bundle are required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
	defer cancel()
	root := t.TempDir()
	data := filepath.Join(root, "data")
	workspace := filepath.Join(root, "workspace")
	for _, dir := range []string{data, workspace} {
		if err := os.MkdirAll(dir, 0700); err != nil {
			t.Fatal(err)
		}
	}
	if err := os.WriteFile(filepath.Join(workspace, "source.txt"), []byte("fixture workspace\n"), 0600); err != nil {
		t.Fatal(err)
	}
	db, err := store.Open(filepath.Join(data, "researchos.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	if err = store.Bootstrap(ctx, db, "../../migrations/sqlite/0001_bootstrap.sql"); err != nil {
		t.Fatal(err)
	}
	svc, err := domain.New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if err != nil {
		t.Fatal(err)
	}
	h, err := host.New(host.Config{DB: db, Dir: filepath.Join(data, "host"), ContractsDir: "../../spec/v2.0/contracts", MigrationFile: "../../migrations/sqlite/0002_domain.sql", SchemaDir: "../../internal/api/contracts"})
	if err != nil {
		t.Fatal(err)
	}
	p := &queueCLIPermissionProfile{host: h}
	handler := &queueCLISwitchableHandler{h: api.HandlerWithConfigurationHost(db, t.TempDir(), svc, nil, h.InstanceID(), localworkspace.NewAuthority(h), localworkspace.NewScanner(), p, h)}
	server := httptest.NewServer(handler)
	defer server.Close()
	discoveryFile := filepath.Join(data, "discovery.json")
	writeCLIDiscovery(t, discoveryFile, discovery{URL: server.URL, PID: os.Getpid(), DataDir: data}, h.InstanceID())
	configFile := filepath.Join(root, "cli.json")
	pipe := host.PipeName(h.InstanceID())
	nativeCtx, nativeCancel := context.WithCancel(ctx)
	doneNative := make(chan error, 1)
	go func() {
		doneNative <- h.ServeNativeWithChooser(nativeCtx, pipe, func(hint string) (string, error) {
			if hint != workspace {
				return "", errors.New("foreign workspace")
			}
			return workspace, nil
		})
	}()
	defer func() {
		nativeCancel()
		wake, _ := json.Marshal(host.NativeFrame{Kind: "NATIVE_UNKNOWN", ClientID: "test-wake", Payload: json.RawMessage(`{}`)})
		_, _ = host.DialNative(pipe, wake)
		select {
		case <-doneNative:
		case <-time.After(5 * time.Second):
			t.Error("native fixture failed to stop")
		}
	}()
	exe := filepath.Join(root, "researchos.exe")
	build := exec.CommandContext(ctx, filepath.Join(runtime.GOROOT(), "bin", "go.exe"), "build", "-o", exe, ".")
	if raw, e := build.CombinedOutput(); e != nil {
		t.Fatalf("build actual CLI: %v %s", e, raw)
	}
	env := append(os.Environ(), "RESEARCHOS_CLI_DISCOVERY="+discoveryFile, "RESEARCHOS_CLI_CONFIG="+configFile, "RESEARCHOS_CLI_CREDENTIAL=", "RESEARCHOS_CLI_CLIENT_ID=queue-cli-fixture")
	init := exec.CommandContext(ctx, exe, "init", workspace)
	init.Env = env
	if raw, e := init.CombinedOutput(); e != nil {
		t.Fatalf("real CLI init: %v %s", e, raw)
	}
	cfg := readCLIIntegrationConfig(t, configFile)
	owner, e := h.ReadSessionFile()
	if e != nil {
		t.Fatal(e)
	}
	entered := make(chan struct{})
	release := make(chan struct{})
	var releaseOnce sync.Once
	unblock := func() { releaseOnce.Do(func() { close(release) }) }
	defer unblock()
	var payloadMu sync.Mutex
	var payloads []domain.Object
	p.server = httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/__researchos_fixture_readiness__" {
			w.WriteHeader(404)
			return
		}
		if r.URL.Path != "/v1/chat/completions" || r.Header.Get("Authorization") != "Bearer permission-loopback-fixture" {
			w.WriteHeader(403)
			return
		}
		var body domain.Object
		if json.NewDecoder(r.Body).Decode(&body) != nil || body["model"] != "fixture-model" {
			w.WriteHeader(400)
			return
		}
		payloadMu.Lock()
		payloads = append(payloads, body)
		payloadMu.Unlock()
		n := p.calls.Add(1)
		if n == 2 {
			close(entered)
			select {
			case <-release:
			case <-r.Context().Done():
				return
			}
		}
		w.Header().Set("Content-Type", "text/event-stream")
		for i, delta := range []domain.Object{{"role": "assistant", "content": "actual queue loopback response"}, {}} {
			var finish any
			if i == 1 {
				finish = "stop"
			}
			fmt.Fprintf(w, "data: %s\n\n", domain.Bytes(domain.Object{"id": "queue-fixture-response", "object": "chat.completion.chunk", "created": 1, "model": "fixture-model", "choices": []any{domain.Object{"index": 0, "delta": delta, "finish_reason": finish}}}))
		}
		fmt.Fprint(w, "data: [DONE]\n\n")
	}))
	defer p.server.Close()
	queueCLIInstallTLSFixture(t, p.server)
	coordinator, e := queueCLIFixtureModelProfile(ctx, svc, h, server.Client(), server.URL, owner.Token, cfg.ProjectID, data, p)
	if e != nil {
		t.Fatal("actual fixture qualification", e)
	}
	defer coordinator.Close()
	handler.swap(api.HandlerWithConfigurationHost(db, t.TempDir(), svc, coordinator, h.InstanceID(), localworkspace.NewAuthority(h), localworkspace.NewScanner(), p, h))
	cfg.Model = p.modelRef
	if e = os.WriteFile(configFile, domain.Bytes(cfg), 0600); e != nil {
		t.Fatal(e)
	}
	run := exec.CommandContext(ctx, exe)
	run.Env = env
	stdin, e := run.StdinPipe()
	if e != nil {
		t.Fatal(e)
	}
	var output bytes.Buffer
	run.Stdout = &output
	run.Stderr = &output
	if e = run.Start(); e != nil {
		t.Fatal(e)
	}
	done := make(chan error, 1)
	finished := make(chan struct{})
	go func() { done <- run.Wait(); close(finished) }()
	defer func() {
		select {
		case <-finished:
		default:
			_ = run.Process.Kill()
			<-finished
		}
	}()
	if _, e = io.WriteString(stdin, "Original actual CLI run\n"); e != nil {
		t.Fatal(e)
	}

	if mode == "noRun" {
		if _, e = io.WriteString(stdin, "/cancel\n"); e != nil {
			t.Fatal(e)
		}
		_ = stdin.Close()
		select {
		case e = <-done:
		case <-ctx.Done():
			t.Fatal("pending Goal cancellation timed out")
		}
		var exit *exec.ExitError
		if !errors.As(e, &exit) || exit.ExitCode() != 130 {
			t.Fatalf("pending Goal cancel exit: %v %s", e, output.String())
		}
		var runs, confirmed int
		db.QueryRow(`SELECT count(*) FROM runtime_dispatches WHERE json_extract(manifest,'$.purpose')='mu_turn'`).Scan(&runs)
		db.QueryRow(`SELECT count(*) FROM client_control_requests WHERE state='CONFIRMED'`).Scan(&confirmed)
		var active any
		if e = db.QueryRow(`SELECT run_id FROM client_sessions WHERE project_id=? AND task_id IS NOT NULL`, cfg.ProjectID).Scan(&active); e != nil {
			t.Fatal(e)
		}
		if active != nil || runs != 0 || confirmed != 1 || !strings.Contains(output.String(), "HOST_CANCELLATION_SETTLED_WITHOUT_RUN") {
			t.Fatalf("noRun proof active=%v dispatch=%d confirmed=%d %s", active, runs, confirmed, output.String())
		}
		t.Log("actual compiled CLI original Goal cancellation before claim: no placeholder Run, confirmed control, exit130")
		return
	}
	// This is the production coordinator scheduler, driven explicitly to make the fixture bounded.
	started := false
	deadline := time.Now().Add(25 * time.Second)
	for time.Now().Before(deadline) && !started {
		if e = coordinator.Scan(ctx); e != nil {
			t.Fatal(e)
		}
		select {
		case <-entered:
			started = true
		default:
			time.Sleep(25 * time.Millisecond)
		}
	}
	if !started {
		_ = run.Process.Kill()
		<-finished
		rows, err := db.Query(`SELECT kind,id,body FROM domain_objects WHERE kind IN ('Task','Run')`)
		if err != nil {
			t.Fatal(err)
		}
		for rows.Next() {
			var kind, id, body string
			if err = rows.Scan(&kind, &id, &body); err != nil {
				break
			}
			t.Logf("startup diagnosis %s %s %s", kind, id, body)
		}
		rows.Close()
		if dir := os.Getenv("RESEARCHOS_QUEUE_FAILURE_DIR"); dir != "" {
			if err = os.MkdirAll(dir, 0700); err != nil {
				t.Fatal(err)
			}
			path := filepath.Join(dir, t.Name()+".sqlite")
			if _, err = db.Exec("VACUUM INTO ?", path); err != nil {
				t.Fatal(err)
			}
			t.Logf("isolated failed fixture snapshot: %s", path)
		}
		t.Fatalf("original CLI run never reached actual Mu MODEL effect: %s", output.String())
	}
	var task, runID string
	if e = db.QueryRow(`SELECT task_id,run_id FROM client_sessions WHERE project_id=? AND task_id IS NOT NULL`, cfg.ProjectID).Scan(&task, &runID); e != nil {
		t.Fatal(e)
	}
	const exact = "  Same text 中文  "
	if _, e = io.WriteString(stdin, "/steer "+exact+"\n/follow-up "+exact+"\nordinary draft must not dispatch\n"); e != nil {
		t.Fatal(e)
	}
	accepted := 0
	deadline = time.Now().Add(15 * time.Second)
	for time.Now().Before(deadline) {
		if e = db.QueryRow(`SELECT count(*) FROM client_command_queue WHERE state='SDK_ACCEPTED'`).Scan(&accepted); e != nil {
			t.Fatal(e)
		}
		if accepted == 2 {
			break
		}
		time.Sleep(30 * time.Millisecond)
	}
	if accepted != 2 {
		unblock()
		_ = stdin.Close()
		select {
		case <-done:
		case <-time.After(10 * time.Second):
			_ = run.Process.Kill()
			<-done
		}
		t.Fatalf("CLI did not admit both commands while original MODEL was pending: %d\n%s", accepted, output.String())
	}

	if mode == "cancel" {
		if _, e = io.WriteString(stdin, "/cancel\n"); e != nil {
			t.Fatal(e)
		}
		_ = stdin.Close()
		select {
		case e = <-done:
		case <-ctx.Done():
			t.Fatal("active CLI cancel timed out")
		}
		var exit *exec.ExitError
		if !errors.As(e, &exit) || exit.ExitCode() == 130 || exit.ExitCode() == 0 {
			t.Fatalf("unknown effect incorrectly confirmed: %v %s", e, output.String())
		}
		var pending, cleared, aborted, unknown, dispatches int
		db.QueryRow(`SELECT count(*) FROM client_control_requests WHERE state<>'CONFIRMED'`).Scan(&pending)
		db.QueryRow(`SELECT count(*) FROM client_control_receipts WHERE kind='command.cleared'`).Scan(&cleared)
		db.QueryRow(`SELECT count(*) FROM client_control_receipts WHERE kind='command.abort_observed'`).Scan(&aborted)
		db.QueryRow(`SELECT count(*) FROM resource_effects WHERE run=? AND json_extract(body,'$.state')='UNKNOWN'`, runID).Scan(&unknown)
		db.QueryRow(`SELECT count(*) FROM runtime_dispatches WHERE run=?`, runID).Scan(&dispatches)
		if pending != 1 || cleared != 2 || aborted == 0 || unknown == 0 || dispatches != 1 {
			t.Fatalf("pending=%d cleared=%d abort=%d unknown=%d dispatch=%d %s", pending, cleared, aborted, unknown, dispatches, output.String())
		}
		if !strings.Contains(output.String(), "WAIT_FOR_SETTLEMENT") {
			t.Fatal(output.String())
		}
		t.Log("actual compiled CLI active /cancel reached same Mu process; clear+abort observed, UNKNOWN effect retained, original control pending and exit !=130")
		return
	}
	unblock()
	_ = stdin.Close()
	select {
	case e = <-done:
	case <-ctx.Done():
		t.Fatal("CLI execution timed out")
	}
	if e != nil {
		t.Fatalf("actual interactive CLI failed: %v\n%s", e, output.String())
	}
	var consumed, dispatches, otherTasks int
	if e = db.QueryRow(`SELECT count(*) FROM client_command_queue WHERE state='CONSUMED' AND task_id=?`, task).Scan(&consumed); e != nil {
		t.Fatal(e)
	}
	if e = db.QueryRow(`SELECT count(*) FROM runtime_dispatches WHERE run=?`, runID).Scan(&dispatches); e != nil {
		t.Fatal(e)
	}
	if e = db.QueryRow(`SELECT count(*) FROM domain_objects WHERE kind='Task' AND json_extract(body,'$.task_type')='mu_turn'`).Scan(&otherTasks); e != nil {
		t.Fatal(e)
	}
	if consumed != 2 || dispatches != 1 || otherTasks != 1 {
		t.Fatalf("consumed=%d dispatches=%d turnTasks=%d", consumed, dispatches, otherTasks)
	}
	var state string
	var acceptedThrough, sealedThrough int
	if e = db.QueryRow(`SELECT state,accepted_through,sealed_through FROM client_queue_fences WHERE task_id=?`, task).Scan(&state, &acceptedThrough, &sealedThrough); e != nil {
		t.Fatal(e)
	}
	if state != "SEALED" || acceptedThrough != 2 || sealedThrough != 2 {
		t.Fatalf("SEAL proof %s %d %d", state, acceptedThrough, sealedThrough)
	}
	raw := output.String()
	if !strings.Contains(raw, "input.enqueued") || !strings.Contains(raw, "ACTIVE_INPUT_REQUIRES_STEER_OR_FOLLOW_UP") || strings.Contains(raw, owner.Token) {
		t.Fatalf("queue output missing or credential exposed: %s", raw)
	}
	payloadMu.Lock()
	defer payloadMu.Unlock()
	if len(payloads) < 4 {
		t.Fatalf("actual SDK model calls %d", len(payloads))
	}
	final := string(domain.Bytes(payloads[len(payloads)-1]))
	if strings.Count(final, exact) != 2 || strings.Contains(final, "queue_binding") {
		t.Fatalf("SDK custom-message content lost stable occurrences: %s", final)
	}
	t.Logf("FIXTURE actual CLI stdin, private native Host, production API, current Mu SDK: same Task=%s Run=%s dispatch=1 consumed=2 SEAL=2 calls=%d", task, runID, p.calls.Load())
}
