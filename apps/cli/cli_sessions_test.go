package main

import (
	"bytes"
	"context"
	"crypto/sha256"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"

	"researchos.local/research-os/internal/api"
	"researchos.local/research-os/internal/canonical"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/store"
)

type cliSessionBindingFixture struct{ configuredRef *string }

func (p cliSessionBindingFixture) ValidateBinding(_ context.Context, _ *sql.Tx, _, _, _, model string) error {
	expected := "model-cli-fixture"
	if p.configuredRef != nil {
		expected = *p.configuredRef
	}
	if expected == "" || model != expected {
		return domain.Fail(422, "MODEL_UNAVAILABLE", "fixture model mismatch")
	}
	return nil
}
func (cliSessionBindingFixture) AdmitTurn(_ context.Context, _ *sql.Tx, _, _ string, _ domain.Object) error {
	return domain.Fail(503, "RESOURCE_UNAVAILABLE", "fixture has no LIVE runtime")
}

// Explicit SYNTHETIC metadata port for common HTTP transaction tests. It
// grants no runtime/model qualification and has no secret or provider access.
type cliConfigurationMetadataFixture struct{ principal string }

func (p cliConfigurationMetadataFixture) ConfigurationMetadata(_ context.Context, principal, provider string, credential *string) (domain.ClientConfigurationMetadata, error) {
	if principal != p.principal || credential != nil || (provider != "" && provider != "fixture-provider") {
		return domain.ClientConfigurationMetadata{}, domain.Fail(403, "FORBIDDEN", "synthetic metadata scope mismatch")
	}
	return domain.ClientConfigurationMetadata{OwnerHost: "host-111111111111", Principal: principal}, nil
}
func cliPostConfigurationFixture(c *v2Context, payload map[string]any) (string, error) {
	command := domain.ID()
	raw := domain.Bytes(domain.Object{"protocol_version": clientProtocol, "command_id": command, "client_id": c.clientID, "project_id": nil, "session_id": nil, "expected_revision": nil, "writer_epoch": nil, "method": "host.configure", "payload": payload})
	// Use the public typed HTTP contract directly. The legacy CLI configure
	// builder still requires a Session epoch; this fixture does not change it.
	request, e := http.NewRequest(http.MethodPost, c.baseURL+v2CommandPath, bytes.NewReader(raw))
	if e != nil {
		return "", e
	}
	request.Header.Set("Authorization", "Bearer "+c.credential)
	request.Header.Set("Content-Type", "application/json")
	response, e := (&http.Client{Timeout: 8 * time.Second}).Do(request)
	if e != nil {
		return "", e
	}
	defer response.Body.Close()
	body, e := io.ReadAll(io.LimitReader(response.Body, 1048577))
	if e != nil {
		return "", e
	}
	if evidence := os.Getenv("RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR"); evidence != "" {
		dir := filepath.Join(evidence, "typed-configure", command)
		if e = os.MkdirAll(dir, 0700); e != nil {
			return "", e
		}
		for name, data := range map[string][]byte{"request.json": raw, "response.json": body} {
			f, err := os.OpenFile(filepath.Join(dir, name), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
			if err != nil {
				return "", err
			}
			_, err = f.Write(data)
			closeErr := f.Close()
			if err != nil {
				return "", err
			}
			if closeErr != nil {
				return "", closeErr
			}
		}
	}
	if len(body) > 1048576 || response.StatusCode != 200 {
		return "", fmt.Errorf("typed configure HTTP%d bytes=%d", response.StatusCode, len(body))
	}
	strict, e := canonical.JSON(body)
	if e != nil {
		return "", e
	}
	var value any
	if e = json.Unmarshal(strict, &value); e != nil {
		return "", e
	}
	doc, e := api.ClientProtocolDocument()
	if e != nil {
		return "", e
	}
	if e = doc.ValidateDef("CommandResponse", value); e != nil {
		return "", e
	}
	var decoded domain.Response
	if e = json.Unmarshal(strict, &decoded); e != nil {
		return "", e
	}
	if e = domain.ValidateResultAgainstMethod("host.configure", &decoded, doc); e != nil {
		return "", e
	}
	if decoded.ProtocolVersion == nil || *decoded.ProtocolVersion != clientProtocol || decoded.CommandID == nil || *decoded.CommandID != command || decoded.Method == nil || *decoded.Method != "host.configure" || decoded.Status == nil || *decoded.Status != "COMPLETED" || decoded.SessionID != nil || decoded.Revision != nil {
		return "", fmt.Errorf("typed configure identity/status mismatch: status=%v error=%v", decoded.Status, decoded.ErrorCode)
	}
	ref := domain.Str(decoded.Result, "model_config_ref")
	if ref == "" {
		return "", fmt.Errorf("original ConfigureResult has no ref")
	}
	return ref, nil
}
func cliConfigureSessionFixture(t *testing.T, c *v2Context) string {
	t.Helper()
	ref, e := cliPostConfigurationFixture(c, map[string]any{"config_revision": 1, "provider_id": "fixture-provider", "base_url": "https://fixture.invalid/v1", "model_id": "fixture-model", "credential_ref": nil})
	if e != nil {
		t.Fatal("actual typed fixture configure", e)
	}
	return ref
}

func TestW14CLICommandsUseRealSessionHTTP(t *testing.T) {
	ctx := context.Background()
	db, err := store.Open(filepath.Join(t.TempDir(), "cli-sessions.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { db.Close() })
	if err = store.Bootstrap(ctx, db, "../../migrations/sqlite/0001_bootstrap.sql"); err != nil {
		t.Fatal(err)
	}
	svc, err := domain.New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if err != nil {
		t.Fatal(err)
	}
	raw, err := os.ReadFile("../../migrations/sqlite/next_v24_sessions.sql")
	if err != nil {
		t.Fatal(err)
	}
	if _, err = db.Exec(string(raw)); err != nil {
		t.Fatal(err)
	}
	if err = svc.ProvisionPrincipal(ctx, domain.Principal{ID: "cli-owner", Roles: []string{"OWNER"}, CanCreateProject: true}); err != nil {
		t.Fatal(err)
	}
	token, err := svc.IssueCredential(ctx, "cli-owner", time.Minute)
	if err != nil {
		t.Fatal(err)
	}
	var configuredRef string
	server := httptest.NewServer(api.HandlerWithConfigurationHost(db, t.TempDir(), svc, cliSessionBindingFixture{configuredRef: &configuredRef}, "", nil, nil, cliConfigurationMetadataFixture{"cli-owner"}))
	t.Cleanup(server.Close)
	profile := domain.Object{"name": "CLI session fixture", "intent": "one finite message", "facts": domain.Empty(), "accepted_scope": []any{"fixture"}, "constraints": domain.Empty(), "source_configs": domain.Empty(), "source_document_refs": domain.Empty(), "read_snapshot_ids": domain.Empty()}
	req, _ := http.NewRequest("POST", server.URL+"/v1/projects", bytes.NewReader(domain.Bytes(profile)))
	req.Header.Set("Authorization", "Bearer "+token)
	req.Header.Set("Idempotency-Key", domain.ID())
	resp, err := server.Client().Do(req)
	if err != nil {
		t.Fatal(err)
	}
	body, _ := io.ReadAll(resp.Body)
	resp.Body.Close()
	if resp.StatusCode != 201 {
		t.Fatalf("project: %s", body)
	}
	var project domain.Object
	json.Unmarshal(body, &project)
	pid := project["project_id"].(string)
	binding := domain.WorkspaceBinding{AuthorizedRef: "ws-cli", DisplayName: "fixture", DisplayPath: "fixture", RealPath: t.TempDir(), Access: "READ_ONLY", ProjectID: &pid, Revision: 1, Status: domain.WorkspaceActive, PrincipalID: "cli-owner", ClientID: "cli-client", HostPrincipalRef: "fixture-local-user", CreatedAt: domain.Now()}
	if _, err = db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('',?,?,1,?,0)`, domain.KindWorkspaceBinding, "ws-cli", string(domain.Bytes(binding))); err != nil {
		t.Fatal(err)
	}
	c := &v2Context{clientID: "cli-client", credential: token, projectID: pid, commandID: "cli-flow", baseURL: server.URL}
	configuredRef = cliConfigureSessionFixture(t, c)
	cfg := cliConfig{ProjectID: pid, WorkspaceRef: "ws-cli", Model: configuredRef}
	steps, reason, detail := verbSteps("run", []string{"answer this finite message"}, c, cfg)
	if reason != "" {
		t.Fatalf("%s %s", reason, detail)
	}
	if len(steps) != 3 || steps[0].method != "session.create" || steps[1].payload["delivery"] != "NORMAL" {
		t.Fatalf("invalid actual CLI steps: %+v", steps)
	}
	var final map[string]any
	var admitted map[string]any
	for _, step := range steps {
		c.commandID = domain.ID()
		reply, reason, code := v2Call(c, step.method, step.payload)
		if code != exitCompleted {
			t.Fatalf("%s: %s %v", step.method, reason, reply)
		}
		final = reply
		if step.method == "session.send" {
			admitted = cliSnapshot(reply)
		}
	}
	if c.sessionID == "" || c.epoch != 1 || c.revision < 4 {
		t.Fatalf("CLI did not adopt writer snapshot: %+v", c)
	}
	events := final["result"].(map[string]any)["events"].([]any)
	if len(events) != 4 || events[3].(map[string]any)["kind"] != "ERROR" {
		t.Fatalf("blocked runtime was not exposed: %v", events)
	}
	// The same real API/SQLite admission used above must not be presented as
	// completed execution merely because session.send returned COMPLETED.
	flow := &cliFlow{c: c, budget: ctx, base: "cli-observe-blocked", options: cliFollowOptions{
		timeout: time.Second, poll: time.Millisecond, cancelTimeout: time.Second, emit: func(map[string]any) {},
	}}
	if execution, code := followCLIExecution(flow, admitted, "", "", 0); code != exitNotImplemented || execution["reason"] != "TASK_BLOCKED" {
		t.Fatalf("blocked canonical Task became successful CLI execution: code=%d %v", code, execution)
	}
	var count int
	if err = db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Task'", pid).Scan(&count); err != nil || count != 1 {
		t.Fatalf("task count=%d err=%v", count, err)
	}
	steps, reason, _ = verbSteps("run", []string{"next message"}, c, cfg)
	if reason != "" || steps[0].method != "session.get" {
		t.Fatal("existing-session run must refresh its snapshot")
	}
	// A Desktop writer can take over a settled/blocked turn. The CLI resumes by
	// observing and reacquiring the same session, with no user-supplied epoch.
	desktop := &v2Context{clientID: "desktop-client", credential: token, projectID: pid, sessionID: c.sessionID,
		commandID: "desktop-takeover", baseURL: server.URL, revision: c.revision}
	if reply, why, code := v2Call(desktop, "session.attach", map[string]any{"after_sequence": 0, "request_write_owner": true}); code != 0 {
		t.Fatalf("desktop takeover: %s %v", why, reply)
	}
	steps, reason, _ = verbSteps("resume", []string{c.sessionID}, c, cfg)
	if reason != "" || len(steps) != 5 {
		t.Fatalf("resume requires manually supplied writer state: %s %+v", reason, steps)
	}
	c.commandID = "cli-resume-saved-context"
	for index, step := range steps {
		if step.method == "session.attach" && step.payload["request_write_owner"] == true {
			c.epoch = 0
		}
		c.commandID = v2FlowCommandID("cli-resume-saved-context", step.method, index)
		if reply, why, code := v2Call(c, step.method, step.payload); code != 0 {
			t.Fatalf("resume %s: %s %v", step.method, why, reply)
		}
	}
	if c.epoch != 3 {
		t.Fatalf("CLI failed to adopt its new host-assigned epoch: %d", c.epoch)
	}
	if err = db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Task'", pid).Scan(&count); err != nil || count != 1 {
		t.Fatalf("resume dispatched a task without a new user message: count=%d err=%v", count, err)
	}
	desktop.commandID, desktop.epoch = "desktop-stale-write", 2
	if reply, _, code := v2Call(desktop, "session.send", map[string]any{"text": "stale write", "attachment_artifact_ids": []any{}, "delivery": "NORMAL"}); code == 0 || reply["status"] != "REJECTED" {
		t.Fatalf("old desktop writer remained writable: %v", reply)
	}
}

func TestW14CLIRepeatedMessagesHaveDistinctStableCommands(t *testing.T) {
	base := "interactive-command"
	first := v2FlowCommandID(base, "session.send", 0)
	second := v2FlowCommandID(base, "session.send", 1)
	if first != base || first == second || second != v2FlowCommandID(base, "session.send", 1) || !commandIDPattern.MatchString(second) {
		t.Fatal("logical message command identity is not stable and distinct")
	}
}

// This fixture owns a disposable real API/SQLite chain. Metadata and runtime
// admission are explicitly synthetic; no native/model qualification is claimed.
func cliProtocolRealSession(t *testing.T, evidence string, create bool) (*sql.DB, *v2Context, cliConfig) {
	t.Helper()
	ctx := context.Background()
	db, err := store.Open(filepath.Join(evidence, "session.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() {
		if err := db.Close(); err != nil {
			t.Error(err)
		}
	})
	if err = store.Bootstrap(ctx, db, "../../migrations/sqlite/0001_bootstrap.sql"); err != nil {
		t.Fatal(err)
	}
	svc, err := domain.New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if err != nil {
		t.Fatal(err)
	}
	raw, err := os.ReadFile("../../migrations/sqlite/next_v24_sessions.sql")
	if err != nil {
		t.Fatal(err)
	}
	if _, err = db.Exec(string(raw)); err != nil {
		t.Fatal(err)
	}
	if err = svc.ProvisionPrincipal(ctx, domain.Principal{ID: "cli-owner", Roles: []string{"OWNER"}, CanCreateProject: true}); err != nil {
		t.Fatal(err)
	}
	token, err := svc.IssueCredential(ctx, "cli-owner", time.Minute)
	if err != nil {
		t.Fatal(err)
	}
	var configuredRef string
	server := httptest.NewServer(api.HandlerWithConfigurationHost(db, t.TempDir(), svc, cliSessionBindingFixture{configuredRef: &configuredRef}, "", nil, nil, cliConfigurationMetadataFixture{"cli-owner"}))
	t.Cleanup(server.Close)
	profile := domain.Object{"name": "CLI session fixture", "intent": "one finite message", "facts": domain.Empty(), "accepted_scope": []any{"fixture"}, "constraints": domain.Empty(), "source_configs": domain.Empty(), "source_document_refs": domain.Empty(), "read_snapshot_ids": domain.Empty()}
	req, _ := http.NewRequest("POST", server.URL+"/v1/projects", bytes.NewReader(domain.Bytes(profile)))
	req.Header.Set("Authorization", "Bearer "+token)
	req.Header.Set("Idempotency-Key", domain.ID())
	resp, err := server.Client().Do(req)
	if err != nil {
		t.Fatal(err)
	}
	body, _ := io.ReadAll(resp.Body)
	resp.Body.Close()
	if resp.StatusCode != 201 {
		t.Fatalf("project: %s", body)
	}
	var project domain.Object
	json.Unmarshal(body, &project)
	pid := project["project_id"].(string)
	binding := domain.WorkspaceBinding{AuthorizedRef: "ws-cli", DisplayName: "fixture", DisplayPath: "fixture", RealPath: t.TempDir(), Access: "READ_ONLY", ProjectID: &pid, Revision: 1, Status: domain.WorkspaceActive, PrincipalID: "cli-owner", ClientID: "cli-client", HostPrincipalRef: "fixture-local-user", CreatedAt: domain.Now()}
	if _, err = db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('',?,?,1,?,0)`, domain.KindWorkspaceBinding, "ws-cli", string(domain.Bytes(binding))); err != nil {
		t.Fatal(err)
	}
	c := &v2Context{clientID: "cli-client", credential: token, projectID: pid, commandID: "cli-flow", baseURL: server.URL}
	configuredRef = cliConfigureSessionFixture(t, c)
	cfg := cliConfig{ProjectID: pid, WorkspaceRef: "ws-cli", Model: configuredRef}

	if create {
		c.commandID = domain.ID()
		reply, reason, code := v2Call(c, "session.create", map[string]any{"workspace_ref": cfg.WorkspaceRef, "model_config_ref": cfg.Model, "title": "actual protocol ownership"})
		if code != 0 || statusOf(reply) != "COMPLETED" {
			t.Fatalf("real offline create: %d %s %v", code, reason, reply)
		}
		cfg.SessionID, cfg.Revision, cfg.WriterEpoch = c.sessionID, c.revision, c.epoch
	}
	return db, c, cfg
}

func TestCLIProtocolInteractiveAuthority(t *testing.T) {
	cliProtocolCreateNegativeControls(t)
	t.Run("new-two-multiline-turns", cliProtocolTwoMultilineTurns)
	for _, name := range []string{"real-existing-open-readonly", "real-existing-self-send", "real-new-created-owned-send", "fixture-foreign-writer", "fixture-expired-writer", "fixture-new-create-attach-send", "fixture-no-writer-attach-send", "fixture-list-other-item", "fixture-invalid-list", "fixture-slash-read-only"} {
		t.Run(name, func(t *testing.T) {
			if strings.HasPrefix(name, "real-") {
				root := os.Getenv("RESEARCHOS_CLI_PROTOCOL_EVIDENCE_DIR")
				if root == "" {
					t.Fatal("owned evidence required")
				}
				evidence := filepath.Join(root, strings.ReplaceAll(t.Name(), "/", "_"))
				if err := os.MkdirAll(evidence, 0700); err != nil {
					t.Fatal(err)
				}
				db, c, cfg := cliProtocolRealSession(t, evidence, name != "real-new-created-owned-send")
				// cliProtocolProcess uses a synthetic bearer for pure protocol probes. This
				// forwarding endpoint supplies only this fixture's newly issued credential.
				var mu sync.Mutex
				requests := []json.RawMessage{}
				requestBytes := [][]byte{}
				responses := [][]byte{}
				proxy := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
					raw, _ := io.ReadAll(r.Body)
					mu.Lock()
					requests = append(requests, append(json.RawMessage(nil), raw...))
					requestBytes = append(requestBytes, append([]byte(nil), raw...))
					mu.Unlock()
					req, _ := http.NewRequest(r.Method, c.baseURL+r.URL.RequestURI(), bytes.NewReader(raw))
					req.Header.Set("Authorization", "Bearer "+c.credential)
					req.Header.Set("Content-Type", "application/json")
					resp, err := http.DefaultClient.Do(req)
					if err != nil {
						http.Error(w, "fixture upstream unavailable", 500)
						return
					}
					defer resp.Body.Close()
					w.WriteHeader(resp.StatusCode)
					responseRaw, _ := io.ReadAll(resp.Body)
					mu.Lock()
					responses = append(responses, append([]byte(nil), responseRaw...))
					mu.Unlock()
					w.Write(responseRaw)
				}))
				defer proxy.Close()
				// The public Workspace fixture is bound to cli-client; override only the
				// fixture metadata at process setup, never product identity validation.
				t.Setenv("RESEARCHOS_CLI_PROTOCOL_CLIENT", "cli-client")
				input := ""
				expected := 0
				if name == "real-existing-self-send" || name == "real-new-created-owned-send" {
					input = "one actual durable message\n"
					expected = 3
				}
				code, out, _, _ := cliProtocolProcess(t, proxy.URL, cfg, input)
				mu.Lock()
				copyRequests := append([]json.RawMessage(nil), requests...)
				responseEvidence := append([][]byte(nil), responses...)
				requestEvidence := append([][]byte(nil), requestBytes...)
				mu.Unlock()
				encoded, _ := json.MarshalIndent(copyRequests, "", "  ")
				os.WriteFile(filepath.Join(evidence, "requests.json"), encoded, 0600)
				rawResponses, _ := json.MarshalIndent(responseEvidence, "", "  ")
				os.WriteFile(filepath.Join(evidence, "responses.base64.json"), rawResponses, 0600)
				wireRequests := make([]map[string]any, 0, len(requestEvidence))
				for _, raw := range requestEvidence {
					wireRequests = append(wireRequests, map[string]any{"raw_base64": raw, "bytes": len(raw), "sha256": fmt.Sprintf("%x", sha256.Sum256(raw))})
				}
				rawRequests, _ := json.MarshalIndent(wireRequests, "", "  ")
				os.WriteFile(filepath.Join(evidence, "requests.exact.json"), rawRequests, 0600)
				if code != expected {
					t.Fatalf("real API exit=%d expected=%d out=%s", code, expected, out)
				}
				sends, readonly := 0, 0
				for _, raw := range copyRequests {
					var env map[string]any
					json.Unmarshal(raw, &env)
					if env["method"] == "session.send" {
						sends++
					}
					if env["method"] == "session.attach" {
						if cliObject(env["payload"])["request_write_owner"] != false {
							t.Fatal("read/open acquired writer")
						}
						readonly++
					}
				}
				want := 0
				if name == "real-existing-self-send" || name == "real-new-created-owned-send" {
					want = 1
				}
				var tasks, journal int
				if err := db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Task'", cfg.ProjectID).Scan(&tasks); err != nil {
					t.Fatal(err)
				}
				if err := db.QueryRow("SELECT count(*) FROM idempotency WHERE operation='v2:session.send'").Scan(&journal); err != nil {
					t.Fatal(err)
				}
				wantRead := 1
				if name == "real-new-created-owned-send" {
					wantRead = 0
				}
				if sends != want || tasks != want || journal != want || readonly != wantRead {
					t.Fatalf("sends=%d tasks=%d journal=%d readonly=%d", sends, tasks, journal, readonly)
				}
				if want == 1 {
					var body []byte
					if err := db.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='Task'", cfg.ProjectID).Scan(&body); err != nil {
						t.Fatal(err)
					}
					var task map[string]any
					if json.Unmarshal(body, &task) != nil || task["status"] != "BLOCKED" {
						t.Fatal("actual Task not BLOCKED", string(body))
					}
					os.WriteFile(filepath.Join(evidence, "task.original.json"), body, 0600)
					savedRaw, err := os.ReadFile(filepath.Join(evidence, "config.after.json"))
					if err != nil {
						t.Fatal(err)
					}
					var saved cliConfig
					if json.Unmarshal(savedRaw, &saved) != nil || saved.SessionID == "" || saved.WriterEpoch != 1 {
						t.Fatal("validated original SID/epoch not persisted", string(savedRaw))
					}
					creates := 0
					for _, raw := range copyRequests {
						var env map[string]any
						json.Unmarshal(raw, &env)
						if env["method"] == "session.create" {
							creates++
						}
					}
					if name == "real-new-created-owned-send" && creates != 1 {
						t.Fatal("create not exactly once", creates)
					}
				}
				t.Logf("REAL_API synthetic admission only, durable sends=%d tasks=%d journal=%d CLI=%d", sends, tasks, journal, code)
				return
			}
			f := newCLIStreamFixture(t, "blocked")
			var requests []json.RawMessage
			var mu sync.Mutex
			acquired := false
			proxy := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				raw, _ := io.ReadAll(r.Body)
				var env map[string]any
				json.Unmarshal(raw, &env)
				mu.Lock()
				requests = append(requests, append(json.RawMessage(nil), raw...))
				mu.Unlock()
				method, _ := env["method"].(string)
				if method == "session.attach" && cliObject(env["payload"])["request_write_owner"] == true {
					acquired = true
				}
				if method == "session.list" && name == "fixture-list-other-item" {
					snap := f.snapshot()
					snap["session_id"] = "listed-other"
					json.NewEncoder(w).Encode(cliProtocolReplyFixture(env, "COMPLETED", map[string]any{"items": []any{snap}, "next_cursor": nil}, "", nil))
					return
				}
				if method == "session.list" && name == "fixture-invalid-list" {
					w.Write([]byte(`{"status":"COMPLETED"}`))
					return
				}
				if method == "session.get" && (name == "fixture-foreign-writer" || name == "fixture-expired-writer" || name == "fixture-no-writer-attach-send" && !acquired) {
					snap := f.snapshot()
					if name == "fixture-foreign-writer" {
						cliObject(snap["writer"])["client_id"] = "foreign"
					}
					if name == "fixture-expired-writer" {
						cliObject(snap["writer"])["expires_at"] = "2020-01-01T00:00:00Z"
					}
					if name == "fixture-no-writer-attach-send" {
						snap["writer"] = nil
					}
					json.NewEncoder(w).Encode(cliProtocolReplyFixture(env, "COMPLETED", snap, "", snap["revision"]))
					return
				}
				r.Body = io.NopCloser(bytes.NewReader(raw))
				f.serve(w, r)
			}))
			defer proxy.Close()
			cfg := cliConfig{ProjectID: "p1", SessionID: "s1", Revision: 5, WriterEpoch: 1, WorkspaceRef: "ws-fixture", Model: "fixed-model"}
			if name == "fixture-new-create-attach-send" || name == "fixture-list-other-item" {
				cfg.SessionID = ""
				cfg.Revision = 0
				cfg.WriterEpoch = 0
			}
			input := "one finite message\n"
			expected := 3
			if name == "fixture-invalid-list" {
				expected = 1
			}
			if name == "fixture-slash-read-only" {
				input = "/status\n"
				expected = 0
			}
			code, out, _, _ := cliProtocolProcess(t, proxy.URL, cfg, input)
			if code != expected {
				t.Fatalf("fixture CLI=%d expected=%d %s", code, expected, out)
			}
			mu.Lock()
			defer mu.Unlock()
			sends, acquires := 0, 0
			for _, raw := range requests {
				var env map[string]any
				json.Unmarshal(raw, &env)
				if env["method"] == "session.send" {
					sends++
				}
				if env["method"] == "session.attach" && cliObject(env["payload"])["request_write_owner"] == true {
					acquires++
				}
			}
			if name == "fixture-foreign-writer" || name == "fixture-expired-writer" || name == "fixture-invalid-list" || name == "fixture-slash-read-only" {
				if sends != 0 || acquires != 0 {
					t.Fatal("unexpected write", sends, acquires)
				}
			} else if sends != 1 || acquires != func() int {
				if name == "fixture-no-writer-attach-send" {
					return 1
				}
				return 0
			}() {
				t.Fatal("missing completion barrier/send", sends, acquires)
			}
		})
	}
}
