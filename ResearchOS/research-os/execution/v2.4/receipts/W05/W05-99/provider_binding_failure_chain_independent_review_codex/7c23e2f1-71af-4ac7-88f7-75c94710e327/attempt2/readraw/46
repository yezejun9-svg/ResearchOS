package domain

import (
	"strings"
	"testing"
)

func providerFixtureConfig(endpoint string) Object {
	return Object{"ref": "provider-fixture-v1", "api": "openai-completions", "provider": "opencode-go", "model": "deepseek-v4.1-flash", "endpoint": endpoint, "route": "provider-fixture", "max_calls": 4, "max_output_tokens": 512, "tools": Empty(), "provider_policy": runtimeProviderPolicy}
}
func TestProviderBindingConfigAndBody(t *testing.T) {
	c := providerFixtureConfig(runtimeProviderEndpoint)
	profile := Object{"backend": runtimeMuBackend, "model": c["model"], "model_config": c, "bundle_hash": Digest([]byte("fixture"))}
	body := Object{"model": c["model"], "messages": []any{Object{"role": "user", "content": "fixture"}}, "stream": true, "tools": Empty(), "thinking": Object{"type": "enabled"}, "reasoning_effort": "high", "max_tokens": 512}
	if err := validateRuntimeModelConfig(profile); err != nil {
		t.Fatal(err)
	}
	if _, err := validateRuntimeModelRequest(c, Object{"body": body}); err != nil {
		t.Fatal(err)
	}
	for _, bad := range []any{nil, false, 1, "other", Object{}} {
		t.Run("policy-"+Hash(bad), func(t *testing.T) {
			copy, _ := Decode(Bytes(c))
			copy["provider_policy"] = bad
			if _, err := providerPolicy(copy); err == nil {
				t.Fatal("accepted unknown policy")
			}
		})
	}
	for name, change := range map[string]func(Object){"off": func(b Object) { b["thinking"] = Object{"type": "disabled"} }, "low": func(b Object) { b["reasoning_effort"] = "low" }, "cap": func(b Object) { b["max_tokens"] = 513 }, "conflict": func(b Object) { b["max_completion_tokens"] = 512 }, "headers": func(b Object) { b["headers"] = Object{"x-opencode-session": "injected"} }} {
		t.Run(name, func(t *testing.T) {
			b, _ := Decode(Bytes(body))
			change(b)
			if _, err := validateRuntimeModelRequest(c, Object{"body": b}); err == nil {
				t.Fatal("accepted changed fixed body")
			}
		})
	}
	for _, endpoint := range []string{"https://evil.invalid/zen/go/v1/chat/completions", runtimeProviderEndpoint + "?x=1", runtimeProviderEndpoint + "#x", "http://localhost:1234/zen/go/v1/chat/completions"} {
		if providerPolicyEndpoint(endpoint, true) {
			t.Fatal("endpoint accepted", endpoint)
		}
	}
	if providerPolicyEndpoint("http://127.0.0.1:1234/zen/go/v1/chat/completions", false) || !providerPolicyEndpoint("http://127.0.0.1:1234/zen/go/v1/chat/completions", true) {
		t.Fatal("trusted fixture endpoint boundary")
	}
	legacy := modelFixtureConfig("https://fixture.invalid/v1/chat/completions")
	before := string(Bytes(legacy))
	if ok, err := providerPolicy(legacy); ok || err != nil || string(Bytes(legacy)) != before {
		t.Fatal("absent policy mutated")
	}
}

func TestProviderBindingReasoningExactHistory(t *testing.T) {
	c := providerFixtureConfig(runtimeProviderEndpoint)
	raw := "data: {\"choices\":[{\"index\":0,\"delta\":{\"reasoning\":\"  原文 \",\"reasoning_text\":\"ignored\"}}]}\n\ndata: {\"choices\":[{\"index\":0,\"delta\":{\"reasoning_content\":\"\\n续文\",\"reasoning\":\"ignored\",\"content\":\"answer\"},\"finish_reason\":\"stop\"}]}\n\ndata: [DONE]\n\n"
	m := Object{"role": "assistant", "stopReason": "stop", "content": []any{Object{"type": "thinking", "thinking": "  原文 \n续文", "thinkingSignature": "reasoning_content"}, Object{"type": "text", "text": "answer"}}}
	expected, err := providerResponse(c, raw)
	actual, ae := muSDKAssistant(m)
	if err != nil || ae != nil || Hash(expected) != Hash(actual) || verifyProviderReasoning(raw, m) != nil {
		t.Fatalf("selected alias mismatch: %+v %v", expected, err)
	}
	wire := []any{Object{"role": "assistant", "content": "answer", "reasoning_content": "  原文 \n续文"}}
	if err = verifyProviderWireHistory(wire, []any{m}); err != nil {
		t.Fatal(err)
	}
	for _, bad := range []string{"原文 \n续文", "  原文 ", "ignored", ""} {
		w, _ := Decode(Bytes(wire[0]))
		w["reasoning_content"] = bad
		if verifyProviderWireHistory([]any{w}, []any{m}) == nil {
			t.Fatal("changed reasoning accepted")
		}
	}
	swapped, _ := Decode(Bytes(m))
	parts := Arr(swapped, "content")
	parts[0], parts[1] = parts[1], parts[0]
	if verifyProviderReasoning(raw, swapped) == nil {
		t.Fatal("reordered content accepted")
	}
	textFirst := strings.ReplaceAll(raw, "\"reasoning\":\"  原文 \"", "\"reasoning_text\":\"  原文 \"")
	// Different first-signature is meaningful even when thinking bytes agree.
	_ = textFirst
	for _, text := range []string{"data: {\"choices\":[{\"delta\":{\"reasoning_details\":[]}}]}\n\n", "data: {\"choices\":[{\"delta\":{\"signature\":\"encrypted\"}}]}\n\n"} {
		if providerSSEPolicy([]byte(text)) == nil {
			t.Fatal("unsupported reasoning alternative")
		}
	}
}

func TestProviderBindingWireSignatureWhitespaceAndBlocks(t *testing.T) {
	m := Object{"content": []any{Object{"type": "thinking", "thinking": " \n", "thinkingSignature": "reasoning_content"}, Object{"type": "thinking", "thinking": " a ", "thinkingSignature": "reasoning_text"}, Object{"type": "thinking", "thinking": "b\n", "thinkingSignature": "reasoning_content"}}}
	got, err := providerWireReasoning(m, true)
	want := Object{"reasoning_text": " a \nb\n", "reasoning_content": ""}
	if err != nil || Hash(got) != Hash(want) {
		t.Fatalf("first retained signature/newline/empty field: %s %v", Bytes(got), err)
	}
}
