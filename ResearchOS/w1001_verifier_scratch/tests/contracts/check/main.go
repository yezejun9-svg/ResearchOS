// Command check is the W03-02 qualification for the typed local protocol and its
// idempotent event boundary. It replays every published v2 fixture (76 positive,
// 30 negative) through the pinned schema document and the Go runtime decoder, then runs
// real-DB scenarios: writer/session/revision/epoch gating, command_id content-hash replay
// with zero second effect, same-key/different-request conflict, the takeover matrix,
// cancel settlement taken from actual run state, gap detection plus snapshot recovery,
// and the sensitive-field boundary. Prints one JSON assertion report for the dispatcher.
package main

import (
	"context"
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
	"time"

	"researchos.local/research-os/internal/api"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/store"
)

var ids []string
var failures []map[string]string

func ok(label string, cond bool, detail ...any) {
	if cond {
		ids = append(ids, label)
	} else {
		msg := fmt.Sprint(detail...)
		if len(msg) > 300 {
			msg = msg[:300]
		}
		failures = append(failures, map[string]string{"id": label, "detail": msg})
	}
}

type fixture struct {
	Name          string          `json:"name"`
	SchemaDef     string          `json:"schema_definition"`
	ExpectedValid bool            `json:"expected_valid"`
	Value         json.RawMessage `json:"value"`
}

var schemaDoc *domain.SchemaDoc

// validateFixture grades each fixture first against the published schema document itself
// (write direction for command payloads, read direction for responses, events and
// snapshots), then through the runtime decoder, so the shipped contract and the running
// service cannot drift apart in either direction.
func validateFixture(fx fixture) error {
	var v any
	if err := json.Unmarshal(fx.Value, &v); err != nil {
		return err
	}
	switch fx.SchemaDef {
	case "CommandEnvelope":
		if err := schemaDoc.ValidateDefInput(fx.SchemaDef, v); err != nil {
			return err
		}
		if _, err := domain.DecodeEnvelope(fx.Value); err != nil {
			return err
		}
	case "CommandResponse":
		if err := schemaDoc.ValidateDef(fx.SchemaDef, v); err != nil {
			return err
		}
		if _, err := domain.DecodeResponse(fx.Value); err != nil {
			return err
		}
	case "SessionEvent":
		if err := schemaDoc.ValidateDef(fx.SchemaDef, v); err != nil {
			return err
		}
		ev, err := domain.DecodeEvent(fx.Value)
		if err != nil {
			return err
		}
		if err := domain.ValidateEventPayload(schemaDoc, ev); err != nil {
			return err
		}
	case "SessionSnapshot":
		if err := schemaDoc.ValidateDef(fx.SchemaDef, v); err != nil {
			return err
		}
	default:
		if strings.HasPrefix(fx.SchemaDef, "Native") {
			return domain.ValidateNativeTransient(schemaDoc, fx.SchemaDef, fx.Value,
				strings.HasSuffix(fx.SchemaDef, "Request"))
		}
		if err := schemaDoc.ValidateDef(fx.SchemaDef, v); err != nil {
			return err
		}
	}
	return nil
}

