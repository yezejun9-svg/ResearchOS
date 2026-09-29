package domain

import (
	"database/sql"
	"fmt"
	"net/url"
	"strings"
	"time"
)

// createEvidence registers a sealed source snapshot. The producer cannot turn a
// fixture artifact into observed live evidence or claim an unconfigured origin.
func (s *Service) createEvidence(tx *sql.Tx, project string, b Object) (Object, error) {
	profile, err := singleton(tx, project, "ProjectProfile")
	if err != nil {
		return nil, err
	}
	artifactRef, ok := b["snapshot_artifact_ref"].(map[string]any)
	if !ok || artifactRef["entity_type"] != "Artifact" {
		return nil, Fail(422, "GATE_FAILED", "sealed artifact reference required")
	}
	artifact, err := load(tx, project, "Artifact", Str(artifactRef, "id"))
	if err != nil {
		return nil, Fail(422, "GATE_FAILED", "sealed snapshot unavailable")
	}
	if artifact["validity"] != "CURRENT" || artifact["content_hash"] != artifactRef["content_hash"] {
		return nil, Fail(422, "GATE_FAILED", "snapshot is not current or its hash changed")
	}
	if artifact["evidence_kind"] != b["evidence_kind"] {
		return nil, Fail(422, "GATE_FAILED", "snapshot evidence kind differs")
	}
	if b["evidence_kind"] == "OBSERVED" && artifact["measurement_mode"] != "LIVE" {
		return nil, Fail(422, "GATE_FAILED", "observed evidence requires a live snapshot")
	}
	if b["source_kind"] == "GITHUB" || b["source_kind"] == "X" || b["source_kind"] == "PAPER" {
		canonical, err := url.Parse(Str(b, "canonical_url"))
		if err != nil || canonical.Scheme != "https" || canonical.Host == "" || canonical.User != nil {
			return nil, Fail(422, "GATE_FAILED", "public source requires an HTTPS canonical URL")
		}
		origin := canonical.Scheme + "://" + strings.ToLower(canonical.Host)
		configured := false
		for _, entry := range Arr(profile, "source_configs") {
			config := entry.(map[string]any)
			if config["kind"] != b["source_kind"] || config["enabled"] != true {
				continue
			}
			for _, raw := range Arr(config, "allowed_origins") {
				u, e := url.Parse(raw.(string))
				if e == nil && u.Scheme == "https" && strings.EqualFold(origin, u.Scheme+"://"+u.Host) {
					configured = true
				}
			}
		}
		if !configured {
			return nil, Fail(403, "FORBIDDEN", "source origin is not enabled for this project")
		}
	}
	if b["published_at"] == nil && b["time_status"] == "KNOWN" {
		return nil, Fail(422, "GATE_FAILED", "unknown publication time cannot be marked known")
	}
	if b["publisher"] == nil || b["upstream_revision"] == nil {
		return nil, Fail(422, "GATE_FAILED", "source author and version are required for this evidence")
	}
	o := Merge(Base(project), b)
	o["validity"] = "CURRENT"
	o["verification_status"] = "UNVERIFIED"
	o["verified_by_run_id"] = nil
	if err := s.put(tx, "Evidence", o); err != nil {
		return nil, err
	}
	return o, nil
}

// advanceSourceCursor never claims a completed interval unless that interval
// has a persisted observed snapshot. An empty valid page may update the retry
// point but leaves covered_until unchanged until a durable checkpoint exists.
func (s *Service) advanceSourceCursor(tx *sql.Tx, project, id string, b Object) (Object, error) {
	cursor, err := load(tx, project, "SourceCursor", id)
	if err != nil {
		return nil, err
	}
	oldCovered, _ := cursor["covered_until"].(string)
	newCovered, _ := b["covered_until"].(string)
	if oldCovered != "" {
		if newCovered == "" {
			return nil, Fail(409, "STATE_CONFLICT", "source coverage cannot be erased")
		}
		oldTime, e1 := time.Parse(time.RFC3339Nano, oldCovered)
		newTime, e2 := time.Parse(time.RFC3339Nano, newCovered)
		if e1 != nil || e2 != nil || newTime.Before(oldTime) {
			return nil, Fail(409, "STATE_CONFLICT", "source coverage cannot move backwards")
		}
	}
	if newCovered != "" && newCovered != oldCovered {
		profile, e := singleton(tx, project, "ProjectProfile")
		if e != nil {
			return nil, e
		}
		var kind string
		for _, entry := range Arr(profile, "source_configs") {
			c := entry.(map[string]any)
			if c["source_id"] == cursor["source_id"] && Hash(c["query"]) == cursor["query_hash"] {
				kind = Str(c, "kind")
			}
		}
		if kind == "" {
			return nil, Fail(409, "STATE_CONFLICT", "cursor source configuration changed")
		}
		var count int
		err = tx.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Evidence' AND json_extract(body,'$.source_kind')=? AND json_extract(body,'$.evidence_kind')='OBSERVED' AND json_extract(body,'$.retrieved_at')<=?", project, kind, Str(b, "last_success_at")).Scan(&count)
		if err != nil {
			return nil, err
		}
		if count == 0 {
			return nil, Fail(422, "GATE_FAILED", "coverage requires persisted observed evidence")
		}
	}
	for _, key := range []string{"covered_until", "last_success_at", "retry_after", "pending_window_from", "pending_window_to"} {
		if v, ok := b[key].(string); ok {
			if _, err := time.Parse(time.RFC3339Nano, v); err != nil {
				return nil, Fail(400, "INVALID_REQUEST", fmt.Sprintf("invalid %s", key))
			}
		}
	}
	if b["retry_after"] != nil && b["covered_until"] != cursor["covered_until"] {
		return nil, Fail(409, "STATE_CONFLICT", "rate-limited window cannot be marked covered")
	}
	if err := bump(cursor); err != nil {
		return nil, err
	}
	for k, v := range b {
		cursor[k] = v
	}
	return cursor, s.put(tx, "SourceCursor", cursor)
}
