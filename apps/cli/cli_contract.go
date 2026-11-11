package main

// apps/cli/cli_contract.go is W05-03: the command surface, the non-interactive output contract and the exit-code
// contract. It registers into the commandHandlers map the accepted W05-02 entry left for later cards, so no
// already-accepted file (main.go, coding_task.go) is edited here.
//
// The rules this file exists to honour, taken from the card:
//   * stdout carries JSONL only. Every diagnostic goes to stderr. A mixed line is a failure, not a style choice.
//   * exit codes are the contract: 0 completed, 1 failed, 2 usage error, 3 capability not implemented or not bound,
//     130 interrupted. A command that cannot do its real work says so with 3 and a machine-readable reason; it never
//     prints a plausible-looking success.
//   * nothing here shells out. There is deliberately no os/exec import: an alias to another vendor's CLI would make
//     the empty-stub negative ("空stub、shell别名调用外部品牌CLI充数") true of this build, which is the failure the
//     card names.
//   * a model change is a config write with a revision and a settled confirmation, so a silent switch cannot happen.

import (
	"bytes"
	"io"
	"net/http"
	"net/url"
	"time"

	"encoding/json"
	"encoding/json/jsontext"
	"fmt"
	"os"
	"os/signal"
	"path/filepath"
	"researchos.local/research-os/internal/domain"
	"sort"
	"strconv"
	"strings"
	"syscall"
)

const (
	exitCompleted      = 0
	exitFailed         = 1
	exitUsage          = 2
	exitNotImplemented = 3
	exitInterrupted    = 130
)

