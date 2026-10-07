package domain

import (
	"bytes"
	"context"
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	rt "researchos.local/research-os/adapters/runtime"
	"strings"
	"testing"
	"time"

	"golang.org/x/sys/windows"
)

// Fail closed on non-message items except CLI diagnostics; errors cannot supply a successful result.
func c01ToolEvent(raw []byte) bool {
	for _, line := range bytes.Split(raw, []byte("\n")) {
		var event Object
		if json.Unmarshal(line, &event) != nil {
			continue
		}
		if item, ok := event["item"].(map[string]any); ok {
			if item["type"] != "agent_message" && item["type"] != "reasoning" && item["type"] != "error" {
				return true
			}
		}
		if strings.Contains(Str(event, "type"), "tool") {
			return true
		}
	}
	return false
}

func TestW06NoToolMonitor(t *testing.T) {
	for _, kind := range []string{"command_execution", "mcp_tool_call", "web_search", "file_change", "unknown"} {
		if !c01ToolEvent(Bytes(Object{"type": "item.started", "item": Object{"type": kind}})) {
			t.Fatal(kind)
		}
	}
	if c01ToolEvent([]byte(`{"type":"item.completed","item":{"type":"error","message":"CLI feature warning"}}`)) {
		t.Fatal("diagnostic is not a tool")
	}
	if c01ToolEvent([]byte(`{"type":"item.completed","item":{"type":"agent_message","text":"{}"}}`)) {
		t.Fatal("message is not a tool")
	}
}

