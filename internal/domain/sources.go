package domain

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"net/url"
	"researchos.local/research-os/adapters/sources"
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
	o := Merge(Base(project), b)
	o["validity"] = "CURRENT"
	o["verification_status"] = "UNVERIFIED"
	o["verified_by_run_id"] = nil
	if err := s.put(tx, "Evidence", o); err != nil {
		return nil, err
	}
	return o, nil
}

// advanceSourceCursor follows immutable, adapter-produced page checkpoints.
// Evidence elsewhere in the project cannot prove this query/window complete.
func (s *Service) advanceSourceCursor(tx *sql.Tx, project, id string, b Object) (Object, error) {
	cursor, err := load(tx, project, "SourceCursor", id)
	if err != nil {
		return nil, err
	}
	profile, err := singleton(tx, project, "ProjectProfile")
	if err != nil {
		return nil, err
	}
	configured := false
	for _, v := range Arr(profile, "source_configs") {
		c := v.(map[string]any)
		if c["source_id"] == cursor["source_id"] && Hash(c["query"]) == cursor["query_hash"] && c["enabled"] == true {
			configured = true
		}
	}
	if !configured {
		return nil, Fail(409, "STATE_CONFLICT", "cursor source configuration changed")
	}
	for _, key := range []string{"covered_until", "last_success_at", "retry_after", "pending_window_from", "pending_window_to"} {
		if v, ok := b[key].(string); ok {
			if _, err := time.Parse(time.RFC3339Nano, v); err != nil || v == "" {
				return nil, Fail(400, "INVALID_REQUEST", fmt.Sprintf("invalid %s", key))
			}
		}
	}
	oldCovered, _ := cursor["covered_until"].(string)
	newCovered, _ := b["covered_until"].(string)
	if oldCovered != "" {
		oldTime, _ := time.Parse(time.RFC3339Nano, oldCovered)
		newTime, e := time.Parse(time.RFC3339Nano, newCovered)
		if e != nil || newTime.Before(oldTime) {
			return nil, Fail(409, "STATE_CONFLICT", "source coverage cannot move backwards")
		}
	}
	if b["retry_after"] != nil {
		for _, key := range []string{"covered_until", "last_success_at", "opaque_cursor"} {
			if b[key] != cursor[key] {
				return nil, Fail(409, "STATE_CONFLICT", "failed window cannot advance cursor")
			}
		}
	} else if newCovered != oldCovered || b["opaque_cursor"] != cursor["opaque_cursor"] || b["last_success_at"] != cursor["last_success_at"] {
		from := Str(cursor, "pending_window_from")
		to := Str(cursor, "pending_window_to")
		if from == "" {
			from = Str(b, "pending_window_from")
		}
		if to == "" {
			to = Str(b, "pending_window_to")
		}
		if newCovered != oldCovered && to == "" {
			// A completed update clears pending fields; find its unique persisted window.
			rows, e := tx.Query("SELECT DISTINCT window_from FROM source_pages WHERE project=? AND cursor_id=? AND source_id=? AND query_hash=? AND window_to=?", project, id, cursor["source_id"], cursor["query_hash"], newCovered)
			if e != nil {
				return nil, e
			}
			var matches []string
			for rows.Next() {
				var x string
				if e = rows.Scan(&x); e != nil {
					rows.Close()
					return nil, e
				}
				matches = append(matches, x)
			}
			e = rows.Err()
			rows.Close()
			if e != nil {
				return nil, e
			}
			if len(matches) != 1 {
				return nil, Fail(422, "GATE_FAILED", "unique completed window checkpoint required")
			}
			from, to = matches[0], newCovered
		}
		if from == "" || to == "" {
			return nil, Fail(422, "GATE_FAILED", "pending page window required")
		}
		ft, e1 := time.Parse(time.RFC3339Nano, from)
		tt, e2 := time.Parse(time.RFC3339Nano, to)
		if e1 != nil || e2 != nil || !ft.Before(tt) {
			return nil, Fail(400, "INVALID_REQUEST", "invalid page window")
		}
		if oldCovered != "" {
			ot, _ := time.Parse(time.RFC3339Nano, oldCovered)
			if !ft.Equal(ot) {
				return nil, Fail(422, "GATE_FAILED", "source coverage window has a gap")
			}
		}
		last, e := time.Parse(time.RFC3339Nano, Str(b, "last_success_at"))
		if e != nil {
			return nil, Fail(422, "GATE_FAILED", "page success time required")
		}
		final, e := s.verifySourcePageChain(tx, project, cursor, from, to, last, Str(b, "opaque_cursor"))
		if e != nil {
			return nil, e
		}
		if final {
			nt, e := time.Parse(time.RFC3339Nano, newCovered)
			if e != nil || !nt.Equal(tt) || b["opaque_cursor"] != nil || b["pending_window_from"] != nil || b["pending_window_to"] != nil {
				return nil, Fail(422, "GATE_FAILED", "completed page must close exact pending window")
			}
		} else if newCovered != oldCovered || Str(b, "opaque_cursor") == "" || b["pending_window_from"] != from || b["pending_window_to"] != to {
			return nil, Fail(422, "GATE_FAILED", "incomplete page may only advance its page cursor")
		}
	}
	if err := bump(cursor); err != nil {
		return nil, err
	}
	for k, v := range b {
		cursor[k] = v
	}
	return cursor, s.put(tx, "SourceCursor", cursor)
}

