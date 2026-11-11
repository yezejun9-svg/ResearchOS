//go:build windows

package main

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"sync/atomic"
	"testing"
	"time"

	"net/http"
	"net/http/httptest"

	"researchos.local/research-os/adapters/local_workspace"
	"researchos.local/research-os/internal/api"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/host"
	"researchos.local/research-os/internal/store"
)

// This runs a compiled CLI against the real same-SID named pipe, private Host
// credential file, typed HTTP handler, SQLite service and local workspace
// adapter. Only the OS folder dialog is replaced by a deterministic test
// selection; visible human dialog interaction remains unverified.
func TestCLIRealFirstUseAndContinuation(t *testing.T) {
	root := t.TempDir()
	dataDir := filepath.Join(root, "data")
	if err := os.MkdirAll(dataDir, 0o700); err != nil {
		t.Fatal(err)
	}
	workspace := filepath.Join(root, "研究 空间")
	if err := os.Mkdir(workspace, 0o700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(workspace, "README.md"), []byte("# Real first-use inventory\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	db, err := store.Open(filepath.Join(dataDir, "researchos.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { db.Close() })
	if err := store.Bootstrap(context.Background(), db, "../../migrations/sqlite/0001_bootstrap.sql"); err != nil {
		t.Fatal(err)
	}
	service, err := domain.New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if err != nil {
		t.Fatal(err)
	}
	var hostClock atomic.Int64
	hostClock.Store(time.Now().UTC().UnixNano())
	localHost, err := host.New(host.Config{DB: db, Dir: filepath.Join(dataDir, "host"),
		ContractsDir: "../../spec/v2.0/contracts", MigrationFile: "../../migrations/sqlite/0002_domain.sql",
		SchemaDir: "../../internal/api/contracts", Now: func() time.Time { return time.Unix(0, hostClock.Load()).UTC() }})
	if err != nil {
		t.Fatal(err)
	}
	server := httptest.NewServer(api.HandlerWithConfigurationHost(db, t.TempDir(), service, nil, localHost.InstanceID(),
		localworkspace.NewAuthority(localHost), localworkspace.NewScanner(), localHost))
	t.Cleanup(server.Close)
	d := discovery{URL: server.URL, PID: os.Getpid(), DataDir: dataDir}
	discoveryFile := filepath.Join(dataDir, "discovery.json")
	writeCLIDiscovery(t, discoveryFile, d, localHost.InstanceID())
	configFile := filepath.Join(root, "cli-config.json")

	var choiceCount atomic.Int32
	var refuseChoice atomic.Bool
	pipe := host.PipeName(localHost.InstanceID())
	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan error, 1)
	go func() {
		done <- localHost.ServeNativeWithChooser(ctx, pipe, func(hint string) (string, error) {
			choiceCount.Add(1)
			if hint != workspace {
				t.Errorf("CLI passed a different chooser hint: %q", hint)
			}
			if refuseChoice.Load() {
				return "", nil
			}
			return workspace, nil
		})
	}()
	t.Cleanup(func() {
		cancel()
		wake, _ := json.Marshal(host.NativeFrame{Kind: "NATIVE_UNKNOWN", ClientID: "test-wake", Payload: json.RawMessage(`{}`)})
		_, _ = host.DialNative(pipe, wake)
		select {
		case <-done:
		case <-time.After(5 * time.Second):
			t.Error("native server did not stop")
		}
	})

	exe := filepath.Join(root, "researchos-first-use.exe")
	build := exec.Command(filepath.Join(runtime.GOROOT(), "bin", "go.exe"), "build", "-o", exe, ".")
	build.Dir = "."
	if output, err := build.CombinedOutput(); err != nil {
		t.Fatalf("build real CLI: %v\n%s", err, output)
	}
	run := func(config string, args ...string) (map[string]any, int, string) {
		t.Helper()
		callCtx, stop := context.WithTimeout(context.Background(), 30*time.Second)
		defer stop()
		cmd := exec.CommandContext(callCtx, exe, args...)
		cmd.Env = append(os.Environ(), "RESEARCHOS_CLI_DISCOVERY="+discoveryFile,
			"RESEARCHOS_CLI_CONFIG="+config, "RESEARCHOS_CLI_CREDENTIAL=", "RESEARCHOS_CLI_CLIENT_ID=cli-real-first-use")
		output, err := cmd.CombinedOutput()
		if callCtx.Err() != nil {
			t.Fatalf("CLI timed out: %v\n%s", callCtx.Err(), output)
		}
		code := 0
		if err != nil {
			if exit, ok := err.(*exec.ExitError); ok {
				code = exit.ExitCode()
			} else {
				t.Fatalf("CLI could not start: %v", err)
			}
		}
		var record map[string]any
		for _, line := range strings.Split(strings.TrimSpace(string(output)), "\n") {
			if json.Unmarshal([]byte(line), &record) == nil && record["command"] != nil {
				break
			}
		}
		return record, code, string(output)
	}

	first, exitCode, output := run(configFile, "init", workspace)
	if exitCode != 0 || first["status"] != "COMPLETED" {
		t.Fatalf("real first-use failed: exit=%d record=%v\n%s", exitCode, first, output)
	}
	if choiceCount.Load() != 1 {
		t.Fatalf("folder chooser calls: %d", choiceCount.Load())
	}
	session, err := localHost.ReadSessionFile()
	if err != nil || session.Token == "" || strings.Contains(output, session.Token) {
		t.Fatalf("private Host session boundary failed: %v", err)
	}
	config := readCLIIntegrationConfig(t, configFile)
	if config.ProjectID == "" || config.WorkspaceRef == "" || config.ProjectID != first["project_id"] || config.WorkspaceRef != first["workspace_ref"] {
		t.Fatalf("CLI did not persist real Host IDs: %+v record=%v", config, first)
	}
	if got := countCLIObjects(t, db, "ProjectProfile"); got != 1 {
		t.Fatalf("first-use projects=%d", got)
	}

	second, exitCode, output := run(configFile, "init", workspace)
	if exitCode != 0 || second["status"] != "COMPLETED" {
		t.Fatalf("real continuation failed: exit=%d record=%v\n%s", exitCode, second, output)
	}
	continued := readCLIIntegrationConfig(t, configFile)
	if continued.ProjectID != config.ProjectID || continued.WorkspaceRef != config.WorkspaceRef || countCLIObjects(t, db, "ProjectProfile") != 1 {
		t.Fatalf("continuation minted a second project or persisted an unbound alias: before=%+v after=%+v", config, continued)
	}
	if choiceCount.Load() != 2 {
		t.Fatalf("continuation did not require another choice: %d", choiceCount.Load())
	}

	refuseChoice.Store(true)
	failedConfig := filepath.Join(root, "failed-cli-config.json")
	failed, exitCode, output := run(failedConfig, "init", workspace)
	if exitCode == 0 || failed["status"] == "COMPLETED" {
		t.Fatalf("rejected choice reported success: exit=%d record=%v\n%s", exitCode, failed, output)
	}
	if _, err := os.Stat(failedConfig); !os.IsNotExist(err) {
		t.Fatal("failed choice persisted a fabricated CLI config")
	}
	if err := os.Remove(localHost.SessionFile()); err != nil {
		t.Fatal(err)
	}
	choicesBeforeStatus := choiceCount.Load()
	status, exitCode, output := run(configFile, "status")
	if exitCode != 0 || status["status"] != "COMPLETED" {
		t.Fatalf("existing project could not renew local identity: exit=%d record=%v\n%s", exitCode, status, output)
	}
	if choiceCount.Load() != choicesBeforeStatus {
		t.Fatal("ordinary CLI command opened native workspace choice")
	}
	if renewed, err := localHost.ReadSessionFile(); err != nil || renewed.Token == "" || strings.Contains(output, renewed.Token) {
		t.Fatal("native renewal failed or exposed the private credential")
	} else {
		session = renewed
	}

	// These selections traverse the same named pipe and typed HTTP route. The
	// host must reject a different client, a spent ref and an expired ref.
	refuseChoice.Store(false)
	selectRef := func() string {
		t.Helper()
		frame, _ := json.Marshal(host.NativeFrame{Kind: host.KindWorkspaceChooseRequest, ClientID: "cli-real-first-use",
			Payload: json.RawMessage(domain.Bytes(domain.Object{"requested_path": workspace, "requested_access": "READ_WRITE"}))})
		raw, err := host.DialNative(pipe, frame)
		if err != nil {
			t.Fatal(err)
		}
		var result struct {
			Kind    string `json:"kind"`
			Payload struct {
				Ref string `json:"selection_ref"`
			} `json:"payload"`
		}
		if err := json.Unmarshal(raw, &result); err != nil || result.Kind != host.KindWorkspaceChooseResult || result.Payload.Ref == "" {
			t.Fatalf("native choice failed: %s %v", raw, err)
		}
		return result.Payload.Ref
	}
	register := func(ref, client string) map[string]any {
		t.Helper()
		commandID, err := cliFirstUseCommandID("selection-probe")
		if err != nil {
			t.Fatal(err)
		}
		envelope := domain.Object{"protocol_version": domain.ProtocolV2, "command_id": commandID,
			"client_id": client, "project_id": nil, "session_id": nil, "expected_revision": nil,
			"writer_epoch": nil, "method": "workspace.register", "payload": domain.Object{
				"selection_ref": ref, "display_name": "selection-probe", "requested_access": "READ_WRITE"}}
		request, err := http.NewRequest(http.MethodPost, server.URL+v2CommandPath, bytes.NewReader(domain.Bytes(envelope)))
		if err != nil {
			t.Fatal(err)
		}
		request.Header.Set("Content-Type", "application/json")
		request.Header.Set("Authorization", "Bearer "+session.Token)
		response, err := server.Client().Do(request)
		if err != nil {
			t.Fatal(err)
		}
		defer response.Body.Close()
		var result map[string]any
		if err := json.NewDecoder(response.Body).Decode(&result); err != nil {
			t.Fatal(err)
		}
		return result
	}
	foreignRef := selectRef()
	if wrong := register(foreignRef, "another-client"); wrong["status"] != "REJECTED" || wrong["error_code"] != "FORBIDDEN" {
		t.Fatalf("cross-client selection was not refused: %v", wrong)
	}
	if own := register(foreignRef, "cli-real-first-use"); own["status"] != "COMPLETED" {
		t.Fatalf("original client could not redeem selection after foreign refusal: %v", own)
	}
	if reused := register(foreignRef, "cli-real-first-use"); reused["status"] != "REJECTED" || reused["error_code"] != "SELECTION_ALREADY_USED" {
		t.Fatalf("spent selection was accepted: %v", reused)
	}
	expiredRef := selectRef()
	hostClock.Add(int64(host.SelectionTTL + time.Second))
	if expired := register(expiredRef, "cli-real-first-use"); expired["status"] != "REJECTED" || expired["error_code"] != "SELECTION_EXPIRED" {
		t.Fatalf("expired selection was accepted: %v", expired)
	}
}

func readCLIIntegrationConfig(t *testing.T, path string) cliConfig {
	t.Helper()
	var config cliConfig
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if err := json.Unmarshal(raw, &config); err != nil {
		t.Fatal(err)
	}
	return config
}

func countCLIObjects(t *testing.T, db *sql.DB, kind string) int {
	t.Helper()
	var count int
	if err := db.QueryRow(`SELECT count(*) FROM domain_objects WHERE kind=?`, kind).Scan(&count); err != nil {
		t.Fatal(err)
	}
	return count
}
