//go:build windows

package domain

import (
	"bytes"
	"testing"
	"time"
)

// These deliberately invalid fixtures are rejection counterexamples, never
// reconciliation evidence. No fresh correctly bound settled receipt is inserted.
func TestClientAttachRestoreRejectsUnprovenRenewal(t *testing.T) {
	for _, mode := range []string{"absent", "wrong-project", "wrong-run", "wrong-epoch", "stale", "equal-barrier", "children-only", "queue-only", "wrong-spec", "wrong-receipt"} {
		t.Run(mode, func(t *testing.T) {
			o := orchestrationSetup(t)
			f := o.f
			task := o.task("attach-restore-rejection", Empty(), Empty())
			run := o.claim(task)
			runID := Str(run.run, "id")
			epoch, err := Num(run.run, "lease_epoch")
			if err != nil { t.Fatal(err) }
			service, sid, _ := handlerTypedSession(t, f, "restore-owner")
			restored := time.Now().UTC().Add(-time.Minute)
			lease := time.Now().UTC().Add(5 * time.Minute).Format(time.RFC3339Nano)
			if _, err = f.db.Exec("UPDATE client_sessions SET run_id=?,lease_expires_at=? WHERE id=?", runID, lease, sid); err != nil { t.Fatal(err) }
			if _, err = f.db.Exec("INSERT INTO backup_restore_barriers(project,run,restored_at) VALUES(?,?,?)", f.project, runID, restored.Format(time.RFC3339Nano)); err != nil { t.Fatal(err) }
			// Old snapshot settlement flags do not establish fresh reconciliation.
			if _, err = f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.status','RECONCILING','$.children_stopped',json('true'),'$.queue_empty',json('true'),'$.lease_expires_at','1970-01-01T00:00:00Z') WHERE project=? AND kind='Run' AND id=?", f.project, runID); err != nil { t.Fatal(err) }
			if mode != "absent" {
				project, observedRun, observedEpoch := f.project, runID, epoch
				observed := restored.Add(time.Second)
				children, queue := true, true
				specRun := runID
				switch mode {
				case "wrong-project": project = "another-project"
				case "wrong-run": observedRun = "another-run"
				case "wrong-epoch": observedEpoch++
				case "stale": observed = restored.Add(-time.Second)
				case "equal-barrier": observed = restored
				case "children-only": queue = false
				case "queue-only": children = false
				case "wrong-spec": specRun = "another-spec-run"
				}
				observation := Object{"spec": Object{"run_id": specRun, "task_id": run.run["task_id"], "epoch": observedEpoch}, "children_stopped": children, "queue_empty": queue}
				receipt := Hash(observation)
				if mode == "wrong-receipt" { receipt = "not-the-observation-hash" }
				if _, err = f.db.Exec("INSERT INTO runtime_observations(project,run,epoch,receipt_hash,body,observed_at) VALUES(?,?,?,?,?,?)", project, observedRun, observedEpoch, receipt, string(Bytes(observation)), observed.Format(time.RFC3339Nano)); err != nil { t.Fatal(err) }
			}
			before := attachContractRead(t, f, sid)
			var runBefore, barrierBefore string
			if err = f.db.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='Run' AND id=?", f.project, runID).Scan(&runBefore); err != nil { t.Fatal(err) }
			if err = f.db.QueryRow("SELECT restored_at FROM backup_restore_barriers WHERE project=? AND run=?", f.project, runID).Scan(&barrierBefore); err != nil { t.Fatal(err) }
			for _, client := range []string{before.writer, "restore-other-client"} {
				env := attachContractCommand(f, sid, client, before.revision)
				response, replay := handlerCommand(t, f, service, env)
				if replay || deref(response.Status) != "REJECTED" || deref(response.ErrorCode) != "SESSION_BUSY" || attachContractRead(t, f, sid) != before || attachContractEventCount(t, f, sid, deref(env.CommandID)) != 0 {
					t.Fatalf("unproven restore wrote writer state: mode=%s client=%s response=%s", mode, client, Bytes(response))
				}
				again, replay := handlerCommand(t, f, service, env)
				if !replay || !bytes.Equal(Bytes(response), Bytes(again)) || attachContractRead(t, f, sid) != before {
					t.Fatal("rejected command replay changed restore state")
				}
			}
			var runAfter, barrierAfter string
			if err = f.db.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='Run' AND id=?", f.project, runID).Scan(&runAfter); err != nil { t.Fatal(err) }
			if err = f.db.QueryRow("SELECT restored_at FROM backup_restore_barriers WHERE project=? AND run=?", f.project, runID).Scan(&barrierAfter); err != nil { t.Fatal(err) }
			if runAfter != runBefore || barrierAfter != barrierBefore { t.Fatal("attach changed restore barrier or Run recovery state") }
		})
	}
}

// The ordinary active-owner path has no restore barrier and retains lease-only
// renewal. This existing real fixture does not fabricate a restore observation.
func TestClientAttachRestoreGatePreservesOrdinaryActiveRenewal(t *testing.T) {
	TestClientAttachActiveOwnerRenewalDoesNotTransfer(t)
}