// contractCommands is the product-contract surface. Each row names the handler that answers, the check that proves
// the wiring, who owns the answer, the protocol method a host-bound verb actually sends, and `provenBy` — the
// assertion ids in this card's construction check that drive the row. The last field is the answer to the review
// that deleted `doctor` from main.go and found all 46 rows still green: a table may not certify itself, so
// W0503-TABLE-ROWS-ALL-PROVEN fails whenever a row names a probe that did not actually run.
var contractCommands = map[string]struct {
	handler string
	check   string
	needs   string
	owned   string
	method  string
	proven  []string
}{
	"init":     {"cliInit", "W0503-COMMANDS-ALL-HANDLED", "workspace path + host", "W05-03", "project.bootstrap", []string{"W0503-INIT-ACCEPTS-CHINESE-AND-SPACE-PATH", "W0503-INIT-WITHOUT-WORKSPACE-IS-USAGE-ERROR", "W0503-INIT-MISSING-DIRECTORY-FAILS"}},
	"goal":     {"cliHostCommand", "W0503-COMMANDS-ALL-HANDLED", "host + objective", "W05-03", "goal.start", []string{"W0503-GOAL-SENDS-GOAL-START", "W0503-GOAL-WITHOUT-OBJECTIVE-IS-USAGE-ERROR"}},
	"go":       {"cliHostCommand", "W0503-COMMANDS-ALL-HANDLED", "host + objective", "W05-03", "goal.start", []string{"W0503-GO-ALIASES-GOAL-START"}},
	"resume":   {"cliHostCommand", "W0503-COMMANDS-ALL-HANDLED", "host + session + writer epoch", "W05-03", "session.attach + session.control", []string{"W0503-RESUME-SENDS-SESSION-ATTACH", "W0503-RESUME-WITHOUT-EPOCH-IS-USAGE-ERROR"}},
	"status":   {"cliHostCommand", "W0503-COMMANDS-ALL-HANDLED", "host", "W05-03", "session.get + host.status", []string{"W0503-STATUS-SENDS-HOST-STATUS", "W0503-STATUS-EXIT-FOLLOWS-THE-HOST-REPLY"}},
	"cancel":   {"cliHostCommand", "W0503-COMMANDS-ALL-HANDLED", "host + run id", "W05-03", "session.control", []string{"W0503-CANCEL-SENDS-SESSION-CONTROL", "W0503-CANCEL-WITHOUT-RUN-IS-USAGE-ERROR"}},
	"config":   {"cliConfig", "W0503-CONFIG-MODEL-CHANGE-NEEDS-SETTLED-REVISION", "config file + host", "W05-03", "host.configure", []string{"W0503-MODEL-CHANGE-NEEDS-CONFIG-REVISION", "W0503-STALE-CONFIG-REVISION-REFUSED", "W0503-MODEL-CHANGE-NEEDS-SETTLED-FLAG", "W0503-MODEL-CHANGE-NEEDS-SETTLED-RUN-RECORDED", "W0503-SETTLED-MODEL-CHANGE-SENDS-HOST-CONFIGURE", "W0503-CONFIG-SHOW-AFTER-REFUSALS-IS-UNCHANGED"}},
	"commands": {"cliCommands", "W0503-COMMANDS-ALL-HANDLED", "", "W05-03", "", []string{"W0503-COMMANDS-ALL-HANDLED", "W0503-TABLE-ROWS-ALL-PROVEN", "W0503-LIST-FIELDS-ARE-ARRAYS-NOT-NULL"}},
	"/goal":    {"cliHostCommand", "W0503-SLASH-COMMANDS-HANDLED", "host + objective", "W05-03", "goal.start", []string{"W0503-SLASH-GOAL-SENDS-GOAL-START"}},
	"/resume":  {"cliHostCommand", "W0503-SLASH-COMMANDS-HANDLED", "host + session", "W05-03", "session.attach", []string{"W0503-SLASH-RESUME-SENDS-SESSION-ATTACH"}},
	"/status":  {"cliHostCommand", "W0503-SLASH-COMMANDS-HANDLED", "host", "W05-03", "host.status", []string{"W0503-SLASH-STATUS-SENDS-HOST-STATUS"}},
	"/cancel":  {"cliHostCommand", "W0503-SLASH-COMMANDS-HANDLED", "host + run id", "W05-03", "session.control", []string{"W0503-SLASH-CANCEL-SENDS-SESSION-CONTROL"}},
	"/model":   {"cliModel", "W0503-SLASH-COMMANDS-HANDLED", "config file", "W05-03", "", []string{"W0503-MODEL-CHANGE-NEEDS-CONFIG-REVISION"}},
	"/help":    {"cliHelp", "W0503-HELP-COVERS-EVERY-COMMAND", "", "W05-03", "", []string{"W0503-HELP-COVERS-EVERY-COMMAND", "W0503-HELP-LISTS-EVERY-REGISTERED-COMMAND"}},
	"run":      {"runDispatch", "W0502-CASCADE-RUNS-IN-REQUIRED-ORDER", "job object, positional prompt, or --prompt/--prompt-file + project", "accepted W05-02 cascade, delegated; W05-03 contract prompt", "session.send + session.events", []string{"W0503-ACCEPTED-VERBS-NOT-SHADOWED", "W0503-ACCEPTED-WORKER-VERB-STILL-RUNS-INSIDE-THE-CASCADE", "W0503-RUN-SENDS-SESSION-SEND-AND-EVENTS", "W0503-RUN-REJECTS-NON-JSONL-OUTPUT"}},
	"worker":   {"runWorkerLoop", "W0502-WORKER-WAS-REALLY-WRITING-BEFORE-THE-CANCEL", "job object", "accepted W05-02", "", []string{"W0503-ACCEPTED-WORKER-VERB-STILL-RUNS-INSIDE-THE-CASCADE"}},
	"task":     {"taskDispatch", "W0502-TASK-CHECK-REALLY-ROUN-THE-BINARY", "legacy edit flags or --prompt/--prompt-file + Host", "accepted W05-01/W05-02; explicit prompt bridge development checks only", "session.send + session.events (explicit prompt only)", []string{"W0503-TASK-VERB-REACHES-THE-ACCEPTED-RUNNER"}},
	"doctor":   {"main.doctor", "W0203-DOCTOR-HANDSHAKE", "host discovery", "accepted W02-03", "", []string{"W0503-DOCTOR-NOT-FOUND-REFUSES", "W0503-DOCTOR-DOWN-EXIT-1", "W0503-DOCTOR-UP-COMPLETES"}},
	"version":  {"main.version", "W0203-VERSION-PROTOCOL", "", "accepted W02-03", "", []string{"W0503-VERSION-IS-ONE-COMPLETED-RECORD"}},
	"help":     {"cliHelpSurface", "W0503-HELP-COVERS-EVERY-COMMAND", "", "W05-03 surface over accepted W02-03 entry", "", []string{"W0503-HELP-COVERS-EVERY-COMMAND", "W0503-HELP-REACHABLE-NOT-VIA-DEFAULT-BRANCH"}},
	// The interactive TUI is refused, not implemented. The honest owner is not "a later card": W05 contains only
	// W05-01, W05-02, W05-03 and W05-99, and the accepted W05-02 check pins this very refusal on stdout, so the
	// surface stays as delivered and the open question belongs to the W05 gate card and case A04.
	"interactive": {"cliInteractive", "W0503-INTERACTIVE-COMMAND-DELIVERED", "host + stdin", "W05-03", "session.list + session.create + session.send", []string{"W0503-INTERACTIVE-SENDS-LIST-CREATE-SEND", "W0503-INTERACTIVE-WITHOUT-HOST-REFUSES"}},
	"chat":        {"", "W0503-INTERACTIVE-TUI-KEEPS-NOT-IMPLEMENTED", "terminal", "accepted W02-03 refusal, pinned by W05-02; undecided owner is W05-99/A04", "", []string{"W0503-CHAT-KEEPS-THE-ACCEPTED-REFUSAL"}},
}

// registeredHere reports whether this card's table owns the verb, which is what the non-shadowing rule turns on: a
// verb whose owner is not W05-03 must never be answered by commandHandlers[name] set by this file.
func registeredHere(name string) bool {
	o := contractCommands[name].owned
	return o == "W05-03" || strings.HasPrefix(o, "W05-03 ")
}

func cliEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

// outJSON writes exactly one JSONL record to stdout. stdout is never written to by anything else in this file, so
// a caller that captures it can require every line to parse.
func outJSON(fields map[string]any) {
	line, err := json.Marshal(fields)
	if err != nil {
		fmt.Fprintln(os.Stderr, "cli: unserialisable report:", err)
		os.Exit(exitFailed)
	}
	fmt.Fprintln(os.Stdout, string(line))
}

