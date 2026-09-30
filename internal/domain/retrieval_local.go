package domain

import (
	"context"
	"database/sql"
	"errors"
	"path/filepath"
	"researchos.local/research-os/adapters/retrieval"
	"strings"
	"unicode/utf8"
)

// RegisterLocalRoot is a trusted, local Owner operation. No HTTP request can
// provide a host path to the search endpoint.
func (s *Service) RegisterLocalRoot(ctx context.Context, token, project, path string) (string, error) {
	if !filepath.IsAbs(path) {
		return "", Fail(400, "INVALID_REQUEST", "absolute root required")
	}
	path, err := filepath.EvalSymlinks(path)
	if err != nil {
		return "", err
	}
	path, err = filepath.Abs(path)
	if err != nil {
		return "", err
	}
	identity, err := retrieval.Identity(path)
	if err != nil {
		return "", err
	}
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return "", err
	}
	defer tx.Rollback()
	p, err := authenticate(tx, token)
	if err != nil {
		return "", err
	}
	if !p.HasRole("OWNER") || !p.Allowed(project, "", "", false) {
		return "", Fail(403, "FORBIDDEN", "Owner project grant required")
	}
	id := ID()
	_, err = tx.Exec("INSERT INTO retrieval_roots(project,id,path,root_identity,revision) VALUES(?,?,?,?,1)", project, id, path, identity)
	if err != nil {
		return "", err
	}
	return id, tx.Commit()
}

// CaptureLocalSnapshot seals the exact bytes read through os.Root. A change to
// the same file retires its former snapshot before the new one becomes current.
func (s *Service) CaptureLocalSnapshot(ctx context.Context, token, project, rootID, relative string) (Object, error) {
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()
	p, err := authenticate(tx, token)
	if err != nil {
		return nil, err
	}
	if !p.HasRole("OWNER") || !p.Allowed(project, "", "", false) {
		return nil, Fail(403, "FORBIDDEN", "Owner project grant required")
	}
	var rootPath string
	var rootIdentity string
	var rootRev int64
	var revoked bool
	err = tx.QueryRow("SELECT path,root_identity,revision,revoked FROM retrieval_roots WHERE project=? AND id=?", project, rootID).Scan(&rootPath, &rootIdentity, &rootRev, &revoked)
	if err != nil || revoked {
		return nil, Fail(404, "NOT_FOUND", "authorized root unavailable")
	}
	data, err := retrieval.ReadFileBound(rootPath, rootIdentity, relative)
	if err != nil {
		return nil, Fail(422, "GATE_FAILED", "root-scoped file unavailable")
	}
	if !utf8.Valid(data) {
		return nil, Fail(422, "GATE_FAILED", "local text snapshot requires UTF-8")
	}
	var previousID, previousHash string
	err = tx.QueryRow("SELECT artifact_id,content_hash FROM retrieval_snapshots WHERE project=? AND root_id=? AND relative_path=? AND status='CURRENT'", project, rootID, relative).Scan(&previousID, &previousHash)
	if err != nil && !errors.Is(err, sql.ErrNoRows) {
		return nil, err
	}
	if previousID != "" && previousHash == Digest(data) {
		return load(tx, project, "Artifact", previousID)
	}
	profile, err := singleton(tx, project, "ProjectProfile")
	if err != nil {
		return nil, err
	}
	if previousID != "" {
		if err = s.retireLocalPath(tx, project, rootID, relative, previousID, "STALE"); err != nil {
			return nil, err
		}
		var live int
		if err = tx.QueryRow("SELECT count(*) FROM retrieval_snapshots WHERE project=? AND artifact_id=? AND status='CURRENT'", project, previousID).Scan(&live); err != nil {
			return nil, err
		}
		if live == 0 {
			profile["read_snapshot_ids"] = withoutSnapshot(Arr(profile, "read_snapshot_ids"), previousID)
		}
	}
	a, err := s.canonicalLocalArtifact(tx, p, project, data)
	if err != nil {
		return nil, err
	}
	_, err = tx.Exec("INSERT INTO retrieval_snapshots(project,artifact_id,root_id,relative_path,content_hash,root_revision,status) VALUES(?,?,?,?,?,?,'CURRENT')", project, a["id"], rootID, relative, a["content_hash"], rootRev)
	if err != nil {
		return nil, err
	}
	var indexed int
	if err = tx.QueryRow("SELECT count(*) FROM retrieval_index WHERE project=? AND artifact_id=?", project, a["id"]).Scan(&indexed); err != nil {
		return nil, err
	}
	if indexed == 0 {
		if _, err = tx.Exec("INSERT INTO retrieval_fts(project,artifact_id,body) VALUES(?,?,?)", project, a["id"], string(data)); err != nil {
			return nil, err
		}
		var rowid int64
		if err = tx.QueryRow("SELECT last_insert_rowid()").Scan(&rowid); err != nil {
			return nil, err
		}
		if _, err = tx.Exec("INSERT INTO retrieval_index(project,artifact_id,fts_rowid,index_revision,content_hash) VALUES(?,?,?,1,?)", project, a["id"], rowid, a["content_hash"]); err != nil {
			return nil, err
		}
	}
	if !containsSnapshot(Arr(profile, "read_snapshot_ids"), Str(a, "id")) {
		profile["read_snapshot_ids"] = append(Arr(profile, "read_snapshot_ids"), a["id"])
	}
	if err = s.saveSnapshotProfile(tx, p, profile); err != nil {
		return nil, err
	}
	return a, tx.Commit()
}

