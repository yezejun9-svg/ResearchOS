package domain

import (
	"bytes"
	"context"
	"database/sql"
	"strings"
	"testing"
	"time"
)

type rejectingClientPort struct{ calls, inserted int }

func (p *rejectingClientPort) ValidateBinding(ctx context.Context, tx *sql.Tx, _, _, _, _ string) error {
	if _, err := tx.ExecContext(ctx, "INSERT INTO rejected_command_probe(value) VALUES('partial write')"); err != nil {
		return err
	}
	p.calls++
	if err := tx.QueryRowContext(ctx, "SELECT count(*) FROM rejected_command_probe").Scan(&p.inserted); err != nil {
		return err
	}
	return Fail(503, "MODEL_UNAVAILABLE", "fixture refusal after an intermediate write")
}
func (p *rejectingClientPort) AdmitTurn(context.Context, *sql.Tx, string, string, Object) error {
	return nil
}

func TestClientTypedRejectionRollsBackBusinessWrites(t *testing.T) {
	f := contextFixture(t)
	if _, err := f.db.Exec("CREATE TABLE rejected_command_probe(value TEXT)"); err != nil {
		t.Fatal(err)
	}
	svc, sid, _ := handlerTypedSession(t, f, "atomic-client")
	port := &rejectingClientPort{}
	svc.SessionRuntime = port
	env := handlerDecode(t, &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("atomic-client"), ProjectID: &f.project, SessionID: &sid, ExpectedRevision: revPtr(1), WriterEpoch: revPtr(1), Method: strptr("session.send"), Payload: Bytes(Object{"text": "reject after write", "attachment_artifact_ids": Empty(), "delivery": "NORMAL"})})
	for attempt := 0; attempt < 2; attempt++ {
		sourceTx(t, f.db, func(tx *sql.Tx) error {
			res, replay, err := svc.Execute(context.Background(), tx, env, f.owner)
			if err != nil {
				return err
			}
			if deref(res.Status) != "REJECTED" || deref(res.ErrorCode) != "MODEL_UNAVAILABLE" || replay != (attempt == 1) {
				t.Fatalf("rejection or replay changed: %s replay=%v", Bytes(res), replay)
			}
			return nil
		})
	}
	if port.calls != 1 || port.inserted != 1 {
		t.Fatalf("rejection did not reach actual intermediate write: calls=%d inserted=%d", port.calls, port.inserted)
	}
	var count int
	if err := f.db.QueryRow("SELECT count(*) FROM rejected_command_probe").Scan(&count); err != nil || count != 0 {
		t.Fatalf("rejected command committed %d intermediate writes: %v", count, err)
	}
	if err := f.db.QueryRow("SELECT count(*) FROM idempotency WHERE key=?", deref(env.CommandID)).Scan(&count); err != nil || count != 1 {
		t.Fatalf("rejection was not committed once: %d %v", count, err)
	}
}

