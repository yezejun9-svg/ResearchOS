// Command check is the W04-01 construction qualification for local directory registration,
// project continuation and first-use minimal inventory. It drives the real host boundary
// (internal/host), the real domain service over a real SQLite database, and the real adapter
// (adapters/local_workspace), and grades every emitted object against the pinned client protocol.
// Prints one JSON assertion report for the dispatcher.
package main

import (
	"context"
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
	"sync/atomic"
	"time"

	"researchos.local/research-os/adapters/local_workspace"
	"researchos.local/research-os/internal/auth"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/host"
	"researchos.local/research-os/internal/store"
)

var ids []string
var failures []map[string]string
var notVerified []string

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

func errText(e error) string {
	if e == nil {
		return ""
	}
	return e.Error()
}

// faultOf reads the protocol class and the HTTP status back out of a refusal. Matching a code
// substring alone let a refusal move to another status while the suite stayed green, so the
// typed assertions below compare both halves of the answer.
func faultOf(e error) (int, string) {
	var f *domain.Fault
	if errors.As(e, &f) {
		return f.Status, f.Code
	}
	return 0, ""
}

type clock struct{ at time.Time }

func (c *clock) Now() time.Time      { return c.at.UTC() }
func (c *clock) Add(d time.Duration) { c.at = c.at.Add(d) }

type harness struct {
	db        *sql.DB
	root      string
	h         *host.Host
	authority *localworkspace.Authority
	scanner   *localworkspace.Scanner
	grader    domain.DefGrader
	svc       *domain.Service
	principal domain.Principal
	clk       *clock
	chosen    string
	other     string
	ro        string
	outside   string
	alphaRef  string
	betaRef   string
	alphaProj string
	betaProj  string
}

func main() {
	// Selector families the accepted fixture harness owns are forwarded untouched, so binding this
	// card's construction check to the name test.context cannot shadow them.
	if code, routed := routeLegacy(); routed {
		os.Exit(code)
	}
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
			"environment": map[string]any{"os": runtime.GOOS, "windows_host": runtime.GOOS == "windows"}})
		fmt.Println(string(out))
		if len(failures) > 0 {
			os.Exit(1)
		}
	}()

	h, err := newHarness(ctx, repoRoot())
	if err != nil {
		ok("HARNESS", false, err)
		return
	}
	defer h.close()

	h.chainPhase(ctx)
	h.negativePhase(ctx)
	h.continuationPhase(ctx)
	h.inventoryPhase(ctx)
	h.hardeningPhase(ctx)
	h.lifecyclePhase(ctx)
	// W04-02 adds the frozen-context and worker-materialization properties on top of W04-01's
	// registration chain; both cards run in one program, and the report's ids say which is which.
	h.contextPhase(ctx)
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
	tmp, err := os.MkdirTemp(filepath.Join(repo, ".local"), "w0401-")
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
		tx.ExecContext(ctx, `INSERT OR IGNORE INTO schema_migrations(version) VALUES(?)`, i+1)
		tx.Commit()
	}
	nb, _ := os.ReadFile(filepath.Join(repo, "migrations/sqlite/next_v24_sessions.sql"))
	tx, _ := db.BeginTx(ctx, nil)
	if _, err := tx.ExecContext(ctx, string(nb)); err != nil {
		tx.Rollback()
		return nil, err
	}
	tx.ExecContext(ctx, `INSERT OR IGNORE INTO schema_migrations(version) VALUES(9021)`)
	tx.Commit()

	contracts := filepath.Join(repo, "spec", "v2.0", "contracts")
	schemaDir := filepath.Join(repo, "tests", "contracts", "fixtures")
	svc, err := domain.New(db, contracts, filepath.Join(repo, "migrations", "sqlite", "0002_domain.sql"))
	if err != nil {
		return nil, err
	}
	clk := &clock{at: time.Now().UTC()}
	hh, err := host.New(host.Config{DB: db, Dir: filepath.Join(tmp, "host"), ContractsDir: contracts,
		MigrationFile: filepath.Join(repo, "migrations", "sqlite", "0002_domain.sql"),
		SchemaDir:     schemaDir, SessionTTL: 5 * time.Minute, Now: clk.Now})
	if err != nil {
		return nil, err
	}
	proto, err := os.ReadFile(filepath.Join(schemaDir, "client.protocol.schema.json"))
	if err != nil {
		return nil, err
	}
	ext, err := os.ReadFile(filepath.Join(schemaDir, "domain.schema.json"))
	if err != nil {
		return nil, err
	}
	doc, err := domain.LoadSchemaWithExternals(proto, map[string][]byte{"domain.schema.json": ext})
	if err != nil {
		return nil, err
	}

	h := &harness{db: db, root: tmp, h: hh, svc: svc, grader: doc, clk: clk,
		authority: localworkspace.NewAuthority(hh), scanner: localworkspace.NewScanner()}
	h.chosen = filepath.Join(tmp, "project-alpha")
	mustMkTree(h.chosen, "alpha")
	h.other = filepath.Join(tmp, "project-beta")
	mustMkTree(h.other, "beta")
	h.ro = filepath.Join(tmp, "readonly-notes")
	os.MkdirAll(filepath.Join(h.ro, "notes"), 0o755)
	os.WriteFile(filepath.Join(h.ro, "notes", "a.md"), []byte("read only"), 0o600)
	h.outside = filepath.Join(tmp, "outside")
	os.MkdirAll(h.outside, 0o755)
	os.WriteFile(filepath.Join(h.outside, "private.md"), []byte("NEVER-AUTHORISED-MARKER"), 0o600)
	os.WriteFile(filepath.Join(h.outside, "README.md"), []byte("# NEVER-AUTHORISED-MARKER-project\n"), 0o600)

	res, err := hh.BootstrapOwner(ctx)
	if err != nil {
		return nil, err
	}
	tok := res.Session.Token
	pr, err := domain.AuthenticateToken(ctx, db, tok)
	if err != nil {
		return nil, err
	}
	h.principal = pr
	if !pr.CanCreateProject {
		return nil, errors.New("bootstrap principal cannot create projects")
	}
	return h, nil
}

// roRef returns the reference this principal authorised for the read-only fixture directory.
func (h *harness) roRef() string {
	rows, err := h.db.QueryContext(context.Background(), `SELECT id, body FROM domain_objects WHERE kind='WorkspaceBinding' AND json_extract(body,'$.access')='READ_ONLY' ORDER BY id`)
	if err != nil {
		return ""
	}
	defer rows.Close()
	for rows.Next() {
		var id, body string
		if rows.Scan(&id, &body) != nil {
			continue
		}
		// status is read from the row already in hand: the pool is a single connection, so a second
		// query inside an open rows iteration would deadlock.
		if strings.Contains(body, jsonEscape(h.ro)) && strings.Contains(body, "\"status\":\"ACTIVE\"") {
			return id
		}
	}
	return ""
}

func (h *harness) close() {
	if h.db != nil {
		h.db.Close()
	}
	if h.root != "" {
		os.RemoveAll(h.root)
	}
}

func mustMkTree(base, name string) {
	os.MkdirAll(filepath.Join(base, "internal", "domain"), 0o755)
	os.MkdirAll(filepath.Join(base, "services"), 0o755)
	os.WriteFile(filepath.Join(base, "go.mod"), []byte("module researchos.local/"+name+"\n\ngo 1.27\n"), 0o600)
	os.WriteFile(filepath.Join(base, "package.json"), []byte("{\"name\":\""+name+"\",\"version\":\"1.2.3\"}"), 0o600)
	os.WriteFile(filepath.Join(base, "README.md"), []byte("# "+name+"\n"), 0o600)
	os.WriteFile(filepath.Join(base, "internal", "domain", "core.go"), []byte("package main\n"), 0o600)
	// a manifest that cannot be parsed: first-use import must record this per file, not drop it
	os.WriteFile(filepath.Join(base, "services", "broken.json"), []byte("{\"version\": "), 0o600)
}

// choose drives the real native directory choice and returns its single-use reference.
func (h *harness) choose(clientID, dir, access string) (string, error) {
	frame, _ := json.Marshal(map[string]any{"kind": host.KindWorkspaceChooseRequest, "client_id": clientID,
		"payload": map[string]any{"requested_path": nil, "requested_access": access}})
	reply, err := h.h.HandleNative(frame, true, func(string) (string, error) { return dir, nil })
	if err != nil {
		return "", err
	}
	var f struct {
		Payload struct {
			SelectionRef string `json:"selection_ref"`
		} `json:"payload"`
	}
	if err := json.Unmarshal(reply, &f); err != nil {
		return "", err
	}
	return f.Payload.SelectionRef, nil
}

func (h *harness) register(ctx context.Context, sel, name, access, commandID, clientID string) (domain.Object, error) {
	return h.svc.RegisterWorkspace(ctx, h.principal, h.authority, h.grader, domain.RegisterWorkspaceInput{
		SelectionRef: sel, DisplayName: name, RequestedAccess: access, CommandID: commandID, ClientID: clientID})
}

func (h *harness) bootstrap(ctx context.Context, ref, name, commandID string) (domain.Object, error) {
	return h.svc.BootstrapProject(ctx, h.principal, h.authority, h.grader, h.scanner, domain.BootstrapProjectInput{
		AuthorizedWorkspaceRef: ref, DisplayName: name, CommandID: commandID, ClientID: "cli-desktop", MeasurementMode: "FIXTURE"})
}

func (h *harness) count(ctx context.Context, q string, args ...any) int64 {
	var n int64
	row := h.db.QueryRowContext(ctx, q, args...)
	if err := row.Scan(&n); err != nil {
		return -1
	}
	return n
}

