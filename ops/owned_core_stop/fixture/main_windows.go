//go:build windows

// The fixture is a separate executable and is never linked into the stop CLI.
package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"time"

	"golang.org/x/sys/windows"
	_ "modernc.org/sqlite"
	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/internal/auth"
	"researchos.local/research-os/internal/host"
	"researchos.local/research-os/internal/store"
	"researchos.local/research-os/ops/supervisor"
)

type nativeFile struct {
	Path   string `json:"path"`
	Volume uint32 `json:"volume"`
	Index  uint64 `json:"index"`
}

func fileID(path string, dir bool) (nativeFile, error) {
	w, e := windows.UTF16PtrFromString(path)
	if e != nil {
		return nativeFile{}, e
	}
	h, e := windows.CreateFile(w, windows.FILE_READ_ATTRIBUTES, windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE|windows.FILE_SHARE_DELETE, nil, windows.OPEN_EXISTING, windows.FILE_FLAG_OPEN_REPARSE_POINT|windows.FILE_FLAG_BACKUP_SEMANTICS, 0)
	if e != nil {
		return nativeFile{}, e
	}
	defer windows.CloseHandle(h)
	var i windows.ByHandleFileInformation
	if e = windows.GetFileInformationByHandle(h, &i); e != nil {
		return nativeFile{}, e
	}
	if i.FileAttributes&windows.FILE_ATTRIBUTE_REPARSE_POINT != 0 || (i.FileAttributes&windows.FILE_ATTRIBUTE_DIRECTORY != 0) != dir {
		return nativeFile{}, fmt.Errorf("reparse or type mismatch: %s", path)
	}
	return nativeFile{path, i.VolumeSerialNumber, uint64(i.FileIndexHigh)<<32 | uint64(i.FileIndexLow)}, nil
}
func private(path string, dir bool) error {
	token := windows.GetCurrentProcessToken()
	u, e := token.GetTokenUser()
	if e != nil {
		return e
	}
	sid := u.User.Sid.String()
	ace := "(A;;FA;;;" + sid + ")"
	if dir {
		ace = "(A;OICI;FA;;;" + sid + ")"
	}
	sd, e := windows.SecurityDescriptorFromString("O:" + sid + "D:P" + ace)
	if e != nil {
		return e
	}
	acl, _, e := sd.DACL()
	if e != nil {
		return e
	}
	return windows.SetNamedSecurityInfo(path, windows.SE_FILE_OBJECT, windows.DACL_SECURITY_INFORMATION|windows.PROTECTED_DACL_SECURITY_INFORMATION, nil, nil, acl, nil)
}
func setup(root, out string) error {
	if root == "" || out == "" || filepath.IsAbs(root) == false || filepath.IsAbs(out) == false {
		return fmt.Errorf("new absolute fixture root/opdir required")
	}
	for _, path := range []string{root, filepath.Join(root, "host"), out} {
		if e := os.Mkdir(path, 0700); e != nil {
			return e
		}
	}
	if e := private(filepath.Join(root, "host"), true); e != nil {
		return e
	}
	if e := private(out, true); e != nil {
		return e
	}
	a, e := auth.Current()
	if e != nil {
		return e
	}
	state := map[string]any{"version": 1, "principal_ref": a.Ref, "principal_id": "owner-fixture", "host_instance_id": "host-fixture", "bootstrap_at": "", "created_owner": false, "bootstrap_iterations": 0, "active_credential_hash": ""}
	raw, e := json.Marshal(state)
	if e != nil {
		return e
	}
	statePath := filepath.Join(root, "host", "host_state.json")
	if e = os.WriteFile(statePath, raw, 0600); e != nil {
		return e
	}
	if e = private(statePath, false); e != nil {
		return e
	}
	db, e := sql.Open("sqlite", filepath.Join(root, "researchos.sqlite"))
	if e != nil {
		return e
	}
	defer db.Close()
	if _, e = db.Exec(`PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL`); e != nil {
		return e
	}
	files, e := filepath.Glob(filepath.Join("migrations", "sqlite", "[0-9][0-9][0-9][0-9]_*.sql"))
	if e != nil || len(files) != 24 {
		return fmt.Errorf("schema24 migration inventory: %d %v", len(files), e)
	}
	sort.Strings(files)
	for i, file := range files {
		raw, e := os.ReadFile(file)
		if e != nil {
			return e
		}
		if _, e = db.Exec(string(raw)); e != nil {
			return fmt.Errorf("migration %s: %w", file, e)
		}
		if _, e = db.Exec(`INSERT INTO schema_migrations(version) VALUES(?)`, i+1); e != nil {
			return e
		}
	}
	for _, stmt := range []string{
		`INSERT INTO auth_principals(id,roles,revoked) VALUES('owner-fixture','["OWNER"]',0)`,
		`INSERT INTO orchestration_identity(principal,root) VALUES('owner-fixture','root-fixture')`,
		`INSERT INTO domain_objects(project,kind,id,revision,body) VALUES('fixture-project','Run','f3dcb996b2e43cf52cba874be7abfc70',1,'{"status":"RUNNING"}')`,
		`INSERT INTO runtime_dispatches(project,run,epoch,dispatch_key,manifest,manifest_hash,state,prepared_at,updated_at) VALUES('fixture-project','f3dcb996b2e43cf52cba874be7abfc70',1,'705b11ec99044fef19e85f57e2d2b712','{}','fixture-hash','UNKNOWN','fixture-time','fixture-time')`,
		`INSERT INTO resource_effects(project,run,effect_key,sequence,body) VALUES('fixture-project','f3dcb996b2e43cf52cba874be7abfc70','old-model',1,'{"state":"CONFIRMED","payload":{"capability":"MODEL"}}')`,
		`INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at) VALUES('fixture-principal','fixture-project','host:managed-runtime-qualification','bc269e772ada7e1bce54439fd080550c','fixture-hash',202,x'00','{}','fixture-time')`,
		`CREATE TABLE stop_fixture_rows(id TEXT PRIMARY KEY,payload BLOB)`,
	} {
		if _, e = db.Exec(stmt); e != nil {
			return fmt.Errorf("fixture statement: %w", e)
		}
	}
	return nil
}
func describe(root, out string, pid uint32) error {
	n, e := supervisor.ObserveOwnedCoreReadOnly(pid)
	if e != nil {
		return e
	}
	h, e := host.ReadOwnedCoreStopPublicIdentity(context.Background(), root)
	if e != nil {
		return e
	}
	c, e := store.ReadOwnedStopCensus(context.Background(), h.Database)
	if e != nil {
		return e
	}
	r, e := fileID(root, true)
	if e != nil {
		return e
	}
	d, e := fileID(h.Database, false)
	if e != nil {
		return e
	}
	o, e := fileID(out, true)
	if e != nil {
		return e
	}
	return json.NewEncoder(os.Stdout).Encode(struct {
		Native       supervisor.OwnedCoreNativeIdentity `json:"native"`
		Host         host.OwnedCoreStopPublicIdentity   `json:"host"`
		Census       store.OwnedStopCensus              `json:"census"`
		DataRoot     nativeFile                         `json:"data_root"`
		Database     nativeFile                         `json:"database"`
		OperationDir nativeFile                         `json:"operation_dir"`
	}{n, h, c, r, d, o})
}

func main() {
	mode := flag.String("mode", "run", "setup|describe|run")
	root := flag.String("root", "", "new owned fixture data root")
	out := flag.String("out", "", "pre-created private operation directory")
	pid := flag.Uint("pid", 0, "new owned Core fixture PID")
	ready := flag.String("ready", "", "ready marker outside product")
	attempt := flag.String("attempt", "", "attempt trigger")
	attempted := flag.String("attempted", "", "attempted marker")
	flag.Parse()
	if *mode == "setup" {
		if e := setup(*root, *out); e != nil {
			fmt.Fprintln(os.Stderr, e)
			os.Exit(2)
		}
		return
	}
	if *mode == "describe" {
		if e := describe(*root, *out, uint32(*pid)); e != nil {
			fmt.Fprintln(os.Stderr, e)
			os.Exit(2)
		}
		return
	}
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
	if _, err = db.Exec(`PRAGMA busy_timeout=10000`); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
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
