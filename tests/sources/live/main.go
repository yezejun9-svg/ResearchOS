// Command live exercises the product source adapter against one real public
// provider and stores the sealed snapshots in an isolated SQLite product DB.
package main

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"researchos.local/research-os/adapters/sources"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/store"
	"strings"
	"time"
)

type report struct {
	Health            sources.SourceHealth `json:"health"`
	HealthArtifactRef domain.Object        `json:"health_artifact_ref,omitempty"`
	Query             string               `json:"query"`
	SourceID          string               `json:"source_id"`
	Status            string               `json:"status"`
	Scope             string               `json:"scope"`
	Source            string               `json:"source"`
	ProjectID         string               `json:"project_id,omitempty"`
	CursorID          string               `json:"cursor_id,omitempty"`
	WindowFrom        string               `json:"window_from,omitempty"`
	WindowTo          string               `json:"window_to,omitempty"`
	ObservedFrom      any                  `json:"observed_from,omitempty"`
	ObservedTo        any                  `json:"observed_to,omitempty"`
	FetchedAt         string               `json:"fetched_at,omitempty"`
	RequestURLs       []string             `json:"request_urls,omitempty"`
	FinalURLs         []string             `json:"final_urls,omitempty"`
	NextCursor        string               `json:"next_cursor,omitempty"`
	Manifest          map[string]any       `json:"manifest,omitempty"`
	CoveredUntil      any                  `json:"covered_until,omitempty"`
	PageComplete      bool                 `json:"page_complete"`
	Failure           string               `json:"failure,omitempty"`
	Items             []map[string]any     `json:"items,omitempty"`
	RawPage           map[string]any       `json:"raw_page,omitempty"`
	ClaimCheck        map[string]any       `json:"claim_check,omitempty"`
	DBPath            string               `json:"db_path,omitempty"`
}

func main() {
	r := report{Status: "FAIL", Scope: "LIVE_SERVICE", Source: os.Getenv("RESEARCHOS_SOURCE_KIND"), Items: []map[string]any{}}
	e := run(&r)
	if e != nil {
		r.Failure = e.Error()
	}
	b, _ := json.Marshal(r)
	if dir := os.Getenv("RESEARCHOS_SOURCE_OUTPUT_DIR"); dir != "" {
		if err := os.MkdirAll(dir, 0755); err == nil {
			path := filepath.Join(dir, "report-"+r.Source+".json")
			if f, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0644); err == nil {
				f.Write(append(b, '\n'))
				f.Close()
			}
		}
	}
	fmt.Println(string(b))
	if e != nil {
		os.Exit(1)
	}
}

