package domain

import (
	"context"
	"database/sql"
	"fmt"
	"strings"
	"testing"
)

// takeoverAssert records one W12-01 assertion without stopping the test. The shared
// resourcesAssert helper calls t.Fatalf, which would mask every later assertion whenever an
// early one fails, and then a mutation could not be attributed to the single id it broke.
func takeoverAssert(t *testing.T, id string, want, got, evidence any) {
	t.Helper()
	status := "PASS"
	if Hash(want) != Hash(got) {
		status = "FAIL"
	}
	fmt.Println("W12_ASSERTION " + string(Bytes(Object{"assertion_id": id, "expected": want, "actual": got, "status": status, "evidence": evidence})))
	if status == "FAIL" {
		t.Errorf("%s mismatch", id)
	}
}

// W12-01 step 3: "late usage reconciles against the original run and key; disconnect/restart
// must neither recount the charge nor clear the reservation".
//
// Exposure groups ledger entries by (project, run, provider_request_id) and a hold that is
// never settled keeps counting, while reserveRuntimeLocalLaunch keys each hold by lease epoch.
// Two separate defects sit behind that sentence, each with its own assertion:
//
//   - taking over a lease left the dead epoch's hold open, so the run carried one more
//     unresolved hold per reconnect. The repair appends an explicit RELEASE for the older
//     epoch before reserving the new one - recorded, never deleted.
//   - retrying a control request whose outcome is unknown re-enters the same epoch. The
//     ledger's idempotency compares the whole request payload including occurred_at, so a
//     plain repeat answered IDEMPOTENCY_CONFLICT. The repair treats an already-admitted
//     epoch as a no-op.
//
// Every assertion is scoped to this run's runtime-local-launch prefix: the claim that produced
// the run writes its own fixture-dispatch hold, and counting that would prove nothing about
// takeover.
func TestW12BudgetLeaseTakeover(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	task := o.task("takeover-accounting", Empty(), Empty())
	r := o.claim(task)
	runID := Str(r.run, "id")
	prefix := "runtime-local-launch/" + runID + "/"

	admission := Object{"profile": Object{
		"sandbox":          runtimeSandboxProfile,
		"adapter_revision": runtimeBridgeRevision,
		"platform":         "windows-amd64",
		"command_id":       "takeover-probe",
		"build_hash":       "build-hash-under-test",
		"permissions":      Object{"capabilities": Empty(), "network": "none", "environment": "staging-only", "process_limit": 1, "memory_mib": 256},
		"timeout_seconds":  float64(60),
		"outputs":          []any{"result.json"},
	}}

	// Each epoch is reserved in its own committed transaction, so the next takeover reads
	// durable state rather than this transaction's scratch space.
	for _, epoch := range []any{float64(1), float64(2)} {
		tx, e := f.db.BeginTx(context.Background(), nil)
		if e != nil {
			t.Fatal(e)
		}
		run, e := load(tx, f.project, "Run", runID)
		if e != nil {
			tx.Rollback()
			t.Fatal(e)
		}
		run["lease_epoch"] = epoch
		if e = f.s.reserveRuntimeLocalLaunch(tx, f.project, run, admission); e != nil {
			tx.Rollback()
			t.Fatalf("reserve at epoch %v: %v", epoch, e)
		}
		if e = tx.Commit(); e != nil {
			t.Fatal(e)
		}
	}

	history := ledgerHistory(t, f, prefix)
	takeoverAssert(t, "W12-TAKEOVER-HISTORY-RETAINED",
		[]any{[]any{"RESERVE", "RELEASE", "RESERVE"}}, []any{history},
		Object{"prefix": prefix, "operations": history})

	takeoverAssert(t, "W12-TAKEOVER-SINGLE-OPEN-HOLD", []any{1}, []any{openLocalHolds(history)},
		Object{"operations": history, "rule": "a RESERVE with no later RELEASE for the same request keeps counting"})

	// Retrying the epoch that is already admitted must add nothing and must not error.
	before := ledgerHistory(t, f, prefix)
	tx, e := f.db.BeginTx(context.Background(), nil)
	if e != nil {
		t.Fatal(e)
	}
	run, e := load(tx, f.project, "Run", runID)
	if e != nil {
		tx.Rollback()
		t.Fatal(e)
	}
	run["lease_epoch"] = float64(2)
	retryFault := ""
	if e = f.s.reserveRuntimeLocalLaunch(tx, f.project, run, admission); e != nil {
		retryFault = e.Error()
		tx.Rollback()
	} else if e = tx.Commit(); e != nil {
		t.Fatal(e)
	}
	after := ledgerHistory(t, f, prefix)
	takeoverAssert(t, "W12-TAKEOVER-REPLAY-ADDS-NOTHING", []any{before, 0, ""}, []any{after, len(after) - len(before), retryFault},
		Object{"before": before, "after": after, "retry_error": retryFault})

	// The projection a later session reads must agree with the rows, scoped to this run.
	f.token = o.owner
	usage, e := f.s.BudgetUsage(context.Background(), f.token, f.project, runID)
	if e != nil {
		t.Fatal(e)
	}
	local := 0
	for _, v := range Arr(usage, "reserved") {
		entry, ok := v.(map[string]any)
		if !ok {
			continue
		}
		if strings.HasPrefix(Str(entry, "provider_request_id"), prefix) && entry["operation"] == "RESERVE" {
			local++
		}
	}
	takeoverAssert(t, "W12-TAKEOVER-PROJECTION-COUNTS-ONE", []any{1, 0}, []any{local, len(Arr(usage, "unknown"))},
		Object{"reserved": Arr(usage, "reserved"), "unknown_count": len(Arr(usage, "unknown"))})
}

