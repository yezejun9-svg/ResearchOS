// apps/cli/cli_verbs.go binds each host-bound CLI verb to the protocol operations contracts/product.contract.json
// declares for its syntax, with the ids the user actually passed.
//
// Two failures are answered here. The review's first blocker measured that the verbs produced one GET /healthz,
// discarded every positional id and exited 0 — the card's own 空stub negative. And the review's P-R1-11 measured that
// the delivered syntaxes were not the contract's: `researchos init <path>` and `researchos resume <session-id>` are
// positional in the contract, `status` names two operations, and `config` names host.configure rather than a local
// file edit. Each verb now walks the contract's operation list and reports every leg it sent.
package main

import (
	"bufio"
	"context"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"time"
)

type cliInputLine struct {
	text string
	err  error
}

var cliInputPumps sync.Map // *v2Context -> receive-only channel; reader never writes context.

// v2Step is one protocol operation of a command. A command may name several, and the record shows each one's
// outcome: a verb that silently performed one of two operations is the failure mode this file exists to prevent.
type v2Step struct {
	method  string
	payload map[string]any
	skipped string
}

func firstPositional(args []string) (string, bool) {
	sawFlagValue := false
	for i, a := range args {
		if sawFlagValue {
			sawFlagValue = false
			continue
		}
		if strings.HasPrefix(a, "--") {
			// --flag value takes the next argument; --flag=value does not.
			if !strings.Contains(a, "=") && i+1 < len(args) && !strings.HasPrefix(args[i+1], "--") {
				sawFlagValue = true
			}
			continue
		}
		return a, true
	}
	return "", false
}

func intFlag(args []string, name string, def int64) int64 {
	if v, ok := flagValue(args, name); ok {
		n, err := strconv.ParseInt(v, 10, 64)
		if err == nil {
			return n
		}
	}
	return def
}

