// v2verbs.go is the W05-03 remediation phase for the review's first blocker: the host-bound verbs answered with one
// GET /healthz, discarded the ids they were given, and exited 0. Every row here names a protocol method the verb must
// actually send, and the counter-server records the envelope it received, so "the verb performs the operation" is a
// measurement rather than a claim.
package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"encoding/json/jsontext"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"researchos.local/research-os/internal/api"
	"sort"
	"strings"
	"sync/atomic"
	"time"
)

type probe struct {
	server            *http.Server
	ln                net.Listener
	url               string
	mode              string
	seen              []map[string]any
	healths           int
	configurePhase    bool
	configureRevision int
	ackCalls          int
	activeGoal        string
	admittedMessages  int
	fixtureProject    string
	fixtureSession    string
	fixtureRun        string
	fixtureTask       string
	fixtureArtifact   string
	fixtureEvents     []any
	wireOrdinal       atomic.Uint64
}

// wireMethods records every method name that reached any probe host during this run, so the command table's own
// method column can be graded against observed traffic instead of against itself. The round-2 review named the
// defect precisely: "the check grades what its fixture answers, and the fixture answers a method name".
var wireMethods = map[string]int{}

// strictWrite mirrors internal/domain/client_protocol.go:7. It is duplicated here on purpose: a fixture that
// imported the product's own table could not refuse a product change, which is the whole point of the mode.
var strictWrite = map[string]bool{"session.send": true, "session.control": true, "session.update": true,
	"session.handoff": true, "workspace.write": true, "artifact.import": true, "permission.respond": true,
	"goal.start": true, "project.bootstrap": true}

var strictEmptyPayload = map[string]bool{"host.status": true, "session.get": true, "workspace.list": true}

// strictVerdict validates the envelope the way the core does, so anything that lives below the method name - the
// CAS fields, the protocol version, the command id, the closed-payload rule, the model-change epoch rule - has to
// survive an actual refusal rather than an agreeable echo.
func strictVerdict(env map[string]any) string {
	doc, err := api.ClientProtocolDocument()
	if err != nil || doc.ValidateDef("CommandEnvelope", env) != nil {
		return "INVALID_REQUEST"
	}
	method, _ := env["method"].(string)
	if pv, _ := env["protocol_version"].(string); pv != "researchos-client/2" {
		return "UNSUPPORTED_PROTOCOL"
	}
	if cid, _ := env["command_id"].(string); cid == "" {
		return "MISSING_FIELD:command_id"
	}
	for _, f := range []string{"project_id", "session_id"} {
		if v, isStr := env[f].(string); isStr && v == "" {
			return "MISSING_FIELD:" + f
		}
	}
	pl, _ := env["payload"].(map[string]any)
	if method == "session.attach" {
		claim, _ := pl["request_write_owner"].(bool)
		if claim && env["writer_epoch"] != nil {
			return "ATTACKER_CLAIMED_EPOCH"
		}
		if !claim && env["writer_epoch"] == nil {
			return "MISSING_FIELD:writer_epoch"
		}
		return ""
	}
	if strictWrite[method] && !(method == "goal.start" && env["session_id"] == nil) && method != "project.bootstrap" {
		if pid, _ := env["project_id"].(string); pid == "" {
			return "MISSING_FIELD:project_id"
		}
		if env["expected_revision"] == nil {
			return "MISSING_FIELD:expected_revision"
		}
		if env["writer_epoch"] == nil {
			return "MISSING_FIELD:writer_epoch"
		}
	}
	if method == "host.configure" {
		if env["session_id"] == nil {
			for _, key := range []string{"project_id", "session_id", "expected_revision", "writer_epoch"} {
				if env[key] != nil {
					return "INVALID_CONFIGURE_SCOPE"
				}
			}
		} else {
			if env["writer_epoch"] == nil {
				return "MODEL_CHANGE_WITHOUT_EPOCH"
			}
			for _, key := range []string{"project_id", "session_id", "expected_revision", "writer_epoch"} {
				if env[key] == nil {
					return "INVALID_CONFIGURE_SCOPE"
				}
			}
		}
	}

	if strictEmptyPayload[method] && len(pl) > 0 {
		return "UNEXPECTED_PAYLOAD_KEYS"
	}
	return ""
}

func newProbe(mode string) (*probe, error) {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		return nil, err
	}
	p := &probe{ln: ln, mode: mode, url: "http://" + ln.Addr().String()}
	p.server = &http.Server{Handler: http.HandlerFunc(p.recordedHandle)}
	go p.server.Serve(ln)
	for i := 0; i < 60; i++ {
		c, e := net.DialTimeout("tcp", ln.Addr().String(), 200*time.Millisecond)
		if e == nil {
			c.Close()
			return p, nil
		}
		time.Sleep(50 * time.Millisecond)
	}
	_ = p.server.Close()
	return nil, fmt.Errorf("probe listener never accepted on %s", ln.Addr().String())
}

type probeWireResponse struct {
	http.ResponseWriter
	body bytes.Buffer
	code int
}

func (w *probeWireResponse) WriteHeader(code int) {
	if w.code == 0 {
		w.code = code
	}
	w.ResponseWriter.WriteHeader(code)
}

func (w *probeWireResponse) Write(raw []byte) (int, error) {
	if w.code == 0 {
		w.code = http.StatusOK
	}
	n, err := w.ResponseWriter.Write(raw)
	w.body.Write(raw[:n])
	return n, err
}

func (p *probe) recordedHandle(w http.ResponseWriter, r *http.Request) {
	raw, err := io.ReadAll(io.LimitReader(r.Body, (1<<20)+1))
	if err != nil || len(raw) > 1<<20 {
		http.Error(w, "invalid fixture request size", http.StatusBadRequest)
		return
	}
	r.Body = io.NopCloser(bytes.NewReader(raw))
	response := &probeWireResponse{ResponseWriter: w}
	p.handle(response, r)
	requestFact, responseFact := protocolBlobRecord(raw), protocolBlobRecord(response.body.Bytes())
	requestFact["raw_base64"], responseFact["raw_base64"] = raw, response.body.Bytes()
	row := map[string]any{"measurement_mode": "FIXTURE_PROTOCOL", "method": r.Method, "url": p.url + r.URL.RequestURI(), "http_status": response.code, "request": requestFact, "response": responseFact}
	encoded, _ := json.MarshalIndent(row, "", "  ")
	dir := filepath.Join(contractRunDir, "probe-wire", strings.TrimPrefix(p.url, "http://127.0.0.1:"))
	if err := os.MkdirAll(dir, 0700); err != nil {
		panic(err)
	}
	path := filepath.Join(dir, fmt.Sprintf("exchange-%06d.json", p.wireOrdinal.Add(1)))
	file, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if err != nil {
		panic(err)
	}
	_, err = file.Write(encoded)
	closeErr := file.Close()
	if err != nil || closeErr != nil {
		panic("fixture wire evidence write failed")
	}
}