func diag(format string, args ...any) {
	fmt.Fprintf(os.Stderr, "cli: "+format+"\n", args...)
}

func fail(command string, code int, reason string, detail ...string) {
	outJSON(map[string]any{"command": command, "status": "REJECTED", "exit_code": code,
		"reason": reason, "detail": strings.Join(detail, " ")})
	os.Exit(code)
}

// hostDiscovery reuses the discovery file the accepted W02-03 launcher wrote; it never invents a URL.
func hostDiscovery() (discovery, string, error) {
	resolved, err := resolveCLIHostDiscovery()
	return resolved.discovery, resolved.path, err
}

func configPath() string {
	return cliEnv("RESEARCHOS_CLI_CONFIG", filepath.Join(".local", "v24_cli_config.json"))
}

type cliConfig struct {
	ConfigRevision int    `json:"config_revision"`
	Model          string `json:"model"`
	ConfirmedRun   string `json:"settled_run_id"`
	WorkspaceRef   string `json:"workspace_ref"`
	ProjectID      string `json:"project_id"`
	SessionID      string `json:"session_id"`
	Revision       int64  `json:"session_revision"`
	WriterEpoch    int64  `json:"writer_epoch"`
	UpdatedBy      string `json:"updated_by"`
}

func readConfig() (cliConfig, error) {
	var c cliConfig
	raw, err := os.ReadFile(configPath())
	if err != nil {
		return c, err
	}
	err = json.Unmarshal(raw, &c)
	return c, err
}

func writeConfig(c cliConfig) error {
	if err := os.MkdirAll(filepath.Dir(configPath()), 0o700); err != nil {
		return err
	}
	raw, err := json.MarshalIndent(c, "", " ")
	if err != nil {
		return err
	}
	return os.WriteFile(configPath(), append(raw, '\n'), 0o600)
}

func init() {
	for name := range contractCommands {
		if !registeredHere(name) {
			continue
		}
		if _, taken := commandHandlers[name]; taken {
			continue
		}
		handler := name
		commandHandlers[handler] = func(args []string) { dispatchContract(handler, args) }
	}
}

func dispatchContract(name string, args []string) {
	rest := args
	switch name {
	case "commands":
		cliCommands()
	case "/help", "help":
		cliHelp()
	case "init":
		cliInit(rest)
	case "config":
		cliConfigCommand(rest)
	case "/model":
		cliModel(rest)
	case "goal", "/goal", "go", "status", "/status", "cancel", "/cancel", "resume", "/resume":
		cliHostCommand(name, rest)
	default:
		fail(name, exitNotImplemented, "NO_HANDLER_REGISTERED")
	}
}

func flagValue(args []string, name string) (string, bool) {
	for i, a := range args {
		// A flag's value is the next token only when that token is itself a value: `--settled --base-url x` must
		// read --settled as a boolean and keep --base-url's own argument, which is what the old unconditional
		// look-ahead got wrong.
		if a == "--"+name && i+1 < len(args) && !strings.HasPrefix(args[i+1], "--") {
			return args[i+1], true
		}
		if strings.HasPrefix(a, "--"+name+"=") {
			return strings.SplitN(a, "=", 2)[1], true
		}
	}
	return "", false
}

func flagBool(args []string, name string) bool {
	v, ok := flagValue(args, name)
	if !ok {
		for _, a := range args {
			if a == "--"+name {
				return true
			}
		}
		return false
	}
	b, err := strconv.ParseBool(v)
	return err == nil && b
}

// surfaceEntries renders the command table as records: which card owns the answer, whether a handler is wired, and
// what state the verb is in. A verb an accepted card owns is reported as accepted, not as this card's work, and the
// interactive TUI keeps its refusal, so the report cannot overclaim by renaming someone else's verb.
func surfaceEntries() (entries []any, missingHandlers, missingChecks, refused []string) {
	entries = []any{}
	missingHandlers = []string{}
	missingChecks = []string{}
	refused = []string{}
	names := make([]string, 0, len(contractCommands))
	for n := range contractCommands {
		names = append(names, n)
	}
	sort.Strings(names)
	for _, n := range names {
		c := contractCommands[n]
		_, registered := commandHandlers[n]
		state := "NOT_IMPLEMENTED"
		// A row with no handler is a refusal, whatever its owner string says: the review showed an owned-prefix test
		// painting the refused interactive TUI as ACCEPTED work.
		switch {
		case c.handler == "":
			refused = append(refused, n)
		case !registeredHere(n) && strings.HasPrefix(c.owned, "accepted"):
			state = "ACCEPTED"
		case registeredHere(n) && registered:
			state = "IMPLEMENTED"
		}
		if registeredHere(n) && (!registered || c.handler == "") {
			missingHandlers = append(missingHandlers, n)
		}
		// A row counts as covered only when it names the probes that drive it; check_id alone is a label, and the
		// review showed a labelled-but-undriven row (doctor) surviving as an ACCEPTED claim.
		if c.check == "" || len(c.proven) == 0 {
			missingChecks = append(missingChecks, n)
		}
		entry := map[string]any{"command": n, "handler": c.handler, "check_id": c.check,
			"owner": c.owned, "state": state, "needs": c.needs, "method_sent": c.method,
			"proven_by": c.proven, "proven_count": len(c.proven)}
		if n == "task" || n == "run" {
			entry["state_scope"] = "existing legacy/positional branch; explicit prompt qualification is separate"
			entry["explicit_prompt_mode"] = map[string]any{"state": "IMPLEMENTED", "qualification": "DEVELOPMENT_ONLY", "independent_acceptance": "NOT_EVALUATED", "method_sent": "session.send + session.events", "sources": []string{"--prompt", "--prompt-file"}}
		}
		entries = append(entries, entry)
	}
	return
}