func TestAttachSynchronousCompletionAndExactReplay(t *testing.T) {
	f := contextFixture(t)
	svc, sid, _ := handlerTypedSession(t, f, "original-client")
	svc.Host.LeaseTTL = time.Minute
	if _, err := f.db.Exec(`UPDATE client_sessions SET lease_expires_at=? WHERE id=?`, time.Now().Add(-time.Minute).UTC().Format(time.RFC3339Nano), sid); err != nil {
		t.Fatal(err)
	}
	env := handlerDecode(t, &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("new-client"), ProjectID: &f.project, SessionID: &sid, ExpectedRevision: revPtr(1), Method: strptr("session.attach"), Payload: Bytes(Object{"request_write_owner": true, "after_sequence": 0})})
	var first []byte
	for attempt := 0; attempt < 2; attempt++ {
		sourceTx(t, f.db, func(tx *sql.Tx) error {
			res, replay, err := svc.Execute(context.Background(), tx, env, f.owner)
			if err != nil {
				return err
			}
			if deref(res.Status) != "COMPLETED" || res.Result["write_owner_acquired"] != true || derefI64(res.Revision, 0) != 3 || replay != (attempt == 1) {
				t.Fatalf("attach response %s replay=%v", Bytes(res), replay)
			}
			if attempt == 0 {
				first = Bytes(res)
			} else if !bytes.Equal(first, Bytes(res)) {
				t.Fatal("same command changed response bytes")
			}
			return nil
		})
	}
	var epoch, rev, watermark, events int64
	var writer string
	if err := f.db.QueryRow(`SELECT writer_epoch,revision,event_watermark,writer_client_id FROM client_sessions WHERE id=?`, sid).Scan(&epoch, &rev, &watermark, &writer); err != nil {
		t.Fatal(err)
	}
	if err := f.db.QueryRow(`SELECT count(*) FROM outbox WHERE project=? AND json_extract(body,'$.session_id')=? AND json_extract(body,'$.kind')='CLIENT_HANDOFF'`, f.project, sid).Scan(&events); err != nil {
		t.Fatal(err)
	}
	if epoch != 2 || rev != 3 || watermark != 1 || events != 1 || writer != "new-client" {
		t.Fatalf("grant state epoch=%d revision=%d watermark=%d events=%d writer=%s", epoch, rev, watermark, events, writer)
	}
}

func TestAttachHistoricalAckRemainsImmutable(t *testing.T) {
	f := contextFixture(t)
	svc, sid, _ := handlerTypedSession(t, f, "original-client")
	env := handlerDecode(t, &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("original-client"), ProjectID: &f.project, SessionID: &sid, ExpectedRevision: revPtr(1), Method: strptr("session.attach"), Payload: Bytes(Object{"request_write_owner": true, "after_sequence": 0})})
	ack := &Response{ProtocolVersion: strptr(ProtocolV2), CommandID: env.CommandID, Method: env.Method, Status: strptr("ACKNOWLEDGED"), SessionID: env.SessionID, Revision: revPtr(3), Result: map[string]any{"accepted_at": Now(), "operation_id": "op-" + deref(env.CommandID), "after_sequence": int64(1), "related_resource_ref": nil}}
	if err := ValidateResultAgainstMethod("session.attach", ack, svc.Doc); err != nil {
		t.Fatal(err)
	}
	hash, err := env.ContentHash()
	if err != nil {
		t.Fatal(err)
	}
	headers, err := writeClientCommandEnvelope(svc.Doc, env)
	if err != nil {
		t.Fatal(err)
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		if _, err := reserveClientCommandIdentity(context.Background(), tx, svc.Doc, f.owner, env.originalRaw, env); err != nil {
			return err
		}
		_, err := tx.Exec(`INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at) VALUES(?,?,?,?,?,?,?,?,?)`, f.owner, f.project, "v2:session.attach", deref(env.CommandID), hash, 0, string(Bytes(ack)), headers, Now())
		return err
	})
	var original string
	if err := f.db.QueryRow(`SELECT body FROM idempotency WHERE principal=? AND project=? AND operation='v2:session.attach' AND key=?`, f.owner, f.project, deref(env.CommandID)).Scan(&original); err != nil {
		t.Fatal(err)
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		res, replay, err := svc.Execute(context.Background(), tx, env, f.owner)
		if err != nil {
			return err
		}
		if !replay || deref(res.Status) != "ACKNOWLEDGED" || string(Bytes(res)) != original {
			t.Fatalf("historical ACK changed: %s replay=%v", Bytes(res), replay)
		}
		return nil
	})
	var after string
	if err := f.db.QueryRow(`SELECT body FROM idempotency WHERE principal=? AND project=? AND operation='v2:session.attach' AND key=?`, f.owner, f.project, deref(env.CommandID)).Scan(&after); err != nil || after != original {
		t.Fatalf("historical response mutated: %v", err)
	}
}

