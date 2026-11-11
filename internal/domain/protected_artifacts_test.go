//go:build windows

package domain

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"researchos.local/research-os/adapters/protectedstore"
	"strings"
	"testing"
	"time"
)

// These are local authority-transition controls, not an independent LIVE
// verifier. The provider hooks exercise the production pre/post-IO checks.
type w1702Provider struct {
	protectedstore.Provider
	afterRead func()
	readError error
	unready   bool
}

func (p *w1702Provider) Ready(ctx context.Context, mode string) error {
	if p.unready {
		return errors.New("fixture-private-provider-failure")
	}
	return p.Provider.Ready(ctx, mode)
}
func (p *w1702Provider) Read(ctx context.Context, b protectedstore.Blob) ([]byte, error) {
	if p.readError != nil {
		return nil, p.readError
	}
	raw, err := p.Provider.Read(ctx, b)
	if p.afterRead != nil {
		p.afterRead()
	}
	return raw, err
}
func w1702Assert(t *testing.T, id string, want, got any) {
	t.Helper()
	status := "PASS"
	if Hash(want) != Hash(got) {
		status = "FAIL"
	}
	fmt.Println("W1702_ASSERTION " + string(Bytes(Object{"assertion_id": id, "expected": want, "actual": got, "status": status, "mode": "FIXTURE"})))
	if status != "PASS" {
		t.Fatalf("%s", id)
	}
}

func TestW1702AuthorityTransitions(t *testing.T) {
	for _, role := range []string{"EXECUTOR", "PLANNER"} {
		t.Run("restricted-"+role, func(t *testing.T) {
			f, store, _ := protectedFixture(t)
			a := protectedRegister(t, f, store, "W1702_PRIVATE_SYNTHETIC", protectedMetadata())
			f.token = c22Token(t, f, "restricted-wrong-role", []string{role}, true)
			for _, suffix := range []string{"", "/content"} {
				code, raw, headers := protectedGET(f, "/artifacts/"+Str(a, "id")+suffix)
				w1702Assert(t, "W1702-ROLE-"+role+strings.ReplaceAll(suffix, "/", "-"), []any{404, false, "no-store"}, []any{code, bytes.Contains(raw, []byte("W1702_PRIVATE_SYNTHETIC")), headers.Get("Cache-Control")})
			}
			code, raw, _ := protectedGET(f, "/artifacts")
			w1702Assert(t, "W1702-LIST-"+role, []any{200, false}, []any{code, bytes.Contains(raw, []byte(Str(a, "id")))})
			_, err := f.s.RegisterProtectedArtifact(context.Background(), f.token, f.project, Str(a, "storage_key"), protectedMetadata())
			var fault *Fault
			w1702Assert(t, "W1702-REGISTER-"+role, true, errors.As(err, &fault) && fault.Status == 403)
		})
	}
	for _, scenario := range []string{"role-removed", "provider-unavailable", "provider-private-error"} {
		t.Run(scenario, func(t *testing.T) {
			f, store, _ := protectedFixture(t)
			a := protectedRegister(t, f, store, "W1702_PRIVATE_SYNTHETIC", protectedMetadata())
			p := &w1702Provider{Provider: store}
			f.s.Protected = p
			p.afterRead = func() {
				if scenario == "role-removed" {
					if _, err := f.db.Exec("UPDATE auth_principals SET roles=? WHERE id=?", `["EXECUTOR"]`, "canary-restricted-verifier"); err != nil {
						t.Fatal(err)
					}
				} else {
					p.unready = true
				}
			}
			wantCode := 503
			if scenario == "role-removed" {
				wantCode = 404
			}
			if scenario == "provider-private-error" {
				p.readError = errors.New("W1702_PRIVATE_SYNTHETIC provider path and labels")
			}
			code, raw, headers := protectedGET(f, "/artifacts/"+Str(a, "id")+"/content")
			w1702Assert(t, "W1702-READ-"+scenario, []any{wantCode, false, "no-store"}, []any{code, bytes.Contains(raw, []byte("W1702_PRIVATE_SYNTHETIC")), headers.Get("Cache-Control")})
		})
	}
	t.Run("registration-revoked-during-io", func(t *testing.T) {
		f, store, _ := protectedFixture(t)
		blob, err := store.CreateCanary(context.Background(), f.project, "text/plain", []byte("W1702_PRIVATE_SYNTHETIC"))
		if err != nil {
			t.Fatal(err)
		}
		p := &w1702Provider{Provider: store, afterRead: func() {
			if err := f.s.RevokePrincipal(context.Background(), "canary-restricted-verifier"); err != nil {
				t.Fatal(err)
			}
		}}
		f.s.Protected = p
		a, err := f.s.RegisterProtectedArtifact(context.Background(), f.token, f.project, blob.Ticket, protectedMetadata())
		var fault *Fault
		var persisted int
		if e := f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='Artifact' AND json_extract(body,'$.storage_key')=?", blob.Ticket).Scan(&persisted); e != nil {
			t.Fatal(e)
		}
		w1702Assert(t, "W1702-REGISTER-REVOKED", []any{true, true, 0}, []any{errors.As(err, &fault) && fault.Status == 401, a == nil, persisted})
	})
	// This exercises only the deliberately closed body-export method. It does
	// not contact the service or assert independent identity/read capability.
	raw, err := (&protectedstore.FrozenProvider{}).Read(context.Background(), protectedstore.Blob{})
	w1702Assert(t, "W1702-FROZEN-BODY-CLOSED", []any{true, 0}, []any{errors.Is(err, protectedstore.ErrIsolation), len(raw)})
}

