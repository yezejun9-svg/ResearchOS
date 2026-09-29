package domain

import (
	"database/sql"
	"errors"
	"fmt"
	"sort"
	"strings"
)

const retrievalRevision = "fts5-v1"

// searchEvidence consumes IDs, never host paths. It rechecks the live file for
// local snapshots on every read, before consulting any index candidate.
func (s *Service) searchEvidence(tx *sql.Tx, p Principal, project string, b Object) (Object, error) {
	state, err := singleton(tx, project, "ProjectState")
	if err != nil {
		return nil, err
	}
	actual, err := Num(state, "revision")
	if err != nil {
		return nil, err
	}
	expected, err := Num(b, "expected_state_revision")
	if err != nil {
		return nil, err
	}
	if actual != expected {
		return nil, &Fault{412, "STALE_REVISION", "project state changed", actual}
	}
	ids := Arr(b, "snapshot_ids")
	if len(ids) > 1000 {
		return nil, Fail(400, "INVALID_REQUEST", "too many snapshot IDs")
	}
	limit, err := Num(b, "limit")
	if err != nil {
		return nil, err
	}
	q := Str(b, "query")
	type candidate struct {
		artifact   Object
		bytes      []byte
		evidenceID any
		local      bool
	}
	items := make(map[string]candidate, len(ids))
	warnings := Empty()
	manifest := Empty()
	for _, rawID := range ids {
		id := rawID.(string)
		if _, exists := items[id]; exists {
			return nil, Fail(400, "INVALID_REQUEST", "duplicate snapshot ID")
		}
		a, loadErr := s.readObject(tx, p, project, "Artifact", id)
		if loadErr != nil {
			return nil, loadErr
		}
		if a["kind"] != "SOURCE_SNAPSHOT" {
			return nil, Fail(422, "GATE_FAILED", "SOURCE_SNAPSHOT required")
		}
		if !s.visible(tx, p, project, a) {
			return nil, Fail(404, "NOT_FOUND", "snapshot unavailable")
		}
		var data []byte
		localData, local, localErr := readLocalSnapshot(tx, project, id)
		if localErr != nil {
			return nil, localErr
		}
		if local {
			data = localData
			if data == nil || Digest(data) != a["content_hash"] {
				warnings = append(warnings, "snapshot changed or unavailable: "+id)
				continue
			}
		} else {
			if a["validity"] != "CURRENT" {
				warnings = append(warnings, "snapshot unavailable: "+id)
				continue
			}
			err = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, a["storage_key"]).Scan(&data)
			if err != nil || Digest(data) != a["content_hash"] {
				return nil, Fail(422, "CONTENT_HASH_MISMATCH", "sealed snapshot unavailable")
			}
		}
		if a["validity"] != "CURRENT" {
			warnings = append(warnings, "snapshot unavailable: "+id)
			continue
		}
		var evidenceID any
		var evID string
		err = tx.QueryRow("SELECT id FROM domain_objects WHERE project=? AND kind='Evidence' AND json_extract(body,'$.snapshot_artifact_ref.id')=? AND json_extract(body,'$.validity')='CURRENT' ORDER BY id LIMIT 1", project, id).Scan(&evID)
		if err == nil {
			ev, loadErr := load(tx, project, "Evidence", evID)
			if loadErr == nil && s.visible(tx, p, project, ev) {
				evidenceID = evID
			}
		}
		if err != nil && !errors.Is(err, sql.ErrNoRows) {
			return nil, err
		}
		items[id] = candidate{a, data, evidenceID, local}
		manifest = append(manifest, []any{id, a["content_hash"], a["revision"]})
	}
	// A sorted version manifest makes query identity independent of request order.
	sort.Slice(manifest, func(i, j int) bool { return manifest[i].([]any)[0].(string) < manifest[j].([]any)[0].(string) })
	grantHash := Hash([]any{p.ID, p.Roles, p.Grants})
	snapshotHash := Hash([]any{project, actual, grantHash, retrievalRevision, manifest})
	ftsIDs := map[string]bool{}
	ftsAvailable := false
	if strings.TrimSpace(q) != "" {
		phrase := "\"" + strings.ReplaceAll(q, "\"", "\"\"") + "\""
		rows, queryErr := tx.Query("SELECT artifact_id FROM retrieval_fts WHERE project=? AND retrieval_fts MATCH ?", project, phrase)
		if queryErr == nil {
			ftsAvailable = true
			for rows.Next() {
				var id string
				if err = rows.Scan(&id); err != nil {
					rows.Close()
					return nil, err
				}
				ftsIDs[id] = true
			}
			err = rows.Err()
			rows.Close()
			if err != nil {
				return nil, err
			}
		} else {
			warnings = append(warnings, "FTS unavailable; bounded scan used")
		}
	}
	selected := make([]string, 0, len(items))
	for id := range items {
		selected = append(selected, id)
	}
	sort.Strings(selected)
	hits := Empty()
	for _, id := range selected {
		c := items[id]
		if !isTextArtifact(c.artifact) {
			continue
		}
		body := string(c.bytes)
		position := strings.Index(strings.ToLower(body), strings.ToLower(q))
		if position < 0 {
			continue
		}
		start := position - 80
		if start < 0 {
			start = 0
		}
		end := position + len(q) + 120
		if end > len(body) {
			end = len(body)
		}
		// Excerpts are byte bounded but must remain valid UTF-8 for the response.
		for start > 0 && start < len(body) && body[start]&0xc0 == 0x80 {
			start--
		}
		for end < len(body) && body[end]&0xc0 == 0x80 {
			end++
		}
		line := 1 + strings.Count(body[:position], "\n")
		backend := "bounded-scan"
		revision := "scan-v1"
		if ftsAvailable && ftsIDs[id] {
			backend = "sqlite-fts5"
			revision = retrievalRevision
		}
		hits = append(hits, Object{"artifact_ref": Ref(c.artifact, "Artifact"), "evidence_id": c.evidenceID, "locator": fmt.Sprintf("line:%d", line), "excerpt": body[start:end], "validity": "CURRENT", "score": nil, "backend": backend, "backend_revision": revision})
		if int64(len(hits)) >= limit {
			break
		}
	}
	return Object{"hits": hits, "state_revision": actual, "snapshot_hash": snapshotHash, "warnings": warnings}, nil
}

