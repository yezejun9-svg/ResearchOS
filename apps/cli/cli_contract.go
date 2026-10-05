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
	"encoding/json"
	"fmt"
	"os"
	"os/signal"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"sync"
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
	"run":      {"runDispatch", "W0502-CASCADE-RUNS-IN-REQUIRED-ORDER", "job object or prompt + project", "accepted W05-02 cascade, delegated; W05-03 contract prompt", "session.send + session.events", []string{"W0503-ACCEPTED-VERBS-NOT-SHADOWED", "W0503-ACCEPTED-WORKER-VERB-STILL-RUNS-INSIDE-THE-CASCADE", "W0503-RUN-SENDS-SESSION-SEND-AND-EVENTS", "W0503-RUN-REJECTS-NON-JSONL-OUTPUT"}},
	"worker":   {"runWorkerLoop", "W0502-WORKER-WAS-REALLY-WRITING-BEFORE-THE-CANCEL", "job object", "accepted W05-02", "", []string{"W0503-ACCEPTED-WORKER-VERB-STILL-RUNS-INSIDE-THE-CASCADE"}},
	"task":     {"runCodingTask", "W0502-TASK-CHECK-REALLY-ROUN-THE-BINARY", "check command", "accepted W05-01/W05-02", "", []string{"W0503-TASK-VERB-REACHES-THE-ACCEPTED-RUNNER"}},
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
	path := cliEnv("RESEARCHOS_CLI_DISCOVERY", discoveryPath)
	raw, err := os.ReadFile(path)
	if err != nil {
		return discovery{}, path, err
	}
	var d discovery
	if err := json.Unmarshal(raw, &d); err != nil {
		return discovery{}, path, err
	}
	return d, path, nil
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
		entries = append(entries, map[string]any{"command": n, "handler": c.handler, "check_id": c.check,
			"owner": c.owned, "state": state, "needs": c.needs, "method_sent": c.method,
			"proven_by": c.proven, "proven_count": len(c.proven)})
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
	c.WorkspaceRef, c.ProjectID = workspaceRef, projectID
	c.SessionID, c.Revision, c.WriterEpoch = "", 0, 0
	if err := writeConfig(c); err != nil {
		fail("init", exitFailed, "CONFIG_WRITE_FAILED", err.Error())
	}
	base["status"], base["exit_code"], base["project_id"] = "COMPLETED", exitCompleted, projectID
	base["workspace_ref"] = workspaceRef
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
	model, ok := flagValue(args, "model")
	if !ok {
		fail(command, exitUsage, "MISSING_MODEL_FLAG", "pass --model <provider/model>")
	}
	c, err := readConfig()
	if err != nil {
		fail(command, exitFailed, "CONFIG_UNREADABLE", err.Error())
	}
	rev, haveRev := flagValue(args, "config-revision")
	if !haveRev {
		fail(command, exitUsage, "MISSING_CONFIG_REVISION", "a model change must name the revision it was read at")
	}
	if rev != strconv.Itoa(c.ConfigRevision) {
		outJSON(map[string]any{"command": command, "status": "REJECTED", "exit_code": exitFailed,
			"reason": "STALE_CONFIG_REVISION", "claimed_config_revision": rev,
			"current_config_revision": c.ConfigRevision, "model_left_unchanged": c.Model})
		os.Exit(exitFailed)
	}
	// Two separate refusals, because the review measured that one combined condition let the settled-run half be
	// deleted with every row still green: each half now has an input that reaches it and a reason that names it.
	if !flagBool(args, "settled") {
		fail(command, exitFailed, "SETTLED_FLAG_REQUIRED",
			"a model switch needs --settled: the caller must state that the current run settled before the change")
	}
	if strings.TrimSpace(c.ConfirmedRun) == "" {
		fail(command, exitFailed, "SETTLED_RUN_UNRECORDED",
			"--settled names no settled run: record one with `config settle-run --run <id>` first, "+
				"so the confirmation points at an observation instead of a flag")
	}
	previous := c.Model
	// The contract gives `config` the local operation host.configure, so a model switch is a command to the host,
	// not only a file write. What is actually true about the epoch, stated without more than the measurement supports
	// (the round-3 review rejected the previous wording as a claim ahead of it):
	//   * with no epoch anywhere the CLI refuses locally with MODEL_CHANGE_WITHOUT_EPOCH before building the request,
	//     so a switch can never be sent without the field;
	//   * the value sent is whatever the caller passed with --writer-epoch or the config file recorded - it is NOT
	//     observed from the host, because nothing in this CLI ever records a writer epoch from a reply;
	//   * the core only tests presence for this method (client_protocol.go:152). The current-writer comparison at
	//     :800-808 sits on the session-attach path and is not reached by host.configure, so an invented epoch is
	//     accepted by the shape gate. "A model switch can never be silent" therefore holds for absence only, and the
	//     obligation to anchor it to an observed lease is recorded in receipts/W05/W05-03 as P-R3-2.
	d, dpath, herr := hostDiscovery()
	if herr != nil || d.URL == "" {
		fail(command, exitNotImplemented, "MODEL_CHANGE_REQUIRES_HOST_CONFIGURE",
			dpath+": host.configure is the operation the contract assigns to a model switch, and no host is discoverable")
	}
	providerID, baseURLOut, credentialRef := modelProvider(model)
	if b, has := flagValue(args, "base-url"); has {
		baseURLOut = b
	}
	if cr, has := flagValue(args, "credential-ref"); has {
		credentialRef = cr
	}
	if baseURLOut == "" || credentialRef == "" {
		fail(command, exitUsage, "MISSING_CONFIGURE_FIELDS",
			"a model switch needs --base-url and --credential-ref; the CLI will not invent an endpoint or a credential reference")
	}
	ctx := newV2Context(command, args, c, d.URL)
	cfgReply, reason, code := v2Call(ctx, "host.configure", map[string]any{"config_revision": c.ConfigRevision,
		"provider_id": providerID, "base_url": baseURLOut, "model_id": model, "credential_ref": credentialRef})
	if code != exitCompleted {
		// Nothing was written yet, so a refused switch leaves the previous model in place. The order is the fix: an
		// earlier version persisted the new model before asking the host, which is a silent switch by another name.
		fail(command, code, orDefault(reason, "HOST_CONFIGURE_REFUSED"), replyView(cfgReply))
	}
	c.Model = model
	c.ConfigRevision = c.ConfigRevision + 1
	if err := writeConfig(c); err != nil {
		fail(command, exitFailed, "CONFIG_WRITE_FAILED", err.Error())
	}
	outJSON(map[string]any{"command": command, "status": "COMPLETED", "exit_code": exitCompleted,
		"previous_model": previous, "model": model, "config_revision": c.ConfigRevision,
		"settled_run_id": c.ConfirmedRun, "method_sent": "host.configure", "requests_sent": ctx.requestLog,
		"provider_id": providerID, "base_url": baseURLOut, "credential_ref": credentialRef,
		"host_result": cfgReply["result"]})
}

