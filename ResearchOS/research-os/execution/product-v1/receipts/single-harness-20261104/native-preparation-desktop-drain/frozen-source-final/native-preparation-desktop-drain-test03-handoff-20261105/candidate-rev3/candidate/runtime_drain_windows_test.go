//go:build windows

package domain

import (
	"context"
	"database/sql"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	rt "researchos.local/research-os/adapters/runtime"
)

func TestRuntimeDrainLeaseAndScanFence(t *testing.T) {
	f := setup(t)
	var seq int
	var name, path string
	if e := f.db.QueryRow("PRAGMA database_list").Scan(&seq, &name, &path); e != nil {
		t.Fatal(e)
	}
	root := filepath.Dir(path)
	lease, e := rt.AcquireDataRootLease(root)
	if e != nil {
		t.Fatal(e)
	}
	defer lease.Close()
	config := RuntimeCoordinatorConfig{DataRoot: root, APIURL: "http://127.0.0.1:1"}
	bad := config
	bad.Routes = []RuntimeCoordinatorRoute{{CommandID: "fixture", Executable: "relative.exe"}}
	if _, e = f.s.NewRuntimeCoordinatorWithLease(context.Background(), bad, lease); e == nil {
		t.Fatal("invalid constructor accepted")
	}
	c, e := f.s.NewRuntimeCoordinatorWithLease(context.Background(), config, lease)
	if e != nil {
		t.Fatalf("failed constructor retained borrow: %v", e)
	}
	if _, e = f.s.NewRuntimeCoordinatorWithLease(context.Background(), config, lease); e == nil {
		t.Fatal("second coordinator borrowed same lease")
	}
	if e = lease.Close(); e == nil {
		t.Fatal("owner closed lease while coordinator borrowed")
	}
	c.scanMu.Lock()
	result := make(chan error, 1)
	go func() { _, err := c.QuiesceForRelease(context.Background()); result <- err }()
	select {
	case err := <-result:
		if err == nil {
			t.Fatal("busy scan quiesced")
		}
	case <-time.After(200 * time.Millisecond):
		c.scanMu.Unlock()
		t.Fatal("quiesce waited for scan mutex")
	}
	c.scanMu.Unlock()
	if _, e = c.QuiesceForRelease(context.Background()); e == nil || c.quiesced {
		t.Fatal("startup recovery was not complete but drain installed a fence")
	}
	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan error, 1)
	go func() { done <- c.Serve(ctx, nil) }()
	defer cancel()
	deadline := time.Now().Add(time.Second)
	for !c.StartupReady() && time.Now().Before(deadline) {
		time.Sleep(time.Millisecond)
	}
	if !c.StartupReady() {
		t.Fatal("busy pre-start drain stopped normal recovery")
	}
	if _, e = c.QuiesceForRelease(context.Background()); e != nil {
		t.Fatal(e)
	}
	if !c.quiesced {
		t.Fatal("scan fence missing")
	}
	c.ResumeAfterReleaseAbort()
	if c.quiesced {
		t.Fatal("abort failed to resume scans")
	}
	select {
	case err := <-done:
		t.Fatalf("busy/abort stopped coordinator: %v", err)
	default:
	}
	cancel()
	if e = <-done; e != nil {
		t.Fatal(e)
	}
	if e = c.Close(); e != nil {
		t.Fatal(e)
	}
	if l, e := rt.AcquireDataRootLease(root); e == nil {
		l.Close()
		t.Fatal("coordinator Close released owner OS lock before database close")
	}
	if e = f.db.Close(); e != nil {
		t.Fatal(e)
	}
	if e = lease.Close(); e != nil {
		t.Fatal(e)
	}
	l, e := rt.AcquireDataRootLease(root)
	if e != nil {
		t.Fatal("lease remained after DB and owner close", e)
	}
	l.Close()
	t.Log("single borrower; busy scan/startup drain refusal; recovery completes before quiesce; abort keeps Serve alive; coordinator close retains DB owner lock")
}

