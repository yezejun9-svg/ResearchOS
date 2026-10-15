//go:build windows

package domain

import (
	"context"
	"fmt"
	"testing"
)

func TestRuntimeMuResponseParser(t *testing.T) {
	sse := func(delta Object, finish any) string {
		return fmt.Sprintf("data: %s\n\n", Bytes(Object{"choices": []any{Object{"index": 0, "delta": delta, "finish_reason": finish}}}))
	}
	valid := sse(Object{"role": "assistant", "tool_calls": []any{Object{"index": 0, "id": "call-one", "type": "function", "function": Object{"name": "read", "arguments": "{\"path\":"}}}}, nil) + sse(Object{"tool_calls": []any{Object{"index": 0, "function": Object{"arguments": "\"a.txt\"}"}}}}, nil) + sse(Object{}, "tool_calls") + "data: [DONE]\n\n"
	parsed, err := muResponse(valid)
	if err != nil || len(parsed.Calls) != 1 || parsed.Calls[0]["name"] != "read" || parsed.Calls[0]["arguments"].(map[string]any)["path"] != "a.txt" {
		t.Fatalf("split tool arguments: %+v %v", parsed, err)
	}
	for name, raw := range map[string]string{
		"missing finish":           sse(Object{"content": "reply"}, nil) + "data: [DONE]\n\n",
		"length finish":            sse(Object{"content": "partial"}, "length") + "data: [DONE]\n\n",
		"tool finish without call": sse(Object{}, "tool_calls") + "data: [DONE]\n\n",
		"data after finish":        sse(Object{"content": "reply"}, "stop") + sse(Object{"content": "extra"}, nil) + "data: [DONE]\n\n",
		"model error":              "data: {\"error\":{\"message\":\"failed\"}}\n\ndata: [DONE]\n\n",
		"incomplete arguments":     sse(Object{"tool_calls": []any{Object{"index": 0, "id": "call", "type": "function", "function": Object{"name": "read", "arguments": "{"}}}}, "tool_calls") + "data: [DONE]\n\n",
	} {
		t.Run(name, func(t *testing.T) {
			if _, err := muResponse(raw); err == nil {
				t.Fatal("invalid response accepted")
			}
		})
	}
}

func TestRuntimeMuIndependentQualification(t *testing.T) {
	c, route, r, calls := muBrokerFixture(t, nil)
	qualifyNativeCoordinator(t, c, route, r)
	if calls.Load() != 1 || r.registration["status"] != "AVAILABLE" {
		t.Fatalf("qualification not independently accepted: %d %s", calls.Load(), Bytes(r.registration))
	}
	var actual int
	if err := r.f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='BudgetLedgerEntry' AND json_extract(body,'$.run_id')=? AND json_extract(body,'$.cost_basis')='ACTUAL'", r.run["id"]).Scan(&actual); err != nil || actual != 0 {
		t.Fatalf("unknown cost changed: %d %v", actual, err)
	}
	t.Log("real SDK + no-network AppContainer + loopback provider fixture + independent verifier acceptance; monetary actual remains unknown, no LIVE qualification claim")
}

