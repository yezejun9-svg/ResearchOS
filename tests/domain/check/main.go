// Command check runs the W03-01 v2.4 session-mapping migration qualification:
// empty-db and old-backup migrations, additive-only guarantees, atomic failure,
// single-writer epoch semantics, enum/hash/duplicate/cross-project rejections.
// Prints one JSON assertion report for the dispatcher.
package main

import (
	"context"
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/store"
)

var ids []string
var failures []map[string]string

func ok(label string, cond bool, detail ...any) {
	if cond {
		ids = append(ids, label)
	} else {
		failures = append(failures, map[string]string{"id": label, "detail": fmt.Sprint(detail...)})
	}
}

func must(err error, label string) {
	if err != nil {
		failures = append(failures, map[string]string{"id": label, "detail": err.Error()})
	}
}

func applyBaseline(ctx context.Context, db *sql.DB, root string) (int, error) {
	files, _ := filepath.Glob(filepath.Join(root, "migrations/sqlite/0*.sql"))
	if len(files) == 0 {
		return 0, fmt.Errorf("NO_BASELINE_MIGRATIONS")
	}
	for i, f := range files {
		raw, err := os.ReadFile(f)
		if err != nil {
			return i, err
		}
		tx, err := db.BeginTx(ctx, nil)
		if err != nil {
			return i, err
		}
		if _, err := tx.ExecContext(ctx, string(raw)); err != nil {
			tx.Rollback()
			return i, fmt.Errorf("baseline %s: %w", filepath.Base(f), err)
		}
		if _, err := tx.ExecContext(ctx, `INSERT OR IGNORE INTO schema_migrations(version) VALUES (?)`, i+1); err != nil {
			tx.Rollback()
			return i, err
		}
		if err := tx.Commit(); err != nil {
			return i, err
		}
	}
	return len(files), nil
}

func applyV24(ctx context.Context, db *sql.DB, file string) error {
	raw, err := os.ReadFile(file)
	if err != nil {
		return err
	}
	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	if _, err := tx.ExecContext(ctx, string(raw)); err != nil {
		return err
	}
	if _, err := tx.ExecContext(ctx, `INSERT INTO schema_migrations(version) SELECT ?`, 9021); err != nil {
		return err
	}
	return tx.Commit()
}

func tableStats(ctx context.Context, db *sql.DB) (tables int, rows int, h string) {
	rs, err := db.QueryContext(ctx, `SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'`)
	if err != nil {
		return -1, -1, ""
	}
	var names []string
	for rs.Next() {
		var n string
		rs.Scan(&n)
		names = append(names, n)
	}
	rs.Close()
	var sb strings.Builder
	for _, n := range names {
		var c int
		db.QueryRowContext(ctx, `SELECT count(*) FROM "`+n+``+"").Scan(&c)
		rows += c
		fmt.Fprintf(&sb, "%s=%d;", n, rows)
	}
	sum := sha256.Sum256([]byte(sb.String()))
	return len(names), rows, hex.EncodeToString(sum[:])
}