func TestDesktopExitStoppedNativePreparationKeepsConsumedHistory(t *testing.T) {
	f, c, fence, proof := harnessPreparationFixture(t)
	initial, _ := harnessPreparationLedger(t, f, fence)
	if len(initial) != 1 {
		t.Fatal("original local hold missing", initial)
	}
	originalHold := Bytes(initial[0])
	if err := c.finishHarnessPreparationFailure(fence, proof); err != nil {
		t.Fatal(err)
	}
	harnessPreparationReleased(t, f, fence, originalHold)
	c.startupComplete = true // The disposable fixture has no Serve loop.
	ctx := context.Background()
	before, err := f.s.RuntimeDrainSnapshot(ctx)
	if err != nil || before.UnresolvedDispatches != 1 || before.ActiveRuns != 0 || before.Reservations != 0 {
		t.Fatalf("expected one terminal consumed dispatch: %+v %v", before, err)
	}
	if raw, err := c.QuiesceForRelease(ctx); err == nil || raw.UnresolvedDispatches != 1 {
		t.Fatalf("generic release accepted consumed STARTED: %+v %v", raw, err)
	}
	got, err := c.QuiesceForDesktopExit(ctx)
	if err != nil || got.UnresolvedDispatches != 1 || !c.quiesced || c.ClientIntakeOpen() {
		t.Fatalf("Desktop exit rejected stopped original: %+v %v", got, err)
	}
	var state, reason string
	if err = f.db.QueryRow("SELECT state,reason FROM runtime_dispatches WHERE project=? AND run=? AND epoch=?", f.project, fence.runID, fence.epoch).Scan(&state, &reason); err != nil {
		t.Fatal(err)
	}
	if state != "STARTED" || reason == "" {
		t.Fatal("Desktop exit changed consumed dispatch", state, reason)
	}
	c.ResumeAfterReleaseAbort()
	if err = c.finishHarnessPreparationFailure(fence, proof); err != nil {
		t.Fatal("identical settlement lost idempotence", err)
	}
	var audits, failures int
	if err = f.db.QueryRow("SELECT count(*) FROM uploaded_content WHERE sealed=1 AND CAST(bytes AS TEXT) LIKE '%researchos.native-preparation-outcome.v1%'").Scan(&audits); err != nil {
		t.Fatal(err)
	}
	if err = f.db.QueryRow("SELECT coalesce(sum(count),0) FROM orchestration_failures WHERE project=? AND reason_hash=?", f.project, Digest([]byte("native preparation failed before model launch"))).Scan(&failures); err != nil {
		t.Fatal(err)
	}
	if audits != 1 || failures != 1 {
		t.Fatal("Desktop exit duplicated settlement", audits, failures)
	}
	harnessPreparationReleased(t, f, fence, originalHold)
}

// A fixture can deliberately rewrite privileged database facts to exercise
// validator boundaries. Ordinary API callers cannot write the C5 reason.
func desktopPreparationRewriteAudit(t *testing.T, f *fixture, fence harnessPreparationFence, change func(Object)) {
	t.Helper()
	var raw []byte
	var principal string
	if err := f.db.QueryRow("SELECT bytes,principal FROM uploaded_content WHERE project=? AND CAST(bytes AS TEXT) LIKE '%researchos.native-preparation-outcome.v1%'", f.project).Scan(&raw, &principal); err != nil {
		t.Fatal(err)
	}
	audit, err := Decode(raw)
	if err != nil {
		t.Fatal(err)
	}
	change(audit)
	raw = Bytes(audit)
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		if _, err := f.s.serverArtifactMode(tx, f.project, principal, "LOG", "LIVE", raw, Empty()); err != nil {
			return err
		}
		_, err := tx.Exec("UPDATE runtime_dispatches SET reason=? WHERE project=? AND run=? AND epoch=?", "native preparation failed before model launch: "+Str(audit, "reason")+"; proof="+Hash(audit), f.project, fence.runID, fence.epoch)
		return err
	})
}