func TestRuntimeMuVerificationRejectsFabrication(t *testing.T) {
	c, route, r, _ := muBrokerFixture(t, nil)
	if err := c.RunAdmitted(context.Background(), route, r.run, r.lease); err != nil {
		t.Fatal(err)
	}
	f := r.f
	r.run = f.read("runs", Str(r.run, "id"))
	r.task = f.read("tasks", Str(r.task, "id"))
	artifact := f.read("artifacts", Arr(r.run, "result_artifact_ids")[0].(string))
	request := (&orchestrationFixture{f: f, owner: r.ownerToken}).acceptance(r, artifact)
	prepared, err := f.s.prepareTaskAcceptance(context.Background(), f.token, f.project, request)
	if err != nil {
		t.Fatal(err)
	}
	if prepared.verdict != "PASS" {
		t.Fatalf("valid baseline failed: %s", Bytes(prepared.checks))
	}
	cases := map[string]func(Object){
		"worker count": func(s Object) { muMutateResult(s, func(o Object) { o["model_calls"] = 9 }) },
		"forged assistant": func(s Object) {
			muMutateResult(s, func(o Object) {
				a := Arr(o, "messages")
				a[len(a)-1].(map[string]any)["content"] = []any{Object{"type": "text", "text": "invented"}}
			})
		},
		"wrong model":        func(s Object) { muMutateResult(s, func(o Object) { o["model_ref"] = "unbound" }) },
		"worker actual zero": func(s Object) { muMutateResult(s, func(o Object) { o["actual_cost"] = dollars("0") }) },
		"wrong epoch":        func(s Object) { muMutateResult(s, func(o Object) { o["epoch"] = 99 }) },
		"error stop": func(s Object) {
			muMutateResult(s, func(o Object) { a := Arr(o, "messages"); a[len(a)-1].(map[string]any)["stopReason"] = "error" })
		},
		"missing effect": func(s Object) { s["mu_turn"].(map[string]any)["effects"] = Empty() },
		"unknown effect": func(s Object) {
			a := Arr(s["mu_turn"].(map[string]any), "effects")
			a[len(a)-1].(map[string]any)["state"] = "UNKNOWN"
		},
		"not applied": func(s Object) {
			a := Arr(s["mu_turn"].(map[string]any), "effects")
			a[len(a)-1].(map[string]any)["state"] = "NOT_APPLIED"
		},
		"prepared only": func(s Object) { m := s["mu_turn"].(map[string]any); m["effects"] = Arr(m, "effects")[:1] },
		"forged receipt": func(s Object) {
			a := Arr(s["mu_turn"].(map[string]any), "effects")
			a[len(a)-1].(map[string]any)["receipt"].(map[string]any)["receipt_id"] = "sha256:fake"
		},
		"reservation missing": func(s Object) { s["mu_turn"].(map[string]any)["ledger"] = Empty() },
		"unknown money released": func(s Object) {
			m := s["mu_turn"].(map[string]any)
			var l Object
			for _, v := range Arr(m, "ledger") {
				candidate := v.(map[string]any)
				if candidate["provider_request_id"] == Arr(m, "effects")[0].(map[string]any)["key"] {
					l = candidate
					break
				}
			}
			extra := Merge(l, Object{"id": "fake-release", "operation": "RELEASE"})
			m["ledger"] = append(Arr(m, "ledger"), extra)
		},
		"prompt drift": func(s Object) {
			s["mu_turn"].(map[string]any)["prompt"].(map[string]any)["task_description"] = "changed intent"
		},
		"projection copied from another dispatch": func(s Object) {
			m := s["mu_turn"].(map[string]any)["dispatch"].(map[string]any)["manifest"].(map[string]any)
			m["model_execution_projection"].(map[string]any)["dispatch_key"] = "foreign-dispatch"
		},
		"projection effective hash": func(s Object) {
			m := s["mu_turn"].(map[string]any)["dispatch"].(map[string]any)["manifest"].(map[string]any)
			m["model_execution_projection"].(map[string]any)["effective_model_config_hash"] = "sha256:forged"
		},
		"projection source profile": func(s Object) {
			m := s["mu_turn"].(map[string]any)["dispatch"].(map[string]any)["manifest"].(map[string]any)
			m["admission"].(map[string]any)["profile"].(map[string]any)["model"] = "other"
		},
		"projection old tools": func(s Object) {
			m := s["mu_turn"].(map[string]any)
			effects := Arr(m, "effects")
			for _, v := range effects {
				e := v.(map[string]any)
				request, _ := e["payload"].(map[string]any)
				p, _ := request["payload"].(map[string]any)
				body, _ := p["body"].(map[string]any)
				if body != nil {
					body["tools"] = []any{Object{"type": "function", "function": Object{"name": "run_check", "parameters": Object{"type": "object"}}}}
				}
			}
		},
		"projection model excess": func(s Object) {
			m := s["mu_turn"].(map[string]any)
			muMutateResult(s, func(o Object) { o["model_calls"] = 2 })
			m["effects"] = append(Arr(m, "effects"), Object{"key": "forged-second-model"})
		},
		"effect order": func(s Object) {
			a := Arr(s["mu_turn"].(map[string]any), "effects")
			a[len(a)-1].(map[string]any)["_journal_position"] = 0
		},
	}
	for name, mutate := range cases {
		t.Run(name, func(t *testing.T) {
			clone := muCloneSnapshot(t, prepared.snapshot)
			mutate(clone)
			status, why := verifyMuTurn(clone)
			if status != "FAIL" {
				t.Fatalf("fabrication accepted: %s %s", status, why)
			}
		})
	}
	// An append-only broker fact arriving between prepare/finalize invalidates the
	// entire computation, even when the already loaded artifact did not change.
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	facts := Arr(prepared.snapshot["mu_turn"].(map[string]any), "effects")
	changed := Merge(facts[len(facts)-1].(map[string]any), Object{"audit_marker": "concurrent trusted evidence"})
	if err = effectAppend(tx, f.project, Str(r.run, "id"), Str(changed, "key"), changed); err != nil {
		tx.Rollback()
		t.Fatal(err)
	}
	if err = tx.Commit(); err != nil {
		t.Fatal(err)
	}
	tx, err = f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback()
	p, err := authenticate(tx, f.token)
	if err != nil {
		t.Fatal(err)
	}
	_, err = f.s.acceptTask(tx, p, f.project, request, prepared, ID())
	fault, ok := err.(*Fault)
	if !ok || fault.Code != "STALE_INPUT" || fault.Message != "inputs changed during independent verification" {
		t.Fatalf("double snapshot guard: %v", err)
	}
}

func muCloneSnapshot(t *testing.T, s Object) Object {
	t.Helper()
	clone, err := Decode(Bytes(s))
	if err != nil {
		t.Fatal(err)
	}
	original := Arr(s, "artifacts")
	for i, v := range Arr(clone, "artifacts") {
		v.(map[string]any)["bytes"] = append([]byte(nil), original[i].(map[string]any)["bytes"].([]byte)...)
	}
	return clone
}
func muMutateResult(s Object, fn func(Object)) {
	a := Arr(s, "artifacts")[0].(map[string]any)
	o, _ := Decode(a["bytes"].([]byte))
	fn(o)
	a["bytes"] = Bytes(o)
}