func run(r *report) error {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()
	var query string
	var origins []any
	var from time.Time
	switch r.Source {
	case "GITHUB":
		query = "repo:paperclipai/paperclip"
		origins = []any{"https://github.com", "https://api.github.com"}
		from = time.Date(2025, 1, 1, 0, 0, 0, 0, time.UTC)
	case "PAPER":
		query = "id:2304.03442v2"
		origins = []any{"https://arxiv.org", "https://export.arxiv.org"}
		from = time.Date(2023, 1, 1, 0, 0, 0, 0, time.UTC)
	case "X":
		query = "paperclip agents"
		origins = []any{"https://x.com"}
		from = time.Date(2026, 9, 29, 0, 0, 0, 0, time.UTC)
	default:
		return fmt.Errorf("unknown source kind")
	}
	to := time.Now().UTC().Add(-time.Second)
	if !from.Before(to) {
		return fmt.Errorf("source window has not started")
	}
	r.Query = query
	r.WindowFrom = from.Format(time.RFC3339Nano)
	r.WindowTo = to.Format(time.RFC3339Nano)
	dir := os.Getenv("RESEARCHOS_SOURCE_OUTPUT_DIR")
	if dir == "" {
		return fmt.Errorf("source output directory required")
	}
	if e := os.MkdirAll(dir, 0755); e != nil {
		return e
	}
	dbPath := filepath.Join(dir, "live-"+r.Source+".sqlite")
	if _, e := os.Stat(dbPath); e == nil {
		return fmt.Errorf("existing isolated DB must not be overwritten")
	}
	db, e := store.Open(dbPath)
	if e != nil {
		return e
	}
	defer db.Close()
	rootDir, e := os.Getwd()
	if e != nil {
		return e
	}
	relativeDB, e := filepath.Rel(rootDir, dbPath)
	if e != nil {
		return e
	}
	r.DBPath = relativeDB
	if e = store.Bootstrap(ctx, db, "migrations/sqlite/0001_bootstrap.sql"); e != nil {
		return e
	}
	s, e := domain.New(db, "spec/v2.0/contracts", "migrations/sqlite/0002_domain.sql")
	if e != nil {
		return e
	}
	owner := domain.Principal{ID: "w07-live-owner", Roles: []string{"OWNER"}, CanCreateProject: true}
	if e = s.ProvisionPrincipal(ctx, owner); e != nil {
		return e
	}
	ownerToken, e := s.IssueCredential(ctx, owner.ID, 15*time.Minute)
	if e != nil {
		return e
	}
	sourceID := domain.ID()
	r.SourceID = sourceID
	configs := []any{domain.Object{"source_id": sourceID, "kind": r.Source, "required": true, "enabled": true, "query": query, "allowed_origins": origins, "credential_ref": nil}}
	readmeSourceID := ""
	if r.Source == "X" {
		readmeSourceID = domain.ID()
		configs = append(configs, domain.Object{"source_id": readmeSourceID, "kind": "GITHUB", "required": false, "enabled": true, "query": "readme:paperclipai/paperclip", "allowed_origins": []any{"https://github.com", "https://api.github.com"}, "credential_ref": nil})
	}
	projectBody := domain.Object{"name": "W07 live public source probe", "intent": "validate public source snapshot integration", "facts": domain.Empty(), "accepted_scope": []any{"source adapter validation"}, "constraints": domain.Empty(), "source_configs": configs, "source_document_refs": domain.Empty(), "read_snapshot_ids": domain.Empty()}
	project, e := api(s.Handler(), ownerToken, "POST", "/v1/projects", projectBody, "")
	if e != nil {
		return e
	}
	projectID := domain.Str(project, "project_id")
	r.ProjectID = projectID
	adapter := domain.Principal{ID: "w07-live-adapter", Roles: []string{"SOURCE_ADAPTER"}, Grants: []domain.Grant{{ProjectID: projectID}}}
	if e = s.ProvisionPrincipal(ctx, adapter); e != nil {
		return e
	}
	token, e := s.IssueCredential(ctx, adapter.ID, 15*time.Minute)
	if e != nil {
		return e
	}
	var raw string
	e = db.QueryRowContext(ctx, "SELECT body FROM domain_objects WHERE project=? AND kind='SourceCursor' AND json_extract(body,'$.source_id')=?", projectID, sourceID).Scan(&raw)
	if e != nil {
		return e
	}
	cursor, e := domain.Decode([]byte(raw))
	if e != nil {
		return e
	}
	r.CursorID = domain.Str(cursor, "id")
	limit := 1 // one positive item, with an honest pending cursor for further pages
	if r.Source == "X" {
		// The X adapter slices at most twenty visible articles from the search page. Taking one arbitrary post and
		// then asking whether it happens to make a specific claim measures the claim against a sample of one, which
		// is not a coverage statement: an uncorroborated claim from one post is indistinguishable from a page that
		// simply ordered that post first. The whole visible page is taken so the verdict is about the window.
		limit = 20
	}
	capture, e := s.CaptureSourcePage(ctx, token, projectID, r.CursorID, from, to, limit, os.Getenv("RESEARCHOS_BROWSER_ACT"), os.Getenv("RESEARCHOS_BROWSER_ID"))
	r.Health = capture.Health
	if capture.HealthArtifact != nil {
		r.HealthArtifactRef = domain.Ref(capture.HealthArtifact, "Artifact")
	}
	if e != nil {
		return e
	}
	r.PageComplete = capture.Page.Complete
	r.FetchedAt = capture.Page.FetchedAt.UTC().Format(time.RFC3339Nano)
	r.RequestURLs = capture.Page.RequestURLs
	r.FinalURLs = capture.Page.FinalURLs
	r.NextCursor = capture.Page.NextCursor
	if capture.Page.ObservedFrom != nil {
		r.ObservedFrom = capture.Page.ObservedFrom.UTC().Format(time.RFC3339Nano)
	}
	if capture.Page.ObservedTo != nil {
		r.ObservedTo = capture.Page.ObservedTo.UTC().Format(time.RFC3339Nano)
	}
	// A gap in the page is a health record, not a lost read: keep the complete prefix, persist its pending cursor and
	// carry the reason into the report. Only a page that produced no complete item at all counts as a provider failure.
	if capture.Page.Failure != "" && len(capture.Page.Items) == 0 {
		return fmt.Errorf("provider failure: %s (HTTP %d)", capture.Page.Failure, capture.Page.HTTPStatus)
	}
	r.Failure = capture.Page.Failure
	if len(capture.Evidence) != len(capture.Page.Items) {
		return fmt.Errorf("sealed evidence count differs from returned items")
	}
	if len(capture.Evidence) == 0 {
		return fmt.Errorf("real source did not return a full item in selected window")
	}
	if e = verifyArtifact(s.Handler(), token, projectID, capture.RawArtifact, capture.Page.RawResponse); e != nil {
		return e
	}
	r.RawPage = map[string]any{"artifact_id": capture.RawArtifact["id"], "sha256": capture.RawArtifact["content_hash"], "bytes": len(capture.Page.RawResponse), "media_type": capture.Page.RawMediaType}
	r.Manifest = map[string]any{"artifact_id": capture.Manifest["id"], "sha256": capture.Manifest["content_hash"]}
	for i, item := range capture.Page.Items {
		ev := capture.Evidence[i]
		if e = verifyArtifact(s.Handler(), token, projectID, mustArtifact(db, projectID, ev), item.Body); e != nil {
			return e
		}
		if _, e = api(s.Handler(), token, "GET", "/v1/projects/"+projectID+"/evidence/"+domain.Str(ev, "id"), nil, ""); e != nil {
			return e
		}
		r.Items = append(r.Items, map[string]any{"evidence_id": ev["id"], "artifact_ref": ev["snapshot_artifact_ref"], "url": item.CanonicalURL, "author": item.Author, "published_at": item.PublishedAt.UTC().Format(time.RFC3339Nano), "retrieved_at": ev["retrieved_at"], "upstream_revision": item.UpstreamRevision, "upstream_id": item.UpstreamID, "body_bytes": len(item.Body), "body_sha256": domain.Digest(item.Body), "locator": item.Locator})
	}
	if r.Source == "X" {
		r.ClaimCheck, e = captureXPrimaryClaim(ctx, s, db, token, projectID, readmeSourceID, capture, to)
		if e != nil {
			return e
		}
	}
	{ // every kind persists its cursor, X included. Excluding X made the card's resume-from-cursor half unreachable:
		// the read returned a real observed_tail cursor and page_complete false, and the probe simply dropped it, so
		// the next cycle had nothing to resume from and could not tell a pending window from an uncovered one.
		if capture.Page.Complete {
			body := domain.Object{"opaque_cursor": nil, "covered_until": r.WindowTo, "last_success_at": domain.Now(), "retry_after": nil, "pending_window_from": nil, "pending_window_to": nil, "last_cycle_id": nil}
			cursor, e = api(s.Handler(), token, "PUT", "/v1/projects/"+projectID+"/source-cursors/"+r.CursorID, body, fmt.Sprintf("\"r%v\"", cursor["revision"]))
			if e != nil {
				return e
			}
			r.CoveredUntil = cursor["covered_until"]
		} else if capture.Page.NextCursor != "" {
			body := domain.Object{"opaque_cursor": capture.Page.NextCursor, "covered_until": nil, "last_success_at": domain.Now(), "retry_after": nil, "pending_window_from": r.WindowFrom, "pending_window_to": r.WindowTo, "last_cycle_id": nil}
			cursor, e = api(s.Handler(), token, "PUT", "/v1/projects/"+projectID+"/source-cursors/"+r.CursorID, body, fmt.Sprintf("\"r%v\"", cursor["revision"]))
			if e != nil {
				return e
			}
			r.CoveredUntil = cursor["covered_until"]
		}
	}
	r.Status = "PASS"
	return nil
}