func TestDesktopExitStoppedNativePreparationRejectsCounterevidence(t *testing.T) {
	cases := []struct {
		name   string
		mutate func(*testing.T, *fixture, *RuntimeCoordinator, harnessPreparationFence)
	}{
		{"unsealed_audit", func(t *testing.T, f *fixture, _ *RuntimeCoordinator, _ harnessPreparationFence) {
			var key string
			if err := f.db.QueryRow("SELECT storage_key FROM uploaded_content WHERE project=? AND CAST(bytes AS TEXT) LIKE '%researchos.native-preparation-outcome.v1%'", f.project).Scan(&key); err != nil {
				t.Fatal(err)
			}
			if _, err := f.db.Exec("UPDATE uploaded_content SET sealed=0 WHERE storage_key=?", key); err != nil {
				t.Fatal(err)
			}
		}},
		{"duplicate_audit", func(t *testing.T, f *fixture, _ *RuntimeCoordinator, _ harnessPreparationFence) {
			_, err := f.db.Exec("INSERT INTO uploaded_content(storage_key,project,principal,bytes,content_hash,expires_at,sealed) SELECT ?,project,principal,bytes,content_hash,expires_at,1 FROM uploaded_content WHERE project=? AND CAST(bytes AS TEXT) LIKE '%researchos.native-preparation-outcome.v1%'", ID(), f.project)
			if err != nil {
				t.Fatal(err)
			}
		}},
		{"wrong_audit_hash", func(t *testing.T, f *fixture, _ *RuntimeCoordinator, fence harnessPreparationFence) {
			_, err := f.db.Exec("UPDATE runtime_dispatches SET reason='native preparation failed before model launch: QUALIFICATION_POLICY_VIOLATION; proof=sha256:0000' WHERE project=? AND run=?", f.project, fence.runID)
			if err != nil {
				t.Fatal(err)
			}
		}},
		{"wrong_epoch", func(t *testing.T, f *fixture, _ *RuntimeCoordinator, fence harnessPreparationFence) {
			desktopPreparationRewriteAudit(t, f, fence, func(a Object) { a["epoch"] = "2" })
		}},
		{"wrong_run", func(t *testing.T, f *fixture, _ *RuntimeCoordinator, fence harnessPreparationFence) {
			desktopPreparationRewriteAudit(t, f, fence, func(a Object) { a["run_id"] = ID() })
		}},
		{"wrong_task", func(t *testing.T, f *fixture, _ *RuntimeCoordinator, fence harnessPreparationFence) {
			desktopPreparationRewriteAudit(t, f, fence, func(a Object) { a["task_id"] = ID() })
		}},
		{"wrong_source", func(t *testing.T, f *fixture, _ *RuntimeCoordinator, fence harnessPreparationFence) {
			desktopPreparationRewriteAudit(t, f, fence, func(a Object) { a["source_binding_hash"] = Digest([]byte("other")) })
		}},
		{"wrong_worker", func(t *testing.T, f *fixture, _ *RuntimeCoordinator, fence harnessPreparationFence) {
			desktopPreparationRewriteAudit(t, f, fence, func(a Object) { a["worker"] = ID() })
		}},
		{"wrong_manifest", func(t *testing.T, f *fixture, _ *RuntimeCoordinator, fence harnessPreparationFence) {
			desktopPreparationRewriteAudit(t, f, fence, func(a Object) { a["manifest_hash"] = Digest([]byte("other")) })
		}},
		{"wrong_project_in_audit", func(t *testing.T, f *fixture, _ *RuntimeCoordinator, fence harnessPreparationFence) {
			desktopPreparationRewriteAudit(t, f, fence, func(a Object) { a["project_id"] = ID() })
		}},
		{"wrong_same_project_uploader", func(t *testing.T, f *fixture, _ *RuntimeCoordinator, _ harnessPreparationFence) {
			var key, original, other string
			if err := f.db.QueryRow("SELECT storage_key,principal FROM uploaded_content WHERE project=? AND CAST(bytes AS TEXT) LIKE '%researchos.native-preparation-outcome.v1%'", f.project).Scan(&key, &original); err != nil {
				t.Fatal(err)
			}
			if err := f.db.QueryRow("SELECT principal FROM auth_grants WHERE project=? AND principal<>? LIMIT 1", f.project, original).Scan(&other); err != nil {
				t.Fatal(err)
			}
			if _, err := f.db.Exec("UPDATE uploaded_content SET principal=? WHERE storage_key=?", other, key); err != nil {
				t.Fatal(err)
			}
		}},
		{"delegate", func(t *testing.T, f *fixture, _ *RuntimeCoordinator, fence harnessPreparationFence) {
			desktopPreparationRewriteAudit(t, f, fence, func(a Object) { a["model_start_delegated"] = true })
		}},
		{"unknown_child", func(t *testing.T, f *fixture, _ *RuntimeCoordinator, fence harnessPreparationFence) {
			desktopPreparationRewriteAudit(t, f, fence, func(a Object) { a["qualification_no_child"] = false })
		}},
		{"incomplete_child", func(t *testing.T, f *fixture, _ *RuntimeCoordinator, fence harnessPreparationFence) {
			desktopPreparationRewriteAudit(t, f, fence, func(a Object) {
				a["qualification_no_child"] = false
				a["qualification_pid"] = 234
				a["streams_drained"] = false
			})
		}},
		{"model_identity", func(t *testing.T, f *fixture, _ *RuntimeCoordinator, fence harnessPreparationFence) {
			_, err := f.db.Exec("UPDATE runtime_dispatches SET identity='{\"pid\":1}' WHERE project=? AND run=?", f.project, fence.runID)
			if err != nil {
				t.Fatal(err)
			}
		}},
		{"external_observation", func(t *testing.T, f *fixture, _ *RuntimeCoordinator, fence harnessPreparationFence) {
			_, err := f.db.Exec("INSERT INTO runtime_observations(project,run,epoch,receipt_hash,body,observed_at) VALUES(?,?,?,?,?,?)", f.project, fence.runID, fence.epoch, Digest([]byte("inert observation")), `{}`, Now())
			if err != nil {
				t.Fatal(err)
			}
		}},
		{"confirmed_effect", func(t *testing.T, f *fixture, _ *RuntimeCoordinator, fence harnessPreparationFence) {
			_, err := f.db.Exec("INSERT INTO resource_effects(project,run,effect_key,sequence,body) VALUES(?,?,?,1,?)", f.project, fence.runID, ID(), `{"state":"CONFIRMED"}`)
			if err != nil {
				t.Fatal(err)
			}
		}},
		{"model_marker", func(t *testing.T, _ *fixture, c *RuntimeCoordinator, fence harnessPreparationFence) {
			path := filepath.Join(c.config.DataRoot, "runtime-dispatches", fence.locator)
			if err := os.MkdirAll(path, 0700); err != nil {
				t.Fatal(err)
			}
			if err := os.WriteFile(filepath.Join(path, "native-turn-authorization.json"), []byte("counterevidence"), 0600); err != nil {
				t.Fatal(err)
			}
		}},
		{"missing_marker_root", func(_ *testing.T, _ *fixture, c *RuntimeCoordinator, _ harnessPreparationFence) {
			c.config.DataRoot = filepath.Join(c.config.DataRoot, "missing-native-root")
		}},
		{"ordinary_started", func(t *testing.T, f *fixture, _ *RuntimeCoordinator, fence harnessPreparationFence) {
			_, err := f.db.Exec("UPDATE runtime_dispatches SET reason='' WHERE project=? AND run=?", f.project, fence.runID)
			if err != nil {
				t.Fatal(err)
			}
		}},
		{"unknown", func(t *testing.T, f *fixture, _ *RuntimeCoordinator, fence harnessPreparationFence) {
			_, err := f.db.Exec("UPDATE runtime_dispatches SET state='UNKNOWN' WHERE project=? AND run=?", f.project, fence.runID)
			if err != nil {
				t.Fatal(err)
			}
		}},
		{"active_worker", func(_ *testing.T, _ *fixture, c *RuntimeCoordinator, _ harnessPreparationFence) {
			c.active[ID()] = true
		}},
		{"second_unresolved_dispatch", func(t *testing.T, f *fixture, _ *RuntimeCoordinator, fence harnessPreparationFence) {
			_, err := f.db.Exec(`INSERT INTO runtime_dispatches(project,run,epoch,dispatch_key,manifest,manifest_hash,state,prepared_at,updated_at)
				SELECT project,run,epoch+1,?,manifest,manifest_hash,'PREPARED',?,? FROM runtime_dispatches WHERE project=? AND run=? AND epoch=?`, ID(), Now(), Now(), f.project, fence.runID, fence.epoch)
			if err != nil {
				t.Fatal(err)
			}
		}},
		{"reservation", func(t *testing.T, f *fixture, _ *RuntimeCoordinator, fence harnessPreparationFence) {
			ledger := Object{"id": ID(), "run_id": fence.runID, "provider_request_id": ID(), "operation": "RESERVE"}
			_, err := f.db.Exec("INSERT INTO domain_objects(project,kind,id,revision,body) VALUES(?,'BudgetLedgerEntry',?,1,?)", f.project, ledger["id"], Bytes(ledger))
			if err != nil {
				t.Fatal(err)
			}
		}},
		{"unresolved_command", func(t *testing.T, f *fixture, _ *RuntimeCoordinator, _ harnessPreparationFence) {
			_, err := f.db.Exec("INSERT INTO client_control_requests(principal,project,command_id,session_id,control_request_id,request_hash,target_id,task_ids,state,created_at) VALUES(?,?,?,?,?,?,?,'[]','REQUESTED',?)", f.owner, f.project, ID(), ID(), ID(), Digest([]byte("inert command")), ID(), Now())
			if err != nil {
				t.Fatal(err)
			}
		}},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			f, c, fence, proof := harnessPreparationFixture(t)
			if err := c.finishHarnessPreparationFailure(fence, proof); err != nil {
				t.Fatal(err)
			}
			c.startupComplete = true
			clean, err := c.QuiesceForDesktopExit(context.Background())
			if err != nil || clean.Reservations != 0 || clean.UnresolvedDispatches != 1 {
				t.Fatal("counterevidence fixture has no clean exit control", clean, err)
			}
			c.ResumeAfterReleaseAbort()
			tc.mutate(t, f, c, fence)
			_, err = c.QuiesceForDesktopExit(context.Background())
			if err == nil || c.quiesced {
				t.Fatal("Desktop exit accepted conflicting preparation", tc.name)
			}
			want := "original stopped native preparation proof"
			switch tc.name {
			case "ordinary_started", "unknown", "active_worker", "second_unresolved_dispatch", "unresolved_command":
				want = "runtime busy or external effect unresolved"
			case "reservation":
				want = "unknown ledger RESERVE"
			case "model_marker":
				want = "native turn marker"
			case "missing_marker_root":
				want = "native dispatch directory uncertain"
			}
			if !strings.Contains(err.Error(), want) {
				t.Fatalf("%s rejected for unrelated reason: %v", tc.name, err)
			}
		})
	}
}

