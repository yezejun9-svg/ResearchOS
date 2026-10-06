package api

import (
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"researchos.local/research-os/internal/domain"
)

func TestBrowserRouteFallback(t *testing.T) {
	dir := t.TempDir()
	if err := os.WriteFile(filepath.Join(dir, "index.html"), []byte("<main>ResearchOS</main>"), 0600); err != nil {
		t.Fatal(err)
	}
	handler := Handler(nil, dir, &domain.Service{Contracts: &domain.Contracts{}})
	for _, tc := range []struct {
		path   string
		status int
		html   bool
	}{
		{"/projects/project-1/research", 200, true},
		{"/assets/missing.js", 404, false},
		{"/v1/unknown", 404, false},
	} {
		r := httptest.NewRequest("GET", tc.path, nil)
		r.Header.Set("Accept", "text/html")
		w := httptest.NewRecorder()
		handler.ServeHTTP(w, r)
		if w.Code != tc.status || strings.Contains(w.Body.String(), "<main>") != tc.html {
			t.Fatalf("%s: status %d, body %s", tc.path, w.Code, w.Body.String())
		}
	}
}