// cliCommands is the coverage self-report the card's OUTPUT check turns on: every contract command with its owner,
// handler and check id, and the missing set computed rather than asserted.
func cliCommands() {
	entries, missingHandlers, missingChecks, _ := surfaceEntries()
	methods := map[string]any{}
	for name, c := range v2Contract {
		methods[name] = map[string]any{"payload": c.payload, "result": c.result, "required": c.required,
			"write": v2WriteMethods[name]}
	}
	outJSON(map[string]any{"command": "commands", "status": "COMPLETED", "exit_code": exitCompleted,
		"commands": entries, "count": len(entries), "missing_handler": missingHandlers,
		"missing_check": missingChecks, "jsonl_only_stdout": true,
		"protocol_version": clientProtocol, "protocol_methods": methods,
		"protocol_method_count": len(methods),
		"exit_code_contract": map[string]any{"completed": exitCompleted, "failed": exitFailed,
			"usage": exitUsage, "not_implemented": exitNotImplemented, "interrupted": exitInterrupted}})
	if len(missingHandlers) > 0 || len(missingChecks) > 0 {
		os.Exit(exitFailed)
	}
}

func cliHelp() { cliHelpSurface(false) }

// cliHelpSurface is what `researchos help` prints. stdout is the machine record; the human-readable block goes to
// stderr, because the card requires non-interactive stdout to be JSONL only. The record names every command this
// binary can route — including the accepted verbs and the ones still refused — so help cannot overclaim by omission.
func cliHelpSurface(human bool) {
	entries, _, _, refused := surfaceEntries()
	names := make([]string, 0, len(entries))
	for _, e := range entries {
		names = append(names, e.(map[string]any)["command"].(string))
	}
	outJSON(map[string]any{"command": "help", "status": "COMPLETED", "exit_code": exitCompleted,
		"usage": "researchos <command> [flags]", "commands": names, "surface": entries,
		"prompt_usage":    []string{"researchos run --prompt \"<text>\" --project <id> --output jsonl", "researchos task --prompt-file <UTF-8-file> --project <id> --output jsonl"},
		"prompt_limits":   map[string]any{"unicode_characters": cliPromptMaxRunes, "file_bytes": cliPromptMaxFileBytes},
		"not_implemented": refused, "output_contract": "stdout is JSONL only; diagnostics go to stderr",
		"exit_codes": map[string]any{"0": "completed", "1": "failed", "2": "usage error",
			"3": "capability not implemented or not bound", "130": "interrupted"}})
	if human {
		for _, e := range entries {
			m := e.(map[string]any)
			diag("%-9s %-13s owner=%s check=%s", m["command"], m["state"], m["owner"], m["check_id"])
		}
	}
}