func containsSnapshot(ids []any, id string) bool {
	for _, x := range ids {
		if x == id {
			return true
		}
	}
	return false
}

func (s *Service) canonicalLocalArtifact(tx *sql.Tx, p Principal, project string, data []byte) (Object, error) {
	var raw string
	err := tx.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='Artifact' AND json_extract(body,'$.kind')='SOURCE_SNAPSHOT' AND json_extract(body,'$.content_hash')=?", project, Digest(data)).Scan(&raw)
	if err == nil {
		a, e := Decode([]byte(raw))
		if e != nil {
			return nil, e
		}
		if a["evidence_kind"] != "OBSERVED" || a["measurement_mode"] != "LIVE" || a["access_class"] != "PROJECT" || a["media_type"] != "text/plain; charset=utf-8" || len(Arr(a, "input_refs")) != 0 || len(Arr(a, "source_refs")) != 0 {
			return nil, Fail(409, "STATE_CONFLICT", "same hash has incompatible source snapshot metadata")
		}
		var sealed []byte
		if e = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, a["storage_key"]).Scan(&sealed); e != nil || Digest(sealed) != Digest(data) {
			return nil, Fail(422, "CONTENT_HASH_MISMATCH", "canonical snapshot bytes unavailable")
		}
		if a["validity"] != "CURRENT" {
			a["validity"] = "CURRENT"
			if e = bump(a); e != nil {
				return nil, e
			}
			if e = s.put(tx, "Artifact", a); e != nil {
				return nil, e
			}
		}
		return a, nil
	}
	if !errors.Is(err, sql.ErrNoRows) {
		return nil, err
	}
	u, err := s.upload(tx, p, project, data)
	if err != nil {
		return nil, err
	}
	return s.seal(tx, p, project, Object{"run_id": nil, "kind": "SOURCE_SNAPSHOT", "evidence_kind": "OBSERVED", "measurement_mode": "LIVE", "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "text/plain; charset=utf-8", "byte_size": len(data), "input_refs": Empty(), "source_refs": Empty(), "produced_by": p.ID, "access_class": "PROJECT"})
}

func withoutSnapshot(ids []any, id string) []any {
	out := Empty()
	for _, value := range ids {
		if value != id {
			out = append(out, value)
		}
	}
	return out
}

func (s *Service) saveSnapshotProfile(tx *sql.Tx, p Principal, profile Object) error {
	if err := bump(profile); err != nil {
		return err
	}
	if err := s.put(tx, "ProjectProfile", profile); err != nil {
		return err
	}
	project := Str(profile, "project_id")
	state, err := singleton(tx, project, "ProjectState")
	if err != nil {
		return err
	}
	state["profile_revision"] = profile["revision"]
	if err = bump(state); err != nil {
		return err
	}
	if err = s.put(tx, "ProjectState", state); err != nil {
		return err
	}
	return s.event(tx, project, "ProjectProfile", profile, p.ID, ID(), "PROJECT_UPDATED")
}

func (s *Service) retireLocalPath(tx *sql.Tx, project, rootID, relative, artifactID, validity string) error {
	if validity != "STALE" && validity != "REVOKED" {
		return Fail(400, "INVALID_REQUEST", "invalid snapshot validity")
	}
	if _, err := tx.Exec("UPDATE retrieval_snapshots SET status=? WHERE project=? AND root_id=? AND relative_path=? AND artifact_id=? AND status='CURRENT'", validity, project, rootID, relative, artifactID); err != nil {
		return err
	}
	var live int
	if err := tx.QueryRow("SELECT count(*) FROM retrieval_snapshots WHERE project=? AND artifact_id=? AND status='CURRENT'", project, artifactID).Scan(&live); err != nil {
		return err
	}
	if live > 0 {
		return nil
	}
	if err := s.freezeSkillsForSource(tx, project, artifactID); err != nil {
		return err
	}
	rows, err := tx.Query("SELECT id,body FROM domain_objects WHERE project=? AND kind='Evidence' AND json_extract(body,'$.snapshot_artifact_ref.id')=?", project, artifactID)
	if err != nil {
		return err
	}
	var evidence []Object
	for rows.Next() {
		var id, body string
		if err = rows.Scan(&id, &body); err != nil {
			rows.Close()
			return err
		}
		o, e := Decode([]byte(body))
		if e != nil {
			rows.Close()
			return e
		}
		evidence = append(evidence, o)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return err
	}
	for _, o := range evidence {
		if o["validity"] == "CURRENT" {
			o["validity"] = validity
			if err = bump(o); err != nil {
				return err
			}
			if err = s.put(tx, "Evidence", o); err != nil {
				return err
			}
		}
	}
	a, err := load(tx, project, "Artifact", artifactID)
	if err != nil {
		return err
	}
	if a["validity"] == "CURRENT" {
		a["validity"] = validity
		if err = bump(a); err != nil {
			return err
		}
		if err = s.put(tx, "Artifact", a); err != nil {
			return err
		}
	}
	return nil
}

// RefreshLocalSnapshots records changed, missing or escaped files as STALE.
// Revoking the root records REVOKED; sealed history remains for audit.
func (s *Service) RefreshLocalSnapshots(ctx context.Context, token, project string) (int, error) {
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return 0, err
	}
	defer tx.Rollback()
	p, err := authenticate(tx, token)
	if err != nil {
		return 0, err
	}
	if !p.HasRole("OWNER") || !p.Allowed(project, "", "", false) {
		return 0, Fail(403, "FORBIDDEN", "Owner project grant required")
	}
	rows, err := tx.Query("SELECT s.artifact_id,s.root_id,s.relative_path,s.content_hash,r.path,r.root_identity,r.revoked,r.revision,s.root_revision FROM retrieval_snapshots s JOIN retrieval_roots r ON r.project=s.project AND r.id=s.root_id WHERE s.project=? AND s.status='CURRENT'", project)
	if err != nil {
		return 0, err
	}
	type item struct {
		id, rootID, relative, hash, root, identity string
		revoked                                    bool
		rootRev, snapRev                           int64
	}
	var items []item
	for rows.Next() {
		var x item
		if err = rows.Scan(&x.id, &x.rootID, &x.relative, &x.hash, &x.root, &x.identity, &x.revoked, &x.rootRev, &x.snapRev); err != nil {
			rows.Close()
			return 0, err
		}
		items = append(items, x)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return 0, err
	}
	profile, err := singleton(tx, project, "ProjectProfile")
	if err != nil {
		return 0, err
	}
	changed := 0
	for _, x := range items {
		validity := ""
		if x.revoked {
			validity = "REVOKED"
		} else {
			data, readErr := retrieval.ReadFileBound(x.root, x.identity, x.relative)
			if readErr != nil || Digest(data) != x.hash || x.rootRev != x.snapRev {
				validity = "STALE"
			}
		}
		if validity == "" {
			continue
		}
		if err = s.retireLocalPath(tx, project, x.rootID, x.relative, x.id, validity); err != nil {
			return 0, err
		}
		var live int
		if err = tx.QueryRow("SELECT count(*) FROM retrieval_snapshots WHERE project=? AND artifact_id=? AND status='CURRENT'", project, x.id).Scan(&live); err != nil {
			return 0, err
		}
		if live == 0 {
			profile["read_snapshot_ids"] = withoutSnapshot(Arr(profile, "read_snapshot_ids"), x.id)
		}
		changed++
	}
	if changed > 0 {
		if err = s.saveSnapshotProfile(tx, p, profile); err != nil {
			return 0, err
		}
	}
	return changed, tx.Commit()
}

