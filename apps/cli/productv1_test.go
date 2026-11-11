package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"sync/atomic"
	"testing"

	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/host"
)

const s04Credential = "SYNTHETIC_HOST_CREDENTIAL_DO_NOT_PRINT"

type s04RoundTrip func(*http.Request) (*http.Response, error)

func (f s04RoundTrip) RoundTrip(r *http.Request) (*http.Response, error) { return f(r) }
func s04Envelope(data any) domain.Object {
	return domain.Object{"api_version": "harness.v1", "data": data}
}
func s04Ref() domain.Object { return domain.Object{"project_id": "project-a", "task_id": "task-a"} }
func s04Error(code string) domain.Object {
	return domain.Object{"code": code, "message": "fixture error", "retryable": false, "task_ref": nil, "current_task_revision": nil, "current_run": nil}
}
func s04Task(status string, run any) domain.Object {
	terminal := status == "COMPLETED" || status == "FAILED" || status == "CANCELLED" || status == "BLOCKED" || status == "UNKNOWN"
	return domain.Object{"task_ref": s04Ref(), "request_id": "request-a", "harness_id": "codex", "workspace_ref": "opaque-workspace-a", "prompt": "finite task", "scope": "workspace-read", "ephemeral": true, "status": status, "terminal": terminal, "task_revision": "9007199254740993", "run": run, "created_at": "2026-11-04T00:00:00Z", "updated_at": "2026-11-04T00:00:00Z", "result": nil, "failure": nil}
}
func s04Caps() domain.Object {
	flags := domain.Object{}
	for _, k := range []string{"readonly_turn", "event_stream", "cancel", "task_history", "request_lookup"} {
		flags[k] = true
	}
	for _, k := range []string{"token_delta", "write", "resume", "pause", "per_tool_approval", "file_diff", "file_list", "file_artifacts", "attachments"} {
		flags[k] = false
	}
	return domain.Object{"harness_id": "codex", "display_name": "Codex CLI", "backend": "codex-cli-readonly-v1", "installation": domain.Object{"present": false, "version": nil, "executable_sha256": nil, "checked_at": nil}, "authentication": domain.Object{"state": "UNPROBED", "kind": nil, "checked_at": nil}, "verification": domain.Object{"execution": "UNVERIFIED", "workspace_read_scope": "UNVERIFIED", "cancellation": "UNVERIFIED", "checked_at": nil}, "capabilities": flags, "security_scope": domain.Object{"mode": "workspace-read", "profile_id": "fixed-readonly", "config_source": "HOST_FIXED", "hooks": "PLATFORM_POLICY", "mcp": "PLATFORM_POLICY", "native_auth": "CLI_OWNED", "enforcement_verified": false}, "can_submit": false, "reason_codes": []any{"NOT_INSTALLED"}}
}
func s04Ack() domain.Object {
	return s04Envelope(domain.Object{"task_ref": s04Ref(), "request_id": "request-a", "task_revision": "9007199254740993", "status": "QUEUED", "run": nil})
}
func s04List(found bool) domain.Object {
	items := []any{}
	state := "NOT_FOUND"
	cursor := "0"
	if found {
		items = append(items, s04Task("QUEUED", nil))
		state = "FOUND"
		cursor = "17"
	}
	return s04Envelope(domain.Object{"items": items, "next_cursor": cursor, "has_more": false, "lookup": domain.Object{"request_id": "request-a", "state": state}})
}
func s04HTTP(status int, value any) *http.Response {
	raw, _ := json.Marshal(value)
	return &http.Response{StatusCode: status, Header: make(http.Header), Body: io.NopCloser(bytes.NewReader(raw))}
}
func s04Deps(tr http.RoundTripper, calls *int) cliHarnessDependencies {
	return cliHarnessDependencies{transport: tr, connect: func(context.Context) (*cliHarnessHost, error) {
		*calls++
		return &cliHarnessHost{url: "http://127.0.0.1:42345", id: "host-012345abcdef", credential: s04Credential, verify: func() error { return nil }}, nil
	}}
}
func s04Run(t *testing.T, args []string, input string, deps cliHarnessDependencies) (int, domain.Object, string) {
	t.Helper()
	var output, diagnostic bytes.Buffer
	code := runCLIHarness(context.Background(), args, strings.NewReader(input), &output, &diagnostic, deps)
	if bytes.Count(output.Bytes(), []byte("\n")) != 1 {
		t.Fatal("stdout is not one complete JSONL record", output.String())
	}
	reply, err := domain.Decode(output.Bytes())
	if err != nil {
		t.Fatal(err)
	}
	if strings.Contains(output.String()+diagnostic.String(), s04Credential) {
		t.Fatal("credential escaped output")
	}
	return code, reply, output.String()
}
func s04SubmitArgs() []string {
	return []string{"task", "submit", "--project", "project-a", "--workspace-ref", "opaque-workspace-a", "--request-id", "request-a", "--prompt-stdin"}
}

