// apps/cli/cli_v2.go is the W05-03 command client: the frozen client protocol's 23 methods, sent as real envelopes
// to the one endpoint the local core serves for them (`POST /v2/command`).
//
// It exists because the review measured that `goal`, `go`, `resume`, `cancel` and their slash variants performed no
// operation at all: against a host that logs its requests each produced exactly one GET /healthz, discarded every
// positional id, and exited 0. The card names that failure mode itself ("空stub"; and this file's sibling rule that a
// command which cannot do its real work says so with 3, never with a plausible-looking success), so the verbs now
// carry the ids they were given to the method they are named after.
//
// The table mirrors internal/api/contracts/client.protocol.schema.json `x-method-contracts` and
// internal/domain/client_protocol.go's DecodeEnvelope, transcribed rather than guessed. It is a deliberate second
// copy: the shared Core location (internal/domain) is outside this card's write scope, and the alternative — letting
// the CLI send envelopes nobody validated — would move the failure from a local refusal to an unexplained 400.
// W0503-CLI-METHOD-TABLE-MATCHES-THE-FROZEN-SCHEMA closes the drift risk by comparing this table with the schema
// file byte-for-byte in semantics, and W0503-CLI-TABLE-AND-DESKTOP-V2-AGREE compares the two clients.
package main

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"time"

	"encoding/json/jsontext"

	"researchos.local/research-os/internal/api"
)

const v2CommandPath = "/v2/command"

var cliProtocolDocument = sync.OnceValues(api.ClientProtocolDocument)

// v2WriteMethods mirrors client_protocol.go:7. session.attach is excluded because it has its own epoch rule.
var v2WriteMethods = map[string]bool{"session.send": true, "session.control": true, "session.update": true,
	"session.handoff": true, "workspace.write": true, "artifact.import": true, "permission.respond": true,
	"goal.start": true, "project.bootstrap": true}

// v2Contract maps each method to its published payload/result names and required payload keys.
var v2Contract = map[string]struct {
	payload, result string
	required        []string
}{
	"host.status": {"EmptyPayload", "HostStatusResult", nil},
	"host.configure": {"ConfigurePayload", "ConfigureResult",
		[]string{"config_revision", "provider_id", "base_url", "model_id", "credential_ref"}},
	"project.bootstrap": {"BootstrapPayload", "BootstrapResult",
		[]string{"authorized_workspace_ref", "display_name"}},
	"session.list": {"ListSessionsPayload", "SessionListResult", []string{"cursor", "limit"}},
	"session.create": {"CreateSessionPayload", "SessionSnapshot",
		[]string{"workspace_ref", "model_config_ref", "title"}},
	"session.get":    {"EmptyPayload", "SessionSnapshot", nil},
	"session.attach": {"AttachPayload", "AttachResult", []string{"after_sequence", "request_write_owner"}},
	"session.send": {"SendMessagePayload", "SendMessageResult",
		[]string{"text", "attachment_artifact_ids", "delivery"}},
	"session.control": {"ControlPayload", "ControlResult", []string{"action", "target_id", "reason"}},
	"session.events":  {"ReadEventsPayload", "ReadEventsResult", []string{"after_sequence", "limit"}},
	"session.handoff": {"HandoffPayload", "HandoffResult", []string{"target_client_id", "handoff_mode"}},
	"goal.start": {"StartGoalPayload", "StartGoalResult",
		[]string{"objective", "contract_artifact_ids", "start_as_draft"}},
	"provider.models": {"ListModelsPayload", "ListModelsResult",
		[]string{"provider_id", "refresh", "allow_network", "cursor", "limit"}},
	"provider.probe": {"ProbeProviderPayload", "ProbeProviderResult",
		[]string{"model_config_ref", "allow_network", "max_output_tokens", "timeout_ms"}},
	"workspace.register": {"RegisterWorkspacePayload", "WorkspaceBinding",
		[]string{"selection_ref", "display_name", "requested_access"}},
	"workspace.list": {"EmptyPayload", "WorkspaceListResult", nil},
	"workspace.tree": {"WorkspaceTreePayload", "WorkspaceTreeResult",
		[]string{"workspace_ref", "relative_path", "cursor", "limit"}},
	"workspace.read": {"WorkspaceReadPayload", "WorkspaceReadResult",
		[]string{"workspace_ref", "relative_path", "max_bytes"}},
	"workspace.diff": {"WorkspaceDiffPayload", "WorkspaceDiffResult",
		[]string{"workspace_ref", "base", "relative_path", "max_bytes"}},
	"workspace.write": {"WorkspaceWritePayload", "WorkspaceWriteResult",
		[]string{"workspace_ref", "relative_path", "task_id", "expected_content_hash", "text", "create_if_missing"}},
	"artifact.import": {"ImportArtifactPayload", "ImportArtifactResult",
		[]string{"workspace_ref", "relative_path", "expected_content_hash", "purpose"}},
	"session.update": {"UpdateSessionPayload", "SessionSnapshot", []string{"action", "title"}},
	"permission.respond": {"RespondPermissionPayload", "RespondPermissionResult",
		[]string{"resource_request_id", "resource_request_revision", "action_digest", "decision", "reason"}},
}