func (p *probe) handle(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	if r.Method == http.MethodGet && p.fixtureProject != "" {
		prefix := "/v1/projects/" + p.fixtureProject
		var result any
		switch r.URL.Path {
		case prefix + "/goals/" + p.activeGoal:
			result = map[string]any{"id": p.activeGoal, "project_id": p.fixtureProject, "status": "ACTIVE", "task_ids": []any{p.fixtureTask}}
		case prefix + "/tasks/" + p.fixtureTask:
			result = map[string]any{"id": p.fixtureTask, "project_id": p.fixtureProject, "goal_id": p.activeGoal, "active_run_id": p.fixtureRun, "status": "EXECUTION_REPORTED"}
		case prefix + "/tasks":
			result = []any{}
		case prefix + "/runs/" + p.fixtureRun:
			result = map[string]any{"id": p.fixtureRun, "project_id": p.fixtureProject, "task_id": p.fixtureTask, "revision": 1, "status": "SETTLED", "children_stopped": true, "queue_empty": true, "execution_report": "FIXTURE_PROTOCOL finite execution transcript; no SDK/model or independent acceptance", "exit_code": 0, "result_artifact_ids": []any{p.fixtureArtifact}, "runtime_settled_at": "2026-10-05T12:00:00Z", "cancel_confirmed_at": nil, "cancel_requested_at": nil}
		}
		if result != nil {
			json.NewEncoder(w).Encode(result)
			return
		}
	}
	if r.URL.Path == "/healthz" {
		p.healths++
		if p.mode == "unhealthy" {
			w.WriteHeader(503)
			fmt.Fprint(w, `{"state":"NOT_READY"}`)
			return
		}
		fmt.Fprint(w, `{"state":"READY"}`)
		return
	}
	if r.URL.Path != "/v2/command" {
		w.WriteHeader(404)
		fmt.Fprint(w, `{"code":"NOT_FOUND"}`)
		return
	}
	if p.mode == "unhealthy" || p.mode == "http500" {
		// A host that is up but cannot serve the command answers with an HTTP error and no protocol status, which
		// is a different failure from a transport refusal and must not read as a completion either way.
		code := http.StatusServiceUnavailable
		if p.mode == "http500" {
			code = http.StatusInternalServerError
		}
		w.WriteHeader(code)
		fmt.Fprint(w, `{"code":"INTERNAL_ERROR","message":"authoritative store unavailable"}`)
		return
	}
	if !strings.HasPrefix(r.Header.Get("Authorization"), "Bearer ") {
		w.WriteHeader(401)
		fmt.Fprint(w, `{"protocol_version":"researchos-client/2","status":"REJECTED","error_code":"UNAUTHENTICATED"}`)
		return
	}
	raw, _ := io.ReadAll(io.LimitReader(r.Body, 1<<20))
	if !jsontext.Value(raw).IsValid() {
		http.Error(w, "invalid JSON", 400)
		return
	}
	var precise map[string]any
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.UseNumber()
	doc, docErr := api.ClientProtocolDocument()
	if decoder.Decode(&precise) != nil || docErr != nil || doc.ValidateDef("CommandEnvelope", precise) != nil {
		http.Error(w, "invalid typed envelope", 400)
		return
	}
	var env map[string]any
	_ = json.Unmarshal(raw, &env)
	p.seen = append(p.seen, env)
	commandID, _ := env["command_id"].(string)
	method, _ := env["method"].(string)
	if method != "" {
		wireMethods[method]++
	}
	if p.mode == "strict" {
		if code := strictVerdict(env); code != "" {
			w.WriteHeader(422)
			json.NewEncoder(w).Encode(probeResponse(env, "REJECTED", nil, "INVALID_REQUEST"))
			return
		}
	}
	if p.mode == "inprogress" {
		response := probeResponse(env, "IN_PROGRESS", nil, "")
		json.NewEncoder(w).Encode(response)
		return
	}
	if p.mode == "ack" {
		p.ackCalls++
		if p.ackCalls == 1 {
			json.NewEncoder(w).Encode(probeResponse(env, "ACKNOWLEDGED", map[string]any{"accepted_at": time.Now().UTC().Format(time.RFC3339Nano), "operation_id": commandID, "after_sequence": 0, "related_resource_ref": nil}, ""))
			return
		}
	}
	switch p.mode {
	case "rejected":
		json.NewEncoder(w).Encode(probeResponse(env, "REJECTED", nil, "WRITER_BUSY"))
	case "notimplemented":
		json.NewEncoder(w).Encode(probeResponse(env, "REJECTED", nil, "NOT_IMPLEMENTED"))
	case "malformed":
		fmt.Fprint(w, `{"status":`)
	default:
		if method == "host.status" {
			_ = json.NewEncoder(w).Encode(map[string]any{
				"protocol_version": "researchos-client/2", "command_id": commandID, "method": method,
				"status": "COMPLETED", "session_id": env["session_id"], "revision": nil, "error_code": nil, "error": nil,
				"result": map[string]any{"host_instance_id": "fixture-host", "core_build_id": "fixture-build",
					"protocol_versions": []string{"researchos-client/2"}, "host_state": "READY", "client_id": env["client_id"],
					"authenticated_principal_ref": "fixture-principal", "config_revision": p.configureRevision,
					"model_configurations": []any{}, "credentials": []any{}, "workspaces": []any{},
					"supported_methods": []string{"host.status"}, "operating_mode": "LOCAL_USER_HOST"},
			})
			return
		}
		if method == "host.configure" {
			pl := payloadOf(env)
			revision := any(nil)
			if env["session_id"] != nil {
				revision = env["expected_revision"].(float64) + 1
			}
			reply := map[string]any{"protocol_version": "researchos-client/2", "command_id": commandID, "method": method, "status": "COMPLETED", "session_id": env["session_id"], "revision": revision, "error_code": nil, "error": nil, "result": map[string]any{"model_config_ref": "mc-probe-opaque-4", "config_revision": pl["config_revision"], "provider_id": pl["provider_id"], "model_id": pl["model_id"], "base_url": pl["base_url"], "credential_ref": pl["credential_ref"], "verified_at": nil}}
			if p.mode == "configure-busy" {
				reply["status"] = "REJECTED"
				reply["revision"] = env["expected_revision"]
				reply["error_code"] = "SESSION_BUSY"
				reply["result"] = nil
				reply["error"] = map[string]any{"code": "SESSION_BUSY", "message": "fixture session remains busy", "retryable": false, "recovery": "WAIT_FOR_SETTLEMENT", "current_revision": env["expected_revision"], "current_writer_epoch": env["writer_epoch"], "resource_request_id": nil, "retry_after_ms": nil, "correlation_id": commandID}
			} else if n, ok := pl["config_revision"].(float64); !p.configurePhase || !ok || int(n) != p.configureRevision+1 {
				w.Write([]byte(`{"invalid_configure_cas":true}`))
				return
			} else {
				p.configureRevision = int(n)
			}
			json.NewEncoder(w).Encode(reply)
			return
		}
		var result any
		sid, _ := env["session_id"].(string)
		switch method {
		case "session.list":
			items := []any{}
			if p.mode == "identity-substitution" {
				items = append(items, p.snapshot(env, "sess-from-list"))
			}
			result = map[string]any{"items": items, "next_cursor": nil}
		case "session.create":
			sid = "sess-created-1"
			result = p.snapshot(env, sid)
		case "session.get":
			result = p.snapshot(env, sid)
		case "session.attach":
			result = map[string]any{"snapshot": p.snapshot(env, sid), "write_owner_acquired": payloadOf(env)["request_write_owner"] == true}
		case "goal.start":
			if sid == "" {
				sid = "sess-goal-1"
			}
			p.activeGoal = "goal-protocol-fixture"
			snap := p.snapshot(env, sid)
			snap["goal_id"] = p.activeGoal
			snap["goal_status"] = "DRAFT"
			if payloadOf(env)["start_as_draft"] != true {
				snap["goal_status"] = "BLOCKED"
			}
			result = map[string]any{"goal_id": p.activeGoal, "goal_revision": 1, "goal_status": snap["goal_status"], "snapshot": snap}
		case "session.send":
			p.admittedMessages++
			p.installFiniteTranscript(env, sid)
			result = map[string]any{"message_id": fmt.Sprintf("message-%d", p.admittedMessages), "run_id": nil, "queue_position": 0, "snapshot": p.snapshot(env, sid)}
		case "session.events":
			start := int(payloadOf(env)["after_sequence"].(float64))
			if start < 0 || start > len(p.fixtureEvents) || sid != p.fixtureSession {
				json.NewEncoder(w).Encode(probeResponse(env, "REJECTED", nil, "CURSOR_INVALID"))
				return
			}
			result = map[string]any{"events": p.fixtureEvents[start:], "next_sequence": len(p.fixtureEvents), "high_watermark": len(p.fixtureEvents), "has_more": false}
		default:
			json.NewEncoder(w).Encode(probeResponse(env, "REJECTED", nil, "NOT_IMPLEMENTED"))
			return
		}
		response := probeResponse(env, "COMPLETED", result, "")
		if method == "session.create" {
			response["session_id"] = sid
		}
		if method == "session.create" || method == "session.get" || method == "session.attach" || method == "session.send" {
			response["revision"] = 7
		}
		if method == "goal.start" {
			response["revision"] = 1
		}
		json.NewEncoder(w).Encode(response)
	}
}

