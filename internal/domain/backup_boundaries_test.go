package domain

import (
	"bytes"
	"context"
	"os"
	"path/filepath"
	"researchos.local/research-os/internal/store"
	"testing"
	"time"
)

func TestW18Boundaries(t *testing.T) {
	ctx := context.Background()
	o := orchestrationSetup(t)
	f := o.f
	r := o.claim(o.task("cancel-must-survive-restore", Empty(), Empty()))
	resourceCheckpoint(r, Object{"point": "before pending cancellation"})
	r.observe(r.observation("LOST", false))
	f.token = o.owner
	r.run = f.expect(200, "POST", f.path("/runs/"+Str(r.run, "id")+"/cancel"), ID(), testTag(r.run), Object{"reason": "preserve explicit stop"})
	key := backupTestKey(t)
	dir, m := backupTestCreate(t, f.s, key)
	plaintextFound := false
	entries, e := os.ReadDir(dir)
	if e != nil {
		t.Fatal(e)
	}
	for _, entry := range entries {
		raw, e := os.ReadFile(filepath.Join(dir, entry.Name()))
		if e != nil {
			t.Fatal(e)
		}
		if bytes.Contains(raw, []byte(f.token)) || bytes.Contains(raw, []byte(r.lease)) || bytes.Contains(raw, key) {
			plaintextFound = true
		}
	}
	backupAssert(t, "W18-G01-ENCRYPTION", false, plaintextFound, Object{"encrypted_files": len(m.Files), "separate_key": true})
	target := filepath.Join(t.TempDir(), "restore")
	_, e = RestoreBackup(ctx, dir, target, backupOpt(t, f.s, key))
	if e != nil {
		t.Fatal(e)
	}
	db, e := store.Open(filepath.Join(target, "state.sqlite"))
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	s := &Service{DB: db, Contracts: f.s.Contracts}
	token, e := s.IssueCredential(ctx, f.owner, time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	var status string
	var revision int64
	if e = db.QueryRow("SELECT json_extract(body,'$.status'),revision FROM domain_objects WHERE kind='Run' AND id=?", r.run["id"]).Scan(&status, &revision); e != nil {
		t.Fatal(e)
	}
	_, resumeErr := s.ResumeCheckpoint(ctx, token, f.project, Str(r.run, "id"), "cancel-restore-probe", revision)
	backupAssert(t, "W18-G01-CANCELLATION", true, status == "CANCEL_REQUESTED" && resumeErr != nil, Object{"status": status, "resume_error": resumeErr.Error()})
	_, keyErr := RestoreBackup(ctx, dir, filepath.Join(t.TempDir(), "missing-key"), backupOpt(t, f.s, nil))
	backupAssert(t, "W18-G01-KEY-UNAVAILABLE", true, keyErr != nil, Object{"error": keyErr.Error()})
	guardErr := CheckMigrationSafety(f.db, []string{"9999_candidate.sql"})
	migration := filepath.Join(t.TempDir(), "9999_candidate.sql")
	if e = os.WriteFile(migration, []byte("CREATE TABLE should_not_migrate(x);"), 0600); e != nil {
		t.Fatal(e)
	}
	_, startupErr := New(f.db, "../../spec/v2.0/contracts", migration)
	var mutated int
	if e = f.db.QueryRow("SELECT count(*) FROM sqlite_master WHERE name='should_not_migrate'").Scan(&mutated); e != nil {
		t.Fatal(e)
	}
	backupAssert(t, "A12-03-MIGRATION-PREFLIGHT", true, guardErr != nil && startupErr != nil && mutated == 0,
		Object{"direct_guard_rejected": guardErr != nil, "startup_rejected": startupErr != nil, "migration_applied": mutated != 0})
	protected := f.artifact(Object{"protected": "fixture secret boundary"}, Empty())
	protected["id"] = ID()
	protected["kind"] = "LOG"
	protected["access_class"] = "VERIFIER_ONLY"
	tx, e := f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	if e = f.s.put(tx, "Artifact", protected); e != nil {
		tx.Rollback()
		t.Fatal(e)
	}
	if e = tx.Commit(); e != nil {
		t.Fatal(e)
	}
	protectedTarget := filepath.Join(t.TempDir(), "denied")
	_, protectedErr := f.s.CreateBackup(ctx, protectedTarget, key)
	_, statErr := os.Stat(protectedTarget)
	backupAssert(t, "W18-G01-PROTECTED-CONTENT", true, protectedErr != nil && os.IsNotExist(statErr), Object{"error": protectedErr.Error(), "published": !os.IsNotExist(statErr)})
}
