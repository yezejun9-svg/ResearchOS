package main

import (
	"context"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"io"
	"math"
	"net/http"
	"net/url"
	"os"
	"strings"
	"sync"
	"syscall"
	"time"
)

// Only a read-only status call uses this observer. Its goroutine cancels the
// request context; the calling goroutine remains the sole context/log writer.
type cliReadInterrupt struct {
	mu          sync.Mutex
	interrupted bool
	finished    bool
	cancel      context.CancelFunc
	stop        chan struct{}
	done        chan struct{}
}

func observeCLIReadInterrupt(signals <-chan os.Signal, cancel context.CancelFunc) *cliReadInterrupt {
	r := &cliReadInterrupt{cancel: cancel, stop: make(chan struct{}), done: make(chan struct{})}
	go func() {
		defer close(r.done)
		for {
			select {
			case <-r.stop:
				return
			case signal, ok := <-signals:
				if !ok {
					return
				}
				if signal != os.Interrupt && signal != syscall.SIGTERM {
					continue
				}
				r.mu.Lock()
				if !r.finished {
					r.interrupted = true
					r.cancel()
				}
				r.mu.Unlock()
				return
			}
		}
	}()
	return r
}

func (r *cliReadInterrupt) observed() bool {
	r.mu.Lock()
	defer r.mu.Unlock()
	return r.interrupted
}

// This is the report's linearization point. A later signal cannot change it,
// and the observer is joined before the caller returns or saves its context.
func (r *cliReadInterrupt) finish() bool {
	r.mu.Lock()
	if !r.finished {
		r.finished = true
		close(r.stop)
	}
	interrupted := r.interrupted
	r.mu.Unlock()
	<-r.done
	return interrupted
}

func (f *cliFlow) finishReadResult(code int, reason string) (int, string) {
	if f.readInterrupt != nil && f.readInterrupt.finish() && code == exitCompleted {
		return exitInterrupted, "READ_INTERRUPTED"
	}
	return code, reason
}

// These bounds govern observation, never a retry of model/tool execution.
type cliFollowOptions struct {
	timeout, poll, cancelTimeout time.Duration
	interrupts                   <-chan os.Signal
	emit                         func(map[string]any)
}

func defaultCLIFollowOptions(signals <-chan os.Signal) cliFollowOptions {
	return cliFollowOptions{15 * time.Minute, 200 * time.Millisecond, 30 * time.Second, signals, outJSON}
}

type cliFlow struct {
	c                    *v2Context
	budget               context.Context
	options              cliFollowOptions
	base                 string
	ordinal              int
	cancelRequested      bool
	cancelDeadline       time.Time
	operations           []map[string]any
	admissionCommand     string
	goalFlow             bool
	inputs               <-chan cliInputLine
	cancelCommand        *v2Context
	cancelPayload        map[string]any
	readInterrupt        *cliReadInterrupt
	responseExit         int
	transportUnreachable bool
}

func (f *cliFlow) interrupt() {
	if f.cancelRequested {
		return
	}
	select {
	case <-f.options.interrupts:
		f.cancelRequested = true
		f.cancelDeadline = time.Now().Add(f.options.cancelTimeout)
	default:
	}
}

func (f *cliFlow) expired() bool {
	f.interrupt()
	return f.budget.Err() != nil || !f.cancelDeadline.IsZero() && !time.Now().Before(f.cancelDeadline)
}

func (f *cliFlow) pause() {
	timer := time.NewTimer(f.options.poll)
	defer timer.Stop()
	if f.readInterrupt != nil {
		select {
		case <-timer.C:
		case <-f.budget.Done():
		}
		return
	}
	if f.cancelRequested {
		select {
		case <-timer.C:
		case <-f.budget.Done():
		}
		return
	}
	select {
	case <-timer.C:
	case <-f.budget.Done():
	case <-f.options.interrupts:
		f.cancelRequested = true
		f.cancelDeadline = time.Now().Add(f.options.cancelTimeout)
	}
}

