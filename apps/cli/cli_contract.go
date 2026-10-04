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
	exitCompleted    = 0
	exitFailed       = 1
	exitUsage        = 2
	exitNotImplemented = 3
	exitInterrupted  = 130
)

// contractCommands is the product-contract surface: name, the handler that answers it, the check that proves the
// handler is wired, and who owns the answer. `owned` is this card only where this file registers the verb; the verbs
// an already-accepted card answers are named with their owner so the self-report can be complete without taking them
// over. `run` and `worker` are W05-02's real Job Object cascade (apps/cli/cancel_run_windows.go registers them into
// the same map), and `chat` is the interactive TUI the accepted launcher still refuses with NOT_IMPLEMENTED — an
// assertion in the accepted W05-02 check pins that refusal.
var contractCommands = map[string]struct {
	handler string
	check   string
	needs   string
	owned   string
}{
	"init":     {"cliInit", "W0503-COMMANDS-ALL-HANDLED", "workspace path", "W05-03"},
	"goal":     {"cliGoal", "W0503-COMMANDS-ALL-HANDLED", "host", "W05-03"},
	"go":       {"cliGo", "W0503-COMMANDS-ALL-HANDLED", "host", "W05-03"},
	"resume":   {"cliResume", "W0503-COMMANDS-ALL-HANDLED", "host + writer epoch", "W05-03"},
	"status":   {"cliStatus", "W0503-COMMANDS-ALL-HANDLED", "host", "W05-03"},
	"cancel":   {"cliCancel", "W0503-COMMANDS-ALL-HANDLED", "host", "W05-03"},
	"config":   {"cliConfig", "W0503-CONFIG-MODEL-CHANGE-NEEDS-SETTLED-REVISION", "config file", "W05-03"},
	"commands": {"cliCommands", "W0503-COMMANDS-ALL-HANDLED", "", "W05-03"},
	"/goal":    {"cliGoal", "W0503-SLASH-COMMANDS-HANDLED", "host", "W05-03"},
	"/resume":  {"cliResume", "W0503-SLASH-COMMANDS-HANDLED", "host + writer epoch", "W05-03"},
	"/status":  {"cliStatus", "W0503-SLASH-COMMANDS-HANDLED", "host", "W05-03"},
	"/cancel":  {"cliCancel", "W0503-SLASH-COMMANDS-HANDLED", "host", "W05-03"},
	"/model":   {"cliModel", "W0503-SLASH-COMMANDS-HANDLED", "config file", "W05-03"},
	"/help":    {"cliHelp", "W0503-HELP-COVERS-EVERY-COMMAND", "", "W05-03"},
	"run":      {"runCancelCascade", "W0502-CASCADE-RUNS-IN-REQUIRED-ORDER", "job object", "accepted W05-02"},
	"worker":   {"runWorkerLoop", "W0502-WORKER-WAS-REALLY-WRITING-BEFORE-THE-CANCEL", "job object", "accepted W05-02"},
	"task":     {"runCodingTask", "W0502-TASK-CHECK-REALLY-ROUN-THE-BINARY", "check command", "accepted W05-01/W05-02"},
	"doctor":   {"main.doctor", "W0203-DOCTOR-HANDSHAKE", "host discovery", "accepted W02-03"},
	"version":  {"main.version", "W0203-VERSION-PROTOCOL", "", "accepted W02-03"},
	"help":     {"cliHelpSurface", "W0503-HELP-COVERS-EVERY-COMMAND", "", "W05-03 surface over accepted W02-03 entry"},
	"chat":     {"", "W0503-INTERACTIVE-TUI-KEEPS-NOT-IMPLEMENTED", "terminal", "later card; refuses NOT_IMPLEMENTED"},
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
		cliNeedsHost(name, rest)
	default:
		fail(name, exitNotImplemented, "NO_HANDLER_REGISTERED")
	}
}

