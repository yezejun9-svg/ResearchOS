//go:build windows

package main

import (
	"context"
	"os"
	"path/filepath"
	"testing"
	"time"

	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/store"
	"researchos.local/research-os/ops/supervisor"
)

func TestActualReleasePrivateActionsExplicitlyClosed(t *testing.T) {
	peer, e := supervisor.ObserveProcess(uint32(os.Getpid()))
	if e != nil {
		t.Fatal(e)
	}
	name, e := supervisor.NewDrainPipeName()
	if e != nil {
		t.Fatal(e)
	}
	key := make([]byte, 32)
	root := t.TempDir()
	d := &controlDrain{startup: &supervisor.DrainBootstrap{FixtureStore: "inherited-fixture-locator"}, pipe: name, root: root, key: key, peer: peer}
	for _, kind := range []string{"FIXTURE_SEAL", "FIXTURE_CURRENT", "FIXTURE_DISPATCH", "FIXTURE_CUTOVER", "FIXTURE_PROJECT"} {
		ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
		done := make(chan error, 1)
		go func() { done <- d.handle(ctx) }()
		c, err := supervisor.DialDrainPipe(name, peer)
		if err != nil {
			cancel()
			t.Fatal(err)
		}
		if err = c.SetDeadline(time.Now().Add(3 * time.Second)); err != nil {
			c.Close()
			cancel()
			t.Fatal(err)
		}
		frame, err := supervisor.DrainFrameSign(key, supervisor.DrainFrame{Kind: kind, Root: root, Operation: "old-calculator-proof", Epoch: 1, Nonce: "test-bound-nonce", Release: &supervisor.ReleasePrivateMessage{}})
		if err == nil {
			err = supervisor.WriteDrainFrame(c, frame)
		}
		if err != nil {
			c.Close()
			cancel()
			t.Fatal(err)
		}
		reply, err := supervisor.ReadDrainFrame(c)
		c.Close()
		cancel()
		if serverErr := <-done; serverErr != nil {
			t.Fatal(serverErr)
		}
		if err != nil || !supervisor.DrainFrameValid(key, reply) || reply.Kind != kind || reply.Release == nil || reply.Release.Error != "ACTUAL_CONTROL_BEHAVIOR_PROOF_UNAVAILABLE" {
			t.Fatalf("%s actual profile gate open: %+v %v", kind, reply, err)
		}
	}
	t.Log("all five authenticated actual-control private release actions explicitly closed; no domain DB invoked; READY/drain/normal-exit protocol unchanged")
}

func TestControlDrainCheckpointBusyRestoresWrites(t *testing.T) {
	root := t.TempDir()
	path := filepath.Join(root, "researchos.sqlite")
	db, e := store.Open(path)
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	if e = store.Bootstrap(context.Background(), db, "../../migrations/sqlite/0001_bootstrap.sql"); e != nil {
		t.Fatal(e)
	}
	svc, e := domain.New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if e != nil {
		t.Fatal(e)
	}
	reader, e := store.Open(path)
	if e != nil {
		t.Fatal(e)
	}
	defer reader.Close()
	tx, e := reader.Begin()
	if e != nil {
		t.Fatal(e)
	}
	defer tx.Rollback()
	var count int
	if e = tx.QueryRow("SELECT count(*) FROM domain_objects").Scan(&count); e != nil {
		t.Fatal(e)
	}
	if _, e = db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body) VALUES('fixture','Artifact','checkpoint-pin',1,'{}'); PRAGMA busy_timeout=25`); e != nil {
		t.Fatal(e)
	}
	d := &controlDrain{gate: &drainGate{}, service: svc, root: root}
	frame := supervisor.DrainFrame{Operation: "fixture", Epoch: 1, Nonce: "fixture-nonce"}
	if _, e = d.quiesce(context.Background(), frame); e == nil {
		t.Fatal("busy FULL checkpoint acknowledged")
	}
	if d.gate.quiesced || d.operation != "" {
		t.Fatal("busy checkpoint left a partial drain fence")
	}
	if e = tx.Rollback(); e != nil {
		t.Fatal(e)
	}
	if _, e = d.quiesce(context.Background(), frame); e != nil {
		t.Fatal(e)
	}
	if !d.gate.quiesced || d.receipt == "" {
		t.Fatal("idle checkpoint omitted quiesce receipt")
	}
	t.Log("actual SQLite pinned-reader checkpoint busy refuses drain and restores writes; released reader allows quiesce")
}