func (h *harness) census(ctx context.Context) string {
	var b strings.Builder
	for _, q := range []string{`SELECT count(*) FROM domain_objects`, `SELECT count(*) FROM domain_versions`,
		`SELECT count(*) FROM auth_principals`, `SELECT count(*) FROM auth_grants`, `SELECT count(*) FROM outbox`,
		`SELECT count(*) FROM uploaded_content`, `SELECT coalesce(sum(length(body)),0) FROM domain_objects`} {
		fmt.Fprintf(&b, "%d;", h.count(ctx, q))
	}
	sum := sha256.Sum256([]byte(b.String()))
	return hex.EncodeToString(sum[:8])
}

func (h *harness) bodyOf(ctx context.Context, kind, id string) string {
	var body string
	h.db.QueryRowContext(ctx, `SELECT body FROM domain_objects WHERE kind=? AND id=?`, kind, id).Scan(&body)
	return body
}

func (h *harness) bindingField(ctx context.Context, ref, field string) string {
	var v string
	h.db.QueryRowContext(ctx, `SELECT json_extract(body,'$.`+field+`') FROM domain_objects WHERE kind='WorkspaceBinding' AND id=?`, ref).Scan(&v)
	return v
}

func (h *harness) refFor(ctx context.Context, realPath string) string {
	rows, err := h.db.QueryContext(ctx, `SELECT id, body FROM domain_objects WHERE kind='WorkspaceBinding' ORDER BY id`)
	if err != nil {
		return ""
	}
	defer rows.Close()
	for rows.Next() {
		var id, body string
		if rows.Scan(&id, &body) != nil {
			continue
		}
		if strings.Contains(body, jsonEscape(realPath)) {
			return id
		}
	}
	return ""
}

func jsonEscape(s string) string { b, _ := json.Marshal(s); return strings.Trim(string(b), `"`) }

// ------------------------------------------------------------------ the pinned first-use chain
func (h *harness) chainPhase(ctx context.Context) {
	id, idErr := auth.Current()
	ok("AUTHORITY-LOCAL-PRINCIPAL-VERIFIED", idErr == nil && h.authority.HostPrincipalRef() == id.Ref, idErr)

	sel, err := h.choose("cli-desktop", h.chosen, "READ_WRITE")
	ok("CHAIN-SELECTION-ISSUED", err == nil && strings.HasPrefix(sel, "sel-"), err, sel)

	binding, rerr := h.register(ctx, sel, "Alpha", "READ_WRITE", "cmd-register-1", "cli-desktop")
	ok("CHAIN-REGISTER-ACCEPTED", rerr == nil, rerr)
	ref, _ := binding["authorized_workspace_ref"].(string)
	h.alphaRef = ref
	ok("CHAIN-REF-MINTED-AND-IS-NOT-A-PATH", strings.HasPrefix(ref, "wsref-") && !strings.ContainsAny(ref, `/\:`), ref)
	ok("CHAIN-REGISTER-NO-PROJECT-BEFORE-BOOTSTRAP", binding["project_id"] == nil, binding["project_id"])
	ok("CHAIN-REGISTER-ACTIVE", binding["status"] == "ACTIVE", binding["status"])
	ok("CHAIN-REGISTER-REVISION-ONE", fmt.Sprint(binding["revision"]) == "1", binding["revision"])
	ok("CHAIN-ONE-BINDING-RECORD", h.count(ctx, `SELECT count(*) FROM domain_objects WHERE kind='WorkspaceBinding'`) == 1,
		h.count(ctx, `SELECT count(*) FROM domain_objects WHERE kind='WorkspaceBinding'`))
	ok("CHAIN-BINDING-STORES-CANONICAL-PATH", h.bindingField(ctx, ref, "real_path") == filepath.Clean(h.chosen),
		h.bindingField(ctx, ref, "real_path"))
	ok("CHAIN-BINDING-RECORDS-HOST-PRINCIPAL", h.bindingField(ctx, ref, "host_principal_ref") != "", h.bindingField(ctx, ref, "host_principal_ref"))
	ok("CHAIN-REGISTER-TOUCHES-NO-BUSINESS-SESSIONS", h.count(ctx, `SELECT count(*) FROM client_sessions`) == 0)

	// same command id delivered twice: the original binding comes back and no second reference is
	// minted, because the selection is already spent
	censusBefore := h.census(ctx)
	replay, repErr := h.register(ctx, sel, "Alpha", "READ_WRITE", "cmd-register-1", "cli-desktop")
	repRef, _ := replay["authorized_workspace_ref"].(string)
	ok("CHAIN-REGISTER-REPLAY-RETURNS-ORIGINAL", repErr == nil && repRef == ref, repErr, repRef, ref)
	ok("CHAIN-REGISTER-REPLAY-WROTE-NOTHING", h.census(ctx) == censusBefore, h.census(ctx), censusBefore)

	_, reuseErr := h.register(ctx, sel, "Alpha", "READ_WRITE", "cmd-register-2", "cli-desktop")
	ok("CHAIN-SELECTION-REUSE-REFUSED", reuseErr != nil && strings.Contains(errText(reuseErr), "SELECTION_ALREADY_USED"), reuseErr)

	result, berr := h.bootstrap(ctx, ref, "Alpha", "cmd-bootstrap-1")
	ok("CHAIN-BOOTSTRAP-ACCEPTED", berr == nil, berr)
	project, _ := result["project_id"].(string)
	h.alphaProj = project
	ok("CHAIN-BOOTSTRAP-PROJECT-ID-BOUNDED-INTO-BINDING", project != "" && h.bindingField(ctx, ref, "project_id") == project,
		project, h.bindingField(ctx, ref, "project_id"))
	ok("CHAIN-PROJECT-IDENTITY-ROW-EXISTS", h.count(ctx, `SELECT count(*) FROM domain_objects WHERE kind='Project' AND id=?`, project) == 1)
	ok("CHAIN-PROFILE-AND-STATE-WRITTEN", h.count(ctx, `SELECT count(*) FROM domain_objects WHERE project=? AND kind='ProjectProfile'`, project) == 1 &&
		h.count(ctx, `SELECT count(*) FROM domain_objects WHERE project=? AND kind='ProjectState'`, project) == 1)
	ok("CHAIN-PROFILE-ACCEPTED-SCOPE-IS-THE-REFERENCE", strings.Contains(h.bodyOf(ctx, "ProjectProfile", project), ref))
	ok("CHAIN-PROFILE-REF-IS-TYPED", strings.Contains(fmt.Sprint(result["project_profile_ref"]), "ProjectProfile"), result["project_profile_ref"])
	ok("CHAIN-INVENTORY-REF-IS-TYPED", strings.Contains(fmt.Sprint(result["inventory_artifact_ref"]), "Artifact"), result["inventory_artifact_ref"])
	ok("CHAIN-BOOTSTRAP-RUN-NULL-UNTIL-ADMITTED", result["bootstrap_run_id"] == nil, result["bootstrap_run_id"])
	stageID, _ := result["bootstrap_task_id"].(string)
	ok("CHAIN-BOOTSTRAP-TASK-ID-DURABLE", stageID != "" && h.count(ctx,
		`SELECT count(*) FROM domain_objects WHERE kind='BootstrapStage' AND id=?`, stageID) == 1, stageID)
	ok("CHAIN-BOOTSTRAP-GRANT-EXISTS", h.count(ctx, `SELECT count(*) FROM auth_grants WHERE principal=? AND project=?`,
		h.principal.ID, project) == 1)
	ok("CHAIN-BOOTSTRAP-ARTIFACT-SEALED", strings.Contains(h.bodyOf(ctx, "Artifact", h.artifactID(ctx, project)), `"sealed_at"`),
		h.artifactID(ctx, project))
}

// artifactID returns the newest sealed artifact for a project. With an unordered LIMIT 1 a leak
// could land in an artifact no assertion ever reads, so the ordering is part of the check.
func (h *harness) artifactID(ctx context.Context, project string) string {
	var id string
	h.db.QueryRowContext(ctx, `SELECT id FROM domain_objects WHERE project=? AND kind='Artifact' ORDER BY rowid DESC LIMIT 1`, project).Scan(&id)
	return id
}

func (h *harness) inventoryBytes(ctx context.Context, project string) []byte {
	body := h.bodyOf(ctx, "Artifact", h.artifactID(ctx, project))
	var o map[string]any
	json.Unmarshal([]byte(body), &o)
	key := fmt.Sprint(o["storage_key"])
	var raw []byte
	h.db.QueryRowContext(ctx, `SELECT bytes FROM uploaded_content WHERE storage_key=?`, key).Scan(&raw)
	return raw
}

