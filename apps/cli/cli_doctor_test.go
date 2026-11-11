package main

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"sync/atomic"
	"testing"
	"time"

	"researchos.local/research-os/internal/api"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/host"
	"researchos.local/research-os/internal/store"
)

const doctorSentinel = "doctor-test-BEARER-do-not-print"

func doctorBinary(t *testing.T) string {
	t.Helper()
	if exe := os.Getenv("RESEARCHOS_DOCTOR_TEST_BINARY"); exe != "" {
		return exe
	}
	exe := filepath.Join(t.TempDir(), "researchos-doctor.exe")
	goName := "go"
	if runtime.GOOS == "windows" {
		goName += ".exe"
	}
	c := exec.Command(filepath.Join(runtime.GOROOT(), "bin", goName), "build", "-o", exe, ".")
	if raw, err := c.CombinedOutput(); err != nil {
		t.Fatalf("build: %v %s", err, raw)
	}
	return exe
}

func doctorRun(t *testing.T, exe, discoveryFile, config, credential string) (map[string]any, int, string) {
	t.Helper()
	cwd := filepath.Join(t.TempDir(), "医生 诊断")
	if err := os.Mkdir(cwd, 0700); err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	cmd := exec.CommandContext(ctx, exe, "doctor")
	cmd.Dir = cwd
	cmd.Env = append(os.Environ(), "RESEARCHOS_CLI_DISCOVERY="+discoveryFile, "RESEARCHOS_CLI_CONFIG="+config,
		"RESEARCHOS_CLI_CREDENTIAL="+credential, "RESEARCHOS_CLI_CLIENT_ID=doctor-test-client")
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	err := cmd.Run()
	code := 0
	if err != nil {
		if ee, ok := err.(*exec.ExitError); ok {
			code = ee.ExitCode()
		} else {
			t.Fatal(err)
		}
	}
	if ctx.Err() != nil {
		t.Fatal(ctx.Err())
	}
	lines := strings.Split(strings.TrimSpace(stdout.String()), "\n")
	var out map[string]any
	if len(lines) != 1 || json.Unmarshal([]byte(lines[0]), &out) != nil {
		t.Fatalf("not one JSONL: %q", stdout.String())
	}
	combined := stdout.String() + stderr.String()
	if strings.Contains(combined, doctorSentinel) {
		t.Fatal("credential sentinel disclosed")
	}
	if out["exit_code"] != float64(code) {
		t.Fatalf("exit mismatch: %d %v", code, out)
	}
	row, _ := json.Marshal(map[string]any{"actualargv": cmd.Args, "cwd": cwd, "exit": code, "stdout": stdout.String(), "stderr": stderr.String(), "mode": "FIXTURE"})
	t.Logf("DOCTOR_NATIVE %s", row)
	return out, code, combined
}

func doctorDiscovery(t *testing.T, url, data string) string {
	t.Helper()
	file := filepath.Join(t.TempDir(), "discovery.json")
	b, _ := json.Marshal(discovery{URL: url, PID: os.Getpid(), DataDir: data})
	if err := os.WriteFile(file, b, 0600); err != nil {
		t.Fatal(err)
	}
	return file
}

func doctorReply(env map[string]any) map[string]any {
	return map[string]any{"protocol_version": clientProtocol, "command_id": env["command_id"], "method": "host.status", "status": "COMPLETED",
		"session_id": nil, "revision": nil, "error_code": nil, "error": nil, "result": map[string]any{
			"host_instance_id": "test-host", "core_build_id": "test-build", "protocol_versions": []string{clientProtocol}, "host_state": "READY",
			"client_id": env["client_id"], "authenticated_principal_ref": "private-principal", "config_revision": 0,
			"model_configurations": []any{}, "credentials": []any{}, "workspaces": []any{}, "supported_methods": []string{"host.status", "provider.probe"}, "operating_mode": "LOCAL_USER_HOST"}}
}