func (s *Service) verifySourcePageChain(tx *sql.Tx, project string, cursor Object, from, to string, success time.Time, wantNext string) (bool, error) {
	next := ""
	seen := map[string]bool{}
	oldNext := Str(cursor, "opaque_cursor")
	passedOld := oldNext == ""
	for i := 0; i < 1000; i++ {
		if seen[next] {
			return false, Fail(422, "GATE_FAILED", "source page cursor loop")
		}
		seen[next] = true
		if next == oldNext {
			passedOld = true
		}
		var source, query, out, rawID, refsRaw, fetched string
		var complete int
		e := tx.QueryRow("SELECT source_id,query_hash,page_cursor_out,raw_artifact_id,item_refs_json,complete,fetched_at FROM source_pages WHERE project=? AND cursor_id=? AND window_from=? AND window_to=? AND page_cursor_in=?", project, cursor["id"], from, to, next).Scan(&source, &query, &out, &rawID, &refsRaw, &complete, &fetched)
		if errors.Is(e, sql.ErrNoRows) {
			return false, Fail(422, "GATE_FAILED", "source page checkpoint missing")
		}
		if e != nil {
			return false, e
		}
		if source != cursor["source_id"] || query != cursor["query_hash"] {
			return false, Fail(422, "GATE_FAILED", "source page query mismatch")
		}
		ft, e := time.Parse(time.RFC3339Nano, fetched)
		if e != nil || ft.After(success) {
			return false, Fail(422, "GATE_FAILED", "source page was not fetched before success")
		}
		artifact, e := load(tx, project, "Artifact", rawID)
		if e != nil || artifact["validity"] != "CURRENT" || artifact["measurement_mode"] != "LIVE" || artifact["evidence_kind"] != "OBSERVED" {
			return false, Fail(422, "GATE_FAILED", "raw source page snapshot missing")
		}
		var ids []string
		if e = json.Unmarshal([]byte(refsRaw), &ids); e != nil {
			return false, Fail(422, "GATE_FAILED", "invalid page item references")
		}
		for _, id := range ids {
			ev, e := load(tx, project, "Evidence", id)
			if e != nil || ev["evidence_kind"] != "OBSERVED" || ev["validity"] != "CURRENT" {
				return false, Fail(422, "GATE_FAILED", "source page evidence missing")
			}
			ref, ok := ev["snapshot_artifact_ref"].(map[string]any)
			if !ok {
				return false, Fail(422, "GATE_FAILED", "source item snapshot missing")
			}
			snap, e := load(tx, project, "Artifact", Str(ref, "id"))
			if e != nil || snap["validity"] != "CURRENT" || snap["content_hash"] != ref["content_hash"] {
				return false, Fail(422, "GATE_FAILED", "source item snapshot invalid")
			}
		}
		if complete == 1 {
			if wantNext != "" || !passedOld {
				return false, Fail(422, "GATE_FAILED", "completed page has no next cursor")
			}
			return true, nil
		}
		if out == wantNext {
			if !passedOld || out == oldNext {
				return false, Fail(422, "GATE_FAILED", "source page cursor cannot move backwards")
			}
			return false, nil
		}
		next = out
	}
	return false, Fail(422, "GATE_FAILED", "source pagination depth exceeded")
}