// verbSteps returns the operations the contract assigns to this verb, in the order the contract lists them.
func verbSteps(name string, args []string, ctx *v2Context, cfg cliConfig) ([]v2Step, string, string) {
	switch name {
	case "status", "/status":
		steps := []v2Step{}
		if ctx.sessionID != "" {
			steps = append(steps, v2Step{"session.get", map[string]any{}, ""})
		} else {
			steps = append(steps, v2Step{method: "session.get",
				skipped: "NO_SESSION_REFERENCE: pass --session or record one with resume; the leg is reported, not hidden"})
		}
		return append(steps, v2Step{"host.status", map[string]any{}, ""}), "", ""
	case "resume", "/resume":
		session, has := flagValue(args, "session")
		if !has {
			session, has = firstPositional(args)
		}
		if !has {
			return nil, "MISSING_SESSION_REFERENCE",
				"resume takes the session id, positionally as the contract writes it or with --session"
		}
		ctx.sessionID = session
		epoch, hasEpoch := flagValue(args, "writer-epoch")
		if !hasEpoch {
			return []v2Step{
				{"session.get", map[string]any{}, ""},
				{"session.attach", map[string]any{"after_sequence": intFlag(args, "after-sequence", 0), "request_write_owner": true}, ""},
				{"session.get", map[string]any{}, ""},
				{"session.control", map[string]any{"action": "RESUME", "target_id": session, "reason": "resuming saved context from the CLI"}, ""},
				{"session.events", map[string]any{"after_sequence": intFlag(args, "after-sequence", 0), "limit": 200}, ""},
			}, "", ""
		}
		e, err := strconv.ParseInt(epoch, 10, 64)
		if err != nil || e < 0 {
			return nil, "INVALID_WRITER_EPOCH", epoch
		}
		ctx.epoch = e
		after := intFlag(args, "after-sequence", 0)
		reason, _ := flagValue(args, "reason")
		if reason == "" {
			reason = "resuming from the CLI"
		}
		return []v2Step{
			{"session.attach", map[string]any{"after_sequence": after, "request_write_owner": false}, ""},
			{"session.control", map[string]any{"action": "RESUME", "target_id": session, "reason": reason}, ""},
		}, "", ""
	case "goal", "go", "/goal":
		objective, has := firstPositional(args)
		if !has {
			return nil, "MISSING_OBJECTIVE", "goal takes an objective: researchos goal \"<objective>\""
		}
		refs := []any{}
		if r, has := flagValue(args, "contract-artifact-refs"); has {
			for _, p := range strings.Split(r, ",") {
				if p != "" {
					refs = append(refs, p)
				}
			}
		}
		steps := []v2Step{}
		if ctx.sessionID != "" {
			steps = append(steps, v2Step{"session.get", map[string]any{}, ""})
		}
		return append(steps, v2Step{"goal.start", map[string]any{"objective": objective, "contract_artifact_ids": refs,
			"start_as_draft": flagBool(args, "draft")}, ""}), "", ""
	case "cancel", "/cancel":
		target, has := flagValue(args, "run")
		if !has {
			target, has = firstPositional(args)
		}
		if !has {
			return nil, "MISSING_RUN_REFERENCE", "cancel takes a run or goal id, positionally as the contract writes it"
		}
		if s, has := flagValue(args, "session"); has {
			ctx.sessionID = s
		}
		reason, _ := flagValue(args, "reason")
		if reason == "" {
			reason = "requested from the CLI"
		}
		return []v2Step{{"session.control", map[string]any{"action": "CANCEL", "target_id": target,
			"reason": reason}, ""}}, "", ""
	case "run", "/run":
		prompt, has := firstPositional(args)
		if !has {
			return nil, "MISSING_PROMPT", "run takes a prompt: researchos run \"<prompt>\" --project <id> --output jsonl"
		}
		refs := []any{}
		if s, has := flagValue(args, "session"); has {
			ctx.sessionID = s
		}
		steps := []v2Step{}
		if ctx.sessionID == "" {
			steps = append(steps, v2Step{"session.create", map[string]any{"workspace_ref": cfg.WorkspaceRef, "model_config_ref": cfg.Model, "title": clip(prompt, 60)}, ""})
		} else {
			steps = append(steps, v2Step{"session.get", map[string]any{}, ""})
		}
		return append(steps, []v2Step{
			{"session.send", map[string]any{"text": prompt, "attachment_artifact_ids": refs, "delivery": "NORMAL"}, ""},
			{"session.events", map[string]any{"after_sequence": intFlag(args, "after-sequence", 0), "limit": 200}, ""},
		}...), "", ""
	default:
		return nil, "NO_METHOD_BOUND", name
	}
}

// cliHostCommand sends every step the contract assigns to the verb. The exit code is the worst one any step earned,
// so a host that refuses one leg cannot be reported as a completed command.
func cliHostCommand(name string, args []string) {
	d, path, err := hostDiscovery()
	if err != nil || d.URL == "" {
		fail(name, exitNotImplemented, "HOST_DISCOVERY_UNAVAILABLE", path)
	}
	cfg, _ := readConfig()
	c := newV2Context(name, args, cfg, d.URL)
	signals, stop := interruptGuard()
	defer stop()
	out, code := runCLIVerb(name, args, c, cfg, defaultCLIFollowOptions(signals))
	code = cliFlowSummary(out, code, c, &cfg)
	if code != 0 {
		os.Exit(code)
	}
}