func TestS04InvalidInputBeforeHost(t *testing.T) {
	base := s04SubmitArgs()
	cases := map[string][]string{
		"unregistered shortcut": append([]string{}, base[1:]...),
		"wrong task namespace":  {"task", "caps"},
		"missing request":       append([]string{}, base[:6]...),
		"duplicate":             append(append([]string{}, base...), "--request-id", "other"),
		"url":                   append(append([]string{}, base...), "--url", "https://external.invalid"),
		"exe":                   append(append([]string{}, base...), "--exe", "other.exe"),
		"token":                 append(append([]string{}, base...), "--token", "do-not-use"),
		"legacy model":          append(append([]string{}, base...), "--model", "provider-model"),
		"noncanonical cursor":   {"task", "events", "--project", "p", "--task", "t", "--cursor", "01"},
		"overflow cursor":       {"task", "events", "--project", "p", "--task", "t", "--cursor", "9223372036854775808"},
		"cancel missing CAS":    {"task", "cancel", "--project", "p", "--task", "t", "--request-id", "cancel-a"},
		"cancel half fence":     {"task", "cancel", "--project", "p", "--task", "t", "--request-id", "cancel-a", "--expected-task-revision", "1", "--expected-run-id", "run-a"},
	}
	for name, args := range cases {
		t.Run(name, func(t *testing.T) {
			calls := 0
			code, _, _ := s04Run(t, args, "finite task", s04Deps(nil, &calls))
			if code != exitUsage || calls != 0 {
				t.Fatal("invalid option reached Host", code, calls)
			}
		})
	}
	for name, input := range map[string]string{"blank": " \n", "invalid utf8": string([]byte{0xff}), "oversize": strings.Repeat("x", 65537), "NUL": "finite\x00task"} {
		t.Run(name, func(t *testing.T) {
			calls := 0
			code, _, _ := s04Run(t, base, input, s04Deps(nil, &calls))
			if code != exitUsage || calls != 0 {
				t.Fatal("invalid stdin reached Host", code, calls)
			}
		})
	}
	calls := 0
	code, reply, _ := s04Run(t, []string{"help"}, "", s04Deps(nil, &calls))
	if code != 0 || calls != 0 || reply["status"] != "COMPLETED" {
		t.Fatal("help touched Host")
	}
}