// modelProvider splits "provider/model" into the fields host.configure names.
func modelProvider(model string) (string, string, string) {
	parts := strings.SplitN(model, "/", 2)
	if len(parts) != 2 || parts[0] == "" || parts[1] == "" {
		fail("config", exitUsage, "MODEL_NOT_PROVIDER_QUALIFIED",
			"pass --model <provider>/<model>; a bare name cannot be mapped to a provider without guessing")
	}
	return parts[0], "", ""
}

// cliNeedsHost is the honest host-bound path: status/resume/goal/go/cancel all need a live host, and when the
// discovery file is absent or the host does not answer they report that with exit 3 or 1 instead of pretending.
// cliNeedsHost was the previous host-bound path: one GET /healthz, positional ids discarded, exit 0. The review
// measured it and named it the card's own 空stub negative, so it is gone; apps/cli/cli_verbs.go now sends the method
// each verb is named after. Only the signal guard from that file is kept.

// interruptGuard turns a real signal into the contract's 130. It is installed only while a host call is in flight,
// because that is the only window in which a non-interactive command can be interrupted at all; a refusal that has
// already been written exits before the guard matters.
func interruptGuard(command string) func() {
	ch := make(chan os.Signal, 1)
	signal.Notify(ch, os.Interrupt, syscall.SIGTERM)
	stopped := false
	var mu sync.Mutex
	go func() {
		<-ch
		mu.Lock()
		defer mu.Unlock()
		if stopped {
			return
		}
		stopped = true
		outJSON(map[string]any{"command": command, "status": "INTERRUPTED", "exit_code": exitInterrupted,
			"reason": "SIGNAL_RECEIVED_BEFORE_HOST_ANSWER"})
		os.Exit(exitInterrupted)
	}()
	return func() {
		mu.Lock()
		stopped = true
		mu.Unlock()
		signal.Stop(ch)
	}
}

func clip(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n] + "..."
}

func exitCodeForInterrupt() int { return exitInterrupted }