func protectedAssert(t *testing.T, id string, want, got, evidence any) {
	t.Helper()
	status := "PASS"
	if Hash(want) != Hash(got) {
		status = "FAIL"
	}
	fmt.Println("W11_PROTECTED_ASSERTION " + string(Bytes(Object{"assertion_id": id, "expected": want, "actual": got, "status": status, "evidence": evidence, "scope": "CANARY_ONLY", "formal_isolation": "BLOCKED"})))
	if status != "PASS" {
		t.Fatalf("%s", id)
	}
}
func protectedFixture(t *testing.T) (*fixture, *protectedstore.CanaryStore, string) {
	f := contextFixture(t)
	store, e := protectedstore.NewCanary(filepath.Join(t.TempDir(), "private"))
	if e != nil {
		t.Fatal(e)
	}
	t.Cleanup(func() { store.Close() })
	f.s.Protected = store
	p := Principal{ID: "canary-restricted-verifier", Roles: []string{"VERIFIER"}, Grants: []Grant{{ProjectID: f.project, Restricted: true}}}
	if e = f.s.ProvisionPrincipal(context.Background(), p); e != nil {
		t.Fatal(e)
	}
	token, e := f.s.IssueCredential(context.Background(), p.ID, time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	f.token = token
	return f, store, token
}
func protectedMetadata() Object {
	return Object{"run_id": nil, "kind": "REPORT", "evidence_kind": "SIMULATED", "measurement_mode": "FIXTURE", "input_refs": Empty(), "source_refs": Empty()}
}
func protectedRegister(t *testing.T, f *fixture, store *protectedstore.CanaryStore, raw string, b Object) Object {
	t.Helper()
	blob, e := store.CreateCanary(context.Background(), f.project, "text/plain; charset=utf-8", []byte(raw))
	if e != nil {
		t.Fatal(e)
	}
	a, e := f.s.RegisterProtectedArtifact(context.Background(), f.token, f.project, blob.Ticket, b)
	if e != nil {
		t.Fatal(e)
	}
	return a
}
func protectedGET(f *fixture, path string) (int, []byte, http.Header) {
	r := httptest.NewRequest("GET", f.path(path), nil)
	r.Header.Set("Authorization", "Bearer "+f.token)
	w := httptest.NewRecorder()
	f.s.Handler().ServeHTTP(w, r)
	return w.Code, w.Body.Bytes(), w.Header()
}

func TestProtectedAPIAndStorage(t *testing.T) {
	f, store, verifierToken := protectedFixture(t)
	const canary = "PRIVATE_CANARY_74e3f2_no_holdout"
	var before int
	f.db.QueryRow("SELECT count(*) FROM uploaded_content").Scan(&before)
	a := protectedRegister(t, f, store, canary, protectedMetadata())
	var after, stored int
	f.db.QueryRow("SELECT count(*) FROM uploaded_content").Scan(&after)
	f.db.QueryRow("SELECT count(*) FROM uploaded_content WHERE bytes LIKE ?", "%"+canary+"%").Scan(&stored)
	protectedAssert(t, "PROTECTED-DB-METADATA-ONLY", []any{before, 0, "VERIFIER_ONLY"}, []any{after, stored, a["access_class"]}, Object{"classification": a["access_class"], "storage_key_kind": "opaque provider ticket; no path or body"})
	code, raw, headers := protectedGET(f, "/artifacts/"+Str(a, "id")+"/content")
	protectedAssert(t, "PROTECTED-AUTHORIZED-CONTENT", []any{200, true, "no-store", "attachment", "nosniff"}, []any{code, string(raw) == canary, headers.Get("Cache-Control"), headers.Get("Content-Disposition"), headers.Get("X-Content-Type-Options")}, Object{"body_returned_only_to_restricted_verifier": true})
	same, e := f.s.RegisterProtectedArtifact(context.Background(), f.token, f.project, Str(a, "storage_key"), protectedMetadata())
	protectedAssert(t, "PROTECTED-REPEATED-REGISTRATION", []any{true, a["id"]}, []any{e == nil, same["id"]}, nil)
	derived := protectedMetadata()
	derived["input_refs"] = []any{Ref(a, "Artifact")}
	derived["access_class"] = "PROJECT"
	child := protectedRegister(t, f, store, "derived synthetic canary", derived)
	protectedAssert(t, "PROTECTED-DERIVED-CLASSIFICATION", "VERIFIER_ONLY", child["access_class"], "trusted registration always inherits the protected boundary")
	var links int
	if e = f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='ImpactLink' AND json_extract(body,'$.from_ref.id')=? AND json_extract(body,'$.to_ref.id')=? AND json_extract(body,'$.relation')='DERIVED_FROM'", f.project, child["id"], a["id"]).Scan(&links); e != nil {
		t.Fatal(e)
	}
	protectedAssert(t, "PROTECTED-DERIVED-IMPACT-LINK", 1, links, "same canonical impactLink helper as public seal")
	// Public upload/seal cannot declassify a protected reference, including for an authorized verifier.
	upload := f.expect(201, "POST", f.path("/content"), ID(), "", []byte("public candidate summary"))
	seal := Object{"run_id": nil, "kind": "REPORT", "evidence_kind": "SIMULATED", "measurement_mode": "FIXTURE", "content_hash": upload["content_hash"], "storage_key": upload["storage_key"], "media_type": "text/plain", "byte_size": len("public candidate summary"), "input_refs": []any{Ref(a, "Artifact")}, "source_refs": Empty(), "produced_by": "canary-restricted-verifier", "access_class": "PROJECT"}
	code, reply, _ := f.request("POST", f.path("/artifacts"), ID(), f.stateTag(), seal)
	protectedAssert(t, "PROTECTED-PUBLIC-DERIVATION-REFUSED", 403, code, reply)
	for _, role := range []string{"READER", "PLANNER", "EXECUTOR", "OWNER"} {
		f.switchPrincipal("canary-unrestricted-"+role, []string{role})
		for _, suffix := range []string{"", "/content"} {
			code, raw, _ = protectedGET(f, "/artifacts/"+Str(a, "id")+suffix)
			protectedAssert(t, "PROTECTED-DIRECT-DENY-"+role+strings.ReplaceAll(suffix, "/", "-"), []any{404, false}, []any{code, bytes.Contains(raw, []byte(canary))}, nil)
		}
	}
	f.switchPrincipal("canary-reader", []string{"READER"})
	for _, path := range []string{"/artifacts", "/events"} {
		code, raw, _ = protectedGET(f, path)
		protectedAssert(t, "PROTECTED-LIST-NO-LEAK"+strings.ReplaceAll(path, "/", "-"), []any{200, false, false}, []any{code, bytes.Contains(raw, []byte(canary)), bytes.Contains(raw, []byte(Str(a, "storage_key")))}, nil)
	}
	f.switchPrincipal(f.owner, []string{"OWNER", "PLANNER", "EXECUTOR", "SCHEDULER"})
	query := Object{"query": canary, "snapshot_ids": []any{a["id"]}, "limit": 10, "expected_state_revision": f.state()["revision"]}
	code, reply, _ = f.request("POST", f.path("/search"), ID(), "", query)
	protectedAssert(t, "PROTECTED-SEARCH-NO-LEAK", []any{true, false}, []any{code >= 400, bytes.Contains(Bytes(reply), []byte(canary))}, nil)
	f.token = verifierToken
	f.s.Protected = nil
	code, raw, _ = protectedGET(f, "/artifacts/"+Str(a, "id")+"/content")
	protectedAssert(t, "PROTECTED-MISSING-PROVIDER", []any{503, false}, []any{code, bytes.Contains(raw, []byte(canary))}, nil)
	f.s.Protected = store
	live := protectedMetadata()
	live["measurement_mode"] = "LIVE"
	_, e = f.s.RegisterProtectedArtifact(context.Background(), f.token, f.project, Str(a, "storage_key"), live)
	protectedAssert(t, "PROTECTED-FORMAL-REGISTRATION-BLOCKED", true, e != nil, nil)
	_, e = f.s.CreateBackup(context.Background(), filepath.Join(t.TempDir(), "backup"), bytes.Repeat([]byte{1}, 32))
	protectedAssert(t, "PROTECTED-BACKUP-REFUSED", true, e != nil && strings.Contains(e.Error(), "PROTECTED_BACKUP_REQUIRES_W17"), nil)
}