func TestS04ExactRequestShapes(t *testing.T) {
	for _, op := range []string{"caps", "submit", "list", "get", "events", "cancel-queued", "cancel-active"} {
		t.Run(op, func(t *testing.T) {
			args := []string{"caps"}
			var expectedMethod, expectedPath string
			var response any
			status := 200
			run := domain.Object{"run_id": "run-a", "epoch": "9007199254740993"}
			switch op {
			case "caps":
				expectedMethod, expectedPath = "GET", "/harness/v1/capabilities"
				response = s04Envelope(s04Caps())
			case "submit":
				args = s04SubmitArgs()
				expectedMethod, expectedPath = "POST", "/harness/v1/tasks"
				response = s04Ack()
				status = 202
			case "list":
				args = []string{"task", "list", "--project", "project-a", "--request-id", "request-a"}
				expectedMethod, expectedPath = "GET", "/harness/v1/tasks"
				response = s04List(true)
			case "get":
				args = []string{"task", "get", "--project", "project-a", "--task", "task-a"}
				expectedMethod, expectedPath = "GET", "/harness/v1/tasks/task-a"
				response = s04Envelope(s04Task("RUNNING", run))
			case "events":
				args = []string{"task", "events", "--project", "project-a", "--task", "task-a", "--cursor", "9007199254740993"}
				expectedMethod, expectedPath = "GET", "/harness/v1/tasks/task-a/events"
				response = s04Envelope(domain.Object{"task_ref": s04Ref(), "events": []any{}, "next_cursor": "9007199254740993", "has_more": false, "end": false, "reset": false, "snapshot": nil})
			case "cancel-queued":
				args = []string{"task", "cancel", "--project", "project-a", "--task", "task-a", "--request-id", "cancel-a", "--expected-task-revision", "9007199254740993", "--expect-no-run"}
				expectedMethod, expectedPath = "POST", "/harness/v1/tasks/task-a/cancel"
				response = s04Envelope(domain.Object{"task": s04Task("CANCELLED", nil), "disposition": "CANCELLED_BEFORE_LAUNCH"})
			case "cancel-active":
				args = []string{"task", "cancel", "--project", "project-a", "--task", "task-a", "--request-id", "cancel-a", "--expected-task-revision", "9007199254740993", "--expected-run-id", "run-a", "--expected-epoch", "9007199254740993"}
				expectedMethod, expectedPath = "POST", "/harness/v1/tasks/task-a/cancel"
				response = s04Envelope(domain.Object{"task": s04Task("CANCEL_REQUESTED", run), "disposition": "CANCEL_REQUESTED"})
			}
			requests, connects := 0, 0
			tr := s04RoundTrip(func(r *http.Request) (*http.Response, error) {
				requests++
				if r.Method != expectedMethod || r.URL.Path != expectedPath || r.Header.Get("Authorization") != "Bearer "+s04Credential || r.Header.Get("Idempotency-Key") != "" || r.GetBody != nil {
					t.Fatal("wrong request authority/shape", r.Method, r.URL.Path)
				}
				if op != "caps" && op != "submit" && r.URL.Query().Get("project_id") != "project-a" {
					t.Fatal("project query absent")
				}
				if op == "submit" {
					raw, _ := io.ReadAll(r.Body)
					body, err := domain.Decode(raw)
					if err != nil || len(body) != 6 || body["request_id"] != "request-a" || body["workspace_ref"] != "opaque-workspace-a" || body["prompt"] != "finite task" || body["scope"] != "workspace-read" || body["harness_id"] != "codex" {
						t.Fatal("submit differs", string(raw))
					}
				}
				if strings.HasPrefix(op, "cancel") {
					raw, _ := io.ReadAll(r.Body)
					body, err := domain.Decode(raw)
					if err != nil || len(body) != 4 || body["expected_task_revision"] != "9007199254740993" {
						t.Fatal("cancel precision changed", string(raw))
					}
					if op == "cancel-queued" && (body["expected_run_id"] != nil || body["expected_epoch"] != nil) {
						t.Fatal("queued fence changed")
					}
					if op == "cancel-active" && body["expected_epoch"] != "9007199254740993" {
						t.Fatal("epoch rounded")
					}
				}
				return s04HTTP(status, response), nil
			})
			code, reply, _ := s04Run(t, args, "finite task", s04Deps(tr, &connects))
			if code != 0 || requests != 1 || connects != 1 {
				t.Fatal("request failed", code, requests, reply)
			}
			if expectedMethod == "POST" && (reply["status"] != "ACKNOWLEDGED" || reply["completion_scope"] != "HOST_MUTATION_ACK") {
				t.Fatal("ACK was mislabeled execution completion", reply)
			}
		})
	}
}

