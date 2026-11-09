//go:build windows

package domain

import (
	"context"
	"database/sql"
	"strings"
	"testing"
	"time"
)

func confirmationFixture(t *testing.T) (*fixture, *RuntimeCoordinator, LocalRuntimeQualificationRequest, string) {
	t.Helper()
	f, client, candidate, assets := localSetupFixture(t)
	ctx := context.Background()
	prepared, e := f.s.PrepareClientRuntime(ctx, f.token, candidate, assets, client.Doc, client.ConfigurationAuthority)
	if e != nil {
		t.Fatal(e)
	}
	ids, tokens := map[string]string{}, map[string]string{}
	for _, role := range []string{"EXECUTOR", "SCHEDULER"} {
		ids[role], e = f.s.EnsureRuntimeSetupPrincipal(ctx, f.token, f.project, role)
		if e != nil {
			t.Fatal(e)
		}
		tokens[role], e = f.s.IssueCredential(ctx, ids[role], time.Minute)
		if e != nil {
			t.Fatal(e)
		}
	}
	c := &RuntimeCoordinator{service: f.s, config: RuntimeCoordinatorConfig{ClientSchema: client.Doc, ConfigurationAuthority: client.ConfigurationAuthority}, active: map[string]bool{}, startupComplete: true}
	if e = c.InstallPreparedRuntime(ctx, prepared, ids["EXECUTOR"], tokens["EXECUTOR"], tokens["SCHEDULER"], assets); e != nil {
		t.Fatal(e)
	}
	r, e := c.PreparedLocalQualification(ctx, f.token, candidate, 600)
	if e != nil {
		t.Fatal(e)
	}
	return f, c, r, ids["EXECUTOR"]
}

// A fresh, isolated confirmation row allows each invalid timestamp/binding to
// reach the transaction check without modifying any previously recorded row.
func isolatedConfirmation(t *testing.T, f *fixture, r LocalRuntimeQualificationRequest) LocalRuntimeQualificationRequest {
	t.Helper()
	r.RequestID = ID()
	_, e := f.db.Exec(`INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at) VALUES(?,?,'host:qualification-confirmation',?,?,200,?,'{}',?)`, f.owner, f.project, r.RequestID, Hash(r), Bytes(r), Now())
	if e != nil {
		t.Fatal(e)
	}
	return r
}

func TestManagedConfirmationBeginTransactionGates(t *testing.T) {
	for _, name := range []string{"expired", "future_issue", "long_ttl", "wrong_owner", "wrong_root", "wrong_host", "wrong_session_hash", "wrong_config_hash", "changed_session_revision", "changed_model", "changed_plan", "unregistered", "owner_revoked"} {
		t.Run(name, func(t *testing.T) {
			f, c, r, executor := confirmationFixture(t)
			ctx := context.Background()
			before := localSetupCensus(t, f)
			switch name {
			case "expired":
				r.IssuedAt = time.Now().Add(-2 * time.Minute).UTC().Format(time.RFC3339Nano)
				r.ExpiresAt = time.Now().Add(-time.Minute).UTC().Format(time.RFC3339Nano)
			case "future_issue":
				r.IssuedAt = time.Now().Add(time.Minute).UTC().Format(time.RFC3339Nano)
				r.ExpiresAt = time.Now().Add(2 * time.Minute).UTC().Format(time.RFC3339Nano)
			case "long_ttl":
				r.ExpiresAt = time.Now().Add(time.Hour).UTC().Format(time.RFC3339Nano)
			case "wrong_owner":
				r.OwnerPrincipal = "foreign-owner"
			case "wrong_root":
				r.OwnerRoot = "foreign-root"
			case "wrong_host":
				r.OwnerHost = "host-111111111111"
			case "wrong_session_hash":
				r.SessionHash = Digest([]byte("changed"))
			case "wrong_config_hash":
				r.ConfigurationHash = Digest([]byte("changed"))
			case "changed_session_revision":
				if _, e := f.db.Exec(`UPDATE client_sessions SET revision=revision+1 WHERE id=?`, r.SessionID); e != nil {
					t.Fatal(e)
				}
			case "changed_model":
				if _, e := f.db.Exec(`UPDATE client_sessions SET model_config_ref=NULL WHERE id=?`, r.SessionID); e != nil {
					t.Fatal(e)
				}
			case "changed_plan":
				r.PlanHash = Digest([]byte("changed"))
			case "unregistered":
				r.RequestID = ID()
			case "owner_revoked":
				if e := f.s.RevokePrincipal(ctx, f.owner); e != nil {
					t.Fatal(e)
				}
			}
			if name != "unregistered" {
				r = isolatedConfirmation(t, f, r)
			}
			// Bypass wrapper/preflight deliberately. Begin itself must reject atomically.
			if _, _, e := c.beginManagedLocalQualification(ctx, f.token, r, executor); e == nil {
				t.Fatal("invalid confirmation reached atomic Begin")
			}
			var consumed int
			if e := f.db.QueryRow(`SELECT count(*) FROM idempotency WHERE operation='host:managed-runtime-qualification'`).Scan(&consumed); e != nil || consumed != 0 {
				t.Fatalf("rejected request consumed: %d %v", consumed, e)
			}
			if localSetupCensus(t, f) != before {
				t.Fatal("rejected confirmation changed Run/effect/ledger activity")
			}
		})
	}
}