type protectedInterceptor struct {
	protectedstore.Provider
	afterRead func()
	tamper    bool
}

func (p *protectedInterceptor) Read(ctx context.Context, b protectedstore.Blob) ([]byte, error) {
	raw, e := p.Provider.Read(ctx, b)
	if p.afterRead != nil {
		p.afterRead()
	}
	if p.tamper && e == nil {
		raw = append(raw, '!')
	}
	return raw, e
}
func TestProtectedReadRevalidation(t *testing.T) {
	for _, scenario := range []string{"grant-revoked", "credential-revoked", "artifact-stale", "corrupt-body"} {
		t.Run(scenario, func(t *testing.T) {
			f, store, _ := protectedFixture(t)
			a := protectedRegister(t, f, store, "canary-current-only", protectedMetadata())
			interceptor := &protectedInterceptor{Provider: store}
			f.s.Protected = interceptor
			interceptor.afterRead = func() {
				switch scenario {
				case "grant-revoked":
					_, e := f.db.Exec("DELETE FROM auth_grants WHERE principal=? AND project=?", "canary-restricted-verifier", f.project)
					if e != nil {
						t.Error(e)
					}
				case "credential-revoked":
					if e := f.s.RevokePrincipal(context.Background(), "canary-restricted-verifier"); e != nil {
						t.Error(e)
					}
				case "artifact-stale":
					_, e := f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.validity','STALE') WHERE project=? AND kind='Artifact' AND id=?", f.project, a["id"])
					if e != nil {
						t.Error(e)
					}
				}
			}
			interceptor.tamper = scenario == "corrupt-body"
			_, raw, e := f.s.ReadProtectedArtifact(context.Background(), f.token, f.project, Str(a, "id"))
			protectedAssert(t, "PROTECTED-REVALIDATE-"+scenario, []any{true, 0}, []any{e != nil, len(raw)}, "authorization/current version/integrity checked after provider IO")
		})
	}
}
func TestProtectedSummaryShape(t *testing.T) {
	summary := protectedstore.SafeSummary{Schema: "researchos.protected-summary.v1", Status: "EXECUTION_REPORTED", Total: 4, Correct: 2, FalseAccept: 1, FalseReject: 0, Abstain: 1, CriticalFalseAccept: 1, MaximumMode: "ADVISORY"}
	protectedAssert(t, "PROTECTED-SUMMARY-COUNTS", true, summary.Validate() == nil, "validator only; no publication/declassification authority")
	raw := append(Bytes(summary)[:len(Bytes(summary))-1], []byte(`,"reason":"private question text"}`)...)
	_, e := protectedstore.ParseSafeSummary(raw)
	protectedAssert(t, "PROTECTED-SUMMARY-FREE-TEXT-REFUSED", true, e != nil, nil)
	summary.Status = "private question"
	protectedAssert(t, "PROTECTED-SUMMARY-ENUM-REFUSED", true, summary.Validate() != nil, nil)
}

