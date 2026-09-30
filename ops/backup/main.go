// backup is a local administrative command; it starts no server or worker.
package main

import (
	"context"
	"crypto/rand"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"researchos.local/research-os/internal/domain"
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
func run() error {
	if len(os.Args) < 2 {
		return fmt.Errorf("usage: backup keygen|create|export|restore [flags]")
	}
	command := os.Args[1]
	f := flag.NewFlagSet(command, flag.ContinueOnError)
	source := f.String("db", "", "existing source SQLite database")
	backup := f.String("backup", "", "existing encrypted backup directory")
	out := f.String("out", "", "new destination (must not exist)")
	keyfile := f.String("key-file", "", "separate recovery key file; never command-line key bytes")
	root := f.String("root", ".", "matching application repository root")
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
	if command != "create" && command != "export" && command != "restore" {
		return fmt.Errorf("unknown command")
	}
	if *out == "" {
		return fmt.Errorf("--out required")
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
		r, e := domain.RestoreBackup(ctx, *backup, *out, domain.RestoreOptions{Key: key, SupportedMigrations: versions, Contracts: contracts})
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
	m, e := s.CreateBackup(ctx, *out, key)
	if e != nil {
		return e
	}
	return json.NewEncoder(os.Stdout).Encode(m)
}
