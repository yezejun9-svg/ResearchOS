//go:build windows

package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	localworkspace "researchos.local/research-os/adapters/local_workspace"
	"researchos.local/research-os/internal/api"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/host"
	"researchos.local/research-os/internal/store"
	"runtime"
	"strings"
	"sync"
	"testing"
	"time"
)

func TestCLIModelStreamCausalDurableJSONL(t *testing.T)   { testCLIModelStream(t, "complete") }
func TestCLIModelStreamInterruptedPrefix(t *testing.T)    { testCLIModelStream(t, "interrupt") }
func TestCLIModelStreamCancelObservedPrefix(t *testing.T) { testCLIModelStream(t, "cancel") }
func TestCLIModelStreamSecretQuarantine(t *testing.T)     { testCLIModelStream(t, "secret") }
func TestCLIModelStreamDurableCommitFailure(t *testing.T) { testCLIModelStream(t, "commit-failure") }
func TestCLIModelStreamPipelinedTerminal(t *testing.T)    { testCLIModelStream(t, "pipeline") }
func TestCLIModelStreamSemanticSecretQuarantine(t *testing.T) {
	for _, kind := range []string{"alias", "reasoning.text", "reasoning.summary", "tool-json", "tool-json-signed-zero"} {
		t.Run(kind, func(t *testing.T) { testCLIModelStream(t, "secret-"+kind) })
	}
}

