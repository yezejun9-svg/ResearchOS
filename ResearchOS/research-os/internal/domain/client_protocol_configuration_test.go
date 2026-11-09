package domain

import (
	"context"
	"database/sql"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"

	"researchos.local/research-os/internal/store"
)

// Explicit synthetic metadata boundary for transaction tests. Actual Windows
// Host/SID/metadata-only composition is exercised in separate Windows tests.
type handlerMetadataFixture struct{ principal string }

// This port observes the actual producer transaction and deliberately refuses
// execution afterward. It supplies no runtime qualification or worker result.
type handlerPendingPort struct {
	t                          *testing.T
	s                          *ClientService
	workspace, model, mutation string
	calls                      int
	proofErr                   error
	prepublication             bool
}

func (p *handlerPendingPort) ValidateBinding(_ context.Context, _ *sql.Tx, _, _, workspace, model string) error {
	if workspace != p.workspace || model != p.model {
		return Fail(503, "MODEL_UNAVAILABLE", "synthetic binding mismatch")
	}
	return nil
}
func (p *handlerPendingPort) ResolveGoalBinding(context.Context, *sql.Tx, string, string, string) (string, string, error) {
	return p.workspace, p.model, nil
}
func (p *handlerPendingPort) AdmitTurn(ctx context.Context, tx *sql.Tx, project, model string, task Object) error {
	p.calls++
	var published int
	if e := tx.QueryRow(`SELECT count(*) FROM client_sessions WHERE project_id=? AND task_id=?`, project, task["id"]).Scan(&published); e != nil {
		return e
	}
	p.prepublication = published == 0
	if original, ok := ctx.Value(pendingClientCommandKey{}).(*pendingClientCommand); ok {
		copy := *original
		switch p.mutation {
		case "no-context":
			ctx = context.Background()
		case "wrong-tx":
			copy.tx = nil
		case "wrong-principal":
			copy.principal = "other-principal"
		case "wrong-hash":
			copy.hash = "sha256:other"
		case "wrong-raw":
			copy.raw = []byte(`{}`)
		case "existing-task":
			copy.entry = map[string]map[string]bool{}
			for kind, ids := range original.entry {
				copy.entry[kind] = map[string]bool{}
				for id, v := range ids {
					copy.entry[kind][id] = v
				}
			}
			copy.entry["Task"][Str(task, "id")] = true
		case "changed-task":
			changed := Object{}
			for key, value := range task {
				changed[key] = value
			}
			changed["title"] = "different task body"
			task = changed
		}
		if p.mutation != "no-context" {
			ctx = context.WithValue(ctx, pendingClientCommandKey{}, &copy)
		}
	}
	_, _, p.proofErr = p.s.pendingClientTask(ctx, tx, project, model, task)
	return Fail(503, "RESOURCE_UNAVAILABLE", "synthetic admission observation; no runtime qualification")
}

func TestHandlerPendingProducerTransaction(t *testing.T) {
	for _, mode := range []string{"normal", "project-goal", "session-goal", "draft", "no-context", "wrong-tx", "wrong-principal", "wrong-hash", "wrong-raw", "existing-task", "changed-task"} {
		t.Run(mode, func(t *testing.T) {
			f := contextFixture(t)
			s, sid, model := handlerTypedSession(t, f, "pending-client")
			var workspace string
			if e := f.db.QueryRow(`SELECT workspace_ref FROM client_sessions WHERE id=?`, sid).Scan(&workspace); e != nil {
				t.Fatal(e)
			}
			p := &handlerPendingPort{t: t, s: s, workspace: workspace, model: model}
			s.SessionRuntime = p
			env := &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("pending-client"), ProjectID: &f.project, SessionID: &sid, ExpectedRevision: revPtr(1), WriterEpoch: revPtr(1), Method: strptr("session.send"), Payload: Bytes(Object{"text": "one exact pending objective", "attachment_artifact_ids": Empty(), "delivery": "NORMAL"})}
			goal := mode == "project-goal" || mode == "session-goal" || mode == "draft"
			if goal {
				env.Method = strptr("goal.start")
				env.Payload = Bytes(Object{"objective": "one exact pending objective", "contract_artifact_ids": Empty(), "start_as_draft": mode == "draft"})
				if mode != "session-goal" {
					env.SessionID = nil
					env.ExpectedRevision = nil
					env.WriterEpoch = nil
				}
			} else if mode != "normal" {
				p.mutation = mode
			}
			r, replay := handlerCommand(t, f, s, env)
			if replay || deref(r.Status) != "COMPLETED" {
				t.Fatalf("producer did not preserve completed/blocked semantics: %s", Bytes(r))
			}
			if mode == "draft" {
				if p.calls != 0 {
					t.Fatal("draft obtained admission context")
				}
				return
			}
			if p.calls != 1 || !p.prepublication {
				t.Fatalf("not the real pre-publication producer: calls=%d before=%v", p.calls, p.prepublication)
			}
			if p.mutation == "" && p.proofErr != nil {
				t.Fatalf("original producer rejected: %v", p.proofErr)
			}
			if p.mutation != "" && p.proofErr == nil {
				t.Fatal("changed pending evidence accepted")
			}
			var tasks, runs, journals int
			f.db.QueryRow(`SELECT count(*) FROM domain_objects WHERE project=? AND kind='Task' AND json_extract(body,'$.status')='BLOCKED'`, f.project).Scan(&tasks)
			f.db.QueryRow(`SELECT count(*) FROM domain_objects WHERE project=? AND kind='Run'`, f.project).Scan(&runs)
			f.db.QueryRow(`SELECT count(*) FROM idempotency WHERE key=?`, deref(env.CommandID)).Scan(&journals)
			if tasks != 1 || runs != 0 || journals != 1 {
				t.Fatalf("durable outcome task/run/journal=%d/%d/%d", tasks, runs, journals)
			}
			r2, replayed := handlerCommand(t, f, s, env)
			if !replayed || string(Bytes(r2)) != string(Bytes(r)) || p.calls != 1 {
				t.Fatal("original replay repeated producer")
			}
		})
	}
}