// cliInit performs the published first-use chain. A path is a picker hint, never
// an authorized workspace reference; only the host may mint that reference.
func cliInit(args []string) {
	path, ok := flagValue(args, "workspace")
	if !ok {
		path, ok = firstPositional(args)
	}
	if !ok {
		fail("init", exitUsage, "MISSING_WORKSPACE_PATH",
			"the contract writes `researchos init <path>`; --workspace <path> is accepted as well")
	}
	abs, err := filepath.Abs(path)
	if err != nil {
		fail("init", exitFailed, "WORKSPACE_PATH_UNRESOLVABLE", err.Error())
	}
	info, err := os.Stat(abs)
	if err != nil || !info.IsDir() {
		fail("init", exitFailed, "WORKSPACE_NOT_A_DIRECTORY", abs)
	}
	c, err := readConfig()
	if err != nil {
		c = cliConfig{ConfigRevision: 0}
	}
	d, dpath, herr := hostDiscovery()
	base := map[string]any{"command": "init", "config_path": configPath(),
		"config_revision": c.ConfigRevision, "path_contains_non_ascii": !isASCII(abs),
		"path_contains_space": strings.ContainsAny(abs, " \t"), "local_leg": "WORKSPACE_PATH_VALIDATED"}
	if herr != nil || d.URL == "" {
		base["status"], base["exit_code"], base["reason"] = "REJECTED", exitNotImplemented, "INIT_REQUIRES_HOST_PROJECT_BOOTSTRAP"
		base["detail"] = dpath + ": host discovery unavailable, and project.bootstrap is the operation init performs"
		outJSON(base)
		os.Exit(exitNotImplemented)
	}
	ctx := newV2Context("init", args, c, d.URL)
	ctx.projectID, ctx.sessionID = "", ""
	ctx.revision, ctx.epoch = 0, 0
	credential, err := cliInitCredential(d, ctx.clientID)
	if err != nil {
		base["status"], base["exit_code"], base["reason"] = "REJECTED", exitNotImplemented, "NATIVE_BOOTSTRAP_FAILED"
		base["detail"] = err.Error()
		outJSON(base)
		os.Exit(exitNotImplemented)
	}
	ctx.credential = credential
	selection, chosenPath, err := cliChooseWorkspace(d, ctx.clientID, abs)
	if err != nil {
		base["status"], base["exit_code"], base["reason"] = "REJECTED", exitFailed, "NATIVE_WORKSPACE_CHOICE_FAILED"
		base["detail"] = err.Error()
		outJSON(base)
		os.Exit(exitFailed)
	}
	registerID, err := cliFirstUseCommandID("register")
	if err != nil {
		fail("init", exitFailed, "COMMAND_ID_UNAVAILABLE")
	}
	ctx.commandID = registerID
	reply, reason, code := v2Call(ctx, "workspace.register", map[string]any{
		"selection_ref": selection, "display_name": filepath.Base(chosenPath), "requested_access": "READ_WRITE"})
	base["requests_sent"], base["host_url"] = ctx.requestLog, d.URL
	if code != exitCompleted {
		base["status"], base["exit_code"], base["reason"] = "REJECTED", code, orDefault(reason, "REGISTER_REFUSED_WITHOUT_CODE")
		base["detail"] = replyView(reply)
		outJSON(base)
		os.Exit(code)
	}
	registered, _ := reply["result"].(map[string]any)
	workspaceRef, _ := registered["authorized_workspace_ref"].(string)
	if workspaceRef == "" {
		fail("init", exitFailed, "REGISTER_REPLY_MISSING_WORKSPACE_REF")
	}
	bootstrapID, err := cliFirstUseCommandID("bootstrap")
	if err != nil {
		fail("init", exitFailed, "COMMAND_ID_UNAVAILABLE")
	}
	ctx.commandID = bootstrapID
	reply, reason, code = v2Call(ctx, "project.bootstrap", map[string]any{
		"authorized_workspace_ref": workspaceRef, "display_name": filepath.Base(chosenPath)})
	base["requests_sent"] = ctx.requestLog
	if code != exitCompleted {
		base["status"], base["exit_code"] = "REJECTED", code
		base["reason"] = orDefault(reason, "BOOTSTRAP_REFUSED_WITHOUT_CODE")
		base["detail"] = replyView(reply)
		outJSON(base)
		os.Exit(code)
	}
	result, _ := reply["result"].(map[string]any)
	projectID, _ := result["project_id"].(string)
	if projectID == "" {
		fail("init", exitFailed, "BOOTSTRAP_REPLY_MISSING_PROJECT_ID")
	}
	boundWorkspace, _ := result["workspace"].(map[string]any)
	finalWorkspaceRef, _ := boundWorkspace["authorized_workspace_ref"].(string)
	boundProjectID, _ := boundWorkspace["project_id"].(string)
	status, _ := boundWorkspace["status"].(string)
	if finalWorkspaceRef == "" || boundProjectID != projectID || status != "ACTIVE" {
		fail("init", exitFailed, "BOOTSTRAP_REPLY_WORKSPACE_UNBOUND")
	}
	c.WorkspaceRef, c.ProjectID = finalWorkspaceRef, projectID
	c.SessionID, c.Revision, c.WriterEpoch = "", 0, 0
	if err := writeConfig(c); err != nil {
		fail("init", exitFailed, "CONFIG_WRITE_FAILED", err.Error())
	}
	base["status"], base["exit_code"], base["project_id"] = "COMPLETED", exitCompleted, projectID
	base["workspace_ref"] = finalWorkspaceRef
	base["result"] = reply["result"]
	outJSON(base)
}

func isASCII(s string) bool {
	for _, r := range s {
		if r > 127 {
			return false
		}
	}
	return true
}

// cliConfig implements `config show` and `config set-model`, the latter only with a matching revision and an
// explicit settled confirmation, so a model change cannot happen silently.
func cliConfigCommand(args []string) {
	if len(args) == 0 || args[0] == "show" {
		c, err := readConfig()
		if err != nil {
			fail("config", exitFailed, "CONFIG_UNREADABLE", err.Error())
		}
		outJSON(map[string]any{"command": "config", "status": "COMPLETED", "exit_code": exitCompleted, "config": c})
		return
	}
	if args[0] == "set-model" {
		setModel("config", args[1:])
		return
	}
	if args[0] == "settle-run" {
		runID, ok := flagValue(args[1:], "run")
		if !ok {
			fail("config", exitUsage, "MISSING_RUN_FLAG", "config settle-run --run <id>")
		}
		c, err := readConfig()
		if err != nil {
			fail("config", exitFailed, "CONFIG_UNREADABLE", err.Error())
		}
		c.ConfirmedRun = runID
		if err := writeConfig(c); err != nil {
			fail("config", exitFailed, "CONFIG_WRITE_FAILED", err.Error())
		}
		// This records the caller's confirmation; it is not proof that the run settled. The host's own session
		// state is the authority, and a model switch that needs that proof is a LIVE-path concern (A04), not
		// something this CLI may assert by writing a field.
		diag("settle-run records a claim, not a host observation: run=%s", runID)
		outJSON(map[string]any{"command": "config", "subcommand": "settle-run", "status": "COMPLETED",
			"exit_code": exitCompleted, "settled_run_id": runID, "config_revision": c.ConfigRevision,
			"settled_run_source": "recorded by the caller; the host session state remains the authority"})
		return
	}
	fail("config", exitUsage, "UNKNOWN_CONFIG_SUBCOMMAND", args[0])
}