func (p *probe) close() { _ = p.server.Close() }

func (p *probe) methods() []string {
	out := []string{}
	for _, e := range p.seen {
		out = append(out, fmt.Sprint(e["method"]))
	}
	return out
}

func (p *probe) last() map[string]any {
	if len(p.seen) == 0 {
		return map[string]any{}
	}
	return p.seen[len(p.seen)-1]
}

// jsonOf parses the single JSONL record the CLI is allowed to put on stdout.
func jsonOf(r run) map[string]any {
	result := map[string]any{}
	for _, line := range nonEmpty(r.stdout) {
		var row map[string]any
		if json.Unmarshal([]byte(line), &row) != nil {
			return map[string]any{}
		}
		if row["command"] != nil && row["exit_code"] != nil {
			result = row
		}
	}
	return result
}

func payloadOf(env map[string]any) map[string]any {
	p, _ := env["payload"].(map[string]any)
	if p == nil {
		return map[string]any{}
	}
	return p
}

func str(v any) string { return fmt.Sprint(v) }

// v2VerbPhase drives the real child against the recording host. cfgPath/discPath are this phase's own files so the
// earlier contract rows keep their configuration.
func v2VerbPhase(repo string) {
	cfgPath := filepath.Join(contractRunDir, "w0503_v2_config.json")
	discPath := filepath.Join(contractRunDir, "w0503_v2_discovery.json")
	_ = os.Remove(cfgPath)
	_ = os.Remove(discPath)
	bin := filepath.Join(contractRunDir, "w0503_cli.exe")

	call := func(env []string, args ...string) run {
		budget, stop := context.WithTimeout(context.Background(), 30*time.Second)
		defer stop()
		c := exec.CommandContext(budget, bin, args...)
		c.Dir = repo
		c.Env = env
		var so, se strings.Builder
		c.Stdout, c.Stderr = &so, &se
		err := c.Run()
		code := 0
		if ee, isExit := err.(*exec.ExitError); isExit {
			code = ee.ExitCode()
		} else if err != nil {
			code = -1
		}
		recordContractChild(c, so.String(), se.String(), code)
		return run{so.String(), se.String(), code, err}
	}
	callWithStdin := func(env []string, stdin string, args ...string) run {
		budget, stop := context.WithTimeout(context.Background(), 30*time.Second)
		defer stop()
		c := exec.CommandContext(budget, bin, args...)
		c.Dir = repo
		c.Env = env
		c.Stdin = strings.NewReader(stdin)
		var so, se strings.Builder
		c.Stdout, c.Stderr = &so, &se
		err := c.Run()
		code := 0
		if ee, isExit := err.(*exec.ExitError); isExit {
			code = ee.ExitCode()
		} else if err != nil {
			code = -1
		}
		recordContractChild(c, so.String(), se.String(), code)
		return run{so.String(), se.String(), code, err}
	}
	base := func(extra ...string) []string {
		e := append([]string{}, os.Environ()...)
		e = append(e, "RESEARCHOS_CLI_CONFIG="+cfgPath, "RESEARCHOS_CLI_DISCOVERY="+discPath,
			"RESEARCHOS_CLI_CLIENT_ID=probe-client", "RESEARCHOS_CLI_CREDENTIAL=probe-token")
		return append(e, extra...)
	}
	writeDisc := func(url string) {
		_ = os.WriteFile(discPath, []byte(`{"url":"`+url+`","pid":`+fmt.Sprint(os.Getpid())+
			`,"data_dir":"","started_at":"now"}`), 0o600)
	}
	writeCfg := func(body string) { _ = os.WriteFile(cfgPath, []byte(body), 0o600) }

	// A host that completes everything: each verb must send the method its name refers to.
	p, err := newProbe("complete")
	if err != nil {
		skip("W0503-STATUS-SENDS-HOST-STATUS", "loopback listen refused: "+err.Error())
		skip("W0503-GOAL-SENDS-GOAL-START", "same listener failure")
		return
	}
	defer p.close()
	writeDisc(p.url)
	// project/session/revision/epoch come from the config the verbs read; nothing here is invented by the CLI.
	writeCfg(`{"config_revision":3,"model":"vendor/old","settled_run_id":"run-settled",` +
		`"workspace_ref":"D:/ws","project_id":"proj-probe","updated_by":"probe"}`)

	st := call(base(), "status")
	ok("W0503-STATUS-SENDS-HOST-STATUS", st.code == 0 && str(jsonOf(st)["status"]) == "COMPLETED" &&
		hasMethod(p.methods(), "host.status") && hasOp(jsonOf(st), "host.status", "COMPLETED") &&
		hasOp(jsonOf(st), "session.get", "SKIPPED"), "code", st.code, "saw", p.methods(), jsonOf(st))
	ok("W0503-STATUS-IS-NOT-A-HEALTH-PROBE", p.healths == 0, "healthz requests", p.healths, p.methods())

	p.resetScope()
	goal := call(base(), "goal", "write the quarterly diff", "--project", "proj-probe",
		"--expected-revision", "7", "--writer-epoch", "2", "--draft")
	env := envelopeWithMethod(p.seen, "goal.start")
	ok("W0503-GOAL-SENDS-GOAL-START", goal.code == 0 && str(env["method"]) == "goal.start" &&
		str(payloadOf(env)["objective"]) == "write the quarterly diff" && str(env["project_id"]) == "proj-probe" &&
		env["session_id"] == nil && env["expected_revision"] == nil && env["writer_epoch"] == nil,
		"code", goal.code, "envelope", env, "stdout", clipOut(goal.stdout))
	missingGoal := call(base(), "goal")
	ok("W0503-GOAL-WITHOUT-OBJECTIVE-IS-USAGE-ERROR", missingGoal.code == 2 && str(jsonOf(missingGoal)["reason"]) == "MISSING_OBJECTIVE", jsonOf(missingGoal))
	p.resetScope()
	aliasGoal := call(base(), "go", "check the citations", "--draft", "--expected-revision", "1", "--writer-epoch", "1")
	aliasEnvelope := envelopeWithMethod(p.seen, "goal.start")
	ok("W0503-GO-ALIASES-GOAL-START", aliasGoal.code == 0 && str(aliasEnvelope["method"]) == "goal.start" && str(payloadOf(aliasEnvelope)["objective"]) == "check the citations", jsonOf(aliasGoal))

	p.resetScope()
	resume := call(base(), "resume", "--session", "sess-42", "--writer-epoch", "5", "--after-sequence", "11")
	attachEnv := envelopeWithMethod(p.seen, "session.attach")
	controlEnv := envelopeWithMethod(p.seen, "session.control")
	ok("W0503-RESUME-SENDS-SESSION-ATTACH", resume.code == 0 &&
		str(attachEnv["session_id"]) == "sess-42" && str(attachEnv["writer_epoch"]) == "5" &&
		payloadOf(attachEnv)["request_write_owner"] == false && str(payloadOf(attachEnv)["after_sequence"]) == "11" &&
		str(payloadOf(controlEnv)["action"]) == "RESUME" && str(payloadOf(controlEnv)["target_id"]) == "sess-42",
		"code", resume.code, "attach", attachEnv, "control", controlEnv)
	ok("W0503-RESUME-WITHOUT-EPOCH-IS-USAGE-ERROR", func() bool {
		r := call(base(), "resume", "--session", "sess-42")
		return r.code == 2 && str(jsonOf(r)["reason"]) == "MISSING_WRITER_EPOCH"
	}(), jsonOf(call(base(), "resume", "--session", "s")))
	ok("W0503-RESUME-WITHOUT-SESSION-IS-USAGE-ERROR", func() bool {
		r := call(base(), "resume", "--writer-epoch", "5")
		return r.code == 2 && str(jsonOf(r)["reason"]) == "MISSING_SESSION_REFERENCE"
	}(), "")

	p.resetScope()
	cancel := call(base(), "cancel", "--run", "run-9", "--session", "sess-42", "--expected-revision", "2",
		"--writer-epoch", "5", "--reason", "user asked from the CLI")
	ok("W0503-CANCEL-SENDS-SESSION-CONTROL", cancel.code == 0 && str(p.last()["method"]) == "session.control" &&
		str(payloadOf(p.last())["action"]) == "CANCEL" && str(payloadOf(p.last())["target_id"]) == "run-9",
		"code", cancel.code, "envelope", p.last())
	ok("W0503-CANCEL-WITHOUT-RUN-IS-USAGE-ERROR", func() bool {
		r := call(base(), "cancel")
		return r.code == 2 && str(jsonOf(r)["reason"]) == "MISSING_RUN_REFERENCE"
	}(), "")

	slashRows := []struct{ verb, want string }{{"/status", "host.status"},
		{"/goal", "goal.start"}, {"/resume", "session.attach"}, {"/cancel", "session.control"}}
	slashArgs := map[string][]string{
		"/status": {},
		"/goal":   {"objective", "--draft", "--expected-revision", "1", "--writer-epoch", "1"},
		"/resume": {"--session", "sess-1", "--writer-epoch", "1"},
		"/cancel": {"--run", "run-1", "--expected-revision", "1", "--writer-epoch", "1"},
	}
	for _, row := range slashRows {
		p.resetScope()
		r := call(base(), append([]string{row.verb}, slashArgs[row.verb]...)...)
		label := "W0503-SLASH-" + strings.ToUpper(strings.TrimPrefix(row.verb, "/")) + "-SENDS-" +
			strings.ToUpper(strings.ReplaceAll(row.want, ".", "-"))
		ok(label, r.code == 0 && hasMethod(p.methods(), row.want), "code", r.code, "saw", p.methods())
	}

	// The exit code follows the host's reply. This is the half the review caught: a stub could exit 0 because it
	// never asked the host anything, so a refusing host must produce a non-zero CLI.
	p.resetScope()
	p.mode = "rejected"
	bad := call(base(), "status")
	ok("W0503-STATUS-EXIT-FOLLOWS-THE-HOST-REPLY", bad.code == 3 &&
		strings.Contains(str(jsonOf(bad)["reason"]), "HOST_REJECTED:WRITER_BUSY"), "code", bad.code, jsonOf(bad))
	p.mode = "notimplemented"
	ni := call(base(), "status")
	ok("W0503-HOST-NOT-IMPLEMENTED-IS-NOT-EXIT-ZERO", ni.code == 3 &&
		strings.Contains(str(jsonOf(ni)["reason"]), "HOST_REJECTED:NOT_IMPLEMENTED"), "code", ni.code, jsonOf(ni))
	p.mode = "malformed"
	mal := call(base(), "status")
	ok("W0503-MALFORMED-HOST-REPLY-FAILS", mal.code == 1 && str(jsonOf(mal)["reason"]) == "MALFORMED_REPLY",
		"code", mal.code, jsonOf(mal))
	p.mode = "complete"

	// A host that answers with an HTTP error and no protocol status is not a completed command.
	deadProbe, derr := newProbe("http500")
	if derr != nil {
		skip("W0503-HOST-HTTP-500-IS-NOT-A-COMPLETION", "second loopback listener refused: "+derr.Error())
	} else {
		defer deadProbe.close()
		writeDisc(deadProbe.url)
		http500 := call(base(), "status")
		ok("W0503-HOST-HTTP-500-IS-NOT-A-COMPLETION", http500.code == 1 &&
			strings.HasPrefix(str(jsonOf(http500)["reason"]), "HOST_HTTP_500"), "code", http500.code,
			jsonOf(http500))
		writeDisc(p.url)
	}

	// No credential is not a silent retry: the CLI never invents a bearer token.
	p.resetScope()
	p.healths = 0
	nocred := call(append([]string{}, envWithout(base(),
		"RESEARCHOS_CLI_CREDENTIAL")...), "status")
	ok("W0503-NO-CREDENTIAL-REFUSES-WITHOUT-PRETENDING", nocred.code == 3 &&
		str(jsonOf(nocred)["reason"]) == "CREDENTIAL_ABSENT" && len(p.methods()) == 0,
		"code", nocred.code, "saw", p.methods())

	// doctor, version and task: the rows the review proved were absent (deleting doctor left every row green).
	deadDisc := filepath.Join(contractRunDir, "w0503_v2_absent.json")
	_ = os.Remove(deadDisc)
	nf := call(append(base(), "RESEARCHOS_CLI_DISCOVERY="+deadDisc), "doctor")
	ok("W0503-DOCTOR-NOT-FOUND-REFUSES", nf.code == 3 && str(jsonOf(nf)["reason"]) == "NOT_FOUND",
		"code", nf.code, jsonOf(nf))
	p.mode = "unhealthy"
	down := call(base(), "doctor")
	// product.contract maps an unhealthy host to 1 (execution_or_check_failed). The accepted W02-03 launcher shipped
	// 4 here, which is not in the contract's map; this card owns CLI/** and its action names the code set, so the
	// code is corrected and the superseded sentence is recorded in doctor_exit_code_correction.json.
	ok("W0503-DOCTOR-DOWN-EXIT-1", down.code == 1 && str(jsonOf(down)["health"]) == "DOWN" &&
		str(jsonOf(down)["http_code"]) == "503" && str(jsonOf(down)["status"]) == "REJECTED",
		"code", down.code, jsonOf(down))
	p.mode = "complete"
	up := call(base(), "doctor")
	ok("W0503-DOCTOR-UP-COMPLETES", up.code == 0 && str(jsonOf(up)["health"]) == "UP" &&
		str(jsonOf(up)["status"]) == "COMPLETED", "code", up.code, jsonOf(up))
	// doctor honours the same discovery path as the verbs: the review measured it ignoring the variable.
	ok("W0503-DOCTOR-HONOURS-DISCOVERY-ENV", strings.Contains(str(jsonOf(nf)["detail"]), "w0503_v2_absent.json"),
		jsonOf(nf))

	v := call(base(), "version")
	ok("W0503-VERSION-IS-ONE-COMPLETED-RECORD", v.code == 0 && len(nonEmpty(v.stdout)) == 1 &&
		str(jsonOf(v)["status"]) == "COMPLETED" && str(jsonOf(v)["protocol"]) == "researchos-client/2",
		"code", v.code, "stdout", clipOut(v.stdout))

	tk := call(base(), "task")
	ok("W0503-TASK-VERB-REACHES-THE-ACCEPTED-RUNNER", tk.code != 3 &&
		!strings.Contains(tk.stdout, "NOT_IMPLEMENTED"), "code", tk.code, "stdout", clipOut(tk.stdout))

	// Model switching, split so each half of the gate is reachable: the flag, then the recorded settled run,
	// then the positive control that actually changes the model.
	p.configurePhase = true
	p.configureRevision = 3
	writeCfg(`{"config_revision":3,"model":"vendor/old","settled_run_id":"run-settled","workspace_ref":"D:/ws","project_id":"proj-probe","session_id":"sess-strict","session_revision":7,"writer_epoch":2}`)
	noFlag := call(base(), "config", "set-model", "--model", "vendor/new", "--config-revision", "3")
	ok("W0503-MODEL-CHANGE-NEEDS-SETTLED-FLAG", noFlag.code == 1 &&
		str(jsonOf(noFlag)["reason"]) == "SETTLED_FLAG_REQUIRED", "code", noFlag.code, jsonOf(noFlag))
	writeCfg(`{"config_revision":3,"model":"vendor/old","workspace_ref":"D:/ws","project_id":"proj-probe","session_id":"sess-strict","session_revision":7,"writer_epoch":2}`)
	noRun := call(base(), "config", "set-model", "--model", "vendor/new", "--config-revision", "3", "--settled")
	ok("W0503-MODEL-CHANGE-NEEDS-SETTLED-RUN-RECORDED", noRun.code == 1 &&
		str(jsonOf(noRun)["reason"]) == "SETTLED_RUN_UNRECORDED" &&
		strings.Contains(str(jsonOf(noRun)["detail"]), "settle-run"), "code", noRun.code, jsonOf(noRun))
	rec := call(base(), "config", "settle-run", "--run", "run-verified")
	ok("W0503-SETTLE-RUN-RECORDS-THE-CONFIRMATION", rec.code == 0 &&
		str(jsonOf(rec)["settled_run_id"]) == "run-verified" &&
		str(jsonOf(rec)["settled_run_source"]) == "recorded by the caller; the host session state remains the authority",
		jsonOf(rec))
	// The endpoint/credential refusal runs before the successful switch, whose revision bump would otherwise make
	// this same input stale for a legitimate reason and measure the wrong gate.
	p.resetScope()
	noFields := call(base(), "config", "set-model", "--model", "vendor/new", "--config-revision", "3", "--settled")
	ok("W0503-MODEL-CHANGE-REFUSES-WITHOUT-ENDPOINT-OR-CREDENTIAL", noFields.code == 2 &&
		str(jsonOf(noFields)["reason"]) == "MISSING_CONFIGURE_FIELDS", "code", noFields.code, jsonOf(noFields))
	showAfterRefusal := call(base(), "config", "show")
	ok("W0503-REFUSED-SWITCH-LEAVES-THE-PREVIOUS-MODEL", showAfterRefusal.code == 0 &&
		str(jsonOf(showAfterRefusal)["config"].(map[string]any)["model"]) == "vendor/old" &&
		str(jsonOf(showAfterRefusal)["config"].(map[string]any)["config_revision"]) == "3",
		"code", showAfterRefusal.code, jsonOf(showAfterRefusal))
	done := call(base(), "config", "set-model", "--model", "vendor/new", "--config-revision", "3", "--settled",
		"--base-url", "https://provider.invalid", "--credential-ref", "cred-1", "--writer-epoch", "2",
		"--expected-revision", "7", "--project", "proj-probe")
	ok("W0503-SETTLED-MODEL-CHANGE-SENDS-HOST-CONFIGURE", done.code == 0 &&
		str(p.last()["method"]) == "host.configure" && str(jsonOf(done)["method_sent"]) == "host.configure" &&
		str(payloadOf(p.last())["model_id"]) == "new" &&
		str(p.last()["writer_epoch"]) == "2",
		"code", done.code, "envelope", p.last(), jsonOf(done))
	ok("W0503-MODEL-CHANGE-CARRIES-THE-OBSERVED-EPOCH", str(p.last()["writer_epoch"]) == "2" &&
		p.last()["writer_epoch"] != nil,
		"a model switch without writer_epoch is refused by the core itself (client_protocol.go:152), so the field has "+
			"to be on the wire; the round-2 review captured 5/5 envelopes with it absent", "envelope", p.last())
	after := call(base(), "config", "show")
	ok("W0503-SETTLED-MODEL-CHANGE-COMPLETES", done.code == 0 &&
		str(jsonOf(done)["model"]) == "mc-probe-opaque-4" && str(jsonOf(after)["config"].(map[string]any)["model"]) == "mc-probe-opaque-4",
		"code", done.code, jsonOf(done), jsonOf(after))
	// And the mirror: with no epoch anywhere the CLI refuses before the request is built, so a switch can neither
	// land silently nor arrive at the host as an unexplained rejection.
	p.resetScope()
	writeCfg(`{"config_revision":4,"model":"mc-probe-opaque-4","workspace_ref":"D:/ws","project_id":"proj-probe","session_id":"sess-strict","session_revision":7,` +
		`"settled_run_id":"run-verified"}`)
	noEpoch := call(base(), "config", "set-model", "--model", "vendor/other", "--config-revision", "4", "--settled",
		"--base-url", "https://provider.invalid", "--credential-ref", "cred-1", "--expected-revision", "7",
		"--project", "proj-probe")
	stillOld := call(base(), "config", "show")
	ok("W0503-MODEL-CHANGE-WITHOUT-EPOCH-REFUSES-BEFORE-THE-HOST", noEpoch.code == 2 &&
		str(jsonOf(noEpoch)["reason"]) == "MODEL_CHANGE_WITHOUT_EPOCH" && len(p.seen) == 0 &&
		str(jsonOf(stillOld)["config"].(map[string]any)["model"]) == "mc-probe-opaque-4",
		"code", noEpoch.code, jsonOf(noEpoch), "envelopes", len(p.seen), jsonOf(stillOld))
	// The strict fixture validates the envelope instead of answering a method name. The same verbs that pass
	// against the agreeable host are re-driven against one that mirrors DecodeEnvelope, so a stripped CAS field, a
	// wrong protocol version or a blank command id has to survive an actual refusal rather than a polite echo.
	p.mode = "strict"
	p.resetScope()
	writeCfg(`{"config_revision":3,"model":"vendor/old","settled_run_id":"run-strict","workspace_ref":"D:/ws",` +
		`"project_id":"proj-probe","session_id":"sess-strict","session_revision":7,"writer_epoch":2}`)
	stStrict := call(base(), "status", "--session", "sess-strict")
	ok("W0503-STATUS-COMPLETES-AGAINST-THE-STRICT-HOST", stStrict.code == 0 && len(p.seen) > 0 &&
		fmt.Sprint(jsonOf(stStrict)["exit_code"]) == "0", "code", stStrict.code, jsonOf(stStrict))
	goStrict := call(base(), "go", "check the citations against a validating host", "--expected-revision", "7",
		"--writer-epoch", "2", "--draft")
	strictGoalEnv := envelopeWithMethod(p.seen, "goal.start")
	ok("W0503-GOAL-CARRIES-ALL-CAS-FIELDS-ON-THE-WIRE", goStrict.code == 0 &&
		strictGoalEnv["expected_revision"] == float64(7) && strictGoalEnv["writer_epoch"] == float64(2) &&
		fmt.Sprint(p.last()["project_id"]) == "proj-probe" &&
		fmt.Sprint(p.last()["protocol_version"]) == "researchos-client/2",
		"code", goStrict.code, "envelope", p.last(), jsonOf(goStrict))

	// And the status the agreeable fixture never emits: a host that has accepted the command but has not settled
	// it is neither a failure nor a completion. R2-M2 (IN_PROGRESS turned into a failure) survived because this
	// probe had no such mode at all, so the row could only ever grade COMPLETED, REJECTED and NOT_IMPLEMENTED.
	p.mode = "inprogress"
	p.resetScope()
	ip := call(base(), "status")
	ok("W0503-IN-PROGRESS-IS-ACCEPTED-NOT-FAILED", ip.code == 1 && len(p.seen) > 0 && str(jsonOf(ip)["reason"]) == "INVALID_REPLY_SCHEMA",
		"code", ip.code, jsonOf(ip), "stderr", clipOut(ip.stderr))
	p.mode = "ack"
	p.ackCalls = 0
	legalPending := call(base(), "status")
	ok("W0503-LEGAL-ACK-REPLAYS-ORIGINAL-COMMAND", legalPending.code == 0 && p.ackCalls >= 2, "FIXTURE_PROTOCOL only", jsonOf(legalPending))
	p.mode = "complete"
	// The strict and in-progress rows above rewrite this phase's config, and the interactive phase further down
	// inherits whatever the file holds, so the previous content is restored here rather than left for a later row
	// to trip over. A phase that changes shared state owes the next phase the state it found.
	writeCfg(`{"config_revision":4,"model":"vendor/new","workspace_ref":"D:/ws","project_id":"proj-probe",` +
		`"settled_run_id":"run-verified"}`)

	// Every leg the command table claims must have been observed on the wire by this point. The table is printed
	// by the CLI, so the claim and the traffic are two different sources and one cannot quietly become the other:
	// this is the row that grades "the verb performs the operation" instead of "the row says it does".
	legs := []string{"session.get", "host.status", "session.attach", "session.control", "goal.start", "host.configure"}
	unseen := []string{}
	for _, m := range legs {
		if wireMethods[m] == 0 {
			unseen = append(unseen, m)
		}
	}
	ok("W0503-EVERY-CLAIMED-OPERATION-LEG-WAS-OBSERVED-ON-THE-WIRE", len(unseen) == 0,
		"unseen", strings.Join(unseen, ","), "wire", fmt.Sprint(wireMethods),
		"scope", "the verbs driven by this point in the phase; run/interactive/init/workspace legs are graded by "+
			"their own hasOp rows later in the same phase")

	// init's contract operation is project.bootstrap, so a host has to be present for the command to complete.
	p.resetScope()
	initWs := filepath.Join(contractRunDir, "w0503 init 工作区 space")
	_ = os.MkdirAll(initWs, 0o700)
	defer os.RemoveAll(initWs)
	boot := call(base(), "init", initWs)
	bootEnv := p.last()
	ok("W0503-INIT-BOOTSTRAPS-PROJECT-WITH-HOST", boot.code == 0 &&
		str(bootEnv["method"]) == "project.bootstrap" &&
		str(payloadOf(bootEnv)["authorized_workspace_ref"]) == filepath.Clean(initWs) &&
		str(jsonOf(boot)["project_id"]) != "", "code", boot.code, "envelope", bootEnv, jsonOf(boot))

	// run carries two meanings: the accepted W05-02 cascade and the contract's prompt command. This is the second.
	p.resetScope()
	runCmd := call(base(), "run", "draft the citation audit", "--project", "proj-probe", "--session", "sess-probe",
		"--expected-revision", "7", "--writer-epoch", "2", "--output", "jsonl")
	ok("W0503-RUN-SENDS-SESSION-SEND-AND-EVENTS", runCmd.code == 0 &&
		hasMethod(p.methods(), "session.send") && hasMethod(p.methods(), "session.events") && str(jsonOf(runCmd)["status"]) == "EXECUTION_REPORTED",
		"code", runCmd.code, "methods", p.methods(), jsonOf(runCmd))
	badOutput := call(base(), "run", "x", "--project", "p", "--session", "s", "--expected-revision", "1",
		"--writer-epoch", "1", "--output", "text")
	ok("W0503-RUN-REJECTS-NON-JSONL-OUTPUT", badOutput.code == 2 &&
		str(jsonOf(badOutput)["reason"]) == "OUTPUT_FORMAT_UNSUPPORTED", "code", badOutput.code, jsonOf(badOutput))

	// The contract's interactive entry: session.list, then create or attach, then one send per stdin line.
	p.resetScope()
	writeCfg(`{"config_revision":4,"model":"mc-probe-opaque-4","workspace_ref":"ws-protocol-fixture","project_id":"proj-probe"}`)
	inter := callProbeMessages(repo, bin, base(), []string{"first question\n", "second question\n"})
	ok("W0503-INTERACTIVE-SENDS-LIST-CREATE-SEND", inter.code == 0 &&
		hasMethod(p.methods(), "session.list") && hasMethod(p.methods(), "session.create") && countProbeMethod(p.seen, "session.send") == 2 &&
		str(jsonOf(inter)["session_id"]) == "sess-created-1" &&
		countCommandSummaries(inter, "run", "EXECUTION_REPORTED") == 2, "code", inter.code, "methods", p.methods(),
		jsonOf(inter))
	p.resetScope()
	attachOnly := callWithStdin(base(), "hello\n", "--session", "sess-given", "--writer-epoch", "4",
		"--expected-revision", "7", "--project", "proj-probe")
	ok("W0503-INTERACTIVE-ATTACHES-WHEN-A-SESSION-IS-GIVEN", attachOnly.code == 0 &&
		hasMethod(p.methods(), "session.list") && hasMethod(p.methods(), "session.attach") && countProbeMethod(p.seen, "session.send") == 1 && payloadOf(envelopeWithMethod(p.seen, "session.attach"))["request_write_owner"] == false &&
		str(jsonOf(attachOnly)["session_id"]) == "sess-given", "methods", p.methods(), jsonOf(attachOnly))
	noHostEnv := append(envWithout(base(), "RESEARCHOS_CLI_DISCOVERY"),
		"RESEARCHOS_CLI_DISCOVERY="+filepath.Join(contractRunDir, "no_such_host.json"))
	noHost := callWithStdin(noHostEnv, "hi\n")
	ok("W0503-INTERACTIVE-WITHOUT-HOST-REFUSES", noHost.code == 3 &&
		str(jsonOf(noHost)["reason"]) == "INTERACTIVE_HOST_UNAVAILABLE", "code", noHost.code, jsonOf(noHost))
	p.resetScope()
	noCred := callWithStdin(envWithout(base(), "RESEARCHOS_CLI_CREDENTIAL"), "hi\n")
	ok("W0503-INTERACTIVE-REFUSES-WITHOUT-CREDENTIAL", noCred.code == 3 &&
		str(jsonOf(noCred)["reason"]) == "CREDENTIAL_ABSENT" && len(p.methods()) == 0, "code", noCred.code,
		p.methods(), jsonOf(noCred))

	// A switch the host itself refuses must not have changed the local configuration. The CLI-side gate refusal is
	// covered elsewhere; this is the branch that only a live answer can reach.
	p.mode = "configure-busy"
	p.configurePhase = true
	p.configureRevision = 3
	p.resetScope()
	writeCfg(`{"config_revision":3,"model":"vendor/old","settled_run_id":"run-settled","workspace_ref":"D:/ws",` +
		`"project_id":"proj-probe","session_id":"sess-probe","session_revision":7,"writer_epoch":2}`)
	hostRefused := call(base(), "config", "set-model", "--model", "vendor/sneaky", "--config-revision", "3",
		"--settled", "--base-url", "https://provider.invalid", "--credential-ref", "cred-1", "--writer-epoch", "2",
		"--expected-revision", "7", "--project", "proj-probe")
	afterRefusal := call(base(), "config", "show")
	shownAfter, _ := jsonOf(afterRefusal)["config"].(map[string]any)
	ok("W0503-HOST-REFUSED-SWITCH-LEAVES-THE-PREVIOUS-MODEL", hostRefused.code == 1 &&
		str(shownAfter["model"]) == "vendor/old" && str(shownAfter["config_revision"]) == "3" &&
		str(p.last()["method"]) == "host.configure" && str(jsonOf(hostRefused)["reason"]) == "HOST_REJECTED:SESSION_BUSY",
		"code", hostRefused.code, jsonOf(hostRefused), shownAfter)
	p.mode = "complete"

	// No reply other than a create may decide which session the CLI is talking about.
	subProbe, serr := newProbe("identity-substitution")
	if serr != nil {
		skip("W0503-INTERACTIVE-NEVER-SUBSTITUTES-THE-CREATED-SESSION", "listener refused: "+serr.Error())
	} else {
		writeDisc(subProbe.url)
		// The previous block records a session in the configuration on purpose, so this flow starts from one
		// that names none: otherwise the CLI is right to keep the caller session and the substitution is not
		// being measured at all.
		writeCfg(`{"config_revision":3,"model":"vendor/old","settled_run_id":"run-settled","workspace_ref":"D:/ws",` +
			`"project_id":"proj-probe"}`)
		sub := callWithStdin(base(), "continue the audit\n")
		ok("W0503-INTERACTIVE-NEVER-SUBSTITUTES-THE-CREATED-SESSION", sub.code == 0 &&
			str(jsonOf(sub)["session_id"]) == "sess-created-1" &&
			strings.HasPrefix(strings.Join(subProbe.methods(), ","), "session.list,session.create"),
			"code", sub.code, "methods", subProbe.methods(), jsonOf(sub))
		writeDisc(p.url)
		subProbe.close()
	}

	// The protocol table cannot drift from the published schema, and the two clients must agree.
	cmds := jsonOf(call(base(), "commands"))
	ok("W0503-CLI-METHOD-TABLE-MATCHES-THE-FROZEN-SCHEMA", schemaMatchesCLI(repo, cmds),
		"see W0503-CLI-METHOD-TABLE-MATCHES-THE-FROZEN-SCHEMA detail in the schema comparison")
	ok("W0503-CLI-TABLE-AND-DESKTOP-V2-AGREE", desktopAgrees(repo, cmds), "compared the two client tables")
}