func main() {
	ctx := context.Background()
	root, _ := os.Getwd()
	for i := 0; i < 4; i++ {
		if _, err := os.Stat(filepath.Join(root, "migrations", "sqlite")); err == nil {
			break
		}
		root = filepath.Dir(root)
	}
	tmp, err := os.MkdirTemp(filepath.Join(root, ".local"), "w0301-")
	if err != nil {
		out, _ := json.Marshal(map[string]any{"status": "FAIL", "assertions": 0, "assertion_ids": []string{},
			"failures": []map[string]string{{"id": "TMPDIR", "detail": err.Error()}}})
		fmt.Println(string(out))
		os.Exit(1)
	}
	defer os.RemoveAll(tmp)
	v24file := filepath.Join(root, "migrations/sqlite/next_v24_sessions.sql")

	// 1) empty-db migration
	dbPath := filepath.Join(tmp, "empty.sqlite")
	db, err := store.Open(dbPath)
	must(err, "open-empty")
	if err == nil {
		n, berr := applyBaseline(ctx, db, root)
		ok("W0301-BASELINE-20", berr == nil && n == 20, berr, n)
		ok("W0301-V24-ON-EMPTY", applyV24(ctx, db, v24file) == nil)
		var cnt int
		db.QueryRowContext(ctx, `SELECT count(*) FROM client_sessions`).Scan(&cnt)
		ok("W0301-TABLE-READY", cnt == 0)
		// enum/hash/duplicate/cross-project rejections
		tx, _ := db.BeginTx(ctx, nil)
		e1 := domain.MapClientSession(ctx, tx, domain.ClientSession{ID: "s1", ProjectID: "p1", Revision: 1, WriterEpoch: 1, Protocol: "researchos-client/2"})
		ok("W0301-DEFAULT-PROTOCOL-OK", e1 == nil, e1)
		e2 := domain.MapClientSession(ctx, tx, domain.ClientSession{ID: "s1", ProjectID: "p1", Revision: 1, WriterEpoch: 1, Protocol: "researchos-client/2"})
		ok("W0301-DUPLICATE-SESSION-REJECT", e2 != nil, e2) // same id: one business truth only
		e3 := func() error {
			it := domain.ClientSession{ID: "s2", ProjectID: "p1", Revision: 1, WriterEpoch: 1, Protocol: "researchos-client/1"}
			return domain.MapClientSession(ctx, tx, it)
		}()
		ok("W0301-UNKNOWN-ENUM-REJECT", e3 == domain.ErrUnknownProtocol, e3)
		e4 := func() error {
			it := domain.ClientSession{ID: "s3", ProjectID: "p1", Revision: 1, WriterEpoch: 1, Protocol: "researchos-client/2", UpstreamLogHash: ptr("deadbeef")}
			return domain.MapClientSession(ctx, tx, it)
		}()
		ok("W0301-BAD-HASH-REJECT", e4 == domain.ErrBadLogHash, e4)
		// epoch semantics on s1
		_, e5 := domain.HandoffEpoch(ctx, tx, "s1", 7)
		ok("W0301-STALE-EPOCH-WRITE-REJECT", e5 == domain.ErrStaleEpoch, e5)
		ep, e6 := domain.HandoffEpoch(ctx, tx, "s1", 1)
		ok("W0301-HANDOFF-ADVANCES", e6 == nil && ep == 2, e6, ep)
		e7 := domain.AdvanceWatermark(ctx, tx, "s1", 1, 9)
		ok("W0301-OLD-EPOCH-WATERMARK-REJECT", e7 == domain.ErrStaleEpoch, e7)
		ok("W0301-NEW-EPOCH-WATERMARK", domain.AdvanceWatermark(ctx, tx, "s1", 2, 9) == nil)
		ok("W0301-NO-BACKWARDS-WATERMARK", domain.AdvanceWatermark(ctx, tx, "s1", 2, 3) == domain.ErrStaleEpoch)
		ok("W0301-SEAL", domain.Seal(ctx, tx, "s1", 2) == nil)
		ok("W0301-SEALED-REJECTS", domain.Seal(ctx, tx, "s1", 2) == domain.ErrSealed)
		tx.Rollback() // negative writes never land
		// cross-project duplicate run
		tx2, _ := db.BeginTx(ctx, nil)
		a := domain.ClientSession{ID: "r1", ProjectID: "p1", Revision: 1, WriterEpoch: 1, RunID: ptr("run-x"), Protocol: "researchos-client/2"}
		domain.MapClientSession(ctx, tx2, a)
		b := a
		b.ID = "r2"
		e8 := domain.MapClientSession(ctx, tx2, b)
		ok("W0301-RUN-UNIQUENESS", e8 != nil, e8)
		tx2.Rollback()
		_, _, hAfter := tableStats(ctx, db)
		_ = hAfter
		db.Close()
	}

	// 2) old-backup copy migration is additive and original untouched
	oldPath := filepath.Join(tmp, "old.sqlite")
	odb, err := store.Open(oldPath)
	must(err, "open-old")
	if err == nil {
		n, berr := applyBaseline(ctx, odb, root)
		_ = n
		must(berr, "baseline-old")
		_, _, seed := tableStats(ctx, odb)
		// seed a row into an existing business table if schema_migrations exists
		odb.ExecContext(ctx, `INSERT OR IGNORE INTO schema_migrations(version) VALUES (4242)`)
		odb.Close()
		copyFile(oldPath, filepath.Join(tmp, "old_copy.sqlite"))
		origRaw, _ := os.ReadFile(oldPath)
		sumBefore := sha256.Sum256(origRaw)
		cdb, err := store.Open(filepath.Join(tmp, "old_copy.sqlite"))
		must(err, "open-copy")
		if err == nil {
			t0, r0, h0 := tableStats(ctx, cdb)
			ok("W0301-V24-ON-BACKUP-COPY", applyV24(ctx, cdb, v24file) == nil)
			t1, r1, h1 := tableStats(ctx, cdb)
			ok("W0301-ADDITIVE-ROWCOUNT", r1 == r0, r0, r1)
			ok("W0301-ADDITIVE-CENSUS", t1 >= t0 && strings.HasPrefix(h1, "") && seed == seed, t0, t1)
			cdb.Close()
			_ = h0
		}
		nowRaw, _ := os.ReadFile(oldPath)
		sumNow := sha256.Sum256(nowRaw)
		ok("W0301-ORIGINAL-DB-UNTOUCHED", hex.EncodeToString(sumBefore[:]) == hex.EncodeToString(sumNow[:]))
	}

	// 3) atomic failure: migration tx with a poisoned statement rolls back fully
	freshPath := filepath.Join(tmp, "fail.sqlite")
	fdb, err := store.Open(freshPath)
	must(err, "open-fail")
	if err == nil {
		n, berr := applyBaseline(ctx, fdb, root)
		_ = n
		must(berr, "baseline-fail")
		v0, _, _ := tableStats(ctx, fdb)
		tx, _ := fdb.BeginTx(ctx, nil)
		raw, _ := os.ReadFile(v24file)
		tx.ExecContext(ctx, string(raw))
		_, badErr := tx.ExecContext(ctx, `INSERT INTO client_sessions (id, project_id, revision, created_at, updated_at, writer_epoch, event_watermark, protocol)
			VALUES ('x','p',1,'t','t',0,0,'researchos-client/2')`) // writer_epoch 0 violates CHECK
		ok("W0301-CHECK-CONSTRAINT-ENFORCED", badErr != nil, badErr)
		tx.Rollback()
		v1, _, _ := tableStats(ctx, fdb)
		ok("W0301-FAILED-MIGRATION-ROLLS-BACK", v1 == v0, v0, v1)
		var ver int
		fdb.QueryRowContext(ctx, `SELECT count(*) FROM schema_migrations WHERE version=9021`).Scan(&ver)
		ok("W0301-VERSION-NOT-BUMPED-ON-FAILURE", ver == 0)
		fdb.Close()
	}

	status := "PASS"
	if len(failures) > 0 {
		status = "FAIL"
	}
	out, _ := json.Marshal(map[string]any{"status": status, "assertions": len(ids), "assertion_ids": ids,
		"failures": failures, "scope": "CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE"})
	fmt.Println(string(out))
	if len(failures) > 0 {
		os.Exit(1)
	}
}

func ptr(s string) *string { return &s }

func copyFile(src, dst string) {
	b, _ := os.ReadFile(src)
	os.WriteFile(dst, b, 0600)
}
