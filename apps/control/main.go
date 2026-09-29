package main

import (
	"context"
	"encoding/json"
	"errors"
	"flag"
	"log"
	"net"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"time"

	"researchos.local/research-os/internal/api"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/store"
)

func setting(name, fallback string) string {
	if value := os.Getenv(name); value != "" {
		return value
	}
	return fallback
}

func main() {
	bootstrapOwner := flag.Bool("bootstrap-owner", false, "initialize the local Owner and write a private credential file")
	credentialFile := flag.String("credential-file", "", "private local output path")
	flag.Parse()
	dataDir := setting("RESEARCHOS_DATA_DIR", filepath.Join(".local", "data"))
	webDir := setting("RESEARCHOS_WEB_DIR", filepath.Join("apps", "web", "dist"))
	if _, err := os.Stat(filepath.Join(webDir, "index.html")); err != nil && !*bootstrapOwner {
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
	service, err := domain.New(db, filepath.Join("spec", "v2.0", "contracts"), filepath.Join("migrations", "sqlite", "0002_domain.sql"))
	if err != nil {
		log.Fatalf("domain unavailable: %v", err)
	}
	if *bootstrapOwner {
		if *credentialFile == "" {
			log.Fatal("credential-file required")
		}
		if err = bootstrap(service, *credentialFile); err != nil {
			log.Fatalf("Owner bootstrap failed: %v", err)
		}
		return
	}
	listen := setting("RESEARCHOS_LISTEN", "127.0.0.1:8787")
	host, _, err := net.SplitHostPort(listen)
	if err != nil || net.ParseIP(host) == nil || !net.ParseIP(host).IsLoopback() {
		log.Fatal("remote listen requires W17 qualified TLS and pairing")
	}
	server := &http.Server{
		Addr:              listen,
		Handler:           api.Handler(db, webDir, service),
		ReadHeaderTimeout: 5 * time.Second,
		ReadTimeout:       15 * time.Second,
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

func bootstrap(s *domain.Service, path string) error {
	// The explicit local command runs under the current OS identity; there is no HTTP bootstrap route.
	if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
		return err
	}
	tx, err := s.DB.BeginTx(context.Background(), nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	var count int
	if err = tx.QueryRow("SELECT count(*) FROM auth_principals").Scan(&count); err != nil {
		return err
	}
	if count != 0 {
		return errors.New("Owner already initialized; use local credential administration")
	}
	f, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if err != nil {
		return err
	}
	committed := false
	defer func() {
		f.Close()
		if !committed {
			os.Remove(path)
		}
	}()
	if err = privateFile(path); err != nil {
		return err
	}
	id := "owner-" + domain.ID()
	token := domain.ID() + domain.ID()
	if _, err = tx.Exec("INSERT INTO auth_principals(id,roles,can_create_project) VALUES(?,?,1)", id, `["OWNER"]`); err != nil {
		return err
	}
	if _, err = tx.Exec("INSERT INTO auth_credentials(token_hash,principal,expires_at) VALUES(?,?,?)", domain.Digest([]byte(token)), id, time.Now().UTC().Add(15*time.Minute).Format(time.RFC3339Nano)); err != nil {
		return err
	}
	if err = json.NewEncoder(f).Encode(map[string]any{"token": token, "principal_id": id, "expires_in_seconds": 900}); err != nil {
		return err
	}
	if err = f.Sync(); err != nil {
		return err
	}
	if err = tx.Commit(); err != nil {
		return err
	}
	committed = true
	return nil
}