func hasMethod(methods []string, want string) bool {
	for _, m := range methods {
		if m == want {
			return true
		}
	}
	return false
}

func hasOp(record map[string]any, method, status string) bool {
	for _, e := range asList(record["operations"]) {
		row, _ := e.(map[string]any)
		if str(row["method"]) == method && str(row["status"]) == status {
			return true
		}
	}
	return false
}

// envelopeWithMethod finds the command a multi-step verb sent by its method rather than by its position, because a
// two-operation command legitimately sends more than one envelope and "the last one" certifies nothing.
func envelopeWithMethod(seen []map[string]any, method string) map[string]any {
	for _, e := range seen {
		if str(e["method"]) == method {
			return e
		}
	}
	return map[string]any{}
}

func jsonNull(s string) string {
	if s == "" {
		return "null"
	}
	return `"` + s + `"`
}

func envWithout(env []string, key string) []string {
	out := []string{}
	for _, e := range env {
		if !strings.HasPrefix(e, key+"=") {
			out = append(out, e)
		}
	}
	return out
}

// schemaMatchesCLI compares the table the CLI reports with the published x-method-contracts block, key by key.
func schemaMatchesCLI(repo string, cmds map[string]any) bool {
	raw, err := os.ReadFile(filepath.Join(repo, "internal", "api", "contracts", "client.protocol.schema.json"))
	if err != nil {
		return false
	}
	var s struct {
		MethodContracts map[string]struct {
			Payload string `json:"payload"`
			Result  string `json:"result"`
		} `json:"x-method-contracts"`
		Defs map[string]struct {
			Required []string `json:"required"`
		} `json:"$defs"`
	}
	if e := json.Unmarshal(raw, &s); e != nil {
		return false
	}
	methods, _ := cmds["protocol_methods"].(map[string]any)
	if len(methods) != len(s.MethodContracts) || len(methods) != 23 {
		return false
	}
	for name, want := range s.MethodContracts {
		got, has := methods[name].(map[string]any)
		if !has {
			return false
		}
		if str(got["payload"]) != want.Payload || str(got["result"]) != want.Result {
			return false
		}
		req := []string{}
		if list, isList := got["required"].([]any); isList {
			for _, x := range list {
				req = append(req, fmt.Sprint(x))
			}
		}
		wantReq := append([]string{}, s.Defs[want.Payload].Required...)
		sort.Strings(wantReq)
		sort.Strings(req)
		if strings.Join(wantReq, ",") != strings.Join(req, ",") {
			return false
		}
	}
	return true
}