func TestProtectedContextRefusal(t *testing.T) {
	f, store, _ := protectedFixture(t)
	a := protectedRegister(t, f, store, "context-private-canary", protectedMetadata())
	p := Principal{ID: "canary-restricted-planner", Roles: []string{"OWNER", "PLANNER"}, Grants: []Grant{{ProjectID: f.project, Restricted: true}}}
	if e := f.s.ProvisionPrincipal(context.Background(), p); e != nil {
		t.Fatal(e)
	}
	var e error
	f.token, e = f.s.IssueCredential(context.Background(), p.ID, time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	task := f.task(f.requirement(), []any{Ref(a, "Artifact")}, "protected-context-canary")
	bundle := f.bundle(task)
	destination := filepath.Join(t.TempDir(), "materialized")
	_, e = f.s.MaterializeTaskContext(context.Background(), f.token, f.project, Str(task, "id"), destination)
	_, statErr := os.Stat(destination)
	protectedAssert(t, "PROTECTED-MATERIALIZE-REFUSED", []any{true, true}, []any{e != nil, os.IsNotExist(statErr)}, "protected content materialization remains unsupported; no destination created")
	f.switchPrincipal("canary-context-reader", []string{"READER"})
	_, e = f.s.GetTaskContext(context.Background(), f.token, f.project, Str(task, "id"))
	code, raw, _ := protectedGET(f, "/context-bundles/"+Str(bundle, "id"))
	protectedAssert(t, "PROTECTED-CONTEXT-NO-LEAK", []any{true, 404, false}, []any{e != nil, code, bytes.Contains(raw, []byte("context-private-canary"))}, nil)
}