func cliModel(args []string) {
	setModel("/model", args)
}

func setModel(command string, args []string) {
	out, reason, code := configureCLIModel(command, args)
	if code != 0 {
		if reason == "SETTLED_RUN_UNRECORDED" {
			fail(command, code, reason, "record the caller claim with config settle-run --run <id>; the host remains settlement authority")
		}
		fail(command, code, reason)
	}
	outJSON(out)
}

// Configuration has its own strict, raw response boundary. Neither an admission
// ACK nor an unverified echoed map authorizes a local configuration write.
func configureCLIModel(command string, args []string) (map[string]any, string, int) {
	reject := func(reason string, code int) (map[string]any, string, int) { return nil, reason, code }
	for _, name := range []string{"api-key", "token", "secret", "password"} {
		if configureFlagPresent(args, name) {
			return reject("CREDENTIAL_MATERIAL_NOT_ALLOWED", 2)
		}
	}
	model, haveModel := flagValue(args, "model")
	if !haveModel || model == "" {
		return reject("MISSING_MODEL_FLAG", 2)
	}
	parts := strings.SplitN(model, "/", 2)
	if len(parts) != 2 || strings.TrimSpace(parts[0]) == "" || strings.TrimSpace(parts[1]) == "" {
		return reject("MODEL_NOT_PROVIDER_QUALIFIED", 2)
	}
	provider, modelID := parts[0], parts[1]
	c, readErr := readConfig()
	if readErr != nil && !os.IsNotExist(readErr) {
		return reject("CONFIG_UNREADABLE", 1)
	}
	scope := &v2Context{projectID: c.ProjectID, sessionID: c.SessionID, revision: c.Revision, epoch: c.WriterEpoch}
	explicitScope := false
	for _, name := range []string{"project", "session", "expected-revision", "writer-epoch"} {
		if configureFlagPresent(args, name) {
			explicitScope = true
			v, ok := flagValue(args, name)
			if !ok || v == "" {
				return reject("INCOMPLETE_CONFIGURE_SCOPE", 2)
			}
			switch name {
			case "project":
				scope.projectID = v
			case "session":
				scope.sessionID = v
			default:
				n, valid := configureDecimal(v)
				if !valid {
					return reject("INCOMPLETE_CONFIGURE_SCOPE", 2)
				}
				if name == "expected-revision" {
					scope.revision = n
				} else {
					scope.epoch = n
				}
			}
		}
	}
	defaultScope := flagBool(args, "default") || scope.sessionID == ""
	if flagBool(args, "default") && explicitScope || scope.sessionID == "" && explicitScope {
		return reject("INCOMPLETE_CONFIGURE_SCOPE", 2)
	}
	if readErr != nil && !defaultScope {
		return reject("CONFIG_UNREADABLE", 1)
	}
	rev, haveRev := flagValue(args, "config-revision")
	if !haveRev {
		return reject("MISSING_CONFIG_REVISION", 2)
	}
	current, valid := configureDecimal(rev)
	if !valid || current >= 9007199254740991 {
		return reject("INVALID_CONFIG_REVISION", 2)
	}
	if current != int64(c.ConfigRevision) {
		return reject("STALE_CONFIG_REVISION", 1)
	}
	if defaultScope {
		scope.projectID = ""
		scope.sessionID = ""
		scope.revision = 0
		scope.epoch = 0
	} else {
		if !flagBool(args, "settled") {
			return reject("SETTLED_FLAG_REQUIRED", 1)
		}
		if strings.TrimSpace(c.ConfirmedRun) == "" {
			return reject("SETTLED_RUN_UNRECORDED", 1)
		}
		if scope.epoch <= 0 {
			return reject("MODEL_CHANGE_WITHOUT_EPOCH", 2)
		}
		if !continuationID(scope.projectID) || !continuationID(scope.sessionID) || scope.revision <= 0 || scope.revision > 9007199254740991 || scope.epoch > 9007199254740991 {
			return reject("INCOMPLETE_CONFIGURE_SCOPE", 2)
		}
	}
	endpoint, haveEndpoint := flagValue(args, "base-url")
	if !haveEndpoint || endpoint == "" {
		return reject("MISSING_CONFIGURE_FIELDS", 2)
	}
	u, e := url.Parse(endpoint)
	if e != nil || u.Scheme != "https" || u.Host == "" || u.User != nil || u.RawQuery != "" || u.ForceQuery || u.Fragment != "" {
		return reject("INVALID_CONFIGURE_ENDPOINT", 2)
	}
	var credential any
	if configureFlagPresent(args, "credential-ref") {
		v, ok := flagValue(args, "credential-ref")
		if !ok || strings.TrimSpace(v) == "" {
			return reject("INVALID_CREDENTIAL_REF", 2)
		}
		credential = v
	}
	d, _, e := hostDiscovery()
	if e != nil || d.URL == "" {
		return reject("MODEL_CHANGE_REQUIRES_HOST_CONFIGURE", 3)
	}
	// Empty local scope prevents credential renewal from using a project claim.
	ctx := newV2Context(command, nil, cliConfig{}, strings.TrimSuffix(d.URL, "/"))
	ctx.projectID, ctx.sessionID, ctx.revision, ctx.epoch = scope.projectID, scope.sessionID, scope.revision, scope.epoch
	payload := map[string]any{"config_revision": current + 1, "provider_id": provider, "base_url": endpoint, "model_id": modelID, "credential_ref": credential}
	envelope, why := v2EnvelopeFor(ctx, "host.configure", payload)
	if why != "" {
		code := 2
		if why == "CREDENTIAL_ABSENT" {
			code = 3
		}
		return reject(why, code)
	}
	doc, err := cliProtocolDocument()
	requestBytes, marshalErr := json.Marshal(envelope)
	var requestValue any
	if err != nil || marshalErr != nil || json.Unmarshal(requestBytes, &requestValue) != nil || doc.ValidateDef("CommandEnvelope", requestValue) != nil {
		return reject("INVALID_CONFIGURE_REQUEST", 2)
	}
	statusCtx := *ctx
	statusCtx.projectID = ""
	statusCtx.sessionID = ""
	statusCtx.revision = 0
	statusCtx.epoch = 0
	statusCtx.commandID = domain.ID()
	statusCtx.requestLog = nil
	status, why, code := configureCLICall(&statusCtx, "host.status", map[string]any{})
	if code != 0 {
		return reject(why, code)
	}
	reported, ok := configureExactInteger(cliObject(status["result"])["config_revision"])
	if !ok || reported != current {
		return reject("STALE_CONFIG_REVISION", 1)
	}
	reply, why, code := configureCLICall(ctx, "host.configure", payload)
	if code != 0 {
		return reject(why, code)
	}
	result := cliObject(reply["result"])
	for _, key := range []string{"provider_id", "base_url", "model_id", "credential_ref"} {
		if result[key] != payload[key] {
			return reject("CONFIGURE_RESULT_MISMATCH", 1)
		}
	}
	actual, ok := configureExactInteger(result["config_revision"])
	ref, refOK := result["model_config_ref"].(string)
	if !ok || actual != current+1 || !refOK || strings.TrimSpace(ref) == "" || result["verified_at"] != nil || ctx.credential != "" && strings.Contains(ref, ctx.credential) {
		return reject("CONFIGURE_RESULT_MISMATCH", 1)
	}
	previous := c.Model
	c.Model = ref
	c.ConfigRevision = int(actual)
	if !defaultScope {
		revision, ok := configureExactInteger(reply["revision"])
		if !ok || revision != ctx.revision+1 {
			return reject("CONFIGURE_REVISION_MISMATCH", 1)
		}
		c.SessionID = ctx.sessionID
		c.ProjectID = ctx.projectID
		c.Revision = revision
		c.WriterEpoch = ctx.epoch
	}
	if e = writeConfig(c); e != nil {
		return reject("CONFIG_WRITE_FAILED", 1)
	}
	return map[string]any{"command": command, "status": "COMPLETED", "exit_code": 0, "previous_model": previous, "model": ref, "selected_model": model, "config_revision": actual, "settled_run_id": c.ConfirmedRun, "method_sent": "host.configure", "requests_sent": []string{"host.status", "host.configure"}, "provider_id": provider}, "", 0
}

