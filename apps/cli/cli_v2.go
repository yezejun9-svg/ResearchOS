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
	"encoding/json"
	"io"
	"net/http"
	"os"
	"regexp"
	"strings"
	"time"
)

const v2CommandPath = "/v2/command"

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
	"session.get": {"EmptyPayload", "SessionSnapshot", nil},
	"session.attach": {"AttachPayload", "AttachResult", []string{"after_sequence", "request_write_owner"}},
	"session.send": {"SendMessagePayload", "SendMessageResult",
		[]string{"text", "attachment_artifact_ids", "delivery"}},
	"session.control": {"ControlPayload", "ControlResult", []string{"action", "target_id", "reason"}},
	"session.events": {"ReadEventsPayload", "ReadEventsResult", []string{"after_sequence", "limit"}},
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
	clientID    string
	credential  string
	projectID   string
	sessionID   string
	revision    int64
	epoch       int64
	commandID   string
	baseURL     string
	requestLog  []string
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
	if ctx.projectID != "" {
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
		if !claim {
			env.WriterEpoch = &ctx.epoch
		}
	} else if v2WriteMethods[method] {
		if env.ProjectID == nil {
			return nil, "MISSING_FIELD:project_id"
		}
		env.ExpectedRevision = &ctx.revision
		env.WriterEpoch = &ctx.epoch
	}
	if method == "host.configure" {
		_, hasModel := keys["model_id"]
		_, hasProvider := keys["provider_id"]
		if (hasModel || hasProvider) && ctx.epoch == 0 {
			return nil, "MODEL_CHANGE_WITHOUT_EPOCH"
		}
		if hasModel || hasProvider {
			// Refusing locally is only half of it: client_protocol.go:152 rejects a configuration change that names
			// a model while writer_epoch is absent, so the observed epoch has to travel on the wire, not merely be
			// non-zero inside this process.
			env.WriterEpoch = &ctx.epoch
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

// v2Call sends the command and returns the host's own reply. A host that refuses is reported as a refusal: the exit
// code follows the reply's status, so COMPLETED is the only answer allowed to exit 0.
func v2Call(ctx *v2Context, method string, payload map[string]any) (map[string]any, string, int) {
	env, refusal := v2EnvelopeFor(ctx, method, payload)
	if refusal != "" {
		if refusal == "CREDENTIAL_ABSENT" {
			// contracts/product.contract.json maps 3 to "blocked_missing_resource_or_authorization"; a CLI with no
			// bearer is blocked, not given an invalid argument.
			return nil, refusal, exitNotImplemented
		}
		return nil, refusal, exitUsage
	}
	body, _ := json.Marshal(env)
	ctx.requestLog = append(ctx.requestLog, method)
	client := http.Client{Timeout: 8 * time.Second}
	req, err := http.NewRequest("POST", ctx.baseURL+v2CommandPath, bytes.NewReader(body))
	if err != nil {
		return nil, "REQUEST_UNBUILDABLE:" + err.Error(), exitFailed
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+ctx.credential)
	resp, err := client.Do(req)
	if err != nil {
		return nil, "HOST_UNREACHABLE:" + err.Error(), exitFailed
	}
	defer resp.Body.Close()
	raw, _ := io.ReadAll(io.LimitReader(resp.Body, 1<<20))
	var reply map[string]any
	if e := json.Unmarshal(raw, &reply); e != nil {
		return nil, "MALFORMED_REPLY", exitFailed
	}
	status, _ := reply["status"].(string)
	switch status {
	case "COMPLETED", "ACKNOWLEDGED":
		return reply, "", exitCompleted
	case "IN_PROGRESS":
		return reply, "", exitCompleted
	case "REJECTED":
		code, _ := reply["error_code"].(string)
		return reply, "HOST_REJECTED:" + orDefault(code, "UNSPECIFIED"), exitFailed
	case "NOT_IMPLEMENTED":
		return reply, "HOST_NOT_IMPLEMENTED:" + method, exitNotImplemented
	default:
		return reply, "UNKNOWN_STATUS:" + orDefault(status, "<absent>"), exitFailed
	}
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
