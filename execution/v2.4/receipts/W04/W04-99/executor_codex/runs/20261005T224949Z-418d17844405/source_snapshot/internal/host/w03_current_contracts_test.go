//go:build windows

package host

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http/httptest"
	"testing"
	"time"

	"researchos.local/research-os/internal/domain"
)

func TestW03NativeHostUsesCurrentMuContracts(t *testing.T) {
	h := firstUseHost(t)
	principal := domain.Principal{ID: "w03-host-fixture", Roles: []string{"OWNER"}, CanCreateProject: true}
	if err := h.domain.ProvisionPrincipal(context.Background(), principal); err != nil {
		t.Fatal(err)
	}
	token, err := h.domain.IssueCredential(context.Background(), principal.ID, time.Minute)
	if err != nil {
		t.Fatal(err)
	}
	body := domain.Object{"name": "native host current constructor", "intent": "fixture only", "facts": []any{}, "accepted_scope": []any{"fixture"}, "constraints": []any{}, "source_configs": []any{}, "source_document_refs": []any{}, "read_snapshot_ids": []any{}}
	r := httptest.NewRequest("POST", "/v1/projects", bytes.NewReader(domain.Bytes(body)))
	r.Header.Set("Authorization", "Bearer "+token)
	r.Header.Set("Idempotency-Key", domain.ID())
	w := httptest.NewRecorder()
	h.domain.Handler().ServeHTTP(w, r)
	if w.Code != 201 {
		t.Fatalf("host-owned domain create: %d %s", w.Code, w.Body.String())
	}
	var project domain.Object
	if err := json.Unmarshal(w.Body.Bytes(), &project); err != nil {
		t.Fatal(err)
	}
	var stored string
	if err := h.db.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='ProjectState'", project["id"]).Scan(&stored); err != nil {
		t.Fatal(err)
	}
	state, err := domain.Decode([]byte(stored))
	if err != nil {
		t.Fatal(err)
	}
	if state["binding"].(map[string]any)["route"] != "MU_FORK" {
		t.Fatal("native host kept legacy producer route")
	}
	if err := h.domain.Contracts.Validate("ProjectState", state); err != nil {
		t.Fatal(err)
	}
}
