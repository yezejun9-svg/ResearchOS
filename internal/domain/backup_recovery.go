package domain

import (
	"bytes"
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"researchos.local/research-os/adapters/retrieval"
)

// Reconstruct registered file roots from sealed snapshots. No restored query
// is allowed to fall back to the original machine's absolute source path.
func (s *Service) backupRelocateSources(stage, destination string) error {
	rows, e := s.DB.Query("SELECT project,id FROM retrieval_roots")
	if e != nil {
		return e
	}
	type root struct{ project, id string }
	roots := []root{}
	for rows.Next() {
		var x root
		if e = rows.Scan(&x.project, &x.id); e != nil {
			rows.Close()
			return e
		}
		roots = append(roots, x)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return e
	}
	for _, r := range roots {
		relative := filepath.Join("sources", strings.TrimPrefix(Hash([]any{r.project, r.id}), "sha256:"))
		path := filepath.Join(stage, relative)
		if e = os.MkdirAll(path, 0700); e != nil {
			return e
		}
		rows, e = s.DB.Query("SELECT x.relative_path,u.bytes,x.content_hash FROM retrieval_snapshots x JOIN domain_objects a ON a.project=x.project AND a.kind='Artifact' AND a.id=x.artifact_id JOIN uploaded_content u ON u.project=a.project AND u.storage_key=json_extract(a.body,'$.storage_key') AND u.sealed=1 WHERE x.project=? AND x.root_id=? AND x.status='CURRENT'", r.project, r.id)
		if e != nil {
			return e
		}
		written := map[string]backupSourceFile{}
		for rows.Next() {
			var name, hash string
			var raw []byte
			if e = rows.Scan(&name, &raw, &hash); e != nil {
				rows.Close()
				return e
			}
			name = filepath.FromSlash(name)
			if !filepath.IsLocal(name) || strings.Contains(name, ":") || Digest(raw) != hash {
				rows.Close()
				return fmt.Errorf("RESTORE_SOURCE_INVALID")
			}
			target := filepath.Join(path, name)
			if e = os.MkdirAll(filepath.Dir(target), 0700); e != nil {
				rows.Close()
				return e
			}
			if e = backupWriteSource(target, raw, hash, written); e != nil {
				rows.Close()
				return e
			}
		}
		e = rows.Err()
		rows.Close()
		if e != nil {
			return e
		}
		identity, e := retrieval.Identity(path)
		if e != nil {
			return e
		}
		target, e := filepath.Abs(filepath.Join(stage, relative))
		if e != nil {
			return e
		}
		if _, e = s.DB.Exec("UPDATE retrieval_roots SET path=?,root_identity=? WHERE project=? AND id=?", target, identity, r.project, r.id); e != nil {
			return e
		}
	}
	return nil
}

type backupSourceFile struct {
	info os.FileInfo
	hash string
}

// Snapshot origin paths remain unchanged. Two paths may name the same native
// file (including Windows case aliases), but may only share identical content.
// An existing file is reusable only if this restore created that exact file.
func backupWriteSource(target string, raw []byte, hash string, written map[string]backupSourceFile) error {
	err := backupWrite(target, raw)
	if err == nil {
		info, err := os.Lstat(target)
		if err != nil {
			return err
		}
		written[target] = backupSourceFile{info: info, hash: hash}
		return nil
	}
	if !os.IsExist(err) {
		return err
	}
	info, err := os.Lstat(target)
	if err != nil || !info.Mode().IsRegular() {
		return fmt.Errorf("RESTORE_SOURCE_CONFLICT")
	}
	for _, prior := range written {
		if os.SameFile(prior.info, info) {
			if prior.hash != hash {
				return fmt.Errorf("RESTORE_SOURCE_CONFLICT")
			}
			actual, err := os.ReadFile(target)
			if err != nil || Digest(actual) != hash || !bytes.Equal(actual, raw) {
				return fmt.Errorf("RESTORE_SOURCE_CONFLICT")
			}
			return nil
		}
	}
	return fmt.Errorf("RESTORE_SOURCE_CONFLICT")
}

func (s *Service) backupPublishSourcePaths(stage, destination string) error {
	rows, e := s.DB.Query("SELECT project,id,path FROM retrieval_roots")
	if e != nil {
		return e
	}
	type entry struct{ project, id, path string }
	entries := []entry{}
	for rows.Next() {
		var x entry
		if e = rows.Scan(&x.project, &x.id, &x.path); e != nil {
			rows.Close()
			return e
		}
		entries = append(entries, x)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return e
	}
	for _, x := range entries {
		rel, e := filepath.Rel(stage, x.path)
		if e != nil || !filepath.IsLocal(rel) {
			return fmt.Errorf("RESTORE_SOURCE_NOT_ISOLATED")
		}
		abs, e := filepath.Abs(filepath.Join(destination, rel))
		if e != nil {
			return e
		}
		if _, e = s.DB.Exec("UPDATE retrieval_roots SET path=? WHERE project=? AND id=?", abs, x.project, x.id); e != nil {
			return e
		}
	}
	return nil
}

