//go:build windows

package domain

import (
	"context"
	"database/sql"
	"testing"
	"time"
)

func TestClientCancelChangesCanonicalRun(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	task := o.task("typed-cancel", Empty(), Empty())
	r := o.claim(task)
	doc, sid := sessionProjectionMapping(t, f, task)
	if _, err := f.db.Exec("UPDATE client_sessions SET run_id=? WHERE id=?", r.run["id"], sid); err != nil {
		t.Fatal(err)
	}
	svc := &ClientService{Doc: doc, Domain: f.s, Host: ClientHostInfo{CoreBuildID: "fixture-build", LeaseTTL: time.Minute}}
	env := &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("mixed-client"), ProjectID: &f.project, SessionID: &sid, ExpectedRevision: revPtr(1), WriterEpoch: revPtr(1), Method: strptr("session.control"), Payload: Bytes(Object{"action": "CANCEL", "target_id": r.run["id"], "reason": "user cancelled"})}
	for attempt := 0; attempt < 2; attempt++ {
		sourceTx(t, f.db, func(tx *sql.Tx) error {
			res, replay, err := svc.Execute(context.Background(), tx, handlerDecode(t, env), f.owner)
			if err != nil {
				return err
			}
			if deref(res.Status) != "ACKNOWLEDGED" || replay != (attempt == 1) {
				t.Fatalf("cancel response %s replay=%v", Bytes(res), replay)
			}
			return nil
		})
	}
	f.token = o.owner
	current := f.read("runs", Str(r.run, "id"))
	if current["status"] != "CANCEL_REQUESTED" || current["cancel_requested_at"] == nil {
		t.Fatalf("canonical run unchanged: %s", Bytes(current))
	}
	var count int
	if err := f.db.QueryRow(`SELECT count(*) FROM outbox WHERE project=? AND json_extract(body,'$.session_id')=? AND json_extract(body,'$.kind')='RUN_STATE' AND json_extract(body,'$.payload.status')='CANCEL_REQUESTED' AND json_extract(body,'$.payload.revision')=?`, f.project, sid, current["revision"]).Scan(&count); err != nil || count != 1 {
		t.Fatalf("cancellation journal mismatch %d %v", count, err)
	}
}

func TestClientSameWriterRenewsExpiredLease(t *testing.T) {
	f := contextFixture(t)
	svc, sid, _ := handlerTypedSession(t, f, "mixed-client")
	svc.Host.LeaseTTL = time.Minute
	if _, err := f.db.Exec("UPDATE client_sessions SET lease_expires_at=? WHERE id=?", time.Now().Add(-time.Minute).UTC().Format(time.RFC3339Nano), sid); err != nil {
		t.Fatal(err)
	}
	env := &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("mixed-client"), ProjectID: &f.project, SessionID: &sid, ExpectedRevision: revPtr(1), Method: strptr("session.attach"), Payload: Bytes(Object{"request_write_owner": true, "after_sequence": 0})}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		res, _, err := svc.Execute(context.Background(), tx, handlerDecode(t, env), f.owner)
		if err != nil {
			return err
		}
		if deref(res.Status) != "COMPLETED" || res.Result["write_owner_acquired"] != true {
			t.Fatalf("renewal refused: %s", Bytes(res))
		}
		return nil
	})
	var epoch int64
	var revision, watermark int64
	var until string
	if err := f.db.QueryRow("SELECT writer_epoch,revision,event_watermark,lease_expires_at FROM client_sessions WHERE id=?", sid).Scan(&epoch, &revision, &watermark, &until); err != nil {
		t.Fatal(err)
	}
	deadline, err := time.Parse(time.RFC3339Nano, until)
	if err != nil || !deadline.After(time.Now()) || epoch != 1 || revision != 1 || watermark != 0 {
		t.Fatalf("ordinary renewal changed generation: epoch=%d revision=%d watermark=%d until=%s %v", epoch, revision, watermark, until, err)
	}
	env.CommandID = strptr(ID())
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		res, _, err := svc.Execute(context.Background(), tx, handlerDecode(t, env), f.owner)
		if err != nil {
			return err
		}
		if deref(res.Status) != "COMPLETED" || derefI64(res.Revision, 0) != 1 {
			t.Fatalf("ordinary renewal changed revision: %s", Bytes(res))
		}
		return nil
	})
}