func TestAttachGrantFaultRollsBackEpochAndIdentity(t *testing.T) {
	f := contextFixture(t)
	svc, sid, _ := handlerTypedSession(t, f, "original-client")
	svc.Host.LeaseTTL = time.Minute
	if _, err := f.db.Exec(`UPDATE client_sessions SET lease_expires_at=? WHERE id=?`, time.Now().Add(-time.Minute).UTC().Format(time.RFC3339Nano), sid); err != nil {
		t.Fatal(err)
	}
	if _, err := f.db.Exec(`CREATE TRIGGER attach_fault BEFORE UPDATE OF writer_client_id ON client_sessions BEGIN SELECT RAISE(ABORT,'attach fault'); END`); err != nil {
		t.Fatal(err)
	}
	env := handlerDecode(t, &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("new-client"), ProjectID: &f.project, SessionID: &sid, ExpectedRevision: revPtr(1), Method: strptr("session.attach"), Payload: Bytes(Object{"request_write_owner": true, "after_sequence": 0})})
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	res, replay, err := svc.Execute(context.Background(), tx, env, f.owner)
	if err == nil || res != nil || replay {
		t.Fatalf("fault unexpectedly completed: %s replay=%v err=%v", Bytes(res), replay, err)
	}
	if err := tx.Rollback(); err != nil {
		t.Fatal(err)
	}
	var rev, epoch, watermark, identities int64
	if err := f.db.QueryRow(`SELECT revision,writer_epoch,event_watermark FROM client_sessions WHERE id=?`, sid).Scan(&rev, &epoch, &watermark); err != nil {
		t.Fatal(err)
	}
	if err := f.db.QueryRow(`SELECT count(*) FROM client_command_identities WHERE principal=? AND command_id=?`, f.owner, deref(env.CommandID)).Scan(&identities); err != nil {
		t.Fatal(err)
	}
	if rev != 1 || epoch != 1 || watermark != 0 || identities != 0 {
		t.Fatalf("fault retained writes: rev=%d epoch=%d watermark=%d identity=%d", rev, epoch, watermark, identities)
	}
}

func TestAttachSnapshotFaultRollsBackHandoffAndJournal(t *testing.T) {
	f := contextFixture(t)
	svc, sid, _ := handlerTypedSession(t, f, "original-client")
	svc.Host.LeaseTTL = time.Minute
	if _, err := f.db.Exec(`UPDATE client_sessions SET lease_expires_at=? WHERE id=?`, time.Now().Add(-time.Minute).UTC().Format(time.RFC3339Nano), sid); err != nil {
		t.Fatal(err)
	}
	if _, err := f.db.Exec(`CREATE TRIGGER attach_snapshot_fault AFTER INSERT ON outbox WHEN json_extract(NEW.body,'$.kind')='CLIENT_HANDOFF' BEGIN UPDATE client_sessions SET created_at='invalid' WHERE id=json_extract(NEW.body,'$.session_id'); END`); err != nil {
		t.Fatal(err)
	}
	env := handlerDecode(t, &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("new-client"), ProjectID: &f.project, SessionID: &sid, ExpectedRevision: revPtr(1), Method: strptr("session.attach"), Payload: Bytes(Object{"request_write_owner": true, "after_sequence": 0})})
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	res, replay, err := svc.Execute(context.Background(), tx, env, f.owner)
	if err == nil || !strings.Contains(err.Error(), "SNAPSHOT_SCHEMA") || res != nil || replay {
		t.Fatalf("snapshot failure not surfaced: %s replay=%v err=%v", Bytes(res), replay, err)
	}
	if err := tx.Rollback(); err != nil {
		t.Fatal(err)
	}
	var revision, epoch, watermark, events, identities int64
	var upstream string
	if err := f.db.QueryRow(`SELECT revision,writer_epoch,event_watermark,upstream_session_id FROM client_sessions WHERE id=?`, sid).Scan(&revision, &epoch, &watermark, &upstream); err != nil {
		t.Fatal(err)
	}
	if err := f.db.QueryRow(`SELECT count(*) FROM outbox WHERE project=? AND json_extract(body,'$.session_id')=? AND json_extract(body,'$.kind')='CLIENT_HANDOFF'`, f.project, sid).Scan(&events); err != nil {
		t.Fatal(err)
	}
	if err := f.db.QueryRow(`SELECT count(*) FROM client_command_identities WHERE principal=? AND command_id=?`, f.owner, deref(env.CommandID)).Scan(&identities); err != nil {
		t.Fatal(err)
	}
	if revision != 1 || epoch != 1 || watermark != 0 || upstream == "" || events != 0 || identities != 0 {
		t.Fatalf("snapshot fault retained writes: rev=%d epoch=%d watermark=%d upstream=%s events=%d identities=%d", revision, epoch, watermark, upstream, events, identities)
	}
}