func TestS04LostSubmitAckNeverReposts(t *testing.T) {
	for _, mode := range []string{"FOUND", "NOT_FOUND", "MISMATCH"} {
		t.Run(mode, func(t *testing.T) {
			var posts, gets atomic.Int64
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				if r.Header.Get("Authorization") != "Bearer "+s04Credential {
					t.Error("wrong bearer")
				}
				if r.Method == "POST" {
					posts.Add(1)
					io.Copy(io.Discard, r.Body)
					conn, _, err := w.(http.Hijacker).Hijack()
					if err != nil {
						t.Error(err)
						return
					}
					conn.Close()
					return
				}
				gets.Add(1)
				if r.URL.Path != "/harness/v1/tasks" || r.URL.Query().Get("request_id") != "request-a" || r.URL.Query().Get("project_id") != "project-a" {
					t.Error("not exact original lookup")
				}
				reply := s04List(mode != "NOT_FOUND")
				if mode == "MISMATCH" {
					reply["data"].(map[string]any)["items"].([]any)[0].(map[string]any)["workspace_ref"] = "foreign-workspace"
				}
				json.NewEncoder(w).Encode(reply)
			}))
			defer server.Close()
			deps := cliHarnessDependencies{connect: func(context.Context) (*cliHarnessHost, error) {
				return &cliHarnessHost{url: server.URL, credential: s04Credential, verify: func() error { return nil }}, nil
			}}
			code, reply, _ := s04Run(t, s04SubmitArgs(), "finite task", deps)
			if posts.Load() != 1 || gets.Load() != 1 {
				t.Fatal("mutation was replayed", posts.Load(), gets.Load())
			}
			if mode == "FOUND" {
				if code != 0 || reply["status"] != "ACKNOWLEDGED" || reply["completion_scope"] != "SUBMIT_REQUEST_LOOKUP" {
					t.Fatal("exact lookup not adopted", reply)
				}
			} else if code != 1 || reply["status"] != "UNKNOWN" {
				t.Fatal("missing/conflicting lookup made false success", reply)
			}
		})
	}
}

func TestS04CancelUnknownAndConflictNeverRefences(t *testing.T) {
	args := []string{"task", "cancel", "--project", "project-a", "--task", "task-a", "--request-id", "cancel-a", "--expected-task-revision", "1", "--expected-run-id", "run-a", "--expected-epoch", "9007199254740993"}
	for _, mode := range []string{"lost", "conflict"} {
		t.Run(mode, func(t *testing.T) {
			calls, connects := 0, 0
			tr := s04RoundTrip(func(r *http.Request) (*http.Response, error) {
				calls++
				if calls == 1 {
					if r.Method != "POST" {
						t.Fatal("cancel not POST")
					}
					if mode == "lost" {
						return nil, io.ErrUnexpectedEOF
					}
					e := s04Error("STATE_CONFLICT")
					e["task_ref"] = s04Ref()
					e["current_task_revision"] = "2"
					e["current_run"] = domain.Object{"run_id": "new-run", "epoch": "9007199254740994"}
					e["message"] = "Bearer " + s04Credential
					return s04HTTP(409, domain.Object{"api_version": "harness.v1", "error": e}), nil
				}
				if r.Method != "GET" || r.URL.Path != "/harness/v1/tasks/task-a" || r.URL.Query().Get("request_id") != "" {
					t.Fatal("cancel ACK used submit lookup or reposted")
				}
				return s04HTTP(200, s04Envelope(s04Task("CANCEL_REQUESTED", domain.Object{"run_id": "run-a", "epoch": "9007199254740993"}))), nil
			})
			code, reply, _ := s04Run(t, args, "", s04Deps(tr, &connects))
			if mode == "lost" {
				if calls != 2 || code != 1 || reply["status"] != "UNKNOWN" {
					t.Fatal("cancel outcome invented", calls, reply)
				}
			} else if calls != 1 || code != exitNotImplemented || reply["status"] != "REJECTED" {
				t.Fatal("conflict was silently refenced", calls, reply)
			}
		})
	}
}

