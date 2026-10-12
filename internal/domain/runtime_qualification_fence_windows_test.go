//go:build windows

package domain

import (
	"context"
	"path/filepath"
	"testing"
	"time"

	rt "researchos.local/research-os/adapters/runtime"
)

func qualificationFenceConfig(t *testing.T, f *fixture, c *RuntimeCoordinator) RuntimeCoordinatorConfig {
	t.Helper()
	var seq int
	var name, path string
	if e := f.db.QueryRow("PRAGMA database_list").Scan(&seq, &name, &path); e != nil {
		t.Fatal(e)
	}
	config := c.config
	config.DataRoot, config.APIURL = filepath.Dir(path), "http://127.0.0.1:1"
	return config
}

// Exercise the real V2 session mutation transaction, not just the atomic flag.
func requireQualificationSessionFence(t *testing.T, f *fixture, c *RuntimeCoordinator, r LocalRuntimeQualificationRequest) {
	t.Helper()
	var revision, epoch int64
	if e := f.db.QueryRow(`SELECT revision,writer_epoch FROM client_sessions WHERE id=?`, r.SessionID).Scan(&revision, &epoch); e != nil {
		t.Fatal(e)
	}
	var before, after int
	if e := f.db.QueryRow(`SELECT count(*) FROM client_sessions`).Scan(&before); e != nil {
		t.Fatal(e)
	}
	svc := &ClientService{Doc: c.config.ClientSchema, Domain: f.s, SessionRuntime: c, ConfigurationAuthority: c.config.ConfigurationAuthority, Host: ClientHostInfo{CoreBuildID: "managed-fence-repair-fixture", LeaseTTL: time.Minute}}
	reply, _ := handlerCommand(t, f, svc, &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("local-setup-client"), ProjectID: &f.project, SessionID: &r.SessionID, ExpectedRevision: &revision, WriterEpoch: &epoch, Method: strptr("session.send"), Payload: Bytes(Object{"text": "must stay fenced", "attachment_artifact_ids": Empty(), "delivery": "NORMAL"})})
	if deref(reply.Status) != "REJECTED" || deref(reply.ErrorCode) != "RESOURCE_BLOCKED" {
		t.Fatalf("real session admission escaped fence: %s", Bytes(reply))
	}
	if e := f.db.QueryRow(`SELECT count(*) FROM client_sessions`).Scan(&after); e != nil || after != before {
		t.Fatalf("refused admission changed sessions: %d -> %d %v", before, after, e)
	}
	var currentRevision, currentEpoch int64
	if e := f.db.QueryRow(`SELECT revision,writer_epoch FROM client_sessions WHERE id=?`, r.SessionID).Scan(&currentRevision, &currentEpoch); e != nil || currentRevision != revision || currentEpoch != epoch {
		t.Fatalf("refused admission changed original session revision/writer: %v", e)
	}
}

func TestManagedFenceRefusedDrainAndAbort(t *testing.T) {
	for _, mode := range []string{"active_unsettled", "durable_only", "startup_hold", "active_idle_abort", "prior_closed_abort"} {
		t.Run(mode, func(t *testing.T) {
			f, c, r, executor := confirmationFixture(t)
			ctx := context.Background()
			switch mode {
			case "active_unsettled", "active_idle_abort":
				if e := c.BeginLocalQualificationWindow(ctx, r.RequestID); e != nil {
					t.Fatal(e)
				}
			case "startup_hold":
				c.config.ManagedStartupHold = true
				c.intakeClosed.Store(true)
			case "prior_closed_abort":
				c.intakeClosed.Store(true)
			}
			if mode == "active_unsettled" || mode == "durable_only" {
				if _, _, e := c.beginManagedLocalQualification(ctx, f.token, r, executor); e != nil {
					t.Fatal(e)
				}
			}
			before := localSetupCensus(t, f)
			_, err := c.QuiesceForRelease(ctx)
			if (mode == "active_unsettled" || mode == "durable_only") && err == nil {
				t.Fatal("unsettled Run allowed release")
			}
			if err != nil && mode != "active_unsettled" && mode != "durable_only" {
				t.Fatal(err)
			}
			requireQualificationSessionFence(t, f, c, r)
			c.ResumeAfterReleaseAbort()
			requireQualificationSessionFence(t, f, c, r)
			if e := c.Scan(ctx); e != nil {
				t.Fatal(e)
			}
			requireQualificationSessionFence(t, f, c, r)
			if localSetupCensus(t, f) != before {
				t.Fatal("drain/abort/Scan changed original domain/effect counters")
			}
		})
	}
}