func (s *Service) RevokeLocalRoot(ctx context.Context, token, project, rootID string) error {
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	p, err := authenticate(tx, token)
	if err != nil {
		return err
	}
	if !p.HasRole("OWNER") || !p.Allowed(project, "", "", false) {
		return Fail(403, "FORBIDDEN", "Owner project grant required")
	}
	result, err := tx.Exec("UPDATE retrieval_roots SET revoked=1,revision=revision+1 WHERE project=? AND id=? AND revoked=0", project, rootID)
	if err != nil {
		return err
	}
	n, _ := result.RowsAffected()
	if n != 1 {
		return Fail(404, "NOT_FOUND", "active root unavailable")
	}
	rows, err := tx.Query("SELECT artifact_id,relative_path FROM retrieval_snapshots WHERE project=? AND root_id=? AND status='CURRENT'", project, rootID)
	if err != nil {
		return err
	}
	type pathRef struct{ id, relative string }
	var ids []pathRef
	for rows.Next() {
		var x pathRef
		if err = rows.Scan(&x.id, &x.relative); err != nil {
			rows.Close()
			return err
		}
		ids = append(ids, x)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return err
	}
	profile, err := singleton(tx, project, "ProjectProfile")
	if err != nil {
		return err
	}
	for _, x := range ids {
		if err = s.retireLocalPath(tx, project, rootID, x.relative, x.id, "REVOKED"); err != nil {
			return err
		}
		var live int
		if err = tx.QueryRow("SELECT count(*) FROM retrieval_snapshots WHERE project=? AND artifact_id=? AND status='CURRENT'", project, x.id).Scan(&live); err != nil {
			return err
		}
		if live == 0 {
			profile["read_snapshot_ids"] = withoutSnapshot(Arr(profile, "read_snapshot_ids"), x.id)
		}
	}
	if err = s.saveSnapshotProfile(tx, p, profile); err != nil {
		return err
	}
	return tx.Commit()
}

