//go:build windows

package main

import (
	"bytes"
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"syscall"
	"testing"

	"golang.org/x/sys/windows"
	_ "modernc.org/sqlite"
	"researchos.local/research-os/internal/auth"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/host"
	"researchos.local/research-os/internal/verifier"
)

func TestRuntimeVerifierReplacementArgumentParser(t *testing.T) {
	good := []string{"--runtime-verifier-replacement", "commit", "--data-root", "D:\\fixture", "--plan", "D:\\plan", "--expect-plan-sha256", "sha256:fixture"}
	if _, e := parseRuntimeVerifierReplacement(good); e != nil {
		t.Fatal(e)
	}
	cases := [][]string{nil, {"--runtime-verifier-replacement"}, {"--runtime-verifier-replacement", "invalid"}, append(append([]string{}, good...), "--force"), append(append([]string{}, good...), "--data-root", "D:\\other"), append(append([]string{}, good...), "positional"), append(append([]string{}, good...), "--desktop-management-stdio"), append(append([]string{}, good...), "--bootstrap-owner"), append(append([]string{}, good...), "--runtime-qualification-request", "request")}
	for i, args := range cases {
		if _, e := parseRuntimeVerifierReplacement(args); e == nil {
			t.Fatalf("case %d accepted", i)
		}
	}
	var out bytes.Buffer
	if handled, _ := runRuntimeVerifierReplacement([]string{"--bootstrap-owner", "--runtime-verifier-replacement"}, &out); handled {
		t.Fatal("dispatcher intercepted non-first marker")
	}
}

func replacementCLIPrivate(t *testing.T, path string, dir bool) {
	t.Helper()
	user, e := windows.GetCurrentProcessToken().GetTokenUser()
	if e != nil {
		t.Fatal(e)
	}
	flags := ""
	if dir {
		flags = "OICI"
	}
	sd, e := windows.SecurityDescriptorFromString("D:P(A;" + flags + ";FA;;;" + user.User.Sid.String() + ")")
	if e != nil {
		t.Fatal(e)
	}
	acl, _, e := sd.DACL()
	if e != nil {
		t.Fatal(e)
	}
	if e = windows.SetNamedSecurityInfo(path, windows.SE_FILE_OBJECT, windows.DACL_SECURITY_INFORMATION|windows.PROTECTED_DACL_SECURITY_INFORMATION, nil, nil, acl, nil); e != nil {
		t.Fatal(e)
	}
}
func replacementCLIWrite(t *testing.T, path string, value any) []byte {
	t.Helper()
	raw, e := json.MarshalIndent(value, "", "  ")
	if e != nil {
		t.Fatal(e)
	}
	if e = os.WriteFile(path, raw, 0600); e != nil {
		t.Fatal(e)
	}
	replacementCLIPrivate(t, path, false)
	return raw
}