func c01FreshAgent(t *testing.T, r *runtimeFixture, bundle Object, historical Object) (Object, Object) {
	t.Helper()
	if os.Getenv("RESEARCHOS_C01_MODEL") != "1" {
		t.Fatal("BLOCKED: C01 requires an explicitly enabled fresh model; deterministic oracle echo is not accepted")
	}
	f := r.f
	out, e := filepath.Abs(os.Getenv("W06_EVIDENCE_DIR"))
	if e != nil || os.Getenv("W06_EVIDENCE_DIR") == "" {
		t.Fatal("W06_EVIDENCE_DIR required")
	}
	write := func(name string, data []byte) {
		if e := os.WriteFile(filepath.Join(out, name), data, 0600); e != nil {
			t.Fatal(e)
		}
	}
	executable, e := exec.LookPath("codex.exe")
	if e != nil {
		t.Fatal(e)
	}
	binary, e := os.ReadFile(executable)
	if e != nil {
		t.Fatal(e)
	}
	const pin = "sha256:86e8ef1013f98df51fdeea446597f7e3ca32e454d1d4d8c0402a68b03c311d70"
	if rt.Hash(binary) != pin {
		t.Fatal("W06-only Codex 0.159.0 pin mismatch")
	}
	cliVersion, e := exec.Command(executable, "--version").Output()
	if e != nil {
		t.Fatal(e)
	}
	root := t.TempDir()
	workspace := filepath.Join(root, "workspace")
	manifest, e := f.s.MaterializeTaskContext(context.Background(), f.token, f.project, Str(r.task, "id"), workspace)
	if e != nil {
		t.Fatal(e)
	}
	inputs := Empty()
	for _, entry := range Arr(manifest, "input_manifest") {
		m := entry.(map[string]any)
		data, err := os.ReadFile(filepath.Join(workspace, Str(m, "path")))
		if err != nil || Digest(data) != m["content_hash"] {
			t.Fatal("materialized input hash", err)
		}
		inputs = append(inputs, Object{"manifest_entry": m, "content": string(data)})
	}
	records := []any{historical}
	tx, e := f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	for _, value := range Arr(bundle, "version_vector") {
		record, err := version(tx, f.project, value.(map[string]any))
		if err != nil {
			tx.Rollback()
			t.Fatal(err)
		}
		records = append(records, Object{"ref": value, "record": record})
	}
	tx.Rollback()
	payload := Object{"bundle": bundle, "manifest": manifest, "materialized_inputs": inputs, "records": records}
	prompt := "ResearchOS C01 fresh continuation. You have no prior conversation. Do not invoke ANY tools, read files, run shell, write files, browse or use network. All authorized information is supplied below. Identify the current Goal and unfinished Task, effective decision and superseded historical decision. Execute the task in the source content named continuation-arithmetic: use its operands and the CURRENT decision selected option (A means addition; B means multiplication). Calculate total yourself; the acceptance contract expected field is NOT the computation answer. Return operation as ADD or MULTIPLY, operands in source order, total, and source id/hash. Set candidate.result to verified only after completing the computation. If needed information is absent return actual requests in questions; never fabricate missing data. Output only the required JSON.\nINPUT:\n" + string(Bytes(payload))
	props := Object{}
	for _, key := range []string{"goal_id", "goal_intent", "next_task_id", "current_decision_id", "historical_decision_id", "source_id", "source_hash", "operation"} {
		props[key] = Object{"type": "string"}
	}
	for _, key := range []string{"current_decision_revision", "total"} {
		props[key] = Object{"type": "integer"}
	}
	props["operands"] = Object{"type": "array", "items": Object{"type": "integer"}}
	props["questions"] = Object{"type": "array", "items": Object{"type": "string"}}
	props["candidate"] = Object{"type": "object", "properties": Object{"result": Object{"type": "string"}}, "required": []any{"result"}, "additionalProperties": false}
	required := Empty()
	for key := range props {
		required = append(required, key)
	}
	schema := Bytes(Object{"type": "object", "properties": props, "required": required, "additionalProperties": false})
	schemaPath := filepath.Join(root, "output.schema.json")
	if e = os.WriteFile(schemaPath, schema, 0600); e != nil {
		t.Fatal(e)
	}
	// Match W05's credential boundary; no config, project identity, skills or history is copied.
	authBase, e := filepath.Abs(filepath.Join("..", "..", ".local", "runtime-auth"))
	if e != nil {
		t.Fatal(e)
	}
	if e = os.MkdirAll(authBase, 0700); e != nil {
		t.Fatal(e)
	}
	authHome, e := os.MkdirTemp(authBase, "c01-")
	if e != nil {
		t.Fatal(e)
	}
	dacl, e := rt.PrivateDirectory(authHome)
	if e != nil {
		t.Fatal(e)
	}
	t.Cleanup(func() { os.RemoveAll(authHome) })
	original := os.Getenv("CODEX_HOME")
	if original == "" {
		original = filepath.Join(os.Getenv("USERPROFILE"), ".codex")
	}
	auth, e := os.ReadFile(filepath.Join(original, "auth.json"))
	if e != nil {
		t.Fatal("authorized login unavailable")
	}
	if e = os.WriteFile(filepath.Join(authHome, "auth.json"), auth, 0600); e != nil {
		t.Fatal(e)
	}
	auth = nil
	sd, e := windows.GetNamedSecurityInfo(filepath.Join(authHome, "auth.json"), windows.SE_FILE_OBJECT, windows.DACL_SECURITY_INFORMATION)
	if e != nil {
		t.Fatal(e)
	}
	args := []string{"exec", "--json", "--ephemeral", "--ignore-user-config", "--ignore-rules", "--skip-git-repo-check", "--sandbox", "read-only", "--model", "gpt-6-luna", "-c", `model_reasoning_effort="low"`, "-c", `web_search="disabled"`, "-c", `skills.include_instructions=false`, "-c", `tools.update_plan.enabled=false`, "-c", `agents.enabled=false`}
	for _, name := range []string{"shell_tool", "unified_exec", "apps", "plugins", "browser_use", "browser_use_external", "computer_use", "image_generation", "view_image", "memories", "multi_agent", "multi_agent_v2", "skill_search", "hooks", "sleep_tool", "code_mode", "code_mode_only"} {
		args = append(args, "--disable", name)
	}
	args = append(args, "--cd", workspace, "--output-schema", schemaPath, "-")
	env := rt.Environment(authHome)
	envNames := Empty()
	for _, value := range env {
		envNames = append(envNames, strings.SplitN(value, "=", 2)[0])
	}
	command := Object{"argv": append([]string{executable}, args...), "cwd": workspace, "environment_names": envNames, "binary_hash": pin, "executor_version": strings.TrimSpace(string(cliVersion)), "configured_model": "gpt-6-luna", "reasoning_effort": "low", "provider_model_revision": nil, "cost": nil, "mode": "FRESH_MODEL_NO_OBSERVED_TOOLS", "input_hash": Hash(payload), "bundle_hash": Hash(bundle), "prompt_hash": Digest([]byte(prompt)), "credential_directory_dacl": dacl, "credential_file_dacl": sd.String(), "no_prior_session": true, "W05_qualification_changed": false}
	write("C01-input.json", Bytes(payload))
	write("C01-prompt.txt", []byte(prompt))
	write("C01-output.schema.json", schema)
	write("C01-command.json", Bytes(command))
	epoch, _ := Num(r.run, "lease_epoch")
	journalDir := filepath.Join(root, "journal")
	w, e := rt.Start(journalDir, rt.Spec{RunID: Str(r.run, "id"), TaskID: Str(r.task, "id"), Epoch: epoch, Commands: []rt.Command{{Executable: executable, Args: args, Directory: workspace, Input: prompt}}, Environment: env, Timeout: 90 * time.Second, Model: "gpt-6-luna", ArtifactTransport: "protocol-json"})
	if e != nil {
		t.Fatal(e)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Second)
	defer cancel()
	done := make(chan rt.Journal, 1)
	go func() { j, _ := w.Wait(ctx); done <- j }()
	tick := time.NewTicker(20 * time.Millisecond)
	defer tick.Stop()
	heartbeat := time.NewTicker(rt.HeartbeatInterval)
	defer heartbeat.Stop()
	toolAttempt := false
	var journal rt.Journal
loop:
	for {
		select {
		case journal = <-done:
			break loop
		case <-ctx.Done():
			w.Cancel(epoch, "C01 deadline")
			t.Fatal("C01 timeout")
		case <-heartbeat.C:
			r.call("/heartbeat", r.heartbeat(), 200)
			if e = w.Renew(epoch, rt.LeaseDuration); e != nil {
				t.Fatal(e)
			}
		case <-tick.C:
			raw, _ := os.ReadFile(filepath.Join(journalDir, "000.stdout"))
			stderr, _ := os.ReadFile(filepath.Join(journalDir, "000.stderr"))
			if !toolAttempt && (c01ToolEvent(raw) || bytes.Contains(bytes.ToLower(stderr), []byte("blocked by policy"))) {
				toolAttempt = true
				w.Cancel(epoch, "C01 unexpected tool; no retry")
			}
		}
	}
	for _, name := range []string{"journal.json", "000.stdout", "000.stderr", "result.json"} {
		if data, err := os.ReadFile(filepath.Join(journalDir, name)); err == nil {
			write("C01-"+name, rt.Redact(data))
		}
	}
	raw, _ := os.ReadFile(filepath.Join(journalDir, "000.stdout"))
	toolAttempt = toolAttempt || c01ToolEvent(raw)
	command["tool_attempt_observed"] = toolAttempt
	command["exit"] = journal.Exit
	command["stdout_hash"] = Digest(raw)
	command["protocol"] = journal.Protocol
	write("C01-command.json", Bytes(command))
	if toolAttempt || journal.State != "SETTLED" || !journal.Protocol.Settled || len(journal.Protocol.Result) == 0 {
		t.Fatal("C01 no-tool model run failed; inspect preserved protocol", journal.State, journal.Reason)
	}
	receipt, e := Decode(journal.Protocol.Result)
	if e != nil {
		t.Fatal(e)
	}
	return receipt, command
}
