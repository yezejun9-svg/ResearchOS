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

func TestClientTranscriptIndexUpgradesExistingSessionTable(t *testing.T) {
	for _, restored := range []bool{false, true} {
		name := "ordinary"
		if restored {
			name = "restore"
		}
		t.Run(name, func(t *testing.T) {
			f := contextFixture(t)
			ctx := context.Background()
			if _, err := f.db.Exec(`ALTER TABLE client_sessions DROP COLUMN transcript_artifact_id`); err != nil {
				t.Fatal(err)
			}
			tx, err := f.db.Begin()
			if err != nil {
				t.Fatal(err)
			}
			id := ID()
			if err = MapClientSession(ctx, tx, ClientSession{
				ID: id, ProjectID: f.project, Revision: 7, CreatedAt: time.Now(), UpdatedAt: time.Now(),
				WriterEpoch: 3, WriterClientID: "transcript-upgrade", EventWatermark: 19,
				UpstreamSession: "existing-session", Protocol: ClientSessionProtocol,
			}); err != nil {
				tx.Rollback()
				t.Fatal(err)
			}
			if err = tx.Commit(); err != nil {
				t.Fatal(err)
			}
			for i := 0; i < 2; i++ {
				if restored {
					err = EnsureClientSessionFence(ctx, f.db)
				} else {
					_, err = New(f.db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
				}
				if err != nil {
					t.Fatalf("upgrade %d: %v", i, err)
				}
			}
			var project, writer, upstream string
			var revision, epoch, watermark int
			var transcript any
			if err = f.db.QueryRow(`SELECT project_id,revision,writer_epoch,event_watermark,writer_client_id,upstream_session_id,transcript_artifact_id FROM client_sessions WHERE id=?`, id).
				Scan(&project, &revision, &epoch, &watermark, &writer, &upstream, &transcript); err != nil {
				t.Fatal(err)
			}
			if project != f.project || revision != 7 || epoch != 3 || watermark != 19 || writer != "transcript-upgrade" || upstream != "existing-session" || transcript != nil {
				t.Fatalf("upgrade changed existing session: %s %d %d %d %s %s %v", project, revision, epoch, watermark, writer, upstream, transcript)
			}
			var count int
			if err = f.db.QueryRow(`SELECT count(*) FROM client_sessions`).Scan(&count); err != nil || count != 1 {
				t.Fatalf("upgrade invented a session: %d %v", count, err)
			}
		})
	}
}

func TestClientTranscriptIndexUpgradeRollsBackWithCallerTransaction(t *testing.T) {
	f := setup(t)
	ctx := context.Background()
	if _, err := f.db.Exec(`ALTER TABLE client_sessions DROP COLUMN transcript_artifact_id`); err != nil {
		t.Fatal(err)
	}
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback()
	if err = installClientSessionFence(ctx, tx, false); err != nil {
		t.Fatal(err)
	}
	var count int
	if err = tx.QueryRow(`SELECT count(*) FROM pragma_table_info('client_sessions') WHERE name='transcript_artifact_id'`).Scan(&count); err != nil || count != 1 {
		t.Fatalf("transaction did not install column: %d %v", count, err)
	}
	if err = tx.Rollback(); err != nil {
		t.Fatal(err)
	}
	if err = f.db.QueryRow(`SELECT count(*) FROM pragma_table_info('client_sessions') WHERE name='transcript_artifact_id'`).Scan(&count); err != nil || count != 0 {
		t.Fatalf("rollback kept column: %d %v", count, err)
	}
}