func replacementCLIFixture(t *testing.T) (base, root, manifest, plan, oldDigest, manifestDigest string) {
	t.Helper()
	base = t.TempDir()
	root = filepath.Join(base, "data")
	hd := filepath.Join(root, "host")
	for _, dir := range []string{root, hd} {
		if e := os.Mkdir(dir, 0700); e != nil {
			t.Fatal(e)
		}
		replacementCLIPrivate(t, dir, true)
	}
	id, e := auth.Current()
	if e != nil {
		t.Fatal(e)
	}
	hash := sha256.Sum256([]byte(hd + "|" + id.Ref))
	hostID := "host-" + hex.EncodeToString(hash[:6])
	owner := "owner-fixture"
	serviceRoot := "local-verifier-root-" + strings.TrimPrefix(domain.Hash([]any{hostID, verifier.ServiceID}), "sha256:")[:24]
	var installs [2]host.RuntimeVerifierInstallation
	for i := range installs {
		path := filepath.Join(base, fmt.Sprintf("verifier%d.exe", i))
		image := []byte(fmt.Sprintf("MZ-unused-CLI-fixture-%d", i))
		if e = os.WriteFile(path, image, 0600); e != nil {
			t.Fatal(e)
		}
		replacementCLIPrivate(t, path, false)
		installs[i] = host.RuntimeVerifierInstallation{Schema: "researchos.runtime-verifier-installation.v1", ServiceID: verifier.ServiceID, Protocol: verifier.Protocol, Executable: path, ExecutableHash: domain.Digest(image), SourceCommit: strings.Repeat(fmt.Sprint(i+1), 40), Arguments: []string{}}
	}
	manifest = filepath.Join(base, "manifest.json")
	plan = filepath.Join(base, "plan.json")
	manifestDigest = domain.Digest(replacementCLIWrite(t, manifest, installs[1]))
	oldDigest = domain.Digest(replacementCLIWrite(t, filepath.Join(hd, "runtime-verifier-installation.json"), domain.Object{"schema": "researchos.runtime-verifier-registration.v1", "owner_host": hostID, "owner_principal": owner, "service_root": serviceRoot, "installation_hash": domain.Hash(installs[0]), "installation": installs[0]}))
	replacementCLIWrite(t, filepath.Join(hd, "host_state.json"), domain.Object{"version": 1, "principal_ref": id.Ref, "principal_id": owner, "host_instance_id": hostID})
	db, e := sql.Open("sqlite", filepath.Join(root, "researchos.sqlite"))
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	ddl := `CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY);CREATE TABLE auth_principals(id TEXT PRIMARY KEY,roles TEXT,revoked INTEGER,can_create_project INTEGER);CREATE TABLE orchestration_identity(principal TEXT PRIMARY KEY,root TEXT,parent TEXT);CREATE TABLE auth_grants(principal TEXT,project TEXT,task TEXT,run TEXT,restricted INTEGER);CREATE TABLE domain_objects(project TEXT,kind TEXT,id TEXT,body TEXT);CREATE TABLE resource_effects(project TEXT,run TEXT,effect_key TEXT,sequence INTEGER,body TEXT);CREATE TABLE runtime_dispatches(project TEXT,run TEXT,state TEXT);CREATE TABLE idempotency(project TEXT,operation TEXT,body TEXT);`
	if _, e = db.Exec(ddl); e != nil {
		t.Fatal(e)
	}
	for i := 1; i <= 24; i++ {
		if _, e = db.Exec("INSERT INTO schema_migrations VALUES(?)", i); e != nil {
			t.Fatal(e)
		}
	}
	if _, e = db.Exec(`INSERT INTO auth_principals VALUES(?,'["OWNER"]',0,1),(?,'["VERIFIER"]',0,0)`, owner, serviceRoot); e != nil {
		t.Fatal(e)
	}
	if _, e = db.Exec(`INSERT INTO orchestration_identity VALUES(?,?,NULL),(?,?,NULL)`, owner, owner, serviceRoot, serviceRoot); e != nil {
		t.Fatal(e)
	}
	if e = db.Close(); e != nil {
		t.Fatal(e)
	}
	return
}