func TestS04NativeBindingIgnoresEnvironmentCredential(t *testing.T) {
	t.Setenv("RESEARCHOS_CLI_CREDENTIAL", "ENV_OVERRIDE_MUST_NOT_BE_USED")
	for _, mode := range []string{"current", "renew", "foreign-host", "foreign-client", "exposed", "changed-discovery"} {
		t.Run(mode, func(t *testing.T) {
			d := discovery{URL: "http://127.0.0.1:42345", PID: 123, DataDir: filepath.Join(t.TempDir(), "fixture-data")}
			native, reads, resolves := 0, 0, 0
			boundary := cliHarnessBoundary{
				resolve: func() (resolvedCLIHost, error) {
					resolves++
					v := d
					if mode == "changed-discovery" && resolves > 1 {
						v.PID++
					}
					return resolvedCLIHost{discovery: v, hostID: "host-012345abcdef"}, nil
				},
				identity: func(discovery) (string, error) { return "host-012345abcdef", nil },
				credential: func(discovery) (string, error) {
					reads++
					if mode != "current" && reads == 1 {
						return "", errors.New("fresh synthetic expiry")
					}
					return s04Credential, nil
				},
				native: func(_ discovery, client, kind string, payload map[string]any) (json.RawMessage, error) {
					native++
					if kind != host.KindUserBootstrapRequest || len(payload) != 0 {
						t.Fatal("wrong native renewal")
					}
					v := domain.Object{"authenticated_principal_ref": "fixture-owner", "client_id": client, "host_instance_id": "host-012345abcdef", "protocol_version": clientProtocol, "credential_exposed_to_renderer": false}
					if mode == "foreign-host" {
						v["host_instance_id"] = "host-aaaaaaaaaaaa"
					}
					if mode == "foreign-client" {
						v["client_id"] = "foreign"
					}
					if mode == "exposed" {
						v["credential_exposed_to_renderer"] = true
					}
					raw, _ := json.Marshal(v)
					return raw, nil
				},
			}
			h, err := connectCLIHarnessHost(context.Background(), boundary)
			if mode == "current" || mode == "renew" {
				if err != nil || h.credential != s04Credential {
					t.Fatal("real handoff not used", err)
				}
				if mode == "current" && native != 0 || mode == "renew" && native != 1 {
					t.Fatal("unexpected bootstrap count", native)
				}
			} else if err == nil {
				t.Fatal("foreign binding accepted")
			}
		})
	}
}

func TestS04WireClosurePrecisionAndEvents(t *testing.T) {
	cmd := cliHarnessCommand{operation: "get", project: "project-a", task: "task-a"}
	for _, mode := range []string{"valid", "numeric-epoch", "overflow-epoch", "wrong-project", "terminal-mismatch", "extra-field", "UTF8-byte-limit"} {
		t.Run(mode, func(t *testing.T) {
			task := s04Task("RUNNING", domain.Object{"run_id": "run-a", "epoch": "9007199254740993"})
			switch mode {
			case "numeric-epoch":
				task["run"].(map[string]any)["epoch"] = json.Number("9007199254740993")
			case "overflow-epoch":
				task["run"].(map[string]any)["epoch"] = "9223372036854775808"
			case "wrong-project":
				task["task_ref"].(map[string]any)["project_id"] = "other"
			case "terminal-mismatch":
				task["terminal"] = true
			case "extra-field":
				task["exe"] = "forbidden.exe"
			case "UTF8-byte-limit":
				task["result"] = domain.Object{"assistant_text": strings.Repeat("界", 400000), "cli_thread_id": nil}
			}
			err := validateCLIHarnessReply("TaskResponse", s04Envelope(task), cmd)
			if (err == nil) != (mode == "valid") {
				t.Fatal("wire validation drift", mode, err)
			}
		})
	}
	event := func(sequence string) domain.Object {
		return domain.Object{"event_id": "event-a", "task_ref": s04Ref(), "run": nil, "sequence": sequence, "timestamp": "2026-11-04T00:00:00Z", "kind": "TASK_QUEUED", "payload": domain.Object{"status": "QUEUED", "text": nil, "tool": nil, "task": s04Task("QUEUED", nil), "error": nil}}
	}
	cmd = cliHarnessCommand{operation: "events", project: "project-a", task: "task-a", cursor: "9007199254740993", limit: 100}
	for _, mode := range []string{"valid", "duplicate", "regression", "numeric-sequence", "foreign-event", "bad-end", "missing-nullable", "valid-reset", "bad-reset"} {
		t.Run(mode, func(t *testing.T) {
			e := event("9007199254740994")
			data := domain.Object{"task_ref": s04Ref(), "events": []any{e}, "next_cursor": "9007199254740994", "has_more": false, "end": false, "reset": false, "snapshot": nil}
			switch mode {
			case "duplicate":
				data["events"] = []any{e, e}
			case "regression":
				e["sequence"] = "9007199254740993"
			case "numeric-sequence":
				e["sequence"] = json.Number("9007199254740994")
			case "foreign-event":
				e["task_ref"] = domain.Object{"project_id": "other", "task_id": "task-a"}
			case "bad-end":
				data["end"], data["has_more"] = true, true
			case "missing-nullable":
				delete(e["payload"].(map[string]any), "error")
			case "valid-reset", "bad-reset":
				data["events"] = []any{}
				data["next_cursor"] = "0"
				data["reset"] = true
				data["snapshot"] = s04Task("QUEUED", nil)
				if mode == "bad-reset" {
					data["snapshot"] = nil
				}
			}
			err := validateCLIHarnessReply("EventsResponse", s04Envelope(data), cmd)
			if (err == nil) != (mode == "valid" || mode == "valid-reset") {
				t.Fatal("event validation drift", mode, err)
			}
		})
	}
}