// Existing local projects renew their short credential through the same-SID
// native bridge. Renewal never opens the workspace chooser.
func newV2Context(name string, args []string, cfg cliConfig, baseURL string) *v2Context {
	credential := os.Getenv("RESEARCHOS_CLI_CREDENTIAL")
	if credential == "" {
		if d, _, err := hostDiscovery(); err == nil && d.URL == baseURL {
			credential, _ = cliSessionCredential(d)
			if credential == "" && cfg.ProjectID != "" && cfg.WorkspaceRef != "" {
				credential, _ = cliInitCredential(d, cliEnv("RESEARCHOS_CLI_CLIENT_ID", defaultClientID()))
			}
		}
	}
	ctx := &v2Context{
		clientID:   cliEnv("RESEARCHOS_CLI_CLIENT_ID", defaultClientID()),
		credential: credential,
		projectID:  cfg.ProjectID,
		sessionID:  cfg.SessionID,
		// A slash alias would otherwise put "/" inside the command id, which the published identifier pattern
		// refuses; the id is this card's own to mint, so it is sanitised here rather than rejected downstream.
		commandID: "cmd-" + strings.ReplaceAll(name, "/", "-") + "-" + strconv.Itoa(os.Getpid()) + "-" + strconv.FormatInt(time.Now().UnixNano(), 36),
		baseURL:   baseURL,
	}
	if p, has := flagValue(args, "project"); has {
		ctx.projectID = p
	}
	if s, has := flagValue(args, "session"); has {
		ctx.sessionID = s
	}
	ctx.revision = intFlag(args, "expected-revision", cfg.Revision)
	ctx.epoch = intFlag(args, "writer-epoch", cfg.WriterEpoch)
	return ctx
}

// The scanner only forwards text. The turn follower remains the sole context
// and network writer while it admits durable queue controls during execution.
func cliInteractive(args []string) {
	d, path, err := hostDiscovery()
	if err != nil || d.URL == "" {
		fail("interactive", exitNotImplemented, "INTERACTIVE_HOST_UNAVAILABLE", path)
	}
	cfg, _ := readConfig()
	c := newV2Context("interactive", args, cfg, d.URL)
	if c.credential == "" {
		fail("interactive", exitNotImplemented, "CREDENTIAL_ABSENT")
	}
	signals, stop := interruptGuard()
	defer stop()
	options := defaultCLIFollowOptions(signals)
	// Discover existing sessions through the same protocol before accepting
	// input. Never adopt a session identity merely echoed by this listing.
	reply, reason, code := v2Call(c, "session.list", map[string]any{"cursor": nil, "limit": 20})
	if code != 0 || statusOf(reply) != "COMPLETED" {
		if code == 0 {
			code = exitNotImplemented
		}
		fail("interactive", code, orDefault(reason, "SESSION_LIST_PENDING"))
	}
	if c.sessionID != "" {
		if reason, code := cliInteractivePrepare(c, cfg, "", options, true); code != 0 {
			fail("interactive", code, reason)
		}
	}
	lines := make(chan cliInputLine, 16)
	cliInputPumps.Store(c, (<-chan cliInputLine)(lines))
	defer cliInputPumps.Delete(c)
	done := make(chan struct{})
	defer close(done)
	go func() {
		defer close(lines)
		scanner := bufio.NewScanner(os.Stdin)
		scanner.Buffer(make([]byte, 4096), 1<<20)
		for scanner.Scan() {
			select {
			case lines <- cliInputLine{text: scanner.Text()}:
			case <-done:
				return
			}
		}
		if err := scanner.Err(); err != nil {
			select {
			case lines <- cliInputLine{err: err}:
			case <-done:
			}
		}
	}()
	base, turn, multiline := c.commandID, 0, ""
	for {
		select {
		case <-signals:
			outJSON(map[string]any{"command": "interactive", "status": "INTERRUPTED_IDLE", "exit_code": exitInterrupted,
				"session_id": c.sessionID, "reason": "NO_ACTIVE_CLI_TURN"})
			os.Exit(exitInterrupted)
		case input, open := <-lines:
			if !open {
				if multiline != "" {
					fail("interactive", exitUsage, "INCOMPLETE_MULTILINE_INPUT")
				}
				return
			}
			if input.err != nil {
				fail("interactive", exitUsage, "INPUT_READ_FAILED")
			}
			line := strings.TrimSpace(input.text)
			if strings.HasSuffix(line, "\\") {
				multiline += strings.TrimSuffix(line, "\\") + "\n"
				continue
			}
			line = multiline + line
			multiline = ""
			if strings.TrimSpace(line) == "" {
				continue
			}
			turn++
			c.commandID, c.requestLog = cliStreamIdentity(base, turn), nil
			name, commandArgs := "run", []string{line}
			if strings.HasPrefix(line, "/") {
				name, commandArgs = cliInteractiveSlash(line)
				switch name {
				case "/help":
					cliHelp()
					continue
				case "/model":
					if err := saveCLIContext(c, &cfg); err != nil {
						fail("interactive", exitFailed, "CONFIG_WRITE_FAILED")
					}
					cliModel(commandArgs)
					cfg, _ = readConfig()
					continue
				case "/goal", "/run", "/resume", "/status", "/cancel":
				default:
					fail("interactive", exitUsage, "UNKNOWN_SLASH_COMMAND", name)
				}
			}
			if name == "run" || name == "/run" {
				prompt, _ := firstPositional(commandArgs)
				if reason, code := cliInteractivePrepare(c, cfg, prompt, options, false); code != 0 {
					out := map[string]any{"command": "interactive", "status": "REJECTED", "reason": reason, "exit_code": code, "requests_sent": c.requestLog}
					code = cliFlowSummary(out, code, c, &cfg)
					os.Exit(code)
				}
			}
			out, code := runCLIVerb(name, commandArgs, c, cfg, options)
			code = cliFlowSummary(out, code, c, &cfg)
			if code != 0 {
				os.Exit(code)
			}
		}
	}
}