// Disposable source fixture synthesizes durable record shapes; it makes no
// native acceptance claim. Actual Host/private-pipe coverage is separate.
func desktopExitFixture(t *testing.T) (*fixture, *RuntimeCoordinator, string, string) {
	t.Helper()
	f, c, r, executor := confirmationFixture(t)
	ctx := context.Background()
	run, _, e := c.beginManagedLocalQualification(ctx, f.token, r, executor)
	if e != nil {
		t.Fatal(e)
	}
	runID := Str(run, "id")
	key := r.TaskID + ":" + runID + ":1:model:1"
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		task, e := load(tx, f.project, "Task", r.TaskID)
		if e != nil {
			return e
		}
		dispatch, e := runtimeDispatch(tx, f.project, runID, 1)
		if e != nil {
			return e
		}
		manifest := dispatch["manifest"].(map[string]any)
		admission := manifest["admission"].(map[string]any)
		profile := admission["profile"].(map[string]any)
		config := profile["model_config"].(map[string]any)
		goal, e := load(tx, f.project, "Goal", Str(task, "goal_id"))
		if e != nil {
			return e
		}
		request := Object{"route": config["route"], "capability": "MODEL", "credential_revision": "none", "payload": Object{"body": Object{"model": config["model"], "stream": true, "max_tokens": 32, "messages": []any{Object{"role": "user", "content": "fixture"}}}}}
		cost := Object{"policy_id": goal["budget_policy_id"], "run_id": runID, "operation": "UNKNOWN", "money": nil, "provider_request_id": key, "provider_event_id": "prepare/" + key, "reservation_id": nil, "cost_basis": "UNKNOWN", "occurred_at": run["created_at"]}
		effect, e := c.service.prepareEffectTx(tx, c.schedulerCredential(f.project), f.project, runID, key, request, cost)
		if e != nil {
			return e
		}
		effect, e = c.service.beginEffectTx(tx, c.schedulerCredential(f.project), f.project, runID, key)
		if e != nil {
			return e
		}
		raw := []byte("data: {\"choices\":[{\"index\":0,\"delta\":{\"content\":\"fixture\"},\"finish_reason\":\"stop\"}]}\n\ndata: [DONE]\n\n")
		receipt := Object{"key": key, "epoch": 1, "run_id": runID, "receipt_id": Digest(raw), "state": "CONFIRMED", "model_transport": true, "actual_cost": nil, "payload": Object{"status": 200, "content_type": "text/event-stream", "body": string(raw)}}
		effect["state"], effect["receipt"] = "CONFIRMED", receipt
		if e = effectAppend(tx, f.project, runID, key, effect); e != nil {
			return e
		}
		identity := Object{"pid": 12345, "created": 123, "image": "fixture"}
		observation := Object{"state": "SETTLED", "children_stopped": true, "queue_empty": true, "streams_drained": true, "cleanup_complete": true, "ended": Now(), "dispatch_key": dispatch["dispatch_key"], "manifest_hash": dispatch["manifest_hash"], "worker": "fixture-worker", "identity": identity, "observation_sequence": 1, "spec": Object{"profile_hash": admission["profile_hash"], "run_id": runID, "task_id": task["id"], "epoch": 1}}
		if _, e = tx.Exec(`UPDATE runtime_dispatches SET state='OBSERVED',worker='fixture-worker',journal_locator=dispatch_key,identity=?,observation_sequence=1,observation_hash=? WHERE project=? AND run=?`, Bytes(identity), Hash(observation), f.project, runID); e != nil {
			return e
		}
		if _, e = tx.Exec(`INSERT INTO runtime_observations(project,run,epoch,receipt_hash,body,observed_at) VALUES(?,?,1,?,?,?)`, f.project, runID, Hash(observation), Bytes(observation), Now()); e != nil {
			return e
		}
		run["status"], run["children_stopped"], run["queue_empty"], run["ended_at"], run["runtime_settled_at"] = "SETTLED", true, true, Now(), Now()
		if e = bump(run); e != nil {
			return e
		}
		if e = f.s.put(tx, "Run", run); e != nil {
			return e
		}
		return f.s.releaseQualificationReservation(tx, f.project, run)
	})
	return f, c, runID, key
}
func TestDesktopExitCompletedLocalUnknownPreservesReleaseGate(t *testing.T) {
	f, c, _, _ := desktopExitFixture(t)
	ctx := context.Background()
	var before string
	f.db.QueryRow(`SELECT group_concat(body) FROM domain_objects WHERE kind='BudgetLedgerEntry'`).Scan(&before)
	strict, e := c.QuiesceForRelease(ctx)
	if e == nil || strict.Reservations != 1 {
		t.Fatalf("release did not retain unknown: %+v %v", strict, e)
	}
	if e = f.s.completedLocalUnknownCosts(ctx); e != nil {
		t.Fatal(e)
	}
	safe, e := c.QuiesceForDesktopExit(ctx)
	if e != nil || safe.Reservations != 1 || c.ClientIntakeOpen() {
		t.Fatalf("safe exit %+v %v", safe, e)
	}
	var after string
	f.db.QueryRow(`SELECT group_concat(body) FROM domain_objects WHERE kind='BudgetLedgerEntry'`).Scan(&after)
	if before != after {
		t.Fatal("UNKNOWN rewritten by exit")
	}
	c.ResumeAfterReleaseAbort()
	if !c.ClientIntakeOpen() {
		t.Fatal("ordinary abort did not restore intake")
	}
}
func TestDesktopExitUnknownIncompleteRefused(t *testing.T) {
	for _, name := range []string{"paid_capability", "credential", "request_hash", "receipt_hash", "effect_unknown", "active_run", "queue_not_empty", "missing_observation", "missing_identity", "reservation", "budget_changed", "active_qualification"} {
		t.Run(name, func(t *testing.T) {
			f, c, run, key := desktopExitFixture(t)
			ctx := context.Background()
			sourceTx(t, f.db, func(tx *sql.Tx) error {
				switch name {
				case "missing_observation":
					_, e := tx.Exec(`UPDATE runtime_dispatches SET observation_hash='missing' WHERE run=?`, run)
					return e
				case "missing_identity":
					_, e := tx.Exec(`UPDATE runtime_dispatches SET identity='{}' WHERE run=?`, run)
					return e
				case "active_qualification":
					c.qualificationActive = true
					return nil
				case "active_run", "queue_not_empty":
					r, e := load(tx, f.project, "Run", run)
					if e != nil {
						return e
					}
					if name == "active_run" {
						r["status"] = "RUNNING"
					} else {
						r["queue_empty"] = false
					}
					if e = bump(r); e != nil {
						return e
					}
					return f.s.put(tx, "Run", r)
				case "budget_changed":
					r, e := load(tx, f.project, "Run", run)
					if e != nil {
						return e
					}
					task, e := load(tx, f.project, "Task", Str(r, "task_id"))
					if e != nil {
						return e
					}
					goal, e := load(tx, f.project, "Goal", Str(task, "goal_id"))
					if e != nil {
						return e
					}
					policy, e := load(tx, f.project, "BudgetPolicy", Str(goal, "budget_policy_id"))
					if e != nil {
						return e
					}
					policy["updated_at"] = "2026-10-12T01:02:03Z"
					if e = bump(policy); e != nil {
						return e
					}
					return f.s.put(tx, "BudgetPolicy", policy)
				case "reservation":
					effect, e := latestEffect(tx, f.project, run, key)
					if e != nil {
						return e
					}
					ledger, e := load(tx, f.project, "BudgetLedgerEntry", Str(effect, "reservation_id"))
					if e != nil {
						return e
					}
					ledger["id"], ledger["operation"], ledger["cost_basis"], ledger["money"], ledger["provider_event_id"] = ID(), "RESERVE", "UPPER_BOUND", dollars("0"), "extra-reserve"
					ledger["receipt_hash"] = Receipt(ledger)
					return f.s.put(tx, "BudgetLedgerEntry", ledger)
				default:
					effect, e := latestEffect(tx, f.project, run, key)
					if e != nil {
						return e
					}
					request := effect["payload"].(map[string]any)
					switch name {
					case "paid_capability":
						request["capability"] = "SOURCE"
					case "credential":
						request["credential_revision"] = "paid-key"
					case "request_hash":
						effect["request_hash"] = "changed"
					case "receipt_hash":
						effect["receipt"].(map[string]any)["receipt_id"] = "changed"
					case "effect_unknown":
						effect["state"] = "UNKNOWN"
					}
					return effectAppend(tx, f.project, run, key, effect)
				}
			})
			c.intakeClosed.Store(true)
			var before string
			f.db.QueryRow(`SELECT group_concat(body) FROM domain_objects WHERE kind='BudgetLedgerEntry'`).Scan(&before)
			if _, e := c.QuiesceForDesktopExit(ctx); e == nil {
				t.Fatal("incomplete/paid/reserved cost escaped exit fence")
			}
			if c.ClientIntakeOpen() {
				t.Fatal("failed exit removed original closure")
			}
			var after string
			f.db.QueryRow(`SELECT group_concat(body) FROM domain_objects WHERE kind='BudgetLedgerEntry'`).Scan(&after)
			if before != after {
				t.Fatal("failed exit changed money")
			}
		})
	}
}