func TestS04RedirectDuplicateJSONAndCredentialIsolation(t *testing.T) {
	receives := 0
	target := httptest.NewServer(http.HandlerFunc(func(http.ResponseWriter, *http.Request) { receives++ }))
	defer target.Close()
	origin := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.Redirect(w, r, target.URL, http.StatusTemporaryRedirect)
	}))
	defer origin.Close()
	deps := cliHarnessDependencies{connect: func(context.Context) (*cliHarnessHost, error) {
		return &cliHarnessHost{url: origin.URL, credential: s04Credential, verify: func() error { return nil }}, nil
	}}
	code, _, _ := s04Run(t, []string{"caps"}, "", deps)
	if code == 0 || receives != 0 {
		t.Fatal("redirect received authority")
	}
	calls, connects := 0, 0
	tr := s04RoundTrip(func(*http.Request) (*http.Response, error) {
		calls++
		return &http.Response{StatusCode: 202, Header: make(http.Header), Body: io.NopCloser(strings.NewReader(`{"api_version":"harness.v1","api_version":"harness.v1","data":{}}`))}, nil
	})
	code, reply, _ := s04Run(t, s04SubmitArgs(), "finite task", s04Deps(tr, &connects))
	if code != 1 || reply["status"] != "UNKNOWN" || calls != 2 {
		t.Fatal("malformed ACK caused success/replay", reply, calls)
	}
	// Quoted credentials must be removed before JSON encoding, not by a raw-byte
	// replacement that misses escaped data. This is only a synthetic handoff.
	hCredential := "quoted-\"synthetic\\credential"
	data := cliHarnessSafeOutput(domain.Object{"message": hCredential}, hCredential).(map[string]any)
	if data["message"] != "[REDACTED]" {
		t.Fatal("escaped credential was not isolated")
	}
}

func TestS04ContractPinAndLegacyEntry(t *testing.T) {
	if domain.Digest([]byte(cliHarnessContract)) != "sha256:046a49b2b1f82593fe86924913b2ee4d77152ac1cef7dbbb86562f6dfe0cfa1c" {
		t.Fatal("inline contract differs from frozen rev2")
	}
	source, err := os.ReadFile("main.go")
	if err != nil {
		t.Fatal(err)
	}
	for _, fragment := range []string{`case "harness":`, `cliHarness(args[1:])`, `case "task":`, `taskDispatch(args[1:])`, `cliInteractive(args)`, `cliHelpSurface(true)`} {
		if !bytes.Contains(source, []byte(fragment)) {
			t.Fatal("entry removed expected path", fragment)
		}
	}
	if schemas, err := cliHarnessSchemas(); err != nil || len(schemas) != 22 {
		t.Fatal("all actual wire definitions were not compiled", err, len(schemas))
	}
}

