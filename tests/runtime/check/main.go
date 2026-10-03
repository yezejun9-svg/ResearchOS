// Command check is the W05-01 construction qualification for the delegated runtime loop: a real
// Windows Job Object worker owns one admitted Run, really reads and writes files inside a bounded
// workspace, and its outcome is bound to the domain service's Run/Task, lease epoch and event ledger.
// Everything here drives the real adapters and the real domain service over a real SQLite database.
// Model tool execution and the pinned executor binary are BLOCKED and reported as BLOCKED; no fixture
// is presented as a live model capability. Prints one JSON assertion report for the dispatcher.
package main

import (
	"bytes"
	"context"
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
	"time"

	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/store"
)

var ids []string
var failures []map[string]string
var notVerified []string
var diagnostics []domain.Object

func ok(label string, cond bool, detail ...any) {
	if cond {
		ids = append(ids, label)
		return
	}
	parts := make([]string, 0, len(detail))
	for _, d := range detail {
		s := fmt.Sprint(d)
		if len(s) > 600 {
			s = s[:600]
		}
		parts = append(parts, s)
	}
	failures = append(failures, map[string]string{"id": label, "detail": strings.Join(parts, " | ")})
}

func skip(label, reason string) { notVerified = append(notVerified, label+": "+reason) }

func note(probe string, cond bool, detail any) {
	diagnostics = append(diagnostics, domain.Object{"probe": probe, "observed": cond, "detail": truncate(detail)})
}

func truncate(v any) any {
	s := fmt.Sprint(v)
	if len(s) > 500 {
		return s[:500]
	}
	return v
}

func faultOf(e error) (int, string) {
	var f *domain.Fault
	if errors.As(e, &f) {
		return f.Status, f.Code
	}
	return 0, ""
}

func sha(b []byte) string { s := sha256.Sum256(b); return "sha256:" + hex.EncodeToString(s[:]) }

type harness struct {
	db      *sql.DB
	dir     string
	handler http.Handler
	svc     *domain.Service
	token   string
	project string
	base    string
}

func repoRoot() string {
	d, e := os.Getwd()
	if e != nil {
		panic(e)
	}
	for i := 0; i < 8; i++ {
		if _, e = os.Stat(filepath.Join(d, "migrations", "sqlite", "0002_domain.sql")); e == nil {
			return d
		}
		d = filepath.Dir(d)
	}
	panic("repository root not found")
}

func boot(ctx context.Context, dir string) (*harness, error) {
	if e := os.MkdirAll(dir, 0o700); e != nil {
		return nil, e
	}
	db, e := store.Open(filepath.Join(dir, "w0501.sqlite"))
	if e != nil {
		return nil, e
	}
	root := repoRoot()
	if e = store.Bootstrap(ctx, db, filepath.Join(root, "migrations", "sqlite", "0001_bootstrap.sql")); e != nil {
		return nil, e
	}
	s, e := domain.New(db, filepath.Join(root, "spec/v2.0/contracts"), filepath.Join(root, "migrations", "sqlite", "0002_domain.sql"))
	if e != nil {
		return nil, e
	}
	h := &harness{db: db, dir: dir, svc: s, handler: s.Handler()}
	p := domain.Principal{ID: "w0501-owner", Roles: []string{"OWNER", "PLANNER", "EXECUTOR", "SCHEDULER"}, CanCreateProject: true}
	if e = h.svc.ProvisionPrincipal(ctx, p); e != nil {
		return nil, e
	}
	if h.token, e = h.svc.IssueCredential(ctx, p.ID, 15*time.Minute); e != nil {
		return nil, e
	}
	code, project, body := h.api(ctx, "POST", "/v1/projects", domain.ID(), "", domain.Object{
		"name": "w0501 delegated runtime", "intent": "one controlled loop over a real worker", "facts": domain.Empty(),
		"accepted_scope": []any{"qualification"}, "constraints": domain.Empty(), "source_configs": domain.Empty(),
		"source_document_refs": domain.Empty(), "read_snapshot_ids": domain.Empty()})
	if code != 201 {
		return nil, fmt.Errorf("project %d %s", code, body)
	}
	h.project = domain.Str(project, "project_id")
	h.base = "/v1/projects/" + h.project
	return h, nil
}

func (h *harness) api(ctx context.Context, method, path, key, etag string, body any) (int, domain.Object, string) {
	var raw []byte
	switch v := body.(type) {
	case nil:
	case []byte:
		raw = v
	default:
		raw = domain.Bytes(v)
	}
	r := httptest.NewRequest(method, path, bytes.NewReader(raw))
	r.Header.Set("Authorization", "Bearer "+h.token)
	if key != "" {
		r.Header.Set("Idempotency-Key", key)
	}
	if etag != "" {
		r.Header.Set("If-Match", etag)
	}
	w := httptest.NewRecorder()
	h.handler.ServeHTTP(w, r)
	out := domain.Object{}
	_ = json.Unmarshal(w.Body.Bytes(), &out)
	return w.Code, out, w.Body.String()
}

func (h *harness) stateTag(ctx context.Context) string {
	_, s, _ := h.api(ctx, "GET", h.base+"/state", "", "", nil)
	return tagOf(s)
}

func tagOf(o domain.Object) string { e, _ := domain.ETag(o); return e }

func main() {
	if code, routed := routeLegacy(); routed {
		os.Exit(code)
	}
	ctx := context.Background()
	defer func() {
		if r := recover(); r != nil {
			failures = append(failures, map[string]string{"id": "PANIC", "detail": fmt.Sprint(r)})
		}
		if len(ids) == 0 && len(failures) == 0 {
			failures = append(failures, map[string]string{"id": "NO-ASSERTIONS-RECORDED",
				"detail": "a run that recorded nothing is never a pass"})
		}
		status := "PASS"
		if len(failures) > 0 {
			status = "FAIL"
		}
		out, _ := json.Marshal(map[string]any{"status": status, "assertions": len(ids), "assertion_ids": ids,
			"failures": failures, "not_verified": sortedUnique(notVerified), "diagnostics": diagnostics,
			"scope":       "CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE",
			"environment": map[string]any{"os": runtime.GOOS, "windows_host": runtime.GOOS == "windows"}})
		fmt.Println(string(out))
		if len(failures) > 0 {
			os.Exit(1)
		}
	}()

	routingTruthTableOK()
	dir := filepath.Join(repoRoot(), ".local", "w0501-run")
	_ = os.RemoveAll(dir)
	h, e := boot(ctx, dir)
	if e != nil {
		ok("W0501-HARNESS-BOOT", false, e)
		return
	}
	defer h.db.Close()

	adapterPhase(ctx)
	protocolPhase()
	servicePhase(ctx, h)
}

func sortedUnique(in []string) []string {
	seen := map[string]bool{}
	out := []string{}
	for _, s := range in {
		if !seen[s] {
			seen[s] = true
			out = append(out, s)
		}
	}
	sort.Strings(out)
	return out
}
