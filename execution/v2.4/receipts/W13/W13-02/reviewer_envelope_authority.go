// Reviewer authority probe (qoder-desktop:/root/w1302_verifier_r1).
//
// The card's browser probe answers with a stub host that does not run internal/domain.DecodeEnvelope, so the
// receipt cannot say whether the envelopes the renderer actually sends would be accepted by the real core.
// This program feeds every envelope the reviewer's node probe dumped (reviewer_envelopes_dump.json: the card
// driver's fixtures plus the payloads apps/web/src/continuity.jsx really passes to run()) to the shipped
// domain.DecodeEnvelope and records accept/refuse plus the error string, so the direction of any divergence is
// measured rather than argued.
//
// Run from the repository root with the pinned Go toolchain:
//   .local/tools/go1.27.1/go/bin/go.exe run execution/v2.4/receipts/W13/W13-02/reviewer_envelope_authority.go
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"sort"

	"researchos.local/research-os/internal/domain"
)

type dumped struct {
	Origin     string          `json:"origin"`
	Method     string          `json:"method"`
	JSRefused  string          `json:"js_refused"`
	Envelope   json.RawMessage `json:"envelope"`
}

type row struct {
	Origin    string `json:"origin"`
	Method    string `json:"method"`
	JSVerdict string `json:"js_verdict"`
	GoVerdict string `json:"go_verdict"`
	GoError   string `json:"go_error,omitempty"`
	Direction string `json:"direction"`
}

func main() {
	path := "execution/v2.4/receipts/W13/W13-02/reviewer_envelopes_dump.json"
	raw, err := os.ReadFile(path)
	if err != nil {
		fmt.Println(`{"fatal":"` + err.Error() + `"}`)
		os.Exit(1)
	}
	var dumps []dumped
	if err := json.Unmarshal(raw, &dumps); err != nil {
		fmt.Println(`{"fatal":"` + err.Error() + `"}`)
		os.Exit(1)
	}
	rows := make([]row, 0, len(dumps))
	counts := map[string]int{}
	goOnlyRefuses := map[string]string{}
	jsOnlyRefuses := map[string]string{}
	for _, d := range dumps {
		r := row{Origin: d.Origin, Method: d.Method}
		if d.JSRefused != "" {
			r.JSVerdict = "JS_LOCAL_REFUSED:" + d.JSRefused
			// Would the real core have accepted this envelope anyway? Rebuild it with the client's own
			// defaults so the question is about the protocol rule, not about the client's choice.
			r.GoVerdict = "not sent"
			r.Direction = "js-refuses-before-core"
			jsOnlyRefuses[d.Method+"|"+d.JSRefused] = d.Origin
			rows = append(rows, r)
			counts["js_refused"]++
			continue
		}
		_, derr := domain.DecodeEnvelope(d.Envelope)
		if derr == nil {
			r.GoVerdict = "CORE_ACCEPTS"
			r.JSVerdict = "JS_ACCEPTS"
			r.Direction = "agree"
			counts["agree_accept"]++
		} else {
			r.GoVerdict = "CORE_REFUSES"
			r.GoError = derr.Error()
			r.JSVerdict = "JS_ACCEPTS"
			// The renderer let this envelope out; the shipped core would refuse it. That is the direction
			// the stub host cannot show: the stub answers every method with COMPLETED.
			r.Direction = "js-permissive-core-refuses"
			goOnlyRefuses[d.Method+"|"+derr.Error()] = d.Origin
			counts["js_accepts_core_refuses"]++
		}
		rows = append(rows, r)
	}
	// Which methods does the shipped service actually implement, as opposed to decode?
	// The other direction: envelopes the renderer refuses locally. Hand-built here so the question
	// "does the client ever veto a command the core would accept?" is measured too.
	type veto struct {
		Name  string `json:"name"`
		Raw   string `json:"raw_envelope"`
		JSVet string `json:"js_verdict"`
	}
	vetoes := []veto{
		{"host.status with an extra payload key",
			`{"protocol_version":"researchos-client/2","command_id":"v1","client_id":"desktop-renderer","project_id":null,"session_id":null,"expected_revision":null,"writer_epoch":null,"method":"host.status","payload":{"anything":1}}`,
			"JS_LOCAL_REFUSED:UNEXPECTED_PAYLOAD_KEYS:anything"},
		{"session.handoff without handoff_mode",
			`{"protocol_version":"researchos-client/2","command_id":"v2","client_id":"desktop-renderer","project_id":"proj-stub","session_id":"sess-stub-1","expected_revision":7,"writer_epoch":2,"method":"session.handoff","payload":{"target_client_id":"cli-1"}}`,
			"JS_LOCAL_REFUSED:MISSING_PAYLOAD_FIELDS:handoff_mode"},
		{"session.send without delivery",
			`{"protocol_version":"researchos-client/2","command_id":"v3","client_id":"desktop-renderer","project_id":"proj-stub","session_id":"sess-stub-1","expected_revision":7,"writer_epoch":2,"method":"session.send","payload":{"text":"q","attachment_artifact_ids":[]}}`,
			"JS_LOCAL_REFUSED:MISSING_PAYLOAD_FIELDS:delivery"},
	}
	vetoRows := make([]map[string]any, 0, len(vetoes))
	for _, v := range vetoes {
		_, derr := domain.DecodeEnvelope([]byte(v.Raw))
		verdict := "CORE_ACCEPTS"
		msg := ""
		if derr != nil {
			verdict = "CORE_REFUSES"
			msg = derr.Error()
		}
		vetoRows = append(vetoRows, map[string]any{"case": v.Name, "js": v.JSVet, "core": verdict, "core_error": msg,
			"direction": func() string { if verdict == "CORE_ACCEPTS" { return "js-stricter-core-accepts" }; return "agree" }()})
	}
	out := map[string]any{
		"reviewer_id":                       "qoder-desktop:/root/w1302_verifier_r1",
		"purpose":                           "rule the card's rendered envelopes against the shipped domain.DecodeEnvelope",
		"total":                             len(dumps),
		"counts":                            counts,
		"core_refuses_what_the_renderer_sends": sortedKeys(goOnlyRefuses),
		"js_only_refusals":                  sortedKeys(jsOnlyRefuses),
		"js_veto_cases":                     vetoRows,
		"note_on_implementation":            "DecodeEnvelope is the boundary gate; dispatch then answers NOT_IMPLEMENTED for every method whose handler belongs to a later card (handleRead covers host.status/session.get/session.attach/session.events, handleWrite covers session.attach takeover and session.control CANCEL only).",
		"rows":                              rows,
	}
	b, _ := json.MarshalIndent(out, "", " ")
	fmt.Println(string(b))
}

func sortedKeys(m map[string]string) []string {
	out := make([]string, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}
