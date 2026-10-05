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
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

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
			return nil, "MISSING_WRITER_EPOCH",
				"resume reads as the writer it observed: pass --writer-epoch <n> from the session you are continuing"
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
		return []v2Step{{"goal.start", map[string]any{"objective": objective, "contract_artifact_ids": refs,
			"start_as_draft": flagBool(args, "draft")}, ""}}, "", ""
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
	if err != nil {
		fail(name, exitNotImplemented, "HOST_DISCOVERY_UNAVAILABLE", path+": "+err.Error())
	}
	if d.URL == "" {
		fail(name, exitNotImplemented, "HOST_URL_EMPTY", path)
	}
	cfg, _ := readConfig()
	ctx := newV2Context(name, args, cfg, d.URL)
	steps, refusal, detail := verbSteps(name, args, ctx, cfg)
	if refusal != "" {
		fail(name, exitUsage, refusal, detail)
	}
	report := []map[string]any{}
	worst := exitCompleted
	worstReason := ""
	stop := interruptGuard(name)
	for _, s := range steps {
		if s.skipped != "" {
			report = append(report, map[string]any{"method": s.method, "status": "SKIPPED", "reason": s.skipped})
			continue
		}
		reply, reason, code := v2Call(ctx, s.method, s.payload)
		row := map[string]any{"method": s.method, "exit_code": code,
			"status": orDefault(statusOf(reply), orDefault(reason, "NO_REPLY"))}
		if reason != "" {
			row["reason"] = reason
			row["detail"] = replyView(reply)
		}
		if reply != nil {
			row["result"] = reply["result"]
			row["revision"] = reply["revision"]
		}
		report = append(report, row)
		if code > worst {
			worst, worstReason = code, reason
		}
	}
	stop()
	out := map[string]any{"command": name, "exit_code": worst, "operations": report,
		"requests_sent": ctx.requestLog, "host_url": d.URL, "client_id": ctx.clientID}
	if worst == exitCompleted {
		out["status"] = "COMPLETED"
		outJSON(out)
		return
	}
	out["status"] = "REJECTED"
	if worstReason != "" {
		out["reason"] = worstReason
	}
	outJSON(out)
	os.Exit(worst)
}

// newV2Context reads the current short local credential without opening a UI.
// Explicit init is the only verb permitted to renew it through the native bridge.
func newV2Context(name string, args []string, cfg cliConfig, baseURL string) *v2Context {
	credential := os.Getenv("RESEARCHOS_CLI_CREDENTIAL")
	if credential == "" {
		if d, _, err := hostDiscovery(); err == nil && d.URL == baseURL {
			credential, _ = cliSessionCredential(d)
		}
	}
	ctx := &v2Context{
		clientID:   cliEnv("RESEARCHOS_CLI_CLIENT_ID", defaultClientID()),
		credential: credential,
		projectID:  cfg.ProjectID,
		sessionID:  cfg.SessionID,
		// A slash alias would otherwise put "/" inside the command id, which the published identifier pattern
		// refuses; the id is this card's own to mint, so it is sanitised here rather than rejected downstream.
		commandID: "cmd-" + strings.ReplaceAll(name, "/", "-") + "-" + strconv.Itoa(os.Getpid()),
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

// cliInteractive is the contract's `researchos [--project <path-or-id>]`, whose local operations are session.list,
// session.create, session.attach and session.send. The review caught the card attributing the interactive surface to
// "a later card" that this plan does not contain; the contract marks the command required, so it is delivered here.
// A piped stdin is a supported input, which is also what makes this command measurable rather than aspirational.
func cliInteractive(args []string) {
	d, path, err := hostDiscovery()
	if err != nil {
		fail("interactive", exitNotImplemented, "INTERACTIVE_HOST_UNAVAILABLE", path+": "+err.Error())
	}
	cfg, _ := readConfig()
	ctx := newV2Context("interactive", args, cfg, d.URL)
	if ctx.credential == "" {
		fail("interactive", exitNotImplemented, "CREDENTIAL_ABSENT",
			"the CLI never invents a bearer token; the local host issues it and the CLI reads RESEARCHOS_CLI_CREDENTIAL")
	}
	lines := []string{}
	sc := bufio.NewScanner(os.Stdin)
	sc.Buffer(make([]byte, 0, 4096), 1<<20)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line != "" {
			lines = append(lines, line)
		}
	}
	steps := []v2Step{{"session.list", map[string]any{"cursor": nil, "limit": 20}, ""}}
	if sid, has := flagValue(args, "session"); has {
		ctx.sessionID = sid
		steps = append(steps, v2Step{"session.attach", map[string]any{"after_sequence": intFlag(args, "after-sequence", 0),
			"request_write_owner": flagBool(args, "take-writer")}, ""})
	} else {
		title := "interactive session"
		if len(lines) > 0 {
			title = clip(lines[0], 60)
		}
		steps = append(steps, v2Step{"session.create", map[string]any{"workspace_ref": cfg.WorkspaceRef,
			"model_config_ref": cfg.Model, "title": title}, ""})
	}
	for _, line := range lines {
		steps = append(steps, v2Step{"session.send", map[string]any{"text": line,
			"attachment_artifact_ids": []any{}, "delivery": "NORMAL"}, ""})
	}
	report := []map[string]any{}
	worst := exitCompleted
	stop := interruptGuard("interactive")
	baseCommand := ctx.commandID
	methodCalls := map[string]int{}
	for _, s := range steps {
		ctx.commandID = v2FlowCommandID(baseCommand, s.method, methodCalls[s.method])
		methodCalls[s.method]++
		previousSession := ctx.sessionID
		reply, reason, code := v2Call(ctx, s.method, s.payload)
		row := map[string]any{"method": s.method, "exit_code": code,
			"status": orDefault(statusOf(reply), orDefault(reason, "NO_REPLY"))}
		if reply != nil {
			// Only session.create mints a session, so only its answer is adopted; an identity the caller named, or
			// one a listing happened to echo, is never substituted for it.
			if res, isMap := reply["result"].(map[string]any); isMap && previousSession == "" && s.method == "session.create" {
				// Only a flow that had no session adopts one; a --session the user typed is never overwritten by a
				// reply, which is what made an attach report a session other than the one it attached to.
				if sid, has := res["session_id"].(string); has && sid != "" {
					ctx.sessionID = sid
					row["session_id_adopted"] = sid
				}
			}
			row["revision"] = reply["revision"]
		}
		if reason != "" {
			row["reason"] = reason
		}
		report = append(report, row)
		if code > worst {
			worst = code
		}
	}
	stop()
	status := "COMPLETED"
	if worst != exitCompleted {
		status = "REJECTED"
	}
	outJSON(map[string]any{"command": "interactive", "status": status, "exit_code": worst,
		"operations": report, "requests_sent": ctx.requestLog, "client_id": ctx.clientID,
		"session_id": ctx.sessionID, "messages_read_from_stdin": len(lines)})
	if worst != exitCompleted {
		os.Exit(worst)
	}
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