func TestW05DoctorDiscoveryAndDownCompatibility(t *testing.T) {
	exe := doctorBinary(t)
	missing := filepath.Join(t.TempDir(), "missing-"+doctorSentinel+".json")
	out, code, _ := doctorRun(t, exe, missing, "", doctorSentinel)
	if code != 3 || out["reason"] != "NOT_FOUND" {
		t.Fatalf("missing: %v", out)
	}
	invalid := filepath.Join(t.TempDir(), "invalid.json")
	os.WriteFile(invalid, []byte("{"+doctorSentinel), 0600)
	out, code, _ = doctorRun(t, exe, invalid, "", doctorSentinel)
	if code != 3 || out["reason"] != "INVALID_JSON" {
		t.Fatalf("invalid: %v", out)
	}
	var posts atomic.Int32
	for _, mode := range []string{"503", "malformed", "closed"} {
		t.Run(mode, func(t *testing.T) {
			s := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				if r.Method != "GET" {
					posts.Add(1)
				}
				if mode == "503" {
					w.WriteHeader(503)
				}
				w.Write([]byte("private-" + doctorSentinel))
			}))
			defer s.Close()
			if mode == "closed" {
				s.Close()
			}
			out, code, _ := doctorRun(t, exe, doctorDiscovery(t, s.URL, ""), "", doctorSentinel)
			if code != 1 || out["health"] != "DOWN" || out["status"] != "REJECTED" {
				t.Fatalf("down: %v", out)
			}
			if mode == "503" && out["http_code"] != float64(503) {
				t.Fatal(out)
			}
		})
	}
	if posts.Load() != 0 {
		t.Fatal("POST after failed health")
	}
}

func TestW05DoctorTypedHostStatus(t *testing.T) {
	exe := doctorBinary(t)
	cases := []string{"valid", "command", "method", "protocol", "client", "extra", "missing", "pending", "ack", "session", "401", "503", "plain401", "plain403", "plain503", "oversize", "timeout", "rejected", "badjson"}
	for _, mode := range cases {
		t.Run(mode, func(t *testing.T) {
			var gets, posts atomic.Int32
			s := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				if r.URL.Path == "/healthz" {
					gets.Add(1)
					w.Write([]byte(`{"state":"READY"}`))
					return
				}
				posts.Add(1)
				if r.URL.Path != "/v2/command" || r.Method != "POST" || r.Header.Get("Authorization") != "Bearer "+doctorSentinel {
					t.Error("unexpected request")
				}
				var env map[string]any
				json.NewDecoder(r.Body).Decode(&env)
				requestRaw, _ := json.Marshal(env)
				t.Logf("DOCTOR_REQUEST %s", requestRaw)
				if env["method"] != "host.status" || len(env["payload"].(map[string]any)) != 0 {
					t.Error("not host.status")
				}
				for _, k := range []string{"session_id", "project_id", "expected_revision", "writer_epoch"} {
					if env[k] != nil {
						t.Errorf("scope leaked: %s", k)
					}
				}
				reply := doctorReply(env)
				result := reply["result"].(map[string]any)
				switch mode {
				case "command":
					reply["command_id"] = "wrong"
				case "method":
					reply["method"] = "session.get"
				case "protocol":
					reply["protocol_version"] = "wrong"
				case "client":
					result["client_id"] = "wrong"
				case "extra":
					result["unexpected"] = "bad"
				case "missing":
					delete(result, "credentials")
				case "pending":
					reply["status"] = "IN_PROGRESS"
				case "ack":
					reply["status"] = "ACKNOWLEDGED"
				case "session":
					reply["session_id"] = "stale-session"
				case "401":
					w.WriteHeader(401)
				case "503":
					w.WriteHeader(503)
				case "plain401", "plain403", "plain503":
					status := map[string]int{"plain401": 401, "plain403": 403, "plain503": 503}[mode]
					w.WriteHeader(status)
					w.Write([]byte("private-" + doctorSentinel))
					return
				case "oversize":
					w.Write([]byte(strings.Repeat("x", (1<<20)+1)))
					return
				case "timeout":
					<-r.Context().Done()
					return
				case "rejected":
					reply["status"] = "REJECTED"
					reply["result"] = nil
					reply["error_code"] = "FORBIDDEN"
					reply["error"] = map[string]any{"code": "FORBIDDEN", "message": "private-" + doctorSentinel, "retryable": false, "recovery": "REAUTHENTICATE_OS_USER", "current_revision": nil, "current_writer_epoch": nil, "resource_request_id": nil, "retry_after_ms": nil, "correlation_id": "test-error"}
				case "badjson":
					w.Write([]byte("private-" + doctorSentinel))
					return
				}
				json.NewEncoder(w).Encode(reply)
			}))
			defer s.Close()
			config := filepath.Join(t.TempDir(), "config.json")
			saved := []byte(`{"project_id":"stale-project","session_id":"stale-session","workspace_ref":"old-workspace","writer_epoch":99}`)
			os.WriteFile(config, saved, 0600)
			out, code, _ := doctorRun(t, exe, doctorDiscovery(t, s.URL, ""), config, doctorSentinel)
			want := 1
			if mode == "valid" {
				want = 0
			}
			if mode == "401" || mode == "plain401" || mode == "plain403" || mode == "rejected" {
				want = 3
			}
			if code != want {
				t.Fatalf("want %d: %v", want, out)
			}
			if gets.Load() != 1 || posts.Load() != 1 {
				t.Fatal("incorrect request count")
			}
			after, _ := os.ReadFile(config)
			if !bytes.Equal(after, saved) {
				t.Fatal("config changed")
			}
			if mode == "valid" && (out["model_configurations_reporting"] != "NOT_REPORTED_BY_HOST" || out["provider_verification"] != "NOT_CHECKED") {
				t.Fatal(out)
			}
		})
	}
}