func TestManagedConfirmationClaimCrashAndStatus(t *testing.T) {
	f, c, r, executor := confirmationFixture(t)
	ctx := context.Background()
	run, lease, e := c.beginManagedLocalQualification(ctx, f.token, r, executor)
	if e != nil {
		t.Fatal(e)
	}
	if _, _, e = c.beginManagedLocalQualification(ctx, f.token, r, executor); e == nil {
		t.Fatal("claimed request replayed")
	}
	var body string
	f.db.QueryRow(`SELECT body FROM idempotency WHERE operation='host:managed-runtime-qualification' AND key=?`, r.RequestID).Scan(&body)
	if strings.Contains(body, lease) {
		t.Fatal("Run lease escaped into durable confirmation")
	}
	// Fresh coordinator instance simulates loss of all in-memory management state.
	restarted := &RuntimeCoordinator{service: f.s, config: c.config, active: map[string]bool{}, startupComplete: true}
	if fenced, e := restarted.managedQualificationUnsettled(ctx); e != nil || !fenced {
		t.Fatalf("claimed Run did not restore fence: %v", e)
	}
	if e = restarted.Scan(ctx); e != nil || restarted.ClientIntakeOpen() {
		t.Fatalf("restart escaped outstanding claim fence: %v", e)
	}
	status, e := restarted.LocalQualificationStatus(ctx, f.token, r.ProjectID, r.RequestID, Hash(r))
	if e != nil || status["state"] != "UNRESOLVED" || status["consumed"] != true {
		t.Fatalf("original claim status lost: %s %v", Bytes(status), e)
	}
	if e = c.BeginLocalQualificationWindow(ctx, ID()); e == nil {
		t.Fatal("outstanding Run admitted another qualification")
	}
	if e = c.EndLocalQualificationWindow(ctx); e == nil {
		t.Fatal("unsettled claim cleared dispatch fence")
	}
	// Explicit original UNKNOWN effect remains append-only; no money/ledger is
	// introduced by fencing or status reads, and no worker has been launched.
	effect := Object{"state": "UNKNOWN", "reason": "isolated crash after external preparation"}
	if _, e = f.db.Exec(`INSERT INTO resource_effects(project,run,effect_key,sequence,body) VALUES(?,?,?,1,?)`, f.project, run["id"], "source-test-unknown", Bytes(effect)); e != nil {
		t.Fatal(e)
	}
	if _, _, e = c.beginManagedLocalQualification(ctx, f.token, r, executor); e == nil {
		t.Fatal("UNKNOWN was replayed")
	}
	var current string
	f.db.QueryRow(`SELECT body FROM resource_effects WHERE effect_key='source-test-unknown'`).Scan(&current)
	if current != string(Bytes(effect)) {
		t.Fatal("UNKNOWN evidence rewritten")
	}
	t.Log("claim-only crash: original request consumed once; fresh coordinator fenced; original UNKNOWN retained; model calls=0")
}

