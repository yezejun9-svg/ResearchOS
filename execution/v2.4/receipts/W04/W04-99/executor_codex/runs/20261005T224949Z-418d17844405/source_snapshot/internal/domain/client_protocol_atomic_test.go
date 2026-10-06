package domain

import (
	"context"
	"database/sql"
	"testing"
)

type rejectingClientPort struct{}

func (rejectingClientPort) ValidateBinding(ctx context.Context, tx *sql.Tx, _, _, _, _ string) error {
	if _, err := tx.ExecContext(ctx, "INSERT INTO rejected_command_probe(value) VALUES('partial write')"); err != nil {
		return err
	}
	return Fail(503, "MODEL_UNAVAILABLE", "fixture refusal after an intermediate write")
}
func (rejectingClientPort) AdmitTurn(context.Context, *sql.Tx, string, string, Object) error {
	return nil
}

func TestClientTypedRejectionRollsBackBusinessWrites(t *testing.T) {
	f := contextFixture(t)
	if _, err := f.db.Exec("CREATE TABLE rejected_command_probe(value TEXT)"); err != nil {
		t.Fatal(err)
	}
	b := WorkspaceBinding{AuthorizedRef: "atomic-workspace", DisplayName: "fixture", DisplayPath: "fixture", RealPath: t.TempDir(), Access: "READ_ONLY", ProjectID: &f.project, Revision: 1, Status: WorkspaceActive, PrincipalID: f.owner, ClientID: "atomic-client", HostPrincipalRef: "fixture", CreatedAt: Now()}
	if _, err := f.db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('',?,?,1,?,0)`, KindWorkspaceBinding, b.AuthorizedRef, string(Bytes(b))); err != nil {
		t.Fatal(err)
	}
	svc := &ClientService{Domain: f.s, SessionRuntime: rejectingClientPort{}}
	env := &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("atomic-client"), ProjectID: &f.project, Method: strptr("session.create"), Payload: Bytes(Object{"workspace_ref": b.AuthorizedRef, "model_config_ref": "unavailable", "title": "refused"})}
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
	var count int
	if err := f.db.QueryRow("SELECT count(*) FROM rejected_command_probe").Scan(&count); err != nil || count != 0 {
		t.Fatalf("rejected command committed %d intermediate writes: %v", count, err)
	}
	if err := f.db.QueryRow("SELECT count(*) FROM idempotency WHERE key=?", deref(env.CommandID)).Scan(&count); err != nil || count != 1 {
		t.Fatalf("rejection was not committed once: %d %v", count, err)
	}
}
