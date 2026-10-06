package domain

import (
	"context"
	"database/sql"
	"errors"
	"researchos.local/research-os/adapters/retrieval"
	"sort"
	"strings"
)

// RecordEvidenceOrigin is a reviewed local annotation, not a similarity guess.
// originID is empty only for a reviewer-confirmed independent root. The basis
// must be a current sealed artifact visible to the reviewer.
func (s *Service) RecordEvidenceOrigin(ctx context.Context, token, project, evidenceID, originID, basisArtifactID, basisRootID, basisRelativePath string) error {
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	p, err := authenticate(tx, token)
	if err != nil {
		return err
	}
	if !(p.HasRole("OWNER") || p.HasRole("VERIFIER")) || !p.Allowed(project, "", "", false) {
		return Fail(403, "FORBIDDEN", "reviewer project grant required")
	}
	ev, err := s.readObject(tx, p, project, "Evidence", evidenceID)
	if err != nil {
		return err
	}
	if ev["evidence_kind"] != "OBSERVED" || ev["validity"] != "CURRENT" {
		return Fail(422, "GATE_FAILED", "current observed evidence required")
	}
	basis, err := s.readObject(tx, p, project, "Artifact", basisArtifactID)
	if err != nil {
		return err
	}
	if err = s.requireCurrentArtifactBody(tx, project, basis); err != nil {
		return Fail(422, "GATE_FAILED", "current sealed basis required")
	}
	ref, ok := ev["snapshot_artifact_ref"].(map[string]any)
	if !ok || ref["id"] != basisArtifactID || basis["content_hash"] != ref["content_hash"] {
		return Fail(422, "GATE_FAILED", "origin review must cite the evidence's sealed source body")
	}
	if !reviewedBasisCurrent(tx, project, basis, basisRootID, basisRelativePath) {
		return Fail(422, "GATE_FAILED", "reviewed source location is not current")
	}
	relation := "ROOT"
	if originID != "" {
		relation = "DERIVED"
		if originID == evidenceID {
			return Fail(422, "GATE_FAILED", "evidence cannot derive from itself")
		}
		origin, err := s.readObject(tx, p, project, "Evidence", originID)
		if err != nil {
			return err
		}
		if origin["evidence_kind"] != "OBSERVED" || origin["validity"] != "CURRENT" {
			return Fail(422, "GATE_FAILED", "current observed origin required")
		}
		if !s.evidenceBodyCurrent(tx, p, project, origin) {
			return Fail(422, "GATE_FAILED", "current origin source required")
		}
		originURL := Str(origin, "canonical_url")
		if originURL == "" {
			return Fail(422, "GATE_FAILED", "origin needs a citable canonical URL")
		}
		var sourceBody []byte
		if err = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, basis["storage_key"]).Scan(&sourceBody); err != nil || Digest(sourceBody) != basis["content_hash"] {
			return Fail(422, "CONTENT_HASH_MISMATCH", "sealed basis bytes unavailable")
		}
		if !strings.Contains(string(sourceBody), originURL) {
			return Fail(422, "GATE_FAILED", "derived source does not cite claimed origin URL")
		}
		if ev["origin_evidence_id"] != nil && ev["origin_evidence_id"] != originID {
			return Fail(409, "STATE_CONFLICT", "existing origin disagrees")
		}
		// A declared chain must terminate at an independently reviewed root.
		seen := map[string]bool{evidenceID: true}
		cursor := originID
		for cursor != "" {
			if seen[cursor] {
				return Fail(422, "GATE_FAILED", "origin cycle")
			}
			seen[cursor] = true
			var next, kind string
			err = tx.QueryRow("SELECT origin_id,relation FROM evidence_origins WHERE project=? AND evidence_id=?", project, cursor).Scan(&next, &kind)
			if errors.Is(err, sql.ErrNoRows) {
				return Fail(422, "GATE_FAILED", "origin chain is not reviewed")
			}
			if err != nil {
				return err
			}
			if kind == "ROOT" {
				break
			}
			cursor = next
		}
	}
	var existing int
	if err = tx.QueryRow("SELECT count(*) FROM evidence_origins WHERE project=? AND evidence_id=?", project, evidenceID).Scan(&existing); err != nil {
		return err
	}
	if existing != 0 {
		return Fail(409, "STATE_CONFLICT", "origin relationship already recorded")
	}
	if relation == "ROOT" {
		if ev["origin_evidence_id"] != nil {
			return Fail(422, "GATE_FAILED", "derived evidence cannot be declared an independent root")
		}
	} else {
		ev["origin_evidence_id"] = originID
		rootID, err := s.originRoot(tx, p, project, originID)
		if err != nil {
			return err
		}
		root, err := load(tx, project, "Evidence", rootID)
		if err != nil {
			return err
		}
		ev["independence_key"] = root["independence_key"]
		if err = bump(ev); err != nil {
			return err
		}
		if err = s.put(tx, "Evidence", ev); err != nil {
			return err
		}
	}
	_, err = tx.Exec("INSERT INTO evidence_origins(project,evidence_id,origin_id,relation,basis_artifact_id,basis_root_id,basis_relative_path,recorded_by,recorded_at) VALUES(?,?,?,?,?,?,?,?,?)", project, evidenceID, originID, relation, basisArtifactID, basisRootID, basisRelativePath, p.ID, Now())
	if err != nil {
		return err
	}
	if err = s.event(tx, project, "Evidence", ev, p.ID, ID(), "EVIDENCE_ADDED"); err != nil {
		return err
	}
	return tx.Commit()
}