func captureXPrimaryClaim(ctx context.Context, s *domain.Service, db *sql.DB, token, projectID, readmeSourceID string, x domain.SourceCapture, to time.Time) (map[string]any, error) {
	const xTopic = "paperclipai/paperclip"
	var xEvidence domain.Object
	var xBody []byte
	for i, item := range x.Page.Items {
		if bytes.Contains(bytes.ToLower(item.Body), []byte(xTopic)) && bytes.Contains(bytes.ToLower(item.Body), []byte("agent management")) {
			xEvidence = x.Evidence[i]
			xBody = item.Body
			break
		}
	}
	if xEvidence == nil {
		if len(x.Evidence) == 0 {
			return nil, fmt.Errorf("no X evidence for disposition")
		}
		return sealXUncorroborated(s, db, token, projectID, x.Evidence[0], x.Page.Items[0].Body, "No relevant corroborated claim in this visible observation")
	}
	var readmeCursorID string
	if e := db.QueryRowContext(ctx, "SELECT id FROM domain_objects WHERE project=? AND kind='SourceCursor' AND json_extract(body,'$.source_id')=?", projectID, readmeSourceID).Scan(&readmeCursorID); e != nil {
		return nil, e
	}
	from := time.Date(2025, 1, 1, 0, 0, 0, 0, time.UTC)
	primary, e := s.CaptureSourcePage(ctx, token, projectID, readmeCursorID, from, to, 1, "", "")
	if e != nil {
		return sealXUncorroborated(s, db, token, projectID, xEvidence, xBody, "Primary source unavailable: "+e.Error())
	}
	if primary.Page.Failure != "" || len(primary.Page.Items) != 1 || len(primary.Evidence) != 1 {
		return sealXUncorroborated(s, db, token, projectID, xEvidence, xBody, "Primary source did not corroborate the claim: "+primary.Page.Failure)
	}
	primaryItem := primary.Page.Items[0]
	primaryEvidence := primary.Evidence[0]
	if !bytes.Contains(bytes.ToLower(primaryItem.Body), []byte("manage ai agents for work")) {
		return sealXUncorroborated(s, db, token, projectID, xEvidence, xBody, "Primary body does not support the narrowed claim")
	}
	result, e := sealXClaimCheck(s, db, token, projectID, xEvidence, primaryEvidence, xBody, primaryItem.Body, primaryItem.CanonicalURL, primaryItem.UpstreamRevision)
	if e != nil {
		return nil, e
	}
	result["request_urls"] = primary.Page.RequestURLs
	result["final_urls"] = primary.Page.FinalURLs
	return result, nil
}

