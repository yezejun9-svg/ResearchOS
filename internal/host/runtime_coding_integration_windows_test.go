//go:build windows

package host_test

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	localworkspace "researchos.local/research-os/adapters/local_workspace"
	"researchos.local/research-os/internal/api"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/host"
	"researchos.local/research-os/internal/store"
	"researchos.local/research-os/internal/verifier"
	"runtime"
	"strings"
	"sync/atomic"
	"testing"
	"time"
)

// Isolated synthetic SSE transport; actual Host, inherited anonymous pipe,
// current Mu/AppContainer, verifier process and offline Go check. No live model.
func TestProductCodingPrivateHostSyntheticTools(t *testing.T) { testProductCodingPrivateHost(t, true) }
func TestProductCodingPrivateHostSyntheticFileTools(t *testing.T) {
	testProductCodingPrivateHost(t, false)
}
func testProductCodingPrivateHost(t *testing.T, includeCheck bool) {
	if *productionRuntimeAssets == "" || *localVerifierExecutable == "" {
		t.Skip("explicit Mu and verifier assets required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 4*time.Minute)
	defer cancel()
	initial := "package calc\nfunc Value() int { return 1 }\n"
	fixed := strings.Replace(initial, "return 1", "return 2", 1)
	var calls atomic.Int32
	var successfulChecks atomic.Int32
	model := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		n := calls.Add(1)
		var body domain.Object
		if json.NewDecoder(r.Body).Decode(&body) != nil {
			t.Error("invalid model request")
			w.WriteHeader(400)
			return
		}
		if r.Header.Get("Authorization") != "" || r.URL.Path != "/v1/chat/completions" {
			t.Error("unexpected model transport")
			w.WriteHeader(400)
			return
		}
		toolCount := len(domain.Arr(body, "tools"))
		if toolCount != 4 {
			t.Errorf("qualification/normal tool schema count n=%d tools=%d", n, toolCount)
		}
		delta := domain.Object{"role": "assistant", "content": "Synthetic coding transport completed."}
		finish := "stop"
		var name string
		var args domain.Object
		switch n {
		case 2:
			name = "read"
			args = domain.Object{"path": "calc/value.go"}
		case 3:
			name = "edit"
			args = domain.Object{"path": "calc/value.go", "expected_hash": domain.Digest([]byte(initial)), "old_text": "return 1", "new_text": "return 2"}
		case 4:
			name = "write"
			args = domain.Object{"path": "notes.txt", "content": "fixture coding edit complete\n", "expected_hash": nil}
		case 5:
			if includeCheck {
				name = "run_check"
				args = domain.Object{"check_id": "value-check"}
			}
		}
		if name != "" {
			delta = domain.Object{"role": "assistant", "tool_calls": []any{domain.Object{"index": 0, "id": fmt.Sprintf("call-%d", n), "type": "function", "function": domain.Object{"name": name, "arguments": string(domain.Bytes(args))}}}}
			finish = "tool_calls"
		}
		w.Header().Set("Content-Type", "text/event-stream")
		for _, item := range []domain.Object{{"index": 0, "delta": delta, "finish_reason": nil}, {"index": 0, "delta": domain.Object{}, "finish_reason": finish}} {
			fmt.Fprintf(w, "data: %s\n\n", domain.Bytes(domain.Object{"id": "synthetic-coding", "object": "chat.completion.chunk", "created": 1, "model": "synthetic-local-model", "choices": []any{item}}))
		}
		fmt.Fprint(w, "data: [DONE]\n\n")
	}))
	defer model.Close()
	repo, data, workspace := backupTestRepo(t), t.TempDir(), t.TempDir()
	for p, s := range map[string]string{"go.mod": "module fixture.local/productcoding\n\ngo 1.27\n", "calc/value.go": initial, "calc/value_test.go": "package calc\nimport \"testing\"\nfunc TestValue(t *testing.T) { if Value()!=2 { t.Fatal(\"value not fixed\") } }\n"} {
		full := filepath.Join(workspace, filepath.FromSlash(p))
		if e := os.MkdirAll(filepath.Dir(full), 0700); e != nil {
			t.Fatal(e)
		}
		if e := os.WriteFile(full, []byte(s), 0600); e != nil {
			t.Fatal(e)
		}
	}
	db, e := store.Open(filepath.Join(data, "researchos.sqlite"))
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	if e = store.Bootstrap(ctx, db, filepath.Join(repo, "migrations/sqlite/0001_bootstrap.sql")); e != nil {
		t.Fatal(e)
	}
	svc, e := domain.NewCurrentMu(db, filepath.Join(repo, "spec/v2.0/contracts"), filepath.Join(repo, "migrations/sqlite/0002_domain.sql"))
	if e != nil {
		t.Fatal(e)
	}
	h := backupTestHost(t, db, data, repo)
	owner, e := h.BootstrapOwner(ctx)
	if e != nil {
		t.Fatal(e)
	}
	doc, e := api.ClientProtocolDocument()
	if e != nil {
		t.Fatal(e)
	}
	authority := localworkspace.NewAuthority(h)
	raw, e := h.HandleNative(domain.Bytes(domain.Object{"kind": host.KindWorkspaceChooseRequest, "client_id": "coding-client", "payload": domain.Object{"requested_path": workspace, "requested_access": host.AccessReadWrite}}), true, func(string) (string, error) { return workspace, nil })
	if e != nil {
		t.Fatal(e)
	}
	var chosen struct {
		Payload struct {
			Ref string `json:"selection_ref"`
		} `json:"payload"`
	}
	if e = json.Unmarshal(raw, &chosen); e != nil {
		t.Fatal(e)
	}
	p := domain.Principal{ID: owner.PrincipalID, Roles: []string{"OWNER"}, CanCreateProject: true}
	registered, e := svc.RegisterWorkspace(ctx, p, authority, doc, domain.RegisterWorkspaceInput{SelectionRef: chosen.Payload.Ref, DisplayName: "coding synthetic", RequestedAccess: host.AccessReadWrite, ClientID: "coding-client", CommandID: domain.ID()})
	if e != nil {
		t.Fatal(e)
	}
	workspaceRef := domain.Str(registered, "authorized_workspace_ref")
	project, e := svc.BootstrapProject(ctx, p, authority, doc, localworkspace.NewScanner(), domain.BootstrapProjectInput{AuthorizedWorkspaceRef: workspaceRef, DisplayName: "synthetic coding", ClientID: "coding-client", CommandID: domain.ID(), MeasurementMode: "FIXTURE"})
	if e != nil {
		t.Fatal(e)
	}
	projectID := domain.Str(project, "project_id")
	server := httptest.NewUnstartedServer(nil)
	setup := h.NewRuntimeSetup(svc, doc, *productionRuntimeAssets)
	c, e := svc.NewRuntimeCoordinator(ctx, domain.RuntimeCoordinatorConfig{DataRoot: data, APIURL: "http://" + server.Listener.Addr().String(), WorkspaceAuthority: authority, ConfigurationAuthority: h, ClientSchema: doc, ModelCredential: h.ModelCredential, RunTool: func(ctx context.Context, request domain.RuntimeToolRequest) (domain.Object, error) {
		result, err := h.ExecuteRuntimeTool(ctx, request)
		if request.Name == "run_check" && err == nil {
			details, _ := result["details"].(map[string]any)
			if domain.Hash(details["exit_code"]) == domain.Hash(0) && details["timed_out"] == false && details["children_stopped"] == true && details["streams_drained"] == true && details["cleanup_complete"] == true {
				successfulChecks.Add(1)
			}
		}
		t.Logf("actual host tool=%s err=%v result=%s", request.Name, err, domain.Bytes(domain.Object{"details": result["details"], "host_evidence_hash": domain.Hash(result["host_evidence"])}))
		return result, err
	}, PrepareLocalRuntime: setup.Reconcile})
	if e != nil {
		t.Fatal(e)
	}
	defer c.Close()
	server.Config.Handler = api.HandlerWithConfigurationHost(db, filepath.Join(repo, "apps/web/dist"), svc, c, h.InstanceID(), authority, localworkspace.NewScanner(), h, h)
	server.Start()
	defer server.Close()
	command := func(method string, project, session, revision, epoch any, payload domain.Object) domain.Object {
		t.Helper()
		body := domain.Bytes(domain.Object{"protocol_version": domain.ProtocolV2, "command_id": domain.ID(), "client_id": "coding-client", "project_id": project, "session_id": session, "expected_revision": revision, "writer_epoch": epoch, "method": method, "payload": payload})
		r, e := http.NewRequestWithContext(ctx, "POST", server.URL+"/v2/command", bytes.NewReader(body))
		if e != nil {
			t.Fatal(e)
		}
		r.Header.Set("Authorization", "Bearer "+owner.Session.Token)
		r.Header.Set("Content-Type", "application/json")
		response, e := server.Client().Do(r)
		if e != nil {
			t.Fatal(e)
		}
		defer response.Body.Close()
		var result domain.Object
		if json.NewDecoder(response.Body).Decode(&result) != nil || response.StatusCode != 200 || result["status"] != "COMPLETED" {
			t.Fatalf("typed %s HTTP=%d %s", method, response.StatusCode, domain.Bytes(result))
		}
		return result
	}
	saved := command("host.configure", nil, nil, nil, nil, domain.Object{"config_revision": 1, "provider_id": "ollama", "base_url": model.URL + "/v1", "model_id": "synthetic-local-model", "credential_ref": nil})
	modelRef := domain.Str(saved["result"].(map[string]any), "model_config_ref")
	created := command("session.create", projectID, nil, nil, nil, domain.Object{"workspace_ref": workspaceRef, "model_config_ref": modelRef, "title": "coding synthetic"})
	sessionID := domain.Str(created, "session_id")
	binary, e := os.ReadFile(*localVerifierExecutable)
	if e != nil {
		t.Fatal(e)
	}
	manifest := host.RuntimeVerifierInstallation{Schema: "researchos.runtime-verifier-installation.v1", ServiceID: verifier.ServiceID, Protocol: verifier.Protocol, Executable: *localVerifierExecutable, ExecutableHash: domain.Digest(binary), SourceCommit: strings.Repeat("0", 40), Arguments: []string{}}
	input, parentWrite, e := os.Pipe()
	if e != nil {
		t.Fatal(e)
	}
	defer input.Close()
	defer parentWrite.Close()
	parentRead, output, e := os.Pipe()
	if e != nil {
		t.Fatal(e)
	}
	defer parentRead.Close()
	defer output.Close()
	management, e := host.NewDesktopManagement(h, svc, c, server.URL, manifest, input, output, func(ctx context.Context) error { _, e := c.QuiesceForDesktopExit(ctx); return e })
	if e != nil {
		t.Fatal(e)
	}
	managedCtx, managedCancel := context.WithCancel(ctx)
	defer managedCancel()
	done := make(chan error, 1)
	go func() { done <- management.Serve(managedCtx) }()
	reader := bufio.NewReader(parentRead)
	read := func() domain.Object {
		t.Helper()
		line, e := reader.ReadBytes('\n')
		if e != nil {
			t.Fatal(e)
		}
		if bytes.Contains(line, []byte(owner.Session.Token)) {
			t.Fatal("Owner token leaked")
		}
		value, e := domain.Decode(line)
		if e != nil {
			t.Fatal(e)
		}
		return value
	}
	if ready := read(); ready["kind"] != "READY" {
		t.Fatal("management READY absent")
	}
	exchange := func(operation string, payload domain.Object) domain.Object {
		t.Helper()
		payload["protocol"], payload["operation"], payload["host_id"], payload["message_id"] = host.DesktopManagementProtocol, operation, h.InstanceID(), domain.ID()
		if _, e := parentWrite.Write(append(domain.Bytes(payload), '\n')); e != nil {
			t.Fatal(e)
		}
		value := read()
		if value["kind"] != "RESULT" {
			t.Fatalf("private %s failed: %s", operation, domain.Bytes(value))
		}
		return value["result"].(map[string]any)
	}
	paths := []string{"go.mod", "calc/value.go", "calc/value_test.go", "notes.txt"}
	intent := domain.RuntimeCodingIntent{ClientID: "coding-client", ExpectedRevision: 1, WriterEpoch: 1, ConfigRevision: 2, WorkspaceRef: workspaceRef, ReadPaths: paths, WritePaths: []string{"calc/value.go", "notes.txt"}, MaxReadBytes: 8192, MaxWriteBytes: 8192, MaxToolCalls: 8, MaxOutputTokens: 2048, Checks: []domain.RuntimeCodingCheck{{ID: "value-check", Package: "./calc", TestPattern: "^TestValue$", SourcePaths: paths[:3], ToolchainRoot: runtime.GOROOT(), TimeoutSeconds: 90, ProcessLimit: 32, MemoryMiB: 1024, MaxTextBytes: 4096}}}
	prepared := exchange("PREPARE_CODING", domain.Object{"project_id": projectID, "session_id": sessionID, "model_config_ref": modelRef, "coding": intent})
	if calls.Load() != 0 {
		t.Fatal("coding prepare called model")
	}
	var head int64
	if e = db.QueryRow(`SELECT current_revision FROM host_model_config_heads`).Scan(&head); e != nil || head != 1 {
		t.Fatal("coding prepare mutated config")
	}
	binding := domain.Object{"project_id": projectID, "request_id": prepared["request_id"], "request_hash": prepared["request_hash"]}
	configured := exchange("CONFIRM_CODING", binding)
	if calls.Load() != 0 || configured["state"] != "CODING_CONFIGURED" {
		t.Fatal("coding install called model")
	}
	newRef := domain.Str(configured, "model_config_ref")
	if newRef == modelRef || newRef == "" {
		t.Fatal("coding profile did not create new reference")
	}
	status := exchange("STATUS_CODING", domain.Object{"project_id": projectID, "request_id": prepared["request_id"], "request_hash": prepared["request_hash"]})
	if domain.Hash(status) != domain.Hash(configured) {
		t.Fatal("coding status changed original result")
	}
	qualification := exchange("PREPARE", domain.Object{"project_id": projectID, "session_id": sessionID, "model_config_ref": newRef})
	var request domain.LocalRuntimeQualificationRequest
	if e = json.Unmarshal(domain.Bytes(qualification["request"]), &request); e != nil {
		t.Fatal(e)
	}
	result := exchange("CONFIRM", domain.Object{"project_id": projectID, "request_id": request.RequestID, "request_hash": domain.Hash(request)})
	if result["state"] != "QUALIFIED_PURPOSE_AUTHORIZED" || calls.Load() != 1 {
		t.Fatalf("coding qualification %s calls=%d", domain.Bytes(result), calls.Load())
	}
	var toolEffects int
	db.QueryRow(`SELECT count(DISTINCT effect_key) FROM resource_effects WHERE json_extract(body,'$.payload.capability')='TOOL'`).Scan(&toolEffects)
	if toolEffects != 0 {
		t.Fatal("qualification executed tools")
	}
	// Same immutable unknown ledger remains strict for release but permits safe Desktop exit.
	var originalLedger string
	db.QueryRow(`SELECT group_concat(body) FROM domain_objects WHERE kind='BudgetLedgerEntry'`).Scan(&originalLedger)
	if _, e = c.QuiesceForRelease(ctx); e == nil {
		t.Fatal("release ignored UNKNOWN ledger")
	}
	if snap, err := c.QuiesceForDesktopExit(ctx); err != nil {
		t.Fatalf("completed local qualification exit refused: %v %+v", err, snap)
	}
	c.ResumeAfterReleaseAbort()
	var unchanged string
	db.QueryRow(`SELECT group_concat(body) FROM domain_objects WHERE kind='BudgetLedgerEntry'`).Scan(&unchanged)
	if originalLedger != unchanged {
		t.Fatal("exit rewrote accounting")
	}
	runtimeErrors := make(chan error, 8)
	serveCtx, serveCancel := context.WithCancel(ctx)
	serveDone := make(chan error, 1)
	go func() {
		serveDone <- c.Serve(serveCtx, func(e error) {
			t.Logf("runtime error: %v", e)
			select {
			case runtimeErrors <- e:
			default:
			}
		})
	}()
	defer func() { serveCancel(); <-serveDone }()
	// The explicit one-minute writer may expire during the independent process;
	// normal public takeover renews the same client lease without new coding authority.
	var revision, epoch int64
	db.QueryRow(`SELECT revision,writer_epoch FROM client_sessions WHERE id=?`, sessionID).Scan(&revision, &epoch)
	command("session.send", projectID, sessionID, revision, epoch, domain.Object{"text": "Read calc/value.go, change Value to return 2, write notes.txt and run value-check.", "attachment_artifact_ids": domain.Empty(), "delivery": "NORMAL"})
	if e = c.Scan(ctx); e != nil {
		t.Fatal(e)
	}
	deadline := time.Now().Add(140 * time.Second)
	var settled int
	var runtimeFailure error