// desktopAgrees reads the desktop client's CONTRACT literal textually: two hand-maintained copies of one frozen
// contract must be checked against each other, because nothing else in the repository would notice them diverge.
func desktopAgrees(repo string, cmds map[string]any) bool {
	raw, err := os.ReadFile(filepath.Join(repo, "apps", "desktop", "main", "lib", "v2.js"))
	if err != nil {
		return false
	}
	text := string(raw)
	methods, _ := cmds["protocol_methods"].(map[string]any)
	for name := range methods {
		quoted := "'" + name + "'"
		if !strings.Contains(text, quoted) {
			return false
		}
		m := payloadNameFor(text, name)
		if m == "" || m != str(methods[name].(map[string]any)["payload"]) {
			return false
		}
	}
	// No extra method on the desktop side: the sets must be equal, not merely compatible.
	count := 0
	for _, line := range strings.Split(text, "\n") {
		if strings.Contains(line, "{ payload: '") {
			count++
		}
	}
	return count == len(methods)
}

func payloadNameFor(text, method string) string {
	for _, line := range strings.Split(text, "\n") {
		if strings.Contains(line, "'"+method+"'") && strings.Contains(line, "payload:") {
			i := strings.Index(line, "payload: '")
			if i < 0 {
				return ""
			}
			rest := line[i+len("payload: '"):]
			j := strings.Index(rest, "'")
			if j < 0 {
				return ""
			}
			return rest[:j]
		}
	}
	return ""
}