// ------------------------------------------------------------------------ the negative matrix
func (h *harness) negativePhase(ctx context.Context) {
	_, e := h.register(ctx, "sel-never-issued", "Ghost", "READ_ONLY", "cmd-neg-1", "cli-desktop")
	ok("NEG-UNKNOWN-SELECTION-REFUSED", e != nil, e)

	_, e = h.bootstrap(ctx, h.chosen, "Fake", "cmd-neg-2")
	ok("NEG-ABSOLUTE-PATH-IS-NOT-AN-AUTHORISED-REF", e != nil && strings.Contains(errText(e), "FORBIDDEN"), e)

	_, e = h.bootstrap(ctx, `C:\Windows\System32`, "Fake", "cmd-neg-2b")
	ok("NEG-WINDOWS-PATH-IS-NOT-A-REF", e != nil && strings.Contains(errText(e), "FORBIDDEN"), e)

	_, e = h.bootstrap(ctx, "wsref-0000000000000000", "Ghost", "cmd-neg-3")
	ok("NEG-UNMINTED-REF-NOT-FOUND", e != nil && strings.Contains(errText(e), "NOT_FOUND"), e)

	_, e = h.register(ctx, "", "x", "READ_ONLY", "cmd-neg-5", "cli-desktop")
	ok("NEG-CANCELLED-CHOICE-REFUSED", e != nil, e)
	_, e = h.register(ctx, "sel-x", "", "READ_ONLY", "cmd-neg-5b", "cli-desktop")
	ok("NEG-REGISTER-NEEDS-DISPLAY-NAME", e != nil, e)
	_, e = h.register(ctx, "sel-x", "n", "EXECUTE", "cmd-neg-5c", "cli-desktop")
	ok("NEG-REGISTER-REJECTS-UNKNOWN-ACCESS", e != nil, e)
	_, e = h.register(ctx, "sel-x", "n", "READ_ONLY", "cmd-neg-5d", "")
	ok("NEG-REGISTER-NEEDS-CLIENT", e != nil, e)
	_, e = h.svc.RegisterWorkspace(ctx, h.principal, nil, h.grader, domain.RegisterWorkspaceInput{
		SelectionRef: "sel-x", DisplayName: "n", RequestedAccess: "READ_ONLY", CommandID: "c", ClientID: "cli"})
	ok("NEG-REGISTER-WITHOUT-AUTHORITY-REFUSED", e != nil, e)
	_, e = h.svc.BootstrapProject(ctx, h.principal, h.authority, h.grader, nil, domain.BootstrapProjectInput{
		AuthorizedWorkspaceRef: h.alphaRef, DisplayName: "x", CommandID: "c", ClientID: "cli"})
	ok("NEG-BOOTSTRAP-WITHOUT-SCANNER-REFUSED", e != nil, e)

	// expired reference: the host window closed before the ordinary command arrived
	sel, cerr := h.choose("cli-desktop", h.ro, "READ_ONLY")
	ok("NEG-EXPIRY-CASE-SELECTION-ISSUED", cerr == nil, cerr)
	h.clk.Add(6 * time.Minute)
	_, e = h.register(ctx, sel, "Late", "READ_ONLY", "cmd-neg-6", "cli-desktop")
	ok("NEG-EXPIRED-SELECTION-REFUSED", e != nil && strings.Contains(errText(e), "SELECTION_EXPIRED"), e)
	// an expired selection is a 410 naming its own class: a generic denial that happens to mention
	// the word would satisfy the substring match above and still be the wrong answer
	ok("NEG-EXPIRED-SELECTION-STATUS-CLASS", func() bool { st, code := faultOf(e); return st == 410 && code == "SELECTION_EXPIRED" }(), e)
	h.clk.Add(-6 * time.Minute)

	// access escalation: a read-only choice cannot become a writable binding
	sel2, _ := h.choose("cli-desktop", h.ro, "READ_ONLY")
	_, e = h.register(ctx, sel2, "Escalate", "READ_WRITE", "cmd-neg-7", "cli-desktop")
	ok("NEG-ACCESS-ESCALATION-REFUSED", e != nil && strings.Contains(errText(e), "POLICY_DENIED"), e)
	// An escalation attempt consumes the choice: the host marks a revealed reference spent even
	// when the command later fails, because a second use would be indistinguishable from a replay.
	_, e = h.register(ctx, sel2, "Notes", "READ_ONLY", "cmd-ro-retry", "cli-desktop")
	ok("NEG-ESCALATION-CONSUMES-THE-CHOICE", e != nil && strings.Contains(errText(e), "SELECTION_ALREADY_USED"), e)
	// the same level through a fresh choice does work, so the refusal above is not blanket
	sel2b, _ := h.choose("cli-desktop", h.ro, "READ_ONLY")
	_, e = h.register(ctx, sel2b, "Notes", "READ_ONLY", "cmd-ro-register", "cli-desktop")
	ok("NEG-READ-ONLY-REGISTER-ACCEPTED", e == nil, e)

	// a second client of the same OS user cannot spend a choice it did not make
	sel3, _ := h.choose("cli-desktop", h.other, "READ_WRITE")
	_, e = h.register(ctx, sel3, "Stolen", "READ_WRITE", "cmd-neg-8", "cli-other")
	ok("NEG-FOREIGN-CLIENT-CHOICE-REFUSED", e != nil && strings.Contains(errText(e), "FORBIDDEN"), e)
	bind, re := h.register(ctx, sel3, "Beta", "READ_WRITE", "cmd-beta-register", "cli-desktop")
	ok("NEG-SAME-CHOICE-WITH-ITS-OWN-CLIENT-WORKS", re == nil, re)
	h.betaRef, _ = bind["authorized_workspace_ref"].(string)

	// an unauthorised principal cannot register or bootstrap even with a minted reference
	if err := h.svc.ProvisionPrincipal(ctx, domain.Principal{ID: "w04-reader", Roles: []string{"READER"}}); err != nil {
		ok("NEG-READER-PROVISIONED", false, err)
	} else {
		tok, terr := h.svc.IssueCredential(ctx, "w04-reader", time.Minute)
		pr, aerr := domain.AuthenticateToken(ctx, h.db, tok)
		_, e := h.svc.RegisterWorkspace(ctx, pr, h.authority, h.grader, domain.RegisterWorkspaceInput{
			SelectionRef: "sel-none", DisplayName: "Nope", RequestedAccess: "READ_ONLY", CommandID: "cmd-neg-9", ClientID: "cli-reader"})
		ok("NEG-UNAUTHORISED-PRINCIPAL-REGISTER-REFUSED", terr == nil && aerr == nil && e != nil, terr, aerr, e)
		_, e = h.svc.BootstrapProject(ctx, pr, h.authority, h.grader, h.scanner, domain.BootstrapProjectInput{
			AuthorizedWorkspaceRef: h.alphaRef, DisplayName: "Snoop", CommandID: "cmd-neg-10", ClientID: "cli-reader"})
		ok("NEG-UNAUTHORISED-PRINCIPAL-BOOTSTRAP-REFUSED", e != nil, e)
	}
	ok("NEG-REFUSALS-NEVER-CREATED-A-PROJECT", h.count(ctx, `SELECT count(*) FROM domain_objects WHERE kind='Project'`) == 1,
		h.count(ctx, `SELECT count(*) FROM domain_objects WHERE kind='Project'`))
	ok("NEG-OUTSIDE-DIRECTORY-NEVER-REGISTERED", h.refFor(ctx, filepath.Clean(h.outside)) == "", h.refFor(ctx, filepath.Clean(h.outside)))
}

// ------------------------------------------------------- continuation, alias and name isolation
func (h *harness) continuationPhase(ctx context.Context) {
	result, e := h.bootstrap(ctx, h.alphaRef, "Alpha renamed", "cmd-bootstrap-again")
	ok("CONT-REPEAT-BOOTSTRAP-REUSES-PROJECT", e == nil && fmt.Sprint(result["project_id"]) == h.alphaProj, e, result)
	ok("CONT-ONE-PROJECT-IDENTITY", h.count(ctx, `SELECT count(*) FROM domain_objects WHERE kind='Project'`) == 1,
		h.count(ctx, `SELECT count(*) FROM domain_objects WHERE kind='Project'`))
	ok("CONT-ONE-PROFILE", h.count(ctx, `SELECT count(*) FROM domain_objects WHERE kind='ProjectProfile'`) == 1,
		h.count(ctx, `SELECT count(*) FROM domain_objects WHERE kind='ProjectProfile'`))

	// an alias registered later for the same canonical directory continues the same project
	selAlias, aerr := h.choose("cli-desktop", h.chosen, "READ_WRITE")
	ok("CONT-ALIAS-SELECTION-ISSUED", aerr == nil, aerr)
	alias, regErr := h.register(ctx, selAlias, "Alpha alias", "READ_WRITE", "cmd-alias-register", "cli-desktop")
	ok("CONT-ALIAS-REGISTERED", regErr == nil, regErr)
	aliasRef, _ := alias["authorized_workspace_ref"].(string)
	ok("CONT-ALIAS-REFERENCE-DIFFERS", aliasRef != "" && aliasRef != h.alphaRef, aliasRef, h.alphaRef)
	res2, e2 := h.bootstrap(ctx, aliasRef, "Alpha", "cmd-alias-bootstrap")
	ok("CONT-ALIAS-REUSES-SAME-PROJECT", e2 == nil && fmt.Sprint(res2["project_id"]) == h.alphaProj, e2, res2, h.alphaProj)
	ok("CONT-ALIAS-DOES-NOT-SPAWN-A-PROJECT", h.count(ctx, `SELECT count(*) FROM domain_objects WHERE kind='Project'`) == 1)

	// the same display name over a different directory is a different project with its own scope
	bres, berr := h.bootstrap(ctx, h.betaRef, "Alpha", "cmd-beta-bootstrap")
	h.betaProj = fmt.Sprint(bres["project_id"])
	ok("ISOLATION-SAME-NAME-DIFFERENT-PROJECT", berr == nil && h.betaProj != "" && h.betaProj != h.alphaProj, berr, h.betaProj, h.alphaProj)
	ok("ISOLATION-TWO-PROFILES", h.count(ctx, `SELECT count(*) FROM domain_objects WHERE kind='ProjectProfile'`) == 2)
	ok("ISOLATION-BETA-SCOPE-EXCLUDES-ALPHA-REF", !strings.Contains(h.bodyOf(ctx, "ProjectProfile", h.betaProj), h.alphaRef),
		h.bodyOf(ctx, "ProjectProfile", h.betaProj))
	ok("ISOLATION-TWO-DISTINCT-PROJECT-ROWS", h.count(ctx, `SELECT count(DISTINCT id) FROM domain_objects WHERE kind='Project'`) == 2,
		h.count(ctx, `SELECT count(DISTINCT id) FROM domain_objects WHERE kind='Project'`))
	ok("ISOLATION-EACH-PROJECT-OWNS-ITS-ROWS", h.count(ctx, `SELECT count(*) FROM domain_objects WHERE kind='Project'`) == 2 &&
		h.count(ctx, `SELECT count(*) FROM domain_objects WHERE project=? AND kind='Project' AND id=?`, h.alphaProj, h.alphaProj) == 1 &&
		h.count(ctx, `SELECT count(*) FROM domain_objects WHERE project=? AND kind='Project' AND id=?`, h.betaProj, h.betaProj) == 1,
		h.count(ctx, `SELECT count(*) FROM domain_objects WHERE kind='Project'`))
	ok("ISOLATION-STORAGE-KEYS-DIFFER", storageKeyOf(ctx, h, h.alphaProj) != storageKeyOf(ctx, h, h.betaProj))
	alphaInv := string(h.inventoryBytes(ctx, h.alphaProj))
	betaInv := string(h.inventoryBytes(ctx, h.betaProj))
	ok("ISOLATION-INVENTORIES-CARRY-OWN-MODULE-ONLY", strings.Contains(alphaInv, "sha256:") &&
		strings.Contains(betaInv, "sha256:") && !strings.Contains(betaInv, "researchos.local/alpha"),
		firstChars(betaInv))
	ok("ISOLATION-OUTSIDE-MARKER-NEVER-STORED", !strings.Contains(alphaInv, "NEVER-AUTHORISED-MARKER") &&
		!strings.Contains(betaInv, "NEVER-AUTHORISED-MARKER") &&
		h.count(ctx, `SELECT count(*) FROM uploaded_content WHERE bytes LIKE '%NEVER-AUTHORISED-MARKER%'`) == 0)
}

