package main

import (
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"researchos.local/research-os/internal/host"
)

func writeCLIDiscovery(t *testing.T, file string, d discovery, hostID string) {
	t.Helper()
	raw, err := json.Marshal(map[string]any{"url": d.URL, "pid": d.PID, "data_dir": d.DataDir,
		"host_instance_id": hostID})
	if err != nil {
		t.Fatal(err)
	}
	if err := os.MkdirAll(filepath.Dir(file), 0o700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(file, raw, 0o600); err != nil {
		t.Fatal(err)
	}
}

func TestCLIInitUsesNativeSelectionAndHostAssignedRefs(t *testing.T) {
	root := t.TempDir()
	workspace := filepath.Join(root, "研究 空间")
	if err := os.Mkdir(workspace, 0o700); err != nil {
		t.Fatal(err)
	}
	configFile := filepath.Join(root, "cli-config.json")
	steps := []string{}
	commandIDs := []string{}
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != v2CommandPath || r.Header.Get("Authorization") != "Bearer controlled-token" {
			t.Errorf("unexpected request path/auth: %s", r.URL.Path)
			http.Error(w, "bad request", http.StatusBadRequest)
			return
		}
		var request struct {
			CommandID string         `json:"command_id"`
			ProjectID *string        `json:"project_id"`
			Method    string         `json:"method"`
			Payload   map[string]any `json:"payload"`
		}
		if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
			t.Error(err)
			return
		}
		if request.ProjectID != nil {
			t.Errorf("first-use method claimed project_id: %s", *request.ProjectID)
		}
		if _, err := os.Stat(configFile); !os.IsNotExist(err) {
			t.Error("CLI persisted configuration before Host bootstrap completed")
		}
		steps = append(steps, request.Method)
		commandIDs = append(commandIDs, request.CommandID)
		var result map[string]any
		switch request.Method {
		case "workspace.register":
			if request.Payload["selection_ref"] != "sel-from-picker" || request.Payload["requested_access"] != "READ_WRITE" {
				t.Errorf("untrusted register payload: %+v", request.Payload)
			}
			result = map[string]any{"authorized_workspace_ref": "ws-from-host"}
		case "project.bootstrap":
			if request.Payload["authorized_workspace_ref"] != "ws-from-host" {
				t.Errorf("bootstrap did not use Host ref: %+v", request.Payload)
			}
			result = map[string]any{"project_id": "proj-from-host", "workspace": map[string]any{
				"authorized_workspace_ref": "ws-from-host", "project_id": "proj-from-host", "status": "ACTIVE"}}
		default:
			t.Errorf("unexpected method: %s", request.Method)
		}
		_ = json.NewEncoder(w).Encode(map[string]any{"status": "COMPLETED", "result": result})
	}))
	defer server.Close()
	d := discovery{URL: server.URL, PID: 42, DataDir: filepath.Join(root, "data")}
	discoveryFile := filepath.Join(root, "discovery.json")
	writeCLIDiscovery(t, discoveryFile, d, "host-012345abcdef")
	t.Setenv("RESEARCHOS_CLI_DISCOVERY", discoveryFile)
	t.Setenv("RESEARCHOS_CLI_CONFIG", configFile)
	t.Setenv("RESEARCHOS_CLI_CREDENTIAL", "")
	previousDial := cliNativeDial
	nativeSteps := []string{}
	cliNativeDial = func(pipe string, request []byte) ([]byte, error) {
		if pipe != host.PipeName("host-012345abcdef") {
			t.Errorf("wrong native pipe: %s", pipe)
		}
		var frame host.NativeFrame
		if err := json.Unmarshal(request, &frame); err != nil {
			t.Fatal(err)
		}
		nativeSteps = append(nativeSteps, frame.Kind)
		if frame.Kind == host.KindUserBootstrapRequest {
			privateFile := filepath.Join(d.DataDir, "host", "session.json")
			if err := os.MkdirAll(filepath.Dir(privateFile), 0o700); err != nil {
				t.Fatal(err)
			}
			raw, _ := json.Marshal(map[string]any{"token": "controlled-token", "expires_at": time.Now().Add(time.Minute).Format(time.RFC3339Nano)})
			if err := os.WriteFile(privateFile, raw, 0o600); err != nil {
				t.Fatal(err)
			}
			return []byte(`{"kind":"NATIVE_USER_BOOTSTRAP_RESULT","payload":{"host_instance_id":"host-012345abcdef"}}`), nil
		}
		var choice map[string]any
		if err := json.Unmarshal(frame.Payload, &choice); err != nil {
			t.Fatal(err)
		}
		if frame.Kind != host.KindWorkspaceChooseRequest || choice["requested_path"] != workspace {
			t.Errorf("path was not merely a picker hint: %s", request)
		}
		return []byte(`{"kind":"NATIVE_WORKSPACE_CHOOSE_RESULT","payload":{"selection_ref":"sel-from-picker","display_path":"` + strings.ReplaceAll(workspace, `\`, `\\`) + `","expires_at":"2026-10-05T00:00:00Z"}}`), nil
	}
	t.Cleanup(func() { cliNativeDial = previousDial })
	oldStdout := os.Stdout
	reader, writer, err := os.Pipe()
	if err != nil {
		t.Fatal(err)
	}
	os.Stdout = writer
	defer func() { os.Stdout = oldStdout; reader.Close() }()
	cliInit([]string{workspace})
	writer.Close()
	output, err := io.ReadAll(reader)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(output), `"status":"COMPLETED"`) {
		t.Fatalf("init did not complete: %s", output)
	}
	if len(steps) != 2 || steps[0] != "workspace.register" || steps[1] != "project.bootstrap" || commandIDs[0] == commandIDs[1] {
		t.Fatalf("wrong first-use chain: steps=%v command_ids=%v", steps, commandIDs)
	}
	if len(nativeSteps) != 2 || nativeSteps[0] != host.KindUserBootstrapRequest || nativeSteps[1] != host.KindWorkspaceChooseRequest {
		t.Fatalf("wrong native first-use chain: %v", nativeSteps)
	}
	config, err := readConfig()
	if err != nil || config.WorkspaceRef != "ws-from-host" || config.ProjectID != "proj-from-host" {
		t.Fatalf("did not persist Host refs: %+v %v", config, err)
	}
}

