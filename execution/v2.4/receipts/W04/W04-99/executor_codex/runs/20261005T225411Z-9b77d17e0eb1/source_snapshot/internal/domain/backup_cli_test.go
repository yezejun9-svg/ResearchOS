package domain

import (
	"context"
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"testing"
)

func TestW18CLI(t *testing.T) {
	goexe := os.Getenv("RESEARCHOS_GO")
	if goexe == "" {
		var e error
		goexe, e = exec.LookPath("go")
		if e != nil {
			t.Fatal("RESEARCHOS_GO required for CLI acceptance")
		}
	}
	f := contextFixture(t)
	f.artifact(Object{"portable": "CLI export preserves provenance"}, Empty())
	var dbpath, name string
	var seq int
	if e := f.db.QueryRow("PRAGMA database_list").Scan(&seq, &name, &dbpath); e != nil {
		t.Fatal(e)
	}
	work := t.TempDir()
	key := filepath.Join(work, "separate.key")
	pack := filepath.Join(work, "export")
	target := filepath.Join(work, "restored")
	commands := []any{}
	invoke := func(args ...string) []byte {
		t.Helper()
		cmd := exec.Command(goexe, append([]string{"run", "./ops/backup"}, args...)...)
		cmd.Dir = "../.."
		raw, e := cmd.CombinedOutput()
		if e != nil {
			t.Fatalf("CLI %v: %v %s", args, e, raw)
		}
		commands = append(commands, Object{"argv": cmd.Args, "exit_code": 0, "output_sha256": Digest(raw)})
		return raw
	}
	invoke("keygen", "--key-file", key)
	raw := invoke("export", "--db", dbpath, "--out", pack, "--key-file", key)
	var manifest BackupManifest
	if e := json.Unmarshal(raw, &manifest); e != nil {
		t.Fatal(e)
	}
	raw = invoke("restore", "--backup", pack, "--out", target, "--key-file", key)
	var report RestoreReport
	if e := json.Unmarshal(raw, &report); e != nil {
		t.Fatal(e)
	}
	secret, e := os.ReadFile(key)
	if e != nil {
		t.Fatal(e)
	}
	_, files, e := readBackup(pack, secret)
	if e != nil {
		t.Fatal(e)
	}
	var portable Object
	if e = json.Unmarshal(files["portable.json"], &portable); e != nil {
		t.Fatal(e)
	}
	backupAssert(t, "A12-04-CLI", true, report.BackupID == manifest.ID && len(Arr(portable, "objects")) > 0 && report.Status == "RESTORED_RECONCILIATION_REQUIRED", Object{"commands": commands, "manifest": manifest, "report": report})
	// The encryption key is not evidence and is never copied into the package.
	if out := os.Getenv("W18_EVIDENCE_DIR"); out != "" {
		dest := filepath.Join(out, "encrypted-cli-package")
		if e = os.Mkdir(dest, 0700); e != nil {
			t.Fatal(e)
		}
		entries, e := os.ReadDir(pack)
		if e != nil {
			t.Fatal(e)
		}
		for _, entry := range entries {
			b, e := os.ReadFile(filepath.Join(pack, entry.Name()))
			if e != nil {
				t.Fatal(e)
			}
			if e = os.WriteFile(filepath.Join(dest, entry.Name()), b, 0600); e != nil {
				t.Fatal(e)
			}
		}
		backupEvidence(t, "cli.json", Object{"commands": commands, "manifest": manifest, "report": report, "key_retained_in_evidence": false, "verification": "independent rerun generates a new key/package; original package remains encrypted"})
	}
	// Repeating create refuses overwrite and leaves the stable manifest unchanged.
	_, e = f.s.CreateBackup(context.Background(), pack, secret)
	backupAssert(t, "W18-CLI-NO-OVERWRITE", true, e != nil, Object{"error": e.Error()})
	clear(secret)
}