func reviewedBasisCurrent(tx *sql.Tx, project string, basis Object, rootID, relative string) bool {
	if rootID == "" || relative == "" {
		if rootID != "" || relative != "" {
			return false
		}
		var count int
		return tx.QueryRow("SELECT count(*) FROM retrieval_snapshots WHERE project=? AND artifact_id=?", project, basis["id"]).Scan(&count) == nil && count == 0
	}
	var rootPath, identity, hash, status string
	var rootRev, snapRev int64
	var revoked bool
	err := tx.QueryRow("SELECT r.path,r.root_identity,r.revoked,r.revision,s.root_revision,s.content_hash,s.status FROM retrieval_snapshots s JOIN retrieval_roots r ON r.project=s.project AND r.id=s.root_id WHERE s.project=? AND s.artifact_id=? AND s.root_id=? AND s.relative_path=?", project, basis["id"], rootID, relative).Scan(&rootPath, &identity, &revoked, &rootRev, &snapRev, &hash, &status)
	if err != nil || status != "CURRENT" || revoked || rootRev != snapRev || hash != basis["content_hash"] {
		return false
	}
	data, err := retrieval.ReadFileBound(rootPath, identity, relative)
	return err == nil && Digest(data) == hash
}

func (s *Service) originRoot(tx *sql.Tx, p Principal, project, evidenceID string) (string, error) {
	seen := map[string]bool{}
	for evidenceID != "" {
		if seen[evidenceID] {
			return "", Fail(422, "GATE_FAILED", "origin cycle")
		}
		seen[evidenceID] = true
		evidence, err := s.readObject(tx, p, project, "Evidence", evidenceID)
		if err != nil {
			return "", err
		}
		if evidence["evidence_kind"] != "OBSERVED" || evidence["validity"] != "CURRENT" || !s.evidenceBodyCurrent(tx, p, project, evidence) {
			return "", Fail(422, "GATE_FAILED", "origin chain contains unavailable reviewed evidence")
		}
		var next, kind string
		err = tx.QueryRow("SELECT origin_id,relation FROM evidence_origins WHERE project=? AND evidence_id=?", project, evidenceID).Scan(&next, &kind)
		if errors.Is(err, sql.ErrNoRows) {
			return "", Fail(422, "GATE_FAILED", "origin unknown")
		}
		if err != nil {
			return "", err
		}
		if kind == "ROOT" {
			return evidenceID, nil
		}
		evidenceID = next
	}
	return "", Fail(422, "GATE_FAILED", "origin unknown")
}

func (s *Service) evidenceBodyCurrent(tx *sql.Tx, p Principal, project string, ev Object) bool {
	ref, ok := ev["snapshot_artifact_ref"].(map[string]any)
	if !ok {
		return false
	}
	body, err := s.readObject(tx, p, project, "Artifact", Str(ref, "id"))
	if err != nil || s.requireCurrentArtifactBody(tx, project, body) != nil {
		return false
	}
	var rootID, relative string
	if err = tx.QueryRow("SELECT basis_root_id,basis_relative_path FROM evidence_origins WHERE project=? AND evidence_id=? AND basis_artifact_id=?", project, ev["id"], body["id"]).Scan(&rootID, &relative); err != nil {
		return false
	}
	return reviewedBasisCurrent(tx, project, body, rootID, relative)
}

// EvidenceSupportSummary preserves every record, but counts only reviewed,
// current OBSERVED roots. Unknown origins and simulated opinions stay separate.
func (s *Service) EvidenceSupportSummary(ctx context.Context, token, project string, ids []string) (Object, error) {
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()
	p, err := authenticate(tx, token)
	if err != nil {
		return nil, err
	}
	if !p.Allowed(project, "", "", false) {
		return nil, Fail(404, "NOT_FOUND", "project unavailable")
	}
	records := Empty()
	roots := map[string]bool{}
	unknown := 0
	simulated := 0
	for _, id := range ids {
		ev, readErr := s.readObject(tx, p, project, "Evidence", id)
		if readErr != nil {
			return nil, readErr
		}
		kind := Str(ev, "evidence_kind")
		relation := "UNKNOWN"
		rootID := ""
		if kind == "SIMULATED" {
			simulated++
		} else if kind == "OBSERVED" && ev["validity"] == "CURRENT" && ev["stance"] == "SUPPORT" && s.evidenceBodyCurrent(tx, p, project, ev) {
			rootID, readErr = s.originRoot(tx, p, project, id)
			if readErr == nil {
				root, rootErr := s.readObject(tx, p, project, "Evidence", rootID)
				if rootErr == nil && root["validity"] == "CURRENT" && s.evidenceBodyCurrent(tx, p, project, root) {
					relation = "CONFIRMED"
					roots[rootID] = true
				}
			}
			if relation != "CONFIRMED" {
				rootID = ""
				unknown++
			}
		} else {
			unknown++
		}
		records = append(records, Object{"evidence_id": id, "evidence_kind": kind, "origin_relation": relation, "root_evidence_id": rootID, "validity": ev["validity"], "origin_evidence_id": ev["origin_evidence_id"]})
	}
	rootList := make([]string, 0, len(roots))
	for id := range roots {
		rootList = append(rootList, id)
	}
	sort.Strings(rootList)
	return Object{"records": records, "independent_observed_count": len(rootList), "independent_root_ids": rootList, "unknown_count": unknown, "simulated_count": simulated}, nil
}