// SourceCapture is the product adapter's durable result. Only a trusted
// adapter fetch can create a page checkpoint; HTTP callers cannot report one.
type SourceCapture struct {
	Page        sources.Page
	RawArtifact Object
	Evidence    []Object
	Manifest    Object
}

// CaptureSourcePage chooses the configured public provider, authenticates the
// current SOURCE_ADAPTER credential, and seals its raw page and full items.
func (s *Service) CaptureSourcePage(ctx context.Context, token, project, cursorID string, from, to time.Time, limit int, browserActPath, browserID string) (SourceCapture, error) {
	config, cursor, e := s.sourceConfig(ctx, token, project, cursorID)
	if e != nil {
		return SourceCapture{}, e
	}
	var adapter sources.Adapter
	allowed := []string{}
	for _, v := range Arr(config, "allowed_origins") {
		allowed = append(allowed, v.(string))
	}
	switch config["kind"] {
	case "GITHUB":
		adapter = sources.GitHubReleases{AllowedOrigins: allowed}
	case "PAPER":
		adapter = &sources.Arxiv{AllowedOrigins: allowed}
	case "X":
		if browserActPath == "" || browserID == "" {
			return SourceCapture{}, Fail(503, "RESOURCE_UNAVAILABLE", "authorized X browser unavailable")
		}
		adapter = sources.XBrowser{Runner: sources.BrowserActCLI{Executable: browserActPath}, BrowserID: browserID}
	default:
		return SourceCapture{}, Fail(400, "INVALID_REQUEST", "unsupported source kind")
	}
	return s.captureSourcePage(ctx, token, project, cursor, config, from, to, limit, adapter)
}

func (s *Service) sourceConfig(ctx context.Context, token, project, cursorID string) (Object, Object, error) {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, nil, e
	}
	defer tx.Rollback()
	p, e := authenticate(tx, token)
	if e != nil {
		return nil, nil, e
	}
	if !p.HasRole("SOURCE_ADAPTER") || !p.Allowed(project, "", "", false) {
		return nil, nil, Fail(403, "FORBIDDEN", "source adapter project grant required")
	}
	cursor, e := load(tx, project, "SourceCursor", cursorID)
	if e != nil {
		return nil, nil, e
	}
	profile, e := singleton(tx, project, "ProjectProfile")
	if e != nil {
		return nil, nil, e
	}
	for _, v := range Arr(profile, "source_configs") {
		c := v.(map[string]any)
		if c["source_id"] == cursor["source_id"] && c["enabled"] == true && Hash(c["query"]) == cursor["query_hash"] {
			return c, cursor, nil
		}
	}
	return nil, nil, Fail(409, "STATE_CONFLICT", "source configuration no longer matches cursor")
}