func sealXClaimCheck(s *domain.Service, db *sql.DB, token, projectID string, xEvidence, primaryEvidence domain.Object, xBody, primaryBody []byte, primaryURL, primaryCommit string) (map[string]any, error) {
	const primarySpan = "manage AI agents for work"
	if !bytes.Contains(bytes.ToLower(xBody), []byte("paperclipai/paperclip")) || !bytes.Contains(bytes.ToLower(xBody), []byte("agent management")) || !strings.Contains(strings.ToLower(string(primaryBody)), strings.ToLower(primarySpan)) {
		return nil, fmt.Errorf("X claim or primary README span is missing")
	}
	if e := verifyArtifact(s.Handler(), token, projectID, mustArtifact(db, projectID, xEvidence), xBody); e != nil {
		return nil, e
	}
	if e := verifyArtifact(s.Handler(), token, projectID, mustArtifact(db, projectID, primaryEvidence), primaryBody); e != nil {
		return nil, e
	}
	claim := domain.Object{
		"claim":                "The X post categorizes paperclipai/paperclip as agent management; the project's README describes managing AI agents for work.",
		"conclusion":           "SUPPORTED_NARROW_SCOPE",
		"adoption_authority":   false,
		"x_evidence_ref":       domain.Ref(xEvidence, "Evidence"),
		"x_snapshot_ref":       xEvidence["snapshot_artifact_ref"],
		"x_locator":            "post.text#paperclipai/paperclip+agent management",
		"primary_evidence_ref": domain.Ref(primaryEvidence, "Evidence"),
		"primary_snapshot_ref": primaryEvidence["snapshot_artifact_ref"],
		"primary_url":          primaryURL,
		"primary_commit":       primaryCommit,
		"primary_locator":      "README.md#intro",
		"primary_excerpt":      primarySpan,
		"unverified_claims":    unverifiedXClaims(xBody),
	}
	content := domain.Bytes(claim)
	upload, e := uploadBytes(s.Handler(), token, projectID, content)
	if e != nil {
		return nil, e
	}
	refs := []any{domain.Ref(xEvidence, "Evidence"), domain.Ref(primaryEvidence, "Evidence")}
	state, e := api(s.Handler(), token, "GET", "/v1/projects/"+projectID+"/state", nil, "")
	if e != nil {
		return nil, e
	}
	match, e := domain.ETag(state)
	if e != nil {
		return nil, e
	}
	artifact, e := api(s.Handler(), token, "POST", "/v1/projects/"+projectID+"/artifacts", domain.Object{"run_id": nil, "kind": "MANIFEST", "evidence_kind": "GENERATED", "measurement_mode": "LIVE", "content_hash": upload["content_hash"], "storage_key": upload["storage_key"], "media_type": "application/json", "byte_size": len(content), "input_refs": refs, "source_refs": refs, "produced_by": "w07-live-adapter", "access_class": "PROJECT"}, match)
	if e != nil {
		return nil, e
	}
	if e = verifyArtifact(s.Handler(), token, projectID, artifact, content); e != nil {
		return nil, e
	}
	return map[string]any{"artifact_ref": domain.Ref(artifact, "Artifact"), "x_evidence_ref": domain.Ref(xEvidence, "Evidence"), "primary_evidence_ref": domain.Ref(primaryEvidence, "Evidence"), "primary_snapshot_ref": primaryEvidence["snapshot_artifact_ref"], "primary_url": primaryURL, "primary_commit": primaryCommit, "primary_locator": "README.md#intro", "primary_excerpt": primarySpan, "primary_body_sha256": domain.Digest(primaryBody), "conclusion": "SUPPORTED_NARROW_SCOPE", "adoption_authority": false, "unverified_claims": claim["unverified_claims"], "retrieved_at": primaryEvidence["retrieved_at"]}, nil
}