type v2Envelope struct {
	ProtocolVersion  string          `json:"protocol_version"`
	CommandID        string          `json:"command_id"`
	ClientID         string          `json:"client_id"`
	ProjectID        *string         `json:"project_id"`
	SessionID        *string         `json:"session_id"`
	ExpectedRevision *int64          `json:"expected_revision"`
	WriterEpoch      *int64          `json:"writer_epoch"`
	Method           string          `json:"method"`
	Payload          json.RawMessage `json:"payload"`
}

type v2Context struct {
	clientID   string
	credential string
	projectID  string
	sessionID  string
	revision   int64
	epoch      int64
	commandID  string
	baseURL    string
	requestLog []string
}

var commandIDPattern = regexp.MustCompile(`^[A-Za-z0-9._:-]{1,64}$`)

// v2EnvelopeFor validates locally, exactly as DecodeEnvelope does on the far side, so a malformed command never
// leaves the process: the refusal names the missing field instead of arriving as an unexplained 400.
func v2EnvelopeFor(ctx *v2Context, method string, payload map[string]any) (*v2Envelope, string) {
	c, known := v2Contract[method]
	if !known {
		return nil, "UNKNOWN_METHOD"
	}
	if ctx.clientID == "" {
		return nil, "MISSING_FIELD:client_id"
	}
	if ctx.credential == "" {
		return nil, "CREDENTIAL_ABSENT"
	}
	if !commandIDPattern.MatchString(ctx.commandID) {
		return nil, "MISSING_FIELD:command_id"
	}
	raw, err := json.Marshal(payload)
	if err != nil {
		return nil, "PAYLOAD_NOT_OBJECT"
	}
	var keys map[string]json.RawMessage
	if err := json.Unmarshal(raw, &keys); err != nil {
		return nil, "PAYLOAD_NOT_OBJECT"
	}
	for _, k := range c.required {
		if _, has := keys[k]; !has {
			return nil, "MISSING_PAYLOAD_FIELD:" + k
		}
	}
	if c.payload == "EmptyPayload" && len(keys) > 0 {
		return nil, "UNEXPECTED_PAYLOAD_KEYS:" + strings.Join(sortedKeys(keys), ",")
	}
	env := &v2Envelope{ProtocolVersion: clientProtocol, CommandID: ctx.commandID, ClientID: ctx.clientID,
		Method: method, Payload: raw}
	// These two first-use methods are host-level. The host returns the durable
	// project identity only after a selected workspace has been registered.
	if ctx.projectID != "" && method != "workspace.register" && method != "project.bootstrap" {
		env.ProjectID = &ctx.projectID
	}
	if ctx.sessionID != "" {
		env.SessionID = &ctx.sessionID
	}
	if method == "session.attach" {
		claim := false
		if v, isBool := payload["request_write_owner"].(bool); isBool {
			claim = v
		}
		if claim && ctx.epoch != 0 {
			return nil, "ATTACKER_CLAIMED_EPOCH"
		}
		if claim {
			env.ExpectedRevision = &ctx.revision
		}
		if !claim {
			env.WriterEpoch = &ctx.epoch
		}
	} else if v2WriteMethods[method] && method != "project.bootstrap" {
		if env.ProjectID == nil {
			return nil, "MISSING_FIELD:project_id"
		}
		if method != "goal.start" || env.SessionID != nil {
			env.ExpectedRevision = &ctx.revision
			env.WriterEpoch = &ctx.epoch
		}
	}
	if method == "host.configure" {
		if ctx.sessionID == "" {
			if ctx.projectID != "" || ctx.revision != 0 || ctx.epoch != 0 {
				return nil, "INCOMPLETE_CONFIGURE_SCOPE"
			}
			env.ProjectID, env.SessionID, env.ExpectedRevision, env.WriterEpoch = nil, nil, nil, nil
		} else {
			if ctx.epoch <= 0 {
				return nil, "MODEL_CHANGE_WITHOUT_EPOCH"
			}
			if !continuationID(ctx.sessionID) || !continuationID(ctx.projectID) || ctx.revision <= 0 || ctx.revision > 9007199254740991 || ctx.epoch > 9007199254740991 {
				return nil, "INCOMPLETE_CONFIGURE_SCOPE"
			}
			env.ExpectedRevision, env.WriterEpoch = &ctx.revision, &ctx.epoch
		}
	}
	return env, ""
}