func configureFlagPresent(args []string, name string) bool {
	for _, v := range args {
		if v == "--"+name || strings.HasPrefix(v, "--"+name+"=") {
			return true
		}
	}
	return false
}
func configureDecimal(s string) (int64, bool) {
	if s == "" {
		return 0, false
	}
	for _, c := range s {
		if c < '0' || c > '9' {
			return 0, false
		}
	}
	n, e := strconv.ParseInt(s, 10, 64)
	return n, e == nil && n >= 0 && n <= 9007199254740991
}

func configureExactInteger(value any) (int64, bool) {
	// Num uses a rational parsed from json.Number, without a float64 roundtrip.
	n, err := domain.Num(domain.Object{"value": value}, "value")
	return n, err == nil && n >= 0
}

func configureCLICall(ctx *v2Context, method string, payload map[string]any) (map[string]any, string, int) {
	env, why := v2EnvelopeFor(ctx, method, payload)
	if why != "" {
		code := 2
		if why == "CREDENTIAL_ABSENT" {
			code = 3
		}
		return nil, why, code
	}
	body, e := json.Marshal(env)
	if e != nil {
		return nil, "INVALID_CONFIGURE_REQUEST", 2
	}
	req, e := http.NewRequest("POST", ctx.baseURL+v2CommandPath, bytes.NewReader(body))
	if e != nil {
		return nil, "INVALID_HOST_URL", 2
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+ctx.credential)
	client := http.Client{Timeout: 8 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	ctx.requestLog = append(ctx.requestLog, method)
	response, e := client.Do(req)
	if e != nil {
		return nil, "HOST_UNREACHABLE", 1
	}
	defer response.Body.Close()
	if response.StatusCode < 200 || response.StatusCode >= 300 {
		code := 3
		if response.StatusCode >= 500 && response.StatusCode <= 599 {
			code = 1
		}
		return nil, "HOST_HTTP_" + strconv.Itoa(response.StatusCode), code
	}
	raw, e := io.ReadAll(io.LimitReader(response.Body, (1<<20)+1))
	if e != nil || len(raw) > 1<<20 {
		return nil, "INCOMPLETE_OR_OVERSIZE_REPLY", 1
	}
	// Validate raw Unicode, decoded-key uniqueness and the single complete JSON
	// value before decoding. Canonicalization would round numeric lexemes.
	if !jsontext.Value(raw).IsValid() {
		return nil, "MALFORMED_REPLY", 1
	}
	var reply map[string]any
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.UseNumber()
	if decoder.Decode(&reply) != nil {
		return nil, "MALFORMED_REPLY", 1
	}
	doc, e := cliProtocolDocument()
	if e != nil || doc.ValidateDef("CommandResponse", reply) != nil {
		return nil, "INVALID_CONFIGURE_REPLY", 1
	}
	if reply["protocol_version"] != clientProtocol || reply["command_id"] != ctx.commandID || reply["method"] != method {
		return nil, "REPLY_IDENTITY_MISMATCH", 1
	}
	if ctx.sessionID == "" {
		if reply["session_id"] != nil || method == "host.configure" && reply["revision"] != nil {
			return nil, "REPLY_SCOPE_MISMATCH", 1
		}
	} else if reply["session_id"] != ctx.sessionID {
		return nil, "REPLY_SCOPE_MISMATCH", 1
	}
	if reply["status"] != "COMPLETED" {
		if reply["status"] == "REJECTED" {
			if cliObject(reply["error"])["code"] != reply["error_code"] {
				return nil, "INVALID_CONFIGURE_REPLY", 1
			}
			errcode, _ := reply["error_code"].(string)
			code := 1
			switch errcode {
			case "RESOURCE_BLOCKED", "RESOURCE_UNAVAILABLE", "MODEL_UNAVAILABLE", "HOST_UNAVAILABLE", "UNAUTHENTICATED", "FORBIDDEN", "LEASE_EXPIRED", "WRITER_BUSY", "STALE_WRITER_EPOCH", "CANCEL_UNCONFIRMED":
				code = 3
			case "INVALID_REQUEST", "UNSUPPORTED_PROTOCOL", "UNSUPPORTED_METHOD":
				code = 2
			}
			return nil, "HOST_REJECTED:" + errcode, code
		}
		return nil, "CONFIGURE_NOT_COMPLETED", 1
	}
	result := cliObject(reply["result"])
	definition := "ConfigureResult"
	if method == "host.status" {
		definition = "HostStatusResult"
	}
	if doc.ValidateDef(definition, result) != nil {
		return nil, "INVALID_CONFIGURE_RESULT", 1
	}
	if method == "host.status" {
		versions, ok := result["protocol_versions"].([]any)
		if result["client_id"] != ctx.clientID || !ok || len(versions) != 1 || versions[0] != clientProtocol {
			return nil, "HOST_STATUS_IDENTITY_MISMATCH", 1
		}
	}
	return reply, "", 0
}

// modelProvider preserves the existing helper signature; configuration sends
// the suffix as model_id and stores only the host's opaque configuration ref.
func modelProvider(model string) (string, string, string) {
	parts := strings.SplitN(model, "/", 2)
	if len(parts) != 2 || parts[0] == "" || parts[1] == "" {
		fail("config", exitUsage, "MODEL_NOT_PROVIDER_QUALIFIED", "pass --model <provider>/<model>")
	}
	return parts[0], "", ""
}

// cliNeedsHost is the honest host-bound path: status/resume/goal/go/cancel all need a live host, and when the
// discovery file is absent or the host does not answer they report that with exit 3 or 1 instead of pretending.
// cliNeedsHost was the previous host-bound path: one GET /healthz, positional ids discarded, exit 0. The review
// measured it and named it the card's own 空stub negative, so it is gone; apps/cli/cli_verbs.go now sends the method
// each verb is named after. Only the signal guard from that file is kept.

// interruptGuard records intent. The active host flow sends CANCEL and waits
// for actual settlement; receiving a signal alone never claims tools stopped.
func interruptGuard() (<-chan os.Signal, func()) {
	ch := make(chan os.Signal, 1)
	signal.Notify(ch, os.Interrupt, syscall.SIGTERM)
	return ch, func() { signal.Stop(ch) }
}

func clip(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n] + "..."
}

func exitCodeForInterrupt() int { return exitInterrupted }