func probeResponse(env map[string]any, status string, result any, code string) map[string]any {
	reply := map[string]any{"protocol_version": "researchos-client/2", "command_id": env["command_id"], "method": env["method"], "session_id": env["session_id"], "revision": nil, "status": status, "error_code": nil, "error": nil, "result": result}
	if code != "" {
		reply["error_code"] = code
		reply["error"] = map[string]any{"code": code, "message": "FIXTURE_PROTOCOL refusal", "retryable": false, "recovery": "STOP_AND_REPORT", "current_revision": nil, "current_writer_epoch": nil, "resource_request_id": nil, "retry_after_ms": nil, "correlation_id": env["command_id"]}
	}
	return reply
}
func (p *probe) snapshot(env map[string]any, sid string) map[string]any {
	var goal, status, run any
	if p.activeGoal != "" {
		goal, status = p.activeGoal, "BLOCKED"
	}
	if p.fixtureSession == sid && p.fixtureRun != "" {
		status, run = "ACTIVE", p.fixtureRun
	}
	return map[string]any{"protocol_version": "researchos-client/2", "session_id": sid, "project_id": env["project_id"], "workspace_ref": "ws-protocol-fixture", "native_session_ref": "native-protocol-fixture", "core_build_id": "fixture-build", "revision": 7, "title": "Protocol fixture", "archived_at": nil, "created_at": "2026-10-05T12:00:00Z", "updated_at": "2026-10-05T12:00:00Z", "model_config_ref": "model-protocol-fixture", "goal_id": goal, "goal_status": status, "active_run_id": run, "run_status": nil, "writer": map[string]any{"client_id": env["client_id"], "epoch": 2, "expires_at": time.Now().Add(time.Hour).UTC().Format(time.RFC3339Nano)}, "event_sequence": len(p.fixtureEvents), "earliest_event_sequence": 0, "checkpoint_artifact_ref": nil, "pending_command_ids": []any{}, "pending_permissions": []any{}, "resume_requires_explicit_user": false, "messages": []any{}, "transcript_artifact_ref": nil, "has_earlier_messages": false}
}

