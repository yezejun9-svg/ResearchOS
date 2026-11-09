package runtime

import (
	"bufio"
	"bytes"
	"encoding/json"
	"regexp"
)

type Protocol struct {
	Settled       bool           `json:"settled"`
	ToolFailed    bool           `json:"tool_failed"`
	Failure       string         `json:"failure"`
	ThreadID      string         `json:"thread_id"`
	Usage         map[string]any `json:"usage"`
	ModelRevision *string        `json:"model_revision"`
	Cost          any            `json:"cost"`
}

func Parse(raw []byte, exit int) Protocol {
	p := Protocol{}
	s := bufio.NewScanner(bytes.NewReader(raw))
	s.Buffer(make([]byte, 4096), 8*1024*1024)
	for s.Scan() {
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
		case "turn.failed", "error":
			p.Failure = "request_failed"
		case "item.completed":
			if item, ok := o["item"].(map[string]any); ok {
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
