package api

import (
	"context"
	"database/sql"
	"encoding/json"
	"log"
	"net/http"
	"path"
	"path/filepath"
	"strings"
	"time"

	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/store"
)

func Handler(db *sql.DB, webDir string, service *domain.Service) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(r.Context(), 3*time.Second)
		defer cancel()
		if err := store.Ready(ctx, db); err != nil {
			w.Header().Set("Content-Type", "application/json; charset=utf-8")
			w.Header().Set("Cache-Control", "no-store")
			w.WriteHeader(http.StatusServiceUnavailable)
			json.NewEncoder(w).Encode(map[string]string{"status": "unavailable", "scope": "DEVELOPMENT_ONLY"})
			return
		}
		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		w.Header().Set("Cache-Control", "no-store")
		json.NewEncoder(w).Encode(map[string]string{"status": "ready", "scope": "DEVELOPMENT_ONLY", "database": "sqlite"})
	})
	mux.Handle("/v1/", service.Handler())
	// The typed v2 boundary is served from this process, so the CLI and the Desktop reach the
	// same command service, the same transaction and the same journal.
	v2 := newV2Service(db)
	mux.HandleFunc("POST /v2/command", v2.serve)
	if v2.loadErr != nil {
		log.Printf("v2 typed service closed: %v", v2.loadErr)
	}
	files := http.FileServer(http.Dir(webDir))
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if (r.Method == "GET" || r.Method == "HEAD") && path.Ext(r.URL.Path) == "" && strings.Contains(r.Header.Get("Accept"), "text/html") {
			w.Header().Set("Cache-Control", "no-store")
			http.ServeFile(w, r, filepath.Join(webDir, "index.html"))
			return
		}
		files.ServeHTTP(w, r)
	})
	return mux
}
