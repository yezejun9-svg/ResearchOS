//go:build windows

package host_test

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync/atomic"
	"syscall"
	"testing"
	"time"

	localworkspace "researchos.local/research-os/adapters/local_workspace"
	"researchos.local/research-os/internal/api"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/host"
	"researchos.local/research-os/internal/store"
	"researchos.local/research-os/internal/verifier"
)

var localVerifierExecutable = flag.String("local-runtime-verifier-executable", "", "explicit candidate verifier executable for synthetic local integration")
var localControlExecutable = flag.String("local-runtime-control-executable", "", "explicit candidate control executable for inherited management lifecycle fixture")

func TestDesktopManagementActualControlLifecycle(t *testing.T) {
	if *localControlExecutable == "" || *localVerifierExecutable == "" {
		t.Skip("explicit candidate control and verifier binaries required")
	}
	repo, data, web := backupTestRepo(t), t.TempDir(), t.TempDir()
	if e := os.WriteFile(filepath.Join(web, "index.html"), []byte("isolated control lifecycle fixture"), 0600); e != nil {
		t.Fatal(e)
	}
	verifierBytes, e := os.ReadFile(*localVerifierExecutable)
	if e != nil {
		t.Fatal(e)
	}
	manifest := host.RuntimeVerifierInstallation{Schema: "researchos.runtime-verifier-installation.v1", ServiceID: verifier.ServiceID, Protocol: verifier.Protocol, Executable: *localVerifierExecutable, ExecutableHash: domain.Digest(verifierBytes), SourceCommit: strings.Repeat("0", 40), Arguments: []string{}}
	manifestFile := filepath.Join(t.TempDir(), "installed-verifier.json")
	if e = os.WriteFile(manifestFile, domain.Bytes(manifest), 0600); e != nil {
		t.Fatal(e)
	}
	var originalHost, originalOwner string
	for generation := 1; generation <= 2; generation++ {
		cmd := exec.Command(*localControlExecutable, "--desktop-management-stdio", "--runtime-verifier-manifest", manifestFile, "--discovery-file", filepath.Join(data, "discovery.json"))
		cmd.Dir = repo
		cmd.Env = append(os.Environ(), "RESEARCHOS_DATA_DIR="+data, "RESEARCHOS_WEB_DIR="+web, "RESEARCHOS_LISTEN=127.0.0.1:0")
		cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
		var stderr bytes.Buffer
		cmd.Stderr = &stderr
		in, e := cmd.StdinPipe()
		if e != nil {
			t.Fatal(e)
		}
		out, e := cmd.StdoutPipe()
		if e != nil {
			t.Fatal(e)
		}
		if e = cmd.Start(); e != nil {
			t.Fatal(e)
		}
		waited := make(chan error, 1)
		go func() { waited <- cmd.Wait() }()
		exited := false
		defer func() {
			if exited {
				return
			}
			// Best-effort cleanup uses only the original inherited management
			// capability and this fresh fixture's exact discovery. Never Kill.
			var discovery domain.Object
			if raw, err := os.ReadFile(filepath.Join(data, "discovery.json")); err == nil && json.Unmarshal(raw, &discovery) == nil {
				frame := domain.Object{"protocol": host.DesktopManagementProtocol, "message_id": domain.ID(), "operation": "SHUTDOWN", "host_id": discovery["host_instance_id"]}
				_, _ = in.Write(append(domain.Bytes(frame), '\n'))
			}
			select {
			case err := <-waited:
				t.Logf("fixture cleanup actual graceful exit PID=%d result=%v", cmd.Process.Pid, err)
			case <-time.After(8 * time.Second):
				t.Errorf("fixture orderly cleanup blocked; PID=%d retained, no force-kill", cmd.Process.Pid)
			}
		}()
		reader := bufio.NewReader(out)
		read := func() domain.Object {
			t.Helper()
			type readResult struct {
				raw []byte
				e   error
			}
			done := make(chan readResult, 1)
			go func() { raw, e := reader.ReadBytes('\n'); done <- readResult{raw, e} }()
			select {
			case got := <-done:
				if got.e != nil {
					t.Fatalf("control private pipe: %v diagnostics=%s", got.e, stderr.String())
				}
				obj, e := domain.Decode(got.raw)
				if e != nil {
					t.Fatal(e)
				}
				return obj
			case <-time.After(15 * time.Second):
				t.Fatalf("control management timeout PID=%d", cmd.Process.Pid)
				return nil
			}
		}
		ready := read()
		if ready["kind"] != "READY" {
			t.Fatalf("control READY absent: %s", domain.Bytes(ready))
		}
		hostID := domain.Str(ready, "host_id")
		if generation == 1 {
			originalHost = hostID
		} else if hostID != originalHost {
			t.Fatal("restart changed original Host")
		}
		actual := ready["control_process"].(map[string]any)
		pid, _ := domain.Num(actual, "PID")
		parent := ready["parent_process"].(map[string]any)
		parentPID, _ := domain.Num(parent, "PID")
		if pid != int64(cmd.Process.Pid) || parentPID != int64(os.Getpid()) {
			t.Fatal("actual inherited parent/child identity differs")
		}
		raw, e := host.DialNative(host.PipeName(hostID), domain.Bytes(domain.Object{"kind": host.KindUserBootstrapRequest, "client_id": "managed-control-lifecycle", "payload": domain.Object{}}))
		if e != nil {
			t.Fatal(e)
		}
		var native domain.Object
		if json.Unmarshal(raw, &native) != nil || native["kind"] == "NATIVE_ERROR" {
			t.Fatalf("actual native bootstrap failed: %s", raw)
		}
		state, e := os.ReadFile(filepath.Join(data, "host", "host_state.json"))
		if e != nil {
			t.Fatal(e)
		}
		var hostState domain.Object
		if json.Unmarshal(state, &hostState) != nil {
			t.Fatal("invalid original host state")
		}
		owner := domain.Str(hostState, "principal_id")
		if owner == "" {
			t.Fatal("native Owner not bound")
		}
		if generation == 1 {
			originalOwner = owner
		} else if owner != originalOwner {
			t.Fatal("restart created another Owner")
		}
		if generation == 1 {
			second := exec.Command(*localControlExecutable, "--discovery-file", filepath.Join(data, "second-discovery.json"))
			second.Dir = repo
			second.Env = cmd.Env
			second.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
			output, e := second.CombinedOutput()
			if e == nil || !bytes.Contains(output, []byte("data-root lease unavailable")) {
				t.Fatalf("second coordinator not refused: %v %s", e, output)
			}
			t.Logf("actual second control exit refused: %s", bytes.TrimSpace(output))
		}
		frame := domain.Object{"protocol": host.DesktopManagementProtocol, "message_id": domain.ID(), "operation": "SHUTDOWN", "host_id": hostID}
		if _, e = in.Write(append(domain.Bytes(frame), '\n')); e != nil {
			t.Fatal(e)
		}
		stopped := read()
		if stopped["kind"] != "RESULT" || stopped["result"].(map[string]any)["state"] != "SHUTDOWN_ACCEPTED" {
			t.Fatalf("orderly shutdown refused: %s", domain.Bytes(stopped))
		}
		select {
		case e = <-waited:
			exited = true
			if e != nil {
				t.Fatalf("control exit: %v diagnostics=%s", e, stderr.String())
			}
		case <-time.After(15 * time.Second):
			t.Fatal("control did not finish orderly shutdown")
		}
		t.Logf("actual control generation=%d PID=%d Host=%s parent=%d exit=0 diagnostics=%s", generation, cmd.Process.Pid, hostID, os.Getpid(), stderr.String())
	}
	t.Log("actual inherited private pipe and Native3 bootstrap, same Host/Owner after orderly exit/restart, second coordinator denied, model calls=0")
}