func TestS04InterruptionNeverBecomesCancellationOrReplay(t *testing.T) {
	for _, mode := range []string{"before-stdin", "during-stdin", "during-auth", "after-post"} {
		t.Run(mode, func(t *testing.T) {
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			var input io.Reader = strings.NewReader("finite task")
			calls, connects := 0, 0
			deps := s04Deps(s04RoundTrip(func(r *http.Request) (*http.Response, error) {
				calls++
				if r.Method != "POST" {
					t.Fatal("cancelled mutation retried as another operation")
				}
				cancel()
				return nil, context.Canceled
			}), &connects)
			if mode == "before-stdin" {
				cancel()
			}
			if mode == "during-stdin" {
				reader, writer := io.Pipe()
				defer reader.Close()
				defer writer.Close()
				input = reader
				go func() { cancel() }()
			}
			if mode == "during-auth" {
				deps.connect = func(context.Context) (*cliHarnessHost, error) { connects++; cancel(); return nil, context.Canceled }
			}
			var output, diagnostic bytes.Buffer
			code := runCLIHarness(ctx, s04SubmitArgs(), input, &output, &diagnostic, deps)
			reply, err := domain.Decode(output.Bytes())
			if err != nil {
				t.Fatal(err)
			}
			if mode == "after-post" {
				if code != exitFailed || calls != 1 || reply["status"] != "UNKNOWN" {
					t.Fatal("sent mutation interruption invented completion/cancel", code, calls, reply)
				}
			} else if code != exitInterrupted || calls != 0 {
				t.Fatal("pre-request interruption sent authority", code, calls)
			}
		})
	}
}

func TestS04InvalidVerbDoesNotEchoSensitiveArguments(t *testing.T) {
	calls := 0
	code, reply, raw := s04Run(t, []string{"--token=SENSITIVE_ARGUMENT_MUST_NOT_ECHO"}, "", s04Deps(nil, &calls))
	if code != exitUsage || calls != 0 || reply["command"] != "harness" || strings.Contains(raw, "SENSITIVE_ARGUMENT_MUST_NOT_ECHO") {
		t.Fatal("invalid verb echoed raw input", code, calls)
	}
}

func TestS04RunStartedNullableSnapshot(t *testing.T) {
	for _, mode := range []string{"null", "matching", "wrong-task", "wrong-status", "wrong-run", "omitted"} {
		t.Run(mode, func(t *testing.T) {
			run := domain.Object{"run_id": "run-a", "epoch": "9007199254740993"}
			payload := domain.Object{"status": "STARTING", "text": nil, "tool": nil, "task": nil, "error": nil}
			if mode != "null" && mode != "omitted" {
				task := s04Task("STARTING", run)
				switch mode {
				case "wrong-task":
					task["task_ref"] = domain.Object{"project_id": "project-a", "task_id": "other-task"}
				case "wrong-status":
					task["status"] = "RUNNING"
				case "wrong-run":
					task["run"] = domain.Object{"run_id": "other-run", "epoch": "9007199254740993"}
				}
				payload["task"] = task
			}
			if mode == "omitted" {
				delete(payload, "task")
			}
			event := domain.Object{"event_id": "event-started", "task_ref": s04Ref(), "run": run, "sequence": "9007199254740994", "timestamp": "2026-11-04T00:00:00Z", "kind": "RUN_STARTED", "payload": payload}
			envelope := s04Envelope(domain.Object{"task_ref": s04Ref(), "events": []any{event}, "next_cursor": "9007199254740994", "has_more": false, "end": false, "reset": false, "snapshot": nil})
			schemas, err := cliHarnessSchemas()
			if err != nil {
				t.Fatal(err)
			}
			schemaErr := schemas["EventsResponse"].Validate(envelope)
			if (schemaErr == nil) != (mode != "omitted") {
				t.Fatal("fixture does not match frozen nullable schema", mode, schemaErr)
			}
			requests, connects := 0, 0
			tr := s04RoundTrip(func(r *http.Request) (*http.Response, error) {
				requests++
				if r.Method != "GET" {
					t.Fatal("event read mutated Host")
				}
				return s04HTTP(200, envelope), nil
			})
			code, reply, _ := s04Run(t, []string{"task", "events", "--project", "project-a", "--task", "task-a", "--cursor", "9007199254740993"}, "", s04Deps(tr, &connects))
			valid := mode == "null" || mode == "matching"
			if (code == exitCompleted) != valid || requests != 1 {
				t.Fatal("nullable snapshot or present-snapshot identity drift", mode, code, requests, reply)
			}
		})
	}
}
