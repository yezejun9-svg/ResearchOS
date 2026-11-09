package domain

import (
	"database/sql"
	"encoding/json"
	"net/url"
	"strings"
	"unicode/utf8"
)

const runtimeMuBackend = "mu-sdk-broker-v1"

// Only a complete final SSE data event terminates the transport. A model may
// legitimately mention [DONE] inside JSON content; that is not a terminator.
func completeRuntimeModelSSE(raw []byte) bool {
	if !utf8.Valid(raw) {
		return false
	}
	text := strings.ReplaceAll(string(raw), "\r\n", "\n")
	if !strings.HasSuffix(text, "\n\n") {
		return false
	}
	complete, seenData := false, false
	for _, event := range strings.Split(text, "\n\n") {
		data := []string{}
		for _, line := range strings.Split(event, "\n") {
			if strings.HasPrefix(line, "data:") {
				data = append(data, strings.TrimPrefix(strings.TrimPrefix(line, "data:"), " "))
			}
		}
		if len(data) == 0 {
			continue
		}
		if complete {
			return false
		}
		payload := strings.Join(data, "\n")
		if payload == "[DONE]" {
			complete = true
			continue
		}
		var object map[string]any
		if json.Unmarshal([]byte(payload), &object) != nil || object == nil {
			return false
		}
		seenData = true
	}
	return complete && seenData
}

func validateRuntimeModelConfig(profile Object) error {
	if profile["backend"] != runtimeMuBackend {
		return nil
	}
	config, ok := profile["model_config"].(map[string]any)
	if !ok || config["api"] != "openai-completions" || config["model"] != profile["model"] || Str(config, "model") == "" || Str(config, "provider") == "" || Str(config, "ref") == "" || Str(config, "route") == "" {
		return Fail(422, "GATE_FAILED", "frozen Mu model configuration required")
	}
	u, e := url.Parse(Str(config, "endpoint"))
	if e != nil || u.Hostname() == "" || u.User != nil || u.Fragment != "" || u.RawQuery != "" {
		return Fail(422, "GATE_FAILED", "frozen model endpoint required")
	}
	limit, e := Num(config, "max_output_tokens")
	if e != nil || limit < 1 || limit > 8192 {
		return Fail(422, "GATE_FAILED", "bounded model output required")
	}
	calls, e := Num(config, "max_calls")
	if e != nil || calls < 1 || calls > 32 {
		return Fail(422, "GATE_FAILED", "bounded model calls required")
	}
	if _, ok := config["tools"].([]any); !ok || len(Arr(config, "tools")) > 16 {
		return Fail(422, "GATE_FAILED", "frozen model tool schemas required")
	}
	for _, v := range Arr(config, "tools") {
		tool, ok := v.(map[string]any)
		if !ok || tool["type"] != "function" {
			return Fail(422, "GATE_FAILED", "only frozen function tools supported")
		}
		fn, ok := tool["function"].(map[string]any)
		if !ok || Str(fn, "name") == "" || fn["parameters"] == nil {
			return Fail(422, "GATE_FAILED", "complete function schema required")
		}
	}
	if len(Str(profile, "bundle_hash")) != 71 {
		return Fail(422, "GATE_FAILED", "frozen Mu bundle hash required")
	}
	if qualification, exists := profile["model_qualification"]; exists {
		q, ok := qualification.(map[string]any)
		if !ok || len(q) != 3 || q["route"] != config["route"] || Hash(q["model_config_hash"]) != Hash(Hash(config)) {
			return Fail(422, "GATE_FAILED", "model qualification must bind the exact model configuration")
		}
		n, e := Num(q, "max_calls")
		if e != nil || n < 1 || n > 2 {
			return Fail(422, "GATE_FAILED", "model qualification allows at most two bounded calls")
		}
	}
	return nil
}

