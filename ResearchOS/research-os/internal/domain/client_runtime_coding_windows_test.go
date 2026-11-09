//go:build windows

package domain

import (
	"context"
	"database/sql"
	"testing"
	"time"
)

func codingFixture(t *testing.T) (*fixture, *RuntimeCoordinator, RuntimeSetupCandidate, RuntimeCodingIntent, RuntimeCodingFreezer) {
	t.Helper()
	f, c, r, _ := confirmationFixture(t)
	ctx := context.Background()
	var workspace string
	if e := f.db.QueryRow(`SELECT workspace_ref FROM client_sessions WHERE id=?`, r.SessionID).Scan(&workspace); e != nil {
		t.Fatal(e)
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		b, e := f.s.binding(ctx, tx, workspace)
		if e != nil {
			return e
		}
		b.Access = "READ_WRITE"
		b.Revision++
		return f.s.putOpaque(ctx, tx, "", KindWorkspaceBinding, b.AuthorizedRef, b.record())
	})
	c.config.WorkspaceAuthority = clientWorkspaceAuthority{}
	in := RuntimeCodingIntent{ClientID: "local-setup-client", ExpectedRevision: 2, WriterEpoch: 1, ConfigRevision: 3, WorkspaceRef: workspace, ReadPaths: []string{"go.mod", "pkg/main.go", "pkg/main_test.go"}, WritePaths: []string{"pkg/main.go"}, MaxReadBytes: 4096, MaxWriteBytes: 4096, MaxToolCalls: 16, MaxOutputTokens: 1024, Checks: []RuntimeCodingCheck{{ID: "selected", Package: "./pkg", TestPattern: "^TestSelected$", SourcePaths: []string{"go.mod", "pkg/main.go", "pkg/main_test.go"}, ToolchainRoot: "C:/fixture-go", TimeoutSeconds: 30, ProcessLimit: 8, MemoryMiB: 512, MaxTextBytes: 2048}}}
	freeze := func(context.Context, WorkspaceBinding, RuntimeCodingIntent) (Object, error) {
		return Decode(Bytes(Object{"tool_policy": Object{"max_calls": in.MaxToolCalls, "read_paths": in.ReadPaths, "write_paths": in.WritePaths, "max_read_bytes": in.MaxReadBytes, "max_write_bytes": in.MaxWriteBytes, "checks": []any{Object{"id": "selected"}}}, "check_summaries": []any{Object{"id": "selected", "source_count": 3}}, "initial_read_manifest_hash": Digest([]byte("fixture"))}))
	}
	return f, c, RuntimeSetupCandidate{ProjectID: f.project, SessionID: r.SessionID, PrincipalID: f.owner, ModelRef: r.ModelRef}, in, freeze
}
func TestProductCodingAtomicConfigurationAndScope(t *testing.T) {
	f, c, candidate, in, freeze := codingFixture(t)
	ctx := context.Background()
	before := localSetupCensus(t, f)
	prepared, e := c.PrepareRuntimeCoding(ctx, f.token, "parent", candidate, in, freeze)
	if e != nil {
		t.Fatal(e)
	}
	if localSetupCensus(t, f) != before {
		t.Fatal("prepare altered business activity")
	}
	result, e := c.ConfirmRuntimeCoding(ctx, f.token, "parent", f.project, Str(prepared, "request_id"), Str(prepared, "request_hash"), freeze)
	if e != nil {
		t.Fatal(e)
	}
	newRef := Str(result, "model_config_ref")
	if newRef == candidate.ModelRef || newRef == "" {
		t.Fatal("missing fresh config")
	}
	tx, e := f.db.BeginTx(ctx, nil)
	if e != nil {
		t.Fatal(e)
	}
	runtime, e := load(tx, f.project, "RuntimeRegistration", Str(result, "runtime_id"))
	if e != nil {
		t.Fatal(e)
	}
	_, artifact, e := c.service.currentRuntimeBinding(tx, f.project, runtime)
	if e != nil {
		t.Fatal(e)
	}
	profile, e := runtimeProfileBody(tx, f.project, artifact)
	if e != nil {
		tx.Rollback()
		t.Fatal(e)
	}
	if e = validateLocalQualificationProfile(profile); e != nil {
		tx.Rollback()
		t.Fatal(e)
	}
	config := profile["model_config"].(map[string]any)
	calls, _ := Num(config, "max_calls")
	q := profile["model_qualification"].(map[string]any)
	if calls != 8 || len(Arr(config, "tools")) != 4 || q["model_config_hash"] != Hash(config) {
		t.Fatal("coding or qualifier limits changed")
	}
	if e = c.validateCodingWorkspace(ctx, tx, f.owner, f.project, candidate.SessionID, in.WorkspaceRef, profile); e != nil {
		t.Fatal(e)
	}
	if e = c.validateCodingWorkspace(ctx, tx, f.owner, f.project, "foreign-session", in.WorkspaceRef, profile); e == nil {
		t.Fatal("coding authority transferred session")
	}
	if e = c.validateCodingWorkspace(ctx, tx, f.owner, f.project, candidate.SessionID, "foreign-workspace", profile); e == nil {
		t.Fatal("coding authority transferred workspace")
	}
	tx.Rollback()
	var activity int
	if e = f.db.QueryRow(`SELECT (SELECT count(*) FROM runtime_dispatches)+(SELECT count(*) FROM resource_effects)+(SELECT count(*) FROM domain_objects WHERE kind IN ('Run','AcceptanceReceipt','BudgetLedgerEntry'))`).Scan(&activity); e != nil || activity != 0 {
		t.Fatalf("offline activity %d %v", activity, e)
	}
	installed := localSetupCensus(t, f)
	if _, e = c.ConfirmRuntimeCoding(ctx, f.token, "parent", f.project, Str(prepared, "request_id"), Str(prepared, "request_hash"), freeze); e == nil {
		t.Fatal("confirmation replayed")
	}
	if localSetupCensus(t, f) != installed {
		t.Fatal("replay mutated state")
	}
	status, e := c.RuntimeCodingStatus(ctx, f.token, "parent", f.project, Str(prepared, "request_id"), Str(prepared, "request_hash"))
	if e != nil || Hash(status) != Hash(result) {
		t.Fatalf("status %v %v", status, e)
	}
}
func TestProductCodingConfirmationRefusals(t *testing.T) {
	for _, name := range []string{"parent", "expired", "writer", "config_head", "workspace_readonly", "source_drift", "owner_revoked", "rollback_profile"} {
		t.Run(name, func(t *testing.T) {
			f, c, candidate, in, freeze := codingFixture(t)
			ctx := context.Background()
			prepared, e := c.PrepareRuntimeCoding(ctx, f.token, "parent", candidate, in, freeze)
			if e != nil {
				t.Fatal(e)
			}
			parent := "parent"
			id, digest := Str(prepared, "request_id"), Str(prepared, "request_hash")
			switch name {
			case "parent":
				parent = "different"
			case "expired":
				tx, _ := f.db.BeginTx(ctx, nil)
				r, err := c.loadCodingConfirmation(ctx, tx, f.token, f.project, id, digest)
				tx.Rollback()
				if err != nil {
					t.Fatal(err)
				}
				r.RequestID = ID()
				r.IssuedAt = time.Now().Add(-2 * time.Minute).UTC().Format(time.RFC3339Nano)
				r.ExpiresAt = time.Now().Add(-time.Minute).UTC().Format(time.RFC3339Nano)
				id, digest = r.RequestID, Hash(r)
				if _, e = f.db.Exec(`INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at) VALUES(?,?,'host:coding-confirmation',?,?,200,?,'{}',?)`, f.owner, f.project, id, digest, Bytes(r), Now()); e != nil {
					t.Fatal(e)
				}
			case "writer":
				_, e = f.db.Exec(`UPDATE client_sessions SET writer_epoch=writer_epoch+1 WHERE id=?`, candidate.SessionID)
			case "config_head":
				client := &ClientService{Domain: f.s, Doc: c.config.ClientSchema, ConfigurationAuthority: c.config.ConfigurationAuthority}
				reply, _ := handlerCommand(t, f, client, &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: &in.ClientID, Method: strptr("host.configure"), Payload: Bytes(Object{"config_revision": 3, "provider_id": "ollama", "base_url": "http://127.0.0.1:1/v1", "model_id": "different", "credential_ref": nil})})
				if deref(reply.Status) != "COMPLETED" {
					t.Fatal("fixture config change refused")
				}
			case "workspace_readonly":
				sourceTx(t, f.db, func(tx *sql.Tx) error {
					b, e := f.s.binding(ctx, tx, in.WorkspaceRef)
					if e != nil {
						return e
					}
					b.Access = "READ_ONLY"
					b.Revision++
					return f.s.putOpaque(ctx, tx, "", KindWorkspaceBinding, b.AuthorizedRef, b.record())
				})
			case "source_drift":
				old := freeze
				freeze = func(ctx context.Context, b WorkspaceBinding, i RuntimeCodingIntent) (Object, error) {
					v, e := old(ctx, b, i)
					v["initial_read_manifest_hash"] = Digest([]byte("drift"))
					return v, e
				}
			case "owner_revoked":
				e = f.s.RevokePrincipal(ctx, f.owner)
			case "rollback_profile":
				_, e = f.db.Exec(`CREATE TRIGGER coding_profile_reject BEFORE INSERT ON domain_objects WHEN NEW.kind='Artifact' BEGIN SELECT RAISE(ABORT,'fixture profile rejected'); END`)
			}
			if e != nil {
				t.Fatal(e)
			}
			before := localSetupCensus(t, f)
			var head int64
			f.db.QueryRow(`SELECT current_revision FROM host_model_config_heads`).Scan(&head)
			if _, e = c.ConfirmRuntimeCoding(ctx, f.token, parent, f.project, id, digest, freeze); e == nil {
				t.Fatal("invalid coding confirmation admitted")
			}
			if localSetupCensus(t, f) != before {
				t.Fatal("failed install left business state")
			}
			var after int64
			f.db.QueryRow(`SELECT current_revision FROM host_model_config_heads`).Scan(&after)
			if after != head {
				t.Fatal("failed installation advanced configuration")
			}
			var count int
			f.db.QueryRow(`SELECT count(*) FROM idempotency WHERE operation IN ('host:coding-installation','host:coding-authorization')`).Scan(&count)
			if count != 0 {
				t.Fatal("failed installation persisted authority")
			}
		})
	}
}