func TestW05DoctorSecretsAndNoProviderCalls(t *testing.T) {
	exe := doctorBinary(t)
	var targetCalls atomic.Int32
	target := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { targetCalls.Add(1) }))
	defer target.Close()
	for _, mode := range []string{"health-redirect", "command-redirect", "inventory", "remote", "userinfo", "query"} {
		t.Run(mode, func(t *testing.T) {
			s := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				if r.URL.Path == "/healthz" {
					if mode == "health-redirect" {
						http.Redirect(w, r, target.URL, 302)
					} else {
						w.Write([]byte(`{"state":"READY","secret":"` + doctorSentinel + `"}`))
					}
					return
				}
				if mode == "command-redirect" {
					http.Redirect(w, r, target.URL, 307)
					return
				}
				var env map[string]any
				json.NewDecoder(r.Body).Decode(&env)
				if env["method"] != "host.status" {
					t.Error("provider/mutating method")
				}
				reply := doctorReply(env)
				rr := reply["result"].(map[string]any)
				rr["model_configurations"] = []any{map[string]any{"model_config_ref": "private-model-ref", "config_revision": 1, "provider_id": "private-provider", "base_url": "https://user:password@provider.invalid/?token=private", "model_id": "private-model", "credential_ref": "private-credential", "verified_at": "2026-01-01T00:00:00Z"}}
				rr["credentials"] = []any{map[string]any{"credential_ref": "private-credential", "provider_id": "private-provider", "status": "AVAILABLE", "last_checked_at": nil}}
				json.NewEncoder(w).Encode(reply)
			}))
			defer s.Close()
			url := s.URL
			switch mode {
			case "remote":
				url = "https://provider.invalid"
			case "userinfo":
				url = "http://user:" + doctorSentinel + "@127.0.0.1"
			case "query":
				url = s.URL + "?token=" + doctorSentinel
			}
			out, code, raw := doctorRun(t, exe, doctorDiscovery(t, url, ""), "", doctorSentinel)
			want := 1
			if mode == "inventory" {
				want = 0
			}
			if mode == "remote" || mode == "userinfo" || mode == "query" {
				want = 2
			}
			if code != want {
				t.Fatalf("want%d: %v", want, out)
			}
			for _, secret := range []string{"private-credential", "private-provider", "private-model", "private-principal", "password", "provider.invalid"} {
				if strings.Contains(raw, secret) {
					t.Fatalf("unallowlisted value leaked: %s", secret)
				}
			}
			if out["provider_verification"] != "NOT_CHECKED" || out["provider_network_called"] != false || out["tool_qualification"] != "NOT_EVALUATED" {
				t.Fatal(out)
			}
		})
	}
	if targetCalls.Load() != 0 {
		t.Fatal("followed redirect")
	}
}