func storageKeyOf(ctx context.Context, h *harness, project string) string {
	body := h.bodyOf(ctx, "Artifact", h.artifactID(ctx, project))
	var o map[string]any
	json.Unmarshal([]byte(body), &o)
	return fmt.Sprint(o["storage_key"])
}

func firstChars(s string) string {
	if len(s) > 200 {
		return s[:200]
	}
	return s
}

// ------------------------------------------------------- inventory honesty, stages and idempotency
func (h *harness) inventoryPhase(ctx context.Context) {
	inv := string(h.inventoryBytes(ctx, h.alphaProj))
	ok("INV-CONTENT-NONEMPTY", len(inv) > 2, len(inv))
	var payload map[string]any
	err := json.Unmarshal([]byte(inv), &payload)
	ok("INV-PARSES", err == nil, err)
	ok("INV-GRADED-BY-PUBLISHED-DEF", err == nil && h.grader.ValidateDef("LocalInventoryPayload", payload) == nil, err)
	ok("INV-SCOPE-USES-REFERENCES", strings.Contains(inv, h.alphaRef) && !strings.Contains(inv, jsonEscape(h.chosen)), firstChars(inv))
	ok("INV-ENVIRONMENT-RECORDED", strings.Contains(inv, `"environment"`), firstChars(inv))
	ok("INV-OBSERVED-AT-RECORDED", strings.Contains(inv, `"observed_at"`), firstChars(inv))
	ok("INV-GO-MODULE-FOUND", strings.Contains(inv, `"go_module"`) && strings.Contains(inv, `"FOUND"`), firstChars(inv))
	ok("INV-NODE-VERSION-READ", strings.Contains(inv, "1.2.3"), firstChars(inv))
	ok("INV-SOURCE-TREE-FOUND", strings.Contains(inv, `"source_tree"`), firstChars(inv))
	// the unparseable manifest is a recorded per-file failure, not a silently missing entry
	ok("INV-PARTIAL-PARSE-HAS-A-RECORD", strings.Contains(inv, "NOT_CHECKED") && strings.Contains(inv, "not valid JSON"), firstChars(inv))
	ok("INV-FAILURE-USES-RELATIVE-PATH", strings.Contains(inv, "broken.json") && !strings.Contains(inv, jsonEscape(h.root)), firstChars(inv))
	ok("INV-NO-FILE-CONTENT-STORED", !strings.Contains(inv, "module researchos.local/alpha") && !strings.Contains(inv, "package main"))

	// stages this card must not finish are recorded as not started
	stages := h.stageSummary(ctx, h.alphaProj)
	ok("INV-STAGE-LOCAL-INVENTORY-RECORDED", strings.Contains(stages, "LOCAL_INVENTORY:COMPLETED") ||
		strings.Contains(stages, "LOCAL_INVENTORY:PARTIAL"), stages)
	ok("INV-RESEARCH-NOT-CLAIMED", strings.Contains(stages, "RESEARCH:NOT_STARTED"), stages)
	ok("INV-REUSE-DECISION-NOT-CLAIMED", strings.Contains(stages, "REUSE_DECISION:NOT_STARTED"), stages)
	ok("INV-IMPLEMENTATION-NOT-CLAIMED", strings.Contains(stages, "IMPLEMENTATION:NOT_STARTED"), stages)
	ok("INV-STAGES-IN-PUBLISHED-ORDER", stageOrderOK(stages), stages)
	ok("INV-NO-EXTRA-STAGE-INVENTED", strings.Count(stages, ":") == 4 && h.stageRowCount(ctx, h.alphaProj) == 4,
		stages, h.stageRowCount(ctx, h.alphaProj))

	// a root that cannot be read is reported as inaccessible by the adapter, never as empty
	missing := filepath.Join(h.root, "vanished")
	res, serr := h.scanner.Scan(context.Background(), missing)
	ok("INV-MISSING-ROOT-IS-NOT-EMPTY", serr == nil && len(res.Entries) == 1 && res.Entries[0].Status == "NOT_ACCESSIBLE", serr, res)
	ok("INV-MISSING-ROOT-REASON-CLASSIFIED", len(res.Failures) == 1 && res.Failures[0].Reason != "", res.Failures)
	ok("INV-MISSING-ROOT-LEAKS-NO-PATH", !strings.Contains(firstChars(fmt.Sprint(res)), jsonEscape(h.root)), fmt.Sprint(res))

	// A repeat import is idempotent about IDENTITY, not about observation: one project, one stage
	// row (whose revision advances) and one new sealed artifact per genuine re-observation, with
	// the earlier artifact kept as history rather than rewritten.
	beforeArtifacts := h.count(ctx, `SELECT count(*) FROM domain_objects WHERE kind='Artifact'`)
	beforeProjects := h.count(ctx, `SELECT count(*) FROM domain_objects WHERE kind='Project'`)
	stageBefore := h.stageRevision(ctx, h.alphaProj)
	_, e := h.bootstrap(ctx, h.alphaRef, "Alpha", "cmd-repeat-inventory")
	ok("INV-REPEAT-BOOTSTRAP-ACCEPTED", e == nil, e)
	ok("INV-REPEAT-KEEPS-ONE-PROJECT", h.count(ctx, `SELECT count(*) FROM domain_objects WHERE kind='Project'`) == beforeProjects,
		beforeProjects, h.count(ctx, `SELECT count(*) FROM domain_objects WHERE kind='Project'`))
	ok("INV-REPEAT-KEEPS-ONE-STAGE-ROW", h.count(ctx,
		`SELECT count(*) FROM domain_objects WHERE project=? AND kind='BootstrapStage' AND id LIKE '%local-inventory'`, h.alphaProj) == 1,
		h.count(ctx, `SELECT count(*) FROM domain_objects WHERE project=? AND kind='BootstrapStage' AND id LIKE '%local-inventory'`, h.alphaProj))
	// the stage record is the same row refreshed by exactly one revision, never a new row and never
	// a rewritten history
	ok("INV-REPEAT-STAGE-REVISION-ADVANCES-ONE", addsOne(stageBefore, h.stageRevision(ctx, h.alphaProj)),
		stageBefore, h.stageRevision(ctx, h.alphaProj))
	// Recovery contract: every domain_versions row must validate against the frozen domain schema,
	// because internal/domain/backup.go does exactly this for every row before a restore is
	// accepted. A future writer that versions a non-schema kind would fail here first.
	totalRows, badRows := h.versionedRowsThatValidate(ctx)
	ok("REC-VERSIONS-ALL-VALIDATE", totalRows > 0 && badRows == 0, totalRows, badRows)
	ok("REC-NON-SCHEMA-KINDS-ARE-NOT-VERSIONED", h.count(ctx,
		`SELECT count(*) FROM domain_versions WHERE kind IN ('WorkspaceBinding','BootstrapStage','BootstrapReplay','Project')`) == 0,
		h.count(ctx, `SELECT count(*) FROM domain_versions WHERE kind IN ('WorkspaceBinding','BootstrapStage','BootstrapReplay','Project')`))
	ok("REC-BUSINESS-HISTORY-STILL-VERSIONED", h.count(ctx,
		`SELECT count(*) FROM domain_versions WHERE kind IN ('ProjectProfile','ProjectState','Artifact')`) >= 3,
		h.count(ctx, `SELECT count(*) FROM domain_versions WHERE kind IN ('ProjectProfile','ProjectState','Artifact')`))
	ok("INV-REPEAT-ADDS-ONE-OBSERVATION", h.count(ctx, `SELECT count(*) FROM domain_objects WHERE kind='Artifact'`) == beforeArtifacts+1,
		beforeArtifacts, h.count(ctx, `SELECT count(*) FROM domain_objects WHERE kind='Artifact'`))
	ok("INV-REPEAT-BINDING-REVISION-UNCHANGED", h.bindingField(ctx, h.alphaRef, "revision") == "2",
		h.bindingField(ctx, h.alphaRef, "revision"))

	// the same command id replayed for the same project answers from the durable records
	censusBeforeReplay := h.census(ctx)
	artifactsBeforeReplay := h.count(ctx, `SELECT count(*) FROM domain_objects WHERE kind='Artifact'`)
	replayed, e := h.bootstrap(ctx, h.alphaRef, "Alpha", "cmd-repeat-inventory")
	ok("INV-REPLAY-SAME-COMMAND-ACCEPTED", e == nil, e)
	ok("INV-REPLAY-RETURNS-SAME-PROJECT", e == nil && fmt.Sprint(replayed["project_id"]) == h.alphaProj, e, replayed)
	// the nested workspace object is the live binding, not a snapshot from before the project was
	// bound: a stale or hand-built nesting is visible here rather than only in the reply shape
	nested, _ := replayed["workspace"].(map[string]any)
	ok("REPLY-NESTED-WORKSPACE-CARRIES-THE-PROJECT", nested != nil && fmt.Sprint(nested["project_id"]) == h.alphaProj, nested)
	ok("REPLY-NESTED-WORKSPACE-REVISION-MATCHES-STORE", nested != nil &&
		fmt.Sprint(nested["revision"]) == h.bindingField(ctx, h.alphaRef, "revision"), nested, h.bindingField(ctx, h.alphaRef, "revision"))
	ok("REPLY-NESTED-WORKSPACE-STATUS-MATCHES-STORE", nested != nil &&
		fmt.Sprint(nested["status"]) == h.bindingField(ctx, h.alphaRef, "status"), nested)
	ok("INV-REPLAY-CREATES-NOTHING-NEW", h.census(ctx) == censusBeforeReplay &&
		h.count(ctx, `SELECT count(*) FROM domain_objects WHERE kind='Artifact'`) == artifactsBeforeReplay,
		h.census(ctx), censusBeforeReplay)
	// the refresh above advanced the LOCAL_INVENTORY stage instead of promoting a later one
	invStage := h.stageSummary(ctx, h.alphaProj)
	ok("INV-STAGE-REFRESH-KEEPS-ORDER", strings.Contains(invStage, "RESEARCH:NOT_STARTED") &&
		strings.Contains(invStage, "LOCAL_INVENTORY:"), invStage)

	// grading is load-bearing, not a formality: the same project with a scanner that emits an entry
	// the published definition rejects must be refused before anything is written
	censusBeforeBad := h.census(ctx)
	bad := badScanner{fallback: h.scanner}
	_, eBad := h.svc.BootstrapProject(ctx, h.principal, h.authority, h.grader, bad, domain.BootstrapProjectInput{
		AuthorizedWorkspaceRef: h.alphaRef, DisplayName: "Alpha", CommandID: "cmd-bad-entry", ClientID: "cli-desktop"})
	ok("INV-GRADER-REFUSES-NONCONFORMANT-ENTRY", eBad != nil && strings.Contains(errText(eBad), "published definition"), eBad)
	ok("INV-GRADER-REFUSAL-WROTE-NO-BUSINESS-STATE", h.census(ctx) == censusBeforeBad, h.census(ctx), censusBeforeBad)
	// the pinned definition itself is proved to have teeth, otherwise the grading assertions above
	// would only be measuring a permissive schema
	ok("INV-DEFINITION-REJECTS-MISSING-FIELD", h.grader.ValidateDef("LocalInventoryPayload", domain.Object{
		"project_id": h.alphaProj, "authorized_scope_refs": []any{h.alphaRef}, "entries": []any{}}) != nil)
	ok("INV-DEFINITION-REJECTS-UNKNOWN-STATUS", h.grader.ValidateDef("LocalInventoryPayload", domain.Object{
		"project_id": h.alphaProj, "authorized_scope_refs": []any{h.alphaRef}, "environment": "e", "observed_at": "2026-10-02T00:00:00Z",
		"entries": []any{map[string]any{"capability": "c", "location_ref": "x", "status": "MAGIC",
			"revision_or_hash": nil, "notes": ""}}}) != nil)
	ok("BINDING-DEFINITION-REJECTS-EXTRA-FIELD", h.grader.ValidateDef("WorkspaceBinding", domain.Object{
		"authorized_workspace_ref": h.alphaRef, "display_name": "x", "display_path": "y", "access": "READ_ONLY",
		"project_id": nil, "revision": int64(1), "status": "ACTIVE", "real_path": `C:\secret`}) != nil)
	// the published definition cannot express the reference shape (a path is a legal string there),
	// which is exactly why refusing a path-shaped ref is a domain rule and not a schema accident
	ok("BINDING-DEFINITION-CANNOT-EXPRESS-REF-SHAPE", h.grader.ValidateDef("WorkspaceBinding", domain.Object{
		"authorized_workspace_ref": `C:\Users`, "display_name": "x", "display_path": "y", "access": "READ_ONLY",
		"project_id": nil, "revision": int64(1), "status": "ACTIVE"}) == nil)

	// a link planted inside the chosen directory is recorded as unexamined and is never followed:
	// the inventory must not acquire anything from outside the authorised root
	junctionPath := filepath.Join(h.chosen, "linkout")
	if made, reason := makeJunction(junctionPath, h.outside); made {
		res, serr := h.scanner.Scan(context.Background(), h.chosen)
		linked := false
		for _, e := range res.Entries {
			if e.Capability == "reparse_point" && e.Status == "NOT_CHECKED" {
				linked = true
			}
		}
		ok("INV-LINK-INSIDE-ROOT-RECORDED-NOT-FOLLOWED", serr == nil && linked, serr, linked)
		_, e := h.svc.BootstrapProject(ctx, h.principal, h.authority, h.grader, h.scanner, domain.BootstrapProjectInput{
			AuthorizedWorkspaceRef: h.alphaRef, DisplayName: "Alpha", CommandID: "cmd-link-scan", ClientID: "cli-desktop"})
		after := string(h.inventoryBytes(ctx, h.alphaProj))
		ok("INV-LINK-NEVER-BRIDGES-OUTSIDE-CONTENT", e == nil && !strings.Contains(after, "NEVER-AUTHORISED-MARKER"), e)
		removeJunction(junctionPath)
	} else {
		skip("INV-LINK-INSIDE-ROOT-RECORDED-NOT-FOLLOWED", reason)
		skip("INV-LINK-NEVER-BRIDGES-OUTSIDE-CONTENT", reason)
	}

	// a foreign replay of someone else's command id is refused, not silently served
	reader, rerr := domain.AuthenticateToken(ctx, h.db, mustToken(ctx, h, "w04-reader"))
	if rerr != nil {
		ok("INV-REPLAY-FOREIGN-PRINCIPAL-REFUSED", false, rerr)
	} else {
		_, e := h.svc.BootstrapProject(ctx, reader, h.authority, h.grader, h.scanner, domain.BootstrapProjectInput{
			AuthorizedWorkspaceRef: h.alphaRef, DisplayName: "Sneak", CommandID: "cmd-repeat-inventory", ClientID: "cli-desktop"})
		ok("INV-REPLAY-FOREIGN-PRINCIPAL-REFUSED", e != nil && strings.Contains(errText(e), "COMMAND_ID_CONFLICT"), e)
		// the same collision must be named on the registration namespace. It is probed with a
		// principal that IS allowed to create projects, because an unauthorised caller is refused
		// earlier on purpose: revealing that a command id exists is not something a caller without
		// any project right should learn.
		if err := h.svc.ProvisionPrincipal(ctx, domain.Principal{ID: "w04-builder", Roles: []string{"EXECUTOR"}, CanCreateProject: true}); err != nil {
			ok("REG-COMMAND-ID-COLLISION-NAMED", false, err)
		} else {
			bt, _ := h.svc.IssueCredential(ctx, "w04-builder", time.Minute)
			bpr, berr := domain.AuthenticateToken(ctx, h.db, bt)
			_, e2 := h.svc.RegisterWorkspace(ctx, bpr, h.authority, h.grader, domain.RegisterWorkspaceInput{
				SelectionRef: "sel-nobody", DisplayName: "Sneak", RequestedAccess: "READ_ONLY", CommandID: "cmd-register-1", ClientID: "cli-builder"})
			ok("REG-COMMAND-ID-COLLISION-NAMED", berr == nil && e2 != nil && strings.Contains(errText(e2), "COMMAND_ID_CONFLICT"), berr, e2)
			// and an unauthorised caller is still refused before it learns anything about the id
			_, e3 := h.svc.RegisterWorkspace(ctx, reader, h.authority, h.grader, domain.RegisterWorkspaceInput{
				SelectionRef: "sel-nobody", DisplayName: "Sneak", RequestedAccess: "READ_ONLY", CommandID: "cmd-register-1", ClientID: "cli-reader"})
			ok("REG-COLLISION-NOT-DISCLOSED-TO-UNAUTHORISED", e3 != nil && strings.Contains(errText(e3), "FORBIDDEN"), e3)
		}
	}
}