func TestManagedQualificationFenceOtherReadyTask(t *testing.T) {
	c, _, r, _ := nativeNormalFixture(t, false)
	ctx := context.Background()
	f := r.f
	if f.read("tasks", Str(r.task, "id"))["status"] != "READY" {
		t.Fatal("real ordinary READY fixture missing")
	}
	if e := c.BeginLocalQualificationWindow(ctx, ID()); e != nil {
		t.Fatal(e)
	}
	if c.ClientIntakeOpen() {
		t.Fatal("session execution intake open during qualification")
	}
	before := localSetupCensus(t, f)
	for i := 0; i < 3; i++ {
		if e := c.Scan(ctx); e != nil {
			t.Fatal(e)
		}
	}
	if localSetupCensus(t, f) != before || f.read("tasks", Str(r.task, "id"))["status"] != "READY" {
		t.Fatal("other READY task dispatched during window")
	}
	if e := c.EndLocalQualificationWindow(ctx); e != nil {
		t.Fatal(e)
	}
	if !c.ClientIntakeOpen() {
		t.Fatal("settled window failed to restore original intake")
	}
	if e := c.Scan(ctx); e != nil {
		t.Fatal(e)
	}
	c.workers.Wait()
	if f.read("tasks", Str(r.task, "id"))["status"] != "EXECUTION_REPORTED" {
		t.Fatal("ordinary task not dispatchable after window")
	}
	t.Log("actual native fixture: other READY task unchanged during full window, starts only after explicit settlement; model calls=0")
}

func TestManagedQualificationOfflinePrepareDoesNotScan(t *testing.T) {
	f, c, r, _ := confirmationFixture(t)
	called := 0
	c.config.PrepareLocalRuntime = func(context.Context, *RuntimeCoordinator) error { called++; return nil }
	before := localSetupCensus(t, f)
	if e := c.PrepareLocalRuntimeOffline(context.Background()); e != nil || called != 1 || localSetupCensus(t, f) != before {
		t.Fatal("offline prepare invoked execution")
	}
	// Startup hold precedes the first ordinary Scan for legacy managed startup.
	c.config.ManagedStartupHold = true
	if e := c.Scan(context.Background()); e != nil || called != 1 {
		t.Fatal("startup qualification raced ordinary scan")
	}
	var row string
	if e := f.db.QueryRow(`SELECT body FROM idempotency WHERE operation='host:qualification-confirmation' AND key=?`, r.RequestID).Scan(&row); e != nil {
		t.Fatal(e)
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error { return localQualificationIdle(tx) })
}

func TestManagedQualificationRefusesForeignUnresolvedEffect(t *testing.T) {
	f, c, r, executor := confirmationFixture(t)
	ctx := context.Background()
	effect := Object{"state": "UNKNOWN", "reason": "original foreign route effect retained"}
	if _, e := f.db.Exec(`INSERT INTO resource_effects(project,run,effect_key,sequence,body) VALUES(?,?,?,1,?)`, f.project, ID(), "foreign-original-effect", Bytes(effect)); e != nil {
		t.Fatal(e)
	}
	before := localSetupCensus(t, f)
	if e := c.BeginLocalQualificationWindow(ctx, r.RequestID); e == nil {
		t.Fatal("global UNKNOWN effect escaped via idle selected executor")
	}
	if _, _, e := c.beginManagedLocalQualification(ctx, f.token, r, executor); e == nil {
		t.Fatal("atomic Begin ignored foreign unresolved effect")
	}
	if localSetupCensus(t, f) != before {
		t.Fatal("busy refusal changed original effect or added a Run")
	}
	var original string
	f.db.QueryRow(`SELECT body FROM resource_effects WHERE effect_key='foreign-original-effect'`).Scan(&original)
	if original != string(Bytes(effect)) {
		t.Fatal("UNKNOWN was reinterpreted or rewritten")
	}
}