func unverifiedXClaims(body []byte) []any {
	claims := []any{}
	for _, line := range strings.Split(string(body), "\n") {
		line = strings.TrimSpace(line)
		lower := strings.ToLower(line)
		if line != "" && (strings.Contains(lower, "stars") || strings.Contains(lower, "growth") || strings.Contains(lower, "effectiveness") || strings.Contains(lower, "adoption")) {
			if runes := []rune(line); len(runes) > 240 {
				line = string(runes[:240])
			}
			claims = append(claims, line)
			if len(claims) == 8 {
				break
			}
		}
	}
	if len(claims) == 0 {
		claims = append(claims, "Any X growth, usage or effectiveness claim is unverified without its own primary source.")
	}
	return claims
}

func uploadBytes(h http.Handler, token, project string, body []byte) (domain.Object, error) {
	request := httptest.NewRequest("POST", "/v1/projects/"+project+"/content", bytes.NewReader(body))
	request.Header.Set("Authorization", "Bearer "+token)
	request.Header.Set("Idempotency-Key", domain.ID())
	w := httptest.NewRecorder()
	h.ServeHTTP(w, request)
	var result domain.Object
	if e := json.Unmarshal(w.Body.Bytes(), &result); e != nil {
		return nil, e
	}
	if w.Code != 201 {
		return nil, fmt.Errorf("content upload returned %d %v", w.Code, result["code"])
	}
	return result, nil
}