func TestW05DoctorCredentialBlockAndContextPreservation(t *testing.T) {
	exe := doctorBinary(t)
	var posts atomic.Int32
	s := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method == "POST" {
			posts.Add(1)
		}
		w.Write([]byte(`{"state":"READY"}`))
	}))
	defer s.Close()
	for _, expired := range []bool{false, true} {
		t.Run(map[bool]string{false: "absent", true: "expired"}[expired], func(t *testing.T) {
			data := t.TempDir()
			os.Mkdir(filepath.Join(data, "host"), 0700)
			session := filepath.Join(data, "host", "session.json")
			var before []byte
			if expired {
				before = []byte(`{"token":"` + doctorSentinel + `","expires_at":"2000-01-01T00:00:00Z"}`)
				os.WriteFile(session, before, 0600)
			}
			config := filepath.Join(data, "cli.json")
			cfg := []byte(`{"project_id":"p","workspace_ref":"w","session_id":"s","writer_epoch":9}`)
			os.WriteFile(config, cfg, 0600)
			out, code, _ := doctorRun(t, exe, doctorDiscovery(t, s.URL, data), config, "")
			if code != 3 || out["reason"] != "CREDENTIAL_ABSENT" {
				t.Fatal(out)
			}
			after, _ := os.ReadFile(session)
			if !bytes.Equal(before, after) {
				t.Fatal("session changed")
			}
			after, _ = os.ReadFile(config)
			if !bytes.Equal(cfg, after) {
				t.Fatal("config changed")
			}
		})
	}
	if posts.Load() != 0 {
		t.Fatal("credential-less POST")
	}
}

func TestW05DoctorLocalHostIntegration(t *testing.T) {
	t.Setenv("RESEARCHOS_WRITER_LEASE_TTL", "60s")
	exe := doctorBinary(t)
	data := t.TempDir()
	db, err := store.Open(filepath.Join(data, "doctor.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	if err = store.Bootstrap(context.Background(), db, "../../migrations/sqlite/0001_bootstrap.sql"); err != nil {
		t.Fatal(err)
	}
	service, err := domain.New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if err != nil {
		t.Fatal(err)
	}
	h, err := host.New(host.Config{DB: db, Dir: filepath.Join(data, "host"), ContractsDir: "../../spec/v2.0/contracts", MigrationFile: "../../migrations/sqlite/0002_domain.sql", SchemaDir: "../../internal/api/contracts"})
	if err != nil {
		t.Fatal(err)
	}
	boot, err := h.BootstrapOwner(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	before, err := os.ReadFile(h.SessionFile())
	if err != nil {
		t.Fatal(err)
	}
	s := httptest.NewServer(api.HandlerWithConfigurationHost(db, t.TempDir(), service, nil, h.InstanceID(), nil, nil, h))
	defer s.Close()
	out, code, raw := doctorRun(t, exe, doctorDiscovery(t, s.URL, data), filepath.Join(data, "absent-config.json"), "")
	if code != 0 || out["health"] != "UP" || out["credentials_reporting"] != "NOT_REPORTED_BY_HOST" || out["model_configurations_reporting"] != "NOT_REPORTED_BY_HOST" {
		t.Fatal(out)
	}
	if strings.Contains(raw, boot.Session.Token) {
		t.Fatal("real session disclosed")
	}
	after, _ := os.ReadFile(h.SessionFile())
	if !bytes.Equal(before, after) {
		t.Fatal("real credential renewed")
	}
	if _, err := os.Stat(filepath.Join(data, "absent-config.json")); !os.IsNotExist(err) {
		t.Fatal("config created")
	}
}