func TestCLINativeDiscoveryFallbackRejectsMismatch(t *testing.T) {
	root := t.TempDir()
	d := discovery{URL: "http://127.0.0.1:1234", PID: 12, DataDir: filepath.Join(root, "data")}
	legacy := filepath.Join(root, "legacy.json")
	writeCLIDiscovery(t, legacy, d, "")
	t.Setenv("RESEARCHOS_CLI_DISCOVERY", legacy)
	current := filepath.Join(d.DataDir, "discovery.json")
	writeCLIDiscovery(t, current, discovery{URL: d.URL, PID: 99, DataDir: d.DataDir}, "host-012345abcdef")
	if _, err := cliHostInstanceID(d); err == nil {
		t.Fatal("accepted a different process native pipe")
	}
	writeCLIDiscovery(t, current, d, "host-012345abcdef")
	if id, err := cliHostInstanceID(d); err != nil || id != "host-012345abcdef" {
		t.Fatalf("matching current discovery refused: %s %v", id, err)
	}
}

func TestCLISessionCredentialExpiresWithoutNativeUI(t *testing.T) {
	root := t.TempDir()
	d := discovery{DataDir: root}
	path := filepath.Join(root, "host", "session.json")
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		t.Fatal(err)
	}
	write := func(exp time.Time) {
		raw, _ := json.Marshal(map[string]any{"token": "private-token", "expires_at": exp.Format(time.RFC3339Nano)})
		if err := os.WriteFile(path, raw, 0o600); err != nil {
			t.Fatal(err)
		}
	}
	write(time.Now().Add(-time.Minute))
	if token, err := cliSessionCredential(d); err == nil || token != "" {
		t.Fatal("expired credential accepted")
	}
	write(time.Now().Add(time.Minute))
	if token, err := cliSessionCredential(d); err != nil || token != "private-token" {
		t.Fatalf("current local credential refused: %q %v", token, err)
	}
}