func qualificationModelEffectAllowed(tx *sql.Tx, project string, task, payload Object) error {
	if payload["capability"] != "MODEL" || task["task_type"] != "runtime_qualification" {
		return Fail(503, "RESOURCE_UNAVAILABLE", "qualification grants no unplanned effect authority")
	}
	var runID, runtimeID string
	var epoch int64
	if e := tx.QueryRow("SELECT run,runtime,epoch FROM runtime_qualification_runs WHERE project=? AND task=?", project, task["id"]).Scan(&runID, &runtimeID, &epoch); e != nil {
		return e
	}
	plan, _, _, e := qualificationPlan(tx, project, Str(task, "id"), runtimeID)
	if e != nil {
		return e
	}
	permission, ok := plan["model_qualification"].(map[string]any)
	if !ok || permission["route"] != payload["route"] {
		return Fail(403, "FORBIDDEN", "qualification has no exact model route permission")
	}
	dispatch, e := runtimeDispatch(tx, project, runID, epoch)
	if e != nil {
		return e
	}
	profile := dispatch["manifest"].(map[string]any)["admission"].(map[string]any)["profile"].(map[string]any)
	if profile["backend"] != runtimeMuBackend || Hash(profile["model_qualification"]) != Hash(permission) || permission["model_config_hash"] != Hash(profile["model_config"]) || plan["task_hash"] != qualificationTaskHash(task) {
		return Fail(412, "STALE_INPUT", "model qualification authority changed")
	}
	return nil
}

// The SDK decides how to encode model context. The host checks authority and
// bounded provider parameters before accepting that complete body for dispatch.
func validateRuntimeModelRequest(config, payload Object) (Object, error) {
	if len(payload) != 1 {
		return nil, Fail(400, "INVALID_REQUEST", "model request must contain only body")
	}
	body, ok := payload["body"].(map[string]any)
	if !ok || body["model"] != config["model"] || body["stream"] != true {
		return nil, Fail(403, "FORBIDDEN", "model or transport differs from frozen configuration")
	}
	allowed := map[string]bool{"model": true, "messages": true, "stream": true, "stream_options": true, "max_tokens": true, "max_completion_tokens": true, "temperature": true, "top_p": true, "presence_penalty": true, "frequency_penalty": true, "reasoning_effort": true, "stop": true, "tools": true, "tool_choice": true, "parallel_tool_calls": true, "seed": true}
	for key := range body {
		if !allowed[key] {
			return nil, Fail(403, "FORBIDDEN", "model parameter is not permitted: "+key)
		}
	}
	max, _ := Num(config, "max_output_tokens")
	bounded := false
	for _, key := range []string{"max_tokens", "max_completion_tokens"} {
		if _, exists := body[key]; exists {
			n, e := Num(body, key)
			if e != nil || n < 1 || n > max {
				return nil, Fail(403, "FORBIDDEN", "model output exceeds frozen bound")
			}
			bounded = true
		}
	}
	if !bounded || len(Arr(body, "messages")) == 0 {
		return nil, Fail(400, "INVALID_REQUEST", "complete bounded model context required")
	}
	tools := body["tools"]
	if tools == nil {
		tools = Empty()
	}
	if Hash(tools) != Hash(config["tools"]) {
		return nil, Fail(403, "FORBIDDEN", "model tool schemas differ from frozen configuration")
	}
	raw, e := json.Marshal(body)
	if e != nil || len(raw) > 48*1024 {
		return nil, Fail(413, "INVALID_REQUEST", "model context exceeds bridge limit; context must be rebuilt")
	}
	return body, nil
}

func runtimeModelCallGate(tx *sql.Tx, project, run, key string, config Object) error {
	var count int64
	if e := tx.QueryRow(`SELECT count(DISTINCT effect_key) FROM resource_effects WHERE project=? AND run=? AND effect_key<>? AND json_extract(body,'$.payload.capability')='MODEL'`, project, run, key).Scan(&count); e != nil {
		return e
	}
	limit, e := Num(config, "max_calls")
	if e != nil || count >= limit {
		return Fail(403, "FORBIDDEN", "frozen model call limit exhausted")
	}
	return nil
}