// Opening a session is read-only. An explicit ordinary message may acquire an
// unowned session, but never takes a foreign or expired writer lease implicitly.
func cliInteractivePrepare(c *v2Context, cfg cliConfig, prompt string, options cliFollowOptions, opening bool) (string, int) {
	budget, stop := context.WithTimeout(context.Background(), options.timeout)
	defer stop()
	f := &cliFlow{c: c, budget: budget, options: options, base: v2FlowCommandID(c.commandID, "interactive.prepare", -1)}
	if opening {
		_, reason, code := f.call("session.attach", map[string]any{"after_sequence": 0, "request_write_owner": false}, true)
		return reason, code
	}
	created := c.sessionID == ""
	method, payload := "session.get", map[string]any{}
	if created {
		method = "session.create"
		payload = map[string]any{"workspace_ref": cfg.WorkspaceRef, "model_config_ref": cfg.Model, "title": clip(prompt, 60)}
	}
	reply, reason, code := f.call(method, payload, true)
	if code != 0 {
		return reason, code
	}
	snapshot := cliSnapshot(reply)
	writer := cliObject(snapshot["writer"])
	if writer != nil {
		if writer["client_id"] != c.clientID {
			return "HOST_REJECTED:WRITER_BUSY", exitNotImplemented
		}
		expires, err := time.Parse(time.RFC3339Nano, continuationString(writer, "expires_at"))
		if err != nil || !time.Now().Before(expires) {
			return "HOST_REJECTED:LEASE_EXPIRED", exitNotImplemented
		}
		epoch, ok := cliInteger(writer["epoch"])
		if !ok || epoch < 1 {
			return "ATTACH_WRITER_UNRESOLVED", exitNotImplemented
		}
		// A completed create already granted this exact writer lease. It is
		// subject to the same fresh expiry check as an existing own writer.
		return "", exitCompleted
	}
	_, reason, code = f.call("session.attach", map[string]any{"after_sequence": 0, "request_write_owner": true}, true)
	return reason, code
}

func statusOf(reply map[string]any) string {
	if reply == nil {
		return ""
	}
	s, _ := reply["status"].(string)
	return s
}

// replyView keeps a refusal readable without letting a long host message break the one-line JSONL record.
func replyView(reply map[string]any) string {
	if reply == nil {
		return "no reply"
	}
	code, _ := reply["error_code"].(string)
	msg := ""
	if e, isObj := reply["error"].(map[string]any); isObj {
		msg, _ = e["message"].(string)
	}
	return clip(strings.TrimSpace(code+" "+msg), 400)
}

func defaultClientID() string {
	h, err := os.Hostname()
	if err != nil || h == "" {
		h = "unknown-host"
	}
	return "cli-" + h + "-" + filepath.Base(os.Args[0])
}
