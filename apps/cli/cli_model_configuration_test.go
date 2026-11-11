package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
	"testing"
	"time"

	"researchos.local/research-os/internal/canonical"
	"researchos.local/research-os/internal/domain"
)

const configurationCLISecret = "SYNTHETIC_CONFIGURE_BEARER_NEVER_PRINT"

func configurationCLIEvidence(t *testing.T) string {
	t.Helper()
	base := os.Getenv("RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR")
	if base == "" {
		return t.TempDir()
	}
	dir := filepath.Join(base, filepath.FromSlash(t.Name()))
	if e := os.MkdirAll(dir, 0700); e != nil {
		t.Fatal(e)
	}
	return dir
}
func configurationCLIWrite(t *testing.T, dir, name string, b []byte) {
	t.Helper()
	f, e := os.OpenFile(filepath.Join(dir, name), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if e != nil {
		t.Fatal(e)
	}
	if _, e = f.Write(b); e != nil {
		t.Fatal(e)
	}
	if e = f.Close(); e != nil {
		t.Fatal(e)
	}
}
func configurationCLIBinary(t *testing.T) string {
	t.Helper()
	dir := configurationCLIEvidence(t)
	exe := filepath.Join(dir, "configuration-cli.exe")
	goName := "go"
	if runtime.GOOS == "windows" {
		goName += ".exe"
	}
	cmd := exec.Command(filepath.Join(runtime.GOROOT(), "bin", goName), "build", "-o", exe, ".")
	start := time.Now().UTC()
	raw, e := cmd.CombinedOutput()
	configurationCLIWrite(t, dir, "build.raw", raw)
	exit := 0
	if e != nil {
		exit = 1
	}
	cwd, _ := os.Getwd()
	configurationCLIWrite(t, dir, "build.invocation.json", domain.Bytes(domain.Object{"actualargv": cmd.Args, "cwd": cwd, "started_at": start.Format(time.RFC3339Nano), "ended_at": domain.Now(), "exit": exit}))
	if e != nil {
		t.Fatalf("build: %v %s", e, raw)
	}
	return exe
}
func configurationCLIRun(t *testing.T, exe, disc, config, credential string, args ...string) (map[string]any, int) {
	t.Helper()
	dir := configurationCLIEvidence(t)
	id := domain.ID()
	before, readErr := os.ReadFile(config)
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	cmd := exec.CommandContext(ctx, exe, args...)
	cmd.Env = append(os.Environ(), "RESEARCHOS_CLI_DISCOVERY="+disc, "RESEARCHOS_CLI_CONFIG="+config, "RESEARCHOS_CLI_CREDENTIAL="+credential, "RESEARCHOS_CLI_CLIENT_ID=configuration-cli")
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	start := time.Now().UTC()
	e := cmd.Run()
	exit := 0
	if e != nil {
		ee, ok := e.(*exec.ExitError)
		if !ok {
			t.Fatal(e)
		}
		exit = ee.ExitCode()
	}
	if ctx.Err() != nil {
		t.Fatal(ctx.Err())
	}
	if strings.Contains(stdout.String()+stderr.String(), credential) && credential != "" {
		t.Fatal("credential material disclosed")
	}
	after, afterErr := os.ReadFile(config)
	binary, e := os.ReadFile(exe)
	if e != nil {
		t.Fatal(e)
	}
	cwd, _ := os.Getwd()
	configurationCLIWrite(t, dir, id+".stdout", stdout.Bytes())
	configurationCLIWrite(t, dir, id+".stderr", stderr.Bytes())
	configurationCLIWrite(t, dir, id+".invocation.json", domain.Bytes(domain.Object{"actualargv": cmd.Args, "cwd": cwd, "started_at": start.Format(time.RFC3339Nano), "ended_at": domain.Now(), "exit": exit, "binary_sha256": domain.Digest(binary), "before_exists": readErr == nil, "before_hash": domain.Digest(before), "after_exists": afterErr == nil, "after_hash": domain.Digest(after), "measurement_mode": "LOCAL_FIXTURE_NOT_LIVE", "external_calls": 0, "paid_calls": 0}))
	configurationCLIWrite(t, dir, id+".config.before", before)
	configurationCLIWrite(t, dir, id+".config.after", after)
	var out map[string]any
	lines := strings.Split(strings.TrimSpace(stdout.String()), "\n")
	if len(lines) == 1 {
		if json.Unmarshal([]byte(lines[0]), &out) != nil {
			t.Fatalf("invalid JSONL: %s", stdout.String())
		}
	}
	t.Logf("CONFIGURE_NATIVE argv=%q exit=%d binary_sha256=%s raw=%s", args, exit, domain.Digest(binary), filepath.Join(dir, id+".invocation.json"))
	return out, exit
}

type configurationCLIProbe struct {
	mu        sync.Mutex
	requests  []map[string]any
	raws      [][]byte
	mode      string
	revision  int
	redirects int
}

func (p *configurationCLIProbe) handler(w http.ResponseWriter, r *http.Request) {
	raw, _ := io.ReadAll(io.LimitReader(r.Body, (1<<20)+1))
	var env map[string]any
	strict, e := canonical.JSON(raw)
	if e != nil || json.Unmarshal(strict, &env) != nil {
		w.WriteHeader(400)
		return
	}
	p.mu.Lock()
	defer p.mu.Unlock()
	p.requests = append(p.requests, env)
	p.raws = append(p.raws, append([]byte{}, raw...))
	if r.Header.Get("Authorization") != "Bearer "+configurationCLISecret {
		w.WriteHeader(401)
		return
	}
	method, _ := env["method"].(string)
	if method == "session.create" {
		w.WriteHeader(403)
		return
	}
	reply := doctorReply(env)
	if method == "host.status" {
		reply["revision"] = 1 // Actual host read response; only default configure requires null.
		reply["result"].(map[string]any)["config_revision"] = p.revision
		if p.mode == "status-client" {
			reply["result"].(map[string]any)["client_id"] = "other-client"
		}
		if p.mode == "status-duplicate" {
			b, _ := json.Marshal(reply)
			w.Write(append([]byte(`{"status":"COMPLETED",`), b[1:]...))
			return
		}
		if p.mode == "status-near-integer" {
			b, _ := json.Marshal(reply)
			w.Write(bytes.Replace(b, []byte(`"config_revision":1`), []byte(`"config_revision":1.0000000000000001`), 1))
			return
		}
	} else {
		pl := env["payload"].(map[string]any)
		result := map[string]any{"model_config_ref": "mc-opaque-from-original-host", "config_revision": pl["config_revision"], "provider_id": pl["provider_id"], "model_id": pl["model_id"], "base_url": pl["base_url"], "credential_ref": pl["credential_ref"], "verified_at": nil}
		reply["method"] = method
		reply["session_id"] = env["session_id"]
		reply["result"] = result
		if env["session_id"] != nil {
			reply["revision"] = env["expected_revision"].(float64) + 1
		}
		switch p.mode {
		case "http401", "http403", "http503":
			code := 401
			if p.mode == "http403" {
				code = 403
			}
			if p.mode == "http503" {
				code = 503
			}
			w.WriteHeader(code)
			w.Write([]byte(configurationCLISecret))
			return
		case "redirect":
			w.Header().Set("Location", "/must-not-follow")
			w.WriteHeader(302)
			return
		case "timeout":
			<-r.Context().Done()
			return
		case "oversize":
			w.Write([]byte(strings.Repeat(" ", (1<<20)+1)))
			return
		case "malformed":
			w.Write([]byte(`{"status":`))
			return
		case "invalid-utf8":
			w.Write([]byte{'{', '"', 'x', '"', ':', '"', 255, '"', '}'})
			return
		case "two-json":
			b, _ := json.Marshal(reply)
			w.Write(append(b, []byte(`{}`)...))
			return
		case "duplicate":
			b, _ := json.Marshal(reply)
			w.Write(append([]byte(`{"\u0073tatus":"COMPLETED",`), b[1:]...))
			return
		case "nested-duplicate":
			b, _ := json.Marshal(reply)
			w.Write(bytes.Replace(b, []byte(`"model_id":`), []byte(`"model_id":"other","model_id":`), 1))
			return
		case "unknown":
			reply["extra"] = true
		case "missing":
			delete(reply, "error")
		case "ack":
			reply["status"] = "ACKNOWLEDGED"
			reply["result"] = map[string]any{"accepted_at": "2026-10-01T00:00:00Z", "operation_id": "pending-configure", "after_sequence": 0, "related_resource_ref": nil}
		case "in-progress":
			reply["status"] = "IN_PROGRESS"
		case "wrong-command":
			reply["command_id"] = "other-command"
		case "wrong-method":
			reply["method"] = "host.status"
		case "wrong-protocol":
			reply["protocol_version"] = "researchos-client/1"
		case "wrong-session":
			reply["session_id"] = "other-session"
		case "wrong-revision":
			reply["revision"] = 99
		case "wrong-model":
			result["model_id"] = "other"
		case "wrong-provider":
			result["provider_id"] = "other"
		case "wrong-endpoint":
			result["base_url"] = "https://other.invalid"
		case "wrong-credential":
			result["credential_ref"] = "other-ref"
		case "wrong-config-revision":
			result["config_revision"] = 99
		case "empty-ref":
			result["model_config_ref"] = ""
		case "secret-ref":
			result["model_config_ref"] = configurationCLISecret
		case "verified":
			result["verified_at"] = "2026-10-01T00:00:00Z"
		case "cross-result":
			reply["result"] = doctorReply(env)["result"]
		case "config-near-integer":
			b, _ := json.Marshal(reply)
			w.Write(bytes.Replace(b, []byte(`"config_revision":1`), []byte(`"config_revision":1.0000000000000001`), 1))
			return
		case "session-near-integer":
			b, _ := json.Marshal(reply)
			w.Write(bytes.Replace(b, []byte(`"revision":8`), []byte(`"revision":8.0000000000000001`), 1))
			return
		case "rejected":
			reply["status"] = "REJECTED"
			reply["result"] = nil
			reply["error_code"] = "SESSION_BUSY"
			reply["error"] = map[string]any{"code": "SESSION_BUSY", "message": configurationCLISecret, "retryable": false, "recovery": "WAIT_FOR_SETTLEMENT", "current_revision": nil, "current_writer_epoch": nil, "resource_request_id": nil, "retry_after_ms": nil, "correlation_id": env["command_id"]}
		}
	}
	json.NewEncoder(w).Encode(reply)
}

func TestCLIModelConfigurationNativeMatrix(t *testing.T) {
	exe := configurationCLIBinary(t)
	type row struct {
		name, mode                string
		scope, missing, malformed bool
		args                      []string
		code                      int
		reason                    string
		requests                  int
	}
	defaults := []string{"config", "set-model", "--model", "vendor/org/name", "--base-url", "https://provider.invalid/v1/", "--config-revision", "0"}
	cases := []row{
		{name: "C01-first-default", missing: true, requests: 2},
		{name: "C02-explicit-default-preserves-session", scope: true, args: []string{"--default"}, requests: 2},
		{name: "C03-project-residue", requests: 2},
		{name: "C03-partial-explicit", args: []string{"--project", "project-fixture"}, code: 2, reason: "INCOMPLETE_CONFIGURE_SCOPE"},
		{name: "C03-default-conflict", scope: true, args: []string{"--default", "--session", "session-fixture"}, code: 2, reason: "INCOMPLETE_CONFIGURE_SCOPE"},
		{name: "C04-missing-revision", mode: "missing-revision", code: 2, reason: "MISSING_CONFIG_REVISION"},
		{name: "C04-stale-local", mode: "stale-local", code: 1, reason: "STALE_CONFIG_REVISION"},
		{name: "C04-overflow", mode: "overflow", code: 2, reason: "INVALID_CONFIG_REVISION"},
		{name: "C05-stale-host", mode: "stale-host", code: 1, reason: "STALE_CONFIG_REVISION", requests: 1},
		{name: "C06-scoped-no-claim", scope: true, code: 1, reason: "SETTLED_FLAG_REQUIRED"},
		{name: "C07-scoped-no-record", scope: true, mode: "no-record", args: []string{"--settled"}, code: 1, reason: "SETTLED_RUN_UNRECORDED"},
		{name: "C08-scoped-no-epoch", scope: true, mode: "no-epoch", args: []string{"--settled"}, code: 2, reason: "MODEL_CHANGE_WITHOUT_EPOCH"},
		{name: "C09-scoped-completed", scope: true, args: []string{"--settled"}, requests: 2},
		{name: "C10-bare-model", mode: "bare-model", code: 2, reason: "MODEL_NOT_PROVIDER_QUALIFIED"},
		{name: "C11-null-credential", requests: 2},
		{name: "C11-empty-credential", args: []string{"--credential-ref="}, code: 2, reason: "INVALID_CREDENTIAL_REF"},
		{name: "C12-no-endpoint", mode: "no-endpoint", code: 2, reason: "MISSING_CONFIGURE_FIELDS"},
		{name: "C13-exact-echo", requests: 2},
		{name: "C19-future-session-consumes-ref", requests: 2},
		{name: "C23-material-argument", args: []string{"--api-key", configurationCLISecret}, code: 2, reason: "CREDENTIAL_MATERIAL_NOT_ALLOWED"},
		{name: "C23-secret-ref", mode: "secret-ref", code: 1, requests: 2},
		{name: "C15-status-near-integer", mode: "status-near-integer", code: 1, requests: 1},
		{name: "C15-config-near-integer", mode: "config-near-integer", code: 1, requests: 2},
		{name: "C15-session-near-integer", mode: "session-near-integer", scope: true, args: []string{"--settled"}, code: 1, requests: 2},
		{name: "C13-config-exact-upper-bound", mode: "config-upper-bound", requests: 2},
		{name: "C16-session-exact-max-plus-one", mode: "session-upper-bound", scope: true, args: []string{"--settled"}, requests: 2},
		{name: "C24-malformed-existing", malformed: true, code: 1, reason: "CONFIG_UNREADABLE"},
	}
	for _, mode := range []string{"ack", "in-progress"} {
		cases = append(cases, row{name: "C14-" + mode, mode: mode, code: 1, requests: 2})
	}
	for _, mode := range []string{"malformed", "invalid-utf8", "duplicate", "nested-duplicate", "two-json", "unknown", "missing", "oversize", "status-duplicate"} {
		n := 2
		if mode == "status-duplicate" {
			n = 1
		}
		cases = append(cases, row{name: "C15-" + mode, mode: mode, code: 1, requests: n})
	}
	for _, mode := range []string{"wrong-command", "wrong-method", "wrong-protocol", "wrong-session", "wrong-revision", "status-client"} {
		n := 2
		if mode == "status-client" {
			n = 1
		}
		cases = append(cases, row{name: "C16-" + mode, mode: mode, code: 1, requests: n})
	}
	for _, mode := range []string{"wrong-model", "wrong-provider", "wrong-endpoint", "wrong-credential", "wrong-config-revision", "empty-ref", "verified", "cross-result"} {
		cases = append(cases, row{name: "C17-" + mode, mode: mode, code: 1, requests: 2})
	}
	for _, mode := range []string{"http401", "http403", "http503", "redirect", "timeout", "rejected"} {
		code := 1
		if mode == "http401" || mode == "http403" || mode == "redirect" {
			code = 3
		}
		cases = append(cases, row{name: "C18-" + mode, mode: mode, code: code, requests: 2})
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			p := &configurationCLIProbe{mode: tc.mode}
			if tc.mode == "stale-host" {
				p.revision = 1
			}
			if tc.mode == "status-near-integer" {
				p.revision = 1
			}
			if tc.mode == "config-upper-bound" {
				p.revision = 9007199254740990
			}
			server := httptest.NewServer(http.HandlerFunc(p.handler))
			defer server.Close()
			disc := doctorDiscovery(t, server.URL, "")
			config := filepath.Join(t.TempDir(), "config.json")
			cfg := cliConfig{Model: "vendor/old", WorkspaceRef: "workspace-fixture", ProjectID: "project-fixture", ConfirmedRun: "run-claim"}
			if tc.scope {
				cfg.SessionID = "session-fixture"
				cfg.Revision = 7
				cfg.WriterEpoch = 2
			}
			if tc.mode == "no-record" {
				cfg.ConfirmedRun = ""
			}
			if tc.mode == "no-epoch" {
				cfg.WriterEpoch = 0
			}
			if tc.mode == "stale-local" {
				cfg.ConfigRevision = 1
			}
			if tc.mode == "status-near-integer" {
				cfg.ConfigRevision = 1
			}
			if tc.mode == "config-upper-bound" {
				cfg.ConfigRevision = 9007199254740990
			}
			if tc.mode == "session-upper-bound" {
				cfg.Revision = 9007199254740991
				cfg.WriterEpoch = 9007199254740991
			}
			if !tc.missing {
				raw, _ := json.Marshal(cfg)
				if tc.malformed {
					raw = []byte(`{"config_revision":`)
				}
				if e := os.WriteFile(config, raw, 0600); e != nil {
					t.Fatal(e)
				}
			} else {
				cfg = cliConfig{}
			}
			before, beforeErr := os.ReadFile(config)
			args := append([]string{}, defaults...)
			switch tc.mode {
			case "missing-revision":
				args = args[:len(args)-2]
			case "overflow":
				args[len(args)-1] = "9007199254740992"
			case "bare-model":
				args[3] = "bare"
			case "no-endpoint":
				args = append(args[:4], args[6:]...)
			case "status-near-integer":
				args[len(args)-1] = "1"
			case "config-upper-bound":
				args[len(args)-1] = "9007199254740990"
			}
			args = append(args, tc.args...)
			out, code := configurationCLIRun(t, exe, disc, config, configurationCLISecret, args...)
			if code != tc.code || tc.reason != "" && out["reason"] != tc.reason {
				t.Fatalf("exit/reason: code=%d out=%v expected=%d/%s", code, out, tc.code, tc.reason)
			}
			p.mu.Lock()
			requests := append([]map[string]any{}, p.requests...)
			raws := append([][]byte{}, p.raws...)
			p.mu.Unlock()
			dir := configurationCLIEvidence(t)
			for i, raw := range raws {
				configurationCLIWrite(t, dir, fmt.Sprintf("wire-%02d.json", i), raw)
			}
			if len(requests) != tc.requests {
				t.Fatalf("requests=%d want=%d", len(requests), tc.requests)
			}
			if len(requests) > 0 {
				s := requests[0]
				if s["method"] != "host.status" || s["project_id"] != nil || s["session_id"] != nil || s["expected_revision"] != nil || s["writer_epoch"] != nil {
					t.Fatal("status carried scope", s)
				}
			}
			after, afterErr := os.ReadFile(config)
			if code != 0 {
				if !bytes.Equal(before, after) || os.IsNotExist(beforeErr) != os.IsNotExist(afterErr) {
					t.Fatal("refusal changed local bytes")
				}
				return
			}
			var saved cliConfig
			if json.Unmarshal(after, &saved) != nil || saved.Model != "mc-opaque-from-original-host" || saved.ConfigRevision != cfg.ConfigRevision+1 {
				t.Fatal("opaque config not saved")
			}
			configure := requests[1]
			pl := configure["payload"].(map[string]any)
			if configure["command_id"] == requests[0]["command_id"] || pl["model_id"] != "org/name" || pl["provider_id"] != "vendor" || pl["config_revision"] != float64(cfg.ConfigRevision+1) || pl["credential_ref"] != nil {
				t.Fatal("wrong typed request", configure)
			}
			scoped := tc.scope && !flagBool(tc.args, "default")
			if scoped {
				if configure["session_id"] != cfg.SessionID || configure["project_id"] != cfg.ProjectID || configure["expected_revision"] != float64(cfg.Revision) || configure["writer_epoch"] != float64(cfg.WriterEpoch) || saved.Revision != cfg.Revision+1 {
					t.Fatal("scoped CAS changed")
				}
			} else {
				for _, key := range []string{"project_id", "session_id", "expected_revision", "writer_epoch"} {
					if configure[key] != nil {
						t.Fatal("default scope", configure)
					}
				}
				if saved.SessionID != cfg.SessionID || saved.Revision != cfg.Revision || saved.WriterEpoch != cfg.WriterEpoch || saved.WorkspaceRef != cfg.WorkspaceRef {
					t.Fatal("default changed existing context")
				}
			}
			if tc.name == "C19-future-session-consumes-ref" {
				_, code = configurationCLIRun(t, exe, disc, config, configurationCLISecret, "run", "Do not execute fixture")
				if code == 0 {
					t.Fatal("fixture resource refusal ignored")
				}
				p.mu.Lock()
				last := p.requests[len(p.requests)-1]
				p.mu.Unlock()
				if last["method"] != "session.create" || last["payload"].(map[string]any)["model_config_ref"] != saved.Model {
					t.Fatal("future Session did not consume exact ref", last)
				}
			}
		})
	}
}