func TestAttachJournalFaultRollsBackHandoff(t *testing.T) {
	f:=contextFixture(t)
	svc,sid,_:=handlerTypedSession(t,f,"original-client")
	svc.Host.LeaseTTL=time.Minute
	if _,err:=f.db.Exec(`UPDATE client_sessions SET lease_expires_at=? WHERE id=?`,time.Now().Add(-time.Minute).UTC().Format(time.RFC3339Nano),sid);err!=nil{t.Fatal(err)}
	if _,err:=f.db.Exec(`CREATE TRIGGER attach_journal_fault BEFORE INSERT ON outbox WHEN json_extract(NEW.body,'$.kind')='CLIENT_HANDOFF' BEGIN SELECT RAISE(ABORT,'journal fault'); END`);err!=nil{t.Fatal(err)}
	env:=handlerDecode(t,&Envelope{ProtocolVersion:strptr(ProtocolV2),CommandID:strptr(ID()),ClientID:strptr("new-client"),ProjectID:&f.project,SessionID:&sid,ExpectedRevision:revPtr(1),Method:strptr("session.attach"),Payload:Bytes(Object{"request_write_owner":true,"after_sequence":0})})
	tx,err:=f.db.Begin();if err!=nil{t.Fatal(err)}
	res,replay,err:=svc.Execute(context.Background(),tx,env,f.owner)
	if err==nil || !strings.Contains(err.Error(),"journal fault") || res!=nil || replay {t.Fatalf("journal failure not surfaced: %s replay=%v err=%v",Bytes(res),replay,err)}
	if err:=tx.Rollback();err!=nil{t.Fatal(err)}
	var revision,epoch,watermark,identities int64
	if err:=f.db.QueryRow(`SELECT revision,writer_epoch,event_watermark FROM client_sessions WHERE id=?`,sid).Scan(&revision,&epoch,&watermark);err!=nil{t.Fatal(err)}
	if err:=f.db.QueryRow(`SELECT count(*) FROM client_command_identities WHERE principal=? AND command_id=?`,f.owner,deref(env.CommandID)).Scan(&identities);err!=nil{t.Fatal(err)}
	if revision!=1 || epoch!=1 || watermark!=0 || identities!=0 {t.Fatalf("journal fault retained writes: rev=%d epoch=%d watermark=%d identity=%d",revision,epoch,watermark,identities)}
}

