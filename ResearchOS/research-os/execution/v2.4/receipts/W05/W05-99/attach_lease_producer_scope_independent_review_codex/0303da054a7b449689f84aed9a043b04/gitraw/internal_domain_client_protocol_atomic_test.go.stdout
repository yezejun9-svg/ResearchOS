package domain

import (
	"context"
	"database/sql"
	"testing"
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
