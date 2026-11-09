//go:build windows

package host

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
	"time"

	"researchos.local/research-os/internal/api"
	"researchos.local/research-os/internal/auth"
	"researchos.local/research-os/internal/domain"
)

type nativeCreateHostFixture struct {
	h                                *Host
	handler                          http.Handler
	service                          *domain.Service
	token, project, workspace, model string
}

func newNativeCreateHostFixture(t *testing.T) *nativeCreateHostFixture {
	t.Helper()
	h := firstUseHost(t)
	ctx := context.Background()
	s, e := domain.New(h.db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if e != nil {
		t.Fatal(e)
	}
	if e = domain.InstallClientNativeWriterOriginPreparedSchema(ctx, h.db); e != nil {
		t.Fatal(e)
	}
	if e = s.ProvisionPrincipal(ctx, domain.Principal{ID: "native-owner", Roles: []string{"OWNER"}, CanCreateProject: true}); e != nil {
		t.Fatal(e)
	}
	token, e := s.IssueCredential(ctx, "native-owner", 10*time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	// Trusted fresh fixture binding, not a bootstrap or a client-supplied identity.
	h.state = &hostState{Version: 1, PrincipalID: "native-owner", PrincipalRef: h.identity.Ref, HostInstanceID: h.InstanceID()}
	f := &nativeCreateHostFixture{h: h, service: s, token: token, workspace: "native-workspace"}
	f.handler = api.HandlerWithNativeCreateHost(h.db, t.TempDir(), s, nil, h.InstanceID(), nil, nil, h, h)
	profile := domain.Object{"name": "Native Host fixture", "intent": "One finite fresh create", "facts": domain.Empty(), "accepted_scope": []any{"fixture"}, "constraints": domain.Empty(), "source_configs": domain.Empty(), "source_document_refs": domain.Empty(), "read_snapshot_ids": domain.Empty()}
	r := f.call(t, "/v1/projects", domain.Bytes(profile), "")
	if r.Code != 201 {
		t.Fatalf("project: %d %s", r.Code, r.Body.Bytes())
	}
	var project domain.Object
	if e = json.Unmarshal(r.Body.Bytes(), &project); e != nil {
		t.Fatal(e)
	}
	f.project = domain.Str(project, "project_id")
	binding := domain.WorkspaceBinding{AuthorizedRef: f.workspace, DisplayName: "fixture", DisplayPath: "fixture", RealPath: t.TempDir(), Access: "READ_ONLY", ProjectID: &f.project, Revision: 1, Status: domain.WorkspaceActive, PrincipalID: "native-owner", ClientID: "native-client", HostPrincipalRef: h.identity.Ref, CreatedAt: domain.Now()}
	if _, e = h.db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('',?,?,1,?,0)`, domain.KindWorkspaceBinding, f.workspace, string(domain.Bytes(binding))); e != nil {
		t.Fatal(e)
	}
	configure := f.envelope("host.configure", "native-configure", domain.Object{"config_revision": 1, "provider_id": "fixture-provider", "base_url": "https://fixture.invalid/v1", "model_id": "fixture-model", "credential_ref": nil})
	configure["project_id"] = nil
	r = f.call(t, "/v2/command", domain.Bytes(configure), "")
	var out domain.Object
	if json.Unmarshal(r.Body.Bytes(), &out) != nil || r.Code != 200 || out["status"] != "COMPLETED" {
		t.Fatalf("configure: %d %s", r.Code, r.Body.Bytes())
	}
	f.model = domain.Str(out["result"].(map[string]any), "model_config_ref")
	h.peerLookup = func(uint32) (auth.Identity, error) { return h.Identity(), nil }
	return f
}
func (f *nativeCreateHostFixture) call(t *testing.T, path string, raw []byte, ref string) *httptest.ResponseRecorder {
	t.Helper()
	req := httptest.NewRequest("POST", path, bytes.NewReader(raw))
	req.Header.Set("Authorization", "Bearer "+f.token)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Idempotency-Key", domain.ID())
	if ref != "" {
		req.Header.Set(domain.NativeCreateAttestationHeader, ref)
	}
	r := httptest.NewRecorder()
	f.handler.ServeHTTP(r, req)
	return r
}
func (f *nativeCreateHostFixture) envelope(method, key string, payload domain.Object) domain.Object {
	return domain.Object{"protocol_version": domain.ProtocolV2, "command_id": key, "client_id": "native-client", "project_id": f.project, "session_id": nil, "expected_revision": nil, "writer_epoch": nil, "method": method, "payload": payload}
}
func (f *nativeCreateHostFixture) createRaw(key string) []byte {
	return domain.Bytes(f.envelope("session.create", key, domain.Object{"workspace_ref": f.workspace, "model_config_ref": f.model, "title": "fresh witnessed create"}))
}
func (f *nativeCreateHostFixture) attestationFrame(key string, raw []byte, token string) []byte {
	return domain.Bytes(domain.Object{"kind": KindNativeClientAttestRequest, "client_id": "native-client", "payload": domain.Object{"schema_version": 1, "credential_value": token, "command_id": key, "method": "session.create", "project_id": f.project, "request_raw_sha256": domain.Digest(raw), "session_id": nil, "expected_revision": nil, "writer_epoch": nil}})
}
func (f *nativeCreateHostFixture) issue(t *testing.T, key string, raw []byte) string {
	t.Helper()
	peer, e := f.h.verifyNativePeer(42)
	if e != nil {
		t.Fatal(e)
	}
	reply, e := f.h.handleVerifiedNative(f.attestationFrame(key, raw, f.token), peer, nil)
	if e != nil {
		t.Fatal(e)
	}
	if bytes.Contains(reply, []byte(f.token)) || bytes.Contains(reply, []byte(domain.Digest([]byte(f.token)))) || bytes.Contains(reply, []byte(f.h.identity.Ref)) {
		t.Fatal("private Native facts leaked in result")
	}
	var out domain.Object
	if json.Unmarshal(reply, &out) != nil || len(out) != 2 || out["kind"] != KindNativeClientAttestResult {
		t.Fatal("closed result frame changed")
	}
	return domain.Str(out["payload"].(map[string]any), "attestation_ref")
}

func TestNativeCreateRealProducerMapAndRecorderTransaction(t *testing.T) {
	f := newNativeCreateHostFixture(t)
	raw := f.createRaw("host-native-create")
	var before, after int
	if e := f.h.db.QueryRow(`SELECT count(*) FROM auth_credentials`).Scan(&before); e != nil {
		t.Fatal(e)
	}
	ref := f.issue(t, "host-native-create", raw)
	if e := f.h.db.QueryRow(`SELECT count(*) FROM auth_credentials`).Scan(&after); e != nil || after != before {
		t.Fatal("attestation issued a credential", e)
	}
	if _, e := os.Stat(f.h.SessionFile()); !os.IsNotExist(e) {
		t.Fatal("attestation bootstrapped/wrote a shared session file", e)
	}
	f.h.nativeCreate.mu.Lock()
	w := f.h.nativeCreate.witnesses[ref]
	f.h.nativeCreate.mu.Unlock()
	if w.origin.ExpiresAt.Sub(w.origin.IssuedAt) > 60*time.Second || w.origin.CredentialHash != domain.Digest([]byte(f.token)) || w.origin.ActualRawSHA256 != domain.Digest(raw) {
		t.Fatal("witness fields not bound")
	}
	r := f.call(t, "/v2/command", raw, ref)
	var out domain.Object
	if json.Unmarshal(r.Body.Bytes(), &out) != nil || r.Code != 200 || out["status"] != "COMPLETED" {
		t.Fatalf("real producer vertical: %d %s", r.Code, r.Body.Bytes())
	}
	var count int
	if e := f.h.db.QueryRow(`SELECT count(*) FROM client_native_writer_origins`).Scan(&count); e != nil || count != 1 {
		t.Fatal("first writer origin missing", e)
	}
	f.h.nativeCreate.mu.Lock()
	f.h.nativeCreate.witnesses = map[string]nativeCreateWitness{}
	f.h.nativeCreate.mu.Unlock()
	replay := f.call(t, "/v2/command", raw, ref)
	if replay.Code != 200 || !bytes.Equal(r.Body.Bytes(), replay.Body.Bytes()) {
		t.Fatal("cold sealed replay created new authority", replay.Body.String())
	}
	if _, e := domain.ValidateClientNativeWriterOriginHistory(context.Background(), f.h.db, f.h.nativeCreate.service.Doc); e != nil {
		t.Fatal("historical validator required current map", e)
	}
}

func TestNativeCreateRejectsLegacyClosureAndWrongFacts(t *testing.T) {
	f := newNativeCreateHostFixture(t)
	raw := f.createRaw("host-proof-reject")
	frame := f.attestationFrame("host-proof-reject", raw, f.token)
	if _, e := f.h.HandleNative(frame, true, nil); e == nil {
		t.Fatal("legacy true boolean minted Native evidence")
	}
	peer, e := f.h.verifyNativePeer(42)
	if e != nil {
		t.Fatal(e)
	}
	for _, bad := range [][]byte{append(append([]byte(nil), frame...), []byte(` {}`)...), bytes.Replace(frame, []byte(`"schema_version":1`), []byte(`"schema_version":1,"schema_version":1`), 1), bytes.Replace(frame, []byte(`"schema_version":1`), []byte(`"schema_version":1,"unknown":"secret-canary-value"`), 1)} {
		if _, e = f.h.handleVerifiedNative(bad, peer, nil); e == nil || strings.Contains(e.Error(), "secret-canary-value") {
			t.Fatal("privileged closure accepted or leaked input")
		}
	}
	if _, e = f.h.handleVerifiedNative(f.attestationFrame("host-proof-reject", raw, "secret-canary-value"), peer, nil); e == nil || strings.Contains(e.Error(), "secret-canary-value") {
		t.Fatal("invalid bearer accepted or leaked")
	}
	ref := f.issue(t, "host-proof-reject", raw)
	for _, change := range []string{"wire", "credential", "service", "store", "generation"} {
		t.Run(change, func(t *testing.T) {
			f.h.nativeCreate.mu.Lock()
			w := f.h.nativeCreate.witnesses[ref]
			f.h.nativeCreate.mu.Unlock()
			q := domain.NativeCreateProofQuery{Service: w.service, Store: w.store, AttestationRef: ref, Principal: w.origin.Principal, AuthorityRoot: w.origin.AuthorityRoot, CredentialHash: w.origin.CredentialHash, CredentialExpiresAt: time.Now().Add(time.Hour), CommandID: w.origin.CommandID, ClientID: w.origin.ClientID, ProjectID: w.origin.ProjectID, Method: "session.create", ActualRawSHA256: w.origin.ActualRawSHA256}
			v := &nativeCreateVerifier{f.h, w.service}
			if change == "wire" {
				q.ActualRawSHA256 = domain.Digest(append([]byte(" "), raw...))
			}
			if change == "credential" {
				q.CredentialHash = domain.Digest([]byte("other"))
			}
			if change == "service" {
				q.Service = &domain.ClientService{Domain: f.service}
			}
			if change == "store" {
				q.Store = nil
			}
			old := f.h.bootGeneration
			if change == "generation" {
				f.h.bootGeneration[0] ^= 0xff
			}
			defer func() { f.h.bootGeneration = old }()
			tx, e := f.h.db.Begin()
			if e != nil {
				t.Fatal(e)
			}
			defer tx.Rollback()
			if _, e = v.VerifyNativeCreate(context.Background(), tx, q); e == nil {
				t.Fatal("witness binding ignored", change)
			}
		})
	}
}

func TestNativeCreateWitnessExpiryCapacityAndRebind(t *testing.T) {
	f := newNativeCreateHostFixture(t)
	raw := f.createRaw("host-limits")
	ref := f.issue(t, "host-limits", raw)
	f.h.nativeCreate.mu.Lock()
	w := f.h.nativeCreate.witnesses[ref]
	f.h.nativeCreate.mu.Unlock()
	f.h.now = func() time.Time { return w.origin.ExpiresAt }
	r := f.call(t, "/v2/command", raw, ref)
	var body domain.Object
	if json.Unmarshal(r.Body.Bytes(), &body) != nil || body["status"] == "COMPLETED" {
		t.Fatal("TTL equality was not expired")
	}
	f.h.now = func() time.Time { return time.Now().UTC() }
	f.h.nativeCreate.mu.Lock()
	for i := 0; i < 256; i++ {
		x := w
		x.origin.ExpiresAt = time.Now().Add(time.Minute)
		f.h.nativeCreate.witnesses[domain.ID()] = x
	}
	f.h.nativeCreate.mu.Unlock()
	peer, e := f.h.verifyNativePeer(42)
	if e != nil {
		t.Fatal(e)
	}
	if _, e = f.h.handleVerifiedNative(f.attestationFrame("capacity", f.createRaw("capacity"), f.token), peer, nil); e == nil {
		t.Fatal("unbounded witness map")
	}
	if _, e = f.h.BindNativeCreateAuthority(&domain.ClientService{Domain: f.service}); e != nil {
		t.Fatal(e)
	}
	if len(f.h.nativeCreate.witnesses) != 0 {
		t.Fatal("new service incarnation inherited witnesses")
	}
}