wait:
	for time.Now().Before(deadline) {
		select {
		case runtimeFailure = <-runtimeErrors:
			break wait
		default:
		}
		db.QueryRow(`SELECT count(*) FROM domain_objects WHERE kind='Run' AND json_extract(body,'$.status') IN ('SETTLED','FAILED','CANCELLED')`).Scan(&settled)
		if settled == 2 {
			break
		}
		time.Sleep(100 * time.Millisecond)
	}
	wantCalls, wantTools := int32(5), 3
	if includeCheck {
		wantCalls, wantTools = 6, 4
	}
	if settled != 2 || calls.Load() != wantCalls {
		var diagnostic string
		db.QueryRow(`SELECT group_concat(state||':'||reason) FROM runtime_dispatches`).Scan(&diagnostic)
		t.Fatalf("coding normal turn failed settled=%d calls=%d dispatch=%s", settled, calls.Load(), diagnostic+fmt.Sprint(runtimeFailure))
	}
	got, e := os.ReadFile(filepath.Join(workspace, "calc/value.go"))
	if e != nil || string(got) != fixed {
		t.Fatalf("actual edit %q %v", got, e)
	}
	got, e = os.ReadFile(filepath.Join(workspace, "notes.txt"))
	if e != nil || string(got) != "fixture coding edit complete\n" {
		t.Fatalf("actual write %q %v", got, e)
	}
	db.QueryRow(`SELECT count(DISTINCT effect_key) FROM resource_effects WHERE json_extract(body,'$.payload.capability')='TOOL'`).Scan(&toolEffects)
	if toolEffects != wantTools {
		t.Fatalf("tools=%d", toolEffects)
	}
	var unknown, toolReceipts int
	db.QueryRow(`SELECT count(*) FROM domain_objects WHERE kind='BudgetLedgerEntry' AND json_extract(body,'$.operation')='UNKNOWN' AND json_type(body,'$.money')='null' AND json_extract(body,'$.cost_basis')='UNKNOWN'`).Scan(&unknown)
	db.QueryRow(`SELECT count(DISTINCT effect_key) FROM resource_effects WHERE json_extract(body,'$.payload.capability')='TOOL' AND json_extract(body,'$.state')='CONFIRMED'`).Scan(&toolReceipts)
	if unknown != int(wantCalls) {
		t.Fatalf("model UNKNOWN accounting changed: %d", unknown)
	}
	if includeCheck && successfulChecks.Load() != 1 {
		t.Fatal("native offline check did not exit 0 with complete stopped/drained/cleanup evidence")
	}
	var beforeExit string
	db.QueryRow(`SELECT group_concat(body) FROM domain_objects WHERE kind='BudgetLedgerEntry'`).Scan(&beforeExit)
	// Stop only the fixture scan loop after all canonical Runs settle; no process kill.
	serveCancel()
	if e = <-serveDone; e != nil {
		t.Fatal(e)
	}
	serveDone <- nil
	if _, e = c.QuiesceForRelease(ctx); e == nil {
		t.Fatal("release allowed original MODEL UNKNOWN")
	}
	stopped := exchange("SHUTDOWN", domain.Object{})
	if stopped["state"] != "SHUTDOWN_ACCEPTED" {
		t.Fatal("private safe exit missing")
	}
	select {
	case <-done:
	case <-ctx.Done():
		t.Fatal("private shutdown did not finish")
	}
	if e = c.Close(); e != nil {
		t.Fatal(e)
	}
	var afterExit string
	db.QueryRow(`SELECT group_concat(body) FROM domain_objects WHERE kind='BudgetLedgerEntry'`).Scan(&afterExit)
	if beforeExit != afterExit {
		t.Fatal("private exit mutated original UNKNOWN/null")
	}
	t.Logf("SOURCE_FIXTURE private_coding=true new_config=%s original_session=%s qualification=1MODEL/0TOOL normal_model=%d tools=%d include_native_check=%v actual_files_changed=true settled=2 UNKNOWN_null=%d tool_receipts=%d private_SHUTDOWN=accepted release=refused ledgers=unchanged real_model_calls=0", newRef, sessionID, wantCalls-1, wantTools, includeCheck, unknown, toolReceipts)
}
