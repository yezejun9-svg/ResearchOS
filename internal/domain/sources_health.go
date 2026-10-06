package domain

import (
	"context"
	"database/sql"
	"encoding/json"
	"time"

	"researchos.local/research-os/adapters/sources"
)

const sourceHealthSchema = "researchos.source-health.v1"

// A nonexhaustive snapshot is historical capture provenance, not a page-chain
// checkpoint. Only a sealed host health report with the same cursor can bind it.
func healthBoundSourceArtifact(tx *sql.Tx, project string, artifact, cursor Object) (bool, error) {
	rows, err := tx.Query(`SELECT a.body,u.bytes FROM domain_objects a JOIN uploaded_content u ON u.project=a.project AND u.storage_key=json_extract(a.body,'$.storage_key') WHERE a.project=? AND a.kind='Artifact' AND json_extract(a.body,'$.media_type')='application/vnd.researchos.source-health.v1+json' AND u.sealed=1`, project)
	if err != nil {
		return false, err
	}
	type record struct {
		body string
		raw  []byte
	}
	records := []record{}
	for rows.Next() {
		var r record
		if err = rows.Scan(&r.body, &r.raw); err != nil {
			rows.Close()
			return false, err
		}
		records = append(records, r)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return false, err
	}
	for _, r := range records {
		a, e := Decode([]byte(r.body))
		if e != nil || a["validity"] != "CURRENT" || a["evidence_kind"] != "GENERATED" || Digest(r.raw) != a["content_hash"] {
			continue
		}
		d, e := Decode(r.raw)
		if e != nil || d["schema"] != sourceHealthSchema || d["source_id"] != cursor["source_id"] || d["query_hash"] != cursor["query_hash"] || Hash(d["source_refs"]) != Hash(a["source_refs"]) {
			continue
		}
		cr, ok := d["cursor_ref"].(map[string]any)
		if !ok || Hash(cr) != Hash(Ref(cursor, "SourceCursor")) {
			continue
		}
		for _, v := range Arr(a, "source_refs") {
			ref, ok := v.(map[string]any)
			if !ok {
				continue
			}
			if ref["entity_type"] == "Artifact" && Hash(ref) == Hash(Ref(artifact, "Artifact")) {
				return true, nil
			}
			if ref["entity_type"] == "Evidence" {
				ev, e := load(tx, project, "Evidence", Str(ref, "id"))
				if e == nil && Hash(Ref(ev, "Evidence")) == Hash(ref) && ev["validity"] == "CURRENT" && Hash(ev["snapshot_artifact_ref"]) == Hash(Ref(artifact, "Artifact")) {
					return true, nil
				}
			}
		}
	}
	return false, nil
}

