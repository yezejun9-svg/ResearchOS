//go:build windows

package domain

import (
	"bytes"
	"context"
	"database/sql"
	"errors"
	"testing"
	"time"
)

type attachContractState struct {
	revision, epoch, sequence               int64
	writer, lease, model, workspace, native string
}

func attachContractRead(t *testing.T, f *fixture, sid string) attachContractState {
	t.Helper()
	var state attachContractState
	if err := f.db.QueryRow("SELECT revision,writer_epoch,event_watermark,writer_client_id,COALESCE(lease_expires_at,''),model_config_ref,workspace_ref,upstream_session_id FROM client_sessions WHERE id=?", sid).
		Scan(&state.revision, &state.epoch, &state.sequence, &state.writer, &state.lease, &state.model, &state.workspace, &state.native); err != nil {
		t.Fatal(err)
	}
	return state
}

func attachContractCommand(f *fixture, sid, client string, revision int64) *Envelope {
	return &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: &client,
		ProjectID: &f.project, SessionID: &sid, ExpectedRevision: revPtr(revision),
		Method: strptr("session.attach"), Payload: Bytes(Object{"request_write_owner": true, "after_sequence": 0})}
}

func attachContractComplete(t *testing.T, response *Response, state attachContractState, sid string) {
	t.Helper()
	if deref(response.Status) != "COMPLETED" || deref(response.SessionID) != sid ||
		response.Revision == nil || *response.Revision != state.revision || response.Result["write_owner_acquired"] != true {
		t.Fatalf("not a completed acquisition: %s", Bytes(response))
	}
	snapshot, ok := response.Result["snapshot"].(map[string]any)
	if !ok || Str(snapshot, "session_id") != sid || Str(snapshot, "model_config_ref") != state.model ||
		Str(snapshot, "workspace_ref") != state.workspace || Str(snapshot, "native_session_ref") != state.native {
		t.Fatalf("AttachResult changed session bindings: %s", Bytes(response))
	}
	writer, ok := snapshot["writer"].(map[string]any)
	epoch, _ := Num(writer, "epoch")
	revision, _ := Num(snapshot, "revision")
	sequence, _ := Num(snapshot, "event_sequence")
	if !ok || Str(writer, "client_id") != state.writer || Str(writer, "expires_at") != state.lease ||
		epoch != state.epoch || revision != state.revision || sequence != state.sequence {
		t.Fatalf("AttachResult does not describe committed state: %s", Bytes(response))
	}
}

func attachContractEventCount(t *testing.T, f *fixture, sid, command string) int {
	t.Helper()
	var count int
	if err := f.db.QueryRow("SELECT count(*) FROM outbox WHERE project=? AND json_extract(body,'$.session_id')=? AND json_extract(body,'$.kind')='CLIENT_HANDOFF' AND json_extract(body,'$.command_id')=?", f.project, sid, command).Scan(&count); err != nil {
		t.Fatal(err)
	}
	return count
}

func TestClientAttachValidOwnerRenewsWithoutGenerationChange(t *testing.T) {
	f := contextFixture(t)
	service, sid, _ := handlerTypedSession(t, f, "attach-owner")
	service.Host.LeaseTTL = 5 * time.Minute
	oldLease := time.Now().UTC().Add(time.Minute)
	if _, err := f.db.Exec("UPDATE client_sessions SET lease_expires_at=? WHERE id=?", oldLease.Format(time.RFC3339Nano), sid); err != nil {
		t.Fatal(err)
	}
	before := attachContractRead(t, f, sid)
	env := attachContractCommand(f, sid, before.writer, before.revision)
	first, replay := handlerCommand(t, f, service, env)
	after := attachContractRead(t, f, sid)
	attachContractComplete(t, first, after, sid)
	until, err := time.Parse(time.RFC3339Nano, after.lease)
	if err != nil || !until.After(oldLease) || replay || after.revision != before.revision ||
		after.epoch != before.epoch || after.sequence != before.sequence || after.writer != before.writer {
		t.Fatalf("renewal changed generation or failed to renew: before=%+v after=%+v err=%v", before, after, err)
	}
	again, replay := handlerCommand(t, f, service, env)
	if !replay || !bytes.Equal(Bytes(first), Bytes(again)) || attachContractRead(t, f, sid) != after ||
		attachContractEventCount(t, f, sid, deref(env.CommandID)) != 0 {
		t.Fatal("renewal replay repeated a lease write or fabricated handoff")
	}
}

