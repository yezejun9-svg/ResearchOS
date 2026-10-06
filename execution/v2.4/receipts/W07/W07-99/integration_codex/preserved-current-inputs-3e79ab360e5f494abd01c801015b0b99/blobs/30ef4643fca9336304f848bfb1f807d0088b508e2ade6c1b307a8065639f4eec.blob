package main

import (
	"context"
	"path/filepath"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/store"
	"testing"
	"time"
)

func TestW07XUncorroboratedDispositionSealed(t *testing.T) {
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

	body := []byte("Uncorroborated public context; growth claims require primary evidence")
	first := offlineEvidence(t, db, s.Handler(), token, projectID, xSource, "https://x.com/public/status/122", "X", "public", "122", "post.text", []byte("unrelated post"))
	second := offlineEvidence(t, db, s.Handler(), token, projectID, xSource, "https://x.com/public/status/123", "X", "public", "123", "post.text", body)
	result, err := sealXUncorroborated(s, db, token, projectID, second, body, "Primary source not available")
	if err != nil {
		t.Fatal(err)
	}
	if result["conclusion"] != "NOT_CORROBORATED" || result["adoption_authority"] != false || domain.Hash(result["x_evidence_ref"]) != domain.Hash(domain.Ref(second, "Evidence")) || domain.Hash(result["x_evidence_ref"]) == domain.Hash(domain.Ref(first, "Evidence")) {
		t.Fatal(result)
	}
	content := getArtifactBytes(t, s.Handler(), token, projectID, domain.Str(result["artifact_ref"].(map[string]any), "id"))
	doc, err := domain.Decode(content)
	if err != nil || doc["primary_evidence_ref"] != nil || doc["adoption_authority"] != false {
		t.Fatal(doc, err)
	}
	if _, err = sealXUncorroborated(s, db, token, projectID, second, []byte("wrong body"), "reason"); err == nil {
		t.Fatal("wrong selected snapshot accepted")
	}
}