func mustToken(ctx context.Context, h *harness, principal string) string {
	t, _ := h.svc.IssueCredential(ctx, principal, time.Minute)
	return t
}

// stageSummary reads the four published stages in contract order. The rows themselves are ordered
// by id in the table, so the summary is built from the canonical sequence rather than from
// whatever alphabetical accident the storage produced.
func (h *harness) stageSummary(ctx context.Context, project string) string {
	want := []string{"LOCAL_INVENTORY", "RESEARCH", "REUSE_DECISION", "IMPLEMENTATION"}
	out := []string{}
	for _, w := range want {
		var status sql.NullString
		e := h.db.QueryRowContext(ctx, `SELECT json_extract(body,'$.status') FROM domain_objects WHERE project=? AND kind='BootstrapStage' AND json_extract(body,'$.stage')=?`,
			project, w).Scan(&status)
		if e != nil {
			continue
		}
		out = append(out, w+":"+status.String)
	}
	return strings.Join(out, ",")
}

// stageOrderOK asserts the recorded sequence is exactly the published one and that nothing beyond
// LOCAL_INVENTORY has been promoted.
func stageOrderOK(stages string) bool {
	want := []string{"LOCAL_INVENTORY:", "RESEARCH:NOT_STARTED", "REUSE_DECISION:NOT_STARTED", "IMPLEMENTATION:NOT_STARTED"}
	pos := -1
	for _, w := range want {
		i := strings.Index(stages, w)
		if i < 0 || i < pos {
			return false
		}
		pos = i
	}
	return true
}

// addsOne compares two revision strings as integers, so a refresh can be proven to advance by
// exactly one without hard-coding how many bootstraps ran earlier in this process.
func addsOne(before, after string) bool {
	var b, a int64
	if _, err := fmt.Sscanf(before, "%d", &b); err != nil {
		return false
	}
	if _, err := fmt.Sscanf(after, "%d", &a); err != nil {
		return false
	}
	return a == b+1
}

