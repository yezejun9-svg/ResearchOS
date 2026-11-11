package verifier

import (
	"bytes"
	"context"
	"strings"
	"testing"
)

func TestVerifierPrivateFramesFailClosed(t *testing.T) {
	for name, raw := range map[string]string{"unknown field": "{\"protocol\":\"x\",\"token\":\"secret\"}\n", "trailing object": "{}{}\n", "incomplete": "{}", "oversize": strings.Repeat(" ", MaximumFrameBytes+1) + "\n"} {
		t.Run(name, func(t *testing.T) {
			var c Challenge
			if e := ReadFrame(strings.NewReader(raw), &c); e == nil {
				t.Fatal("malformed private frame accepted")
			}
		})
	}
	var out bytes.Buffer
	challenge := Challenge{Protocol: Protocol, Nonce: strings.Repeat("a", 64)}
	if e := WriteFrame(&out, challenge); e != nil {
		t.Fatal(e)
	}
	var hello bytes.Buffer
	if _, e := Handshake(&out, &hello); e != nil {
		t.Fatal(e)
	}
	var result Hello
	if e := ReadFrame(&hello, &result); e != nil || result.Nonce != challenge.Nonce || result.ServiceID != ServiceID || result.PID <= 0 {
		t.Fatalf("handshake identity missing: %+v %v", result, e)
	}
}

func TestVerifierRejectsUntrustedJobBeforeNetwork(t *testing.T) {
	for _, endpoint := range []string{"https://127.0.0.1:1", "http://localhost:1", "http://example.com", "http://user@127.0.0.1:1", "http://127.0.0.1:1/?token=x"} {
		t.Run(endpoint, func(t *testing.T) {
			result, e := Verify(context.Background(), Job{APIURL: endpoint, Token: "must-not-leak"})
			if e == nil || result.Status != "REJECTED" || strings.Contains(e.Error(), "must-not-leak") {
				t.Fatal("unsafe job accepted or token exposed")
			}
		})
	}
}