// This exercises actual Host, Mu/AppContainer, a separate verifier executable
// and the existing HTTP acceptance authority. ALL model responses come from
// this synthetic in-process SSE server, never Ollama or a paid/live provider.
// Its isolated test database is discarded and confers no product qualification.
func TestManagedLocalRuntimeQualificationSyntheticTransport(t *testing.T) {
	testManagedLocalQualification(t, "")
}

func TestDesktopManagementSyntheticQualification(t *testing.T) {
	testManagedLocalQualification(t, "", "private")
}

func TestDesktopManagementLostReplySettlesOriginalEffect(t *testing.T) {
	testManagedLocalQualification(t, "", "lost_reply")
}

func TestManagedLocalQualificationRootRevocation(t *testing.T) {
	for _, phase := range []string{"before_acceptance", "before_qualify", "before_purpose", "after_purpose"} {
		t.Run(phase, func(t *testing.T) { testManagedLocalQualification(t, phase) })
	}
}

func testManagedLocalQualification(t *testing.T, revokePhase string, managementMode ...string) {
	if *productionRuntimeAssets == "" || *localVerifierExecutable == "" {
		t.Skip("explicit packaged Mu assets and candidate verifier executable required; no live model used")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()
	lostReply := len(managementMode) > 0 && managementMode[0] == "lost_reply"
	modelArrived, modelRelease := make(chan struct{}), make(chan struct{})
	releaseModel := func() {
		select {
		case <-modelRelease:
		default:
			close(modelRelease)
		}
	}
	defer releaseModel()
	var calls atomic.Int32
	model := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		call := calls.Add(1)
		if lostReply && call == 1 {
			close(modelArrived)
			select {
			case <-modelRelease:
			case <-ctx.Done():
				return
			}
		}
		if r.Header.Get("Authorization") != "" || r.URL.Path != "/v1/chat/completions" {
			t.Errorf("unexpected model request path=%s credential_forwarded=%v", r.URL.Path, r.Header.Get("Authorization") != "")
			w.WriteHeader(403)
			return
		}
		var body domain.Object
		if json.NewDecoder(r.Body).Decode(&body) != nil || body["model"] != "synthetic-local-model" {
			w.WriteHeader(400)
			return
		}
		w.Header().Set("Content-Type", "text/event-stream")
		for _, delta := range []domain.Object{{"role": "assistant", "content": "Synthetic transport response for isolated source verification."}, {}} {
			var finish any
			if len(delta) == 0 {
				finish = "stop"
			}
			fmt.Fprintf(w, "data: %s\n\n", domain.Bytes(domain.Object{"id": "source-fixture", "object": "chat.completion.chunk", "created": 1, "model": "synthetic-local-model", "choices": []any{domain.Object{"index": 0, "delta": delta, "finish_reason": finish}}}))
		}
		fmt.Fprint(w, "data: [DONE]\n\n")
	}))
	defer model.Close()
	repo := backupTestRepo(t)
	data := t.TempDir()
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
	workspace := t.TempDir()
	raw, e := h.HandleNative(domain.Bytes(domain.Object{"kind": host.KindWorkspaceChooseRequest, "client_id": "qualification-source-fixture", "payload": domain.Object{"requested_path": workspace, "requested_access": host.AccessReadOnly}}), true, func(string) (string, error) { return workspace, nil })
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
	registered, e := svc.RegisterWorkspace(ctx, p, authority, doc, domain.RegisterWorkspaceInput{SelectionRef: chosen.Payload.Ref, DisplayName: "synthetic qualification workspace", RequestedAccess: host.AccessReadOnly, ClientID: "qualification-source-fixture", CommandID: domain.ID()})
	if e != nil {
		t.Fatal(e)
	}
	workspaceRef := domain.Str(registered, "authorized_workspace_ref")
	project, e := svc.BootstrapProject(ctx, p, authority, doc, localworkspace.NewScanner(), domain.BootstrapProjectInput{AuthorizedWorkspaceRef: workspaceRef, DisplayName: "isolated synthetic qualifier", ClientID: "qualification-source-fixture", CommandID: domain.ID(), MeasurementMode: "FIXTURE"})
	if e != nil {
		t.Fatal(e)
	}
	projectID := domain.Str(project, "project_id")
	server := httptest.NewUnstartedServer(nil)
	setup := h.NewRuntimeSetup(svc, doc, *productionRuntimeAssets)
	c, e := svc.NewRuntimeCoordinator(ctx, domain.RuntimeCoordinatorConfig{DataRoot: data, APIURL: "http://" + server.Listener.Addr().String(), WorkspaceAuthority: authority, ConfigurationAuthority: h, ClientSchema: doc, ModelCredential: h.ModelCredential, RunTool: h.ExecuteRuntimeTool, PrepareLocalRuntime: setup.Reconcile})
	if e != nil {
		t.Fatal(e)
	}
	defer c.Close()
	baseHandler := api.HandlerWithConfigurationHost(db, filepath.Join(repo, "apps/web/dist"), svc, c, h.InstanceID(), authority, localworkspace.NewScanner(), h, h)
	var revokedRoot string
	var retainedReceipt string
	revokeServiceRoot := func() {
		t.Helper()
		if revokedRoot != "" {
			t.Fatal("test attempted duplicate root revocation")
		}
		if e := db.QueryRow(`SELECT o.root FROM orchestration_identity o JOIN auth_principals p ON p.id=o.principal WHERE o.parent=o.root AND p.roles='["VERIFIER"]'`).Scan(&revokedRoot); e != nil {
			t.Fatal(e)
		}
		var receipt string
		if e := db.QueryRow(`SELECT body FROM domain_objects WHERE kind='AcceptanceReceipt'`).Scan(&receipt); e == nil {
			retainedReceipt = receipt
		}
		if e := svc.RevokePrincipal(ctx, revokedRoot); e != nil {
			t.Fatal(e)
		}
	}
	server.Config.Handler = http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method == "POST" && (strings.HasSuffix(r.URL.Path, "/acceptances") || strings.HasSuffix(r.URL.Path, "/qualify")) {
			if c.ClientIntakeOpen() {
				t.Error("ordinary session execution intake open during independent acceptance/purpose window")
			}
			if err := c.Scan(ctx); err != nil {
				t.Error(err)
			}
			if calls.Load() != 1 {
				t.Error("ordinary scan dispatched during independent acceptance")
			}
			if (revokePhase == "before_acceptance" && strings.HasSuffix(r.URL.Path, "/acceptances")) || (revokePhase == "before_qualify" && strings.HasSuffix(r.URL.Path, "/qualify")) {
				revokeServiceRoot()
			}
			recorder := httptest.NewRecorder()
			baseHandler.ServeHTTP(recorder, r)
			if revokePhase == "before_purpose" && strings.HasSuffix(r.URL.Path, "/qualify") && recorder.Code == 200 {
				revokeServiceRoot()
			}
			if recorder.Code >= 400 {
				t.Logf("synthetic authority rejected %s HTTP %d: %s", r.URL.Path, recorder.Code, recorder.Body.Bytes())
			}
			for name, values := range recorder.Header() {
				for _, value := range values {
					w.Header().Add(name, value)
				}
			}
			w.WriteHeader(recorder.Code)
			_, _ = w.Write(recorder.Body.Bytes())
			return
		}
		baseHandler.ServeHTTP(w, r)
	})
	server.Start()
	defer server.Close()
	command := func(method string, project, session, revision, epoch any, payload domain.Object) domain.Object {
		t.Helper()
		body := domain.Bytes(domain.Object{"protocol_version": domain.ProtocolV2, "command_id": domain.ID(), "client_id": "qualification-source-fixture", "project_id": project, "session_id": session, "expected_revision": revision, "writer_epoch": epoch, "method": method, "payload": payload})
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
		if json.NewDecoder(response.Body).Decode(&result) != nil || response.StatusCode != 200 {
			t.Fatalf("typed %s status=%d", method, response.StatusCode)
		}
		if result["status"] != "COMPLETED" {
			t.Fatalf("typed %s: %s", method, domain.Bytes(result))
		}
		return result
	}
	saved := command("host.configure", nil, nil, nil, nil, domain.Object{"config_revision": 1, "provider_id": "ollama", "base_url": model.URL + "/v1", "model_id": "synthetic-local-model", "credential_ref": nil})
	modelRef := domain.Str(saved["result"].(map[string]any), "model_config_ref")
	created := command("session.create", projectID, nil, nil, nil, domain.Object{"workspace_ref": workspaceRef, "model_config_ref": modelRef, "title": "synthetic qualification"})
	sessionID := domain.Str(created, "session_id")
	if e = c.Scan(ctx); e != nil {
		t.Fatal(e)
	}
	request, e := c.PreparedLocalQualification(ctx, owner.Session.Token, domain.RuntimeSetupCandidate{ProjectID: projectID, SessionID: sessionID, PrincipalID: owner.PrincipalID, ModelRef: modelRef}, 600)
	if e != nil {
		t.Fatal(e)
	}
	binary, e := os.ReadFile(*localVerifierExecutable)
	if e != nil {
		t.Fatal(e)
	}
	manifest := host.RuntimeVerifierInstallation{Schema: "researchos.runtime-verifier-installation.v1", ServiceID: verifier.ServiceID, Protocol: verifier.Protocol, Executable: *localVerifierExecutable, ExecutableHash: domain.Digest(binary), SourceCommit: strings.Repeat("0", 40), Arguments: []string{}}
	manifestFile := filepath.Join(t.TempDir(), "verifier-installation.json")
	if e = os.WriteFile(manifestFile, domain.Bytes(manifest), 0600); e != nil {
		t.Fatal(e)
	}
	installed, e := host.LoadRuntimeVerifierInstallation(manifestFile)
	if e != nil {
		t.Fatal(e)
	}
	var result domain.Object
	if len(managementMode) > 0 {
		input, parentWrite, err := os.Pipe()
		if err != nil {
			t.Fatal(err)
		}
		defer input.Close()
		defer parentWrite.Close()
		parentRead, output, err := os.Pipe()
		if err != nil {
			t.Fatal(err)
		}
		defer parentRead.Close()
		defer output.Close()
		management, err := host.NewDesktopManagement(h, svc, c, server.URL, installed, input, output, nil)
		if err != nil {
			t.Fatal(err)
		}
		managedCtx, managedCancel := context.WithCancel(ctx)
		defer managedCancel()
		done := make(chan error, 1)
		go func() { done <- management.Serve(managedCtx) }()
		reader := bufio.NewReader(parentRead)
		read := func() domain.Object {
			t.Helper()
			line, err := reader.ReadBytes('\n')
			if err != nil {
				t.Fatal(err)
			}
			value, err := domain.Decode(line)
			if err != nil {
				t.Fatal(err)
			}
			if bytes.Contains(line, []byte(owner.Session.Token)) {
				t.Fatal("native Owner token leaked to management pipe")
			}
			return value
		}
		ready := read()
		if ready["kind"] != "READY" || ready["host_id"] != h.InstanceID() {
			t.Fatal("private original Host READY missing")
		}
		exchange := func(operation string, payload domain.Object) domain.Object {
			t.Helper()
			payload["protocol"], payload["operation"], payload["host_id"], payload["message_id"] = host.DesktopManagementProtocol, operation, h.InstanceID(), domain.ID()
			if _, err := parentWrite.Write(append(domain.Bytes(payload), '\n')); err != nil {
				t.Fatal(err)
			}
			return read()
		}
		prepared := exchange("PREPARE", domain.Object{"project_id": projectID, "session_id": sessionID, "model_config_ref": modelRef})
		if prepared["kind"] != "RESULT" || calls.Load() != 0 {
			t.Fatalf("private prepare made model call or failed: %s", domain.Bytes(prepared))
		}
		confirmation := prepared["result"].(map[string]any)
		if json.Unmarshal(domain.Bytes(confirmation["request"]), &request) != nil {
			t.Fatal("invalid private confirmation")
		}
		if domain.Hash(request) != confirmation["request_hash"] {
			t.Fatal("private confirmation hash changed")
		}
		binding := domain.Object{"project_id": projectID, "request_id": request.RequestID, "request_hash": domain.Hash(request)}
		if lostReply {
			binding["protocol"], binding["operation"], binding["host_id"], binding["message_id"] = host.DesktopManagementProtocol, "CONFIRM", h.InstanceID(), domain.ID()
			if _, err = parentWrite.Write(append(domain.Bytes(binding), '\n')); err != nil {
				t.Fatal(err)
			}
			select {
			case <-modelArrived:
			case <-ctx.Done():
				t.Fatal("synthetic original effect never arrived")
			}
			parentRead.Close()
			parentWrite.Close()
			releaseModel()
			select {
			case err = <-done:
				if err == nil {
					t.Fatal("lost private response was not reported")
				}
			case <-ctx.Done():
				t.Fatal("original admitted effect did not settle after link loss")
			}
			result, e = c.LocalQualificationStatus(ctx, owner.Session.Token, projectID, request.RequestID, domain.Hash(request))
			if e != nil || result["state"] != "QUALIFIED_PURPOSE_AUTHORIZED" || calls.Load() != 1 {
				t.Fatalf("lost reply lost original authority or replayed: %s %v", domain.Bytes(result), e)
			}
			t.Log("private pipe lost while synthetic effect pending: original Run/independent acceptance/purpose settled once; durable STATUS recovered; no retry or forced host stop")
		} else {
			confirmed := exchange("CONFIRM", binding)
			if confirmed["kind"] != "RESULT" {
				t.Fatalf("private confirm: %s", domain.Bytes(confirmed))
			}
			result = confirmed["result"].(map[string]any)
			status := exchange("STATUS", domain.Object{"project_id": projectID, "request_id": request.RequestID, "request_hash": domain.Hash(request)})
			if status["kind"] != "RESULT" || status["result"].(map[string]any)["state"] != "QUALIFIED_PURPOSE_AUTHORIZED" {
				t.Fatalf("durable status not revalidated: %s", domain.Bytes(status))
			}
			second := exchange("CONFIRM", domain.Object{"project_id": projectID, "request_id": request.RequestID, "request_hash": domain.Hash(request)})
			if second["kind"] != "ERROR" || calls.Load() != 1 {
				t.Fatal("duplicate private CONFIRM repeated model call")
			}
			parentWrite.Close()
			select {
			case <-done:
			case <-ctx.Done():
				t.Fatal("private EOF did not close only management link")
			}
			t.Log("actual Host private pipe PREPARE=zero calls CONFIRM=one STATUS=original authority duplicate=denied EOF=host retained")
		}
	} else {
		result, e = h.QualifyLocalRuntime(ctx, svc, c, server.URL, request, installed)
	}
	if revokePhase != "" {
		if revokePhase == "after_purpose" {
			if e != nil || result["state"] != "QUALIFIED_PURPOSE_AUTHORIZED" {
				t.Fatalf("valid pre-revocation baseline failed: %v %s", e, domain.Bytes(result))
			}
			revokeServiceRoot()
		} else if e == nil {
			t.Fatalf("revoked service root retained qualification authority: %s", domain.Bytes(result))
		}
		if calls.Load() != 1 || revokedRoot == "" {
			t.Fatal("revocation fixture did not cover original one-call execution")
		}
		var runtimeStatus string
		if e = db.QueryRow(`SELECT json_extract(body,'$.status') FROM domain_objects WHERE kind='RuntimeRegistration' AND id=?`, request.RuntimeID).Scan(&runtimeStatus); e != nil {
			t.Fatal(e)
		}
		wantRuntime := "REGISTERED"
		wantReceipts := 0
		wantGrants := 0
		if revokePhase != "before_acceptance" {
			wantReceipts = 1
		}
		if revokePhase == "before_purpose" || revokePhase == "after_purpose" {
			wantRuntime = "AVAILABLE"
		}
		if revokePhase == "after_purpose" {
			wantGrants = 1
		}
		var receiptCount, grantCount, credentials int
		db.QueryRow(`SELECT count(*) FROM domain_objects WHERE kind='AcceptanceReceipt'`).Scan(&receiptCount)
		db.QueryRow(`SELECT count(*) FROM resource_route_grants WHERE purpose='mu_turn'`).Scan(&grantCount)
		db.QueryRow(`SELECT count(*) FROM auth_credentials c JOIN orchestration_identity o ON o.principal=c.principal WHERE o.root=? AND c.revoked=0`, revokedRoot).Scan(&credentials)
		if runtimeStatus != wantRuntime || receiptCount != wantReceipts || grantCount != wantGrants || credentials != 0 {
			t.Fatalf("revocation boundary leaked authority: runtime=%s receipts=%d grants=%d live_credentials=%d", runtimeStatus, receiptCount, grantCount, credentials)
		}
		if retainedReceipt != "" {
			var original string
			if e = db.QueryRow(`SELECT body FROM domain_objects WHERE kind='AcceptanceReceipt'`).Scan(&original); e != nil || original != retainedReceipt {
				t.Fatal("original acceptance receipt changed or lost")
			}
		}
		if e = svc.AuthorizeRuntimePurpose(ctx, owner.Session.Token, projectID, request.RuntimeID, "mu_turn", time.Now().Add(time.Minute)); e == nil {
			t.Fatal("revoked verifier root issued a new purpose")
		}
		command("session.send", projectID, sessionID, 1, 1, domain.Object{"text": "Must not dispatch after verifier root revocation.", "attachment_artifact_ids": domain.Empty(), "delivery": "NORMAL"})
		if e = c.Scan(ctx); e != nil {
			t.Fatal(e)
		}
		if e = c.Close(); e != nil {
			t.Fatal(e)
		}
		var runs, unknown int
		db.QueryRow(`SELECT count(*) FROM domain_objects WHERE kind='Run' AND json_extract(body,'$.runtime_id')=?`, request.RuntimeID).Scan(&runs)
		db.QueryRow(`SELECT count(*) FROM domain_objects WHERE kind='BudgetLedgerEntry' AND json_extract(body,'$.operation')='UNKNOWN' AND json_extract(body,'$.cost_basis')='UNKNOWN' AND json_type(body,'$.money')='null' AND json_type(body,'$.reservation_id')='null'`).Scan(&unknown)
		if runs != 1 || unknown != 1 || calls.Load() != 1 {
			t.Fatalf("revoked root consumed new authority or rewrote old UNKNOWN: runs=%d unknown=%d synthetic_calls=%d", runs, unknown, calls.Load())
		}
		t.Logf("SOURCE_FIXTURE root_revoked_at=%s original_runtime_status=%s retained_receipts=%d retained_grants=%d new_purpose=DENIED admission=DENIED original_UNKNOWN_null=1 verifier_token_revoked=true synthetic_calls=1 real_model_calls=0", revokePhase, runtimeStatus, receiptCount, grantCount)
		return
	}
	if e != nil {
		t.Fatalf("synthetic qualification failed (calls=%d): %v diagnostic=%s", calls.Load(), e, domain.Bytes(result))
	}
	if result["state"] != "QUALIFIED_PURPOSE_AUTHORIZED" || calls.Load() != 1 {
		t.Fatalf("qualification chain: %s calls=%d", domain.Bytes(result), calls.Load())
	}
	var root, child string
	if e = db.QueryRow(`SELECT o.root,o.principal FROM orchestration_identity o JOIN auth_principals p ON p.id=o.principal WHERE o.parent=o.root AND p.roles='["VERIFIER"]'`).Scan(&root, &child); e != nil {
		t.Fatal(e)
	}
	var ownerRoot string
	if e = db.QueryRow(`SELECT root FROM orchestration_identity WHERE principal=?`, owner.PrincipalID).Scan(&ownerRoot); e != nil || root == ownerRoot {
		t.Fatalf("verifier authority aliases author: %v", e)
	}
	var liveCredentials int
	if e = db.QueryRow(`SELECT count(*) FROM auth_credentials WHERE principal=? AND revoked=0`, child).Scan(&liveCredentials); e != nil || liveCredentials != 0 {
		t.Fatalf("verifier credential not revoked: %d %v", liveCredentials, e)
	}
	var receipts int
	if e = db.QueryRow(`SELECT count(*) FROM domain_objects WHERE kind='AcceptanceReceipt' AND json_extract(body,'$.verifier_principal_id')=? AND json_extract(body,'$.verdict')='PASS'`, child).Scan(&receipts); e != nil || receipts != 1 {
		t.Fatal("independent server acceptance missing", e)
	}
	// Force a fresh offline reconciliation after the original Run grant exists.
	if e = h.NewRuntimeSetup(svc, doc, *productionRuntimeAssets).Reconcile(ctx, c); e != nil {
		t.Fatalf("legitimate runtime-added grant blocked renewal: %v", e)
	}
	if _, e = h.QualifyLocalRuntime(ctx, svc, c, server.URL, request, installed); e == nil || calls.Load() != 1 {
		t.Fatal("consumed qualification retried")
	}
	command("session.send", projectID, sessionID, 1, 1, domain.Object{"text": "Return one synthetic source-test response.", "attachment_artifact_ids": domain.Empty(), "delivery": "NORMAL"})
	if e = c.Scan(ctx); e != nil {
		t.Fatal(e)
	}
	deadline := time.Now().Add(25 * time.Second)
	for time.Now().Before(deadline) {
		var settled int
		db.QueryRow(`SELECT count(*) FROM domain_objects WHERE kind='Run' AND json_extract(body,'$.status')='SETTLED'`).Scan(&settled)
		if settled == 2 {
			break
		}
		time.Sleep(50 * time.Millisecond)
	}
	if e = c.Close(); e != nil {
		t.Fatal(e)
	}
	var settled int
	if e = db.QueryRow(`SELECT count(*) FROM domain_objects WHERE kind='Run' AND json_extract(body,'$.status')='SETTLED'`).Scan(&settled); e != nil || settled != 2 || calls.Load() != 2 {
		t.Fatalf("normal qualified mu_turn not settled: runs=%d synthetic_calls=%d err=%v", settled, calls.Load(), e)
	}
	if e = h.NewRuntimeSetup(svc, doc, *productionRuntimeAssets).Reconcile(ctx, c); e != nil {
		t.Fatalf("normal turn grant blocked renewal: %v", e)
	}
	var unknown, changedMoney int
	if e = db.QueryRow(`SELECT count(*) FROM domain_objects WHERE kind='BudgetLedgerEntry' AND json_extract(body,'$.operation')='UNKNOWN' AND json_extract(body,'$.cost_basis')='UNKNOWN' AND json_type(body,'$.money')='null' AND json_type(body,'$.reservation_id')='null'`).Scan(&unknown); e != nil || unknown != 2 {
		t.Fatalf("original null-cost ledger missing: %d %v", unknown, e)
	}
	// The inventory bootstrap fixture has its own zero resource reservation;
	// inspect the original MODEL keys, not unrelated accounting entries.
	if e = db.QueryRow(`SELECT count(*) FROM domain_objects WHERE kind='BudgetLedgerEntry' AND json_extract(body,'$.provider_request_id') IN (SELECT effect_key FROM resource_effects WHERE json_extract(body,'$.payload.capability')='MODEL') AND (json_type(body,'$.money')<>'null' OR json_extract(body,'$.cost_basis')<>'UNKNOWN')`).Scan(&changedMoney); e != nil || changedMoney != 0 {
		t.Fatalf("unknown money rewritten: %d %v", changedMoney, e)
	}
	t.Log("SOURCE_FIXTURE actual_host=true actual_Mu_AppContainer=true independent_verifier_process=true explicit_service_root=true inherited_private_token=true token_revoked=true server_acceptance=PASS runtime=AVAILABLE exact_mu_turn_grant=true normal_turn=SETTLED synthetic_SSE_calls=2 real_model_calls=0 protected_holdout=false")
}
