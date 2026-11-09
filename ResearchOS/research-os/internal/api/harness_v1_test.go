package api

import (
	"context"
	"net/http"
	"net/http/httptest"
	"researchos.local/research-os/internal/domain"
	"strings"
	"testing"
)

type harnessPortFixture struct {
	calls int
	last  domain.HarnessSubmit
}

func (p *harnessPortFixture) Capabilities(context.Context, string) (domain.Object, error) {
	return domain.Object{"api_version": "harness.v1", "data": domain.Object{"can_submit": false}}, nil
}
func (p *harnessPortFixture) Submit(_ context.Context, _ string, v domain.HarnessSubmit) (domain.Object, error) {
	p.calls++
	p.last = v
	return domain.Object{"api_version": "harness.v1", "data": domain.Object{"status": "QUEUED", "run": nil}}, nil
}
func (p *harnessPortFixture) List(context.Context, string, domain.HarnessList) (domain.Object, error) {
	return nil, nil
}
func (p *harnessPortFixture) Get(context.Context, string, string, string) (domain.Object, error) {
	return nil, nil
}
func (p *harnessPortFixture) Events(context.Context, string, domain.HarnessEvents) (domain.Object, error) {
	return nil, nil
}
func (p *harnessPortFixture) Cancel(context.Context, string, string, string, domain.HarnessCancel) (domain.Object, error) {
	return nil, nil
}
func TestHarnessV1HTTPStrictInput(t *testing.T) {
	port := &harnessPortFixture{}
	mux := http.NewServeMux()
	mountHarnessV1(mux, port)
	valid := `{"request_id":"request-1","project_id":"p","workspace_ref":"opaque","harness_id":"codex","scope":"workspace-read","prompt":"task"}`
	for _, body := range []string{strings.Replace(valid, `"prompt":"task"`, `"prompt":"task","prompt":"changed"`, 1), strings.Replace(valid, `"prompt":"task"`, `"prompt":"task","trusted":true`, 1), `{}`, valid + "{}"} {
		req := httptest.NewRequest("POST", "/harness/v1/tasks", strings.NewReader(body))
		req.Header.Set("Authorization", "Bearer owned")
		rec := httptest.NewRecorder()
		mux.ServeHTTP(rec, req)
		if rec.Code != 400 || port.calls != 0 {
			t.Fatal("invalid HTTP body reached submit", rec.Code, rec.Body.String(), port.calls)
		}
	}
	req := httptest.NewRequest("POST", "/harness/v1/tasks", strings.NewReader(valid))
	req.Header.Set("Authorization", "Bearer owned")
	rec := httptest.NewRecorder()
	mux.ServeHTTP(rec, req)
	if rec.Code != 202 || port.calls != 1 || port.last.WorkspaceRef != "opaque" {
		t.Fatal("valid transport", rec.Code, rec.Body.String())
	}
	for _, url := range []string{"/harness/v1/tasks?project_id=p&cursor=01", "/harness/v1/tasks?project_id=p&limit=101", "/harness/v1/tasks?project_id=p&project_id=q"} {
		req = httptest.NewRequest("GET", url, nil)
		req.Header.Set("Authorization", "Bearer owned")
		rec = httptest.NewRecorder()
		mux.ServeHTTP(rec, req)
		if rec.Code != 400 {
			t.Fatal("invalid query accepted", url, rec.Code)
		}
	}
}