// ledgerHistory returns operation names for one run's local-launch ledger rows, insert order.
func ledgerHistory(t *testing.T, f *fixture, prefix string) []any {
	t.Helper()
	rows, e := f.db.Query("SELECT json_extract(body,'$.operation') FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.provider_request_id') LIKE ? ORDER BY rowid", f.project, prefix+"%")
	if e != nil {
		t.Fatal(e)
	}
	defer rows.Close()
	out := []any{}
	for rows.Next() {
		var op string
		if e = rows.Scan(&op); e != nil {
			t.Fatal(e)
		}
		out = append(out, op)
	}
	if e = rows.Err(); e != nil {
		t.Fatal(e)
	}
	return out
}

// openLocalHolds counts reservations in one run's scoped history that no later terminal
// operation covered.
func openLocalHolds(history []any) int {
	open := 0
	for i, v := range history {
		if v != "RESERVE" {
			continue
		}
		settled := false
		for _, w := range history[i+1:] {
			if w == "RELEASE" || w == "COMMIT" || w == "RECONCILE" {
				settled = true
				break
			}
		}
		if !settled {
			open++
		}
	}
	return open
}

// Source fixtures retain every original ledger row. The private Host integration
// separately exercises the canonical report transaction with a real native run.
func TestCompletedRuntimeLocalLaunchRelease(t *testing.T) {
	for _, name := range []string{"settled", "failed", "cancelled", "active", "children", "queue", "missing_observation", "missing_identity", "nonzero", "foreign_event", "wrong_policy", "stale_epoch"} {
		t.Run(name, func(t *testing.T) {
			o := orchestrationSetup(t)
			f := o.f
			task := o.task("local-launch-terminal", Empty(), Empty())
			r := o.claim(task)
			runID := Str(r.run, "id")
			admission := Object{"profile": Object{"sandbox": runtimeSandboxProfile, "adapter_revision": runtimeBridgeRevision, "platform": "windows-amd64", "command_id": "terminal-probe", "build_hash": "fixture-build", "permissions": Object{"capabilities": Empty(), "network": "none", "environment": "staging-only", "process_limit": 1, "memory_mib": 256}, "timeout_seconds": 60, "outputs": []any{"result.json"}}}
			sourceTx(t, f.db, func(tx *sql.Tx) error {
				run, e := load(tx, f.project, "Run", runID)
				if e != nil {
					return e
				}
				if e = f.s.prepareRuntimeDispatch(tx, f.project, task, run, admission); e != nil {
					return e
				}
				dispatch, e := runtimeDispatch(tx, f.project, runID, run["lease_epoch"])
				if e != nil {
					return e
				}
				identity := Object{"pid": 123, "created": 456, "image": "source-fixture"}
				if name == "missing_identity" {
					identity = Object{}
				}
				observation := Object{"state": "SETTLED", "children_stopped": true, "queue_empty": true, "streams_drained": true, "cleanup_complete": true, "ended": Now(), "dispatch_key": dispatch["dispatch_key"], "manifest_hash": dispatch["manifest_hash"], "worker": "fixture-worker", "identity": identity}
				if _, e = tx.Exec(`UPDATE runtime_dispatches SET state='OBSERVED',worker='fixture-worker',journal_locator=dispatch_key,identity=?,observation_sequence=1,observation_hash=? WHERE project=? AND run=?`, Bytes(identity), Hash(observation), f.project, runID); e != nil {
					return e
				}
				if name != "missing_observation" {
					if _, e = tx.Exec(`INSERT INTO runtime_observations(project,run,epoch,receipt_hash,body,observed_at) VALUES(?,?,?,?,?,?)`, f.project, runID, run["lease_epoch"], Hash(observation), Bytes(observation), Now()); e != nil {
						return e
					}
				}
				goal, e := load(tx, f.project, "Goal", Str(task, "goal_id"))
				if e != nil {
					return e
				}
				request := "runtime-local-launch/" + runID + "/" + string(Bytes(run["lease_epoch"]))
				hold := Object{"policy_id": goal["budget_policy_id"], "run_id": runID, "operation": "RESERVE", "money": dollars("0"), "provider_request_id": request, "provider_event_id": request, "reservation_id": nil, "cost_basis": "UPPER_BOUND", "occurred_at": Now()}
				if name == "nonzero" {
					hold["money"] = dollars("1")
				}
				if name == "foreign_event" {
					hold["provider_event_id"] = "foreign-event"
				}
				if name == "wrong_policy" {
					hold["policy_id"] = "fixture-foreign-policy"
				}
				if name == "stale_epoch" {
					hold["provider_request_id"] = request + "-old"
					hold["provider_event_id"] = request + "-old"
				}
				if name == "wrong_policy" { // A malformed foreign row is never a production source.
					hold["id"], hold["project_id"], hold["revision"] = ID(), f.project, 1
					hold["receipt_hash"] = Receipt(hold)
					_, e = tx.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES(?,'BudgetLedgerEntry',?,1,?,1)`, f.project, hold["id"], Bytes(hold))
				} else {
					_, e = f.s.appendBudget(tx, f.project, hold)
				}
				if e != nil {
					return e
				}
				run["status"], run["children_stopped"], run["queue_empty"], run["ended_at"] = "SETTLED", true, true, Now()
				switch name {
				case "failed":
					run["status"] = "FAILED"
				case "cancelled":
					run["status"] = "CANCELLED"
				case "active":
					run["status"] = "RUNNING"
				case "children":
					run["children_stopped"] = false
				case "queue":
					run["queue_empty"] = false
				}
				var before string
				if e = tx.QueryRow(`SELECT group_concat(body) FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry'`, f.project).Scan(&before); e != nil {
					return e
				}
				if e = f.s.releaseCompletedRuntimeLocalLaunch(tx, f.project, run); e != nil {
					return e
				}
				if e = f.s.releaseCompletedRuntimeLocalLaunch(tx, f.project, run); e != nil {
					return e
				}
				var releases int
				if e = tx.QueryRow(`SELECT count(*) FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.provider_request_id')=? AND json_extract(body,'$.operation')='RELEASE'`, f.project, request).Scan(&releases); e != nil {
					return e
				}
				want := 0
				if name == "settled" || name == "failed" || name == "cancelled" {
					want = 1
				}
				if releases != want {
					t.Fatalf("release %s got %d want %d", name, releases, want)
				}
				if want == 0 {
					var after string
					tx.QueryRow(`SELECT group_concat(body) FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry'`, f.project).Scan(&after)
					if after != before {
						t.Fatal("ineligible ledger changed")
					}
				}
				return nil
			})
		})
	}
}