func TestClientAttachRefusesUnsettledCanonicalRun(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	svc, sid, _ := handlerTypedSession(t, f, "original-client")
	svc.Host.LeaseTTL = time.Minute
	task := o.task("attach-unsettled", Empty(), Empty())
	r := o.claim(task)
	if _, err := f.db.Exec(`UPDATE client_sessions SET task_id=?,run_id=?,lease_expires_at=? WHERE id=?`, task["id"], r.run["id"], time.Now().Add(-time.Minute).UTC().Format(time.RFC3339Nano), sid); err != nil {
		t.Fatal(err)
	}
	env := handlerDecode(t, &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("new-client"), ProjectID: &f.project, SessionID: &sid, ExpectedRevision: revPtr(1), Method: strptr("session.attach"), Payload: Bytes(Object{"request_write_owner": true, "after_sequence": 0})})
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		res, _, err := svc.Execute(context.Background(), tx, env, f.owner)
		if err != nil {
			return err
		}
		if deref(res.ErrorCode) != "SESSION_BUSY" {
			t.Fatalf("unsettled run allowed: %s", Bytes(res))
		}
		return nil
	})
	var epoch, revision int64
	if err := f.db.QueryRow(`SELECT writer_epoch,revision FROM client_sessions WHERE id=?`, sid).Scan(&epoch, &revision); err != nil || epoch != 1 || revision != 1 {
		t.Fatalf("unsettled run changed writer epoch=%d rev=%d err=%v", epoch, revision, err)
	}
}

func TestClientResumeNeverRestartsPreviousRun(t *testing.T) {
	for _, status := range []string{"CANCELLED", "FAILED", "RUNNING"} {
		t.Run(status, func(t *testing.T) {
			o := orchestrationSetup(t)
			f := o.f
			task := o.task("resume-boundary", Empty(), Empty())
			r := o.claim(task)
			doc, sid := sessionProjectionMapping(t, f, task)
			run := MergeCopy(r.run, Object{})
			run["status"] = status
			run["children_stopped"], run["queue_empty"] = status != "RUNNING", status != "RUNNING"
			if _, err := f.db.Exec("UPDATE domain_objects SET body=? WHERE kind='Run' AND id=?", string(Bytes(run)), run["id"]); err != nil {
				t.Fatal(err)
			}
			if _, err := f.db.Exec("UPDATE client_sessions SET run_id=?,workspace_ref='fixture-workspace',model_config_ref='fixture-model',title='resume fixture' WHERE id=?", run["id"], sid); err != nil {
				t.Fatal(err)
			}
			svc := &ClientService{Doc: doc, Domain: f.s, Host: ClientHostInfo{CoreBuildID: "fixture-build", LeaseTTL: time.Minute}}
			env := &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("mixed-client"), ProjectID: &f.project, SessionID: &sid, ExpectedRevision: revPtr(1), WriterEpoch: revPtr(1), Method: strptr("session.control"), Payload: Bytes(Object{"action": "RESUME", "target_id": sid, "reason": "resume context"})}
			sourceTx(t, f.db, func(tx *sql.Tx) error {
				res, _, err := svc.Execute(context.Background(), tx, handlerDecode(t, env), f.owner)
				if err != nil {
					return err
				}
				if status == "RUNNING" {
					if deref(res.ErrorCode) != "SESSION_BUSY" {
						t.Fatalf("running resume: %s", Bytes(res))
					}
				} else if deref(res.Status) != "COMPLETED" {
					t.Fatalf("settled resume: %s", Bytes(res))
				}
				return nil
			})
			var body string
			if err := f.db.QueryRow("SELECT body FROM domain_objects WHERE kind='Run' AND id=?", run["id"]).Scan(&body); err != nil || body != string(Bytes(run)) {
				t.Fatalf("resume mutated prior Run: %v", err)
			}
		})
	}
}
