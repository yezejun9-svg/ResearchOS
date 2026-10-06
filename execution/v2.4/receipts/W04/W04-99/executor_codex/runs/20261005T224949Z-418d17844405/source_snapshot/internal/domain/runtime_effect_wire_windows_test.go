//go:build windows

package domain

import (
	"fmt"
	"net/http"
	"testing"

	rt "researchos.local/research-os/adapters/runtime"
)

func TestRuntimeMuLargeSSECompressionAndReplay(t *testing.T) {
	raw := ""
	for i := 0; i < 400; i++ {
		raw += fmt.Sprintf("data: %s\n\n", Bytes(Object{"id": "realistic-stream-event-envelope", "object": "chat.completion.chunk", "created": 1, "model": "fixture-model", "choices": []any{Object{"index": 0, "delta": Object{"content": "x"}, "finish_reason": nil}}}))
	}
	raw += fmt.Sprintf("data: %s\n\ndata: [DONE]\n\n", Bytes(Object{"id": "realistic-stream-event-envelope", "choices": []any{Object{"index": 0, "delta": Object{}, "finish_reason": "stop"}}}))
	if len(raw) <= 64*1024 {
		t.Fatal("fixture must exceed the old raw bridge bound")
	}
	c, route, r, _ := muBrokerFixture(t, func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "text/event-stream")
		fmt.Fprint(w, raw)
	})
	qualifyNativeCoordinator(t, c, route, r)
	var serialized string
	if err := r.f.db.QueryRow("SELECT body FROM resource_effects WHERE run=? ORDER BY sequence DESC LIMIT 1", r.run["id"]).Scan(&serialized); err != nil {
		t.Fatal(err)
	}
	effect, err := Decode([]byte(serialized))
	if err != nil {
		t.Fatal(err)
	}
	receipt := effect["receipt"].(map[string]any)
	if receipt["payload"].(map[string]any)["body"] != raw {
		t.Fatal("durable raw SSE was changed")
	}
	replayed, err := runtimeEffectWireReply(rt.BridgeFrame{Sequence: 99, Key: Str(effect, "key")}, receipt)
	if err != nil || len(Bytes(replayed)) > 64*1024 || replayed["payload"].(map[string]any)["body_encoding"] != "gzip+base64" {
		t.Fatalf("replay encoding %v", err)
	}
	t.Logf("raw SSE %d bytes traversed bounded bridge and SDK; independent qualification accepted; replay uses identical compression", len(raw))
}
