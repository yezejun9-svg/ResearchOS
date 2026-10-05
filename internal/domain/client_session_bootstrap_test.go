package domain

import (
	"context"
	"testing"
	"time"
)

// This fixture runs the ordinary Service.New path, without a test-only Exec of
// next_v24_sessions.sql. Session UI first use relies on this production path.
func TestClientSessionSchemaInstalledOnOrdinaryStartup(t *testing.T) {
	f := setup(t)
	var count int
	if err := f.db.QueryRow("SELECT count(*) FROM client_sessions").Scan(&count); err != nil {
		t.Fatalf("ordinary startup did not install session schema: %v", err)
	}
	if count != 0 {
		t.Fatalf("startup invented sessions: %d", count)
	}
	if err := EnsureClientSessionFence(context.Background(), f.db); err != nil {
		t.Fatal(err)
	}
	if _, err := New(f.db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql"); err != nil {
		t.Fatalf("ordinary restart failed: %v", err)
	}
}

func TestOrdinaryStartupDoesNotInventRestoreBarrier(t *testing.T) {
	o := orchestrationSetup(t)
	task := o.task("ordinary-startup", []any{}, []any{})
	run := o.claim(task)
	runID := Str(run.run, "id")
	tx, err := o.f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	if err = MapClientSession(context.Background(), tx, ClientSession{
		ID: ID(), ProjectID: o.f.project, Revision: 1, CreatedAt: time.Now(), UpdatedAt: time.Now(),
		RunID: &runID, WriterEpoch: 1, WriterClientID: "startup-test", UpstreamSession: "startup-test",
		Protocol: ClientSessionProtocol,
	}); err != nil {
		tx.Rollback()
		t.Fatal(err)
	}
	if err = tx.Commit(); err != nil {
		t.Fatal(err)
	}
	if _, err = New(o.f.db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql"); err != nil {
		t.Fatal(err)
	}
	var count int
	if err = o.f.db.QueryRow("SELECT count(*) FROM backup_restore_barriers WHERE project=? AND run=?", o.f.project, runID).Scan(&count); err != nil {
		t.Fatal(err)
	}
	if count != 0 {
		t.Fatal("normal startup marked an active run as restored")
	}
}