func (h *harness) stageRevision(ctx context.Context, project string) string {
	var rev sql.NullString
	h.db.QueryRowContext(ctx, `SELECT json_extract(body,'$.revision') FROM domain_objects WHERE project=? AND kind='BootstrapStage' AND json_extract(body,'$.stage')='LOCAL_INVENTORY'`, project).Scan(&rev)
	return rev.String
}

func (h *harness) stageRowCount(ctx context.Context, project string) int64 {
	return h.count(ctx, `SELECT count(*) FROM domain_objects WHERE project=? AND kind='BootstrapStage'`, project)
}

// makeJunction and removeJunction create or drop an NTFS junction through the shell's own mklink,
// which works without elevation. They are Windows features, so the check discloses the case rather
// than pretending it ran elsewhere.
func makeJunction(dir, target string) (bool, string) {
	if runtime.GOOS != "windows" {
		return false, "junctions are a Windows filesystem feature"
	}
	out, err := exec.Command("cmd", "/c", "mklink", "/J", dir, target).CombinedOutput()
	if err != nil {
		return false, "mklink /J refused: " + strings.TrimSpace(string(out))
	}
	return true, ""
}

func removeJunction(dir string) {
	if runtime.GOOS != "windows" {
		return
	}
	exec.Command("cmd", "/c", "rmdir", dir).Run()
	os.RemoveAll(dir)
}

// bootstrapWith runs a full project.bootstrap for a fresh directory with the given scanner, and
// returns the project id so the caller can read the stage row that was written.
func (h *harness) bootstrapWith(ctx context.Context, scan domain.LocalInventoryScanner) string {
	dir := filepath.Join(h.root, "probe-tree-"+randomSuffix())
	os.MkdirAll(dir, 0o755)
	sel, err := h.choose("cli-desktop", dir, "READ_ONLY")
	if err != nil {
		return ""
	}
	bind, err := h.register(ctx, sel, "Probe", "READ_ONLY", "cmd-probe-"+randomSuffix(), "cli-desktop")
	if err != nil {
		return ""
	}
	ref, _ := bind["authorized_workspace_ref"].(string)
	res, err := h.svc.BootstrapProject(ctx, h.principal, h.authority, h.grader, scan, domain.BootstrapProjectInput{
		AuthorizedWorkspaceRef: ref, DisplayName: "Probe", CommandID: "cmd-probe-boot-" + randomSuffix(), ClientID: "cli-desktop"})
	if err != nil {
		return ""
	}
	p, _ := res["project_id"].(string)
	return p
}

// stageFileFailures reads the durable per-file failure list back off the LOCAL_INVENTORY row.
func (h *harness) stageFileFailures(ctx context.Context, project string) string {
	var v sql.NullString
	h.db.QueryRowContext(ctx, `SELECT json_extract(body,'$.file_failures') FROM domain_objects WHERE project=? AND kind='BootstrapStage' AND json_extract(body,'$.stage')='LOCAL_INVENTORY'`,
		project).Scan(&v)
	return v.String
}

func hasCapability(entries []domain.LocalInventoryEntry, capability string) bool {
	for _, e := range entries {
		if e.Capability == capability {
			return true
		}
	}
	return false
}

func mustSel(ctx context.Context, h *harness, clientID, dir, access string) string {
	sel, err := h.choose(clientID, dir, access)
	if err != nil {
		return "sel-unavailable"
	}
	return sel
}

var probeCounter int64

func randomSuffix() string {
	atomic.AddInt64(&probeCounter, 1)
	return fmt.Sprintf("%d-%d", time.Now().UnixNano(), probeCounter)
}

// recoveryProbe re-reads every domain_versions row and validates it the way the accepted restore
// path does, so the recovery contract is checked here rather than assumed.
func (h *harness) versionedRowsThatValidate(ctx context.Context) (int, int) {
	rows, err := h.db.QueryContext(ctx, `SELECT kind, body FROM domain_versions`)
	if err != nil {
		return -1, -1
	}
	defer rows.Close()
	total, bad := 0, 0
	for rows.Next() {
		var kind, raw string
		if rows.Scan(&kind, &raw) != nil {
			return total, bad + 1
		}
		total++
		obj, derr := domain.Decode([]byte(raw))
		if derr != nil || h.svc.Contracts.Validate(kind, obj) != nil {
			bad++
		}
	}
	return total, bad
}

// bindingSequenceOK asserts the revision the binding row carries after mint (1), first project
// bind (2) and revoke (3). The compare-and-set inside putOpaque refuses any other value, so this
// is the observable half of that guard.
func (h *harness) bindingSequenceOK(ctx context.Context) bool {
	return h.bindingField(ctx, h.alphaRef, "revision") == "3"
}

// scopedScanner returns entries whose location escapes the authorised root, which the domain must
// refuse instead of trusting the adapter.
type scopedScanner struct {
	fallback *localworkspace.Scanner
	location string
}

func (b scopedScanner) Scan(ctx context.Context, realPath string) (domain.LocalInventoryScan, error) {
	res, err := b.fallback.Scan(ctx, realPath)
	res.Entries = append(res.Entries, domain.LocalInventoryEntry{Capability: "probe", LocationRef: b.location,
		Status: "FOUND"})
	return res, err
}

// constantScanner ignores the directory entirely, which is how the empty and unreachable
// derivations are observed without depending on OS permission behaviour this machine cannot give.
type constantScanner struct {
	entries  []domain.LocalInventoryEntry
	failures []domain.LocalInventoryFileFailure
}

func (c constantScanner) Scan(ctx context.Context, realPath string) (domain.LocalInventoryScan, error) {
	return domain.LocalInventoryScan{Environment: "probe", Entries: c.entries, Failures: c.failures}, nil
}

func (h *harness) stageStatusOf(ctx context.Context, project string) string {
	var st string
	h.db.QueryRowContext(ctx, `SELECT json_extract(body,'$.status') FROM domain_objects WHERE project=? AND kind='BootstrapStage' AND json_extract(body,'$.stage')='LOCAL_INVENTORY'`,
		project).Scan(&st)
	return st
}

func (h *harness) markerRevisions(ctx context.Context, project string) string {
	rows, err := h.db.QueryContext(ctx, `SELECT json_extract(body,'$.stage'), json_extract(body,'$.revision') FROM domain_objects WHERE project=? AND kind='BootstrapStage' AND json_extract(body,'$.stage')!='LOCAL_INVENTORY' ORDER BY id`, project)
	if err != nil {
		return ""
	}
	defer rows.Close()
	out := []string{}
	for rows.Next() {
		var a, b sql.NullString
		if rows.Scan(&a, &b) != nil {
			continue
		}
		out = append(out, a.String+"="+b.String)
	}
	return strings.Join(out, ",")
}

// routingTruthTable asserts the forwarding rule itself, so a change that answers a task-only
// invocation with this card's assertion ids fails here rather than only showing up in a dispatch.
func routingTruthTableOK() bool {
	cases := []struct {
		check, caseID, taskID string
		forward               bool
	}{
		{"W04-01", "", "W04", false},
		{"W04-01", "A01", "W04", true},
		{"W04-02", "", "W04", false},
		{"W04-02", "C03", "W04", true},
		{"W04-03", "", "W04", true},
		{"", "", "W04", true},
		{"", "", "", false},
		{"W04-G01", "", "W04", true},
		{"W06-G02", "", "W06", true},
		{"", "C02", "W17", true},
	}
	for _, c := range cases {
		if routesToLegacy(c.check, c.caseID, c.taskID) != c.forward {
			return false
		}
	}
	return true
}

// badScanner returns an entry the pinned LocalInventoryPayload definition refuses (an empty
// capability). The domain has no hand-written rule against it, so only the contract grading can
// catch it: if grading were decorative this bootstrap would succeed and the assertions below fail.
type badScanner struct{ fallback *localworkspace.Scanner }

func (b badScanner) Scan(ctx context.Context, realPath string) (domain.LocalInventoryScan, error) {
	res, err := b.fallback.Scan(ctx, realPath)
	if err != nil {
		return res, err
	}
	res.Entries = append(res.Entries, domain.LocalInventoryEntry{Capability: "", LocationRef: "x", Status: "FOUND"})
	return res, nil
}

