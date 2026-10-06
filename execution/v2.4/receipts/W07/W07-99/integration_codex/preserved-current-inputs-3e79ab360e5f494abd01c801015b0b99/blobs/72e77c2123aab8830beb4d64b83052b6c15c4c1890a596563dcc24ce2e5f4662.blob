package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/store"
	"strings"
	"testing"
	"time"
)

func TestW07OfflineXPrimaryClaimSealsProductLineage(t *testing.T) {
	ctx := context.Background()
	db, err := store.Open(filepath.Join(t.TempDir(), "claim.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	root := filepath.Join("..", "..", "..")
	if err = store.Bootstrap(ctx, db, filepath.Join(root, "migrations/sqlite/0001_bootstrap.sql")); err != nil {
		t.Fatal(err)
	}
	s, err := domain.New(db, filepath.Join(root, "spec/v2.0/contracts"), filepath.Join(root, "migrations/sqlite/0002_domain.sql"))
	if err != nil {
		t.Fatal(err)
	}
	owner := domain.Principal{ID: "w07-offline-owner", Roles: []string{"OWNER"}, CanCreateProject: true}
	if err = s.ProvisionPrincipal(ctx, owner); err != nil {
		t.Fatal(err)
	}
	ownerToken, err := s.IssueCredential(ctx, owner.ID, time.Minute)
	if err != nil {
		t.Fatal(err)
	}
	xSource, ghSource := domain.ID(), domain.ID()
	projectBody := domain.Object{"name": "W07 offline linked source check", "intent": "validate sealed primary lineage", "facts": domain.Empty(), "accepted_scope": []any{"source fixture"}, "constraints": domain.Empty(), "source_configs": []any{
		domain.Object{"source_id": xSource, "kind": "X", "required": true, "enabled": true, "query": "paperclip agents", "allowed_origins": []any{"https://x.com"}, "credential_ref": nil},
		domain.Object{"source_id": ghSource, "kind": "GITHUB", "required": false, "enabled": true, "query": "readme:paperclipai/paperclip", "allowed_origins": []any{"https://github.com", "https://api.github.com"}, "credential_ref": nil},
	}, "source_document_refs": domain.Empty(), "read_snapshot_ids": domain.Empty()}
	project, err := api(s.Handler(), ownerToken, "POST", "/v1/projects", projectBody, "")
	if err != nil {
		t.Fatal(err)
	}
	projectID := domain.Str(project, "project_id")
	producer := domain.Principal{ID: "w07-live-adapter", Roles: []string{"SOURCE_ADAPTER"}, Grants: []domain.Grant{{ProjectID: projectID}}}
	if err = s.ProvisionPrincipal(ctx, producer); err != nil {
		t.Fatal(err)
	}
	token, err := s.IssueCredential(ctx, producer.ID, time.Minute)
	if err != nil {
		t.Fatal(err)
	}
	xBody := []byte("#2 paperclipai/paperclip\nAgent management is growing.\n+7 stars in one day; 91 total.\n")
	primaryBody := []byte("# Paperclip\nPaperclip is the app people use to manage AI agents for work.\n")
	commit := strings.Repeat("a", 40)
	xURL := "https://x.com/public/status/123"
	primaryURL := "https://github.com/paperclipai/paperclip/blob/" + commit + "/README.md"
	xEvidence := offlineEvidence(t, db, s.Handler(), token, projectID, xSource, xURL, "X", "public", "123", "post.text", xBody)
	primaryEvidence := offlineEvidence(t, db, s.Handler(), token, projectID, ghSource, primaryURL, "GITHUB", "maintainer", commit, "README.md", primaryBody)
	result, err := sealXClaimCheck(s, db, token, projectID, xEvidence, primaryEvidence, xBody, primaryBody, primaryURL, commit)
	if err != nil {
		t.Fatal(err)
	}
	artifactRef := result["artifact_ref"].(map[string]any)
	var raw string
	if err = db.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='Artifact' AND id=?", projectID, artifactRef["id"]).Scan(&raw); err != nil {
		t.Fatal(err)
	}
	var artifact domain.Object
	if err = json.Unmarshal([]byte(raw), &artifact); err != nil {
		t.Fatal(err)
	}
	content := getArtifactBytes(t, s.Handler(), token, projectID, domain.Str(artifact, "id"))
	var claim domain.Object
	if err = json.Unmarshal(content, &claim); err != nil {
		t.Fatal(err)
	}
	if claim["conclusion"] != "SUPPORTED_NARROW_SCOPE" || claim["adoption_authority"] != false || claim["primary_snapshot_ref"].(map[string]any)["content_hash"] != domain.Digest(primaryBody) {
		t.Fatalf("linked claim was not sealed correctly: %+v", claim)
	}
	if len(artifact["source_refs"].([]any)) != 2 || len(artifact["input_refs"].([]any)) != 2 || !strings.Contains(string(content), "+7 stars") || strings.Contains(string(content), "2,251") {
		t.Fatal("lineage or actual X claim missing from sealed manifest")
	}
	if _, err = sealXClaimCheck(s, db, token, projectID, xEvidence, primaryEvidence, xBody, []byte("unrelated README"), primaryURL, commit); err == nil {
		t.Fatal("unrelated primary body supported X claim")
	}
}

func offlineEvidence(t *testing.T, db *sql.DB, h http.Handler, token, project, sourceID, url, kind, publisher, revision, locator string, body []byte) domain.Object {
	t.Helper()
	upload, err := uploadBytes(h, token, project, body)
	if err != nil {
		t.Fatal(err)
	}
	var raw string
	if err = db.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='SourceCursor' AND json_extract(body,'$.source_id')=?", project, sourceID).Scan(&raw); err != nil {
		t.Fatal(err)
	}
	var cursor domain.Object
	if err = json.Unmarshal([]byte(raw), &cursor); err != nil {
		t.Fatal(err)
	}
	state, err := api(h, token, "GET", "/v1/projects/"+project+"/state", nil, "")
	if err != nil {
		t.Fatal(err)
	}
	match, err := domain.ETag(state)
	if err != nil {
		t.Fatal(err)
	}
	artifact, err := api(h, token, "POST", "/v1/projects/"+project+"/artifacts", domain.Object{"run_id": nil, "kind": "SOURCE_SNAPSHOT", "evidence_kind": "OBSERVED", "measurement_mode": "LIVE", "content_hash": upload["content_hash"], "storage_key": upload["storage_key"], "media_type": "text/plain", "byte_size": len(body), "input_refs": []any{domain.Ref(cursor, "SourceCursor")}, "source_refs": domain.Empty(), "produced_by": "w07-live-adapter", "access_class": "PROJECT"}, match)
	if err != nil {
		t.Fatal(err)
	}
	state, err = api(h, token, "GET", "/v1/projects/"+project+"/state", nil, "")
	if err != nil {
		t.Fatal(err)
	}
	match, err = domain.ETag(state)
	if err != nil {
		t.Fatal(err)
	}
	evidence, err := api(h, token, "POST", "/v1/projects/"+project+"/evidence", domain.Object{"claim": "Observed source at " + url, "stance": "CONTEXT", "evidence_kind": "OBSERVED", "source_kind": kind, "canonical_url": url, "publisher": publisher, "upstream_revision": revision, "published_at": time.Date(2026, 9, 29, 12, 0, 0, 0, time.UTC).Format(time.RFC3339Nano), "modified_at": nil, "retrieved_at": domain.Now(), "time_status": "KNOWN", "snapshot_artifact_ref": domain.Ref(artifact, "Artifact"), "locator": locator, "independence_key": domain.Hash(url), "origin_evidence_id": nil, "discovery_urls": domain.Empty(), "license_status": "UNKNOWN", "license_expression": nil}, match)
	if err != nil {
		t.Fatal(err)
	}
	return evidence
}

func getArtifactBytes(t *testing.T, h http.Handler, token, project, id string) []byte {
	t.Helper()
	request := httptest.NewRequest("GET", "/v1/projects/"+project+"/artifacts/"+id+"/content", nil)
	request.Header.Set("Authorization", "Bearer "+token)
	w := httptest.NewRecorder()
	h.ServeHTTP(w, request)
	if w.Code != 200 {
		t.Fatalf("artifact content read status %d", w.Code)
	}
	return w.Body.Bytes()
}