// currentAuthorizedSnapshots is shared by ContextBundle creation and use.
// The file is checked through the same root handle that search uses.
func (s *Service) currentAuthorizedSnapshots(tx *sql.Tx, p Principal, project string) ([]any, error) {
	profile, err := singleton(tx, project, "ProjectProfile")
	if err != nil {
		return nil, err
	}
	out := Empty()
	for _, rawID := range Arr(profile, "read_snapshot_ids") {
		id := rawID.(string)
		a, e := s.readObject(tx, p, project, "Artifact", id)
		if e != nil {
			continue
		}
		if a["validity"] != "CURRENT" {
			continue
		}
		data, local, e := readLocalSnapshot(tx, project, id)
		if e != nil {
			return nil, e
		}
		if local && (data == nil || Digest(data) != a["content_hash"]) {
			continue
		}
		out = append(out, id)
	}
	return out, nil
}

func (s *Service) validateBundleSnapshots(tx *sql.Tx, p Principal, project string, bundle Object) error {
	current, err := s.currentAuthorizedSnapshots(tx, p, project)
	if err != nil {
		return err
	}
	valid := map[string]bool{}
	for _, id := range current {
		valid[id.(string)] = true
	}
	for _, id := range Arr(bundle, "authorized_snapshot_ids") {
		if !valid[id.(string)] {
			return Fail(412, "STALE_INPUT", "context snapshot changed or permission revoked")
		}
	}
	return nil
}