func TestHandlerScopedConfigurationRetainsOriginalTaskSettlement(t *testing.T) {
	for _, hidden := range []bool{false, true} {
		t.Run(fmt.Sprint(hidden), func(t *testing.T) {
			f := contextFixture(t)
			s, sid, model := handlerTypedSession(t, f, "pending-client")
			var workspace string
			f.db.QueryRow(`SELECT workspace_ref FROM client_sessions WHERE id=?`, sid).Scan(&workspace)
			port := &handlerPendingPort{t: t, s: s, workspace: workspace, model: model}
			s.SessionRuntime = port
			send := &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("pending-client"), ProjectID: &f.project, SessionID: &sid, ExpectedRevision: revPtr(1), WriterEpoch: revPtr(1), Method: strptr("session.send"), Payload: Bytes(Object{"text": "bounded unfinished task", "attachment_artifact_ids": Empty(), "delivery": "NORMAL"})}
			r, _ := handlerCommand(t, f, s, send)
			if deref(r.Status) != "COMPLETED" || port.proofErr != nil {
				t.Fatalf("producer: %s %v", Bytes(r), port.proofErr)
			}
			var taskID string
			if e := f.db.QueryRow(`SELECT task_id FROM client_sessions WHERE id=?`, sid).Scan(&taskID); e != nil {
				t.Fatal(e)
			}
			if hidden {
				if _, e := f.db.Exec(`UPDATE client_sessions SET task_id=NULL WHERE id=?`, sid); e != nil {
					t.Fatal(e)
				}
			}
			var rev int64
			f.db.QueryRow(`SELECT revision FROM client_sessions WHERE id=?`, sid).Scan(&rev)
			configure := handlerDefaultEnvelope(2)
			configure.ClientID = strptr("pending-client")
			configure.ProjectID = &f.project
			configure.SessionID = &sid
			configure.ExpectedRevision = &rev
			configure.WriterEpoch = revPtr(1)
			r, _ = handlerCommand(t, f, s, configure)
			if deref(r.Status) != "REJECTED" || deref(r.ErrorCode) != "SESSION_BUSY" {
				t.Fatalf("unsettled original task was hidden: %s", Bytes(r))
			}
			sourceTx(t, f.db, func(tx *sql.Tx) error {
				task, e := load(tx, f.project, "Task", taskID)
				if e != nil {
					return e
				}
				owner, e := clientPrincipal(context.Background(), tx, f.owner, f.project, true)
				if e != nil {
					return e
				}
				_, e = f.s.controlTask(tx, owner, f.project, task, Object{"action": "CANCEL", "reason": "fixture noRun cancellation"}, ID())
				return e
			})
			var oldTask string
			f.db.QueryRow(`SELECT body FROM domain_objects WHERE project=? AND kind='Task' AND id=?`, f.project, taskID).Scan(&oldTask)
			configure.CommandID = strptr(ID())
			r, _ = handlerCommand(t, f, s, configure)
			if deref(r.Status) != "COMPLETED" {
				t.Fatalf("settled noRun task could not rebind: %s", Bytes(r))
			}
			var currentTask string
			f.db.QueryRow(`SELECT body FROM domain_objects WHERE project=? AND kind='Task' AND id=?`, f.project, taskID).Scan(&currentTask)
			if oldTask != currentTask {
				t.Fatal("rebind changed original task")
			}
			configurationEvidenceSnapshot(t, f.db, "handler-noRun-settlement-"+fmt.Sprint(hidden))
		})
	}
}