func TestAttachFiniteRefusalsLeaveWriterUntouched(t *testing.T) {
	for _, scenario := range []string{"foreign-valid", "future-cursor", "pending-control", "restore-fenced", "non-owner", "remote-device"} {
		t.Run(scenario, func(t *testing.T) {
			f := contextFixture(t)
			svc, sid, _ := handlerTypedSession(t, f, "original-client")
			svc.Host.LeaseTTL = time.Minute
			client, principal, code, cursor := "new-client", f.owner, "SESSION_BUSY", int64(0)
			switch scenario {
			case "foreign-valid":
				code = "WRITER_BUSY"
			case "future-cursor":
				code, cursor = "CURSOR_INVALID", 1
			case "pending-control":
				if _, err := f.db.Exec(`UPDATE client_sessions SET lease_expires_at=? WHERE id=?`, time.Now().Add(-time.Minute).UTC().Format(time.RFC3339Nano), sid); err != nil {
					t.Fatal(err)
				}
				if _, err := f.db.Exec(`INSERT INTO client_control_requests(principal,project,command_id,session_id,control_request_id,request_hash,target_id,task_ids,state,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)`, f.owner, f.project, ID(), sid, ID(), "fixture-hash", sid, "[]", "REQUESTED", Now()); err != nil {
					t.Fatal(err)
				}
			case "restore-fenced":
				client = "original-client"
				if _, err := f.db.Exec(`UPDATE client_sessions SET resume_requires_explicit_user=1 WHERE id=?`, sid); err != nil {
					t.Fatal(err)
				}
			case "non-owner", "remote-device":
				principal = scenario + "-principal"
				roles := []string{"PLANNER"}
				if scenario == "remote-device" {
					roles = []string{"OWNER"}
				}
				if err := f.s.ProvisionPrincipal(context.Background(), Principal{ID: principal, Roles: roles, Grants: []Grant{{ProjectID: f.project}}}); err != nil {
					t.Fatal(err)
				}
				if scenario == "remote-device" {
					if _, err := f.db.Exec(`INSERT INTO remote_devices(id,owner,body) VALUES(?,?,?)`, principal, f.owner, string(Bytes(Object{"status": "ACTIVE", "role": "OWNER"}))); err != nil {
						t.Fatal(err)
					}
				}
				code = "FORBIDDEN"
			}
			env := handlerDecode(t, &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: &client, ProjectID: &f.project, SessionID: &sid, ExpectedRevision: revPtr(1), Method: strptr("session.attach"), Payload: Bytes(Object{"request_write_owner": true, "after_sequence": cursor})})
			sourceTx(t, f.db, func(tx *sql.Tx) error {
				res, _, err := svc.Execute(context.Background(), tx, env, principal)
				if err != nil {
					return err
				}
				if deref(res.Status) != "REJECTED" || deref(res.ErrorCode) != code {
					t.Fatalf("%s: %s", scenario, Bytes(res))
				}
				return nil
			})
			var revision, epoch, watermark int64
			var writer string
			if err := f.db.QueryRow(`SELECT revision,writer_epoch,event_watermark,writer_client_id FROM client_sessions WHERE id=?`, sid).Scan(&revision, &epoch, &watermark, &writer); err != nil {
				t.Fatal(err)
			}
			if revision != 1 || epoch != 1 || watermark != 0 || writer != "original-client" {
				t.Fatalf("refusal mutated writer: rev=%d epoch=%d watermark=%d writer=%s", revision, epoch, watermark, writer)
			}
		})
	}
}

func TestAttachNullLeaseRequiresNewGrant(t *testing.T) {
	f := contextFixture(t)
	svc, sid, _ := handlerTypedSession(t, f, "same-client")
	svc.Host.LeaseTTL = time.Minute
	if _, err := f.db.Exec(`UPDATE client_sessions SET lease_expires_at=NULL WHERE id=?`, sid); err != nil {
		t.Fatal(err)
	}
	env := handlerDecode(t, &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("same-client"), ProjectID: &f.project, SessionID: &sid, ExpectedRevision: revPtr(1), Method: strptr("session.attach"), Payload: Bytes(Object{"request_write_owner": true, "after_sequence": 0})})
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		res, _, err := svc.Execute(context.Background(), tx, env, f.owner)
		if err != nil {
			return err
		}
		if deref(res.Status) != "COMPLETED" || derefI64(res.Revision, 0) != 3 {
			t.Fatalf("null lease treated as renewal: %s", Bytes(res))
		}
		return nil
	})
	var epoch, watermark int64
	if err := f.db.QueryRow(`SELECT writer_epoch,event_watermark FROM client_sessions WHERE id=?`, sid).Scan(&epoch, &watermark); err != nil || epoch != 2 || watermark != 1 {
		t.Fatalf("null regrant epoch=%d watermark=%d err=%v", epoch, watermark, err)
	}
}