func TestRuntimeVerifierReplacementActualCLIAndStartup(t *testing.T) {
	binary := filepath.Join(t.TempDir(), "control.exe")
	goexe := filepath.Join(runtime.GOROOT(), "bin", "go.exe")
	build := exec.Command(goexe, "build", "-o", binary, ".")
	build.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	if out, e := build.CombinedOutput(); e != nil {
		t.Fatalf("actual control build: %v %s", e, out)
	}
	run := func(t *testing.T, dir string, extraEnv []string, args ...string) ([]byte, int) {
		t.Helper()
		cmd := exec.Command(binary, args...)
		cmd.Dir = dir
		cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
		cmd.Env = append([]string{}, extraEnv...)
		for _, key := range []string{"SystemRoot", "WINDIR", "TEMP", "TMP"} {
			if value := os.Getenv(key); value != "" {
				cmd.Env = append(cmd.Env, key+"="+value)
			}
		}
		out, e := cmd.CombinedOutput()
		code := 0
		if e != nil {
			ee, ok := e.(*exec.ExitError)
			if !ok {
				t.Fatal(e)
			}
			code = ee.ExitCode()
		}
		t.Logf("actual argv=%q cwd=%q env_allowlist=SystemRoot,WINDIR,TEMP,TMP,RESEARCHOS_DATA_DIR,RESEARCHOS_WEB_DIR exit=%d stdout=%s", cmd.Args, dir, code, out)
		return out, code
	}
	t.Run("preflight-commit-recover-repeat", func(t *testing.T) {
		base, root, manifest, plan, oldHash, manifestHash := replacementCLIFixture(t)
		dbBefore, _ := os.ReadFile(filepath.Join(root, "researchos.sqlite"))
		stateBefore, _ := os.ReadFile(filepath.Join(root, "host", "host_state.json"))
		op := strings.Repeat("d", 32)
		out, code := run(t, base, nil, "--runtime-verifier-replacement", "preflight", "--data-root", root, "--manifest", manifest, "--expect-record-sha256", oldHash, "--expect-manifest-sha256", manifestHash, "--operation-id", op, "--out", plan)
		if code != 0 {
			t.Fatal(string(out))
		}
		var result host.RuntimeVerifierReplacementResult
		if e := json.Unmarshal(out, &result); e != nil || result.State != "PREFLIGHT" {
			t.Fatalf("preflight output: %+v %v", result, e)
		}
		for _, args := range [][]string{{"--runtime-verifier-replacement", "commit", "--data-root", root, "--plan", plan, "--expect-plan-sha256", result.PlanSHA256}, {"--runtime-verifier-replacement", "recover", "--data-root", root, "--plan", plan, "--expect-plan-sha256", result.PlanSHA256, "--operation-id", op, "--action", "inspect"}, {"--runtime-verifier-replacement", "commit", "--data-root", root, "--plan", plan, "--expect-plan-sha256", result.PlanSHA256}} {
			out, code = run(t, base, nil, args...)
			if code != 0 {
				t.Fatal(string(out))
			}
			var got host.RuntimeVerifierReplacementResult
			if e := json.Unmarshal(out, &got); e != nil || got.Outcome != "APPLIED" || got.State != "COMMITTED" {
				t.Fatalf("commit/inspect output: %+v %v", got, e)
			}
		}
		dbAfter, _ := os.ReadFile(filepath.Join(root, "researchos.sqlite"))
		stateAfter, _ := os.ReadFile(filepath.Join(root, "host", "host_state.json"))
		if !bytes.Equal(dbBefore, dbAfter) || !bytes.Equal(stateBefore, stateAfter) {
			t.Fatal("CLI changed DB/state")
		}
		for _, name := range []string{"discovery.json", "researchos.sqlite-wal", "researchos.sqlite-shm", "host/vault", "host/session.json"} {
			if _, e := os.Stat(filepath.Join(root, filepath.FromSlash(name))); !os.IsNotExist(e) {
				t.Fatalf("unexpected ordinary startup side effect %s: %v", name, e)
			}
		}
	})
	t.Run("startup-gate-before-store-open", func(t *testing.T) {
		base, root, manifest, plan, oldHash, manifestHash := replacementCLIFixture(t)
		op := strings.Repeat("e", 32)
		out, code := run(t, base, nil, "--runtime-verifier-replacement", "preflight", "--data-root", root, "--manifest", manifest, "--expect-record-sha256", oldHash, "--expect-manifest-sha256", manifestHash, "--operation-id", op, "--out", plan)
		if code != 0 {
			t.Fatal(string(out))
		}
		journal := filepath.Join(root, "host", "runtime-verifier-replacements")
		operation := filepath.Join(journal, op)
		for _, dir := range []string{journal, operation} {
			if e := os.Mkdir(dir, 0700); e != nil {
				t.Fatal(e)
			}
			replacementCLIPrivate(t, dir, true)
		}
		web := filepath.Join(base, "web")
		if e := os.Mkdir(web, 0700); e != nil {
			t.Fatal(e)
		}
		os.WriteFile(filepath.Join(web, "index.html"), []byte("fixture"), 0600)
		before, _ := os.ReadFile(filepath.Join(root, "researchos.sqlite"))
		out, code = run(t, base, []string{"RESEARCHOS_DATA_DIR=" + root, "RESEARCHOS_WEB_DIR=" + web})
		if code == 0 || !bytes.Contains(out, []byte("runtime verifier replacement recovery required")) {
			t.Fatalf("actual main did not gate: exit=%d %s", code, out)
		}
		after, _ := os.ReadFile(filepath.Join(root, "researchos.sqlite"))
		if !bytes.Equal(before, after) {
			t.Fatal("ordinary startup opened/mutated DB before gate")
		}
	})
	t.Run("strict-CLI-no-startup", func(t *testing.T) {
		base := t.TempDir()
		for _, args := range [][]string{{"--runtime-verifier-replacement"}, {"--runtime-verifier-replacement", "preflight", "--desktop-management-stdio"}, {"--runtime-verifier-replacement", "commit", "--data-root", "D:\\no-root", "--data-root", "D:\\other"}, {"--runtime-verifier-replacement", "recover", "--force"}, {"--runtime-verifier-replacement", "commit", "positional"}} {
			out, code := run(t, base, nil, args...)
			if code == 0 || !bytes.Contains(out, []byte("REPLACEMENT_ARGUMENTS")) || bytes.Contains(out, []byte("web build unavailable")) {
				t.Fatalf("strict early dispatcher: exit=%d %s", code, out)
			}
		}
	})
}