func (s *Service) backupRecomputeAcceptance() (Object, error) {
	tasks, e := backupObjects(s.DB, "SELECT body FROM domain_objects WHERE kind='Task' AND json_extract(body,'$.status')='ACCEPTED'")
	if e != nil {
		return nil, e
	}
	tx, e := s.DB.Begin()
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	results := Empty()
	for _, task := range tasks {
		if e = s.acceptedTaskBinding(tx, Str(task, "project_id"), task); e != nil {
			return nil, fmt.Errorf("RESTORE_ACCEPTANCE_INEFFECTIVE: %w", e)
		}
		receipt, e := load(tx, Str(task, "project_id"), "AcceptanceReceipt", Str(task, "acceptance_id"))
		if e != nil {
			return nil, e
		}
		results = append(results, Object{"project_id": task["project_id"], "task_id": task["id"], "acceptance_id": receipt["id"], "receipt_hash": receipt["receipt_hash"], "effective": true})
	}
	return Object{"accepted_tasks_recomputed": results}, nil
}

// Restore is a time reversal: even PREPARED effects might have been sent after
// the snapshot. Fence ALL unfinished effects, invalidate credentials, and force
// trusted runtime reconciliation before the existing W12 resume protocol.
func (s *Service) backupFence(ctx context.Context) (Object, error) {
	runs, e := backupObjects(s.DB, "SELECT body FROM domain_objects WHERE kind='Run' AND json_extract(body,'$.status') IN ('QUEUED','STARTING','RUNNING','CANCEL_REQUESTED','RECONCILING','LOST')")
	if e != nil {
		return nil, e
	}
	effects, e := backupObjects(s.DB, `SELECT body FROM resource_effects x WHERE sequence=(SELECT max(y.sequence) FROM resource_effects y WHERE y.project=x.project AND y.run=x.run AND y.effect_key=x.effect_key) AND json_extract(body,'$.state') IN ('PREPARED','STARTED','UNKNOWN')`)
	if e != nil {
		return nil, e
	}
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	// Restore-local guard survives restart and applies to every existing resume
	// route. A snapshot's old observation is never fresh reconciliation evidence.
	if _, e = tx.Exec(`CREATE TABLE IF NOT EXISTS backup_restore_barriers(project TEXT NOT NULL,run TEXT NOT NULL,restored_at TEXT NOT NULL,PRIMARY KEY(project,run));
CREATE TRIGGER IF NOT EXISTS backup_require_fresh_observation BEFORE UPDATE ON domain_objects
WHEN NEW.kind='Run' AND json_extract(NEW.body,'$.lease_epoch')>json_extract(OLD.body,'$.lease_epoch')
AND EXISTS(SELECT 1 FROM backup_restore_barriers b WHERE b.project=NEW.project AND b.run=NEW.id)
AND NOT EXISTS(SELECT 1 FROM runtime_observations o JOIN backup_restore_barriers b ON b.project=o.project AND b.run=o.run WHERE o.project=NEW.project AND o.run=NEW.id AND o.epoch=json_extract(OLD.body,'$.lease_epoch') AND o.observed_at>b.restored_at AND json_extract(o.body,'$.children_stopped')=1 AND json_extract(o.body,'$.queue_empty')=1)
BEGIN SELECT RAISE(ABORT,'RESTORE_FRESH_RECONCILIATION_REQUIRED'); END;`); e != nil {
		return nil, e
	}
	if _, e = tx.Exec("UPDATE auth_credentials SET revoked=1"); e != nil {
		return nil, e
	}
	for _, r := range runs {
		if _, e = tx.Exec("INSERT INTO backup_restore_barriers(project,run,restored_at) VALUES(?,?,?) ON CONFLICT(project,run) DO UPDATE SET restored_at=excluded.restored_at", r["project_id"], r["id"], Now()); e != nil {
			return nil, e
		}
		status := "RECONCILING"
		if r["status"] == "CANCEL_REQUESTED" {
			status = "CANCEL_REQUESTED"
		}
		Merge(r, Object{"status": status, "lease_token_hash": Digest([]byte(ID() + ID())), "lease_expires_at": "1970-01-01T00:00:00Z"})
		if e = bump(r); e != nil {
			return nil, e
		}
		if e = s.put(tx, "Run", r); e != nil {
			return nil, e
		}
		if e = s.event(tx, Str(r, "project_id"), "Run", r, "restore-local-admin", ID(), "RUN_CHANGED"); e != nil {
			return nil, e
		}
	}
	for _, o := range effects {
		o["state"] = "UNKNOWN"
		o["restore_reason"] = "SNAPSHOT_MAY_PREDATE_EXTERNAL_DISPATCH"
		if e = effectAppend(tx, Str(o, "project_id"), Str(o, "run_id"), Str(o, "key"), o); e != nil {
			return nil, e
		}
	}
	if e = tx.Commit(); e != nil {
		return nil, e
	}
	return Object{"active_runs_fenced": len(runs), "effects_requiring_reconciliation": len(effects), "credentials": "REVOKED_REPROVISION_LOCALLY", "external_keys": "NOT_INCLUDED_RESTORE_SEPARATELY", "external_actions_dispatched": 0, "outbox_policy": "preserved; internal consumers deduplicate by event ID; external delivery requires provider reconciliation", "expected_differences": []any{"revoked session credentials", "relocated source roots", "active runs RECONCILING with expired leases and new revisions", "unfinished effects UNKNOWN", "restore audit events"}}, nil
}
