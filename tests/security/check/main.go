// Command check is the W17-01 construction qualification for the trusted local host boundary:
// one-time OWNER bootstrap bound to the OS user, repeated-bootstrap protection, short session
// renewal that never loses state, provider credentials that only ever enter through the native
// frame and stay out of envelopes/logs/events/argv, workspace-root binding with reparse and
// permission checks, single-use selection references, and the negative matrix (no credential,
// expired credential, wrong project, revoked principal, another OS user, oversized or malformed
// frame, replay). Prints one JSON assertion report for the dispatcher.
package main

import (
	"context"
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"reflect"
	"sort"
	"strings"
	"time"

	"researchos.local/research-os/internal/api"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/host"
	"researchos.local/research-os/internal/store"
)

var ids []string
var failures []map[string]string

func ok(label string, cond bool, detail ...any) {
	if cond {
		ids = append(ids, label)
		return
	}
	parts := make([]string, 0, len(detail))
	for _, d := range detail {
		s := fmt.Sprint(d)
		if len(s) > 900 {
			s = s[:900]
		}
		parts = append(parts, s)
	}
	failures = append(failures, map[string]string{"id": label, "detail": strings.Join(parts, " | ")})
}

type harness struct {
	db     *sql.DB
	dir    string
	host   *host.Host
	clock  *fakeClock
	root   string
	webDir string
	svc    *domain.Service
	ts     *httptest.Server
	token  string
}

type fakeClock struct{ at time.Time }

func (c *fakeClock) Now() time.Time      { return c.at.UTC() }
func (c *fakeClock) Add(d time.Duration) { c.at = c.at.Add(d) }

func main() {
	ctx := context.Background()
	defer func() {
		if r := recover(); r != nil {
			failures = append(failures, map[string]string{"id": "PANIC", "detail": fmt.Sprint(r)})
		}
		if len(ids) == 0 {
			failures = append(failures, map[string]string{"id": "NO-ASSERTIONS-RECORDED",
				"detail": "a run that recorded nothing is never a pass"})
		}
		status := "PASS"
		if len(failures) > 0 {
			status = "FAIL"
		}
		out, _ := json.Marshal(map[string]any{"status": status, "assertions": len(ids), "assertion_ids": ids,
			"failures": failures, "not_verified": sortedUnique(notVerified),
			"scope":       "CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE",
			"environment": map[string]any{"os": runtimeOS(), "windows_host": runtimeOS() == "windows"}})
		fmt.Println(string(out))
		if len(failures) > 0 {
			os.Exit(1)
		}
	}()

	repo := repoRoot()
	h, err := newHarness(ctx, repo)
	if err != nil {
		ok("HARNESS", false, err)
		return
	}
	defer h.close()

	bootstrapPhase(ctx, h)
	renewPhase(ctx, h)
	credentialPhase(ctx, h)
	workspacePhase(ctx, h)
	transportPhase(ctx, h)
	gradingPhase(ctx, h)
	httpChainPhase(ctx, h)
}

func repoRoot() string {
	root, _ := os.Getwd()
	for i := 0; i < 5; i++ {
		if _, err := os.Stat(filepath.Join(root, "migrations", "sqlite")); err == nil {
			return root
		}
		root = filepath.Dir(root)
	}
	return root
}