func TestClientAttachSettledAcquisitionCompletesAndReplays(t *testing.T) {
	for _, mode := range []string{"unowned", "expired-same-owner", "other-client"} {
		t.Run(mode, func(t *testing.T) {
			f := contextFixture(t)
			service, sid, _ := handlerTypedSession(t, f, "attach-source")
			service.Host.LeaseTTL = 90 * time.Second
			client := "attach-source"
			switch mode {
			case "unowned":
				if _, err := f.db.Exec("UPDATE client_sessions SET writer_client_id='',lease_expires_at=NULL WHERE id=?", sid); err != nil {
					t.Fatal(err)
				}
			case "expired-same-owner":
				if _, err := f.db.Exec("UPDATE client_sessions SET lease_expires_at=? WHERE id=?", time.Now().UTC().Add(-time.Minute).Format(time.RFC3339Nano), sid); err != nil {
					t.Fatal(err)
				}
			case "other-client":
				client = "attach-target"
			}
			before := attachContractRead(t, f, sid)
			env := attachContractCommand(f, sid, client, before.revision)
			first, replay := handlerCommand(t, f, service, env)
			after := attachContractRead(t, f, sid)
			attachContractComplete(t, first, after, sid)
			until, err := time.Parse(time.RFC3339Nano, after.lease)
			if err != nil || !until.After(time.Now()) || replay || after.epoch != before.epoch+1 ||
				after.revision != before.revision+2 || after.sequence != before.sequence+1 || after.writer != client ||
				after.model != before.model || after.workspace != before.workspace || after.native != before.native {
				t.Fatalf("transfer state mismatch: before=%+v after=%+v err=%v", before, after, err)
			}
			if attachContractEventCount(t, f, sid, deref(env.CommandID)) != 1 {
				t.Fatal("missing unique CLIENT_HANDOFF")
			}
			again, replay := handlerCommand(t, f, service, env)
			if !replay || !bytes.Equal(Bytes(first), Bytes(again)) || attachContractRead(t, f, sid) != after ||
				attachContractEventCount(t, f, sid, deref(env.CommandID)) != 1 {
				t.Fatal("transfer replay changed state or duplicated handoff")
			}
			stale := attachContractCommand(f, sid, "competitor", before.revision)
			rejected, _ := handlerCommand(t, f, service, stale)
			if deref(rejected.ErrorCode) != "VERSION_CONFLICT" || attachContractRead(t, f, sid) != after {
				t.Fatal("stale competitor changed owner")
			}
		})
	}
}