// Pending method replies replay the exact original envelope. In particular,
// a revision learned while waiting must not change an idempotent write body.
func (f *cliFlow) call(method string, payload map[string]any, wait bool) (map[string]any, string, int) {
	f.ordinal++
	f.transportUnreachable = false
	sent := *f.c
	sent.commandID = v2FlowCommandID(f.base, method, f.ordinal)
	if method == "session.attach" && payload["request_write_owner"] == true {
		sent.epoch = 0
	}
	if method == "session.control" && payload["action"] == "CANCEL" {
		frozen := sent
		f.cancelCommand = &frozen
		f.cancelPayload = payload
	}
	if method == "session.send" || method == "goal.start" {
		f.admissionCommand = sent.commandID
	}
	attempted := false
	for {
		if f.expired() {
			if f.readInterrupt != nil && f.readInterrupt.observed() {
				return nil, "READ_INTERRUPTED", exitInterrupted
			}
			return nil, "WAIT_FOR_SETTLEMENT", exitNotImplemented
		}
		if (method == "session.send" || method == "goal.start") && f.cancelRequested && !attempted {
			return nil, "CANCELLED_BEFORE_ADMISSION", exitInterrupted
		}
		attempted = true
		attempt := sent
		attempt.requestLog = nil
		var reply map[string]any
		var reason string
		var code int
		var cause cliTransportCause
		reply, reason, code, cause = v2CallTransportDetailed(f.budget, &attempt, method, payload, true)
		cancelledIO := cause.cancelled
		f.transportUnreachable = cause.unreachable
		f.c.requestLog = append(f.c.requestLog, attempt.requestLog...)
		if cancelledIO && f.readInterrupt != nil && f.budget.Err() == context.Canceled && f.readInterrupt.observed() {
			return nil, "READ_INTERRUPTED", exitInterrupted
		}
		if code != exitCompleted {
			return reply, reason, code
		}
		status := statusOf(reply)
		if status == "COMPLETED" {
			if method == "session.attach" && payload["request_write_owner"] == true {
				snap := cliSnapshot(reply)
				writer := cliObject(snap["writer"])
				expires, err := time.Parse(time.RFC3339Nano, continuationString(writer, "expires_at"))
				epoch, ok := cliInteger(writer["epoch"])
				if cliObject(reply["result"])["write_owner_acquired"] != true || writer["client_id"] != f.c.clientID || !ok || epoch < 1 || err != nil || !time.Now().Before(expires) {
					return reply, "ATTACH_WRITER_UNRESOLVED", exitNotImplemented
				}
			}
			if method == "goal.start" {
				if why := adoptCLIGoal(f.c, reply, payload["start_as_draft"] == true); why != "" {
					return reply, why, exitNotImplemented
				}
			} else if f.goalFlow && method == "session.get" {
				snap := cliSnapshot(reply)
				doc, err := cliProtocolDocument()
				if err != nil || doc.ValidateDef("SessionSnapshot", snap) != nil || snap["session_id"] != f.c.sessionID || snap["project_id"] != f.c.projectID {
					return reply, "INVALID_GOAL_SESSION_SNAPSHOT", exitNotImplemented
				}
				writer := cliObject(snap["writer"])
				epoch, valid := cliInteger(writer["epoch"])
				if writer["client_id"] != f.c.clientID || !valid || epoch < 1 {
					return reply, "GOAL_WRITER_UNRESOLVED", exitNotImplemented
				}
				adoptV2Snapshot(f.c, reply)
			} else {
				adoptV2Snapshot(f.c, reply)
			}
			return reply, "", exitCompleted
		}
		if !wait {
			return reply, "WAIT_FOR_SETTLEMENT", exitNotImplemented
		}
		// ACKNOWLEDGED confirms receipt only; replay the same original envelope.
		f.pause()
	}
}

func cliObject(value any) map[string]any {
	m, _ := value.(map[string]any)
	return m
}

func cliSnapshot(reply map[string]any) map[string]any {
	result := cliObject(reply["result"])
	if nested := cliObject(result["snapshot"]); nested != nil {
		return nested
	}
	return result
}

func cliInteger(value any) (int64, bool) {
	if n, ok := value.(json.Number); ok {
		return configureExactInteger(n)
	}
	v, ok := value.(float64)
	return int64(v), ok && v >= 0 && v < 1<<53 && math.Trunc(v) == v
}

