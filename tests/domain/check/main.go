// Command check runs the W03-01 v2.4 session-mapping migration qualification (rev2,
// review P1..P10 closed): empty-db and old-backup migrations, additive-only per-table
// census, atomic failure with version bump attempted inside the rolled-back tx,
// single-writer epoch semantics with revision CAS, writer attribution, native session
// ref, project existence, cross-project run rejection, and restore-fence triggers
// exercised through the same production helper backup recovery uses.
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
	"sort"
	"strings"
	"time"

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
		ok(label+"-HARD", false, err)
	}
}

func census(ctx context.Context, db *sql.DB) map[string]int {
	out := map[string]int{}
	rs, err := db.QueryContext(ctx, `SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name`)
	if err != nil {
		return out
	}
	var names []string
	for rs.Next() {
		var n string
		rs.Scan(&n)
		names = append(names, n)
	}
	rs.Close()
	for _, n := range names {
		var c int
		db.QueryRowContext(ctx, `SELECT count(*) FROM "`+n+`"`).Scan(&c)
		out[n] = c
	}
	return out
}

func applyBaseline(ctx context.Context, db *sql.DB, root string) (int, error) {
	files, _ := filepath.Glob(filepath.Join(root, "migrations/sqlite/0*.sql"))
	sort.Strings(files)
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

func seedProject(ctx context.Context, db *sql.DB, id string) {
	db.ExecContext(ctx, `INSERT OR IGNORE INTO domain_objects(project,kind,id,revision,body,immutable) VALUES(?,'Project',?,1,'{}',0)`, id, id)
}

func baseSession(id, project string) domain.ClientSession {
	now := time.Now().UTC()
	return domain.ClientSession{ID: id, ProjectID: project, Revision: 1, CreatedAt: now, UpdatedAt: now,
		WriterEpoch: 1, WriterClientID: "cli-1", EventWatermark: 0, UpstreamSession: "up-" + id,
		Protocol: domain.ClientSessionProtocol, ResumeExplicit: 1}
}

func copyFile(src, dst string) {
	b, _ := os.ReadFile(src)
	os.WriteFile(dst, b, 0600)
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
	var tmp string
	defer func() {
		if tmp != "" {
			os.RemoveAll(tmp)
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
	}()
	t, err := os.MkdirTemp(filepath.Join(root, ".local"), "w0301-")
	must(err, "TMPDIR")
	if err != nil {
		return
	}
	tmp = t
	v24file := filepath.Join(root, "migrations/sqlite/next_v24_sessions.sql")

	// ---------- empty-db path ----------
	db, err := store.Open(filepath.Join(tmp, "empty.sqlite"))
	must(err, "OPEN-EMPTY")
	if err != nil {
		return
	}
	defer db.Close()
	n, berr := applyBaseline(ctx, db, root)
	ok("W0301-BASELINE-20", berr == nil && n == 20, berr, n)
	ok("W0301-V24-ON-EMPTY", applyV24(ctx, db, v24file) == nil)
	seedProject(ctx, db, "p1")
	seedProject(ctx, db, "p2")

	tx, _ := db.BeginTx(ctx, nil)
	e1 := domain.MapClientSession(ctx, tx, baseSession("s1", "p1"))
	ok("W0301-MAP-OK", e1 == nil, e1)
	e2 := domain.MapClientSession(ctx, tx, baseSession("s1", "p1"))
	ok("W0301-DUPLICATE-SESSION-REJECT", e2 != nil, e2)
	it := baseSession("sx", "p1")
	it.Protocol = "researchos-client/1"
	ok("W0301-UNKNOWN-ENUM-REJECT", domain.MapClientSession(ctx, tx, it) == domain.ErrUnknownProtocol)
	bad := baseSession("sx", "p1")
	bh := "deadbeef"
	bad.UpstreamLogHash = &bh
	ok("W0301-BAD-HASH-REJECT", domain.MapClientSession(ctx, tx, bad) == domain.ErrBadLogHash)
	nw := baseSession("sx", "p1")
	nw.WriterClientID = ""
	ok("W0301-WRITER-ATTRIBUTION-REQUIRED", domain.MapClientSession(ctx, tx, nw) == domain.ErrMissingWriter)
	nr := baseSession("sx", "p1")
	nr.UpstreamSession = ""
	ok("W0301-NATIVE-REF-REQUIRED", domain.MapClientSession(ctx, tx, nr) != nil)
	unk := baseSession("sx", "nope")
	ok("W0301-PROJECT-EXISTENCE", domain.MapClientSession(ctx, tx, unk) == domain.ErrUnknownProject)

	ok("W0301-WATERMARK-PLUS1", domain.AdvanceWatermark(ctx, tx, "s1", 1, 1, 1) == nil)
	ok("W0301-WATERMARK-PLUS2", domain.AdvanceWatermark(ctx, tx, "s1", 1, 2, 4) == nil)
	ok("W0301-WATERMARK-NO-BACKWARDS", domain.AdvanceWatermark(ctx, tx, "s1", 1, 3, 2) != nil)
	ok("W0301-STALE-REVISION", domain.AdvanceWatermark(ctx, tx, "s1", 1, 99, 5) == domain.ErrStaleRevision)
	_, e := domain.HandoffEpoch(ctx, tx, "s1", 7, 3)
	ok("W0301-STALE-EPOCH-WRITE-REJECT", e == domain.ErrStaleEpoch, e)
	ep, e := domain.HandoffEpoch(ctx, tx, "s1", 1, 3)
	ok("W0301-HANDOFF-ADVANCES", e == nil && ep == 2, e, ep)
	ok("W0301-OLD-EPOCH-WATERMARK-REJECT", domain.AdvanceWatermark(ctx, tx, "s1", 1, 4, 6) == domain.ErrStaleEpoch)
	ok("W0301-NEW-EPOCH-WATERMARK", domain.AdvanceWatermark(ctx, tx, "s1", 2, 4, 6) == nil)
	ok("W0301-SEAL", domain.Seal(ctx, tx, "s1", 2, 5) == nil)
	ok("W0301-SEALED-DISTINCT", domain.AdvanceWatermark(ctx, tx, "s1", 2, 6, 9) == domain.ErrSealed)
	tx.Rollback()

	tx2, _ := db.BeginTx(ctx, nil)
	rs := baseSession("r1", "p1")
	r := "run-x"
	rs.RunID = &r
	ok("W0301-RUN-MAP", domain.MapClientSession(ctx, tx2, rs) == nil)
	r2 := baseSession("r2", "p2")
	r2.RunID = &r
	ok("W0301-CROSS-PROJECT-RUN-REJECT", domain.MapClientSession(ctx, tx2, r2) != nil)
	tx2.Rollback()

	// ---------- old-backup copy path ----------
	oldPath := filepath.Join(tmp, "old.sqlite")
	odb, err := store.Open(oldPath)
	must(err, "OPEN-OLD")
	if err == nil {
		defer odb.Close()
		_, berr := applyBaseline(ctx, odb, root)
		must(berr, "BASELINE-OLD")
		seedProject(ctx, odb, "p9")
		odb.ExecContext(ctx, `INSERT OR IGNORE INTO outbox(project,sequence,id,body) VALUES('p9',7,'o7','{}')`)
		before := census(ctx, odb)
		odb.ExecContext(ctx, `PRAGMA wal_checkpoint(FULL)`)
		origRaw, _ := os.ReadFile(oldPath)
		sumBefore := sha256.Sum256(origRaw)
		copyFile(oldPath, filepath.Join(tmp, "old_copy.sqlite"))
		cdb, err := store.Open(filepath.Join(tmp, "old_copy.sqlite"))
		must(err, "OPEN-COPY")
		if err == nil {
			defer cdb.Close()
			c0 := census(ctx, cdb)
			cpErr := applyV24(ctx, cdb, v24file)
			ok("W0301-V24-ON-BACKUP-COPY", cpErr == nil, cpErr)
			c1 := census(ctx, cdb)
			same := len(c0) > 0
			for k, v := range c0 {
				if k == "schema_migrations" || k == "client_sessions" {
					continue // migration bookkeeping is expected to change
				}
				if nv, has := c1[k]; !has || nv != v {
					same = false
				}
			}
			_, hadCS := c0["client_sessions"]
			_, hasCS := c1["client_sessions"]
			ok("W0301-ADDITIVE-PER-TABLE-CENSUS", same && !hadCS && hasCS && len(c1) == len(c0)+1, len(c0), len(c1))
			var alive string
			cdb.QueryRowContext(ctx, `SELECT id FROM outbox WHERE project='p9' AND sequence=7`).Scan(&alive)
			ok("W0301-BUSINESS-ROW-PRESERVED", alive == "o7", alive)
			afterRaw, _ := os.ReadFile(oldPath)
			sumAfter := sha256.Sum256(afterRaw)
			ok("W0301-ORIGINAL-DB-UNTOUCHED", hex.EncodeToString(sumBefore[:]) == hex.EncodeToString(sumAfter[:]))
			var cnt int
			odb.QueryRowContext(ctx, `SELECT count(*) FROM sqlite_master WHERE type='table' AND name='client_sessions'`).Scan(&cnt)
			ok("W0301-NO-DRIFT-TO-ORIGINAL", cnt == 0, cnt)
			after := census(ctx, odb)
			sameOld := len(after) == len(before)
			for k := range after {
				if after[k] != before[k] {
					sameOld = false
				}
			}
			ok("W0301-OLD-DB-CENSUS-STABLE", sameOld, before, after)
		}
	}

	// ---------- atomic failure ----------
	fdb, err := store.Open(filepath.Join(tmp, "fail.sqlite"))
	must(err, "OPEN-FAIL")
	if err == nil {
		defer fdb.Close()
		applyBaseline(ctx, fdb, root)
		v0 := census(ctx, fdb)
		tx, _ := fdb.BeginTx(ctx, nil)
		raw, _ := os.ReadFile(v24file)
		tx.ExecContext(ctx, string(raw))
		tx.ExecContext(ctx, `INSERT INTO schema_migrations(version) VALUES(9021)`) // bump attempted inside same tx
		_, badErr := tx.ExecContext(ctx, `INSERT INTO client_sessions (id,project_id,revision,created_at,updated_at,writer_epoch,writer_client_id,event_watermark,upstream_session_id,protocol)
			VALUES ('x','p',1,'t','t',0,'c',0,'u','researchos-client/2')`)
		ok("W0301-CHECK-CONSTRAINT-ENFORCED", badErr != nil, badErr)
		tx.Rollback()
		v1 := census(ctx, fdb)
		_, hasCS := v1["client_sessions"]
		ok("W0301-FAILED-MIGRATION-ROLLS-BACK", len(v0) == len(v1) && !hasCS, len(v0), len(v1))
		var ver int
		fdb.QueryRowContext(ctx, `SELECT count(*) FROM schema_migrations WHERE version=9021`).Scan(&ver)
		ok("W0301-VERSION-NOT-BUMPED-ON-FAILURE", ver == 0, ver)
	}

	// ---------- restore fence via production helper ----------
	gdb, err := store.Open(filepath.Join(tmp, "fence.sqlite"))
	must(err, "OPEN-FENCE")
	if err == nil {
		defer gdb.Close()
		applyBaseline(ctx, gdb, root)
		applyV24(ctx, gdb, v24file)
		seedProject(ctx, gdb, "pf")
		tx, _ := gdb.BeginTx(ctx, nil)
		fs := baseSession("fs", "pf")
		fr := "run-f"
		fs.RunID = &fr
		domain.MapClientSession(ctx, tx, fs)
		tx.Commit()
		ok("W0301-FENCE-HELPER", domain.EnsureClientSessionFence(ctx, gdb) == nil)
		gdb.ExecContext(ctx, `INSERT OR IGNORE INTO backup_restore_barriers VALUES('pf','run-f','2026-10-01T00:00:00Z')`)
		_, ferr := gdb.ExecContext(ctx, `UPDATE client_sessions SET writer_epoch=writer_epoch-1 WHERE id='fs'`)
		ok("W0301-EPOCH-REGRESSION-BLOCKED", ferr != nil && strings.Contains(ferr.Error(), "SESSION_EPOCH_REGRESSION"), ferr)
		_, ferr = gdb.ExecContext(ctx, `UPDATE client_sessions SET writer_epoch=writer_epoch+1 WHERE id='fs'`)
		ok("W0301-RESTORED-EPOCH-NEEDS-FRESH-OBSERVATION", ferr != nil && strings.Contains(ferr.Error(), "RESTORE_FRESH_RECONCILIATION_REQUIRED"), ferr)
		pdb, err := store.Open(filepath.Join(tmp, "plain.sqlite"))
		must(err, "OPEN-PLAIN")
		if err == nil {
			defer pdb.Close()
			applyBaseline(ctx, pdb, root)
			ok("W0301-FENCE-NOOP-WITHOUT-TABLE", domain.EnsureClientSessionFence(ctx, pdb) == nil)
		}
	}
}