func TestClientAttachPreservesStaleAndBindingGates(t *testing.T) {
	f := contextFixture(t)
	service, sid, _ := handlerTypedSession(t, f, "attach-binding")
	before := attachContractRead(t, f, sid)
	for _, mode := range []string{"stale-revision", "claimed-epoch", "wrong-project"} {
		env := attachContractCommand(f, sid, before.writer, before.revision)
		want := "VERSION_CONFLICT"
		switch mode {
		case "stale-revision":
			env.ExpectedRevision = revPtr(before.revision + 1)
		case "claimed-epoch":
			env.WriterEpoch = revPtr(before.epoch)
			want = "INVALID_REQUEST"
		case "wrong-project":
			env.ProjectID = strptr("wrong-project")
			want = "FORBIDDEN"
		}
		response, _ := handlerCommand(t, f, service, env)
		if deref(response.Status) != "REJECTED" || deref(response.ErrorCode) != want || attachContractRead(t, f, sid) != before {
			t.Fatalf("%s gate changed: %s", mode, Bytes(response))
		}
	}
	env := attachContractCommand(f, sid, before.writer, before.revision)
	first, _ := handlerCommand(t, f, service, env)
	after := attachContractRead(t, f, sid)
	attachContractComplete(t, first, after, sid)
	_, other, _ := handlerTypedSession(t, f, "attach-other-session")
	env.SessionID = &other
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		_, _, err := service.Execute(context.Background(), tx, handlerDecode(t, env), f.owner)
		if !errors.Is(err, ErrIdemConflict) {
			t.Fatalf("same command rebound to another session: %v", err)
		}
		return nil
	})
	if attachContractRead(t, f, sid) != after {
		t.Fatal("conflicting replay changed original session")
	}
	if _, err := f.db.Exec("UPDATE client_sessions SET model_config_ref='foreign-profile' WHERE id=?", sid); err != nil {
		t.Fatal(err)
	}
	send := &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: &after.writer,
		ProjectID: &f.project, SessionID: &sid, ExpectedRevision: revPtr(after.revision), WriterEpoch: revPtr(after.epoch),
		Method: strptr("session.send"), Payload: Bytes(Object{"text": "must refuse changed binding", "attachment_artifact_ids": Empty(), "delivery": "NORMAL"})}
	rejected, _ := handlerCommand(t, f, service, send)
	if deref(rejected.Status) != "REJECTED" || deref(rejected.ErrorCode) != "MODEL_UNAVAILABLE" {
		t.Fatalf("attach bypassed original session configuration binding: %s", Bytes(rejected))
	}
}

func TestClientAttachActiveOwnerRenewalDoesNotTransfer(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	task := o.task("attach-unsettled", Empty(), Empty())
	run := o.claim(task)
	service, sid, _ := handlerTypedSession(t, f, "attach-running-owner")
	if _, err := f.db.Exec("UPDATE client_sessions SET run_id=? WHERE id=?", Str(run.run, "id"), sid); err != nil {
		t.Fatal(err)
	}
	before := attachContractRead(t, f, sid)
	response, _ := handlerCommand(t, f, service, attachContractCommand(f, sid, before.writer, before.revision))
	after := attachContractRead(t, f, sid)
	attachContractComplete(t, response, after, sid)
	if after.epoch != before.epoch || after.revision != before.revision {
		t.Fatal("active owner renewal rotated writer")
	}
	rejected, _ := handlerCommand(t, f, service, attachContractCommand(f, sid, "attach-running-target", after.revision))
	if deref(rejected.ErrorCode) != "SESSION_BUSY" || attachContractRead(t, f, sid) != after {
		t.Fatalf("unsettled handoff changed ownership: %s", Bytes(rejected))
	}
	for _, status := range []string{"CANCELLED", "FAILED", "COMPLETED"} {
		if _, err := f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.status',?,'$.children_stopped',json('false'),'$.queue_empty',json('false')) WHERE project=? AND kind='Run' AND id=?", status, f.project, Str(run.run, "id")); err != nil {
			t.Fatal(err)
		}
		terminal, _ := handlerCommand(t, f, service, attachContractCommand(f, sid, "attach-terminal-target", after.revision))
		if deref(terminal.ErrorCode) != "SESSION_BUSY" || attachContractRead(t, f, sid) != after {
			t.Fatalf("terminal label replaced stop evidence: status=%s response=%s", status, Bytes(terminal))
		}
	}
}

// Reuse the existing production gate tests, which exercise exact stored profile,
// provider/runtime routing and Task-to-Session binding without starting a model.
// These are regression coverage, not proof of native end-to-end attach acceptance.
func TestClientAttachExistingRuntimeBindingRegressions(t *testing.T) {
	t.Run("stored-profile-and-runtime", TestHandlerRuntimeStoredProfileExactMapping)
	t.Run("exact-task-session", TestHandlerRuntimeTaskNeedsExactSession)
}