func readLocalSnapshot(tx *sql.Tx, project, artifactID string) ([]byte, bool, error) {
	rows, err := tx.Query("SELECT r.path,r.root_identity,s.relative_path,s.content_hash,s.status,r.revoked,r.revision,s.root_revision FROM retrieval_snapshots s JOIN retrieval_roots r ON r.project=s.project AND r.id=s.root_id WHERE s.project=? AND s.artifact_id=?", project, artifactID)
	if err != nil {
		return nil, false, err
	}
	type location struct {
		root, identity, relative, hash, status string
		revoked                                bool
		rootRev, snapRev                       int64
	}
	var paths []location
	for rows.Next() {
		var x location
		if err = rows.Scan(&x.root, &x.identity, &x.relative, &x.hash, &x.status, &x.revoked, &x.rootRev, &x.snapRev); err != nil {
			rows.Close()
			return nil, false, err
		}
		paths = append(paths, x)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return nil, false, err
	}
	for _, x := range paths {
		if x.status != "CURRENT" || x.revoked || x.rootRev != x.snapRev {
			continue
		}
		data, e := retrieval.ReadFileBound(x.root, x.identity, x.relative)
		if e == nil && Digest(data) == x.hash {
			return data, true, nil
		}
	}
	return nil, len(paths) > 0, nil
}

func isTextArtifact(o Object) bool { return strings.HasPrefix(Str(o, "media_type"), "text/") }