func testCLIModelStream(t *testing.T, mode string) {
	if queueCLIExactTLSChild(t) {
		return
	}
	if os.Getenv("RESEARCHOS_NODE") == "" || os.Getenv("RESEARCHOS_MU_BUNDLE") == "" {
		t.Fatal("actual pinned Node and current built Mu bundle are required")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
	defer cancel()
	root := t.TempDir()
	data := filepath.Join(root, "data")
	workspace := filepath.Join(root, "workspace")
	for _, dir := range []string{data, workspace} {
		if err := os.MkdirAll(dir, 0700); err != nil {
			t.Fatal(err)
		}
	}
	if err := os.WriteFile(filepath.Join(workspace, "source.txt"), []byte("fixture workspace\n"), 0600); err != nil {
		t.Fatal(err)
	}
	db, err := store.Open(filepath.Join(data, "researchos.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	if err = store.Bootstrap(ctx, db, "../../migrations/sqlite/0001_bootstrap.sql"); err != nil {
		t.Fatal(err)
	}
	svc, err := domain.New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if err != nil {
		t.Fatal(err)
	}
	h, err := host.New(host.Config{DB: db, Dir: filepath.Join(data, "host"), ContractsDir: "../../spec/v2.0/contracts", MigrationFile: "../../migrations/sqlite/0002_domain.sql", SchemaDir: "../../internal/api/contracts"})
	if err != nil {
		t.Fatal(err)
	}
	p := &queueCLIPermissionProfile{host: h}
	handler := &queueCLISwitchableHandler{h: api.HandlerWithConfigurationHost(db, t.TempDir(), svc, nil, h.InstanceID(), localworkspace.NewAuthority(h), localworkspace.NewScanner(), p, h)}
	server := httptest.NewServer(handler)
	defer server.Close()
	discoveryFile := filepath.Join(data, "discovery.json")
	writeCLIDiscovery(t, discoveryFile, discovery{URL: server.URL, PID: os.Getpid(), DataDir: data}, h.InstanceID())
	configFile := filepath.Join(root, "cli.json")
	pipe := host.PipeName(h.InstanceID())
	nativeCtx, nativeCancel := context.WithCancel(ctx)
	doneNative := make(chan error, 1)
	go func() {
		doneNative <- h.ServeNativeWithChooser(nativeCtx, pipe, func(hint string) (string, error) {
			if hint != workspace {
				return "", errors.New("foreign workspace")
			}
			return workspace, nil
		})
	}()
	defer func() {
		nativeCancel()
		wake, _ := json.Marshal(host.NativeFrame{Kind: "NATIVE_UNKNOWN", ClientID: "test-wake", Payload: json.RawMessage(`{}`)})
		_, _ = host.DialNative(pipe, wake)
		select {
		case <-doneNative:
		case <-time.After(5 * time.Second):
			t.Error("native fixture failed to stop")
		}
	}()
	exe := filepath.Join(root, "researchos.exe")
	build := exec.CommandContext(ctx, filepath.Join(runtime.GOROOT(), "bin", "go.exe"), "build", "-o", exe, ".")
	if raw, e := build.CombinedOutput(); e != nil {
		t.Fatalf("build actual CLI: %v %s", e, raw)
	}
	env := append(os.Environ(), "RESEARCHOS_CLI_DISCOVERY="+discoveryFile, "RESEARCHOS_CLI_CONFIG="+configFile, "RESEARCHOS_CLI_CREDENTIAL=", "RESEARCHOS_CLI_CLIENT_ID=queue-cli-fixture")
	init := exec.CommandContext(ctx, exe, "init", workspace)
	init.Env = env
	if raw, e := init.CombinedOutput(); e != nil {
		t.Fatalf("real CLI init: %v %s", e, raw)
	}
	cfg := readCLIIntegrationConfig(t, configFile)
	owner, e := h.ReadSessionFile()
	if e != nil {
		t.Fatal(e)
	}

	evidence := os.Getenv("RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR")
	if evidence != "" {
		evidence = filepath.Join(evidence, t.Name())
		if err = os.MkdirAll(evidence, 0700); err != nil {
			t.Fatal(err)
		}
		defer func() {
			if _, e := db.Exec("VACUUM INTO ?", filepath.Join(evidence, "fixture.sqlite")); e != nil {
				t.Error(e)
			}
		}()
	}
	gates := make(chan int, 1)
	arrived := make(chan int, 1)
	fixtureError := make(chan error, 1)
	var rawMu sync.Mutex
	var original bytes.Buffer
	p.server = httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/__researchos_fixture_readiness__" {
			w.WriteHeader(404)
			return
		}
		if r.URL.Path != "/v1/chat/completions" || r.Header.Get("Authorization") != "Bearer permission-loopback-fixture" {
			w.WriteHeader(403)
			return
		}
		var request domain.Object
		if json.NewDecoder(r.Body).Decode(&request) != nil || request["model"] != "fixture-model" {
			w.WriteHeader(400)
			return
		}
		n := p.calls.Add(1)
		w.Header().Set("Content-Type", "text/event-stream")
		captureSafeRaw := true
		emit := func(text string, finish any) {
			line := fmt.Sprintf("data: %s\n\n", domain.Bytes(domain.Object{"id": "causal-model", "object": "chat.completion.chunk", "created": 1, "model": "fixture-model", "choices": []any{domain.Object{"index": 0, "delta": domain.Object{"role": "assistant", "content": text}, "finish_reason": finish}}}))
			fmt.Fprint(w, line)
			if n > 1 && captureSafeRaw {
				rawMu.Lock()
				original.WriteString(line)
				rawMu.Unlock()
			}
			w.(http.Flusher).Flush()
		}
		if n == 1 {
			emit("qualification", nil)
			emit("", "stop")
			fmt.Fprint(w, "data: [DONE]\n\n")
			return
		}
		limit := 40
		if mode == "pipeline" {
			emit(strings.Repeat("中🙂", 5000), nil)
			limit = 0
		}
		if mode != "complete" && mode != "pipeline" {
			limit = 3
		}
		for i := 1; i <= limit; i++ {
			emit(fmt.Sprintf("piece-%02d-中🙂 ", i), nil)
			select {
			case arrived <- i:
			case <-r.Context().Done():
				return
			}
			select {
			case got := <-gates:
				if got != i {
					fixtureError <- fmt.Errorf("causal barrier mismatched %d/%d", got, i)
					return
				}
			case <-r.Context().Done():
				return
			case <-time.After(15 * time.Second):
				fixtureError <- fmt.Errorf("upstream flush %d never reached SDK/SQLite/CLI", i)
				return
			}
		}
		if mode == "cancel" {
			<-r.Context().Done()
			return
		}
		if mode == "interrupt" {
			conn, _, err := w.(http.Hijacker).Hijack()
			if err != nil {
				fixtureError <- err
				return
			}
			conn.Close()
			return
		}
		if strings.HasPrefix(mode, "secret-") {
			captureSafeRaw = false
			kind := strings.TrimPrefix(mode, "secret-")
			for i, text := range []string{"permission-", "loopback-fixture"} {
				delta := domain.Object{}
				if kind == "tool-json" || kind == "tool-json-signed-zero" {
					part := `{"value":"perm\u0069`
					if i == 1 {
						part = `ssion-loopback-fixture"}`
					}
					delta["tool_calls"] = []any{domain.Object{"index": 0, "id": "synthetic-tool", "type": "function", "function": domain.Object{"name": "synthetic_tool", "arguments": part}}}
					if kind == "tool-json-signed-zero" {
						call := delta["tool_calls"].([]any)[0].(domain.Object)
						if i == 0 {
							call["index"] = json.RawMessage("-0")
						} else {
							delete(call, "id")
						}
					}
				} else if kind == "alias" {
					key := "reasoning"
					if i == 1 {
						key = "reasoning_content"
					}
					delta[key] = text
				} else {
					field := "text"
					if kind == "reasoning.summary" {
						field = "summary"
					}
					delta["reasoning_details"] = []any{domain.Object{"type": kind, field: text, "index": i}}
				}
				line := fmt.Sprintf("data: %s\n\n", domain.Bytes(domain.Object{"choices": []any{domain.Object{"index": 0, "delta": delta}}}))
				// Exercise decoded strings as well as wire/read boundaries with a wholly
				// synthetic fixture credential; no protected host credential is read.
				line = strings.ReplaceAll(line, "permission-", `perm\u0069ssion-`)
				fmt.Fprint(w, line)
				w.(http.Flusher).Flush()
			}
			emit("", "stop")
			fmt.Fprint(w, "data: [DONE]\n\n")
			return
		}
		if mode == "secret" {
			captureSafeRaw = false
			emit("permission-", nil)
			emit("loopback-fixture", nil)
			return
		}
		emit("", "stop")
		fmt.Fprint(w, "data: [DONE]\n\n")
		rawMu.Lock()
		original.WriteString("data: [DONE]\n\n")
		rawMu.Unlock()
	}))
	defer p.server.Close()
	queueCLIInstallTLSFixture(t, p.server)
	coordinator, e := queueCLIFixtureModelProfile(ctx, svc, h, server.Client(), server.URL, owner.Token, cfg.ProjectID, data, p)
	if e != nil {
		t.Fatal("actual qualification", e)
	}
	defer coordinator.Close()
	handler.swap(api.HandlerWithConfigurationHost(db, t.TempDir(), svc, coordinator, h.InstanceID(), localworkspace.NewAuthority(h), localworkspace.NewScanner(), p, h))
	cfg.Model = p.modelRef
	if e = os.WriteFile(configFile, domain.Bytes(cfg), 0600); e != nil {
		t.Fatal(e)
	}
	run := exec.CommandContext(ctx, exe)
	run.Env = env
	stdin, e := run.StdinPipe()
	if e != nil {
		t.Fatal(e)
	}
	stdout, e := run.StdoutPipe()
	if e != nil {
		t.Fatal(e)
	}
	var stderr bytes.Buffer
	run.Stderr = &stderr
	lines := make(chan domain.Object, 256)
	scanError := make(chan error, 1)
	var output bytes.Buffer
	if e = run.Start(); e != nil {
		t.Fatal(e)
	}
	go func() {
		scanner := bufio.NewScanner(stdout)
		scanner.Buffer(make([]byte, 65536), 1<<20)
		for scanner.Scan() {
			raw := append([]byte(nil), scanner.Bytes()...)
			output.Write(raw)
			output.WriteByte('\n')
			value, err := domain.Decode(raw)
			if err != nil {
				scanError <- err
				return
			}
			lines <- value
		}
		scanError <- scanner.Err()
		close(lines)
	}()
	done := make(chan error, 1)
	go func() { done <- run.Wait() }()
	defer func() {
		if run.ProcessState == nil {
			run.Process.Kill()
			<-done
		}
		if evidence != "" {
			os.WriteFile(filepath.Join(evidence, "cli.stdout.jsonl"), output.Bytes(), 0600)
			os.WriteFile(filepath.Join(evidence, "cli.stderr.raw"), stderr.Bytes(), 0600)
			rawMu.Lock()
			os.WriteFile(filepath.Join(evidence, "provider-original.sse"), original.Bytes(), 0600)
			rawMu.Unlock()
		}
	}()
	if _, e = io.WriteString(stdin, "Causal actual model stream\n"); e != nil {
		t.Fatal(e)
	}
	scanCtx, stopScan := context.WithCancel(ctx)
	defer stopScan()
	scanDone := make(chan error, 1)
	go func() {
		for {
			if e := coordinator.Scan(scanCtx); e != nil && scanCtx.Err() == nil {
				scanDone <- e
				return
			}
			select {
			case <-scanCtx.Done():
				scanDone <- nil
				return
			case <-time.After(25 * time.Millisecond):
			}
		}
	}()
	defer func() {
		stopScan()
		select {
		case <-scanDone:
		case <-time.After(5 * time.Second):
			t.Error("coordinator scan did not stop")
		}
	}()
	expected := 40
	if mode != "complete" {
		expected = 3
	}
	if mode == "pipeline" {
		expected = 0
	}
	if mode == "commit-failure" {
		expected = 1
	}
	prefix := ""
	var session, runID, message string
	var initialRevision int64
	for i := 1; i <= expected; i++ {
		select {
		case got := <-arrived:
			if got != i {
				t.Fatal("flush order", got)
			}
		case e := <-fixtureError:
			t.Fatal(e)
		case e := <-scanDone:
			t.Fatal("coordinator", e)
		case <-ctx.Done():
			t.Fatal("upstream did not flush")
		}
		text := fmt.Sprintf("piece-%02d-中🙂 ", i)
		seen := false
		for !seen {
			select {
			case row := <-lines:
				ev, _ := row["event"].(map[string]any)
				payload, _ := ev["payload"].(map[string]any)
				if payload["role"] == "ASSISTANT" && payload["phase"] == "END" {
					t.Fatal("public END before provider EOF")
				}
				if payload["role"] == "ASSISTANT" && payload["phase"] == "DELTA" {
					if payload["text"] != text {
						t.Fatalf("actual SDK delta %v want %q", payload, text)
					}
					session = domain.Str(ev, "session_id")
					runID = domain.Str(ev, "run_id")
					message = domain.Str(payload, "message_id")
					seen = true
				}
			case e := <-fixtureError:
				t.Fatal(e)
			case e := <-scanError:
				if e != nil {
					t.Fatal(e)
				}
			case <-ctx.Done():
				t.Fatal("CLI did not receive flush", i)
			}
		}
		prefix += text
		var count, wm, revision int64
		var artifact string
		if e = db.QueryRow(`SELECT count(*) FROM client_control_receipts WHERE kind='MODEL_STREAM_OBSERVATION_V1' AND json_extract(body,'$.observation.binding.run_id')=? AND json_extract(body,'$.observation.payload.event')='text_delta'`, runID).Scan(&count); e != nil {
			t.Fatal(e)
		}
		if count != int64(i) {
			t.Fatalf("SDK observation not durable before CLI arrival %d/%d", count, i)
		}
		if e = db.QueryRow(`SELECT event_watermark,revision,transcript_artifact_id FROM client_sessions WHERE id=?`, session).Scan(&wm, &revision, &artifact); e != nil {
			t.Fatal(e)
		}
		if i == 1 {
			initialRevision = revision
		} else if revision != initialRevision {
			t.Fatalf("private token changed control revision %d/%d", revision, initialRevision)
		}
		var raw []byte
		if e = db.QueryRow(`SELECT u.bytes FROM uploaded_content u JOIN domain_objects a ON a.project=u.project AND a.kind='Artifact' AND json_extract(a.body,'$.storage_key')=u.storage_key WHERE a.id=? AND u.sealed=1`, artifact).Scan(&raw); e != nil {
			t.Fatal(e)
		}
		transcript, e := domain.Decode(raw)
		if e != nil {
			t.Fatal(e)
		}
		if transcript["complete"] != false {
			t.Fatal("partial transcript claimed complete")
		}
		found := false
		for _, v := range domain.Arr(transcript, "messages") {
			m := v.(map[string]any)
			if m["message_id"] == message {
				parts := domain.Arr(m, "parts")
				found = len(parts) == 1 && parts[0].(map[string]any)["text"] == prefix && m["complete"] == false
			}
		}
		if !found {
			t.Fatal("partial pointer does not equal exact durable prefix")
		}
		var effectState string
		if e = db.QueryRow(`SELECT json_extract(body,'$.state') FROM resource_effects WHERE run=? ORDER BY rowid DESC LIMIT 1`, runID).Scan(&effectState); e != nil || effectState != "STARTED" {
			t.Fatalf("MODEL ordinary ACK completed before flush barrier: %s %v", effectState, e)
		}
		t.Logf("MODEL_STREAM_CAUSAL %s", domain.Bytes(domain.Object{"flush": i, "sdk_durable_delta": count, "sqlite_watermark": wm, "cli_arrival": true, "prefix_hash": domain.Digest([]byte(prefix)), "ordinary_effect": "STARTED", "observed_at": time.Now().UTC().Format(time.RFC3339Nano)}))
		if mode == "commit-failure" {
			if _, err := db.Exec(`CREATE TRIGGER model_stream_injected_seal_failure BEFORE INSERT ON uploaded_content BEGIN SELECT RAISE(ABORT,'injected stream seal failure'); END;`); err != nil {
				t.Fatal(err)
			}
		}
		gates <- i
	}
	if mode == "cancel" {
		if _, e = io.WriteString(stdin, "/cancel\n"); e != nil {
			t.Fatal(e)
		}
	}
	_ = stdin.Close()
	if mode != "complete" && mode != "pipeline" {
		deadline := time.Now().Add(12 * time.Second)
		unknown := 0
		for time.Now().Before(deadline) {
			db.QueryRow(`SELECT count(*) FROM resource_effects WHERE run=? AND json_extract(body,'$.state')='UNKNOWN'`, runID).Scan(&unknown)
			if unknown > 0 {
				break
			}
			time.Sleep(25 * time.Millisecond)
		}
		if unknown != 1 {
			t.Fatalf("interrupted effect UNKNOWN count=%d", unknown)
		}
		var ends int
		if e = db.QueryRow(`SELECT count(*) FROM outbox WHERE json_extract(body,'$.run_id')=? AND json_extract(body,'$.kind')='MESSAGE' AND json_extract(body,'$.payload.role')='ASSISTANT' AND json_extract(body,'$.payload.phase')='END'`, runID).Scan(&ends); e != nil || ends != 0 {
			t.Fatalf("interrupted public END=%d %v", ends, e)
		}
		if mode == "commit-failure" {
			var deltas int
			if err := db.QueryRow(`SELECT count(*) FROM outbox WHERE json_extract(body,'$.run_id')=? AND json_extract(body,'$.payload.role')='ASSISTANT' AND json_extract(body,'$.payload.phase')='DELTA'`, runID).Scan(&deltas); err != nil || deltas != 1 {
				t.Fatalf("failed prefix seal leaked delta: count=%d error=%v", deltas, err)
			}
			t.Log("MODEL_STREAM_COMMIT_FAILURE first prefix durable, second prefix transaction rolled back, original effect UNKNOWN and no END")
		}
		if strings.HasPrefix(mode, "secret") {
			for _, query := range []string{`SELECT body FROM outbox`, `SELECT body FROM client_control_receipts`, `SELECT body FROM resource_effects`, `SELECT CAST(bytes AS TEXT) FROM uploaded_content`} {
				rows, err := db.Query(query)
				if err != nil {
					t.Fatal(err)
				}
				for rows.Next() {
					var raw string
					rows.Scan(&raw)
					if strings.Contains(raw, "permission-") || strings.Contains(raw, "loopback-fixture") {
						rows.Close()
						t.Fatal("quarantined credential fragment reached durable evidence")
					}
				}
				rows.Close()
			}
			err := filepath.WalkDir(filepath.Join(data, "runtime-dispatches"), func(path string, entry os.DirEntry, err error) error {
				if err != nil {
					return err
				}
				if entry.Name() == "stdout.raw" {
					raw, e := os.ReadFile(path)
					if e != nil {
						return e
					}
					if evidence != "" {
						name := "worker-stdout-" + strings.TrimPrefix(domain.Digest([]byte(path)), "sha256:") + ".raw"
						if err := os.WriteFile(filepath.Join(evidence, name), raw, 0600); err != nil {
							return err
						}
					}
					if bytes.Contains(raw, []byte("permission-")) || bytes.Contains(raw, []byte("loopback-fixture")) {
						return errors.New("quarantined credential reached worker stdout")
					}
				}
				return nil
			})
			if err != nil {
				t.Fatal(err)
			}
		}
		run.Process.Kill()
		<-done
		return
	}
	select {
	case e = <-done:
		if e != nil {
			t.Fatalf("compiled CLI failed %v stderr=%s", e, stderr.String())
		}
	case e = <-scanDone:
		t.Fatal("coordinator finalization", e)
	case <-ctx.Done():
		t.Fatal("compiled CLI did not complete")
	}
	if e = <-scanError; e != nil {
		t.Fatal(e)
	}
	if mode == "pipeline" {
		deltas := 0
		for row := range lines {
			ev, _ := row["event"].(map[string]any)
			payload, _ := ev["payload"].(map[string]any)
			if payload["role"] == "ASSISTANT" && payload["phase"] == "DELTA" {
				prefix += domain.Str(payload, "text")
				runID, message = domain.Str(ev, "run_id"), domain.Str(payload, "message_id")
				deltas++
			}
		}
		if prefix != strings.Repeat("中🙂", 5000) || deltas < 5 {
			t.Fatalf("pipelined UTF8 complete delta count=%d bytes=%d", deltas, len(prefix))
		}
		t.Logf("MODEL_STREAM_PIPELINED raw text bytes=%d (>4 fragments), SDK durable/CLI deltas=%d, terminal completed without credit gap", len(prefix), deltas)
	}
	var ends int
	if e = db.QueryRow(`SELECT count(*) FROM outbox WHERE json_extract(body,'$.run_id')=? AND json_extract(body,'$.payload.message_id')=? AND json_extract(body,'$.payload.phase')='END'`, runID, message).Scan(&ends); e != nil || ends != 1 {
		t.Fatalf("final END=%d %v", ends, e)
	}
	var receiptRaw string
	if e = db.QueryRow(`SELECT json_extract(body,'$.receipt.payload.body') FROM resource_effects WHERE run=? AND json_extract(body,'$.state')='CONFIRMED'`, runID).Scan(&receiptRaw); e != nil {
		t.Fatal(e)
	}
	rawMu.Lock()
	equal := receiptRaw == original.String()
	rawMu.Unlock()
	if !equal {
		t.Fatal("original accepted SSE bytes changed")
	}
	if strings.Contains(output.String(), owner.Token) {
		t.Fatal("host secret in CLI output")
	}
	if mode == "pipeline" {
		t.Log("actual pipelined large SSE event crossed four-frame data window and terminal credit ordering; original bytes preserved")
	} else {
		t.Log("actual causal flushes held B/EOF until SDK observation + SQLite DELTA + compiled CLI JSONL arrival; complete original bytes preserved")
	}
}