func (s *Service) captureSourcePage(ctx context.Context, token, project string, cursor, config Object, from, to time.Time, limit int, adapter sources.Adapter) (SourceCapture, error) {
	var result SourceCapture
	if from.IsZero() || !from.Before(to) || to.After(time.Now().Add(time.Minute)) || limit < 1 || limit > 100 {
		return result, Fail(400, "INVALID_REQUEST", "invalid bounded source window")
	}
	if raw:=Str(cursor,"retry_after"); raw!="" {
		wait,e:=time.Parse(time.RFC3339Nano,raw)
		if e!=nil {return result,Fail(409,"STATE_CONFLICT","invalid persisted source retry time")}
		if time.Now().Before(wait) {result.Page=sources.Page{RequestedFrom:from.UTC(),RequestedTo:to.UTC(),Failure:"RATE_LIMITED",RetryAfter:&wait}; return result,nil}
	}
	pageCursor := Str(cursor, "opaque_cursor")
	q := sources.Query{SourceID: Str(config, "source_id"), Text: Str(config, "query"), From: from.UTC(), To: to.UTC(), Cursor: pageCursor, Limit: limit}
	page, e := adapter.Fetch(ctx, q)
	result.Page = page
	if e != nil || page.Failure != "" {
		return result, e
	}
	if !page.Complete && page.NextCursor == "" && len(page.Items) == 0 {
		return result, Fail(422, "GATE_FAILED", "source returned no verifiable item or cursor")
	}
	if len(page.RawResponse) == 0 || page.RawMediaType == "" {
		return result, Fail(422, "GATE_FAILED", "raw provider page missing")
	}
	if page.FetchedAt.IsZero() || len(page.RequestURLs) == 0 || len(page.FinalURLs) == 0 {
		return result, Fail(422, "GATE_FAILED", "actual request and final URL trace required")
	}
	for _, rawURL := range append(append([]string{}, page.RequestURLs...), page.FinalURLs...) {
		u, e := url.Parse(rawURL)
		if e != nil || u.Scheme != "https" || u.User != nil || u.Host == "" {
			return result, Fail(422, "GATE_FAILED", "source request URL is not public HTTPS")
		}
		allowed := false
		for _, v := range Arr(config, "allowed_origins") {
			origin, e := url.Parse(v.(string))
			if e == nil && strings.EqualFold(origin.Scheme+"://"+origin.Host, u.Scheme+"://"+u.Host) {
				allowed = true
			}
		}
		if !allowed {
			return result, Fail(422, "GATE_FAILED", "source request escaped configured origin")
		}
	}
	if !page.RequestedFrom.Equal(q.From) || !page.RequestedTo.Equal(q.To) {
		return result, Fail(422, "GATE_FAILED", "provider window mismatch")
	}
	// Never hold the DB transaction while the public provider is on the wire.
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return result, e
	}
	defer tx.Rollback()
	p, e := authenticate(tx, token)
	if e != nil {
		return result, e
	}
	if !p.HasRole("SOURCE_ADAPTER") || !p.Allowed(project, "", "", false) {
		return result, Fail(403, "FORBIDDEN", "source adapter project grant required")
	}
	current, e := load(tx, project, "SourceCursor", Str(cursor, "id"))
	if e != nil {
		return result, e
	}
	if current["revision"] != cursor["revision"] || current["opaque_cursor"] != cursor["opaque_cursor"] || current["source_id"] != config["source_id"] || current["query_hash"] != Hash(config["query"]) {
		return result, Fail(409, "STATE_CONFLICT", "source cursor changed during fetch")
	}
	profile, e := singleton(tx, project, "ProjectProfile")
	if e != nil {
		return result, e
	}
	enabled := false
	for _, v := range Arr(profile, "source_configs") {
		c := v.(map[string]any)
		if c["source_id"] == config["source_id"] && c["enabled"] == true && Hash(c) == Hash(config) {
			enabled = true
		}
	}
	if !enabled {
		return result, Fail(409, "STATE_CONFLICT", "source configuration changed during fetch")
	}
	raw, e := s.sealSourceBytes(tx, p, project, current, page.RawResponse, page.RawMediaType, nil)
	if e != nil {
		return result, e
	}
	result.RawArtifact = raw
	refs := []string{}
	for _, item := range page.Items {
		if item.SourceID != config["source_id"] || item.CanonicalURL == "" || item.UpstreamID == "" || len(item.Body) == 0 || item.MediaType == "" || item.PublishedAt.IsZero() || item.PublishedAt.Before(q.From) || !item.PublishedAt.Before(q.To) {
			return SourceCapture{}, Fail(422, "GATE_FAILED", "source item is incomplete or outside window")
		}
		snapshot, e := s.sealSourceBytes(tx, p, project, current, item.Body, item.MediaType, raw)
		if e != nil {
			return SourceCapture{}, e
		}
		var modified any
		if item.ModifiedAt != nil {
			modified = item.ModifiedAt.UTC().Format(time.RFC3339Nano)
		}
		var author, revision any
		if item.Author != "" {
			author = item.Author
		}
		if item.UpstreamRevision != "" {
			revision = item.UpstreamRevision
		}
		body := Object{"claim": "Public source item at " + item.CanonicalURL, "stance": "CONTEXT", "evidence_kind": "OBSERVED", "source_kind": config["kind"], "canonical_url": item.CanonicalURL, "publisher": author, "upstream_revision": revision, "published_at": item.PublishedAt.UTC().Format(time.RFC3339Nano), "modified_at": modified, "retrieved_at": Now(), "time_status": "KNOWN", "snapshot_artifact_ref": Ref(snapshot, "Artifact"), "locator": item.Locator, "independence_key": Hash(item.CanonicalURL), "origin_evidence_id": nil, "discovery_urls": Empty(), "license_status": "UNKNOWN", "license_expression": nil}
		ev, e := s.createEvidence(tx, project, body)
		if e != nil {
			return SourceCapture{}, e
		}
		result.Evidence = append(result.Evidence, ev)
		refs = append(refs, Str(ev, "id"))
	}
	// X UI has no durable provider cursor. Its visible articles are still
	// evidence, but can never become an exhaustive page checkpoint.
	if config["kind"] != "X" {
		if !page.Complete && page.NextCursor == "" {
			return SourceCapture{}, Fail(422, "GATE_FAILED", "incomplete page lacks resumable provider cursor")
		}
		encoded, _ := json.Marshal(refs)
		complete := 0
		if page.Complete {
			complete = 1
		}
		_, e = tx.Exec("INSERT INTO source_pages(project,cursor_id,source_id,query_hash,window_from,window_to,page_cursor_in,page_cursor_out,raw_artifact_id,item_refs_json,complete,fetched_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", project, cursor["id"], config["source_id"], cursor["query_hash"], q.From.Format(time.RFC3339Nano), q.To.Format(time.RFC3339Nano), pageCursor, page.NextCursor, raw["id"], string(encoded), complete, Now())
		if e != nil {
			return SourceCapture{}, e
		}
	}
	manifestRefs := []any{Ref(raw, "Artifact")}
	for _, ev := range result.Evidence {
		manifestRefs = append(manifestRefs, Ref(ev, "Evidence"))
	}
	var observedFrom, observedTo any
	if page.ObservedFrom != nil {
		observedFrom = page.ObservedFrom.UTC().Format(time.RFC3339Nano)
	}
	if page.ObservedTo != nil {
		observedTo = page.ObservedTo.UTC().Format(time.RFC3339Nano)
	}
	manifestBytes := Bytes(Object{"source_id": config["source_id"], "query_hash": cursor["query_hash"], "window_from": q.From.Format(time.RFC3339Nano), "window_to": q.To.Format(time.RFC3339Nano), "observed_from": observedFrom, "observed_to": observedTo, "fetched_at": page.FetchedAt.UTC().Format(time.RFC3339Nano), "request_urls": page.RequestURLs, "final_urls": page.FinalURLs, "page_cursor_in": pageCursor, "page_cursor_out": page.NextCursor, "complete": page.Complete && config["kind"] != "X", "raw_artifact_ref": Ref(raw, "Artifact"), "evidence_refs": manifestRefs[1:]})
	u, e := s.upload(tx, p, project, manifestBytes)
	if e != nil {
		return SourceCapture{}, e
	}
	manifest, e := s.seal(tx, p, project, Object{"run_id": nil, "kind": "MANIFEST", "evidence_kind": "GENERATED", "measurement_mode": "LIVE", "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "application/json", "byte_size": len(manifestBytes), "input_refs": []any{Ref(cursor, "SourceCursor")}, "source_refs": manifestRefs, "produced_by": p.ID, "access_class": "PROJECT"})
	if e != nil {
		return SourceCapture{}, e
	}
	result.Manifest = manifest
	eventType := "PROJECT_UPDATED"
	if len(result.Evidence) > 0 {
		eventType = "EVIDENCE_ADDED"
	}
	if e = s.event(tx, project, "Artifact", manifest, p.ID, ID(), eventType); e != nil {
		return SourceCapture{}, e
	}
	return result, tx.Commit()
}

func (s *Service) sealSourceBytes(tx *sql.Tx, p Principal, project string, cursor Object, body []byte, media string, raw Object) (Object, error) {
	u, e := s.upload(tx, p, project, body)
	if e != nil {
		return nil, e
	}
	sourceRefs := Empty()
	if raw != nil {
		sourceRefs = []any{Ref(raw, "Artifact")}
	}
	return s.seal(tx, p, project, Object{"run_id": nil, "kind": "SOURCE_SNAPSHOT", "evidence_kind": "OBSERVED", "measurement_mode": "LIVE", "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": media, "byte_size": len(body), "input_refs": []any{Ref(cursor, "SourceCursor")}, "source_refs": sourceRefs, "produced_by": p.ID, "access_class": "PROJECT"})
}
