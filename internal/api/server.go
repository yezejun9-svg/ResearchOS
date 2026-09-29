package api

import (
	"context"
	"database/sql"
	"encoding/json"
	"net/http"
	"time"

	"researchos.local/research-os/internal/store"
)

func Handler(db *sql.DB, webDir string) http.Handler {
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
	mux.HandleFunc("/v1/", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		w.WriteHeader(http.StatusNotImplemented)
		json.NewEncoder(w).Encode(map[string]string{"status": "NOT_IMPLEMENTED", "scope": "DEVELOPMENT_ONLY"})
	})
	mux.Handle("/", http.FileServer(http.Dir(webDir)))
	return mux
}