func TestManagedFenceConstructorBeforeAdmission(t *testing.T) {
	for _, mode := range []string{"durable_unsettled", "durable_unknown", "startup_hold", "normal_open"} {
		t.Run(mode, func(t *testing.T) {
			f, c, r, executor := confirmationFixture(t)
			ctx := context.Background()
			config := qualificationFenceConfig(t, f, c)
			if mode == "durable_unsettled" || mode == "durable_unknown" {
				run, _, e := c.beginManagedLocalQualification(ctx, f.token, r, executor)
				if e != nil {
					t.Fatal(e)
				}
				if mode == "durable_unknown" {
					if _, e = f.db.Exec(`INSERT INTO resource_effects(project,run,effect_key,sequence,body) VALUES(?,?,?,1,?)`, f.project, run["id"], "constructor-original-unknown", Bytes(Object{"state": "UNKNOWN"})); e != nil {
						t.Fatal(e)
					}
				}
			}
			config.ManagedStartupHold = mode == "startup_hold"
			before := localSetupCensus(t, f)
			restarted, e := f.s.NewRuntimeCoordinator(ctx, config)
			if e != nil {
				t.Fatal(e)
			}
			defer restarted.Close()
			if mode == "normal_open" {
				if !restarted.ClientIntakeOpen() {
					t.Fatal("normal startup changed intake semantics")
				}
				restarted.startupComplete = true
				if _, e = restarted.QuiesceForRelease(ctx); e != nil {
					t.Fatal(e)
				}
				restarted.ResumeAfterReleaseAbort()
				if !restarted.ClientIntakeOpen() {
					t.Fatal("normal release abort failed to restore prior open intake")
				}
				return
			}
			requireQualificationSessionFence(t, f, restarted, r)
			if e = restarted.Scan(ctx); e != nil {
				t.Fatal(e)
			}
			requireQualificationSessionFence(t, f, restarted, r)
			restarted.ResumeAfterReleaseAbort()
			requireQualificationSessionFence(t, f, restarted, r)
			if _, e = f.s.NewRuntimeCoordinator(ctx, config); e == nil {
				t.Fatal("second coordinator acquired original data-root lease")
			}
			if localSetupCensus(t, f) != before {
				t.Fatal("constructor/Scan/abort altered durable original evidence")
			}
		})
	}
}

func TestManagedFenceObservationAndRecoveryErrors(t *testing.T) {
	for _, mode := range []string{"drain", "scan", "begin_recovery", "serve_recovery"} {
		t.Run(mode, func(t *testing.T) {
			_, c, _, _ := confirmationFixture(t)
			ctx, cancel := context.WithCancel(context.Background())
			cancel()
			var err error
			switch mode {
			case "drain":
				_, err = c.QuiesceForRelease(ctx)
			case "scan":
				err = c.Scan(ctx)
			case "begin_recovery":
				c.startupComplete = false
				err = c.BeginLocalQualificationWindow(ctx, ID())
			case "serve_recovery":
				c.startupComplete = false
				err = c.Serve(ctx, nil)
			}
			if err == nil || c.ClientIntakeOpen() {
				t.Fatalf("observation/recovery failure exposed intake: %v", err)
			}
			c.ResumeAfterReleaseAbort()
			if c.ClientIntakeOpen() {
				t.Fatal("abort erased unknown failure fence")
			}
		})
	}
}

func TestManagedFenceConstructorObservationFailureReturnsLease(t *testing.T) {
	f, c, _, _ := confirmationFixture(t)
	config := qualificationFenceConfig(t, f, c)
	lease, e := rt.AcquireDataRootLease(config.DataRoot)
	if e != nil {
		t.Fatal(e)
	}
	defer lease.Close()
	// Isolated schema fault reaches the durable observation after lease borrow.
	if _, e = f.db.Exec(`ALTER TABLE idempotency RENAME TO isolated_unreadable_idempotency`); e != nil {
		t.Fatal(e)
	}
	if returned, err := f.s.NewRuntimeCoordinatorWithLease(context.Background(), config, lease); err == nil || returned != nil {
		t.Fatal("failed durable observation published coordinator")
	}
	if _, e = f.db.Exec(`ALTER TABLE isolated_unreadable_idempotency RENAME TO idempotency`); e != nil {
		t.Fatal(e)
	}
	restored, e := f.s.NewRuntimeCoordinatorWithLease(context.Background(), config, lease)
	if e != nil {
		t.Fatalf("failed constructor leaked original lease borrow: %v", e)
	}
	if !restored.ClientIntakeOpen() {
		t.Fatal("healthy normal reconstruction remained closed")
	}
	if e = restored.Close(); e != nil {
		t.Fatal(e)
	}
}
