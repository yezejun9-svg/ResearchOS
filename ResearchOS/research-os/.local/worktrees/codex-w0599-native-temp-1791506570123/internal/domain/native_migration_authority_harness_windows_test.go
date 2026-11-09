//go:build windows && researchos_native_recovery_harness

package domain

// This Root-invoked test harness constructs synthetic local fixture data only.
// It never installs an authority, mints an opaque token or signs any payload.
import (
	"bytes"
	"context"
	"crypto/rand"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"reflect"
	"sort"
	"strings"
	"testing"
	"time"

	"golang.org/x/sys/windows"
	runtimeadapter "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/internal/recoveryauthority"
)

type nativeMigrationHarnessConfig struct {
	Schema               string
	Case                 string
	CaseID               string
	OutputDirectory      string
	BuildRoot            string
	RootSigningPublicKey string
	RootProgram          recoveryauthority.RawPin
	ControlProgram       recoveryauthority.RawPin
	BackupProgram        recoveryauthority.RawPin
	EnrollmentProgram    recoveryauthority.RawPin
	PythonProgram        recoveryauthority.RawPin
	BrokerSource         recoveryauthority.RawPin
	PrivateStdinHelper   recoveryauthority.RawPin
}
type nativeMigrationHarnessApproval struct {
	Action        string
	PayloadSHA256 string
	SignedSHA256  string
}
type nativeMigrationHarnessBrokerRequest struct {
	Schema             string
	Program            recoveryauthority.RawPin
	Arguments          []string
	CWD                string
	Environment        map[string]string
	OutputDirectory    string
	TimeoutSeconds     float64
	PrivateStdinHelper recoveryauthority.RawPin
}
type nativeMigrationHarnessBrokerResult struct {
	Result struct {
		ActualExit *int    `json:"actual_exit"`
		Error      *string `json:"error"`
		TimedOut   bool    `json:"timed_out"`
		Resumed    bool    `json:"resumed"`
		Cleanup    struct {
			Assigned bool     `json:"assigned_before_resume"`
			Idle     bool     `json:"job_idle_confirmed"`
			Exited   bool     `json:"primary_exit_confirmed"`
			Closed   bool     `json:"handles_closed"`
			Active   *int     `json:"active_processes_last_observed"`
			Errors   []string `json:"errors"`
		} `json:"job_cleanup"`
	}
}