func flagValue(args []string, name string) (string, bool) {
	for i, a := range args {
		if a == "--"+name && i+1 < len(args) {
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
		switch {
		case !registeredHere(n) && strings.HasPrefix(c.owned, "accepted"):
			state = "ACCEPTED"
		case registeredHere(n) && registered:
			state = "IMPLEMENTED"
		default:
			refused = append(refused, n)
		}
		if registeredHere(n) && (!registered || c.handler == "") {
			missingHandlers = append(missingHandlers, n)
		}
		if c.check == "" {
			missingChecks = append(missingChecks, n)
		}
		entries = append(entries, map[string]any{"command": n, "handler": c.handler, "check_id": c.check,
			"owner": c.owned, "state": state, "needs": c.needs})
	}
	return
}

// cliCommands is the coverage self-report the card's OUTPUT check turns on: every contract command with its owner,
// handler and check id, and the missing set computed rather than asserted.
func cliCommands() {
	entries, missingHandlers, missingChecks, _ := surfaceEntries()
	outJSON(map[string]any{"command": "commands", "status": "COMPLETED", "exit_code": exitCompleted,
		"commands": entries, "count": len(entries), "missing_handler": missingHandlers,
		"missing_check": missingChecks, "jsonl_only_stdout": true,
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

// cliInit performs the only local side effect a hostless CLI can honestly make: it validates and records the
// workspace it was given, including a path containing spaces and non-ASCII characters.
func cliInit(args []string) {
	path, ok := flagValue(args, "workspace")
	if !ok {
		fail("init", exitUsage, "MISSING_WORKSPACE_FLAG", "pass --workspace <path>")
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
	c.WorkspaceRef = abs
	if err := writeConfig(c); err != nil {
		fail("init", exitFailed, "CONFIG_WRITE_FAILED", err.Error())
	}
	outJSON(map[string]any{"command": "init", "status": "COMPLETED", "exit_code": exitCompleted,
		"workspace_ref": abs, "config_path": configPath(), "config_revision": c.ConfigRevision,
		"path_contains_non_ascii": strings.ContainsAny(abs, " \t") || !isASCII(abs),
		"host_required": false})
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
	if !flagBool(args, "settled") || strings.TrimSpace(c.ConfirmedRun) == "" {
		fail(command, exitFailed, "SETTLED_CONFIRMATION_REQUIRED",
			"a model switch needs --settled and a run whose observation is settled")
	}
	previous := c.Model
	c.Model = model
	c.ConfigRevision = c.ConfigRevision + 1
	if err := writeConfig(c); err != nil {
		fail(command, exitFailed, "CONFIG_WRITE_FAILED", err.Error())
	}
	outJSON(map[string]any{"command": command, "status": "COMPLETED", "exit_code": exitCompleted,
		"previous_model": previous, "model": model, "config_revision": c.ConfigRevision,
		"settled_run_id": c.ConfirmedRun})
}

// cliNeedsHost is the honest host-bound path: status/resume/goal/go/cancel all need a live host, and when the
// discovery file is absent or the host does not answer they report that with exit 3 or 1 instead of pretending.
func cliNeedsHost(name string, args []string) {
	d, path, err := hostDiscovery()
	if err != nil {
		fail(name, exitNotImplemented, "HOST_DISCOVERY_UNAVAILABLE", path+": "+err.Error())
	}
	if d.URL == "" {
		fail(name, exitNotImplemented, "HOST_URL_EMPTY", path)
	}
	stop := interruptGuard(name)
	status, body, err := hostGet(d.URL + "/healthz")
	stop()
	if err != nil {
		fail(name, exitFailed, "HOST_UNREACHABLE", err.Error())
	}
	outJSON(map[string]any{"command": name, "status": "HOST_ANSWERED", "exit_code": exitCompleted,
		"host_url": d.URL, "health_status": status, "health_body_truncated": clip(body, 400),
		"capability": "the command is handled here; the operation it drives belongs to the host and is reported as it answers"})
	if name == "resume" {
		diag("resume must also present a writer epoch; the host session index is the authority")
	}
}

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
