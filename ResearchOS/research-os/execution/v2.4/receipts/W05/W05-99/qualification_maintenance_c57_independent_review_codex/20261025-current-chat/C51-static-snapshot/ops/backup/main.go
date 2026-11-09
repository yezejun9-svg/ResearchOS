// backup is a local administrative command; it starts no server or worker.
package main

import (
	"context"
	"crypto/rand"
	"database/sql"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"researchos.local/research-os/internal/domain"
	hostboundary "researchos.local/research-os/internal/host"
	"researchos.local/research-os/internal/store"
	"strconv"
	"strings"
)

func main() {
	if e := run(); e != nil {
		fmt.Fprintln(os.Stderr, e)
		os.Exit(1)
	}
}
func run() (runErr error) {
	if len(os.Args) < 2 {
		return fmt.Errorf("usage: backup keygen|create|export|restore|upgrade-local|upgrade-prepared-backup [flags]")
	}
	command := os.Args[1]
	f := flag.NewFlagSet(command, flag.ContinueOnError)
	source := f.String("db", "", "existing source SQLite database")
	backup := f.String("backup", "", "existing encrypted backup directory")
	out := f.String("out", "", "new destination (must not exist)")
	keyfile := f.String("key-file", "", "separate recovery key file; never command-line key bytes")
	root := f.String("root", ".", "matching application repository root")
	asDataRoot := f.Bool("as-data-root", false, "restore an operational data root (researchos.sqlite plus fresh Host bindings)")
	sourceRoot := f.String("source-root", "", "upgrade: exact schema13 release root")
	sourceProgram := f.String("source-program", "", "upgrade: preserved matching old program")
	targetProgram := f.String("target-program", "", "upgrade: reviewed target program")
	plan := f.String("plan", "", "upgrade: schema13-to14-remote-access-v1 or schema13-to20-research-runtime-v1 (exact releases only)")
	handoffBinding := f.String("handoff-binding", "", "upgrade-prepared-backup: externally reviewed and pinned producer binding")
	handoffSHA256 := f.String("handoff-binding-sha256", "", "upgrade-prepared-backup: expected sha256: digest of binding")
	if e := f.Parse(os.Args[2:]); e != nil {
		return e
	}
	if f.NArg() != 0 {
		return fmt.Errorf("unexpected positional arguments")
	}
	if *keyfile == "" {
		return fmt.Errorf("--key-file required")
	}
	if command == "keygen" {
		key := make([]byte, 32)
		if _, e := rand.Read(key); e != nil {
			return e
		}
		f, e := os.OpenFile(*keyfile, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
		if e != nil {
			return e
		}
		defer f.Close()
		if _, e = f.Write(key); e != nil {
			return e
		}
		if e = f.Sync(); e != nil {
			return e
		}
		fmt.Println(`{"status":"KEY_CREATED_SEPARATELY","key_bytes_printed":false}`)
		return nil
	}
	if command != "create" && command != "export" && command != "restore" && command != "upgrade-local" && command != "upgrade-prepared-backup" {
		return fmt.Errorf("unknown command")
	}
	if *out == "" {
		return fmt.Errorf("--out required")
	}
	var sourceOwner *backupSourceOwner
	if command != "restore" {
		if *source == "" {
			return fmt.Errorf("--db required")
		}
		var err error
		sourceOwner, err = openBackupSourceLease(*source)
		if err != nil {
			return err
		}
		defer func() {
			if closeErr := sourceOwner.Close(); runErr == nil && closeErr != nil {
				runErr = closeErr
			}
		}()
	}
	if command == "upgrade-prepared-backup" {
		r, e := sourceOwner.UpgradePrepared(context.Background(), domain.PreparedBackupHandoffOptions{
			Upgrade: domain.LocalUpgradeOptions{
				Source: *source, Snapshot: *backup, Destination: *out, KeyFile: *keyfile,
				SourceRoot: *sourceRoot, TargetRoot: *root, SourceProgram: *sourceProgram,
				TargetProgram: *targetProgram, Plan: *plan,
			},
			BindingFile: *handoffBinding, BindingSHA256: *handoffSHA256,
		})
		if e != nil {
			return e
		}
		return json.NewEncoder(os.Stdout).Encode(r)
	}
	if command == "upgrade-local" {
		r, e := sourceOwner.UpgradeLocal(context.Background(), domain.LocalUpgradeOptions{
			Source: *source, Snapshot: *backup, Destination: *out, KeyFile: *keyfile,
			SourceRoot: *sourceRoot, TargetRoot: *root, SourceProgram: *sourceProgram,
			TargetProgram: *targetProgram, Plan: *plan,
		})
		if e != nil {
			return e
		}
		return json.NewEncoder(os.Stdout).Encode(r)
	}
	keyPath, e := filepath.Abs(*keyfile)
	if e != nil {
		return e
	}
	for _, dir := range []string{*out, *backup} {
		if dir == "" {
			continue
		}
		abs, e := filepath.Abs(dir)
		if e != nil {
			return e
		}
		rel, e := filepath.Rel(abs, keyPath)
		if e == nil && filepath.IsLocal(rel) {
			return fmt.Errorf("KEY_MUST_BE_OUTSIDE_BACKUP_AND_RESTORE")
		}
	}
	key, e := os.ReadFile(*keyfile)
	if e != nil || len(key) != 32 {
		return fmt.Errorf("BACKUP_KEY_UNAVAILABLE")
	}
	defer clear(key)
	contracts, e := domain.LoadContracts(filepath.Join(*root, "spec/v2.0/contracts"))
	if e != nil {
		return e
	}
	ctx := context.Background()
	hostConfig := func(db *sql.DB, dataRoot string) hostboundary.Config {
		return hostboundary.Config{DB: db, Dir: filepath.Join(dataRoot, "host"),
			ContractsDir:  filepath.Join(*root, "spec", "v2.0", "contracts"),
			MigrationFile: filepath.Join(*root, "migrations", "sqlite", "0002_domain.sql"),
			SchemaDir:     filepath.Join(*root, "internal", "api", "contracts")}
	}
	if command == "restore" {
		if *backup == "" {
			return fmt.Errorf("--backup required")
		}
		files, e := filepath.Glob(filepath.Join(*root, "migrations/sqlite/[0-9][0-9][0-9][0-9]_*.sql"))
		if e != nil {
			return e
		}
		versions := []int{}
		for _, file := range files {
			v, e := strconv.Atoi(filepath.Base(file)[:4])
			if e != nil {
				return e
			}
			versions = append(versions, v)
		}
		target := func(ctx context.Context, destination string, requests []domain.WorkspaceRestoreRequest) ([]domain.WorkspaceRestorePin, error) {
			restored, err := store.Open(filepath.Join(destination, "researchos.sqlite"))
			if err != nil {
				return nil, err
			}
			defer restored.Close()
			h, err := hostboundary.New(hostConfig(restored, destination))
			if err != nil {
				return nil, err
			}
			if _, err := h.BootstrapOwner(ctx); err != nil {
				return nil, err
			}
			pins := make([]domain.WorkspaceRestorePin, 0, len(requests))
			for _, request := range requests {
				pin, err := h.PinRestoredWorkspace(ctx, request)
				if err != nil {
					return nil, err
				}
				pins = append(pins, pin)
			}
			return pins, nil
		}
		options := domain.RestoreOptions{Key: key, SupportedMigrations: versions, Contracts: contracts}
		if *asDataRoot {
			options.WorkspaceTarget = target
			options.DatabaseName = "researchos.sqlite"
		}
		r, e := domain.RestoreBackup(ctx, *backup, *out, options)
		if e != nil {
			return e
		}
		return json.NewEncoder(os.Stdout).Encode(r)
	}
	if *source == "" {
		return fmt.Errorf("--db required")
	}
	st, e := os.Stat(*source)
	if e != nil || !st.Mode().IsRegular() {
		return fmt.Errorf("existing regular source database required")
	}
	// Refuse ambiguous URI DSNs; --db is an ordinary local file path.
	if strings.Contains(*source, "?") {
		return fmt.Errorf("SQLite URI parameters prohibited")
	}
	db, e := store.Open(*source)
	if e != nil {
		return e
	}
	defer db.Close()
	s := &domain.Service{DB: db, Contracts: contracts}
	var active int
	if e := db.QueryRow(`SELECT count(*) FROM domain_objects WHERE project='' AND kind=? AND json_extract(body,'$.status')=?`,
		domain.KindWorkspaceBinding, domain.WorkspaceActive).Scan(&active); e != nil {
		return e
	}
	var m domain.BackupManifest
	if active == 0 {
		m, e = s.CreateBackup(ctx, *out, key)
	} else {
		h, hostErr := hostboundary.New(hostConfig(db, filepath.Dir(*source)))
		if hostErr != nil {
			return hostErr
		}
		m, e = s.CreateBackupWithWorkspaces(ctx, *out, key, h)
	}
	if e != nil {
		return e
	}
	return json.NewEncoder(os.Stdout).Encode(m)
}