// Explicit finite protocol transcript. These public fixture records test CLI
// correlation only; they are never evidence of real MODEL/TOOL execution.
func (p *probe) installFiniteTranscript(env map[string]any, sid string) {
	p.fixtureProject, _ = env["project_id"].(string)
	p.fixtureSession = sid
	p.activeGoal = fmt.Sprintf("goal-message-%d", p.admittedMessages)
	p.fixtureTask = fmt.Sprintf("task-message-%d", p.admittedMessages)
	p.fixtureRun = fmt.Sprintf("run-message-%d", p.admittedMessages)
	p.fixtureArtifact = fmt.Sprintf("artifact-message-%d", p.admittedMessages)
	appendEvent := func(kind string, payload map[string]any) {
		n := len(p.fixtureEvents) + 1
		p.fixtureEvents = append(p.fixtureEvents, map[string]any{"event_id": fmt.Sprintf("fixture-event-%d", n), "session_id": sid, "sequence": n, "core_build_id": "fixture-build", "protocol_version": "researchos-client/2", "run_id": p.fixtureRun, "command_id": env["command_id"], "domain_event_id": nil, "kind": kind, "payload": payload})
	}
	appendEvent("ARTIFACT", map[string]any{"artifact_ref": map[string]any{"entity_type": "Artifact", "id": p.fixtureArtifact, "revision": 1, "content_hash": "sha256:" + strings.Repeat("a", 64)}, "availability": "AVAILABLE"})
	appendEvent("RUN_STATE", map[string]any{"run_id": p.fixtureRun, "status": "SETTLED", "revision": 1, "children_stopped": true, "queue_empty": true, "cancel_requested_at": nil, "cancel_confirmed_at": nil, "settled_at": "2026-10-05T12:00:00Z"})
}