func newHarness(ctx context.Context, repo string) (*harness, error) {
	tmp, err := os.MkdirTemp(filepath.Join(repo, ".local"), "w1701-")
	if err != nil {
		return nil, err
	}
	db, err := store.Open(filepath.Join(tmp, "p.sqlite"))
	if err != nil {
		return nil, err
	}
	files, _ := filepath.Glob(filepath.Join(repo, "migrations/sqlite/0*.sql"))
	if len(files) != 20 {
		return nil, fmt.Errorf("baseline migrations %d", len(files))
	}
	for i, f := range files {
		b, _ := os.ReadFile(f)
		tx, err := db.BeginTx(ctx, nil)
		if err != nil {
			return nil, err
		}
		if _, err := tx.ExecContext(ctx, string(b)); err != nil {
			tx.Rollback()
			return nil, err
		}
		tx.ExecContext(ctx, `INSERT OR IGNORE INTO schema_migrations(version) VALUES (?)`, i+1)
		tx.Commit()
	}
	nb, _ := os.ReadFile(filepath.Join(repo, "migrations/sqlite/next_v24_sessions.sql"))
	tx, _ := db.BeginTx(ctx, nil)
	if _, err := tx.ExecContext(ctx, string(nb)); err != nil {
		tx.Rollback()
		return nil, err
	}
	tx.ExecContext(ctx, `INSERT OR IGNORE INTO schema_migrations(version) VALUES (9021)`)
	tx.Commit()

	dir := filepath.Join(tmp, "host")
	webDir := filepath.Join(tmp, "web")
	os.MkdirAll(webDir, 0o755)
	os.WriteFile(filepath.Join(webDir, "index.html"), []byte("<html></html>"), 0o644)

	svc, err := domain.New(db, filepath.Join(repo, "spec", "v2.0", "contracts"),
		filepath.Join(repo, "migrations", "sqlite", "0002_domain.sql"))
	if err != nil {
		return nil, err
	}
	hc := &fakeClock{at: time.Now().UTC()}
	hh, err := host.New(host.Config{DB: db, Dir: dir,
		ContractsDir:  filepath.Join(repo, "spec", "v2.0", "contracts"),
		MigrationFile: filepath.Join(repo, "migrations", "sqlite", "0002_domain.sql"),
		SchemaDir:     filepath.Join(repo, "tests", "contracts", "fixtures"),
		SessionTTL:    2 * time.Minute, Now: hc.Now})
	if err != nil {
		return nil, err
	}
	ts := httptest.NewServer(api.Handler(db, webDir, svc))
	h := &harness{db: db, dir: dir, host: hh, clock: hc, root: tmp, webDir: webDir, svc: svc, ts: ts}
	// This machine's loopback occasionally refuses the very first connect to a freshly created
	// httptest server. The harness warms that connection once, before any assertion can depend on
	// it, so a transport hiccup cannot be mistaken for an authorisation outcome. Only /healthz is
	// dialed here; no product decision is involved.
	if err := h.waitForTransport(); err != nil {
		return nil, err
	}
	return h, nil
}

func (h *harness) close() {
	if h.ts != nil {
		h.ts.Close()
	}
	if h.db != nil {
		h.db.Close()
	}
	if h.root != "" {
		os.RemoveAll(h.root)
	}
}

// waitForTransport retries a plain readiness GET until the loopback answers or 4 seconds pass.
func (h *harness) waitForTransport() error {
	deadline := time.Now().Add(4 * time.Second)
	var last error
	for time.Now().Before(deadline) {
		resp, err := http.Get(h.ts.URL + "/healthz")
		if err != nil {
			last = err
			time.Sleep(50 * time.Millisecond)
			continue
		}
		io.Copy(io.Discard, io.LimitReader(resp.Body, 4096))
		resp.Body.Close()
		if resp.StatusCode == 200 {
			return nil
		}
		last = fmt.Errorf("healthz status %d", resp.StatusCode)
		time.Sleep(50 * time.Millisecond)
	}
	return fmt.Errorf("test transport never became ready: %v", last)
}

// newHost builds another host over the same database in its own private directory, optionally
// with configuration the production default cannot supply (a substituted peer identity resolver,
// a non-pinned protocol version). The host's own real defaults stay untouched for the main harness.
func (h *harness) newHost(dir string, mutate func(*host.Config)) (*host.Host, error) {
	repo := repoRoot()
	cfg := host.Config{DB: h.db, Dir: dir,
		ContractsDir:  filepath.Join(repo, "spec", "v2.0", "contracts"),
		MigrationFile: filepath.Join(repo, "migrations", "sqlite", "0002_domain.sql"),
		SchemaDir:     filepath.Join(repo, "tests", "contracts", "fixtures"),
		SessionTTL:    2 * time.Minute, Now: h.clock.Now}
	if mutate != nil {
		mutate(&cfg)
	}
	return host.New(cfg)
}