func nativeHarnessDecode(raw []byte, target any) error {
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err := d.Decode(target); err != nil {
		return err
	}
	if err := d.Decode(new(any)); err != io.EOF {
		return fmt.Errorf("harness trailing JSON")
	}
	return nil
}
func nativeHarnessWrite(t *testing.T, path string, value any) []byte {
	t.Helper()
	raw, err := json.Marshal(value)
	if err != nil {
		t.Fatal(err)
	}
	f, err := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		t.Fatal(err)
	}
	_, err = f.Write(raw)
	if err == nil {
		err = f.Sync()
	}
	closed := f.Close()
	if err != nil {
		t.Fatal(err)
	}
	if closed != nil {
		t.Fatal(closed)
	}
	return raw
}
func nativeHarnessPin(t *testing.T, role, path string) recoveryauthority.RawPin {
	t.Helper()
	if !filepath.IsAbs(path) {
		t.Fatal("harness requires absolute public path")
	}
	resolved, err := filepath.EvalSymlinks(path)
	if err != nil || !strings.EqualFold(filepath.Clean(path), resolved) {
		t.Fatal("harness public path aliases", err)
	}
	info, err := os.Lstat(path)
	if err != nil || !info.Mode().IsRegular() {
		t.Fatal("harness public input must be regular", err)
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	return recoveryauthority.RawPin{Role: role, Path: path, SHA256: Digest(raw), Bytes: int64(len(raw))}
}
func nativeHarnessRequirePin(t *testing.T, pin recoveryauthority.RawPin) {
	t.Helper()
	if got := nativeHarnessPin(t, pin.Role, pin.Path); got != pin {
		t.Fatal("harness public input pin changed", pin.Role)
	}
}
func nativeHarnessFileID(t *testing.T, path string, directory bool) string {
	t.Helper()
	p, err := windows.UTF16PtrFromString(path)
	if err != nil {
		t.Fatal(err)
	}
	flags := uint32(windows.FILE_FLAG_OPEN_REPARSE_POINT)
	if directory {
		flags |= windows.FILE_FLAG_BACKUP_SEMANTICS
	}
	handle, err := windows.CreateFile(p, windows.FILE_READ_ATTRIBUTES,
		windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE, nil, windows.OPEN_EXISTING, flags, 0)
	if err != nil {
		t.Fatal(err)
	}
	defer windows.CloseHandle(handle)
	var info windows.ByHandleFileInformation
	if err = windows.GetFileInformationByHandle(handle, &info); err != nil {
		t.Fatal(err)
	}
	if (info.FileAttributes&windows.FILE_ATTRIBUTE_DIRECTORY != 0) != directory {
		t.Fatal("harness native file kind")
	}
	return fmt.Sprintf("%08x:%08x:%08x", info.VolumeSerialNumber, info.FileIndexHigh, info.FileIndexLow)
}
func nativeHarnessSID(t *testing.T) string {
	t.Helper()
	var token windows.Token
	if err := windows.OpenProcessToken(windows.CurrentProcess(), windows.TOKEN_QUERY, &token); err != nil {
		t.Fatal(err)
	}
	defer token.Close()
	user, err := token.GetTokenUser()
	if err != nil {
		t.Fatal(err)
	}
	return user.User.Sid.String()
}
func nativeHarnessSourcePins(t *testing.T, root string) []recoveryauthority.RawPin {
	t.Helper()
	directories := []string{"apps/control", "internal", "adapters", "evaluation", "ops", "migrations/sqlite", "spec/v2.0/contracts"}
	if _, err := os.Stat(filepath.Join(root, "vendor")); err == nil {
		directories = append(directories, "vendor")
	} else if !os.IsNotExist(err) {
		t.Fatal(err)
	}
	paths := []string{}
	for _, directory := range directories {
		err := filepath.WalkDir(filepath.Join(root, filepath.FromSlash(directory)), func(path string, entry os.DirEntry, err error) error {
			if err != nil {
				return err
			}
			if entry.Type()&os.ModeSymlink != 0 {
				return fmt.Errorf("harness source symlink")
			}
			if !entry.IsDir() {
				if !entry.Type().IsRegular() {
					return fmt.Errorf("harness nonregular source")
				}
				paths = append(paths, path)
			}
			return nil
		})
		if err != nil {
			t.Fatal(err)
		}
	}
	for _, path := range []string{"go.mod", "go.sum", "execution/toolchains/locked.json"} {
		paths = append(paths, filepath.Join(root, filepath.FromSlash(path)))
	}
	for _, path := range []string{"go.work", "go.work.sum"} {
		full := filepath.Join(root, path)
		if _, err := os.Stat(full); err == nil {
			paths = append(paths, full)
		} else if !os.IsNotExist(err) {
			t.Fatal(err)
		}
	}
	sort.Strings(paths)
	result := make([]recoveryauthority.RawPin, 0, len(paths))
	for _, path := range paths {
		rel, err := filepath.Rel(root, path)
		if err != nil || !filepath.IsLocal(rel) {
			t.Fatal("source pin scope", err)
		}
		result = append(result, nativeHarnessPin(t, "source:"+filepath.ToSlash(rel), path))
	}
	return result
}
func nativeHarnessWait(t *testing.T, ctx context.Context, path, action string) nativeMigrationHarnessApproval {
	t.Helper()
	for {
		info, err := os.Lstat(path)
		if err == nil {
			if !info.Mode().IsRegular() || info.Size() > 8192 {
				t.Fatal("harness public approval file")
			}
			raw, err := os.ReadFile(path)
			if err != nil {
				t.Fatal(err)
			}
			var approval nativeMigrationHarnessApproval
			if err = nativeHarnessDecode(raw, &approval); err != nil {
				t.Fatal(err)
			}
			if approval.Action != action {
				t.Fatal("harness public approval action mismatch")
			}
			return approval
		}
		if !os.IsNotExist(err) {
			t.Fatal(err)
		}
		select {
		case <-ctx.Done():
			t.Fatal("Root review window ended", ctx.Err())
		case <-time.After(200 * time.Millisecond):
		}
	}
}
func nativeHarnessSigned(t *testing.T, path string, expected []byte, approval nativeMigrationHarnessApproval) []byte {
	t.Helper()
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var wrapper struct {
		Payload   json.RawMessage
		Signature string
	}
	if err = nativeHarnessDecode(raw, &wrapper); err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(wrapper.Payload, expected) || Digest(expected) != approval.PayloadSHA256 || Digest(raw) != approval.SignedSHA256 || wrapper.Signature == "" {
		t.Fatal("Root approved exact public signed payload differs")
	}
	// Signature and capability verification remain solely in the actual Root.
	return raw
}

// nativeHarnessExpectedError compares the first nonempty native stderr line.
// Only the actual standard log.Fatal timestamp is stripped. A later expected
// message cannot hide an earlier different error, and a separate Root
// "exit status N" line after the Control error does not change that error.
func nativeHarnessExpectedError(stderr []byte, expected string) bool {
	for _, line := range strings.Split(string(stderr), "\n") {
		line = strings.TrimSuffix(line, "\r")
		if line == "" {
			continue
		}
		if len(line) >= 20 && line[19] == ' ' {
			if _, err := time.Parse("2006/01/02 15:04:05", line[:19]); err == nil {
				line = line[20:]
			}
		}
		return expected != "" && line == expected
	}
	return false
}

func nativeHarnessReadDB(t *testing.T, path string, expectedVersion int) (preparedUpgradeRows, string) {
	t.Helper()
	u := url.URL{Scheme: "file", Opaque: filepath.ToSlash(path)}
	q := u.Query()
	q.Set("mode", "ro")
	u.RawQuery = q.Encode()
	db, err := sql.Open("sqlite", u.String())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	db.SetMaxOpenConns(1)
	if err = preparedUpgradeVersions(db, expectedVersion); err != nil {
		t.Fatal(err)
	}
	rows, err := preparedUpgradeSnapshot(db)
	if err != nil {
		t.Fatal(err)
	}
	schema, err := preparedUpgradeSchema(db)
	if err != nil {
		t.Fatal(err)
	}
	return rows, schema
}
func nativeHarnessBroker(t *testing.T, ctx context.Context, cfg nativeMigrationHarnessConfig, name string,
	program recoveryauthority.RawPin, arguments []string, input string) (nativeMigrationHarnessBrokerResult, []byte, []byte) {
	t.Helper()
	publicEnvironment, err := nativeHarnessBrokerPublicEnvironment(
		os.Getenv("RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT"),
		map[string]string{"SystemRoot": os.Getenv("SystemRoot"), "WINDIR": os.Getenv("WINDIR"), "TEMP": os.Getenv("TEMP"), "TMP": os.Getenv("TMP")})
	if err != nil {
		t.Fatal(err)
	}
	for _, pin := range []recoveryauthority.RawPin{cfg.PythonProgram, cfg.BrokerSource, cfg.PrivateStdinHelper, program} {
		nativeHarnessRequirePin(t, pin)
	}
	output := filepath.Join(cfg.OutputDirectory, name)
	request := nativeMigrationHarnessBrokerRequest{Schema: "researchos.synthetic-native-broker.v1",
		Program: program, Arguments: arguments, CWD: cfg.BuildRoot,
		Environment:     publicEnvironment,
		OutputDirectory: output, TimeoutSeconds: 180, PrivateStdinHelper: cfg.PrivateStdinHelper}
	requestPath := filepath.Join(cfg.OutputDirectory, name+".request.json")
	nativeHarnessWrite(t, requestPath, request)
	out, err := os.OpenFile(filepath.Join(cfg.OutputDirectory, name+".broker.stdout.raw"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		t.Fatal(err)
	}
	defer out.Close()
	stderr, err := os.OpenFile(filepath.Join(cfg.OutputDirectory, name+".broker.stderr.raw"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		t.Fatal(err)
	}
	defer stderr.Close()
	command := exec.CommandContext(ctx, cfg.PythonProgram.Path, "-I", "-S", "-B", "-X", "utf8", cfg.BrokerSource.Path, requestPath)
	command.Dir = cfg.BuildRoot
	command.Env = []string{"SystemRoot=" + publicEnvironment["SystemRoot"], "WINDIR=" + publicEnvironment["WINDIR"], "TEMP=" + publicEnvironment["TEMP"], "TMP=" + publicEnvironment["TMP"]}
	// os/exec creates an anonymous input pipe for this non-file Reader and
	// closes its writer after copying. Only the reviewed broker receives it.
	// This broker inherits Root's outer owned Job; no breakaway is requested.
	command.Stdin = strings.NewReader(input)
	command.Stdout, command.Stderr = out, stderr
	command.WaitDelay = 3 * time.Second
	if err = command.Run(); err != nil {
		t.Fatal("reviewed broker failed; inspect its public raw receipt", err)
	}
	raw, err := os.ReadFile(filepath.Join(output, "invocation.json"))
	if err != nil {
		t.Fatal(err)
	}
	// The broker retains additional original fields; this minimal projection
	// checks its actual Job closure without rewriting the original receipt.
	var result nativeMigrationHarnessBrokerResult
	if err = json.Unmarshal(raw, &result); err != nil {
		t.Fatal(err)
	}
	c := result.Result.Cleanup
	if result.Result.ActualExit == nil || result.Result.Error != nil || result.Result.TimedOut || !result.Result.Resumed ||
		!c.Assigned || !c.Idle || !c.Exited || !c.Closed || c.Active == nil || *c.Active != 0 || len(c.Errors) != 0 {
		t.Fatal("native process lifetime did not close cleanly")
	}
	stdoutRaw, err := os.ReadFile(filepath.Join(output, "stdout.raw"))
	if err != nil {
		t.Fatal(err)
	}
	stderrRaw, err := os.ReadFile(filepath.Join(output, "stderr.raw"))
	if err != nil {
		t.Fatal(err)
	}
	return result, stdoutRaw, stderrRaw
}
func nativeHarnessRelease(t *testing.T, cfg nativeMigrationHarnessConfig) recoveryauthority.Release {
	t.Helper()
	pins := nativeHarnessSourcePins(t, cfg.BuildRoot)
	if cfg.Case == "release-pin-mismatch" {
		// Deliberately incorrect, explicitly reviewed negative release. No
		// accepted source file or existing release is modified for this case.
		pins[0].SHA256 = Digest([]byte("SYNTHETIC_INVALID_SOURCE_PIN"))
	}
	now := time.Now().UTC()
	return recoveryauthority.Release{Schema: "researchos.recovery-release.v1", Purpose: recoveryauthority.Purpose,
		ID: "synthetic-native-" + cfg.CaseID, SID: nativeHarnessSID(t), RootImage: cfg.RootProgram, ControlImage: cfg.ControlProgram,
		SourceRoot: cfg.BuildRoot, SourceFiles: pins, RootSigningPublicKey: cfg.RootSigningPublicKey,
		NotBeforeUTC: now.Add(-time.Second).Format(time.RFC3339Nano), ExpiresUTC: now.Add(30 * time.Minute).Format(time.RFC3339Nano)}
}

func TestNativeMigrationAuthorityHarness(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Minute)
	t.Cleanup(cancel)
	raw, err := os.ReadFile(os.Getenv("RESEARCHOS_NATIVE_MIGRATION_HARNESS_CONFIG"))
	if err != nil {
		t.Fatal("Root public fixture configuration required", err)
	}
	var cfg nativeMigrationHarnessConfig
	if err = nativeHarnessDecode(raw, &cfg); err != nil {
		t.Fatal(err)
	}
	cases := map[string]string{
		"positive-replay": "", "missing-native-channel": "AUTHORITY_PRIVATE_INHERITANCE_REQUIRED",
		"wrong-purpose": "AUTHORITY_ISSUER_SIGNATURE", "mismatched-database": "AUTHORITY_MIGRATION_GRANT_NATIVE_ID",
		"release-pin-mismatch": "AUTHORITY_RAW_PIN_MISMATCH", "expired-grant": "AUTHORITY_MIGRATION_GRANT",
		"missing-dynamic-pin": "AUTHORITY_MIGRATION_REQUIRED_RAW_PIN_ABSENT", "wrong-owner": "FORBIDDEN: current project Owner required",
		"lease-occupied": "MEASURE_ACTUAL_WIN32_SHARING_VIOLATION",
	}
	expectedError, ok := cases[cfg.Case]
	if !ok || cfg.Schema != "researchos.synthetic-native-migration-config.v1" || cfg.CaseID == "" || !filepath.IsAbs(cfg.OutputDirectory) {
		t.Fatal("invalid Root synthetic native case")
	}
	cwd, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	buildRoot, err := filepath.Abs(filepath.Join(cwd, "../.."))
	if err != nil || !strings.EqualFold(buildRoot, filepath.Clean(cfg.BuildRoot)) {
		t.Fatal("harness build root mismatch", err)
	}
	if !strings.EqualFold(filepath.Dir(cfg.RootProgram.Path), filepath.Dir(cfg.ControlProgram.Path)) {
		t.Fatal("Root and Control must share a fresh case directory")
	}
	if key, err := hex.DecodeString(cfg.RootSigningPublicKey); err != nil || len(key) != 32 {
		t.Fatal("Root public signing key required")
	}
	for role, pin := range map[string]recoveryauthority.RawPin{
		"root-program": cfg.RootProgram, "control-program": cfg.ControlProgram, "backup-program": cfg.BackupProgram, "enrollment-program": cfg.EnrollmentProgram,
		"python-program": cfg.PythonProgram, "broker-source": cfg.BrokerSource, "private-stdin-helper": cfg.PrivateStdinHelper,
	} {
		if pin.Role != role {
			t.Fatal("Root public configuration role mismatch", role)
		}
	}
	for _, pin := range []recoveryauthority.RawPin{cfg.RootProgram, cfg.ControlProgram, cfg.BackupProgram, cfg.EnrollmentProgram, cfg.PythonProgram, cfg.BrokerSource, cfg.PrivateStdinHelper} {
		nativeHarnessRequirePin(t, pin)
	}
	if err = os.Mkdir(cfg.OutputDirectory, 0700); err != nil {
		t.Fatal("fresh Root output directory required", err)
	}
	rootDir := filepath.Dir(cfg.RootProgram.Path)
	for _, name := range []string{"recovery-release.json", "current-schema23-to24-grant.json", "consumed-schema23-to24-grants"} {
		if _, err = os.Lstat(filepath.Join(rootDir, name)); !os.IsNotExist(err) {
			t.Fatal("fresh Root fixed-file namespace required")
		}
	}

	opt, f, run := preparedUpgradePublicFixture(t)
	// Registered after the fixture's TempDir cleanups, so actual fixture files
	// remain available for Root inspection even when a later assertion fails.
	// A hard process kill/Go timeout cannot provide this graceful hold.
	t.Cleanup(func() {
		nativeHarnessWrite(t, filepath.Join(cfg.OutputDirectory, "06-fixture-retained.ready.json"), Object{
			"test_failed": t.Failed(), "database": opt.Source, "release_required": true})
		nativeHarnessWait(t, ctx, filepath.Join(cfg.OutputDirectory, "06-release-fixture.approval.json"), "release-fixture")
	})
	opt.SourceProgram, opt.TargetProgram = cfg.BackupProgram.Path, cfg.ControlProgram.Path
	// Issue all credentials before backup and retain only in this process.
	owner, err := f.s.IssueCredential(ctx, f.owner, 15*time.Minute)
	if err != nil {
		t.Fatal(err)
	}
	executor, err := f.s.IssueCredential(ctx, Str(run, "executor_principal_id"), 15*time.Minute)
	if err != nil {
		t.Fatal(err)
	}
	defer func() { owner = ""; executor = "" }()
	before, err := preparedUpgradeSnapshot(f.db)
	if err != nil {
		t.Fatal(err)
	}
	beforeSchema, err := preparedUpgradeSchema(f.db)
	if err != nil {
		t.Fatal(err)
	}
	if err = preparedUpgradeVersions(f.db, 23); err != nil {
		t.Fatal(err)
	}
	if err = f.db.Close(); err != nil {
		t.Fatal(err)
	}
	nativeHarnessWrite(t, filepath.Join(cfg.OutputDirectory, "before.rows.json"), before)
	nativeHarnessWrite(t, filepath.Join(cfg.OutputDirectory, "fixture.public.json"), Object{
		"schema": "researchos.synthetic-native-fixture.v1", "synthetic": true, "formal": false,
		"case": cfg.Case, "database": opt.Source, "root": filepath.Dir(opt.Source),
		"project_id": f.project, "owner_root": f.owner, "run_id": run["id"],
		"schema_sha256": beforeSchema, "typed_rows_sha256": Hash(before),
		"credential_output": false, "provider_requests": 0, "production_db_writes": 0})
	backupArgs := []string{"upgrade-local", "--db", opt.Source, "--backup", opt.Snapshot, "--out", opt.Destination,
		"--key-file", opt.KeyFile, "--source-root", opt.SourceRoot, "--root", opt.TargetRoot,
		"--source-program", opt.SourceProgram, "--target-program", opt.TargetProgram, "--plan", opt.Plan}
	backupResult, _, _ := nativeHarnessBroker(t, ctx, cfg, "00-rehearsal", cfg.BackupProgram, backupArgs, "PUBLIC_DUMMY_NO_OWNER_REQUIRED")
	if *backupResult.Result.ActualExit != 0 {
		t.Fatal("actual backup rehearsal failed")
	}
	unchanged, schema := nativeHarnessReadDB(t, opt.Source, 23)
	if Hash(unchanged) != Hash(before) || schema != beforeSchema {
		t.Fatal("rehearsal changed original fixture")
	}
	receiptRaw, err := os.ReadFile(filepath.Join(opt.Destination, preparedUpgradeReceiptName))
	if err != nil {
		t.Fatal(err)
	}
	var receipt preparedUpgradeRehearsalReceipt
	if err = nativeHarnessDecode(receiptRaw, &receipt); err != nil {
		t.Fatal(err)
	}
	if !receipt.OriginalUnchanged || !receipt.RollbackVerified || !receipt.ExistingRowsUnchanged ||
		receipt.OriginalRowsHash != Hash(before) || receipt.SourceSchema != beforeSchema || !reflect.DeepEqual(receipt.Options, opt) {
		t.Fatal("real rehearsal does not bind fixture")
	}
	nativeHarnessWrite(t, filepath.Join(cfg.OutputDirectory, "rehearsal.public.json"), receipt)
	release := nativeHarnessRelease(t, cfg)
	releasePayload := nativeHarnessWrite(t, filepath.Join(cfg.OutputDirectory, "01-release.payload.json"), release)
	nativeHarnessWrite(t, filepath.Join(cfg.OutputDirectory, "01-release.ready.json"), Object{
		"sign_kind": "release", "payload_sha256": Digest(releasePayload), "fixed_signed_path": filepath.Join(rootDir, "recovery-release.json"),
		"review_required": true, "synthetic_case": cfg.Case})
	approval := nativeHarnessWait(t, ctx, filepath.Join(cfg.OutputDirectory, "01-release.approval.json"), "release-signed")
	releaseRaw := nativeHarnessSigned(t, filepath.Join(rootDir, "recovery-release.json"), releasePayload, approval)

	optionsRaw, err := json.Marshal(opt)
	if err != nil {
		t.Fatal(err)
	}
	sourceInventory, _, err := preparedUpgradeRelease(opt.SourceRoot, 23)
	if err != nil {
		t.Fatal(err)
	}
	targetInventory, _, err := preparedUpgradeRelease(opt.TargetRoot, 24)
	if err != nil {
		t.Fatal(err)
	}
	backupPin := nativeHarnessPin(t, "encrypted-backup-manifest", filepath.Join(opt.Snapshot, "manifest.json"))
	rehearsalPin := nativeHarnessPin(t, "isolated-restore-rehearsal", filepath.Join(opt.Destination, preparedUpgradeReceiptName))
	binding := recoveryauthority.MigrationBinding{PlanID: opt.Plan, OwnerRoot: f.owner, ProjectID: f.project,
		Root: filepath.Dir(opt.Source), RootIdentity: nativeHarnessFileID(t, filepath.Dir(opt.Source), true),
		Database: opt.Source, DatabaseIdentity: nativeHarnessFileID(t, opt.Source, false),
		SourceReleaseSHA256: cfg.BackupProgram.SHA256, TargetReleaseSHA256: cfg.ControlProgram.SHA256,
		SourceInventorySHA256: Hash(sourceInventory), TargetInventorySHA256: Hash(targetInventory),
		SourceSchemaSHA256: receipt.SourceSchema, TargetSchemaSHA256: receipt.TargetSchema,
		SQLSHA256: recoveryauthority.MigrationSQLSHA256, OriginalRowsSHA256: Hash(before), OptionsSHA256: Digest(optionsRaw),
		Backup: backupPin, Rehearsal: rehearsalPin}
	pins := []recoveryauthority.RawPin{
		nativeHarnessPin(t, "source-program", opt.SourceProgram), nativeHarnessPin(t, "target-program", opt.TargetProgram),
		nativeHarnessPin(t, "migration-sql", filepath.Join(opt.TargetRoot, "migrations/sqlite/0024_prepared_run_abandonment.sql")), backupPin, rehearsalPin}
	for _, pair := range []struct {
		root, prefix string
		inventory    Object
	}{{opt.SourceRoot, "source-inventory:", sourceInventory}, {opt.TargetRoot, "target-inventory:", targetInventory}} {
		names := []string{}
		for name := range pair.inventory {
			names = append(names, name)
		}
		sort.Strings(names)
		for _, name := range names {
			pins = append(pins, nativeHarnessPin(t, pair.prefix+name, filepath.Join(pair.root, filepath.FromSlash(name))))
		}
	}
	encrypted, err := filepath.Glob(filepath.Join(opt.Snapshot, "*.enc"))
	if err != nil || len(encrypted) == 0 {
		t.Fatal("encrypted payload inventory", err)
	}
	sort.Strings(encrypted)
	for _, path := range encrypted {
		pins = append(pins, nativeHarnessPin(t, "encrypted-backup-payload:"+filepath.Base(path), path))
	}
	for _, name := range []string{"before.rows.json", "fixture.public.json", "00-rehearsal/invocation.json", "00-rehearsal/stdout.raw", "00-rehearsal/stderr.raw"} {
		pins = append(pins, nativeHarnessPin(t, "fixture-evidence:"+name, filepath.Join(cfg.OutputDirectory, filepath.FromSlash(name))))
	}
	nonceBytes := make([]byte, 32)
	if _, err = rand.Read(nonceBytes); err != nil {
		t.Fatal(err)
	}
	now := time.Now().UTC()
	grant := recoveryauthority.MigrationGrant{Schema: "researchos.recovery-migration-grant.v1", Purpose: recoveryauthority.MigrationPurpose,
		Stage: "APPLY_ORIGINAL", ReleaseSHA256: Digest(releaseRaw), Nonce: hex.EncodeToString(nonceBytes),
		IssuedUTC: now.Format(time.RFC3339Nano), ExpiresUTC: now.Add(4 * time.Minute).Format(time.RFC3339Nano),
		Binding: binding, Pins: pins, Options: optionsRaw}
	switch cfg.Case {
	case "mismatched-database":
		other, err := os.CreateTemp(t.TempDir(), "other-native-file-")
		if err != nil {
			t.Fatal(err)
		}
		otherPath := other.Name()
		if err = other.Close(); err != nil {
			t.Fatal(err)
		}
		grant.Binding.DatabaseIdentity = nativeHarnessFileID(t, otherPath, false)
	case "expired-grant":
		grant.IssuedUTC = now.Add(-6 * time.Minute).Format(time.RFC3339Nano)
		grant.ExpiresUTC = now.Add(-2 * time.Minute).Format(time.RFC3339Nano)
	case "missing-dynamic-pin":
		for i, pin := range grant.Pins {
			if strings.HasPrefix(pin.Role, "source-inventory:") {
				grant.Pins = append(grant.Pins[:i], grant.Pins[i+1:]...)
				break
			}
		}
	}
	var grantValue any = grant
	signKind := "migration-grant"
	if cfg.Case == "wrong-purpose" {
		signKind = "grant"
		grantValue = recoveryauthority.Grant{Schema: "researchos.recovery-grant.v1", Purpose: recoveryauthority.Purpose,
			ReleaseSHA256: grant.ReleaseSHA256, Nonce: grant.Nonce, IssuedUTC: grant.IssuedUTC, ExpiresUTC: grant.ExpiresUTC,
			Root: binding.Root, RootIdentity: binding.RootIdentity, Database: binding.Database, DatabaseIdentity: binding.DatabaseIdentity, Pins: pins}
	}
	grantPayload := nativeHarnessWrite(t, filepath.Join(cfg.OutputDirectory, "02-grant.payload.json"), grantValue)
	nativeHarnessWrite(t, filepath.Join(cfg.OutputDirectory, "02-grant.ready.json"), Object{
		"sign_kind": signKind, "payload_sha256": Digest(grantPayload), "fixed_signed_path": filepath.Join(rootDir, "current-schema23-to24-grant.json"),
		"expires_utc": grant.ExpiresUTC, "review_required": true, "synthetic_case": cfg.Case, "intentional_negative": cfg.Case != "positive-replay"})
	approval = nativeHarnessWait(t, ctx, filepath.Join(cfg.OutputDirectory, "02-grant.approval.json"), "grant-signed-and-invoke")
	nativeHarnessSigned(t, filepath.Join(rootDir, "current-schema23-to24-grant.json"), grantPayload, approval)
	input := owner
	program := cfg.RootProgram
	args := []string{"schema23-to24"}
	if cfg.Case == "wrong-owner" {
		input = executor
	}
	if cfg.Case == "missing-native-channel" {
		input = "PUBLIC_DUMMY_NO_OWNER_REQUIRED"
		program = cfg.ControlProgram
		args = []string{recoveryauthority.MigrationArgument}
	}
	var occupied *runtimeadapter.DataRootLease
	if cfg.Case == "lease-occupied" {
		occupied, err = runtimeadapter.AcquireDataRootLease(filepath.Dir(opt.Source))
		if err != nil {
			t.Fatal(err)
		}
		defer occupied.Close()
		if !occupied.Held() {
			t.Fatal("live fixture lease was not retained")
		}
		second, probeErr := runtimeadapter.AcquireDataRootLease(filepath.Dir(opt.Source))
		if second != nil {
			second.Close()
			t.Fatal("exclusive lease probe unexpectedly acquired")
		}
		if !errors.Is(probeErr, windows.ERROR_SHARING_VIOLATION) {
			t.Fatal("exclusive lease probe did not measure Win32 sharing violation", probeErr)
		}
		expectedError = probeErr.Error()
		var created, exited, kernel, user windows.Filetime
		if err = windows.GetProcessTimes(windows.CurrentProcess(), &created, &exited, &kernel, &user); err != nil {
			t.Fatal(err)
		}
		nativeHarnessWrite(t, filepath.Join(cfg.OutputDirectory, "03-live-lease.public.json"), Object{
			"root": occupied.Root(), "held_before_native": true, "holder_pid": os.Getpid(),
			"holder_creation_time_100ns": uint64(created.HighDateTime)<<32 | uint64(created.LowDateTime),
			"second_acquire_win32_code":  uint32(windows.ERROR_SHARING_VIOLATION), "expected_native_error": expectedError})
	}
	native, stdout, stderr := nativeHarnessBroker(t, ctx, cfg, "03-native", program, args, input)
	input = ""
	if occupied != nil {
		if !occupied.Held() {
			t.Fatal("live lease ended before actual native process closure")
		}
		if err = occupied.Close(); err != nil {
			t.Fatal(err)
		}
		nativeHarnessWrite(t, filepath.Join(cfg.OutputDirectory, "03-live-lease.closed.json"), Object{
			"held_through_native_closure": true, "close_succeeded": true, "held_after_close": occupied.Held()})
		if occupied.Held() {
			t.Fatal("fixture lease still held after close")
		}
	}
	expectedVersion := 23
	if cfg.Case == "positive-replay" {
		expectedVersion = 24
	}
	after, afterSchema := nativeHarnessReadDB(t, opt.Source, expectedVersion)
	nativeHarnessWrite(t, filepath.Join(cfg.OutputDirectory, "after.rows.json"), after)
	if cfg.Case == "positive-replay" {
		if *native.Result.ActualExit != 0 {
			t.Fatal("native migration positive failed; inspect public stderr")
		}
		var result Object
		if err = json.Unmarshal(stdout, &result); err != nil {
			t.Fatal(err)
		}
		if result["status"] != "SCHEMA24_COMMITTED_ORIGINAL_BUSINESS_ROWS_UNCHANGED" || result["committed"] != true ||
			result["abandonment_performed"] != false || result["provider_requests"] != nil || result["financial_closed"] != false {
			t.Fatal("native migration result differs")
		}
		if err = preparedUpgradeRowInvariant(before, after); err != nil {
			t.Fatal(err)
		}
		if afterSchema != receipt.TargetSchema || len(after[preparedUpgradeProofTable].Rows) != 0 {
			t.Fatal("native migration schema/proof table differs")
		}
		replay, _, replayErr := nativeHarnessBroker(t, ctx, cfg, "04-replay", cfg.RootProgram, []string{"schema23-to24"}, owner)
		replayRows, replaySchema := nativeHarnessReadDB(t, opt.Source, 24)
		if *replay.Result.ActualExit == 0 || !nativeHarnessExpectedError(replayErr, "AUTHORITY_MIGRATION_GRANT_ALREADY_USED") ||
			Hash(replayRows) != Hash(after) || replaySchema != afterSchema {
			t.Fatal("actual nonce replay rejection/state mismatch")
		}
	} else {
		if *native.Result.ActualExit == 0 || !nativeHarnessExpectedError(stderr, expectedError) {
			t.Fatal("native negative did not reach its designated rejection layer")
		}
		if Hash(after) != Hash(before) || afterSchema != beforeSchema {
			t.Fatal("native rejection changed whole fixture rows/schema")
		}
	}
	nativeHarnessWrite(t, filepath.Join(cfg.OutputDirectory, "05-case.result.json"), Object{
		"status": "EXECUTION_REPORTED_PENDING_ROOT_INDEPENDENT_REVIEW", "case": cfg.Case, "synthetic": true, "formal": false,
		"production_db_writes": 0, "provider_requests": 0, "before_rows_sha256": Hash(before), "after_rows_sha256": Hash(after),
		"before_schema_sha256": beforeSchema, "after_schema_sha256": afterSchema, "expected_rejection": expectedError,
		"inner_native_job_id_independently_observed": false, "fixture_retained_until_root_release": true})
}

// Root supplies this public proof root only to the fixed harness process.
// It is never forwarded to the broker or any native child.
func nativeHarnessBrokerPublicEnvironment(proofRoot string, environment map[string]string) (map[string]string, error) {
	if len(environment) != 4 {
		return nil, fmt.Errorf("synthetic native broker public environment must contain exactly four keys")
	}
	resolve := func(name, path string) (string, error) {
		if strings.TrimSpace(path) == "" || !filepath.IsAbs(path) {
			return "", fmt.Errorf("synthetic native broker %s must be an absolute directory", name)
		}
		info, err := os.Stat(path)
		if err != nil || !info.IsDir() {
			return "", fmt.Errorf("synthetic native broker %s directory unavailable", name)
		}
		resolved, err := filepath.EvalSymlinks(path)
		if err != nil || !filepath.IsAbs(resolved) {
			return "", fmt.Errorf("synthetic native broker %s physical directory unavailable", name)
		}
		return filepath.Clean(resolved), nil
	}
	root, err := resolve("proof root", proofRoot)
	if err != nil {
		return nil, err
	}
	physical := make(map[string]string, 4)
	for _, name := range []string{"SystemRoot", "WINDIR", "TEMP", "TMP"} {
		path, ok := environment[name]
		if !ok {
			return nil, fmt.Errorf("synthetic native broker public environment key unavailable")
		}
		physical[name], err = resolve(name, path)
		if err != nil {
			return nil, err
		}
	}
	for _, name := range []string{"SystemRoot", "WINDIR"} {
		if nativeHarnessTempWithin(root, physical[name]) || nativeHarnessTempWithin(physical[name], root) {
			return nil, fmt.Errorf("synthetic native broker proof root overlaps a system directory")
		}
	}
	for _, name := range []string{"TEMP", "TMP"} {
		if !nativeHarnessTempWithin(proofRoot, environment[name]) || !nativeHarnessTempWithin(root, physical[name]) {
			return nil, fmt.Errorf("synthetic native broker %s escapes the isolated proof root", name)
		}
	}
	return map[string]string{
		"SystemRoot": environment["SystemRoot"], "WINDIR": environment["WINDIR"],
		"TEMP": environment["TEMP"], "TMP": environment["TMP"],
	}, nil
}

// Windows comparisons apply to the original and EvalSymlinks-resolved paths.
func nativeHarnessTempWithin(root, path string) bool {
	relative, err := filepath.Rel(strings.ToLower(filepath.Clean(root)), strings.ToLower(filepath.Clean(path)))
	return err == nil && relative != ".." && !strings.HasPrefix(relative, ".."+string(filepath.Separator)) && !filepath.IsAbs(relative)
}

// Synthetic local filesystem/env fixtures only; no native migration authority.
func TestNativeHarnessBrokerIsolatedTempEnvironment(t *testing.T) {
	proof, outside, system := t.TempDir(), t.TempDir(), t.TempDir()
	temp, tmp := filepath.Join(proof, "temp"), filepath.Join(proof, "tmp")
	for _, path := range []string{temp, tmp} {
		if err := os.Mkdir(path, 0700); err != nil {
			t.Fatal(err)
		}
	}
	file := filepath.Join(proof, "not-directory")
	if err := os.WriteFile(file, []byte("synthetic fixture"), 0600); err != nil {
		t.Fatal(err)
	}
	base := map[string]string{"SystemRoot": system, "WINDIR": system, "TEMP": temp, "TMP": tmp}
	cases := []struct {
		name, proof, key, value string
		valid                   bool
	}{
		{"local-temp-allowed", proof, "", "", true},
		{"case-normalized-root", strings.ToUpper(proof), "", "", true},
		{"empty-proof", "", "", "", false},
		{"relative-proof", ".", "", "", false},
		{"missing-proof", filepath.Join(proof, "missing"), "", "", false},
		{"empty-temp", proof, "TEMP", "", false},
		{"empty-tmp", proof, "TMP", "", false},
		{"relative-temp", proof, "TEMP", "temp", false},
		{"relative-tmp", proof, "TMP", "tmp", false},
		{"missing-temp", proof, "TEMP", filepath.Join(proof, "missing"), false},
		{"file-as-temp", proof, "TEMP", file, false},
		{"temp-outside-proof", proof, "TEMP", outside, false},
		{"tmp-different-root", proof, "TMP", outside, false},
		{"proof-is-system-directory", system, "", "", false},
		{"proof-contains-system-directory", filepath.Dir(system), "", "", false},
		{"empty-system-root", proof, "SystemRoot", "", false},
		{"empty-windir", proof, "WINDIR", "", false},
		{"unexpected-environment-key", proof, "RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT", proof, false},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			env := map[string]string{"SystemRoot": base["SystemRoot"], "WINDIR": base["WINDIR"], "TEMP": base["TEMP"], "TMP": base["TMP"]}
			if tc.key != "" {
				env[tc.key] = tc.value
			}
			actual, err := nativeHarnessBrokerPublicEnvironment(tc.proof, env)
			if !tc.valid {
				if err == nil || actual != nil {
					t.Fatal("invalid isolated public environment was accepted")
				}
				return
			}
			if err != nil || !reflect.DeepEqual(actual, base) {
				t.Fatal("valid isolated public environment changed or was rejected", err)
			}
		})
	}
}

// Pure path-boundary comparisons are synthetic; these do not create a junction
// or claim actual reparse-point execution. The env helper always EvalSymlinks.
func TestNativeHarnessBrokerTempBoundaryComparison(t *testing.T) {
	cases := []struct {
		name, root, path string
		inside           bool
	}{
		{"same-directory", "D:/isolated", "D:/isolated", true},
		{"child-directory", "D:/isolated", "D:/isolated/temp", true},
		{"windows-case", "D:/Isolated", "d:/isolated/TEMP", true},
		{"prefix-sibling", "D:/isolated", "D:/isolated-escape/temp", false},
		{"parent-escape", "D:/isolated", "D:/isolated/../outside", false},
		{"resolved-alias-escape", "D:/isolated", "D:/outside", false},
		{"different-volume", "D:/isolated", "C:/temp", false},
		{"system-outside-proof", "D:/isolated", "C:/Windows", false},
		{"system-contains-root", "C:/Windows", "C:/Windows/temp", true},
		{"root-contains-system", "C:/", "C:/Windows", true},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if actual := nativeHarnessTempWithin(tc.root, tc.path); actual != tc.inside {
				t.Fatal("Windows physical path boundary comparison differs", tc.name)
			}
		})
	}
}