func api(h http.Handler, token, method, path string, body any, match string) (domain.Object, error) {
	var payload []byte
	if body != nil {
		payload = domain.Bytes(body)
	}
	request := httptest.NewRequest(method, path, bytes.NewReader(payload))
	request.Header.Set("Authorization", "Bearer "+token)
	if method != "GET" {
		request.Header.Set("Idempotency-Key", domain.ID())
	}
	if match != "" {
		request.Header.Set("If-Match", match)
	}
	w := httptest.NewRecorder()
	h.ServeHTTP(w, request)
	var result domain.Object
	if e := json.Unmarshal(w.Body.Bytes(), &result); e != nil {
		return nil, e
	}
	if w.Code < 200 || w.Code >= 300 {
		return nil, fmt.Errorf("%s %s returned %d %v", method, path, w.Code, result["code"])
	}
	return result, nil
}

func mustArtifact(db *sql.DB, project string, evidence domain.Object) domain.Object {
	ref := evidence["snapshot_artifact_ref"].(map[string]any)
	var raw string
	if e := db.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='Artifact' AND id=?", project, ref["id"]).Scan(&raw); e != nil {
		panic(e)
	}
	obj, e := domain.Decode([]byte(raw))
	if e != nil {
		panic(e)
	}
	return obj
}

func verifyArtifact(h http.Handler, token, project string, artifact domain.Object, want []byte) error {
	path := "/v1/projects/" + project + "/artifacts/" + domain.Str(artifact, "id") + "/content"
	request := httptest.NewRequest("GET", path, nil)
	request.Header.Set("Authorization", "Bearer "+token)
	w := httptest.NewRecorder()
	h.ServeHTTP(w, request)
	if w.Code != 200 || !bytes.Equal(w.Body.Bytes(), want) || artifact["content_hash"] != domain.Digest(want) {
		return fmt.Errorf("sealed artifact content mismatch: %s status %d", path, w.Code)
	}
	return nil
}

func sealXUncorroborated(s *domain.Service, db *sql.DB, token, project string, evidence domain.Object, body []byte, reason string) (map[string]any, error) {
	if evidence["source_kind"] != "X" || evidence["stance"] != "CONTEXT" || evidence["verification_status"] != "UNVERIFIED" {
		return nil, fmt.Errorf("unverified X evidence required")
	}
	if err := verifyArtifact(s.Handler(), token, project, mustArtifact(db, project, evidence), body); err != nil {
		return nil, err
	}
	doc := domain.Object{"schema": "researchos.x-claim-disposition.v1", "conclusion": "NOT_CORROBORATED", "adoption_authority": false, "reason": reason, "x_evidence_ref": domain.Ref(evidence, "Evidence"), "x_snapshot_ref": evidence["snapshot_artifact_ref"], "primary_evidence_ref": nil, "unverified_claims": unverifiedXClaims(body)}
	content := domain.Bytes(doc)
	u, e := uploadBytes(s.Handler(), token, project, content)
	if e != nil {
		return nil, e
	}
	state, e := api(s.Handler(), token, "GET", "/v1/projects/"+project+"/state", nil, "")
	if e != nil {
		return nil, e
	}
	tag, e := domain.ETag(state)
	if e != nil {
		return nil, e
	}
	refs := []any{domain.Ref(evidence, "Evidence")}
	a, e := api(s.Handler(), token, "POST", "/v1/projects/"+project+"/artifacts", domain.Object{"run_id": nil, "kind": "MANIFEST", "evidence_kind": "GENERATED", "measurement_mode": "LIVE", "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "application/json", "byte_size": len(content), "input_refs": refs, "source_refs": refs, "produced_by": "w07-live-adapter", "access_class": "PROJECT"}, tag)
	if e != nil {
		return nil, e
	}
	if e = verifyArtifact(s.Handler(), token, project, a, content); e != nil {
		return nil, e
	}
	doc["artifact_ref"] = domain.Ref(a, "Artifact")
	return doc, nil
}
