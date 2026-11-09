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

	"researchos.local/research-os/adapters/protectedstore"
	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/internal/api"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/store"
	"researchos.local/research-os/ops/supervisor"
)

func setting(name, fallback string) string {
	if value := os.Getenv(name); value != "" {
		return value
	}
	return fallback
}

func main() {
	if handled, err := runFixtureControlReplay(os.Args[1:]); handled {
		if err != nil {
			log.Fatal(err)
		}
		return
	}
	bootstrapOwner := flag.Bool("bootstrap-owner", false, "initialize the local Owner and write a private credential file")
	credentialFile := flag.String("credential-file", "", "private local output path")
	importSpec := flag.String("import-spec", "", "import a pinned specification directory as the initial ResearchOS goal")
	manifestHash := flag.String("manifest-sha256", "", "trusted sha256 digest of the complete package manifest")
	importJev := flag.String("import-jev", "", "register the completed frozen evaluation in this project; independent acceptance remains required")
	developmentFile := flag.String("development-file", "evaluation/development/jev-v2/dataset.json", "hash-pinned public development corpus")
	provision := flag.String("provision-principal", "", "trusted local administration: principal JSON to provision")
	issue := flag.String("issue-credential", "", "trusted local administration: existing principal ID")
	coordinatorFile := flag.String("runtime-coordinator-config", "", "private host configuration for the single runtime coordinator")
	flag.Parse()
	adminActions := 0
	for _, active := range []bool{*bootstrapOwner, *importSpec != "", *importJev != "", *provision != "", *issue != ""} {
		if active {
			adminActions++
		}
	}
	if adminActions > 1 {
		log.Fatal("choose one local administrative action")
	}
	dataDir := setting("RESEARCHOS_DATA_DIR", filepath.Join(".local", "data"))
	webDir := setting("RESEARCHOS_WEB_DIR", filepath.Join("apps", "web", "dist"))
	if _, err := os.Stat(filepath.Join(webDir, "index.html")); err != nil && adminActions == 0 {
		log.Fatalf("web build unavailable: %v", err)
	}
	lease, err := rt.AcquireDataRootLease(dataDir)
	if err != nil {
		log.Fatalf("control data-root lease unavailable: %v", err)
	}
	defer func() {
		if err := lease.Close(); err != nil {
			log.Fatalf("data-root lease close failed: %v", err)
		}
	}()
	dataDir = lease.Root()
	db, err := store.Open(filepath.Join(dataDir, "researchos.sqlite"))
	if err != nil {
		log.Fatalf("database unavailable: %v", err)
	}
	defer func() {
		if err := db.Close(); err != nil {
			log.Fatalf("database close failed: %v", err)
		}
	}()
	if err := store.Bootstrap(context.Background(), db, filepath.Join("migrations", "sqlite", "0001_bootstrap.sql")); err != nil {
		log.Fatalf("database bootstrap failed: %v", err)
	}
	service, err := domain.New(db, filepath.Join("spec", "v2.0", "contracts"), filepath.Join("migrations", "sqlite", "0002_domain.sql"))
	if err != nil {
		log.Fatalf("domain unavailable: %v", err)
	}
	service.Protected = &protectedstore.FrozenProvider{}
	boot, err := supervisor.ReadInheritedDrainBootstrap(dataDir)
	if err != nil {
		log.Fatalf("private drain capability unavailable: %v", err)
	}
	if boot != nil && boot.FixtureStore != "" {
		fixture, e := protectedstore.OpenCanary(boot.FixtureStore)
		if e != nil {
			log.Fatalf("private fixture store unavailable: %v", e)
		}
		defer fixture.Close()
		service.Protected = fixture
	}
	if *provision != "" || *issue != "" {
		if e := adminCredential(service, *provision, *issue, *credentialFile); e != nil {
			log.Fatalf("local credential administration failed: %v", e)
		}
		return
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
	if *importJev != "" {
		raw, e := os.ReadFile(*credentialFile)
		if e != nil {
			log.Fatal("private credential file required")
		}
		credential, e := domain.Decode(raw)
		if e != nil {
			log.Fatal("invalid credential file")
		}
		development, e := os.ReadFile(*developmentFile)
		if e != nil {
			log.Fatal("public development corpus unavailable")
		}
		result, e := service.ImportFrozenQualifications(context.Background(), domain.Str(credential, "token"), *importJev, development)
		if e != nil {
			log.Fatalf("evaluation registration failed: %v", e)
		}
		json.NewEncoder(os.Stdout).Encode(result)
		return
	}
	if *importSpec != "" {
		if *credentialFile == "" || *manifestHash == "" {
			log.Fatal("credential-file and manifest-sha256 required")
		}
		raw, e := os.ReadFile(*credentialFile)
		if e != nil {
			log.Fatal("private credential file unavailable")
		}
		credential, e := domain.Decode(raw)
		if e != nil {
			log.Fatal("invalid credential file")
		}
		result, e := service.ImportSpecification(context.Background(), domain.Str(credential, "token"), *importSpec, *manifestHash, domain.Object{})
		if e != nil {
			log.Fatalf("specification import failed: %v", e)
		}
		json.NewEncoder(os.Stdout).Encode(result)
		return
	}
	listen := setting("RESEARCHOS_LISTEN", "127.0.0.1:8787")
	host, _, err := net.SplitHostPort(listen)
	if err != nil || net.ParseIP(host) == nil || !net.ParseIP(host).IsLoopback() {
		log.Fatal("remote listen requires W17 qualified TLS and pairing")
	}
	gate := &drainGate{}
	httpContext, cancelHTTP := context.WithCancel(context.Background())
	defer cancelHTTP()
	server := &http.Server{
		Addr:              listen,
		Handler:           gate.Wrap(api.Handler(db, webDir, service)),
		BaseContext:       func(net.Listener) context.Context { return httpContext },
		ReadHeaderTimeout: 5 * time.Second,
		ReadTimeout:       15 * time.Second,
	}
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt)
	defer stop()
	listener, err := net.Listen("tcp", listen)
	if err != nil {
		log.Fatalf("control listener unavailable: %v", err)
	}
	defer listener.Close()
	server.Addr = listener.Addr().String()
	var coordinator *domain.RuntimeCoordinator
	coordinatorDone := make(chan struct{})
	if *coordinatorFile != "" {
		raw, e := os.ReadFile(*coordinatorFile)
		if e != nil {
			log.Fatal("runtime coordinator configuration unavailable")
		}
		var config domain.RuntimeCoordinatorConfig
		if e = json.Unmarshal(raw, &config); e != nil {
			log.Fatal("runtime coordinator configuration invalid")
		}
		if config.DataRoot == "" {
			config.DataRoot = dataDir
		}
		if config.APIURL == "" {
			config.APIURL = "http://" + server.Addr
		}
		coordinator, e = service.NewRuntimeCoordinatorWithLease(ctx, config, lease)
		if e != nil {
			log.Fatalf("runtime coordinator unavailable: %v", e)
		}
		defer func() {
			if err := coordinator.Close(); err != nil {
				log.Fatalf("coordinator close failed: %v", err)
			}
		}()
		go func() {
			defer close(coordinatorDone)
			if e := coordinator.Serve(ctx, func(e error) { log.Printf("runtime coordinator operation stopped: %v", e) }); e != nil {
				log.Printf("runtime coordinator stopped: %v", e)
				stop()
			}
		}()
	} else {
		close(coordinatorDone)
	}
	drainDone := make(chan struct{})
	if boot != nil {
		d := &controlDrain{gate: gate, service: service, coordinator: coordinator, lease: lease, listener: listener, startup: boot, pipe: boot.Pipe, root: dataDir, key: boot.Key, peer: boot.Peer, stop: stop}
		go func() {
			defer close(drainDone)
			d.Serve(ctx, func(e error) { log.Printf("private drain stopped: %v", e) })
		}()
	} else {
		close(drainDone)
	}
	shutdownDone := make(chan struct{})
	go func() {
		defer close(shutdownDone)
		<-ctx.Done()
		cancelHTTP() // Cancel SSE/read requests separately from the admission gate.
		shutdown, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if err := server.Shutdown(shutdown); err != nil {
			_ = server.Close()
		}
	}()
	log.Printf("development server listening on %s", server.Addr)
	if err := server.Serve(listener); err != nil && !errors.Is(err, http.ErrServerClosed) {
		log.Printf("control HTTP stopped: %v", err)
	}
	stop()
	<-shutdownDone
	gate.Close()
	<-coordinatorDone
	<-drainDone
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