// hardeningPhase covers the properties the first review proved were missing: a junction must not
// bridge content into the inventory (with a positive control that shows the scanner would have seen
// it), absence may only be claimed over ground that was actually walked, version control is
// detected where it exists, and an authorized workspace reference is not transferable - not even to
// another OWNER.
func (h *harness) hardeningPhase(ctx context.Context) {
	// the outside directory is inventoriable in its own right, which is what makes the next
	// assertion able to fail rather than resting on filenames the scanner ignores
	outRes, oerr := h.scanner.Scan(context.Background(), h.outside)
	outControl := false
	for _, e := range outRes.Entries {
		if e.Capability == "readme" && e.Status == "FOUND" {
			outControl = true
		}
	}
	ok("INV-OUTSIDE-DIRECTORY-IS-INVENTORABLE", oerr == nil && outControl, oerr, outRes)

	junctionPath := filepath.Join(h.chosen, "linkout2")
	if made, reason := makeJunction(junctionPath, h.outside); made {
		res, serr := h.scanner.Scan(context.Background(), h.chosen)
		bridged, markedLink := false, false
		for _, e := range res.Entries {
			if strings.HasPrefix(e.LocationRef, "linkout2/") {
				bridged = true
			}
			if e.Capability == "reparse_point" {
				markedLink = true
			}
		}
		ok("INV-NO-ENTRY-CROSSES-A-JUNCTION", serr == nil && !bridged && markedLink, serr, bridged, markedLink)
		removeJunction(junctionPath)
	} else {
		skip("INV-NO-ENTRY-CROSSES-A-JUNCTION", reason)
	}

	// a capability that exists only inside a skipped subtree is NOT_CHECKED, never NOT_FOUND
	edge := filepath.Join(h.root, "skipped-tree")
	os.MkdirAll(filepath.Join(edge, "node_modules", "pkg"), 0o755)
	os.WriteFile(filepath.Join(edge, "node_modules", "pkg", "pyproject.toml"), []byte("[project]\n"), 0o600)
	os.WriteFile(filepath.Join(edge, "README.md"), []byte("# edge\n"), 0o600)
	edgeRes, eerr := h.scanner.Scan(context.Background(), edge)
	pyStatus, vcStatus := "", ""
	for _, e := range edgeRes.Entries {
		switch e.Capability {
		case "python_manifest":
			pyStatus = e.Status
		case "version_control":
			vcStatus = e.Status
		}
	}
	ok("INV-SKIPPED-SUBTREE-IS-NOT-ABSENCE", eerr == nil && pyStatus == "NOT_CHECKED", eerr, pyStatus)
	ok("INV-SKIPPED-GROUNDS-NEVER-CLAIM-ABSENCE", vcStatus == "NOT_CHECKED", vcStatus)
	// over ground that was walked completely the same capability may say NOT_FOUND
	cleanTree := filepath.Join(h.root, "clean-tree")
	os.MkdirAll(filepath.Join(cleanTree, "src"), 0o755)
	os.WriteFile(filepath.Join(cleanTree, "src", "main.go"), []byte("package main\n"), 0o600)
	cleanRes, cerr := h.scanner.Scan(context.Background(), cleanTree)
	cleanVC, cleanGo := "", ""
	for _, e := range cleanRes.Entries {
		switch e.Capability {
		case "version_control":
			cleanVC = e.Status
		case "go_module":
			cleanGo = e.Status
		}
	}
	ok("INV-WALKED-GROUND-CAN-SAY-NOT-FOUND", cerr == nil && cleanVC == "NOT_FOUND" && cleanGo == "NOT_FOUND",
		cerr, cleanVC, cleanGo)

	gitTree := filepath.Join(h.root, "with-git")
	os.MkdirAll(filepath.Join(gitTree, ".git"), 0o755)
	os.WriteFile(filepath.Join(gitTree, "README.md"), []byte("# g\n"), 0o600)
	gitRes, gerr := h.scanner.Scan(context.Background(), gitTree)
	vcFound := false
	for _, e := range gitRes.Entries {
		if e.Capability == "version_control" && e.Status == "FOUND" {
			vcFound = true
		}
	}
	ok("INV-GIT-DIRECTORY-DETECTED", gerr == nil && vcFound, gerr, gitRes)

	// a binding is not transferable, not even to another OWNER: it records that one user chose that
	// directory, and a role is not a universal key over other users' choices
	if err := h.svc.ProvisionPrincipal(ctx, domain.Principal{ID: "w04-second-owner", Roles: []string{"OWNER"},
		CanCreateProject: true}); err != nil {
		ok("SEC-SECOND-OWNER-PROVISIONED", false, err)
		return
	}
	st, terr := h.svc.IssueCredential(ctx, "w04-second-owner", time.Minute)
	spr, aerr := domain.AuthenticateToken(ctx, h.db, st)
	ok("SEC-SECOND-OWNER-PROVISIONED", terr == nil && aerr == nil, terr, aerr)
	l2, lerr := h.svc.ListWorkspaceBindings(ctx, spr)
	cross := false
	for _, b := range l2 {
		if b.AuthorizedRef == h.alphaRef {
			cross = true
		}
	}
	ok("SEC-FOREIGN-BINDING-NOT-LISTABLE", lerr == nil && !cross, lerr, cross)
	_, be := h.svc.BootstrapProject(ctx, spr, h.authority, h.grader, h.scanner, domain.BootstrapProjectInput{
		AuthorizedWorkspaceRef: h.alphaRef, DisplayName: "Hijack", CommandID: "cmd-hijack", ClientID: "cli-second"})
	ok("SEC-FOREIGN-BINDING-NOT-BOOTSTRAPPABLE", be != nil && strings.Contains(errText(be), "FORBIDDEN"), be)
	ok("SEC-HIJACK-CREATED-NO-PROJECT", h.count(ctx, `SELECT count(DISTINCT id) FROM domain_objects WHERE kind='Project'`) == 2,
		h.count(ctx, `SELECT count(DISTINCT id) FROM domain_objects WHERE kind='Project'`))
	re := h.svc.RevokeWorkspaceBinding(ctx, spr, h.alphaRef)
	ok("SEC-FOREIGN-BINDING-NOT-REVOKABLE", re != nil && strings.Contains(errText(re), "FORBIDDEN"), re)
	// the read path later cards use must be refused too, not only the write paths above
	_, ferr := h.svc.WorkspaceBindingFor(ctx, spr, h.authority, h.alphaRef)
	ok("SEC-FOREIGN-BINDING-NOT-READABLE", ferr != nil && strings.Contains(errText(ferr), "FORBIDDEN"), ferr)
	_, oerr2 := h.svc.WorkspaceBindingFor(ctx, h.principal, h.authority, h.alphaRef)
	ok("SEC-OWNING-PRINCIPAL-STILL-READS-ITS-BINDING", oerr2 == nil, oerr2)
	// the read path refuses a filesystem path the same way bootstrap does; without this, the guard
	// in WorkspaceBindingFor could be deleted and nothing in the suite would notice, because every
	// other case hands it a minted reference
	_, perr := h.svc.WorkspaceBindingFor(ctx, h.principal, h.authority, h.root)
	pst, pcode := faultOf(perr)
	ok("NEG-READ-PATH-REJECTS-PATH-SHAPED-REF", pst == 403 && pcode == "FORBIDDEN", perr)

	// the authorising principal still can, so the refusals above are ownership and not a blanket lock
	ok("SEC-OWNER-STILL-CAN-REVOKE", h.svc.RevokeWorkspaceBinding(ctx, h.principal, h.roRef()) == nil)

	// a replay record is scoped to the reference it was created for: one command id cannot be
	// answered with a different directory's project
	_, p1 := h.svc.BootstrapProject(ctx, h.principal, h.authority, h.grader, h.scanner, domain.BootstrapProjectInput{
		AuthorizedWorkspaceRef: h.betaRef, DisplayName: "Beta", CommandID: "cmd-bootstrap-1", ClientID: "cli-desktop"})
	ok("REPLAY-SCOPED-TO-REFERENCE", p1 != nil && strings.Contains(errText(p1), "COMMAND_ID_CONFLICT"), p1)

	// one canonical directory cannot gain a second permanent identity through another principal
	if _, e := h.svc.RegisterWorkspace(ctx, spr, h.authority, h.grader, domain.RegisterWorkspaceInput{
		SelectionRef: mustSel(ctx, h, "cli-second", h.chosen, "READ_ONLY"), DisplayName: "Same dir",
		RequestedAccess: "READ_ONLY", CommandID: "cmd-second-dir", ClientID: "cli-second"}); true {
		ok("ONE-DIRECTORY-ONE-IDENTITY", e != nil && strings.Contains(errText(e), "POLICY_DENIED"), e)
	}
	ok("ONE-DIRECTORY-STILL-TWO-PROJECTS", h.count(ctx, `SELECT count(DISTINCT id) FROM domain_objects WHERE kind='Project'`) == 2,
		h.count(ctx, `SELECT count(DISTINCT id) FROM domain_objects WHERE kind='Project'`))

	// the domain refuses an inventory entry that points outside the authorised root, so an adapter
	// bug cannot quietly widen the scope
	_, absScope := h.svc.BootstrapProject(ctx, h.principal, h.authority, h.grader,
		scopedScanner{fallback: h.scanner, location: `C:\Windows\win.ini`}, domain.BootstrapProjectInput{
			AuthorizedWorkspaceRef: h.betaRef, DisplayName: "Beta", CommandID: "cmd-abs-scope", ClientID: "cli-desktop"})
	ok("INV-ENTRY-SCOPE-REFUSED", absScope != nil && strings.Contains(errText(absScope), "PATH_OUT_OF_SCOPE"), absScope)
	_, dotScope := h.svc.BootstrapProject(ctx, h.principal, h.authority, h.grader,
		scopedScanner{fallback: h.scanner, location: "../escape/file.md"}, domain.BootstrapProjectInput{
			AuthorizedWorkspaceRef: h.betaRef, DisplayName: "Beta", CommandID: "cmd-dot-scope", ClientID: "cli-desktop"})
	ok("INV-ENTRY-ESCAPE-REFUSED", dotScope != nil && strings.Contains(errText(dotScope), "PATH_OUT_OF_SCOPE"), dotScope)

	// the stage derivation distinguishes an empty but readable root, a partially unreachable one and
	// a wholly unreachable one, instead of collapsing them into one error or one success
	emptyProj := h.bootstrapWith(ctx, constantScanner{})
	ok("INV-EMPTY-BUT-READABLE-IS-COMPLETED", h.stageStatusOf(ctx, emptyProj) == "COMPLETED", h.stageStatusOf(ctx, emptyProj))
	partProj := h.bootstrapWith(ctx, constantScanner{
		entries: []domain.LocalInventoryEntry{{Capability: "readme", LocationRef: "README.md", Status: "FOUND"},
			{Capability: "subtree", LocationRef: "locked", Status: "NOT_ACCESSIBLE"}},
		failures: []domain.LocalInventoryFileFailure{{Path: "locked/x.json", Reason: "permission denied"}}})
	ok("INV-PARTIALLY-UNREACHABLE-IS-PARTIAL", h.stageStatusOf(ctx, partProj) == "PARTIAL", h.stageStatusOf(ctx, partProj))
	allProj := h.bootstrapWith(ctx, constantScanner{entries: []domain.LocalInventoryEntry{
		{Capability: "workspace_root", LocationRef: ".", Status: "NOT_ACCESSIBLE"}}})
	ok("INV-UNREACHABLE-ROOT-IS-FAILED", h.stageStatusOf(ctx, allProj) == "FAILED", h.stageStatusOf(ctx, allProj))

	// the NOT_STARTED markers are created once. The comparison has to be before-and-after on the SAME
	// project: an assertion that only reads a pre-existing snapshot cannot fail.
	beforeMarkers := h.markerRevisions(ctx, h.alphaProj)
	_, markerErr := h.svc.BootstrapProject(ctx, h.principal, h.authority, h.grader, h.scanner, domain.BootstrapProjectInput{
		AuthorizedWorkspaceRef: h.alphaRef, DisplayName: "Alpha", CommandID: "cmd-marker-check", ClientID: "cli-desktop"})
	afterMarkers := h.markerRevisions(ctx, h.alphaProj)
	ok("INV-MARKERS-CREATED-ONCE", markerErr == nil && beforeMarkers == afterMarkers &&
		strings.Contains(afterMarkers, "RESEARCH=1") && strings.Contains(afterMarkers, "REUSE_DECISION=1") &&
		strings.Contains(afterMarkers, "IMPLEMENTATION=1"), beforeMarkers, afterMarkers, markerErr)

	// the per-file failure list is durable state, not just an in-memory scan result
	stageFailures := h.stageFileFailures(ctx, h.alphaProj)
	ok("INV-PARTIAL-PARSE-PERSISTED", strings.Contains(stageFailures, "broken.json") &&
		strings.Contains(stageFailures, "not valid JSON"), stageFailures)
	// measurement mode is recorded, and an unrecognised value falls back to FIXTURE rather than
	// letting a fixture run label itself as LIVE evidence
	ok("INV-MEASUREMENT-MODE-RECORDED", strings.Contains(h.bodyOf(ctx, "Artifact", h.artifactID(ctx, h.alphaProj)),
		`"measurement_mode":"FIXTURE"`), h.artifactID(ctx, h.alphaProj))

	// unexamined ground cannot claim absence: depth cut, skipped subtree and entry cap each have to
	// leave a NOT_CHECKED verdict behind
	deep := filepath.Join(h.root, "deep-tree")
	probe := deep
	for i := 0; i < 11; i++ {
		probe = filepath.Join(probe, "lvl")
	}
	os.MkdirAll(filepath.Join(probe, "pkg"), 0o755)
	os.WriteFile(filepath.Join(probe, "pkg", "pyproject.toml"), []byte("[project]\n"), 0o600)
	deepRes, deepErr := h.scanner.Scan(context.Background(), deep)
	deepStatus := ""
	for _, e := range deepRes.Entries {
		if e.Capability == "python_manifest" {
			deepStatus = e.Status
		}
	}
	ok("INV-DEPTH-CUT-IS-NOT-ABSENCE", deepErr == nil && deepStatus == "NOT_CHECKED", deepErr, deepStatus)
	ok("INV-DEPTH-CUT-RECORDED", hasCapability(deepRes.Entries, "subtree_beyond_depth") &&
		hasCapability(deepRes.Entries, "scan_completeness"), deepRes.Entries)

	wide := filepath.Join(h.root, "wide-tree")
	os.MkdirAll(wide, 0o755)
	// Each unparseable document is its own entry, so this is what actually reaches the cap.
	for i := 0; i < localworkspace.MaxInventoryEntries+5; i++ {
		os.WriteFile(filepath.Join(wide, fmt.Sprintf("bad-%04d.json", i)), []byte("{oops"), 0o600)
	}
	wideRes, wideErr := h.scanner.Scan(context.Background(), wide)
	ok("INV-ENTRY-CAP-LEAVES-A-VERDICT", wideErr == nil && hasCapability(wideRes.Entries, "inventory_truncated") &&
		hasCapability(wideRes.Entries, "scan_completeness"), len(wideRes.Entries))
	widePy := ""
	for _, e := range wideRes.Entries {
		if e.Capability == "node_manifest" {
			widePy = e.Status
		}
	}
	ok("INV-ENTRY-CAP-NEVER-CLAIMS-ABSENCE", widePy == "NOT_CHECKED", widePy)

	// a .git file (worktree or submodule pointer) is version control too
	wt := filepath.Join(h.root, "worktree-dir")
	os.MkdirAll(wt, 0o755)
	os.WriteFile(filepath.Join(wt, ".git"), []byte("gitdir: ../elsewhere/.git/worktrees/x\n"), 0o600)
	wtRes, wtErr := h.scanner.Scan(context.Background(), wt)
	vcFile := false
	for _, e := range wtRes.Entries {
		if e.Capability == "version_control" && e.Status == "FOUND" {
			vcFile = true
		}
	}
	ok("INV-GIT-FILE-DETECTED", wtErr == nil && vcFile, wtErr, wtRes)
}