func sortedKeys(m map[string]json.RawMessage) []string {
	out := make([]string, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	for i := 1; i < len(out); i++ {
		for j := i; j > 0 && out[j] < out[j-1]; j-- {
			out[j], out[j-1] = out[j-1], out[j]
		}
	}
	return out
}

// The returned code classifies transport/admission only. Callers must inspect
// status and follow the admitted operation; even session.send COMPLETED is not
// an execution result. run and interactive use followCLIExecution for that gate.
func v2Call(ctx *v2Context, method string, payload map[string]any) (map[string]any, string, int) {
	return v2CallTransport(context.Background(), ctx, method, payload, false)
}

func v2CallContext(budget context.Context, ctx *v2Context, method string, payload map[string]any) (map[string]any, string, int) {
	return v2CallTransport(budget, ctx, method, payload, true)
}

func v2CallTransport(budget context.Context, ctx *v2Context, method string, payload map[string]any, strictIdentity bool) (map[string]any, string, int) {
	reply, reason, code, _ := v2CallTransportWithCause(budget, ctx, method, payload, strictIdentity)
	return reply, reason, code
}

// Only the read-only status flow consumes this private I/O cause. A context
// cancelled after another failure does not turn that failure into an interrupt.
func v2CallTransportWithCause(budget context.Context, ctx *v2Context, method string, payload map[string]any, strictIdentity bool) (map[string]any, string, int, bool) {
	env, refusal := v2EnvelopeFor(ctx, method, payload)
	if refusal != "" {
		if refusal == "CREDENTIAL_ABSENT" {
			// contracts/product.contract.json maps 3 to "blocked_missing_resource_or_authorization"; a CLI with no
			// bearer is blocked, not given an invalid argument.
			return nil, refusal, exitNotImplemented, false
		}
		return nil, refusal, exitUsage, false
	}
	body, _ := json.Marshal(env)
	ctx.requestLog = append(ctx.requestLog, method)
	client := http.Client{Timeout: 8 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	req, err := http.NewRequestWithContext(budget, "POST", ctx.baseURL+v2CommandPath, bytes.NewReader(body))
	if err != nil {
		return nil, "REQUEST_UNBUILDABLE:" + err.Error(), exitFailed, false
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+ctx.credential)
	resp, err := client.Do(req)
	if err != nil {
		return nil, "HOST_UNREACHABLE:" + err.Error(), exitFailed, errors.Is(err, context.Canceled)
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		code := exitNotImplemented
		if resp.StatusCode >= 500 && resp.StatusCode <= 599 {
			code = exitFailed
		}
		return nil, "HOST_HTTP_" + strconv.Itoa(resp.StatusCode), code, false
	}
	raw, readErr := io.ReadAll(io.LimitReader(resp.Body, (1<<20)+1))
	if readErr != nil || len(raw) > 1<<20 {
		return nil, "INCOMPLETE_OR_OVERSIZE_REPLY", exitFailed, len(raw) <= 1<<20 && errors.Is(readErr, context.Canceled)
	}
	// Both entry points use the same complete gate. strictIdentity is retained
	// for caller compatibility, never as permission to trust a weaker response.
	_ = strictIdentity
	reply, refusal := validateCLIResponse(raw, env)
	if refusal != "" {
		return nil, refusal, exitFailed, false
	}
	status, _ := reply["status"].(string)
	switch status {
	case "COMPLETED", "ACKNOWLEDGED":
		if status == "COMPLETED" && method != "goal.start" {
			adoptV2Snapshot(ctx, reply)
		}
		return reply, "", exitCompleted, false
	case "REJECTED":
		code, _ := reply["error_code"].(string)
		exit := exitFailed
		switch code {
		case "NOT_IMPLEMENTED", "COMMAND_PENDING", "CREDENTIAL_MISSING", "CREDENTIAL_REVOKED", "RESOURCE_BLOCKED", "RESOURCE_UNAVAILABLE", "MODEL_UNAVAILABLE", "HOST_UNAVAILABLE", "UNAUTHENTICATED", "FORBIDDEN", "LEASE_EXPIRED", "WRITER_BUSY", "STALE_WRITER_EPOCH", "CANCEL_UNCONFIRMED":
			exit = exitNotImplemented
		case "INVALID_REQUEST", "UNSUPPORTED_PROTOCOL", "UNSUPPORTED_METHOD":
			exit = exitUsage
		}
		return reply, "HOST_REJECTED:" + orDefault(code, "UNSPECIFIED"), exit, false
	default:
		return reply, "UNKNOWN_STATUS:" + orDefault(status, "<absent>"), exitFailed, false
	}
}

// Goal adoption is atomic: validate the host's pinned typed result and all
// cross-object identities before changing even the in-memory session context.
func adoptCLIGoal(ctx *v2Context, reply map[string]any, draft bool) string {
	result := cliObject(reply["result"])
	doc, err := cliProtocolDocument()
	if err != nil || doc.ValidateDef("StartGoalResult", result) != nil {
		return "INVALID_GOAL_RESULT"
	}
	snap := cliObject(result["snapshot"])
	sid := continuationString(snap, "session_id")
	revision, revisionOK := cliInteger(snap["revision"])
	goalRevision, goalRevisionOK := cliInteger(result["goal_revision"])
	if !continuationID(sid) || !continuationID(continuationString(result, "goal_id")) || !revisionOK || revision < 1 || !goalRevisionOK || goalRevision < 1 ||
		snap["project_id"] != ctx.projectID || snap["goal_id"] != result["goal_id"] || snap["goal_status"] != result["goal_status"] ||
		ctx.sessionID != "" && ctx.sessionID != sid || reply["session_id"] != nil && reply["session_id"] != sid {
		return "GOAL_SCOPE_MISMATCH"
	}
	if draft && result["goal_status"] != "DRAFT" {
		return "GOAL_DRAFT_STATE_MISMATCH"
	}
	writer := cliObject(snap["writer"])
	epoch, epochOK := cliInteger(writer["epoch"])
	if writer == nil || writer["client_id"] != ctx.clientID || !epochOK || epoch < 1 || !cliDate(writer["expires_at"]) {
		return "GOAL_WRITER_UNRESOLVED"
	}
	ctx.sessionID, ctx.revision, ctx.epoch = sid, revision, epoch
	return ""
}

// A successful response supplies the next revision/epoch. Never infer either
// from the request, and never replace an explicitly selected session.
func adoptV2Snapshot(ctx *v2Context, reply map[string]any) {
	if statusOf(reply) != "COMPLETED" {
		return
	}
	next := *ctx
	snapshot := cliSnapshot(reply)
	sid, hasSnapshot := snapshot["session_id"].(string)
	if hasSnapshot {
		if ctx.sessionID != "" && ctx.sessionID != sid || snapshot["project_id"] != ctx.projectID {
			return
		}
		if ctx.sessionID == "" && reply["method"] != "session.create" {
			return
		}
		revision, ok := cliInteger(snapshot["revision"])
		if !ok || revision < 1 {
			return
		}
		next.sessionID, next.revision, next.epoch = sid, revision, 0
		writer := cliObject(snapshot["writer"])
		if writer["client_id"] == ctx.clientID {
			epoch, valid := cliInteger(writer["epoch"])
			expires, err := time.Parse(time.RFC3339Nano, continuationString(writer, "expires_at"))
			if valid && epoch > 0 && err == nil && time.Now().Before(expires) {
				next.epoch = epoch
			}
		}
	} else if ctx.sessionID != "" && reply["session_id"] == ctx.sessionID && reply["revision"] != nil {
		revision, ok := cliInteger(reply["revision"])
		if !ok || revision < 1 {
			return
		}
		next.revision = revision
	}
	ctx.sessionID, ctx.revision, ctx.epoch = next.sessionID, next.revision, next.epoch
}

// Keep the original numeric lexeme until the frozen schema and exact range
// checks have completed. Small integers retain the historical map representation.
func cliResponseNumbers(value any) (any, bool) {
	switch v := value.(type) {
	case json.Number:
		n, ok := configureExactInteger(v)
		if ok && n < 1<<53 {
			return float64(n), true
		}
		return v, true
	case map[string]any:
		for k, item := range v {
			switch k {
			case "revision", "expected_revision", "writer_epoch", "epoch", "goal_revision", "config_revision", "current_revision", "current_writer_epoch", "sequence", "event_sequence", "earliest_event_sequence", "next_sequence", "high_watermark", "after_sequence":
				if item != nil {
					if _, ok := configureExactInteger(item); !ok {
						return nil, false
					}
				}
			}
			converted, ok := cliResponseNumbers(item)
			if !ok {
				return nil, false
			}
			v[k] = converted
		}
	case []any:
		for i, item := range v {
			converted, ok := cliResponseNumbers(item)
			if !ok {
				return nil, false
			}
			v[i] = converted
		}
	}
	return value, true
}

func validateCLIResponse(raw []byte, env *v2Envelope) (map[string]any, string) {
	if !jsontext.Value(raw).IsValid() {
		return nil, "MALFORMED_REPLY"
	}
	var reply map[string]any
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.UseNumber()
	if decoder.Decode(&reply) != nil {
		return nil, "MALFORMED_REPLY"
	}
	if reply["protocol_version"] != clientProtocol || reply["command_id"] != env.CommandID || reply["method"] != env.Method {
		return nil, "REPLY_IDENTITY_MISMATCH"
	}
	doc, err := cliProtocolDocument()
	if err != nil || doc.ValidateDef("CommandResponse", reply) != nil {
		return nil, "INVALID_REPLY_SCHEMA"
	}
	var expectedSID any
	if env.SessionID != nil {
		expectedSID = *env.SessionID
	}
	completed := reply["status"] == "COMPLETED"
	if !(env.Method == "session.create" && completed) && reply["session_id"] != expectedSID {
		return nil, "REPLY_SESSION_MISMATCH"
	}
	if _, ok := cliResponseNumbers(reply); !ok {
		return nil, "REPLY_INTEGER_OUT_OF_RANGE"
	}
	result := cliObject(reply["result"])
	if completed && env.Method == "host.status" && result["client_id"] != env.ClientID {
		return nil, "REPLY_CLIENT_MISMATCH"
	}
	if completed {
		snapshot := cliObject(result["snapshot"])
		switch env.Method {
		case "session.create", "session.get", "session.update":
			snapshot = result
		}
		if snapshot != nil {
			sid := snapshot["session_id"]
			if env.ProjectID == nil || snapshot["project_id"] != *env.ProjectID || expectedSID != nil && sid != expectedSID || env.Method != "goal.start" && sid != reply["session_id"] {
				return nil, "REPLY_SNAPSHOT_SCOPE_MISMATCH"
			}
			if env.Method != "goal.start" {
				top, topOK := cliInteger(reply["revision"])
				nested, nestedOK := cliInteger(snapshot["revision"])
				if !topOK || !nestedOK || top != nested {
					return nil, "REPLY_SNAPSHOT_REVISION_MISMATCH"
				}
			}
		}
	}
	return reply, ""
}

func v2FlowCommandID(base, method string, ordinal int) string {
	if ordinal == 0 {
		return base
	}
	digest := sha256.Sum256([]byte(fmt.Sprintf("%s\x00%s\x00%d", base, method, ordinal)))
	return fmt.Sprintf("flow-%x", digest[:28])
}

func orDefault(s, d string) string {
	if s == "" {
		return d
	}
	return s
}

// answer prints the machine record the caller already assembled and exits with the contract code.
func answer(command string, code int, fields map[string]any) {
	out := map[string]any{"command": command, "exit_code": code}
	for k, v := range fields {
		out[k] = v
	}
	outJSON(out)
	if code != exitCompleted {
		os.Exit(code)
	}
}
