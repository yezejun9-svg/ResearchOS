package domain

import (
	"strings"
	"testing"
)

func modelFixtureConfig(endpoint string) Object {
	return Object{"ref": "model-fixture-v1", "api": "openai-completions", "provider": "openai", "model": "fixture-model", "endpoint": endpoint, "route": "model-fixture", "max_output_tokens": 512, "max_calls": 4, "tools": Empty()}
}

func TestRuntimeModelSSETermination(t *testing.T) {
	for _, tc := range []struct {
		name, raw string
		valid     bool
	}{
		{"complete", "data: {\"choices\":[]}\n\ndata: [DONE]\n\n", true},
		{"crlf", "data: {\"choices\":[]}\r\n\r\ndata: [DONE]\r\n\r\n", true},
		{"in-content", "data: {\"content\":\"[DONE]\"}\n\n", false},
		{"trailing-truncation", "data: {\"choices\":[]}\n\ndata: [DONE]\n\ndata: {", false},
		{"later-data", "data: {\"choices\":[]}\n\ndata: [DONE]\n\ndata: {}\n\n", false},
		{"missing-delimiter", "data: {}\n\ndata: [DONE]\n", false},
		{"no-content", "data: [DONE]\n\n", false},
	} {
		t.Run(tc.name, func(t *testing.T) {
			if got := completeRuntimeModelSSE([]byte(tc.raw)); got != tc.valid {
				t.Fatalf("complete=%v want=%v", got, tc.valid)
			}
		})
	}
}

func TestRuntimeModelRequestBounds(t *testing.T) {
	config := modelFixtureConfig("https://model.invalid/v1/chat/completions")
	valid := Object{"body": Object{"model": "fixture-model", "stream": true, "max_tokens": 512, "messages": []any{Object{"role": "user", "content": "bounded prompt"}}}}
	if _, e := validateRuntimeModelRequest(config, valid); e != nil {
		t.Fatal(e)
	}
	for _, tc := range []struct {
		name   string
		mutate func(Object)
	}{
		{"model", func(v Object) { v["body"].(map[string]any)["model"] = "other" }},
		{"unbounded", func(v Object) { delete(v["body"].(map[string]any), "max_tokens") }},
		{"limit", func(v Object) { v["body"].(map[string]any)["max_tokens"] = 513 }},
		{"fraction", func(v Object) { v["body"].(map[string]any)["max_tokens"] = 1.5 }},
		{"credential", func(v Object) { v["headers"] = Object{"Authorization": "attacker"} }},
		{"tool", func(v Object) {
			v["body"].(map[string]any)["tools"] = []any{Object{"type": "function", "function": Object{"name": "unexpected"}}}
		}},
		{"extra", func(v Object) { v["body"].(map[string]any)["store"] = true }},
		{"overflow", func(v Object) {
			v["body"].(map[string]any)["messages"] = []any{Object{"role": "user", "content": strings.Repeat("a", 49*1024)}}
		}},
	} {
		t.Run(tc.name, func(t *testing.T) {
			v, _ := Decode(Bytes(valid))
			tc.mutate(v)
			if _, e := validateRuntimeModelRequest(config, v); e == nil {
				t.Fatal("unfrozen request accepted")
			}
		})
	}
}