func (h *harness) count1(ctx context.Context, q string, arg any) int64 {
	var n int64
	if err := h.db.QueryRowContext(ctx, q, arg).Scan(&n); err != nil {
		return -1
	}
	return n
}

// post sends one command envelope. The transport retry below is deliberately narrow: only a
// connection-level failure (never an HTTP status) is retried, up to three attempts, because this
// machine's loopback occasionally refuses the very first connect to a freshly created httptest
// server. Assertion outcomes must not depend on that.
func (h *harness) post(body string, token string) (int, []byte) {
	var lastErr error
	for attempt := 0; attempt < 3; attempt++ {
		req, err := http.NewRequest("POST", h.ts.URL+"/v2/command", strings.NewReader(body))
		if err != nil {
			return 0, []byte(err.Error())
		}
		req.Header.Set("Content-Type", "application/json")
		if token != "" {
			req.Header.Set("Authorization", "Bearer "+token)
		}
		resp, err := h.ts.Client().Do(req)
		if err != nil {
			lastErr = err
			time.Sleep(50 * time.Millisecond)
			continue
		}
		defer resp.Body.Close()
		b, _ := io.ReadAll(resp.Body)
		return resp.StatusCode, b
	}
	return 0, []byte(fmt.Sprint(lastErr))
}

func (h *harness) count(ctx context.Context, q string) int64 {
	var n int64
	h.db.QueryRowContext(ctx, q).Scan(&n)
	return n
}

func (h *harness) census(ctx context.Context) string {
	var b strings.Builder
	for _, q := range []string{
		`SELECT count(*) FROM domain_objects`, `SELECT count(*) FROM client_sessions`,
		`SELECT count(*) FROM outbox`, `SELECT count(*) FROM auth_principals`,
		`SELECT coalesce(sum(length(body)),0) FROM domain_objects`,
	} {
		fmt.Fprintf(&b, "%d;", h.count(ctx, q))
	}
	return b.String()
}

func (h *harness) censusHash(ctx context.Context) string {
	sum := sha256.Sum256([]byte(h.census(ctx)))
	return hex.EncodeToString(sum[:8])
}

// frame builds a native frame with an arbitrary payload so negative cases can send shapes the
// contract does not allow.
func frame(kind, clientID string, payload any) []byte {
	b, _ := json.Marshal(map[string]any{"kind": kind, "client_id": clientID, "payload": payload})
	return b
}

func decodeReply(raw []byte) (string, map[string]any, map[string]any) {
	var f struct {
		Kind    string         `json:"kind"`
		Error   map[string]any `json:"error"`
		Payload map[string]any `json:"payload"`
	}
	json.Unmarshal(raw, &f)
	return f.Kind, f.Payload, f.Error
}

// vaultHasNoReadAPI asserts structurally that no exported host or vault surface hands plaintext
// back: only references, states and booleans may cross the boundary.
func vaultHasNoReadAPI() (bool, []string) {
	bad := []string{}
	for _, target := range []any{(*host.Host)(nil)} {
		t := reflect.TypeOf(target).Elem()
		for i := 0; i < t.NumMethod(); i++ {
			name := t.Method(i).Name
			low := strings.ToLower(name)
			if strings.Contains(low, "plaintext") || strings.Contains(low, "readcredential") ||
				strings.Contains(low, "getcredential") || strings.Contains(low, "export") ||
				strings.Contains(low, "dump") {
				bad = append(bad, t.String()+"."+name)
			}
		}
	}
	return len(bad) == 0, bad
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