func (f *cliFlow) snapshot() (map[string]any, string, int) {
	reply, reason, code := f.call("session.get", map[string]any{}, true)
	if code != 0 {
		return nil, reason, code
	}
	snap := cliSnapshot(reply)
	if snap["project_id"] != f.c.projectID || snap["session_id"] != f.c.sessionID || snap["protocol_version"] != clientProtocol {
		return nil, "SNAPSHOT_SCOPE_MISMATCH", exitNotImplemented
	}
	return snap, "", 0
}

// Only public Owner-scoped reads are used. No SQLite or credentials file is
// opened by the follower, and redirects cannot forward its bearer credential.
func (f *cliFlow) object(collection, id string) (map[string]any, string) {
	if !continuationID(f.c.projectID) || !continuationID(id) {
		return nil, "EXECUTION_INVALID_IDENTITY"
	}
	path := "/v1/projects/" + url.PathEscape(f.c.projectID) + "/" + collection + "/" + url.PathEscape(id)
	req, err := http.NewRequestWithContext(f.budget, http.MethodGet, strings.TrimRight(f.c.baseURL, "/")+path, nil)
	if err != nil {
		return nil, "EXECUTION_INVALID_URL"
	}
	req.Header.Set("Authorization", "Bearer "+f.c.credential)
	f.c.requestLog = append(f.c.requestLog, "GET "+path)
	client := http.Client{Timeout: 8 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	resp, err := client.Do(req)
	if err != nil {
		return nil, "EXECUTION_READ_UNRESOLVED"
	}
	defer resp.Body.Close()
	raw, err := io.ReadAll(io.LimitReader(resp.Body, (2<<20)+1))
	if err != nil || len(raw) > 2<<20 || resp.StatusCode != http.StatusOK {
		return nil, "EXECUTION_READ_UNRESOLVED"
	}
	var value map[string]any
	if json.Unmarshal(raw, &value) != nil || value["id"] != id || value["project_id"] != f.c.projectID {
		return nil, "EXECUTION_SCOPE_MISMATCH"
	}
	return value, ""
}

type cliExecution struct {
	goal, task, run, message string
	cursor                   int64
	seen                     map[int64][32]byte
	runStates                map[string]map[string]any
	artifacts                map[string]map[string]bool
	report                   map[string]any
	build                    string
	cancelSent               bool
}

func (e *cliExecution) result(c *v2Context, code int, reason string) map[string]any {
	status := "UNRESOLVED"
	switch code {
	case 0:
		status = "EXECUTION_REPORTED"
	case exitFailed:
		status = "FAILED"
	case exitInterrupted:
		status = "CANCELLED"
	}
	return map[string]any{"status": status, "exit_code": code, "reason": reason,
		"project_id": c.projectID, "session_id": c.sessionID, "goal_id": e.goal,
		"task_id": e.task, "run_id": e.run, "message_id": e.message,
		"event_sequence": e.cursor, "cancel_requested": e.cancelSent,
		"independent_acceptance": "NOT_EVALUATED", "host_execution": e.report}
}

// consume validates an entire page before emitting it. An exact replay is
// deduplicated; changed replay, cursor jumps and foreign identities fail closed.
func (e *cliExecution) consume(f *cliFlow, result map[string]any) (bool, string) {
	events, ok := result["events"].([]any)
	next, nextOK := cliInteger(result["next_sequence"])
	watermark, watermarkOK := cliInteger(result["high_watermark"])
	more, moreOK := result["has_more"].(bool)
	if !ok || len(events) > 200 || !nextOK || !watermarkOK || !moreOK || next < e.cursor || next > watermark {
		return false, "INVALID_EVENT_PAGE"
	}
	last := e.cursor
	fresh := []map[string]any{}
	pageSeen := map[int64][32]byte{}
	for _, value := range events {
		ev := cliObject(value)
		sequence, valid := cliInteger(ev["sequence"])
		if !valid || sequence < 1 || sequence > watermark || ev["session_id"] != f.c.sessionID || ev["protocol_version"] != clientProtocol ||
			continuationString(ev, "event_id") == "" || continuationString(ev, "kind") == "" || cliObject(ev["payload"]) == nil || ev["core_build_id"] != e.build {
			return false, "EVENT_SCOPE_OR_SHAPE_MISMATCH"
		}
		raw, _ := json.Marshal(ev)
		digest := sha256.Sum256(raw)
		if old, exists := e.seen[sequence]; exists {
			if old != digest {
				return false, "EVENT_REPLAY_CHANGED"
			}
			continue
		}
		if old, exists := pageSeen[sequence]; exists {
			if old != digest {
				return false, "EVENT_REPLAY_CHANGED"
			}
			continue
		}
		if sequence != last+1 {
			return false, "EVENT_SEQUENCE_GAP"
		}
		last = sequence
		pageSeen[sequence] = digest
		fresh = append(fresh, ev)
	}
	if next != last || more && next == e.cursor || more && next >= watermark || !more && next != watermark {
		return false, "EVENT_CURSOR_NOT_ADVANCING"
	}
	if len(e.seen)+len(pageSeen) > 65536 {
		return false, "EVENT_OBSERVATION_LIMIT"
	}
	for sequence, digest := range pageSeen {
		e.seen[sequence] = digest
	}
	for _, ev := range fresh {
		if ev["kind"] == "ARTIFACT" {
			payload := cliObject(ev["payload"])
			ref := cliObject(payload["artifact_ref"])
			runID, artifactID := continuationString(ev, "run_id"), continuationString(ref, "id")
			if runID != "" && artifactID != "" && payload["availability"] == "AVAILABLE" {
				if e.artifacts == nil {
					e.artifacts = map[string]map[string]bool{}
				}
				if e.artifacts[runID] == nil {
					e.artifacts[runID] = map[string]bool{}
				}
				e.artifacts[runID][artifactID] = true
			}
		}
		if ev["kind"] == "RUN_STATE" {
			payload := cliObject(ev["payload"])
			if id := continuationString(ev, "run_id"); id != "" && payload["run_id"] == id {
				e.runStates[id] = payload
			}
		}
		f.options.emit(map[string]any{"type": "session.event", "event": ev})
	}
	e.cursor = next
	return more, ""
}

func (e *cliExecution) pages(f *cliFlow) string {
	for !f.expired() {
		reply, reason, code := f.call("session.events", map[string]any{"after_sequence": e.cursor, "limit": 200}, true)
		if code != 0 {
			f.responseExit = code
			if code == exitFailed && f.transportUnreachable && f.admissionCommand != "" && e.task != "" {
				// A completed admission and its original Task already exist.
				// A failed HTTP exchange cannot establish their settlement.
				// The typed cause is set only by client.Do, never a reply string.
				f.responseExit = exitNotImplemented
			}
			if statusOf(reply) == "REJECTED" && reply["error_code"] == "CURSOR_INVALID" && f.admissionCommand != "" && e.task != "" {
				// A real snapshot is the recovery vehicle. It does not contain
				// all tool events, so missing execution reporting cannot pass.
				if snap, snapshotReason, snapshotCode := f.snapshot(); snapshotCode == 0 {
					f.options.emit(map[string]any{"type": "session.snapshot", "snapshot": snap, "reason": "EVENT_RESYNC_REQUIRED"})
					f.responseExit = exitNotImplemented
				} else {
					f.responseExit = exitFailed
					return snapshotReason
				}
			}
			return reason
		}
		more, reason := e.consume(f, cliObject(reply["result"]))
		if reason != "" {
			return reason
		}
		if !more {
			return ""
		}
	}
	return "WAIT_FOR_SETTLEMENT"
}

func cliDate(value any) bool {
	s, ok := value.(string)
	_, err := time.Parse(time.RFC3339Nano, s)
	return ok && err == nil
}

// The host owns effectsReconciled before canonical report/recovery. The CLI
// verifies that report and its matching journal projection; it does not claim
// direct access to the private EffectLog or issue an independent acceptance.
func (e *cliExecution) terminal(task, run map[string]any) (int, bool) {
	state := e.runStates[e.run]
	revision, valid := cliInteger(run["revision"])
	projected, projectedOK := cliInteger(state["revision"])
	if !valid || !projectedOK || revision != projected || state["status"] != run["status"] ||
		run["children_stopped"] != true || run["queue_empty"] != true || state["children_stopped"] != true || state["queue_empty"] != true {
		return 0, false
	}
	if run["status"] == "CANCELLED" {
		return exitInterrupted, cliDate(run["cancel_confirmed_at"]) && state["cancel_confirmed_at"] == run["cancel_confirmed_at"]
	}
	if !cliDate(run["runtime_settled_at"]) || state["settled_at"] != run["runtime_settled_at"] {
		return 0, false
	}
	if run["status"] == "FAILED" {
		return exitFailed, true
	}
	if run["status"] == "SETTLED" && (task["status"] == "EXECUTION_REPORTED" || task["status"] == "VERIFYING" || task["status"] == "ACCEPTED") {
		ids, ok := run["result_artifact_ids"].([]any)
		exit, exitOK := cliInteger(run["exit_code"])
		if !ok || len(ids) == 0 || !exitOK || exit != 0 || strings.TrimSpace(continuationString(run, "execution_report")) == "" {
			return 0, false
		}
		for _, value := range ids {
			id, valid := value.(string)
			if !valid || !e.artifacts[e.run][id] {
				return 0, false
			}
		}
		return 0, true
	}
	return 0, false
}

func followCLIExecution(f *cliFlow, snapshot map[string]any, message, explicitRun string, after int64) (map[string]any, int) {
	e := &cliExecution{goal: continuationString(snapshot, "goal_id"), message: message, cursor: after,
		seen: map[int64][32]byte{}, runStates: map[string]map[string]any{}, build: continuationString(snapshot, "core_build_id")}
	finish := func(code int, reason string) (map[string]any, int) {
		out := e.result(f.c, code, reason)
		out["cancel_requested"] = f.cancelRequested || e.cancelSent
		return out, code
	}
	if snapshot["project_id"] != f.c.projectID || snapshot["session_id"] != f.c.sessionID || snapshot["protocol_version"] != clientProtocol || e.goal == "" || e.build == "" {
		return finish(exitNotImplemented, "ADMISSION_IDENTITY_UNRESOLVED")
	}
	goal, reason := f.object("goals", e.goal)
	if reason != "" {
		return finish(exitNotImplemented, reason)
	}
	ids, ok := goal["task_ids"].([]any)
	if !ok || len(ids) != 1 {
		return finish(exitNotImplemented, "ADMISSION_TASK_AMBIGUOUS")
	}
	e.task, _ = ids[0].(string)
	if !continuationID(e.task) {
		return finish(exitNotImplemented, "ADMISSION_TASK_UNRESOLVED")
	}
	for !f.expired() {
		if reason := e.pages(f); reason != "" {
			if f.responseExit != 0 {
				return finish(f.responseExit, reason)
			}
			return finish(exitNotImplemented, reason)
		}
		task, reason := f.object("tasks", e.task)
		if reason != "" {
			return finish(exitNotImplemented, reason)
		}
		if task["goal_id"] != e.goal {
			return finish(exitNotImplemented, "EXECUTION_TASK_SCOPE_CHANGED")
		}
		runID := continuationString(task, "active_run_id")
		if e.run != "" && runID != e.run || explicitRun != "" && runID != "" && runID != explicitRun {
			return finish(exitNotImplemented, "EXECUTION_RUN_CHANGED")
		}
		if runID != "" {
			e.run = runID
		}
		snap, reason, code := f.snapshot()
		if code != 0 {
			return finish(code, reason)
		}
		if snap["goal_id"] != e.goal || snap["core_build_id"] != e.build {
			return finish(exitNotImplemented, "SESSION_TARGET_CHANGED")
		}
		f.consumeActiveInput(snap, e)
		f.interrupt()
		// BLOCKED admission is not successful execution. Pending cancellation
		// continues to observe the original task instead of inventing a Run.
		if e.run == "" && !f.cancelRequested {
			switch task["status"] {
			case "BLOCKED", "DEFERRED_NO_PROGRESS", "NEEDS_REVALIDATION":
				return finish(exitNotImplemented, "TASK_BLOCKED")
			case "FAILED":
				return finish(exitFailed, "TASK_FAILED_WITHOUT_RUN")
			}
		}
		if f.cancelRequested && e.run == "" && !e.cancelSent {
			writer := cliObject(snap["writer"])
			if writer["client_id"] != f.c.clientID {
				return finish(exitNotImplemented, "CANCEL_AUTHORITY_UNRESOLVED")
			}
			reply, why, code := f.call("session.control", map[string]any{"action": "CANCEL", "target_id": e.goal, "reason": "User interrupted before Run admission"}, true)
			if code != 0 {
				return finish(exitNotImplemented, why)
			}
			result := cliObject(reply["result"])
			if result["settled"] == true && result["children_stopped"] == true && result["queue_empty"] == true {
				return finish(exitInterrupted, "HOST_CANCELLATION_SETTLED_WITHOUT_RUN")
			}
			e.cancelSent = true
		}
		if e.cancelSent && f.cancelCommand != nil {
			attempt := *f.cancelCommand
			attempt.requestLog = nil
			_, why, code := v2CallContext(f.budget, &attempt, "session.control", f.cancelPayload)
			f.c.requestLog = append(f.c.requestLog, attempt.requestLog...)
			if code != 0 {
				return finish(exitNotImplemented, why)
			}
		}
		if e.run != "" {
			run, reason := f.object("runs", e.run)
			if reason != "" || run["task_id"] != e.task {
				return finish(exitNotImplemented, orDefault(reason, "EXECUTION_RUN_SCOPE_MISMATCH"))
			}
			watermark, valid := cliInteger(snap["event_sequence"])
			if valid && e.cursor >= watermark && snap["active_run_id"] == e.run {
				if code, settled := e.terminal(task, run); settled {
					e.report = map[string]any{"status": run["status"], "revision": run["revision"], "execution_report": run["execution_report"],
						"result_artifact_ids": run["result_artifact_ids"], "children_stopped": run["children_stopped"], "queue_empty": run["queue_empty"],
						"runtime_settled_at": run["runtime_settled_at"], "cancel_confirmed_at": run["cancel_confirmed_at"]}
					return finish(code, "HOST_EXECUTION_SETTLED")
				}
			}
			f.interrupt()
			if f.cancelRequested && !e.cancelSent {
				writer := cliObject(snap["writer"])
				if snap["active_run_id"] != e.run || writer["client_id"] != f.c.clientID || !cliDate(writer["expires_at"]) {
					// The canonical Task can lead the session projection. Wait
					// for that original Run; do not cancel another session run.
					if snap["active_run_id"] == nil && writer["client_id"] == f.c.clientID {
						f.pause()
						continue
					}
					return finish(exitNotImplemented, "CANCEL_AUTHORITY_UNRESOLVED")
				}
				_, reason, code := f.call("session.control", map[string]any{"action": "CANCEL", "target_id": e.run, "reason": "User interrupted the CLI execution"}, false)
				if code != 0 {
					return finish(exitNotImplemented, reason)
				}
				e.cancelSent = true
			}
		}
		f.pause()
	}
	return finish(exitNotImplemented, "WAIT_FOR_SETTLEMENT")
}

func runCLIVerb(name string, args []string, c *v2Context, cfg cliConfig, options cliFollowOptions) (map[string]any, int) {
	originalContext := c
	readOnly := name == "status" || name == "/status"
	if readOnly {
		pending := *c
		pending.requestLog = append([]string(nil), c.requestLog...)
		c = &pending
	}
	budget, stop := context.WithTimeout(context.Background(), options.timeout)
	defer stop()
	f := &cliFlow{c: c, budget: budget, options: options, base: c.commandID, goalFlow: name == "goal" || name == "go" || name == "/goal"}
	if name == "status" || name == "/status" {
		readContext, cancelRead := context.WithCancel(budget)
		defer cancelRead()
		f.budget = readContext
		f.readInterrupt = observeCLIReadInterrupt(options.interrupts, cancelRead)
		defer f.readInterrupt.finish()
		// The observer is the only receiver for read-only calls. Active calls
		// retain their original cancellation/settlement signal handling.
		f.options.interrupts = nil
	}
	if input, ok := cliInputPumps.Load(c); ok {
		f.inputs = input.(<-chan cliInputLine)
	}
	steps, reason, detail := verbSteps(name, args, c, cfg)
	out := map[string]any{"command": name, "client_id": c.clientID, "host_url": c.baseURL}
	code := 0
	var snapshot map[string]any
	var after int64
	for _, step := range steps {
		if step.skipped != "" {
			f.operations = append(f.operations, map[string]any{"method": step.method, "status": "SKIPPED", "reason": step.skipped})
			continue
		}
		if step.method == "session.events" && (name == "run" || name == "/run") {
			continue // The admitted task is followed below, not by one page.
		}
		if reason != "" {
			code = exitUsage
			break
		}
		if step.method == "session.control" && step.payload["action"] == "CANCEL" {
			snapshot, reason, code = f.snapshot()
			if code != 0 {
				break
			}
			f.cancelRequested = true
			f.cancelDeadline = time.Now().Add(options.cancelTimeout)
			var result map[string]any
			explicit := continuationString(step.payload, "target_id")
			if explicit == snapshot["goal_id"] {
				explicit = ""
			}
			result, code = followCLIExecution(f, snapshot, "", explicit, 0)
			out["execution"] = result
			reason = continuationString(result, "reason")
			break
		}
		reply, why, currentCode := f.call(step.method, step.payload, true)
		f.operations = append(f.operations, map[string]any{"method": step.method, "status": statusOf(reply), "exit_code": currentCode, "reason": why, "result": reply["result"]})
		if currentCode != 0 {
			reason, code = why, currentCode
			break
		}
		if step.method == "session.get" || step.method == "session.create" {
			snapshot = cliSnapshot(reply)
			after, _ = cliInteger(snapshot["event_sequence"])
		}
		if step.method == "session.send" {
			result := cliObject(reply["result"])
			admitted := cliSnapshot(reply)
			if result["message_id"] == nil || snapshot != nil && admitted["goal_id"] == snapshot["goal_id"] {
				reason, code = "ADMISSION_IDENTITY_UNRESOLVED", exitNotImplemented
				break
			}
			var execution map[string]any
			execution, code = followCLIExecution(f, admitted, continuationString(result, "message_id"), continuationString(result, "run_id"), after)
			out["execution"] = execution
			reason = continuationString(execution, "reason")
			break
		}
		if step.method == "goal.start" {
			result := cliObject(reply["result"])
			out["goal"] = map[string]any{"goal_id": result["goal_id"], "goal_revision": result["goal_revision"], "goal_status": result["goal_status"]}
			if step.payload["start_as_draft"] == true {
				out["execution"] = map[string]any{"status": "NOT_STARTED", "independent_acceptance": "NOT_EVALUATED"}
				break
			}
			if result["goal_status"] == "DRAFT" {
				reason, code = "GOAL_NOT_STARTED", exitNotImplemented
				break
			}
			var execution map[string]any
			execution, code = followCLIExecution(f, cliSnapshot(reply), "", "", after)
			out["execution"] = execution
			reason = continuationString(execution, "reason")
			break
		}
	}
	if reason != "" && len(steps) == 0 {
		code = exitUsage
	}
	if code == 0 && (name == "status" || name == "/status") {
		continuation, why, statusCode, cancelledIO := cliReadContinuationWithCause(f.budget, c, snapshot)
		out["continuation"] = continuation
		if statusCode != 0 {
			code, reason = statusCode, why
			if cancelledIO && f.budget.Err() == context.Canceled && f.readInterrupt.observed() {
				code, reason = exitInterrupted, "READ_INTERRUPTED"
			}
		}
	}
	code, reason = f.finishReadResult(code, reason)
	if readOnly {
		if code == 0 {
			*originalContext = *c
		} else {
			originalContext.requestLog = c.requestLog
		}
	}
	out["status"], out["exit_code"] = "COMPLETED", code
	if execution := cliObject(out["execution"]); execution != nil {
		out["status"] = execution["status"]
		if execution["status"] == "NOT_STARTED" && code == 0 {
			out["status"] = "GOAL_DRAFT_CREATED"
		}
	} else if code != 0 {
		out["status"] = "REJECTED"
		if f.readInterrupt != nil && code == exitInterrupted {
			out["status"] = "INTERRUPTED_READ_ONLY"
		}
	}
	out["operations"], out["requests_sent"] = f.operations, c.requestLog
	out["admission_command_id"] = f.admissionCommand
	out["session_id"], out["reason"], out["detail"] = c.sessionID, reason, detail
	return out, code
}

// Called only by the single flow after a canonical snapshot. The stdin pump
// holds at most 16 intents and never sends a request or mutates writer state.
func (f *cliFlow) consumeActiveInput(snapshot map[string]any, e *cliExecution) {
	if f.inputs == nil {
		return
	}
	select {
	case input, ok := <-f.inputs:
		if !ok {
			f.inputs = nil
			return
		}
		name, rest, _ := strings.Cut(input.text, " ")
		if name == "/cancel" || name == "/stop" {
			f.cancelRequested = true
			f.cancelDeadline = time.Now().Add(f.options.cancelTimeout)
			return
		}
		mode := ""
		if name == "/steer" {
			mode = "STEER"
		}
		if name == "/follow-up" || name == "/followup" {
			mode = "FOLLOW_UP"
		}
		row := map[string]any{"type": "input.rejected", "draft": input.text, "reason": "ACTIVE_INPUT_REQUIRES_STEER_OR_FOLLOW_UP"}
		if input.err != nil {
			row["reason"] = "INPUT_READ_FAILED"
		} else if mode != "" && strings.TrimSpace(rest) != "" && !f.cancelRequested {
			writer := cliObject(snapshot["writer"])
			if writer["client_id"] != f.c.clientID {
				row["reason"] = "WRITER_BUSY"
			} else {
				originalAdmission := f.admissionCommand
				reply, why, code := f.call("session.send", map[string]any{"text": rest, "attachment_artifact_ids": []any{}, "delivery": mode}, true)
				f.admissionCommand = originalAdmission
				row["reason"], row["exit_code"], row["response"] = why, code, reply
				if code == 0 && statusOf(reply) == "COMPLETED" {
					row["type"] = "input.enqueued"
					delete(row, "draft")
				}
			}
		}
		if f.options.emit != nil {
			f.options.emit(row)
		}
	default:
	}
}

func saveCLIContext(c *v2Context, cfg *cliConfig) error {
	if c.sessionID == "" || c.projectID == "" || c.revision < 1 {
		return nil
	}
	if cfg.ProjectID == c.projectID && cfg.SessionID == c.sessionID && cfg.Revision == c.revision && cfg.WriterEpoch == c.epoch {
		return nil
	}
	cfg.ProjectID, cfg.SessionID = c.projectID, c.sessionID
	cfg.Revision, cfg.WriterEpoch, cfg.UpdatedBy = c.revision, c.epoch, c.clientID
	return writeConfig(*cfg)
}

func cliFlowSummary(out map[string]any, code int, c *v2Context, cfg *cliConfig) int {
	if out["command"] == "status" || out["command"] == "/status" {
		// A read report can display a freshly validated snapshot without
		// replacing the persisted recovery or writer context.
		outJSON(out)
		return code
	}
	// Even a blocked/interrupted admission must retain its recovery identity.
	if err := saveCLIContext(c, cfg); err != nil {
		diag("session context could not be saved: %s", err)
		out["context_save_error"] = "CONFIG_WRITE_FAILED"
		if code == 0 {
			code = exitFailed
			out["status"], out["exit_code"] = "REJECTED", code
		}
	}
	outJSON(out)
	return code
}

func cliInteractiveSlash(line string) (string, []string) {
	name, rest, _ := strings.Cut(line, " ")
	rest = strings.TrimSpace(rest)
	if rest == "" {
		return name, nil
	}
	if name == "/goal" || name == "/run" {
		return name, []string{rest}
	}
	return name, strings.Fields(rest)
}

func cliStreamIdentity(base string, turn int) string {
	return fmt.Sprintf("interactive-%x", sha256.Sum256([]byte(fmt.Sprintf("%s/%d", base, turn))))[:60]
}
