//go:build windows

package main

import (
	"context"
	"path/filepath"
	"testing"

	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/store"
	"researchos.local/research-os/ops/supervisor"
)

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
