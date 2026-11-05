package runtime

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"regexp"
	"strings"
	"time"
)

type Protocol struct {
	Settled        bool            `json:"settled"`
	ToolFailed     bool            `json:"tool_failed"`
	Failure        string          `json:"failure"`
	ThreadID       string          `json:"thread_id"`
	Usage          map[string]any  `json:"usage"`
	ModelRevision  *string         `json:"model_revision"`
	Cost           any             `json:"cost"`
	Result         json.RawMessage `json:"result"`
	ToolsCompleted int             `json:"tools_completed"`
}

var reconnectDiagnostic = regexp.MustCompile(`^Reconnecting\.\.\. [1-9][0-9]*/[1-9][0-9]* \(stream disconnected before completion: .+\)$`)

func Parse(raw []byte, exit int) Protocol {
	p := Protocol{}
	seen := map[string]bool{}
	s := bufio.NewScanner(bytes.NewReader(raw))
	s.Buffer(make([]byte, 4096), 8*1024*1024)
	for s.Scan() {
		line := string(s.Bytes())
		var o map[string]any
		if json.Unmarshal(s.Bytes(), &o) != nil {
			p.Failure = "invalid_protocol"
			continue
		}
		switch o["type"] {
		case "thread.started":
			p.ThreadID, _ = o["thread_id"].(string)
		case "turn.completed":
			p.Settled = true
			p.Usage, _ = o["usage"].(map[string]any)
		case "turn.failed":
			p.Failure = "request_failed"
		case "error":
			message, _ := o["message"].(string)
			if reconnectDiagnostic.MatchString(message) {
				// A transport retry still needs a later completed turn; terminal failures stay sticky.
				p.Settled = false
			} else {
				p.Failure = "request_failed"
			}
		case "item.completed":
			if seen[line] {
				continue
			}
			seen[line] = true
			if item, ok := o["item"].(map[string]any); ok {
				if item["type"] == "agent_message" {
					if text, ok := item["text"].(string); ok && json.Valid([]byte(text)) {
						p.Result = json.RawMessage(text)
					}
				}
				if item["type"] == "command_execution" && item["status"] == "completed" {
					p.ToolsCompleted++
				}
				if code, ok := item["exit_code"].(float64); ok && code != 0 {
					p.ToolFailed = true
				}
				if item["status"] == "failed" {
					p.ToolFailed = true
				}
			}
		}
	}
	if s.Err() != nil {
		p.Failure = "protocol_overflow"
	}
	if exit != 0 {
		p.Failure = "executor_exit"
	}
	if !p.Settled && p.Failure == "" {
		p.Failure = "missing_settled"
	}
	if p.ToolFailed {
		p.Failure = "tool_failed"
	}
	if p.Failure != "" {
		p.Settled = false
	}
	return p
}

// Codex may emit turn.completed/exit 0 after a tool router rejection. That is a failure.
func ParseStreams(stdout, stderr []byte, exit int) Protocol {
	p := Parse(stdout, exit)
	text := strings.ToLower(string(stderr))
	if strings.Contains(text, "rejected: blocked by policy") {
		p.ToolFailed = true
		p.Settled = false
		p.Failure = "tool_permission_denied"
	} else if strings.Contains(text, "error=exec_command failed") {
		p.ToolFailed = true
		p.Settled = false
		p.Failure = "tool_failed"
	}
	return p
}

var secrets = []*regexp.Regexp{
	regexp.MustCompile(`(?i)(Bearer\s+)[A-Za-z0-9._~+/=-]+`),
	regexp.MustCompile(`\bsk-[A-Za-z0-9_-]{16,}\b`),
	regexp.MustCompile(`\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b`),
	regexp.MustCompile(`(?i)("(?:access_token|refresh_token|id_token|api_key|password|authorization)"\s*:\s*")[^"]*`),
}

func Redact(b []byte) []byte {
	for i, r := range secrets {
		replacement := []byte("[REDACTED]")
		if i == 0 || i == 3 {
			replacement = []byte("${1}[REDACTED]")
		}
		b = r.ReplaceAll(b, replacement)
	}
	return b
}

// CodexDescriptor is Host-owned metadata. Verification is not inferred from
// installation or authentication; secrets/config contents never appear here.
type CodexDescriptor struct {
	Present                                                     bool
	Version, ExecutableHash, AuthState, AuthKind, AuthCheckedAt string
	ConfigurationControlled                                     bool
	UnavailableReason                                           string
	NativeTransport                                             string
}
type CodexLaunch struct {
	TaskID, RunID, Epoch, Workspace, Prompt, Directory, SourceBindingHash string
	Timeout                                                               time.Duration
}
type CodexIdentity struct {
	PID     uint32
	Created int64
	Job     string
}

// CodexTurnEvidence is a value-only projection of the live RPC barrier.
// A serialized copy cannot recreate the driver's private one-use permit.
type CodexTurnEvidence struct {
	PolicyIdentity                                                  CodexPolicyIdentity
	RenderedConfigSHA256, SourceBindingHash, ProfileNonce, ThreadID string
	TaskID, RunID, Epoch                                            string
	Process                                                         CodexIdentity
	CaptureBytes                                                    int64
}
type CodexEvent struct{ Kind, Text, ToolID, ToolName, ToolPhase, NativeID string }
type CodexResult struct {
	State, Failure, ThreadID, Assistant      string
	ExitCode                                 int
	Identity                                 CodexIdentity
	Stopped, StreamsDrained, CleanupComplete bool
	Stdout, Stderr                           []byte
}
type CodexCallbacks struct {
	BeforeResume    func(CodexIdentity) error
	BeforeModelTurn func(CodexTurnEvidence) error
	Event           func(CodexEvent) error
}
type CodexHandle interface {
	Cancel()
	Wait(context.Context) (CodexResult, error)
}
type CodexDriver interface {
	Descriptor() CodexDescriptor
	ReadinessSnapshot() CodexReadiness
	Start(context.Context, CodexLaunch, CodexCallbacks) (CodexHandle, error)
}
