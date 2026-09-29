package main

import (
	"context"
	"errors"
	"log"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"time"

	"researchos.local/research-os/internal/api"
	"researchos.local/research-os/internal/store"
)

func setting(name, fallback string) string {
	if value := os.Getenv(name); value != "" {
		return value
	}
	return fallback
}

func main() {
	dataDir := setting("RESEARCHOS_DATA_DIR", filepath.Join(".local", "data"))
	webDir := setting("RESEARCHOS_WEB_DIR", filepath.Join("apps", "web", "dist"))
	if _, err := os.Stat(filepath.Join(webDir, "index.html")); err != nil {
		log.Fatalf("web build unavailable: %v", err)
	}
	db, err := store.Open(filepath.Join(dataDir, "researchos.sqlite"))
	if err != nil {
		log.Fatalf("database unavailable: %v", err)
	}
	defer db.Close()
	if err := store.Bootstrap(context.Background(), db, filepath.Join("migrations", "sqlite", "0001_bootstrap.sql")); err != nil {
		log.Fatalf("database bootstrap failed: %v", err)
	}
	server := &http.Server{
		Addr:              setting("RESEARCHOS_LISTEN", "127.0.0.1:8787"),
		Handler:           api.Handler(db, webDir),
		ReadHeaderTimeout: 5 * time.Second,
	}
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt)
	defer stop()
	go func() {
		<-ctx.Done()
		shutdown, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		server.Shutdown(shutdown)
	}()
	log.Printf("development server listening on %s", server.Addr)
	if err := server.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
		log.Fatal(err)
	}
}