func (p *probe) resetScope() {
	p.seen = nil
	p.activeGoal, p.fixtureProject, p.fixtureSession, p.fixtureRun, p.fixtureTask, p.fixtureArtifact = "", "", "", "", "", ""
	p.fixtureEvents = nil
	p.admittedMessages = 0
}
func countProbeMethod(rows []map[string]any, method string) int {
	n := 0
	for _, r := range rows {
		if r["method"] == method {
			n++
		}
	}
	return n
}
func countCommandSummaries(r run, command, status string) int {
	n := 0
	for _, line := range nonEmpty(r.stdout) {
		var row map[string]any
		if json.Unmarshal([]byte(line), &row) == nil && row["command"] == command && row["status"] == status {
			n++
		}
	}
	return n
}

// Deliver the next logical question only after the previous CLI summary, while
// stdin remains open. A completed protocol fixture turn is not a real model run.
func callProbeMessages(repo, binary string, env, messages []string) run {
	ctx, stop := context.WithTimeout(context.Background(), 30*time.Second)
	defer stop()
	cmd := exec.CommandContext(ctx, binary)
	cmd.Dir, cmd.Env = repo, env
	in, err := cmd.StdinPipe()
	if err != nil {
		return run{code: -1, err: err}
	}
	out, err := cmd.StdoutPipe()
	if err != nil {
		in.Close()
		return run{code: -1, err: err}
	}
	var stdout, stderr strings.Builder
	cmd.Stderr = &stderr
	if err = cmd.Start(); err != nil {
		in.Close()
		return run{code: -1, err: err}
	}
	summaries := make(chan int, len(messages)+1)
	done := make(chan struct{})
	go func() {
		defer close(done)
		scanner := bufio.NewScanner(out)
		scanner.Buffer(make([]byte, 4096), 1<<20)
		for scanner.Scan() {
			line := scanner.Text()
			stdout.WriteString(line + "\n")
			var row map[string]any
			if json.Unmarshal([]byte(line), &row) == nil && row["command"] == "run" {
				if code, ok := row["exit_code"].(float64); ok {
					summaries <- int(code)
				}
			}
		}
	}()
messagesLoop:
	for _, message := range messages {
		if _, err = io.WriteString(in, message); err != nil {
			break
		}
		select {
		case code := <-summaries:
			if code != 0 {
				break messagesLoop
			}
		case <-done:
			break messagesLoop
		case <-ctx.Done():
			break messagesLoop
		}
	}
	in.Close()
	<-done
	err = cmd.Wait()
	code := 0
	if ee, ok := err.(*exec.ExitError); ok {
		code = ee.ExitCode()
	} else if err != nil {
		code = -1
	}
	recordContractChild(cmd, stdout.String(), stderr.String(), code)
	return run{stdout.String(), stderr.String(), code, err}
}
