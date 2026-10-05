// Command check is the W12-01 construction qualification for cost reservation, settlement and
// bounded retry. It drives the real domain service over a real SQLite database through the real
// HTTP handler, and prints one JSON assertion report for the command dispatcher.
//
// Nothing here is a product acceptance: scope says CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE, and
// cases C11/C13/C14/C15/C16 keep their own final owner at parent W12-99.
package main

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
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

// diagnostics records the actual answer beside a refusal assertion even when the assertion
// passed, because a mutant that leaves a refusal green is only explainable if the response body
// was captured while it was still passing.
var diagnostics []map[string]any

func note(probe string, code int, body string) {
	diagnostics = append(diagnostics, map[string]any{"probe": probe, "code": code, "body": truncate(body, 320)})
}

func truncate(s string, n int) string {
	if len(s) > n {
		return s[:n]
	}
	return s
}

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

// faultOf returns both halves of a typed refusal. Matching only the code substring let a refusal
// move to another HTTP status while the suite stayed green, so every gate below compares both.
func faultOf(e error) (int, string) {
	var f *domain.Fault
	if errors.As(e, &f) {
		return f.Status, f.Code
	}
	return 0, ""
}

func tagOf(o domain.Object) string {
	etag, _ := domain.ETag(o)
	return etag
}

type harness struct {
	db      *sql.DB
	dir     string
	svc     *domain.Service
	handler http.Handler
	token   string
	project string
	base    string
}

