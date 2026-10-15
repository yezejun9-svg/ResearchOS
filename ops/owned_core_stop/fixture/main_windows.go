//go:build windows

// The fixture is a separate executable and is never linked into the stop CLI.
package main

import (
	"context"
	"database/sql"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"time"

	_ "modernc.org/sqlite"
	rt "researchos.local/research-os/adapters/runtime"
)

func main() {
	root := flag.String("root", "", "new owned fixture data root")
	ready := flag.String("ready", "", "ready marker outside product")
	attempt := flag.String("attempt", "", "attempt trigger")
	attempted := flag.String("attempted", "", "attempted marker")
	flag.Parse()
	if *root == "" || *ready == "" || *attempt == "" || *attempted == "" {
		fmt.Fprintln(os.Stderr, "all fixture paths required")
		os.Exit(2)
	}
	lease, err := rt.AcquireDataRootLease(*root)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	defer lease.Close()
	db, err := sql.Open("sqlite", filepath.Join(*root, "researchos.sqlite"))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	defer db.Close()
	db.SetMaxOpenConns(1)
	if _,err=db.Exec(`PRAGMA busy_timeout=10000`);err!=nil{fmt.Fprintln(os.Stderr,err);os.Exit(2)}
	if _, err = db.Exec(`PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL; INSERT INTO stop_fixture_rows VALUES('committed',x'0001ff')`); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	if err = os.WriteFile(*ready, []byte("READY\n"), 0600); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	for deadline := time.Now().Add(30 * time.Second); time.Now().Before(deadline); time.Sleep(20 * time.Millisecond) {
		if _, err = os.Stat(*attempt); err == nil {
			break
		}
	}
	if _, err = os.Stat(*attempt); err != nil {
		return
	}
	conn, err := db.Conn(context.Background())
	if err != nil {
		return
	}
	defer conn.Close()
	if _, err = conn.ExecContext(context.Background(), "BEGIN DEFERRED"); err != nil {
		return
	}
	if err = os.WriteFile(*attempted, []byte("ATTEMPTED\n"), 0600); err != nil {
		return
	}
	_, _ = conn.ExecContext(context.Background(), `INSERT INTO stop_fixture_rows VALUES('inflight',x'02')`)
	_, _ = conn.ExecContext(context.Background(), "ROLLBACK")
}