func (m handlerMetadataFixture) ConfigurationMetadata(_ context.Context, p, provider string, ref *string) (ClientConfigurationMetadata, error) {
	if p != m.principal {
		return ClientConfigurationMetadata{}, Fail(403, "FORBIDDEN", "fixture principal mismatch")
	}
	r := ClientConfigurationMetadata{OwnerHost: configurationFixtureOwner, Principal: p}
	if ref != nil {
		r.Credential = &ClientCredentialMetadata{Ref: *ref, Provider: provider, Kind: "API_KEY", Status: "AVAILABLE", CheckedAt: Now()}
	}
	return r, nil
}
func handlerDecode(t *testing.T, env *Envelope) *Envelope {
	t.Helper()
	raw := Bytes(env)
	e, err := DecodeEnvelope(raw)
	if err != nil {
		t.Fatal(err)
	}
	return e
}
func handlerCommand(t *testing.T, f *fixture, s *ClientService, env *Envelope) (*Response, bool) {
	t.Helper()
	env = handlerDecode(t, env)
	var r *Response
	var replay bool
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		var e error
		r, replay, e = s.Execute(context.Background(), tx, env, f.owner)
		return e
	})
	return r, replay
}
func handlerTypedSession(t *testing.T, f *fixture, client string) (*ClientService, string, string) {
	t.Helper()
	doc := configurationSchema(t)
	s := &ClientService{Doc: doc, Domain: f.s, ConfigurationAuthority: handlerMetadataFixture{f.owner}, Host: ClientHostInfo{InstanceID: configurationFixtureOwner, CoreBuildID: "handler-fixture", LeaseTTL: time.Hour}}
	var head int64
	if err := f.db.QueryRow(`SELECT COALESCE(MAX(current_revision),0) FROM host_model_config_heads WHERE owner_host_ref=? AND principal=?`, configurationFixtureOwner, f.owner).Scan(&head); err != nil {
		t.Fatal(err)
	}
	configure := &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: &client, Method: strptr("host.configure"), Payload: Bytes(Object{"config_revision": head + 1, "provider_id": "fixture-provider", "base_url": "https://fixture.invalid/v1", "model_id": "fixture-model", "credential_ref": nil})}
	r, _ := handlerCommand(t, f, s, configure)
	if deref(r.Status) != "COMPLETED" {
		t.Fatalf("configure: %s", Bytes(r))
	}
	ref := Str(r.Result, "model_config_ref")
	workspace := "handler-workspace-" + ID()
	b := WorkspaceBinding{AuthorizedRef: workspace, DisplayName: "handler fixture", DisplayPath: "fixture", RealPath: t.TempDir(), Access: "READ_ONLY", ProjectID: &f.project, Revision: 1, Status: WorkspaceActive, PrincipalID: f.owner, ClientID: client, HostPrincipalRef: "SYNTHETIC-METADATA", CreatedAt: Now()}
	if _, e := f.db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('',?,?,1,?,0)`, KindWorkspaceBinding, workspace, string(Bytes(b))); e != nil {
		t.Fatal(e)
	}
	create := &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: &client, ProjectID: &f.project, Method: strptr("session.create"), Payload: Bytes(Object{"workspace_ref": workspace, "model_config_ref": ref, "title": "handler fixture"})}
	r, _ = handlerCommand(t, f, s, create)
	if deref(r.Status) != "COMPLETED" {
		t.Fatalf("offline create: %s", Bytes(r))
	}
	return s, deref(r.SessionID), ref
}

func TestHandlerOriginalHeaderExactBytesAndCorruption(t *testing.T) {
	doc := configurationSchema(t)
	raw, _ := configurationEnvelope(t, doc, "header-original", 1)
	raw = append([]byte(" \n"), raw...)
	env, e := DecodeEnvelope(raw)
	if e != nil {
		t.Fatal(e)
	}
	h, e := writeClientCommandEnvelope(doc, env)
	if e != nil {
		t.Fatal(e)
	}
	r, known, e := readClientCommandEnvelope(doc, h)
	if e != nil || !known || string(r.env.originalRaw) != string(raw) {
		t.Fatalf("raw mismatch: %v", e)
	}
	var value map[string]any
	if e = json.Unmarshal([]byte(h), &value); e != nil {
		t.Fatal(e)
	}
	for _, name := range []string{"unknown", "newline-base64", "unpadded", "wrong-encoding", "outer-space", "duplicate", "oversize"} {
		t.Run(name, func(t *testing.T) {
			var v map[string]any
			json.Unmarshal([]byte(h), &v)
			bad := ""
			switch name {
			case "unknown":
				v["extra"] = true
			case "newline-base64":
				v["raw_envelope_base64"] = base64.StdEncoding.EncodeToString(raw) + "\n"
			case "unpadded":
				v["raw_envelope_base64"] = strings.TrimRight(base64.StdEncoding.EncodeToString(raw), "=")
			case "wrong-encoding":
				v["encoding"] = "raw"
			case "outer-space":
				bad = " " + h
			case "duplicate":
				bad = strings.Replace(h, "{", "{\"schema\":\"other\",", 1)
			case "oversize":
				bad = strings.Repeat(" ", clientCommandHeaderMax+1)
			}
			if bad == "" {
				bad = string(Bytes(v))
			}
			if _, _, e = readClientCommandEnvelope(doc, bad); e == nil {
				t.Fatal("corrupt header accepted")
			}
		})
	}
}

func TestHandlerEndpointLexicalMapping(t *testing.T) {
	for _, base := range []string{"https://fixture.invalid", "https://Fixture.INVALID/", "https://fixture.invalid/v1/", "https://fixture.invalid:00443/v1", "https://127.0.0.1:8443/v1", "https://[::1]:8443/v1", "https://xn--bcher-kva.example/v1"} {
		if got, e := clientConfigurationEndpoint(base, nil); e != nil || got != strings.TrimSuffix(base, "/")+"/chat/completions" {
			t.Errorf("%s: %s %v", base, got, e)
		}
	}
	for _, base := range []string{"HTTPS://fixture.invalid", "http://fixture.invalid", "https://fixture.invalid:", "https://fixture.invalid:0", "https://fixture.invalid:65536", "https://fixture.invalid:+443", "https://::1/v1", "https://[fe80::1%25eth0]/v1", "https://书.example/v1", "https://user@fixture.invalid/v1", "https://fixture.invalid/v1?", "https://fixture.invalid/v1#", "https://fixture.invalid/v1//", "https://fixture.invalid/%76%31", "https://fixture.invalid/a/../v1", "https://fixture.invalid/CHAT/Completions/"} {
		if _, e := clientConfigurationEndpoint(base, nil); e == nil {
			t.Errorf("accepted %s", base)
		}
	}
	for _, base := range []string{"http://127.0.0.1:11434/v1", "http://[::1]:11434/v1"} {
		got, e := clientConfigurationEndpoint(base, nil)
		if e != nil || got != base+"/chat/completions" || !clientConfigurationLoopbackModelEndpoint(got) {
			t.Errorf("local %s: %s %v", base, got, e)
		}
		credential := "cred-fixture-api_key-1234567890-12345678-12345678"
		if _, e := clientConfigurationEndpoint(base, &credential); e == nil {
			t.Errorf("local credential accepted: %s", base)
		}
	}
	for _, base := range []string{"http://localhost:11434/v1", "http://127.1:11434/v1", "http://127.000.0.1:11434/v1", "http://2130706433:11434/v1", "http://0.0.0.0:11434/v1", "http://192.168.1.1:11434/v1", "http://[::ffff:127.0.0.1]:11434/v1", "http://[::1%25eth0]:11434/v1", "http://user@127.0.0.1:11434/v1", "http://127.0.0.1:11434/%76%31", "http://127.0.0.1:11434/v1?x=1"} {
		if _, e := clientConfigurationEndpoint(base, nil); e == nil {
			t.Errorf("unsafe local URL accepted: %s", base)
		}
	}
}

func TestHandlerOfflineTypedSessionAndScopedRebind(t *testing.T) {
	f := contextFixture(t)
	s, sid, old := handlerTypedSession(t, f, "config-client")
	env := &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("config-client"), ProjectID: &f.project, SessionID: &sid, ExpectedRevision: revPtr(1), WriterEpoch: revPtr(1), Method: strptr("host.configure"), Payload: Bytes(Object{"config_revision": 2, "provider_id": "fixture-provider", "base_url": "https://fixture.invalid/v1", "model_id": "new-model", "credential_ref": nil})}
	r, replay := handlerCommand(t, f, s, env)
	if deref(r.Status) != "COMPLETED" || replay || r.Revision == nil || *r.Revision != 2 || Str(r.Result, "model_config_ref") == old {
		t.Fatalf("scoped: %s", Bytes(r))
	}
	first := string(Bytes(r))
	r, replay = handlerCommand(t, f, s, env)
	if !replay || string(Bytes(r)) != first {
		t.Fatal("scoped replay changed")
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		_, e := readClientConfiguration(context.Background(), tx, s.Doc, configurationFixtureOwner, f.owner, old)
		return e
	})
	var runs, watermark int
	if e := f.db.QueryRow(`SELECT count(*) FROM domain_objects WHERE kind='Run'`).Scan(&runs); e != nil {
		t.Fatal(e)
	}
	f.db.QueryRow(`SELECT event_watermark FROM client_sessions WHERE id=?`, sid).Scan(&watermark)
	if runs != 0 || watermark != 0 {
		t.Fatalf("save/create caused execution or events: %d %d", runs, watermark)
	}
}

func handlerDefaultEnvelope(revision int64) *Envelope {
	return &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("config-client"), Method: strptr("host.configure"), Payload: Bytes(Object{"config_revision": revision, "provider_id": "fixture-provider", "base_url": "https://fixture.invalid/v1", "model_id": "fixture-model", "credential_ref": nil})}
}

func TestHandlerStrictScopesAndRaw(t *testing.T) {
	valid := string(Bytes(handlerDefaultEnvelope(1)))
	for name, raw := range map[string]string{
		"missing-null":  strings.Replace(valid, `"writer_epoch":null,`, "", 1),
		"partial-scope": strings.Replace(valid, `"project_id":null`, `"project_id":"project"`, 1),
		"duplicate":     strings.Replace(valid, "{", `{"method":"host.status",`, 1),
		"unknown":       strings.Replace(valid, "{", `{"not_contract":true,`, 1),
		"zero-revision": strings.Replace(valid, `"config_revision":1`, `"config_revision":0`, 1),
		"invalid-utf8":  valid + string([]byte{255}),
	} {
		t.Run(name, func(t *testing.T) {
			env, e := DecodeEnvelope([]byte(raw))
			if e == nil {
				_, e = validateClientIdentityRequest(configurationSchema(t), []byte(raw), env)
			}
			if e == nil {
				t.Fatal("invalid original request accepted")
			}
		})
	}
}

func TestHandlerGlobalIdentityCASAndFirstRaw(t *testing.T) {
	f := contextFixture(t)
	s := &ClientService{Doc: configurationSchema(t), Domain: f.s, ConfigurationAuthority: handlerMetadataFixture{f.owner}}
	env := handlerDefaultEnvelope(1)
	raw := append([]byte(" \n"), Bytes(env)...)
	first, e := DecodeEnvelope(raw)
	if e != nil {
		t.Fatal(e)
	}
	var r *Response
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		var err error
		r, _, err = s.Execute(context.Background(), tx, first, f.owner)
		return err
	})
	if deref(r.Status) != "COMPLETED" {
		t.Fatal(string(Bytes(r)))
	}
	var body, headers, at string
	if e = f.db.QueryRow(`SELECT body,headers,created_at FROM idempotency WHERE key=?`, *env.CommandID).Scan(&body, &headers, &at); e != nil {
		t.Fatal(e)
	}
	stored, known, e := readClientCommandEnvelope(s.Doc, headers)
	if e != nil || !known || string(stored.env.originalRaw) != string(raw) {
		t.Fatal("first raw not retained", e)
	}
	replayed, replay := handlerCommand(t, f, s, env)
	if !replay || string(Bytes(replayed)) != body {
		t.Fatal("semantic retry changed original response")
	}
	var nextHeaders, nextAt string
	f.db.QueryRow(`SELECT headers,created_at FROM idempotency WHERE key=?`, *env.CommandID).Scan(&nextHeaders, &nextAt)
	if headers != nextHeaders || at != nextAt {
		t.Fatal("retry rewrote original proof")
	}
	conflict := handlerDecode(t, &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: env.CommandID, ClientID: env.ClientID, Method: strptr("host.status"), Payload: Bytes(Object{})})
	tx, e := f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	_, _, e = s.Execute(context.Background(), tx, conflict, f.owner)
	tx.Rollback()
	if e != ErrIdemConflict {
		t.Fatalf("cross-method identity conflict: %v", e)
	}
	stale := handlerDefaultEnvelope(1)
	r, _ = handlerCommand(t, f, s, stale)
	if deref(r.Status) != "REJECTED" || r.Error.Code != "CONFIG_CONFLICT" {
		t.Fatalf("stale CAS: %s", Bytes(r))
	}
	var configs, identities, journals int
	f.db.QueryRow(`SELECT count(*) FROM host_model_configurations`).Scan(&configs)
	f.db.QueryRow(`SELECT count(*) FROM client_command_identities`).Scan(&identities)
	f.db.QueryRow(`SELECT count(*) FROM idempotency WHERE operation LIKE 'v2:%'`).Scan(&journals)
	if configs != 1 || identities != 2 || journals != 2 {
		t.Fatalf("transaction counts=%d/%d/%d", configs, identities, journals)
	}
}

func TestHandlerStatusBoundedCompleteHistory(t *testing.T) {
	f := contextFixture(t)
	s := &ClientService{Doc: configurationSchema(t), Domain: f.s, ConfigurationAuthority: handlerMetadataFixture{f.owner}, Host: ClientHostInfo{InstanceID: configurationFixtureOwner, CoreBuildID: "fixture", OperatingMode: "LOCAL_USER_HOST"}}
	refs := []string{}
	for i := 0; i <= 201; i++ {
		if i > 0 {
			r, _ := handlerCommand(t, f, s, handlerDefaultEnvelope(int64(i)))
			if deref(r.Status) != "COMPLETED" {
				t.Fatal(string(Bytes(r)))
			}
			refs = append(refs, Str(r.Result, "model_config_ref"))
		}
		if i != 0 && i != 1 && i != 99 && i != 100 && i != 101 && i != 201 {
			continue
		}
		t.Run(fmt.Sprint(i), func(t *testing.T) {
			r, _ := handlerCommand(t, f, s, &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("config-client"), Method: strptr("host.status"), Payload: Bytes(Object{})})
			if deref(r.Status) != "COMPLETED" || Str(r.Result, "authenticated_principal_ref") != f.owner {
				t.Fatal(string(Bytes(r)))
			}
			items := Arr(r.Result, "model_configurations")
			want := i
			if want > 100 {
				want = 100
			}
			if len(items) != want {
				t.Fatalf("items %d want %d", len(items), want)
			}
			if i > 0 && Str(items[0].(map[string]any), "model_config_ref") != refs[i-1] {
				t.Fatal("head not first")
			}
			if len(Arr(r.Result, "credentials")) != 0 {
				t.Fatal("null credential invented")
			}
		})
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		_, e := readClientConfiguration(context.Background(), tx, s.Doc, configurationFixtureOwner, f.owner, refs[0])
		return e
	})
	// Mutate an old row outside the 100 projected entries in this hostile-copy
	// fixture. Full-history validation must still refuse the bounded status.
	configurationBackupMutation(t, f.db, `UPDATE host_model_configurations SET canonical_config_json=json_set(canonical_config_json,'$.model_id','tampered') WHERE config_revision=1`)
	tx, e := f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	_, _, _, e = s.clientConfigurationStatus(context.Background(), tx, f.owner)
	tx.Rollback()
	if e == nil {
		t.Fatal("hidden historical corruption accepted")
	}
}

func TestHandlerStatusCredentialDedupAndLegacyReplay(t *testing.T) {
	f := contextFixture(t)
	s := &ClientService{Doc: configurationSchema(t), Domain: f.s, ConfigurationAuthority: handlerMetadataFixture{f.owner}, Host: ClientHostInfo{InstanceID: configurationFixtureOwner, CoreBuildID: "fixture"}}
	credential := "cred-fixture-api_key-1234567890-12345678-12345678"
	for i := int64(1); i <= 3; i++ {
		e := handlerDefaultEnvelope(i)
		e.Payload = Bytes(Object{"config_revision": i, "provider_id": "fixture-provider", "base_url": "https://fixture.invalid/v1", "model_id": "fixture-model", "credential_ref": credential})
		r, _ := handlerCommand(t, f, s, e)
		if deref(r.Status) != "COMPLETED" {
			t.Fatal(string(Bytes(r)))
		}
	}
	env := handlerDecode(t, &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("status-client"), Method: strptr("host.status"), Payload: Bytes(Object{})})
	r, _ := handlerCommand(t, f, s, env)
	if len(Arr(r.Result, "credentials")) != 1 || len(Arr(r.Result, "model_configurations")) != 3 {
		t.Fatal("credential projection was not deduplicated")
	}
	if e := validateBackupHostConfiguration(f.db); e != nil {
		t.Fatal(e)
	}
	// Explicit legacy-row fixture. This tests replay compatibility, not an
	// actual historical Host or provider qualification.
	r.Result["authenticated_principal_ref"] = "principal:" + f.owner
	oldBody := string(Bytes(r))
	configurationBackupMutation(t, f.db, `DELETE FROM client_command_identities WHERE command_id=?`, deref(env.CommandID))
	configurationBackupMutation(t, f.db, `UPDATE idempotency SET headers='{}',body=? WHERE key=?`, oldBody, deref(env.CommandID))
	r2, replay := handlerCommand(t, f, s, env)
	if !replay || string(Bytes(r2)) != oldBody {
		t.Fatal("legacy status replay changed original bytes")
	}
	var n int
	var h string
	f.db.QueryRow(`SELECT count(*) FROM client_command_identities WHERE command_id=?`, deref(env.CommandID)).Scan(&n)
	f.db.QueryRow(`SELECT headers FROM idempotency WHERE key=?`, deref(env.CommandID)).Scan(&h)
	if n != 0 || h != "{}" {
		t.Fatal("legacy replay backfilled identity/header")
	}
	configurationEvidenceSnapshot(t, f.db, "handler-legacy-status-replay")
}

func TestHandlerUnanchoredLegacyReadAndExplicitRebind(t *testing.T) {
	f := contextFixture(t)
	s, typedSID, _ := handlerTypedSession(t, f, "pending-client")
	var workspace string
	f.db.QueryRow(`SELECT workspace_ref FROM client_sessions WHERE id=?`, typedSID).Scan(&workspace)
	// A trusted runtime unit port can supply a legacy creation binding. It
	// cannot supply historical profile evidence or an exemption from PC01.
	legacy := "mc-old-unanchored-fixture"
	p := &handlerPendingPort{t: t, s: s, workspace: workspace, model: legacy}
	s.SessionRuntime = p
	created, _ := handlerCommand(t, f, s, &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("pending-client"), ProjectID: &f.project, Method: strptr("session.create"), Payload: Bytes(Object{"workspace_ref": workspace, "model_config_ref": legacy, "title": "explicit legacy unit fixture"})})
	if deref(created.Status) != "COMPLETED" {
		t.Fatal(string(Bytes(created)))
	}
	sid := deref(created.SessionID)
	read, _ := handlerCommand(t, f, s, &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("pending-client"), ProjectID: &f.project, SessionID: &sid, Method: strptr("session.get"), Payload: Bytes(Object{})})
	if deref(read.Status) != "COMPLETED" {
		t.Fatal("legacy read blocked")
	}
	refused, _ := handlerCommand(t, f, s, &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("pending-client"), ProjectID: &f.project, SessionID: &sid, ExpectedRevision: revPtr(1), WriterEpoch: revPtr(1), Method: strptr("session.send"), Payload: Bytes(Object{"text": "must not infer a historical profile", "attachment_artifact_ids": Empty(), "delivery": "NORMAL"})})
	if deref(refused.Status) != "REJECTED" || deref(refused.ErrorCode) != "MODEL_UNAVAILABLE" || p.calls != 0 {
		t.Fatalf("legacy execution fabricated qualification: %s", Bytes(refused))
	}
	rebind := handlerDefaultEnvelope(2)
	rebind.ClientID = strptr("pending-client")
	rebind.ProjectID = &f.project
	rebind.SessionID = &sid
	rebind.ExpectedRevision = revPtr(1)
	rebind.WriterEpoch = revPtr(1)
	configured, _ := handlerCommand(t, f, s, rebind)
	if deref(configured.Status) != "COMPLETED" {
		t.Fatalf("authorized noRun rebind refused: %s", Bytes(configured))
	}
	newref := Str(configured.Result, "model_config_ref")
	configurationBackupMutation(t, f.db, `DELETE FROM host_model_configurations WHERE model_config_ref=?`, newref)
	// The previous legacy identity must not survive rebinding as a permanent
	// bypass when the new typed row is subsequently missing.
	tx, e := f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	sess, e := loadClientSession(context.Background(), tx, sid, f.project)
	if e == nil {
		e = s.validateSessionConfiguration(context.Background(), tx, f.owner, sess, false)
	}
	tx.Rollback()
	if e == nil {
		t.Fatal("typed-rebound Session fell back to legacy")
	}
}

func TestHandlerCreateNeverSuppliesImplicitModel(t *testing.T) {
	f := contextFixture(t)
	s, sid, _ := handlerTypedSession(t, f, "config-client")
	var workspace string
	f.db.QueryRow(`SELECT workspace_ref FROM client_sessions WHERE id=?`, sid).Scan(&workspace)
	for _, model := range []any{nil, "", 123} {
		raw := Bytes(&Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("config-client"), ProjectID: &f.project, Method: strptr("session.create"), Payload: Bytes(Object{"workspace_ref": workspace, "model_config_ref": model, "title": "invalid model"})})
		if _, e := decodeClientIdentityEnvelope(s.Doc, raw); e == nil {
			t.Fatalf("invalid model %v normalized into default", model)
		}
	}
	raw := Bytes(&Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("config-client"), ProjectID: &f.project, Method: strptr("session.create"), Payload: Bytes(Object{"workspace_ref": workspace, "title": "missing model"})})
	if _, e := decodeClientIdentityEnvelope(s.Doc, raw); e == nil {
		t.Fatal("missing model filled from head")
	}
	var n int
	f.db.QueryRow(`SELECT count(*) FROM client_sessions`).Scan(&n)
	if n != 1 {
		t.Fatal("invalid create mutated sessions")
	}
}

func TestHandlerScopedFencesAndNoHistoricalRebind(t *testing.T) {
	for _, name := range []string{"stale-revision", "stale-epoch", "wrong-writer", "expired-lease", "archived", "sealed", "changed-model", "missing-creation", "missing-typed-row"} {
		t.Run(name, func(t *testing.T) {
			f := contextFixture(t)
			s, sid, ref := handlerTypedSession(t, f, "config-client")
			env := handlerDefaultEnvelope(2)
			env.ProjectID = &f.project
			env.SessionID = &sid
			env.ExpectedRevision = revPtr(1)
			env.WriterEpoch = revPtr(1)
			switch name {
			case "stale-revision":
				env.ExpectedRevision = revPtr(2)
			case "stale-epoch":
				env.WriterEpoch = revPtr(2)
			case "wrong-writer":
				env.ClientID = strptr("other-client")
			case "expired-lease":
				f.db.Exec(`UPDATE client_sessions SET lease_expires_at='2000-01-01T00:00:00Z' WHERE id=?`, sid)
			case "archived":
				if _, e := f.db.Exec(`UPDATE client_sessions SET archived_at=? WHERE id=?`, Now(), sid); e != nil {
					t.Fatal(e)
				}
			case "sealed":
				if _, e := f.db.Exec(`UPDATE client_sessions SET sealed_at=? WHERE id=?`, Now(), sid); e != nil {
					t.Fatal(e)
				}
			case "changed-model":
				f.db.Exec(`UPDATE client_sessions SET model_config_ref='foreign-ref' WHERE id=?`, sid)
			case "missing-creation":
				configurationBackupMutation(t, f.db, `DELETE FROM idempotency WHERE operation='v2:session.create'`)
			case "missing-typed-row":
				configurationBackupMutation(t, f.db, `DELETE FROM host_model_configurations WHERE model_config_ref=?`, ref)
			}
			before, _ := backupHostConfigurationState(f.db)
			r, _ := handlerCommand(t, f, s, env)
			if deref(r.Status) != "REJECTED" {
				t.Fatalf("fence accepted: %s", Bytes(r))
			}
			var head, rev, epoch, watermark int
			f.db.QueryRow(`SELECT current_revision FROM host_model_config_heads`).Scan(&head)
			f.db.QueryRow(`SELECT revision,writer_epoch,event_watermark FROM client_sessions WHERE id=?`, sid).Scan(&rev, &epoch, &watermark)
			if head != 1 || rev != 1 || epoch != 1 || watermark != 0 {
				t.Fatalf("rejection wrote business: %d/%d/%d/%d original=%s", head, rev, epoch, watermark, Hash(before))
			}
		})
	}
}

func TestHandlerSQLFaultsRollbackOuterTransaction(t *testing.T) {
	for name, statement := range map[string]string{
		"identity": `CREATE TRIGGER injected_fault BEFORE INSERT ON client_command_identities BEGIN SELECT RAISE(ABORT,'injected identity fault'); END`,
		"config":   `CREATE TRIGGER injected_fault AFTER INSERT ON host_model_configurations BEGIN SELECT RAISE(ABORT,'injected config fault'); END`,
		"head":     `CREATE TRIGGER injected_fault AFTER INSERT ON host_model_config_heads BEGIN SELECT RAISE(ABORT,'injected head fault'); END`,
		"journal":  `CREATE TRIGGER injected_fault BEFORE INSERT ON idempotency WHEN NEW.operation='v2:host.configure' BEGIN SELECT RAISE(ABORT,'injected journal fault'); END`,
		"commit":   `CREATE TABLE injected_parent(id TEXT PRIMARY KEY); CREATE TABLE injected_child(id TEXT REFERENCES injected_parent(id) DEFERRABLE INITIALLY DEFERRED); CREATE TRIGGER injected_fault AFTER INSERT ON idempotency WHEN NEW.operation='v2:host.configure' BEGIN INSERT INTO injected_child VALUES('absent'); END`,
	} {
		t.Run(name, func(t *testing.T) {
			f := contextFixture(t)
			s := &ClientService{Doc: configurationSchema(t), Domain: f.s, ConfigurationAuthority: handlerMetadataFixture{f.owner}}
			if _, e := f.db.Exec(statement); e != nil {
				t.Fatal(e)
			}
			env := handlerDecode(t, handlerDefaultEnvelope(1))
			tx, e := f.db.Begin()
			if e != nil {
				t.Fatal(e)
			}
			_, _, e = s.Execute(context.Background(), tx, env, f.owner)
			if name == "commit" {
				if e != nil {
					tx.Rollback()
					t.Fatal("did not reach commit fault", e)
				}
				e = tx.Commit()
			}
			if e == nil {
				tx.Rollback()
				t.Fatal("injected fault was not observed")
			}
			tx.Rollback()
			for _, table := range []string{"host_model_configurations", "host_model_config_heads", "client_command_identities"} {
				var n int
				if x := f.db.QueryRow(`SELECT count(*) FROM ` + table).Scan(&n); x != nil || n != 0 {
					t.Fatalf("%s left %d %v", table, n, x)
				}
			}
			var n int
			if x := f.db.QueryRow(`SELECT count(*) FROM idempotency WHERE key=?`, *env.CommandID).Scan(&n); x != nil || n != 0 {
				t.Fatalf("orphan journal %d %v", n, x)
			}
			configurationEvidenceSnapshot(t, f.db, "after-original-injected-fault")
		})
	}
}

func TestHandlerConcurrentDefaultCAS(t *testing.T) {
	f := contextFixture(t)
	s := &ClientService{Doc: configurationSchema(t), Domain: f.s, ConfigurationAuthority: handlerMetadataFixture{f.owner}}
	var seq int
	var name, path string
	if e := f.db.QueryRow(`PRAGMA database_list`).Scan(&seq, &name, &path); e != nil {
		t.Fatal(e)
	}
	other, e := store.Open(filepath.Clean(path))
	if e != nil {
		t.Fatal(e)
	}
	defer other.Close()
	start := make(chan struct{})
	var wg sync.WaitGroup
	type result struct {
		response *Response
		err      error
	}
	results := make(chan result, 2)
	for _, db := range []*sql.DB{f.db, other} {
		env := handlerDecode(t, handlerDefaultEnvelope(1))
		wg.Add(1)
		go func(db *sql.DB, env *Envelope) {
			defer wg.Done()
			<-start
			tx, e := db.Begin()
			if e != nil {
				results <- result{err: e}
				return
			}
			r, _, e := s.Execute(context.Background(), tx, env, f.owner)
			if e == nil {
				e = tx.Commit()
			} else {
				tx.Rollback()
			}
			results <- result{r, e}
		}(db, env)
	}
	close(start)
	wg.Wait()
	close(results)
	winners, committedRefusals := 0, 0
	for r := range results {
		if r.err != nil {
			if !strings.Contains(strings.ToLower(r.err.Error()), "locked") && !strings.Contains(strings.ToLower(r.err.Error()), "busy") {
				t.Fatal(r.err)
			}
			t.Log("actual SQLite concurrent contender refused; no automatic retry")
			continue
		}
		if deref(r.response.Status) == "COMPLETED" {
			winners++
		} else if deref(r.response.ErrorCode) == "CONFIG_CONFLICT" {
			committedRefusals++
		} else {
			t.Fatal(string(Bytes(r.response)))
		}
	}
	if winners != 1 {
		t.Fatalf("winners=%d", winners)
	}
	var configs, head, identities, journals int
	f.db.QueryRow(`SELECT count(*) FROM host_model_configurations`).Scan(&configs)
	f.db.QueryRow(`SELECT current_revision FROM host_model_config_heads`).Scan(&head)
	f.db.QueryRow(`SELECT count(*) FROM client_command_identities`).Scan(&identities)
	f.db.QueryRow(`SELECT count(*) FROM idempotency WHERE operation='v2:host.configure'`).Scan(&journals)
	if configs != 1 || head != 1 || identities != 1+committedRefusals || journals != identities {
		t.Fatalf("concurrent CAS leaked %d/%d/%d/%d", configs, head, identities, journals)
	}
	configurationEvidenceSnapshot(t, f.db, "concurrent-CAS")
}

func TestHandlerScopedCASFaultRollsBackAllBusiness(t *testing.T) {
	for _, stage := range []string{"session-update", "journal-insert", "commit"} {
		t.Run(stage, func(t *testing.T) {
			f := contextFixture(t)
			s, sid, _ := handlerTypedSession(t, f, "config-client")
			var beforeSession string
			if e := f.db.QueryRow(`SELECT model_config_ref || ':' || revision || ':' || writer_epoch || ':' || event_watermark FROM client_sessions WHERE id=?`, sid).Scan(&beforeSession); e != nil {
				t.Fatal(e)
			}
			statement := `CREATE TRIGGER scoped_fault AFTER UPDATE OF model_config_ref ON client_sessions BEGIN SELECT RAISE(ABORT,'injected scoped update'); END`
			if stage == "journal-insert" {
				statement = `CREATE TRIGGER scoped_fault BEFORE INSERT ON idempotency WHEN NEW.operation='v2:host.configure' BEGIN SELECT RAISE(ABORT,'injected scoped journal'); END`
			}
			if stage == "commit" {
				statement = `CREATE TABLE scoped_parent(id TEXT PRIMARY KEY); CREATE TABLE scoped_child(id TEXT REFERENCES scoped_parent(id) DEFERRABLE INITIALLY DEFERRED); CREATE TRIGGER scoped_fault AFTER UPDATE OF model_config_ref ON client_sessions BEGIN INSERT INTO scoped_child VALUES('absent'); END`
			}
			if _, e := f.db.Exec(statement); e != nil {
				t.Fatal(e)
			}
			env := handlerDefaultEnvelope(2)
			env.ProjectID = &f.project
			env.SessionID = &sid
			env.ExpectedRevision = revPtr(1)
			env.WriterEpoch = revPtr(1)
			env = handlerDecode(t, env)
			tx, e := f.db.Begin()
			if e != nil {
				t.Fatal(e)
			}
			_, _, e = s.Execute(context.Background(), tx, env, f.owner)
			if stage == "commit" {
				if e != nil {
					tx.Rollback()
					t.Fatal("did not reach real deferred commit", e)
				}
				e = tx.Commit()
			}
			if e == nil {
				tx.Rollback()
				t.Fatal("scoped fault was not observed")
			}
			tx.Rollback()
			var afterSession string
			if e = f.db.QueryRow(`SELECT model_config_ref || ':' || revision || ':' || writer_epoch || ':' || event_watermark FROM client_sessions WHERE id=?`, sid).Scan(&afterSession); e != nil {
				t.Fatal(e)
			}
			var configs, head, identities, journals int
			if e = f.db.QueryRow(`SELECT count(*) FROM host_model_configurations`).Scan(&configs); e != nil {
				t.Fatal(e)
			}
			if e = f.db.QueryRow(`SELECT current_revision FROM host_model_config_heads`).Scan(&head); e != nil {
				t.Fatal(e)
			}
			f.db.QueryRow(`SELECT count(*) FROM client_command_identities WHERE command_id=?`, *env.CommandID).Scan(&identities)
			f.db.QueryRow(`SELECT count(*) FROM idempotency WHERE key=?`, *env.CommandID).Scan(&journals)
			if beforeSession != afterSession || configs != 1 || head != 1 || identities != 0 || journals != 0 {
				t.Fatalf("partial scoped commit session=%s/%s config/head/identity/journal=%d/%d/%d/%d", beforeSession, afterSession, configs, head, identities, journals)
			}
			configurationEvidenceSnapshot(t, f.db, "scoped-fault-"+stage)
		})
	}
}

func TestHandlerConcurrentScopedCAS(t *testing.T) {
	f := contextFixture(t)
	s, sid, _ := handlerTypedSession(t, f, "config-client")
	var seq int
	var name, path string
	if e := f.db.QueryRow(`PRAGMA database_list`).Scan(&seq, &name, &path); e != nil {
		t.Fatal(e)
	}
	other, e := store.Open(filepath.Clean(path))
	if e != nil {
		t.Fatal(e)
	}
	defer other.Close()
	type result struct {
		r   *Response
		err error
		env *Envelope
	}
	results := make(chan result, 2)
	start := make(chan struct{})
	var wg sync.WaitGroup
	for _, db := range []*sql.DB{f.db, other} {
		env := handlerDefaultEnvelope(2)
		env.ProjectID = &f.project
		env.SessionID = &sid
		env.ExpectedRevision = revPtr(1)
		env.WriterEpoch = revPtr(1)
		env = handlerDecode(t, env)
		wg.Add(1)
		go func(db *sql.DB, env *Envelope) {
			defer wg.Done()
			<-start
			tx, e := db.Begin()
			if e != nil {
				results <- result{err: e, env: env}
				return
			}
			r, _, e := s.Execute(context.Background(), tx, env, f.owner)
			if e == nil {
				e = tx.Commit()
			} else {
				tx.Rollback()
			}
			results <- result{r, e, env}
		}(db, env)
	}
	close(start)
	wg.Wait()
	close(results)
	winners, refusals := 0, 0
	var winner result
	for got := range results {
		if got.err != nil {
			if !strings.Contains(strings.ToLower(got.err.Error()), "locked") && !strings.Contains(strings.ToLower(got.err.Error()), "busy") {
				t.Fatal(got.err)
			}
			t.Log("actual SQLite scoped contender refused without retry")
			continue
		}
		if deref(got.r.Status) == "COMPLETED" {
			winners++
			winner = got
		} else if deref(got.r.Status) == "REJECTED" {
			refusals++
		} else {
			t.Fatal(string(Bytes(got.r)))
		}
	}
	var configs, head, revision, epoch, watermark, identities, journals int
	var bound string
	f.db.QueryRow(`SELECT count(*) FROM host_model_configurations`).Scan(&configs)
	f.db.QueryRow(`SELECT current_revision FROM host_model_config_heads`).Scan(&head)
	f.db.QueryRow(`SELECT revision,writer_epoch,event_watermark,model_config_ref FROM client_sessions WHERE id=?`, sid).Scan(&revision, &epoch, &watermark, &bound)
	f.db.QueryRow(`SELECT count(*) FROM client_command_identities`).Scan(&identities)
	f.db.QueryRow(`SELECT count(*) FROM idempotency WHERE operation LIKE 'v2:%'`).Scan(&journals)
	if winners != 1 || configs != 2 || head != 2 || revision != 2 || epoch != 1 || watermark != 0 || identities != 3+refusals || journals != identities || bound != Str(winner.r.Result, "model_config_ref") {
		t.Fatalf("scoped double CAS winners=%d config/head/revision/epoch/watermark/identity/journal=%d/%d/%d/%d/%d/%d/%d", winners, configs, head, revision, epoch, watermark, identities, journals)
	}
	replay, ok := handlerCommand(t, f, s, winner.env)
	if !ok || string(Bytes(replay)) != string(Bytes(winner.r)) {
		t.Fatal("stale scoped exact replay changed original response")
	}
	configurationEvidenceSnapshot(t, f.db, "concurrent-scoped-CAS")
}

func TestHandlerGlobalOriginalConflictFields(t *testing.T) {
	f := contextFixture(t)
	defer configurationEvidenceSnapshot(t, f.db, "original-conflict-fields")
	s := &ClientService{Doc: configurationSchema(t), Domain: f.s, ConfigurationAuthority: handlerMetadataFixture{f.owner}}
	original := handlerDefaultEnvelope(1)
	first, _ := handlerCommand(t, f, s, original)
	if deref(first.Status) != "COMPLETED" {
		t.Fatal(string(Bytes(first)))
	}
	for _, field := range []string{"client_id", "provider_id", "model_id", "base_url", "credential_ref"} {
		t.Run(field, func(t *testing.T) {
			env := *original
			payload, _ := Decode(original.Payload)
			if field == "client_id" {
				env.ClientID = strptr("different-client")
			} else {
				switch field {
				case "base_url":
					payload[field] = "https://other.invalid/v1"
				case "credential_ref":
					payload[field] = "cred-other"
				default:
					payload[field] = "different"
				}
				env.Payload = Bytes(payload)
			}
			tx, e := f.db.Begin()
			if e != nil {
				t.Fatal(e)
			}
			_, _, e = s.Execute(context.Background(), tx, handlerDecode(t, &env), f.owner)
			tx.Rollback()
			if e != ErrIdemConflict {
				t.Fatalf("full original %s conflict: %v", field, e)
			}
		})
	}
	advanced, _ := handlerCommand(t, f, s, handlerDefaultEnvelope(2))
	if deref(advanced.Status) != "COMPLETED" {
		t.Fatal(string(Bytes(advanced)))
	}
	replay, yes := handlerCommand(t, f, s, original)
	if !yes || Hash(first) != Hash(replay) {
		t.Fatal("head advance changed original reply")
	}
	var before int
	f.db.QueryRow(`SELECT count(*) FROM client_command_identities`).Scan(&before)
	if _, e := f.db.Exec(`UPDATE auth_principals SET revoked=1 WHERE id=?`, f.owner); e != nil {
		t.Fatal(e)
	}
	tx, e := f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	r, yes, e := s.Execute(context.Background(), tx, handlerDecode(t, original), f.owner)
	tx.Rollback()
	if e == nil && (yes || r == nil || deref(r.Status) != "REJECTED") {
		t.Fatal("revoked authentication acquired replay authority")
	}
	var after int
	f.db.QueryRow(`SELECT count(*) FROM client_command_identities`).Scan(&after)
	if before != after {
		t.Fatal("revoked replay wrote identity")
	}
}

func TestHandlerHistoricalReferenceAndRepeatedRebind(t *testing.T) {
	f := contextFixture(t)
	defer configurationEvidenceSnapshot(t, f.db, "historical-reference-rebind")
	s, sid, old := handlerTypedSession(t, f, "config-client")
	var workspace string
	if e := f.db.QueryRow(`SELECT workspace_ref FROM client_sessions WHERE id=?`, sid).Scan(&workspace); e != nil {
		t.Fatal(e)
	}
	for rev := int64(2); rev <= 102; rev++ {
		r, _ := handlerCommand(t, f, s, handlerDefaultEnvelope(rev))
		if deref(r.Status) != "COMPLETED" {
			t.Fatal(string(Bytes(r)))
		}
	}
	var current string
	if e := f.db.QueryRow(`SELECT model_config_ref FROM client_sessions WHERE id=?`, sid).Scan(&current); e != nil || current != old {
		t.Fatal("new defaults changed existing Session", e)
	}
	created, _ := handlerCommand(t, f, s, &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("config-client"), ProjectID: &f.project, Method: strptr("session.create"), Payload: Bytes(Object{"workspace_ref": workspace, "model_config_ref": old, "title": "explicit historical ref"})})
	if deref(created.Status) != "COMPLETED" || Str(created.Result, "model_config_ref") != old {
		t.Fatal("old ref fell outside status view but must remain usable offline", string(Bytes(created)))
	}
	for step := int64(1); step <= 2; step++ {
		env := handlerDefaultEnvelope(102 + step)
		env.ProjectID = &f.project
		env.SessionID = &sid
		env.ExpectedRevision = &step
		env.WriterEpoch = revPtr(1)
		r, _ := handlerCommand(t, f, s, env)
		if deref(r.Status) != "COMPLETED" || derefI64(r.Revision, 0) != step+1 {
			t.Fatal(string(Bytes(r)))
		}
		var watermark, epoch int
		if e := f.db.QueryRow(`SELECT event_watermark,writer_epoch FROM client_sessions WHERE id=?`, sid).Scan(&watermark, &epoch); e != nil || watermark != 0 || epoch != 1 {
			t.Fatal("configuration changed event/writer generation", e)
		}
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		_, e := readClientConfiguration(context.Background(), tx, s.Doc, configurationFixtureOwner, f.owner, old)
		return e
	})
	var runs, effects int
	f.db.QueryRow(`SELECT count(*) FROM domain_objects WHERE kind='Run'`).Scan(&runs)
	f.db.QueryRow(`SELECT count(*) FROM resource_effects`).Scan(&effects)
	if runs != 0 || effects != 0 {
		t.Fatal("history/configuration created execution")
	}
}