func main() {
	ctx := context.Background()
	defer func() {
		if r := recover(); r != nil {
			buf := make([]byte, 8192)
			n := runtime.Stack(buf, false)
			failures = append(failures, map[string]string{"id": "PANIC", "detail": fmt.Sprint(r) + " || " + string(buf[:n])})
		}
		if len(ids) == 0 {
			failures = append(failures, map[string]string{"id": "NO-ASSERTIONS-RECORDED", "detail": "a run that recorded nothing is never a pass"})
		}
		status := "PASS"
		if len(failures) > 0 {
			status = "FAIL"
		}
		out, _ := json.Marshal(map[string]any{"status": status, "assertions": len(ids), "assertion_ids": ids,
			"failures": failures, "scope": "CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE"})
		fmt.Println(string(out))
		if len(failures) > 0 {
			os.Exit(1)
		}
	}()
	root, _ := os.Getwd()
	for i := 0; i < 4; i++ {
		if _, err := os.Stat(filepath.Join(root, "migrations", "sqlite")); err == nil {
			break
		}
		root = filepath.Dir(root)
	}
	fxdir := filepath.Join("tests", "contracts", "fixtures")
	sraw, err := os.ReadFile(filepath.Join(fxdir, "client.protocol.schema.json"))
	if err != nil {
		ok("SCHEMA-READABLE", false, err)
		return
	}
	if sh := sha256.Sum256(sraw); hex.EncodeToString(sh[:]) != schemaSHA {
		ok("SCHEMA-HASH", false, hex.EncodeToString(sh[:]))
		return
	}
	draw, err := os.ReadFile(filepath.Join(fxdir, "domain.schema.json"))
	if err != nil {
		ok("EXTERNAL-SCHEMA-READABLE", false, err)
		return
	}
	if sh := sha256.Sum256(draw); hex.EncodeToString(sh[:]) != domainSchemaSHA {
		ok("EXTERNAL-SCHEMA-HASH", false, hex.EncodeToString(sh[:]))
		return
	}
	schemaDoc, err = domain.LoadSchemaWithExternals(sraw, map[string][]byte{"domain.schema.json": draw})
	if err != nil {
		ok("SCHEMA-LOAD", false, err)
		return
	}
	// The published contract is only meaningful if every method and event kind the
	// service registers is covered by a contract entry, and vice versa.
	ok("SCHEMA-METHODS-23", len(schemaDoc.Methods) == 23, len(schemaDoc.Methods))
	ok("SCHEMA-EVENTS-14", len(schemaDoc.Events) == 14, len(schemaDoc.Events))

	raw, err := os.ReadFile(filepath.Join(fxdir, "client_protocol_v2_fixtures.json"))
	if err != nil {
		ok("FIXTURE-SET-READABLE", false, err)
		return
	}
	sum := sha256.Sum256(raw)
	ok("FIXTURE-SET-HASH", hex.EncodeToString(sum[:]) == fixtureSetSHA, hex.EncodeToString(sum[:]))
	var doc struct {
		Fixtures []fixture `json:"fixtures"`
	}
	if err := json.Unmarshal(raw, &doc); err != nil {
		ok("FIXTURE-SET-DECODE", false, err)
		return
	}
	vid, bad, inv := 0, 0, 0
	byDef := map[string]int{}
	for _, fx := range doc.Fixtures {
		byDef[fx.SchemaDef]++
		err := validateFixture(fx)
		if fx.ExpectedValid && err != nil {
			bad++
			failures = append(failures, map[string]string{"id": "FIXTURE-" + fx.Name, "detail": "expected valid: " + err.Error()})
		}
		if !fx.ExpectedValid && err == nil {
			bad++
			failures = append(failures, map[string]string{"id": "FIXTURE-" + fx.Name, "detail": "expected invalid but accepted"})
		}
		if fx.ExpectedValid {
			vid++
		} else {
			inv++
		}
	}
	ok("FIXTURE-CORPUS-SHAPE", len(doc.Fixtures) == 106 && vid == 76 && inv == 30, len(doc.Fixtures), vid, inv)
	ok("FIXTURE-DEF-COVERAGE", byDef["CommandEnvelope"] == 47 && byDef["CommandResponse"] == 33 &&
		byDef["SessionEvent"] == 21 && byDef["SessionSnapshot"] == 1 && byDef["NativeUserBootstrapResult"]+
		byDef["NativeCredentialImportRequest"]+byDef["NativeCredentialImportResult"]+
		byDef["NativeWorkspaceChooseRequest"]+byDef["NativeWorkspaceChooseResult"] == 4, byDef)
	ok("FIXTURE-REPLAY-ALL", bad == 0, bad)

	// ---------------- runtime service on a real migrated database ----------------
	tmp, err := os.MkdirTemp(filepath.Join(root, ".local"), "w0302-")
	if err != nil {
		ok("TMPDIR", false, err)
		return
	}
	defer os.RemoveAll(tmp)
	db, err := store.Open(filepath.Join(tmp, "p.sqlite"))
	if err != nil {
		ok("OPEN-DB", false, err)
		return
	}
	defer db.Close()
	files, _ := filepath.Glob(filepath.Join(root, "migrations/sqlite/0*.sql"))
	ok("BASELINE-MIGRATIONS-20", len(files) == 20, len(files))
	for i, f := range files {
		b, _ := os.ReadFile(f)
		tx, err := db.BeginTx(ctx, nil)
		if err != nil {
			ok("BASELINE-BEGIN", false, err)
			return
		}
		if _, err := tx.ExecContext(ctx, string(b)); err != nil {
			tx.Rollback()
			ok("BASELINE-STAGE", false, f, err)
			return
		}
		tx.ExecContext(ctx, `INSERT OR IGNORE INTO schema_migrations(version) VALUES (?)`, i+1)
		tx.Commit()
	}
	nb, _ := os.ReadFile(filepath.Join(root, "migrations/sqlite/next_v24_sessions.sql"))
	tx, _ := db.BeginTx(ctx, nil)
	if _, err := tx.ExecContext(ctx, string(nb)); err != nil {
		tx.Rollback()
		ok("V24-MIGRATION", false, err)
		return
	}
	tx.ExecContext(ctx, `INSERT INTO schema_migrations(version) VALUES (9021)`)
	tx.Commit()

	db.ExecContext(ctx, `INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('p1','Project','p1',1,'{}',0)`)
	now := time.Now().UTC()
	seedRun := func(id, body string, rev int64) {
		db.ExecContext(ctx, `INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('p1','Run',?,?,?,0)`, id, rev, body)
	}
	seedRun("run-live", `{"status":"RUNNING","children_stopped":false,"queue_empty":false}`, 4)
	seedRun("run-cancelling", `{"status":"CANCEL_REQUESTED","children_stopped":false,"queue_empty":false,"cancel_requested_at":"`+now.Add(-time.Minute).Format(time.RFC3339Nano)+`"}`, 5)
	seedRun("run-settled", `{"status":"CANCEL_REQUESTED","children_stopped":true,"queue_empty":true,"cancel_requested_at":"`+now.Add(-3*time.Minute).Format(time.RFC3339Nano)+`","cancel_confirmed_at":"`+now.Add(-time.Minute).Format(time.RFC3339Nano)+`"}`, 7)
	seedRun("run-failed", `{"status":"FAILED","children_stopped":true,"queue_empty":true}`, 3)
	// a foreign-project run must never be reachable through p1's session
	db.ExecContext(ctx, `INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('p2','Run','run-other',1,'{"status":"RUNNING"}',0)`)

	seedSession := func(id string, withLease bool) {
		s := domain.ClientSession{ID: id, ProjectID: "p1", Revision: 1, CreatedAt: now, UpdatedAt: now,
			WriterEpoch: 1, WriterClientID: "cli-a", UpstreamSession: "up-" + id,
			WorkspaceRef: strptr("ws-p1"), Title: strptr("qualification session"),
			ModelConfigRef: strptr("model-deepseek-flash"), CoreBuildID: strptr("core-build-w0302"),
			Protocol: domain.ClientSessionProtocol, ResumeExplicit: 1}
		if withLease {
			s.LeaseExpiresAt = tmptr(now.Add(2 * time.Hour))
		}
		t, _ := db.BeginTx(ctx, nil)
		if err := domain.MapClientSession(ctx, t, s); err != nil {
			failures = append(failures, map[string]string{"id": "SEED-" + id, "detail": err.Error()})
		}
		t.Commit()
	}
	for i := 1; i <= 9; i++ {
		seedSession(fmt.Sprintf("s%d", i), i != 9)
	}

	svc := &domain.ClientService{Doc: schemaDoc, Host: domain.ClientHostInfo{
		InstanceID: "host-w0302", CoreBuildID: "core-build-w0302", OperatingMode: "LOCAL_USER_HOST",
		ConfigRevision: 3, LeaseTTL: 2 * time.Hour}}

	env := func(cmd, client, sess, method, payload string, epoch any, expectedRev int64) json.RawMessage {
		sid := any(sess)
		if sess == "" {
			sid = nil
		}
		rev := any(expectedRev)
		if expectedRev == 0 {
			rev = nil
		}
		e := map[string]any{"protocol_version": "researchos-client/2", "command_id": cmd, "client_id": client,
			"project_id": "p1", "session_id": sid, "expected_revision": rev,
			"writer_epoch": epoch, "method": method, "payload": json.RawMessage(payload)}
		b, _ := json.Marshal(e)
		return b
	}
	// run() returns the response exactly as it goes on the wire: normalising through JSON is
	// what lets the assertions compare the typed service against the published schema.
	run := func(raw json.RawMessage, principal string) (*domain.Response, bool, error) {
		e, err := domain.DecodeEnvelope(raw)
		if err != nil {
			return nil, false, err
		}
		t, err := db.BeginTx(ctx, nil)
		if err != nil {
			return nil, false, err
		}
		res, replayed, err := svc.Execute(ctx, t, e, principal)
		if err != nil {
			t.Rollback()
			return nil, replayed, err
		}
		if err := t.Commit(); err != nil {
			return nil, false, err
		}
		b, _ := json.Marshal(res)
		var wire domain.Response
		if err := json.Unmarshal(b, &wire); err != nil {
			return nil, false, err
		}
		return &wire, replayed, nil
	}
	statusOf := func(r *domain.Response) string {
		if r == nil || r.Status == nil {
			return "<nil>"
		}
		return *r.Status
	}
	codeOf := func(r *domain.Response) string {
		if r == nil || r.ErrorCode == nil {
			return ""
		}
		return *r.ErrorCode
	}
	sessionCol := func(id, col string) int64 {
		var v int64
		db.QueryRowContext(ctx, `SELECT `+col+` FROM client_sessions WHERE id=?`, id).Scan(&v)
		return v
	}
	sessionState := func(id string) (rev, epoch, wm int64) {
		db.QueryRowContext(ctx, `SELECT revision, writer_epoch, event_watermark FROM client_sessions WHERE id=?`, id).Scan(&rev, &epoch, &wm)
		return
	}
	journalRows := func(project string) int {
		var n int
		db.QueryRowContext(ctx, `SELECT count(*) FROM outbox WHERE project=?`, project).Scan(&n)
		return n
	}
	seqList := func(project, sessionID string) []int64 {
		var out []int64
		r, err := db.QueryContext(ctx, `SELECT json_extract(body,'$.sequence') FROM outbox WHERE project=? AND json_extract(body,'$.session_id')=? ORDER BY 1`, project, sessionID)
		if err != nil {
			return out
		}
		defer r.Close()
		for r.Next() {
			var v int64
			r.Scan(&v)
			out = append(out, v)
		}
		return out
	}
	rowsFor := func(project, sessionID string) int {
		var n int
		db.QueryRowContext(ctx, `SELECT count(*) FROM outbox WHERE project=? AND json_extract(body,'$.session_id')=?`, project, sessionID).Scan(&n)
		return n
	}

	// --- handshake: host.status on the shared typed service
	hs, replay, err := run(env("cmd-host-1", "cli-a", "", "host.status", `{}`, nil, 0), "os-user-a")
	ok("HOST-STATUS-COMPLETED", err == nil && statusOf(hs) == "COMPLETED" && !replay, err, hs)
	if hs != nil && hs.Result != nil {
		b, _ := json.Marshal(hs.Result)
		var g any
		json.Unmarshal(b, &g)
		ok("HOST-STATUS-SCHEMA", schemaDoc.ValidateDef("HostStatusResult", g) == nil, schemaDoc.ValidateDef("HostStatusResult", g))
		ok("HOST-STATUS-BUILD-TRUTH", hs.Result["core_build_id"] == "core-build-w0302" &&
			hs.Result["authenticated_principal_ref"] == "principal:os-user-a", hs.Result["core_build_id"], hs.Result["authenticated_principal_ref"])
	}
	// unauthenticated connection is refused before any handler runs
	uh, _, err := run(env("cmd-host-2", "cli-a", "", "host.status", `{}`, nil, 0), "")
	ok("UNAUTHENTICATED-REJECT", err == nil && statusOf(uh) == "REJECTED" && codeOf(uh) == "UNAUTHENTICATED", err, uh)
	// a host-level write is gated by its own handler card and refused without side effects,
	// instead of half-applying configuration
	cfg, _, errCfg := run(env("cmd-cfg", "cli-a", "", "host.configure",
		`{"config_revision":1,"provider_id":"deepseek","base_url":"https://api.deepseek.com","model_id":"deepseek-chat","credential_ref":null}`, 1, 1), "os-user-a")
	ok("HOST-CONFIGURE-NOT-IMPLEMENTED-YET", errCfg == nil && statusOf(cfg) == "REJECTED" && codeOf(cfg) == "NOT_IMPLEMENTED", errCfg, cfg)
	ok("CONFIGURE-ENVELOPE-SCHEMA-VALID", schemaDoc.ValidateDefInput("CommandEnvelope", jsonGeneric(
		env("cmd-cfg2", "cli-a", "", "host.configure",
			`{"config_revision":1,"provider_id":"deepseek","base_url":"https://api.deepseek.com","model_id":"deepseek-chat","credential_ref":"cred-1"}`, 1, 1))) == nil)

	// --- cancel: real settlement comes from run state, never from the request
	ctrlPayload := func(target string) string {
		return `{"action":"CANCEL","target_id":"` + target + `","reason":"user requested"}`
	}
	c1, _, err := run(env("cmd-cancel-live", "cli-a", "s1", "session.control", ctrlPayload("run-live"), 1, 1), "os-user-a")
	ok("CANCEL-ACKNOWLEDGED", err == nil && statusOf(c1) == "ACKNOWLEDGED", err, c1)
	ok("CANCEL-WATERMARK-1", sessionCol("s1", "event_watermark") == 1, sessionCol("s1", "event_watermark"))
	ok("CANCEL-REVISION-BUMPED", sessionCol("s1", "revision") == 2, sessionCol("s1", "revision"))
	ok("CANCEL-JOURNAL-1", journalRows("p1") == 1, journalRows("p1"))
	ok("CANCEL-PENDING-RESULT-TYPED", c1 != nil && c1.Result != nil && c1.Result["operation_id"] == "op-cmd-cancel-live" &&
		c1.Result["related_resource_ref"] == nil, c1.Result)
	// replay of the same command_id: identical answer, zero additional effect
	c1b, replayed, err := run(env("cmd-cancel-live", "cli-a", "s1", "session.control", ctrlPayload("run-live"), 1, 1), "os-user-a")
	ok("REPLAY-SAME-ANSWER", err == nil && replayed && statusOf(c1b) == "ACKNOWLEDGED", err, replayed, c1b)
	ok("REPLAY-ZERO-SECOND-EFFECT", sessionCol("s1", "event_watermark") == 1 && sessionCol("s1", "revision") == 2 && journalRows("p1") == 1,
		sessionCol("s1", "event_watermark"), sessionCol("s1", "revision"), journalRows("p1"))
	// same key, different request body -> conflict, and nothing was written
	_, _, errConflict := run(env("cmd-cancel-live", "cli-a", "s1", "session.control", ctrlPayload("run-settled"), 1, 1), "os-user-a")
	ok("CONFLICT-SAME-KEY-DIFFERENT-REQUEST", errConflict == domain.ErrIdemConflict, errConflict)
	ok("CONFLICT-NO-STATE-DRIFT", journalRows("p1") == 1 && sessionCol("s1", "revision") == 2, journalRows("p1"), sessionCol("s1", "revision"))
	// a second principal is evaluated in its own idempotency namespace, not served another
	// user's stored answer
	other, otherReplay, errOther := run(env("cmd-cancel-live", "cli-a", "s2", "session.control", ctrlPayload("run-live"), 1, 1), "os-user-b")
	ok("PRINCIPAL-SCOPED-IDEMPOTENCY", errOther == nil && !otherReplay && statusOf(other) == "ACKNOWLEDGED", errOther, otherReplay, other)
	// cancel already confirmed and settled by the runtime -> COMPLETED with settlement truth
	c2, _, err := run(env("cmd-cancel-settled", "cli-a", "s3", "session.control", ctrlPayload("run-settled"), 1, 1), "os-user-a")
	ok("CANCEL-SETTLED-COMPLETED", err == nil && statusOf(c2) == "COMPLETED", err, c2)
	if c2 != nil && c2.Result != nil {
		ok("CANCEL-SETTLED-FIELDS", c2.Result["settled"] == true && c2.Result["children_stopped"] == true &&
			c2.Result["queue_empty"] == true && c2.Result["snapshot"] != nil, c2.Result)
	}
	// cancel requested but not yet confirmed is never reported as settled
	c3, _, err := run(env("cmd-cancel-unconfirmed", "cli-a", "s4", "session.control", ctrlPayload("run-cancelling"), 1, 1), "os-user-a")
	ok("CANCEL-UNCONFIRMED-NOT-SETTLED", err == nil && statusOf(c3) == "ACKNOWLEDGED" && codeOf(c3) == "", err, c3)
	if c3 != nil {
		if b, err := json.Marshal(c3.Result); err == nil {
			var g any
			json.Unmarshal(b, &g)
			ok("CANCEL-UNCONFIRMED-PENDING-SCHEMA", schemaDoc.ValidateDef("PendingResult", g) == nil, schemaDoc.ValidateDef("PendingResult", g))
		}
	}
	// terminal run without a confirmed cancel
	c4, _, err := run(env("cmd-cancel-failed", "cli-a", "s5", "session.control", ctrlPayload("run-failed"), 1, 1), "os-user-a")
	ok("CANCEL-ALREADY-TERMINAL", err == nil && statusOf(c4) == "REJECTED" && codeOf(c4) == "ALREADY_TERMINAL", err, c4)
	// unknown target, and a target belonging to another project
	c6, _, _ := run(env("cmd-cancel-other", "cli-a", "s6", "session.control", ctrlPayload("run-other"), 1, 1), "os-user-a")
	ok("CANCEL-CROSS-PROJECT-NOT-FOUND", statusOf(c6) == "REJECTED" && codeOf(c6) == "NOT_FOUND", c6)
	// PAUSE/RESUME are honestly refused until their handler card lands
	c7, _, _ := run(env("cmd-pause", "cli-a", "s6", "session.control", `{"action":"PAUSE","target_id":"run-live","reason":"x"}`, 1, 1), "os-user-a")
	ok("CONTROL-PAUSE-NOT-IMPLEMENTED", statusOf(c7) == "REJECTED" && codeOf(c7) == "NOT_IMPLEMENTED", c7)
	// every journal row for a session equals its watermark: no orphan events, no lost writes
	for _, sid := range []string{"s1", "s2", "s3", "s4", "s5", "s6"} {
		ok("ROWS-EQ-WATERMARK-"+sid, int64(rowsFor("p1", sid)) == sessionCol(sid, "event_watermark"),
			rowsFor("p1", sid), sessionCol(sid, "event_watermark"))
	}

	// --- writer / revision / epoch gates
	stale, _, err := run(env("cmd-stale-rev", "cli-b", "s7", "session.attach",
		`{"after_sequence":0,"request_write_owner":true}`, nil, 99), "os-user-a")
	ok("TAKEOVER-STALE-REVISION", err == nil && statusOf(stale) == "REJECTED" && codeOf(stale) == "VERSION_CONFLICT", err, stale)
	if stale != nil {
		ok("TAKEOVER-STALE-REPORTS-CURRENT", stale.Revision != nil && *stale.Revision == 1, stale.Revision)
	}
	sameClient, _, _ := run(env("cmd-tk-same", "cli-a", "s7", "session.attach",
		`{"after_sequence":0,"request_write_owner":true}`, nil, 1), "os-user-a")
	ok("TAKEOVER-SAME-CLIENT-BUSY", statusOf(sameClient) == "REJECTED" && codeOf(sameClient) == "WRITER_BUSY", sameClient)
	ok("TAKEOVER-SAME-CLIENT-NO-MOVE", sessionCol("s7", "writer_epoch") == 1 && sessionCol("s7", "revision") == 1,
		sessionCol("s7", "writer_epoch"), sessionCol("s7", "revision"))
	tk, _, err := run(env("cmd-tk-real", "cli-b", "s7", "session.attach",
		`{"after_sequence":0,"request_write_owner":true}`, nil, 1), "os-user-a")
	ok("TAKEOVER-ACKNOWLEDGED", err == nil && statusOf(tk) == "ACKNOWLEDGED", err, tk)
	ok("TAKEOVER-EPOCH-ADVANCED", sessionCol("s7", "writer_epoch") == 2, sessionCol("s7", "writer_epoch"))
	// the transfer is journaled with the new writer lease, taken from host configuration
	handoffRows := rowsFor("p1", "s7")
	ok("TAKEOVER-JOURNALED", handoffRows == 1, handoffRows)
	// a takeover request that claims a writer epoch is refused at the decode boundary
	badClaim, _, badClaimErr := run(env("cmd-tk-claim", "cli-c", "s8", "session.attach",
		`{"after_sequence":0,"request_write_owner":true}`, 1, 1), "os-user-a")
	ok("TAKEOVER-WITH-EPOCH-INVALID", badClaimErr != nil || codeOf(badClaim) == "INVALID_REQUEST", badClaimErr, badClaim)
	ok("TAKEOVER-WITH-EPOCH-NO-MOVE", sessionCol("s8", "writer_epoch") == 1 && rowsFor("p1", "s8") == 0,
		sessionCol("s8", "writer_epoch"), rowsFor("p1", "s8"))
	// after the transfer the old epoch is refused on its own, with the current revision
	s7rev, _, _ := sessionState("s7")
	oldEpoch, _, errOld := run(env("cmd-old-epoch", "cli-b", "s7", "session.control", ctrlPayload("run-live"), 1, s7rev), "os-user-a")
	ok("OLD-EPOCH-REJECTED", errOld == nil && statusOf(oldEpoch) == "REJECTED" && codeOf(oldEpoch) == "STALE_WRITER_EPOCH", errOld, oldEpoch)
	// the new writer continues on the current revision and epoch
	newRev, newEpoch, _ := sessionState("s7")
	newWrite, _, errNew := run(env("cmd-new-writer", "cli-b", "s7", "session.control", ctrlPayload("run-live"), newEpoch, newRev), "os-user-a")
	ok("NEW-WRITER-WRITE-OK", errNew == nil && statusOf(newWrite) == "ACKNOWLEDGED", errNew, newWrite, newRev, newEpoch)
	// a session id from another project never resolves
	proj2 := map[string]any{"protocol_version": "researchos-client/2", "command_id": "cmd-cross-proj2", "client_id": "cli-a",
		"project_id": "p2", "session_id": "s1", "expected_revision": newRev, "writer_epoch": 1,
		"method": "session.control", "payload": json.RawMessage(ctrlPayload("run-live"))}
	p2b, _ := json.Marshal(proj2)
	crossProj, _, _ := run(p2b, "os-user-a")
	ok("CROSS-PROJECT-SESSION-REJECT", statusOf(crossProj) == "REJECTED" && codeOf(crossProj) == "NOT_FOUND", crossProj)
	// concurrent takeovers on one session: exactly one epoch transfer survives
	var wg sync.WaitGroup
	conc := make([]*domain.Response, 2)
	concErr := make([]error, 2)
	for i := 0; i < 2; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			r, _, e := run(env(fmt.Sprintf("cmd-conc-%d", i), fmt.Sprintf("cli-x%d", i), "s9", "session.attach",
				`{"after_sequence":0,"request_write_owner":true}`, nil, 1), "os-user-a")
			conc[i], concErr[i] = r, e
		}(i)
	}
	wg.Wait()
	acks, rej := 0, 0
	for _, r := range conc {
		switch statusOf(r) {
		case "ACKNOWLEDGED":
			acks++
		case "REJECTED":
			rej++
		}
	}
	ok("CONCURRENT-TAKEOVER-ONE-WRITER", acks == 1 && rej == 1 && sessionCol("s9", "writer_epoch") == 2, acks, rej, concErr, sessionCol("s9", "writer_epoch"))

	// --- event tail, cursor and snapshot recovery
	ev1, _, err := run(env("cmd-events", "cli-a", "s1", "session.events", `{"after_sequence":0,"limit":50}`, nil, 0), "os-user-a")
	ok("EVENTS-COMPLETED", err == nil && statusOf(ev1) == "COMPLETED", err, ev1)
	if ev1 != nil {
		arr, _ := ev1.Result["events"].([]any)
		ok("EVENTS-TAIL-1", len(arr) == 1 && ev1.Result["high_watermark"] == float64(1) &&
			ev1.Result["next_sequence"] == float64(1) && ev1.Result["has_more"] == false, len(arr), ev1.Result)
		b, _ := json.Marshal(ev1)
		var g map[string]any
		json.Unmarshal(b, &g)
		ok("EVENTS-RESPONSE-SCHEMA", schemaDoc.ValidateDef("CommandResponse", g) == nil, schemaDoc.ValidateDef("CommandResponse", g))
	}
	future, _, _ := run(env("cmd-events-future", "cli-a", "s1", "session.events", `{"after_sequence":9,"limit":50}`, nil, 0), "os-user-a")
	ok("EVENTS-FUTURE-CURSOR-REJECT", statusOf(future) == "REJECTED" && codeOf(future) == "CURSOR_INVALID", future)
	// the same cursor position on attach is answered by the snapshot, not by a journal hole
	attachBad, _, _ := run(env("cmd-attach-future", "cli-a", "s1", "session.attach", `{"after_sequence":9,"request_write_owner":false}`, 1, 2), "os-user-a")
	ok("ATTACH-FUTURE-CURSOR-REJECT", statusOf(attachBad) == "REJECTED" && codeOf(attachBad) == "CURSOR_INVALID", attachBad)
	attachOK, _, errAttach := run(env("cmd-attach-ok", "cli-a", "s1", "session.attach", `{"after_sequence":1,"request_write_owner":false}`, 1, 2), "os-user-a")
	ok("ATTACH-SNAPSHOT-RECOVERY", errAttach == nil && statusOf(attachOK) == "COMPLETED" &&
		attachOK.Result["write_owner_acquired"] == false && attachOK.Result["snapshot"] != nil, errAttach, attachOK)
	// snapshot carries the watermark the writers advance, so recovery is unambiguous
	sg, _, err := run(env("cmd-snapshot", "cli-a", "s1", "session.get", `{}`, nil, 0), "os-user-a")
	ok("SNAPSHOT-COMPLETED", err == nil && statusOf(sg) == "COMPLETED", err, sg)
	if sg != nil {
		snap := sg.Result
		ok("SNAPSHOT-WATERMARK-MATCHES-JOURNAL", snap["event_sequence"] == float64(1), snap["event_sequence"])
		ok("SNAPSHOT-RESUME-FLAG", snap["resume_requires_explicit_user"] == true, snap["resume_requires_explicit_user"])
		w, _ := snap["writer"].(map[string]any)
		ok("SNAPSHOT-WRITER-LEASE", w != nil && w["client_id"] == "cli-a" && w["epoch"] == float64(1), snap["writer"])
	}
	s9snap, _, _ := run(env("cmd-snapshot-9", "cli-a", "s9", "session.get", `{}`, nil, 0), "os-user-a")
	if s9snap != nil && s9snap.Result != nil {
		snap := s9snap.Result
		// s9 has no lease expiry: writer must be reported as null, never fabricated
		ok("SNAPSHOT-NULL-WRITER", snap["writer"] == nil, snap["writer"])
		ok("SNAPSHOT-NULLABLE-REFS", snap["goal_id"] == nil && snap["active_run_id"] == nil &&
			snap["checkpoint_artifact_ref"] == nil && snap["run_status"] == nil, snap["goal_id"], snap["active_run_id"])
	}

	// --- stream reconstruction and gap detection straight on the journal
	rev2, ep2, wm2 := sessionState("s2")
	type pending struct {
		seq   int64
		rev   int64
		kind  string
		pay   string
		id    string
	}
	kindOf := func(seq, rev int64, kind, pay, id string) pending {
		return pending{seq: seq, rev: rev, kind: kind, pay: pay, id: id}
	}
	plan := []pending{
		kindOf(wm2+1, rev2, "RUN_STATE", `{"run_id":"run-settled","status":"SETTLED","revision":7,"cancel_requested_at":null,"cancel_confirmed_at":null,"settled_at":"`+now.Format(time.RFC3339Nano)+`","children_stopped":true,"queue_empty":true}`, "ev-direct-1"),
		kindOf(wm2+2, rev2+1, "MESSAGE", `{"message_id":"m1","role":"ASSISTANT","phase":"START","part_index":0,"content_offset_utf8_bytes":0,"text":""}`, "ev-direct-2"),
		kindOf(wm2+3, rev2+2, "MESSAGE", `{"message_id":"m1","role":"ASSISTANT","phase":"DELTA","part_index":0,"content_offset_utf8_bytes":0,"text":"hello "}`, "ev-direct-3"),
		kindOf(wm2+4, rev2+3, "MESSAGE", `{"message_id":"m1","role":"ASSISTANT","phase":"DELTA","part_index":0,"content_offset_utf8_bytes":6,"text":"world"}`, "ev-direct-4"),
		kindOf(wm2+5, rev2+4, "MESSAGE", `{"message_id":"m1","role":"ASSISTANT","phase":"END","part_index":0,"content_offset_utf8_bytes":11,"text":""}`, "ev-direct-5"),
	}
	tx2, _ := db.BeginTx(ctx, nil)
	for i, a := range plan {
		ev := &domain.SessionEvent{EventID: strptr(a.id), SessionID: strptr("s2"), Sequence: i64ptr(a.seq),
			CoreBuildID: strptr("core-build-w0302"), ProtocolVersion: strptr(domain.ProtocolV2),
			DomainEventID: strptr("de-" + a.id), Kind: strptr(a.kind), Payload: []byte(a.pay)}
		err := domain.AppendSessionEvent(ctx, tx2, schemaDoc, "p1", ev, ep2, a.rev)
		ok(fmt.Sprintf("APPEND-%s-%d", a.kind, i+1), err == nil, err)
		if err != nil {
			break
		}
	}
	tx2.Commit()
	// reuse, holes and a stale epoch are each refused with their own error, inside one tx
	curRev2, curEp2, curWm2 := sessionState("s2")
	tx3, _ := db.BeginTx(ctx, nil)
	mkEv := func(seq int64, kind, pay, id string) *domain.SessionEvent {
		return &domain.SessionEvent{EventID: strptr(id), SessionID: strptr("s2"), Sequence: i64ptr(seq),
			CoreBuildID: strptr("core-build-w0302"), ProtocolVersion: strptr(domain.ProtocolV2),
			DomainEventID: strptr("de-" + id), Kind: strptr(kind), Payload: []byte(pay)}
	}
	errReuse := domain.AppendSessionEvent(ctx, tx3, schemaDoc, "p1", mkEv(curWm2, "RUN_STATE",
		`{"run_id":"run-settled","status":"SETTLED","revision":7,"cancel_requested_at":null,"cancel_confirmed_at":null,"settled_at":"`+now.Format(time.RFC3339Nano)+`","children_stopped":true,"queue_empty":true}`, "ev-dup"), curEp2, curRev2)
	ok("APPEND-REUSE-REJECT", errors.Is(errReuse, domain.ErrEventSequence), errReuse)
	errHole := domain.AppendSessionEvent(ctx, tx3, schemaDoc, "p1", mkEv(curWm2+5, "ERROR",
		`{"code":"INTERNAL_ERROR","message":"x","retryable":false,"recovery":"WAIT_FOR_SETTLEMENT","current_revision":null,"current_writer_epoch":null,"resource_request_id":null,"retry_after_ms":null,"correlation_id":"c"}`, "ev-hole"), curEp2, curRev2)
	ok("APPEND-HOLE-REJECT", errors.Is(errHole, domain.ErrEventSequence), errHole)
	errEpoch := domain.AppendSessionEvent(ctx, tx3, schemaDoc, "p1", mkEv(curWm2+1, "ERROR",
		`{"code":"INTERNAL_ERROR","message":"x","retryable":false,"recovery":"WAIT_FOR_SETTLEMENT","current_revision":null,"current_writer_epoch":null,"resource_request_id":null,"retry_after_ms":null,"correlation_id":"c"}`, "ev-stale-ep"), curEp2-1, curRev2)
	ok("APPEND-STALE-EPOCH-REJECT", errors.Is(errEpoch, domain.ErrStaleEpoch), errEpoch)
	errStaleRev := domain.AppendSessionEvent(ctx, tx3, schemaDoc, "p1", mkEv(curWm2+1, "ERROR",
		`{"code":"INTERNAL_ERROR","message":"x","retryable":false,"recovery":"WAIT_FOR_SETTLEMENT","current_revision":null,"current_writer_epoch":null,"resource_request_id":null,"retry_after_ms":null,"correlation_id":"c"}`, "ev-stale-rev"), curEp2, curRev2+3)
	ok("APPEND-STALE-REVISION-REJECT", errors.Is(errStaleRev, domain.ErrStaleRevision), errStaleRev)
	// a stream that never started cannot be continued
	errStream := domain.AppendSessionEvent(ctx, tx3, schemaDoc, "p1", mkEv(curWm2+1, "MESSAGE",
		`{"message_id":"m-new","role":"ASSISTANT","phase":"DELTA","part_index":0,"content_offset_utf8_bytes":3,"text":"x"}`, "ev-no-start"), curEp2, curRev2)
	ok("APPEND-STREAM-WITHOUT-START-REJECT", errors.Is(errStream, domain.ErrStreamWithoutStart), errStream)
	tx3.Rollback()
	// duplicate event ids cannot be journaled twice even under a different sequence
	tx6, _ := db.BeginTx(ctx, nil)
	errDupID := domain.AppendSessionEvent(ctx, tx6, schemaDoc, "p1", mkEv(curWm2+1, "RUN_STATE",
		`{"run_id":"run-settled","status":"SETTLED","revision":7,"cancel_requested_at":null,"cancel_confirmed_at":null,"settled_at":"`+now.Format(time.RFC3339Nano)+`","children_stopped":true,"queue_empty":true}`, "ev-direct-1"), curEp2, curRev2+1)
	ok("APPEND-DUPLICATE-EVENT-ID-REJECT", errDupID != nil, errDupID)
	tx6.Rollback()
	// a command failure rolls the business write and its event back together
	rowsBefore := rowsFor("p1", "s6")
	s6rev := sessionCol("s6", "revision")
	tx7, _ := db.BeginTx(ctx, nil)
	e7, derr7 := domain.DecodeEnvelope(env("cmd-poison", "cli-a", "s6", "session.control", ctrlPayload("run-live"), 1, s6rev))
	if derr7 == nil {
		_, _, _ = svc.Execute(ctx, tx7, e7, "os-user-a")
	}
	tx7.Rollback()
	ok("FAILED-COMMAND-NO-ORPHAN-EVENT", derr7 == nil && rowsFor("p1", "s6") == rowsBefore, derr7, rowsBefore, rowsFor("p1", "s6"))
	tx8, _ := db.BeginTx(ctx, nil)
	missing, err := domain.DetectEventGaps(ctx, tx8, "p1", "s2")
	tx8.Rollback()
	dbg := seqList("p1", "s2")
	ok("NO-GAPS-AFTER-APPENDS", err == nil && len(missing) == 0, err, missing, dbg, sessionCol("s2", "event_watermark"))
	// a forged hole is detectable and recovery falls back to the snapshot
	realRows := rowsFor("p1", "s2")
	db.ExecContext(ctx, `INSERT INTO outbox(project,sequence,id,body) VALUES('p1',900,'ev-forged',
		'{"event_id":"ev-forged","session_id":"s2","sequence":`+fmt.Sprint(realRows+2)+`,"core_build_id":"core-build-w0302","protocol_version":"researchos-client/2","run_id":null,"command_id":null,"domain_event_id":"de-forged","kind":"ERROR","payload":{"code":"INTERNAL_ERROR","message":"forged","retryable":false,"recovery":"WAIT_FOR_SETTLEMENT","current_revision":null,"current_writer_epoch":null,"resource_request_id":null,"retry_after_ms":null,"correlation_id":"forged"}}')`)
	tx4, _ := db.BeginTx(ctx, nil)
	missing, _ = domain.DetectEventGaps(ctx, tx4, "p1", "s2")
	ok("GAP-DETECTED-AFTER-FORGER", len(missing) > 0 && missing[0] == int64(realRows+1), missing, realRows)
	tx4.Rollback()
	// the durable journal cannot be rewritten or deleted out from under the watermark
	_, delErr := db.ExecContext(ctx, `DELETE FROM outbox WHERE id='ev-direct-5'`)
	ok("JOURNAL-DELETE-BLOCKED", delErr != nil, delErr)
	_, updErr := db.ExecContext(ctx, `UPDATE outbox SET body='{"event_id":"ev-direct-5"}' WHERE id='ev-direct-5'`)
	ok("JOURNAL-UPDATE-BLOCKED", updErr != nil, updErr)
	// snapshot reconstruction reads the journal, not any client-side cache
	sg2, _, _ := run(env("cmd-snapshot-2", "cli-a", "s2", "session.get", `{}`, nil, 0), "os-user-a")
	if sg2 != nil && sg2.Result != nil {
		msgs, _ := sg2.Result["messages"].([]any)
		ok("SNAPSHOT-MESSAGES-REBUILT", len(msgs) == 1, msgs)
		if len(msgs) == 1 {
			m := msgs[0].(map[string]any)
			parts, _ := m["parts"].([]any)
			txt := ""
			if len(parts) == 1 {
				txt, _ = parts[0].(map[string]any)["text"].(string)
			}
			ok("SNAPSHOT-STREAM-TEXT", m["complete"] == true && txt == "hello world" && m["role"] == "ASSISTANT", m, txt)
		}
		b, _ := json.Marshal(sg2)
		var g map[string]any
		json.Unmarshal(b, &g)
		ok("SNAPSHOT-RESPONSE-SCHEMA", schemaDoc.ValidateDef("CommandResponse", g) == nil, schemaDoc.ValidateDef("CommandResponse", g))
	}

	// --- sensitive fields never enter ordinary payloads
	tx5, _ := db.BeginTx(ctx, nil)
	sens := mkEv(curWm2+1, "USAGE", `{"ledger_entry_id":"l1","provider_usage_id":"u1","input_tokens":1,"output_tokens":1,"money":null,"cost_known":false,"credential_value":"sk-secret"}`, "ev-secret")
	err = domain.AppendSessionEvent(ctx, tx5, schemaDoc, "p1", sens, curEp2, curRev2)
	ok("SENSITIVE-EVENT-REJECTED", err != nil && strings.Contains(err.Error(), "SENSITIVE_FIELD_IN_EVENT_PAYLOAD"), err)
	tx5.Rollback()
	credResp := []byte(`{"protocol_version":"researchos-client/2","command_id":"r1","method":"host.status","status":"COMPLETED","session_id":null,"revision":1,"error_code":null,"error":null,"result":{"host_instance_id":"h","core_build_id":"b","protocol_versions":["researchos-client/2"],"host_state":"READY","client_id":"c","authenticated_principal_ref":"p","config_revision":1,"model_configurations":[],"credentials":[{"provider":"deepseek","kind":"API_KEY","credential_ref":"r","availability":"AVAILABLE","last_checked_at":null,"credential_exposed_to_renderer":false,"credential_value":"sk-leak"}],"workspaces":[],"supported_methods":["host.status"],"operating_mode":"LOCAL_USER_HOST"}}`)
	var generic map[string]any
	json.Unmarshal(credResp, &generic)
	ok("CREDENTIAL-IN-RESPONSE-REJECTED", schemaDoc.ValidateDef("CommandResponse", generic) != nil, "writeOnly field accepted in read direction")
	// credential material is legal only in the native import request direction
	credReq := []byte(`{"provider_id":"p1","credential_kind":"API_KEY","credential_value":"EXAMPLE_ONLY_NOT_A_REAL_SECRET","replace_credential_ref":null}`)
	ok("CREDENTIAL-IN-NATIVE-REQUEST-ALLOWED", domain.ValidateNativeTransient(schemaDoc, "NativeCredentialImportRequest", credReq, true) == nil)
	ok("CREDENTIAL-IN-NATIVE-RESULT-REJECTED", domain.ValidateNativeTransient(schemaDoc, "NativeCredentialImportResult", credReq, false) != nil)

	// --- protocol boundary negatives
	_, _, bareErr := run([]byte(`{"method":"host.status","payload":{}}`), "os-user-a")
	ok("BARE-OBJECT-REJECT", bareErr != nil && strings.Contains(bareErr.Error(), "UNtyped_ENVELOPE"), bareErr)
	_, _, oldP := run([]byte(`{"protocol_version":"researchos-client/1","command_id":"x","client_id":"c","project_id":"p1","session_id":null,"expected_revision":null,"writer_epoch":null,"method":"host.status","payload":{}}`), "os-user-a")
	ok("OLD-PROTOCOL-NO-DOWNGRADE", oldP == domain.ErrProtocolVersion, oldP)
	_, _, unknownM := run(env("cmd-unknown", "cli-a", "", "session.teleport", `{}`, nil, 0), "os-user-a")
	ok("UNKNOWN-METHOD-REJECT", unknownM == domain.ErrUnknownMethod, unknownM)
	crossResp := []byte(`{"protocol_version":"researchos-client/2","command_id":"x","method":"workspace.read","status":"COMPLETED","session_id":"s1","revision":1,"error_code":null,"error":null,"result":{"action":"CANCEL","target_id":"t","control_request_id":"c","settled":true,"children_stopped":true,"queue_empty":true,"snapshot":{}}}`)
	cr, err := domain.DecodeResponse(crossResp)
	if err == nil {
		err = domain.ValidateResultAgainstMethod("session.control", cr, schemaDoc)
	}
	ok("CROSS-METHOD-RESULT-REJECT", err == domain.ErrCrossMethod, err)
	// a COMPLETED attach whose result is an empty object is refused by the published schema
	bareRes := []byte(`{"protocol_version":"researchos-client/2","command_id":"x","method":"session.attach","status":"COMPLETED","session_id":"s1","revision":1,"error_code":null,"error":null,"result":{}}`)
	var br map[string]any
	json.Unmarshal(bareRes, &br)
	ok("BARE-RESULT-SCHEMA-REJECT", schemaDoc.ValidateDef("CommandResponse", br) != nil, "empty attach result accepted")
	// an ACKNOWLEDGED that claims settlement is refused
	claim := []byte(`{"protocol_version":"researchos-client/2","command_id":"x","method":"session.control","status":"ACKNOWLEDGED","session_id":"s1","revision":1,"error_code":null,"error":null,"result":{"settled":true,"accepted_at":"2026-10-01T00:00:00Z","operation_id":"op","after_sequence":0,"related_resource_ref":null}}`)
	_, err = domain.DecodeResponse(claim)
	ok("ACK-CLAIMS-SETTLEMENT-REJECT", err != nil && strings.Contains(fmt.Sprint(err), "ACKNOWLEDGED_CLAIMS_SETTLEMENT"), err)
	// a non-rejection carrying error fields is refused
	mixed := []byte(`{"protocol_version":"researchos-client/2","command_id":"x","method":"host.status","status":"COMPLETED","session_id":null,"revision":1,"error_code":"NOT_FOUND","error":null,"result":{}}`)
	_, err = domain.DecodeResponse(mixed)
	ok("NON-REJECT-WITH-ERROR-REJECT", err != nil && strings.Contains(fmt.Sprint(err), "NON_REJECT_WITH_ERROR_FIELDS"), err)
	// a rejection without the matching error object is refused
	noErrObj := []byte(`{"protocol_version":"researchos-client/2","command_id":"x","method":"host.status","status":"REJECTED","session_id":null,"revision":1,"error_code":"NOT_FOUND","error":null,"result":null}`)
	_, err = domain.DecodeResponse(noErrObj)
	ok("REJECT-WITHOUT-ERROR-OBJECT", err != nil && strings.Contains(fmt.Sprint(err), "REJECT_WITHOUT_MATCHING_ERROR_OBJECT"), err)
	// sealed sessions reject writes and event appends
	s5rev, s5ep, _ := sessionState("s5")
	txs, _ := db.BeginTx(ctx, nil)
	sealErr := domain.Seal(ctx, txs, "s5", s5ep, s5rev)
	ok("SEAL-OK", sealErr == nil, sealErr)
	txs.Commit()
	sealedWrite, _, _ := run(env("cmd-sealed", "cli-a", "s5", "session.control", ctrlPayload("run-live"), s5ep, sessionCol("s5", "revision")), "os-user-a")
	ok("SEALED-WRITE-REJECT", statusOf(sealedWrite) == "REJECTED" && codeOf(sealedWrite) == "SESSION_ARCHIVED", sealedWrite)
	// an unknown protocol version inside an event is refused
	badProto := []byte(`{"event_id":"e","session_id":"s1","sequence":1,"core_build_id":"b","protocol_version":"researchos-client/1","run_id":null,"command_id":null,"domain_event_id":"d","kind":"ERROR","payload":{}}`)
	_, err = domain.DecodeEvent(badProto)
	ok("EVENT-OLD-PROTOCOL-REJECT", err == domain.ErrProtocolVersion, err)
	missingField := []byte(`{"event_id":"e","session_id":"s1","sequence":1,"core_build_id":"b","protocol_version":"researchos-client/2","run_id":null,"command_id":null,"kind":"ERROR","payload":{}}`)
	_, err = domain.DecodeEvent(missingField)
	ok("EVENT-MISSING-DOMAIN-ID-REJECT", err != nil && strings.Contains(fmt.Sprint(err), "MISSING_FIELD:domain_event_id"), err)
	unknownField := []byte(`{"event_id":"e","session_id":"s1","sequence":1,"core_build_id":"b","protocol_version":"researchos-client/2","run_id":null,"command_id":null,"domain_event_id":"d","kind":"ERROR","payload":{},"task_id":"t"}`)
	_, err = domain.DecodeEvent(unknownField)
	ok("EVENT-UNKNOWN-FIELD-REJECT", err != nil && strings.Contains(fmt.Sprint(err), "UNKNOWN_FIELD:task_id"), err)
	// native transients are graded by direction, and never masquerade as command methods
	ok("NATIVE-TRANSIENT-REQUEST-OK", domain.ValidateNativeTransient(schemaDoc, "NativeCredentialImportRequest", credReq, true) == nil)
	ok("NATIVE-TRANSIENT-UNKNOWN-ENUM", domain.ValidateNativeTransient(schemaDoc, "NativeCredentialImportRequest",
		[]byte(`{"provider_id":"p1","credential_kind":"NOT_A_KIND","credential_value":"x","replace_credential_ref":null}`), true) != nil)
	// the pinned contract's only writeOnly annotation is NativeCredentialImportRequest's
	// credential_value: the schema accepts that shape structurally, so ONLY the direction rule
	// can reject it in a read path. This is the case that makes the direction rule observable.
	credReqRead := map[string]any{"provider_id": "p1", "credential_kind": "API_KEY",
		"credential_value": "EXAMPLE_ONLY_NOT_A_REAL_SECRET", "replace_credential_ref": nil}
	writeErr := schemaDoc.ValidateDefInput("NativeCredentialImportRequest", credReqRead)
	readErr := schemaDoc.ValidateDef("NativeCredentialImportRequest", credReqRead)
	ok("WRITE-ONLY-DEF-ALLOWED-IN-DIRECTION", writeErr == nil, writeErr)
	ok("WRITE-ONLY-DEF-READ-DIRECTION-REJECTED", readErr != nil &&
		strings.Contains(readErr.Error(), "WRITE_ONLY_IN_READ_PATH"), readErr)
	ok("NATIVE-TRANSIENT-NOT-A-METHOD", func() bool {
		_, err := domain.DecodeEnvelope([]byte(`{"protocol_version":"researchos-client/2","command_id":"c","client_id":"a","project_id":"p1","session_id":null,"expected_revision":null,"writer_epoch":null,"method":"credential.import","payload":{}}`))
		return err == domain.ErrUnknownMethod
	}())
	// the published relative-path pattern keeps its real semantics under RE2
	for _, tc := range []struct {
		value string
		valid bool
	}{
		{"src/main.go", true}, {"a/b/c.txt", true}, {"notes.md", true}, {`a\b\c.go`, true},
		{"../secrets", false}, {"/abs/path", false}, {"C:/Windows", false}, {"a/../b", false},
		{`..\..\x`, false}, {"with\x00nul", false}, {"", false},
	} {
		err := schemaDoc.ValidateDef("RelativePath", tc.value)
		name := strings.NewReplacer("/", "_", "\\", "_", "\x00", "NUL", ".", "dot").Replace(tc.value)
		if name == "" {
			name = "EMPTY"
		}
		label := "RELPATH-ACCEPT-" + name
		if !tc.valid {
			label = "RELPATH-REJECT-" + name
		}
		ok(label, (err != nil) != tc.valid, tc.value, err)
	}

	// --- the same typed service behind the host's HTTP boundary (CLI and Desktop share it)
	hdb, herr := store.Open(filepath.Join(tmp, "host.sqlite"))
	ok("HOST-DB-OPEN", herr == nil, herr)
	if herr == nil {
		defer hdb.Close()
		// the host database is brought up by the same continuous migration the real host runs
		hfiles, _ := filepath.Glob(filepath.Join(root, "migrations/sqlite/0*.sql"))
		hmigOK := true
		for i, f := range hfiles {
			hb, _ := os.ReadFile(f)
			htx, e := hdb.BeginTx(ctx, nil)
			if e != nil {
				hmigOK = false
				break
			}
			if _, e = htx.ExecContext(ctx, string(hb)); e != nil {
				htx.Rollback()
				hmigOK = false
				break
			}
			htx.ExecContext(ctx, `INSERT OR IGNORE INTO schema_migrations(version) VALUES (?)`, i+1)
			htx.Commit()
		}
		hnext, _ := os.ReadFile(filepath.Join(root, "migrations/sqlite/next_v24_sessions.sql"))
		htx2, e := hdb.BeginTx(ctx, nil)
		if e != nil {
			hmigOK = false
		} else {
			if _, e = htx2.ExecContext(ctx, string(hnext)); e != nil {
				htx2.Rollback()
				hmigOK = false
			} else {
				htx2.ExecContext(ctx, `INSERT OR IGNORE INTO schema_migrations(version) VALUES (9021)`)
				if e = htx2.Commit(); e != nil {
					hmigOK = false
				}
			}
		}
		ok("HOST-V24-MIGRATION", hmigOK, e)
		ok("HOST-BASELINE-MIGRATION", hmigOK && len(hfiles) == 20, len(hfiles))
		svc2, nerr := domain.New(hdb, filepath.Join(root, "spec", "v2.0", "contracts"),
			filepath.Join(root, "migrations", "sqlite", "0002_domain.sql"))
		ok("HOST-SERVICE-READY", nerr == nil, nerr)
		if nerr == nil {
			webDir := filepath.Join(tmp, "web")
			os.MkdirAll(webDir, 0o755)
			os.WriteFile(filepath.Join(webDir, "index.html"), []byte("<html><body>researchos</body></html>"), 0o644)
			ts := httptest.NewServer(api.Handler(hdb, webDir, svc2))
			defer ts.Close()
			// The local loopback listener occasionally refuses the very first connection on this
			// Windows host (already observed in W02-03); retry the transport only, never a
			// request that reached the service, and keep the retry count as evidence.
			httpRetries := 0
			post := func(body, token string) (int, []byte) {
				for attempt := 0; attempt < 4; attempt++ {
					req, e := http.NewRequest("POST", ts.URL+"/v2/command", strings.NewReader(body))
					if e != nil {
						return 0, []byte(e.Error())
					}
					req.Header.Set("Content-Type", "application/json")
					if token != "" {
						req.Header.Set("Authorization", "Bearer "+token)
					}
					resp, e := ts.Client().Do(req)
					if e != nil {
						httpRetries++
						time.Sleep(150 * time.Millisecond)
						continue
					}
					b, _ := io.ReadAll(resp.Body)
					resp.Body.Close()
					return resp.StatusCode, b
				}
				return 0, []byte("transport unavailable after retries")
			}
			hostStatus := `{"protocol_version":"researchos-client/2","command_id":"http-host-1","client_id":"cli-http","project_id":null,"session_id":null,"expected_revision":null,"writer_epoch":null,"method":"host.status","payload":{}}`
			st0, body0 := post(hostStatus, "")
			ok("HTTP-UNAUTHENTICATED-401", st0 == 401 && bytes.Contains(body0, []byte("UNAUTHENTICATED")), st0, string(body0))
			stBare, bodyBare := post(`not-json-at-all`, "")
			ok("HTTP-NON-JSON-400", stBare == 400 && bytes.Contains(bodyBare, []byte("INVALID_REQUEST")), stBare, string(bodyBare))
			stNoProto, bodyNoProto := post(`{"method":"host.status","payload":{}}`, "")
			ok("HTTP-MISSING-PROTOCOL-400", stNoProto == 400 && bytes.Contains(bodyNoProto, []byte("UNSUPPORTED_PROTOCOL")), stNoProto, string(bodyNoProto))
			stOld, bodyOld := post(`{"protocol_version":"researchos-client/1","command_id":"http-old","client_id":"c","project_id":null,"session_id":null,"expected_revision":null,"writer_epoch":null,"method":"host.status","payload":{}}`, "")
			// the protocol answer comes before any credential question
			ok("HTTP-OLD-PROTOCOL-BEFORE-AUTH", stOld == 400 && bytes.Contains(bodyOld, []byte("UNSUPPORTED_PROTOCOL")), stOld, string(bodyOld))

			perr := svc2.ProvisionPrincipal(ctx, domain.Principal{ID: "qual-w0302", Roles: []string{"READER"},
				Grants: []domain.Grant{{ProjectID: "p1"}}})
			ok("HTTP-PRINCIPAL-PROVISIONED", perr == nil, perr)
			token, terr := svc2.IssueCredential(ctx, "qual-w0302", 5*time.Minute)
			ok("HTTP-CREDENTIAL-ISSUED", terr == nil && token != "", terr)
			st1, body1 := post(hostStatus, token)
			ok("HTTP-HOST-STATUS-200", st1 == 200, st1, string(body1))
			var wire map[string]any
			json.Unmarshal(body1, &wire)
			if wire != nil {
				verr := schemaDoc.ValidateDef("CommandResponse", wire)
				ok("HTTP-HOST-STATUS-TYPED", verr == nil, verr)
				res, _ := wire["result"].(map[string]any)
				build, _ := res["core_build_id"].(string)
				ok("HTTP-HOST-BUILD-REAL", strings.HasPrefix(build, "core-"), build)
				ok("HTTP-HOST-PRINCIPAL-FROM-CREDENTIAL", res["authenticated_principal_ref"] == "principal:qual-w0302", res["authenticated_principal_ref"])
			}

			hdb.ExecContext(ctx, `INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('p1','Project','p1',1,'{}',0)`)
			hdb.ExecContext(ctx, `INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('p1','Run','run-http',1,'{"status":"RUNNING","children_stopped":false,"queue_empty":false}',0)`)
			tsession := domain.ClientSession{ID: "shttp", ProjectID: "p1", Revision: 1, CreatedAt: now, UpdatedAt: now,
				WriterEpoch: 1, WriterClientID: "cli-http", UpstreamSession: "up-shttp", RunID: strptr("run-http"),
				WorkspaceRef: strptr("ws-p1"), Title: strptr("http session"), ModelConfigRef: strptr("model-http"),
				CoreBuildID: strptr("core-build-w0302"), Protocol: domain.ClientSessionProtocol, ResumeExplicit: 1,
				LeaseExpiresAt: tmptr(now.Add(2 * time.Hour))}
			ttx, _ := hdb.BeginTx(ctx, nil)
			merr := domain.MapClientSession(ctx, ttx, tsession)
			ttx.Commit()
			ok("HTTP-SESSION-MAPPED", merr == nil, merr)
			cancelCmd := `{"protocol_version":"researchos-client/2","command_id":"http-cancel-1","client_id":"cli-http","project_id":"p1","session_id":"shttp","expected_revision":1,"writer_epoch":1,"method":"session.control","payload":{"action":"CANCEL","target_id":"run-http","reason":"user"}}`
			st2, body2 := post(cancelCmd, token)
			var wire2 map[string]any
			json.Unmarshal(body2, &wire2)
			status2 := ""
			if wire2 != nil {
				status2, _ = wire2["status"].(string)
			}
			ok("HTTP-CANCEL-ACKNOWLEDGED", st2 == 200 && status2 == "ACKNOWLEDGED", st2, string(body2))
			if wire2 != nil {
				verr2 := schemaDoc.ValidateDef("CommandResponse", wire2)
				ok("HTTP-CANCEL-TYPED", verr2 == nil, verr2)
			}
			var wmHTTP, revHTTP int64
			hdb.QueryRowContext(ctx, `SELECT event_watermark, revision FROM client_sessions WHERE id='shttp'`).Scan(&wmHTTP, &revHTTP)
			ok("HTTP-CANCEL-JOURNALED-ONCE", wmHTTP == 1 && revHTTP == 2, wmHTTP, revHTTP)
			st3, body3 := post(cancelCmd, token)
			var wm3 int64
			hdb.QueryRowContext(ctx, `SELECT event_watermark FROM client_sessions WHERE id='shttp'`).Scan(&wm3)
			ok("HTTP-REPLAY-NO-SECOND-EFFECT", st3 == 200 && string(body3) == string(body2) && wm3 == wmHTTP, st3, wm3, wmHTTP)
			noGrant := `{"protocol_version":"researchos-client/2","command_id":"http-forbidden-1","client_id":"cli-http","project_id":"p2","session_id":"shttp","expected_revision":2,"writer_epoch":1,"method":"session.control","payload":{"action":"CANCEL","target_id":"run-http","reason":"x"}}`
			st4, body4 := post(noGrant, token)
			ok("HTTP-FORBIDDEN-403", st4 == 403 && bytes.Contains(body4, []byte("FORBIDDEN")), st4, string(body4))
			st5, body5 := post(cancelCmd, "")
			var rev5, wm5 int64
			hdb.QueryRowContext(ctx, `SELECT revision, event_watermark FROM client_sessions WHERE id='shttp'`).Scan(&rev5, &wm5)
			ok("HTTP-UNAUTHENTICATED-WRITE-NO-SIDE-EFFECT", st5 == 401 && bytes.Contains(body5, []byte("UNAUTHENTICATED")) && rev5 == revHTTP && wm5 == wmHTTP, st5, rev5, wm5)
			ok("CONTRACT-NEUTRALISED-PATTERNS-EXACTLY-1", schemaDoc.NeutralizedPatterns == 1, schemaDoc.NeutralizedPatterns)
			ok("HTTP-TRANSPORT-BOUNDED-RETRY", httpRetries <= 3, httpRetries)
		}
	}
}

func jsonGeneric(raw []byte) any {
	var v any
	json.Unmarshal(raw, &v)
	return v
}

func strptr(s string) *string { return &s }
func i64ptr(i int64) *int64   { return &i }
func tmptr(t time.Time) *time.Time {
	return &t
}

const fixtureSetSHA = "a796725fe23bb54f0e9d499a6d6f3f3ccba5db64c55e3e6509ba389024432127"
const schemaSHA = "8943fe363bcfda4a2c45231e54c266133ffccc8642c541724d93d2e56d3a9a9b"
const domainSchemaSHA = "b53d9e6eddfeed89d27ee65c378d8067ae8b0c46de2ba2a098856a7557df1c54"
