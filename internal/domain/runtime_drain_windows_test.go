//go:build windows

package domain

import (
	"context"
	"database/sql"
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

// Disposable source fixture synthesizes durable record shapes; it makes no
// native acceptance claim. Actual Host/private-pipe coverage is separate.
func desktopExitFixture(t *testing.T) (*fixture, *RuntimeCoordinator, string, string) {
	return desktopExitFixtureTools(t, false)
}
func desktopExitFixtureTools(t *testing.T, oldTools bool) (*fixture, *RuntimeCoordinator, string, string) {
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
		if oldTools {
			request["payload"].(map[string]any)["body"].(map[string]any)["tools"] = []any{Object{"type": "function", "function": Object{"name": "run_check", "parameters": Object{"type": "object"}}}}
		}
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

func TestQualificationProjectionUnknownCostRejectsOldTools(t *testing.T) {
	f, _, _, _ := desktopExitFixtureTools(t, true)
	var before string
	if err := f.db.QueryRow(`SELECT group_concat(body) FROM domain_objects WHERE kind='BudgetLedgerEntry'`).Scan(&before); err != nil {
		t.Fatal(err)
	}
	err := f.s.completedLocalUnknownCosts(context.Background())
	if err == nil || !strings.Contains(err.Error(), "tool schemas") {
		t.Fatalf("old coding tools accepted or wrong guard: %v", err)
	}
	var after string
	if err := f.db.QueryRow(`SELECT group_concat(body) FROM domain_objects WHERE kind='BudgetLedgerEntry'`).Scan(&after); err != nil {
		t.Fatal(err)
	}
	if before != after {
		t.Fatal("UNKNOWN ledger changed after rejection")
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