// boot opens a real database, applies the real migrations and creates a real project. The directory
// lives under the repository's own .local so a run is reproducible and never touches the product
// data root.
func boot(ctx context.Context, dir string) (*harness, error) {
	if e := os.MkdirAll(dir, 0o755); e != nil {
		return nil, e
	}
	db, e := store.Open(filepath.Join(dir, "w1201.sqlite"))
	if e != nil {
		return nil, e
	}
	repo := repoRoot()
	if e = store.Bootstrap(ctx, db, filepath.Join(repo, "migrations", "sqlite", "0001_bootstrap.sql")); e != nil {
		return nil, e
	}
	s, e := domain.New(db, filepath.Join(repo, "spec", "v2.0", "contracts"), filepath.Join(repo, "migrations", "sqlite", "0002_domain.sql"))
	if e != nil {
		return nil, e
	}
	h := &harness{db: db, dir: dir, svc: s, handler: s.Handler()}
	p := domain.Principal{ID: "w1201-owner", Roles: []string{"OWNER", "PLANNER", "EXECUTOR", "SCHEDULER"}, CanCreateProject: true}
	if e = h.svc.ProvisionPrincipal(ctx, p); e != nil {
		return nil, e
	}
	if h.token, e = h.svc.IssueCredential(ctx, p.ID, 15*time.Minute); e != nil {
		return nil, e
	}
	code, project, body := h.api(ctx, "POST", "/v1/projects", domain.ID(), "", domain.Object{
		"name": "W12-01 cost qualification", "intent": "reserve, settle and retry within bounds",
		"facts": domain.Empty(), "accepted_scope": []any{"qualification"}, "constraints": domain.Empty(),
		"source_configs": domain.Empty(), "source_document_refs": domain.Empty(), "read_snapshot_ids": domain.Empty()})
	if code != 201 {
		return nil, fmt.Errorf("project creation %d %s", code, body)
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

func (h *harness) liveState(ctx context.Context) (domain.Object, string) {
	_, state, _ := h.api(ctx, "GET", h.base+"/state", "", "", nil)
	return state, tagOf(state)
}

// ledger posts one CostEntryRequest and reports the status plus the refusal shape.
func (h *harness) ledger(ctx context.Context, tag string, body domain.Object) (int, domain.Object, string) {
	return h.api(ctx, "POST", h.base+"/budget-ledger", domain.ID(), tag, body)
}

func (h *harness) stateTag(ctx context.Context) string {
	_, state, _ := h.api(ctx, "GET", h.base+"/state", "", "", nil)
	return tagOf(state)
}

func dollars(amount string) domain.Object {
	return domain.Object{"amount": amount, "currency": "USD"}
}

func main() {
	// The accepted v2.0 fixture harness owns every selector this card does not serve; forwarding
	// them keeps binding W12-01 to the name test.resources from shadowing W12-G01/G02 or the
	// formal cases C11/C13/C14/C15/C16.
	if code, routed := routeLegacy(); routed {
		os.Exit(code)
	}
	ctx := context.Background()
	defer func() {
		if r := recover(); r != nil {
			failures = append(failures, map[string]string{"id": "PANIC", "detail": fmt.Sprint(r)})
		}
		if os.Getenv("RESEARCHOS_CHECK_ID") == "W12-02" {
			// Reconciled in the report path, not at the end of the phase, because the phase returns early
			// whenever a precondition cannot be built and those are exactly the runs worth flagging.
			w1202RosterOK()
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

	dir := filepath.Join(repoRoot(), ".local", "w1201-run")
	_ = os.RemoveAll(dir)
	h, e := boot(ctx, dir)
	if e != nil {
		ok("W1201-HARNESS-BOOT", false, e)
		return
	}
	defer h.db.Close()

	defaultsPhase(ctx, h)
	graph, e := orchestrationGraph(ctx, h, "W1201-RUN-ADMITTED")
	if e != nil {
		ok("W1201-RUN-ADMITTED", false, e)
		skip("W1201-LEDGER-COLUMNS-SEPARATED", "no run could be admitted: "+e.Error())
		return
	}
	if os.Getenv("RESEARCHOS_CHECK_ID") == "W12-02" {
		// A different selector on the same command key serves a different card; the accepted W12-01 phases
		// stay untouched for their own selector and for a selector-less developer run.
		w1202Phase(ctx, h, graph)
		return
	}
	// the start-time refusal probe runs before the ledger probes: it needs the Goal policy still at its
	// default so an unresolved liability can enter, and it restores that policy on the way out
	startRefusalPhase(ctx, h, graph)
	ledgerPhase(ctx, h, graph)
	restartPhase(ctx, h, graph)
}

// routingTruthTable pins the forwarding rule as data, so a later edit that silently swallows an
// accepted selector fails a named assertion instead of quietly returning NOT_IMPLEMENTED.
func routingTruthTableOK() {
	rows := []struct {
		check, caseID, task string
		serve               bool
	}{
		{"W12-01", "", "W12", true},
		{"W12-02", "", "W12", true},
		// a run with no selector at all is a developer run of this card, not a forward
		{"", "", "", true},
		{"W12-G01", "", "W12", false},
		{"W12-G02", "", "W12", false},
		{"", "C13", "W12", false},
		{"", "C11", "W12", false},
		{"W12-01", "C13", "W12", false},
		{"W04-02", "", "W04", false},
	}
	all := true
	for _, r := range rows {
		// pass requires forwarding exactly when the row is NOT served here
		if got := routesToLegacy(r.check, r.caseID, r.task) != !r.serve; got {
			all = false
		}
	}
	ok("W1201-ROUTING-TRUTH-TABLE", all, rows)
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

// goTest runs the package's own test binary with the locked toolchain and returns its stdout.
func goTest(args ...string) (string, error) {
	goExe := os.Getenv("RESEARCHOS_GO")
	if goExe == "" {
		// the dispatcher pins the locked toolchain through tool_env; a developer running this by
		// hand falls back to the same repository-local binary rather than whatever go is on PATH
		goExe = filepath.Join(repoRoot(), ".local", "tools", "go1.27.1", "go", "bin", "go.exe")
		if _, e := os.Stat(goExe); e != nil {
			return "", fmt.Errorf("no locked toolchain: RESEARCHOS_GO is unset and %s is missing", goExe)
		}
	}
	cmd := exec.Command(goExe, append([]string{"test", "./internal/domain", "-count=1"}, args...)...)
	cmd.Dir = repoRoot()
	out, e := cmd.CombinedOutput()
	return string(out), e
}

func tail(s string) string {
	if len(s) > 400 {
		return s[len(s)-400:]
	}
	return s
}