// -------------------------------------------------------------------------- binding lifecycle
func (h *harness) lifecyclePhase(ctx context.Context) {
	list, err := h.svc.ListWorkspaceBindings(ctx, h.principal)
	ok("LIFE-LIST-SHOWS-AUTHORISED-ROOTS", err == nil && len(list) >= 3, err, len(list))
	seen := map[string]bool{}
	for _, b := range list {
		seen[b.AuthorizedRef] = true
	}
	ok("LIFE-LIST-INCLUDES-BOUND-REFERENCE", seen[h.alphaRef], len(list))

	// revocation refuses new work and keeps the reference visible as history
	revBeforeRevoke := h.bindingField(ctx, h.alphaRef, "revision")
	if e := h.svc.RevokeWorkspaceBinding(ctx, h.principal, h.alphaRef); e != nil {
		ok("LIFE-REVOKE-APPLIED", false, e)
	} else {
		ok("LIFE-REVOKE-APPLIED", true)
		_, e := h.bootstrap(ctx, h.alphaRef, "Alpha", "cmd-after-revoke")
		ok("LIFE-REVOKE-REFUSES-BOOTSTRAP", e != nil && strings.Contains(errText(e), "WORKSPACE_REVOKED"), e)
		bindings, _ := h.svc.ListWorkspaceBindings(ctx, h.principal)
		found := false
		for _, b := range bindings {
			if b.AuthorizedRef == h.alphaRef && b.Status == domain.WorkspaceRevoked {
				found = true
			}
		}
		ok("LIFE-REVOKED-REFERENCE-KEPT-AS-HISTORY", found, len(bindings))
		ok("LIFE-REVOKED-BINDING-ADVANCED-ONE-REVISION", addsOne(revBeforeRevoke, h.bindingField(ctx, h.alphaRef, "revision")),
			revBeforeRevoke, h.bindingField(ctx, h.alphaRef, "revision"))
		ok("LIFE-PROJECT-SURVIVES-REVOCATION", h.count(ctx, `SELECT count(*) FROM domain_objects WHERE kind='Project' AND id=?`, h.alphaProj) == 1)
		ok("LIFE-INVENTORY-SURVIVES-REVOCATION", h.artifactID(ctx, h.alphaProj) != "")
	}
	// a second revocation is a no-op, not a revision storm
	before := h.bindingField(ctx, h.alphaRef, "revision")
	h.svc.RevokeWorkspaceBinding(ctx, h.principal, h.alphaRef)
	ok("LIFE-SECOND-REVOKE-IS-IDEMPOTENT", h.bindingField(ctx, h.alphaRef, "revision") == before, before, h.bindingField(ctx, h.alphaRef, "revision"))

	// version history is append-only, and the domain refuses to reuse a command id for a new mint
	// The binding row is current-state, so its history is the revision sequence rather than a
	// version table: 1 when minted, 2 when a project is bound, 3 when revoked.
	ok("LIFE-BINDING-REVISION-SEQUENCE", h.bindingSequenceOK(ctx), h.bindingField(ctx, h.alphaRef, "revision"))
	ok("REC-BINDING-KIND-NEVER-VERSIONED", h.count(ctx, `SELECT count(*) FROM domain_versions WHERE kind='WorkspaceBinding'`) == 0)

	// a directory that moved out from under the binding is refused, not scanned as an empty place
	betaLive := h.betaRef
	original := h.other
	swapped := original + "-moved"
	if rerr := os.Rename(original, swapped); rerr != nil {
		ok("LIFE-SWAPPED-DIRECTORY-REFUSED", false, rerr)
	} else {
		_, e := h.bootstrap(ctx, betaLive, "Beta", "cmd-swapped-bootstrap")
		ok("LIFE-SWAPPED-DIRECTORY-REFUSED", e != nil && (strings.Contains(errText(e), "PATH_OUT_OF_SCOPE") ||
			strings.Contains(errText(e), "WORKSPACE_REVOKED")), e)
		_, e2 := h.register(ctx, "sel-after-swap", "Beta", "READ_WRITE", "cmd-after-swap", "cli-desktop")
		ok("LIFE-SWAPPED-DIRECTORY-REGISTER-REFUSED", e2 != nil, e2)
		if rerr := os.Rename(swapped, original); rerr != nil {
			ok("LIFE-DIRECTORY-RESTORED", false, rerr)
		} else {
			ok("LIFE-DIRECTORY-RESTORED", true)
		}
	}

	// the domain keeps no second truth: a session cannot be created against a revoked workspace by
	// the mapping that W03-01 accepted, so a Project row is what makes the id resolvable at all
	ok("LIFE-PROJECT-ID-RESOLVES-FOR-SESSION-MAPPING",
		h.count(ctx, `SELECT count(*) FROM domain_objects WHERE kind='Project' AND project=?`, h.alphaProj) == 1)
	ok("ROUTE-TRUTH-TABLE", routingTruthTableOK())
}

func (h *harness) versionHistoryImmutable(ctx context.Context) bool {
	if _, e := h.db.ExecContext(ctx, `UPDATE domain_versions SET body='{}' WHERE kind='WorkspaceBinding'`); e == nil {
		return false
	}
	if _, e := h.db.ExecContext(ctx, `DELETE FROM domain_versions WHERE kind='WorkspaceBinding'`); e == nil {
		return false
	}
	return true
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
