//go:build windows

// release_host is a same-user disposable R2 fixture process. It has no LIVE
// authority and never installs or controls a Windows service.
package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"researchos.local/research-os/adapters/protectedstore"
	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/store"
)

func run() error {
	dbPath := flag.String("db", "", "fixture authority SQLite path")
	contracts := flag.String("contracts", "", "contracts directory")
	migration := flag.String("migration", "", "migration path")
	private := flag.String("private", "", "existing CanaryStore root")
	project := flag.String("project", "", "project")
	operation := flag.String("operation", "", "operation")
	control := flag.String("control", "", "exact actual-control fixture executable")
	root := flag.String("root", "", "existing fixture host root")
	work := flag.String("work-dir", "", "control working directory")
	web := flag.String("web-dir", "", "fixture web build directory")
	listen := flag.String("listen", "", "control loopback listener")
	flag.Parse()
	if *control != "" {
		return runControlHost(*control, *root, *work, *web, *listen, *private, *contracts)
	}
	if *dbPath == "" || *contracts == "" || *migration == "" || *private == "" || *project == "" || *operation == "" {
		return fmt.Errorf("R2_FIXTURE_ARGUMENTS_REQUIRED")
	}
	protected, err := protectedstore.OpenCanary(*private)
	if err != nil {
		return err
	}
	defer protected.Close()
	lease, err := rt.AcquireDataRootLease(filepath.Dir(*dbPath))
	if err != nil {
		return fmt.Errorf("offline legacy fixture authority required: %w", err)
	}
	defer lease.Close()
	db, err := store.Open(*dbPath)
	if err != nil {
		return err
	}
	defer db.Close()
	svc, err := domain.New(db, *contracts, *migration)
	if err != nil {
		return err
	}
	svc.Protected = protected
	result, err := svc.RunEvolutionReleaseFixtureOnce(context.Background(), *project, *operation)
	if err != nil {
		return err
	}
	return json.NewEncoder(os.Stdout).Encode(result)
}

func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