func (s *Service) sealSourceHealth(tx *sql.Tx, p Principal, project string, cursor, config Object, result SourceCapture) (Object, error) {
	profile, err := singleton(tx, project, "ProjectProfile")
	if err != nil {
		return nil, err
	}
	refs := Empty()
	if result.Manifest != nil {
		refs = append(refs, Ref(result.Manifest, "Artifact"))
	}
	if result.RawArtifact != nil {
		refs = append(refs, Ref(result.RawArtifact, "Artifact"))
	}
	for _, ev := range result.Evidence {
		refs = append(refs, Ref(ev, "Evidence"))
	}
	doc := Object{"schema": sourceHealthSchema, "source_id": config["source_id"], "query_hash": cursor["query_hash"], "config_hash": Hash(config), "query": config["query"], "cursor_ref": Ref(cursor, "SourceCursor"), "profile_ref": Ref(profile, "ProjectProfile"), "health": result.Health, "source_refs": refs, "fetched_at": result.Page.FetchedAt.UTC().Format(time.RFC3339Nano), "failed_provider_raw": failedSourceRaw(result)}
	body := Bytes(doc)
	// Exact replay preserves the original report and all preceding observations.
	var prior string
	err = tx.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='Artifact' AND json_extract(body,'$.kind')='REPORT' AND json_extract(body,'$.content_hash')=?", project, Digest(body)).Scan(&prior)
	if err == nil {
		return Decode([]byte(prior))
	}
	if err != sql.ErrNoRows {
		return nil, err
	}
	u, err := s.upload(tx, p, project, body)
	if err != nil {
		return nil, err
	}
	return s.sealArtifact(tx, p, project, Object{"run_id": nil, "kind": "REPORT", "evidence_kind": "GENERATED", "measurement_mode": "LIVE", "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "application/vnd.researchos.source-health.v1+json", "byte_size": len(body), "input_refs": []any{Ref(cursor, "SourceCursor"), Ref(profile, "ProjectProfile")}, "source_refs": refs, "produced_by": p.ID, "access_class": "PROJECT"}, true)
}

func (s *Service) persistSourceHealth(ctx context.Context, token, project string, cursor, config Object, result SourceCapture) (Object, error) {
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()
	p, err := authenticate(tx, token)
	if err != nil {
		return nil, err
	}
	if !p.HasRole("SOURCE_ADAPTER") || !p.Allowed(project, "", "", false) {
		return nil, Fail(403, "FORBIDDEN", "source adapter project grant required")
	}
	current, err := load(tx, project, "SourceCursor", Str(cursor, "id"))
	if err != nil {
		return nil, err
	}
	if Hash(Ref(current, "SourceCursor")) != Hash(Ref(cursor, "SourceCursor")) {
		return nil, Fail(409, "STATE_CONFLICT", "source cursor changed during fetch")
	}
	profile, err := singleton(tx, project, "ProjectProfile")
	if err != nil {
		return nil, err
	}
	enabled := false
	for _, v := range Arr(profile, "source_configs") {
		c := v.(map[string]any)
		if c["enabled"] == true && Hash(c) == Hash(config) {
			enabled = true
		}
	}
	if !enabled {
		return nil, Fail(409, "STATE_CONFLICT", "source configuration changed during fetch")
	}
	a, err := s.sealSourceHealth(tx, p, project, cursor, config, result)
	if err != nil {
		return nil, err
	}
	if result.Health.Status == "NOT_CONFIGURED" {
		request := Object{"category": "CREDENTIAL", "account_ref": nil, "reason_code": "RESEARCH_SOURCE_NOT_CONFIGURED:" + Str(config, "source_id"), "summary": "Required research source backend is not configured", "blocked_task_ids": Empty(), "continuable_task_ids": Empty(), "completed_artifact_refs": Empty(), "requested_capability": "Configure source " + Str(config, "source_id"), "estimated_cost": nil, "cost_known": false, "resume_checkpoint_ref": nil}
		if _, err = s.createResourceRequest(tx, p, project, request); err != nil {
			return nil, err
		}
	}
	return a, tx.Commit()
}

// latestSourceHealth validates immutable bytes, exact config/window and every
// substantive body reference. A report can explain a gap, never prove coverage.
func (s *Service) latestSourceHealth(tx *sql.Tx, project string, profile, config, cursor Object, from, to time.Time) (*sources.SourceHealth, error) {
	rows, err := tx.Query("SELECT body FROM domain_objects WHERE project=? AND kind='Artifact' AND json_extract(body,'$.kind')='REPORT' AND json_extract(body,'$.media_type')='application/vnd.researchos.source-health.v1+json' ORDER BY json_extract(body,'$.created_at') DESC, rowid DESC", project)
	if err != nil {
		return nil, err
	}
	var reports []Object
	for rows.Next() {
		var raw string
		if err = rows.Scan(&raw); err != nil {
			rows.Close()
			return nil, err
		}
		a, e := Decode([]byte(raw))
		if e != nil {
			rows.Close()
			return nil, e
		}
		reports = append(reports, a)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return nil, err
	}
	var latest *sources.SourceHealth
	readIDs := map[string]bool{}
	var observedMin, observedMax *time.Time
	for _, a := range reports {
		if a["validity"] != "CURRENT" || a["evidence_kind"] != "GENERATED" {
			continue
		}
		var raw []byte
		if e := tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, a["storage_key"]).Scan(&raw); e != nil {
			continue
		}
		if Digest(raw) != a["content_hash"] {
			continue
		}
		d, e := Decode(raw)
		if e != nil || d["schema"] != sourceHealthSchema || d["source_id"] != config["source_id"] || d["query_hash"] != Hash(config["query"]) || d["config_hash"] != Hash(config) || Hash(d["profile_ref"]) != Hash(Ref(profile, "ProjectProfile")) || Hash(d["source_refs"]) != Hash(a["source_refs"]) {
			continue
		}
		cr, ok := d["cursor_ref"].(map[string]any)
		if !ok || cr["id"] != cursor["id"] || Hash(a["input_refs"]) != Hash([]any{cr, d["profile_ref"]}) {
			continue
		}
		if _, e = version(tx, project, cr); e != nil {
			continue
		}
		var h sources.SourceHealth
		if json.Unmarshal(Bytes(d["health"]), &h) != nil || !h.RequestedFrom.Equal(from) || !h.RequestedTo.Equal(to) {
			continue
		}
		switch h.Status {
		case "NOT_CONFIGURED", "PARTIAL", "COMPLETE", "RATE_LIMITED", "UNAVAILABLE":
		default:
			continue
		}
		if h.FullReadCount > 0 {
			refs := Arr(a, "source_refs")
			if len(refs) < 3 {
				continue
			}
			ref, ok := refs[0].(map[string]any)
			if !ok || ref["entity_type"] != "Artifact" {
				continue
			}
			manifest, e := load(tx, project, "Artifact", Str(ref, "id"))
			if e != nil || manifest["kind"] != "MANIFEST" || !verifiedSourceBytes(tx, project, manifest) {
				continue
			}
			var body []byte
			if tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, manifest["storage_key"]).Scan(&body) != nil {
				continue
			}
			doc, e := Decode(body)
			if e != nil || doc["source_id"] != config["source_id"] || doc["query_hash"] != cursor["query_hash"] || doc["window_from"] != from.UTC().Format(time.RFC3339Nano) || doc["window_to"] != to.UTC().Format(time.RFC3339Nano) || Hash(refs[1:]) != Hash(manifest["source_refs"]) {
				continue
			}
		}
		valid, reads := true, 0
		itemIDs := map[string]time.Time{}
		for _, r := range Arr(a, "source_refs") {
			ref, ok := r.(map[string]any)
			if !ok {
				valid = false
				break
			}
			obj, e := load(tx, project, Str(ref, "entity_type"), Str(ref, "id"))
			if e != nil || Hash(Ref(obj, Str(ref, "entity_type"))) != Hash(ref) || obj["validity"] != "CURRENT" {
				valid = false
				break
			}
			if ref["entity_type"] == "Artifact" {
				if !verifiedSourceBytes(tx, project, obj) {
					valid = false
					break
				}
			}
			if ref["entity_type"] == "Evidence" {
				snapRef, ok := obj["snapshot_artifact_ref"].(map[string]any)
				if !ok {
					valid = false
					break
				}
				snap, e := load(tx, project, "Artifact", Str(snapRef, "id"))
				if e != nil || snap["content_hash"] != snapRef["content_hash"] || !verifiedSourceBytes(tx, project, snap) {
					valid = false
					break
				}
				published, e := time.Parse(time.RFC3339Nano, Str(obj, "published_at"))
				if e != nil || published.Before(from) || !published.Before(to) {
					valid = false
					break
				}
				itemIDs[Str(obj, "id")] = published
				reads++
			}
		}
		if !valid || reads != h.FullReadCount {
			continue
		}
		if latest == nil {
			selected := h
			latest = &selected
		}
		for id, published := range itemIDs {
			readIDs[id] = true
			if observedMin == nil || published.Before(*observedMin) {
				v := published
				observedMin = &v
			}
			if observedMax == nil || published.After(*observedMax) {
				v := published
				observedMax = &v
			}
		}
	}
	if latest != nil {
		latest.FullReadCount = len(readIDs)
		if len(readIDs) > 0 {
			latest.ObservedFrom, latest.ObservedTo = observedMin, observedMax
		}
	}
	return latest, nil
}

func failedSourceRaw(result SourceCapture) any {
	if result.RawArtifact == nil && len(result.Page.RawResponse) > 0 {
		return result.Page.RawResponse
	}
	return nil
}
func verifiedSourceBytes(tx *sql.Tx, project string, a Object) bool {
	var b []byte
	return a["validity"] == "CURRENT" && tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, a["storage_key"]).Scan(&b) == nil && Digest(b) == a["content_hash"]
}
