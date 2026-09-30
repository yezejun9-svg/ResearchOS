package domain

import (
	"context"
	"testing"
)

func TestIntentRejectsUntrustedProposals(t *testing.T) {
	f, req, _, task := intentFixture(t, `请先后生成两份 {"result":"verified"} JSON 报告。`)
	tx, e := f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	meta, e := f.s.planningSnapshot(tx, f.project, task)
	tx.Rollback()
	if e != nil {
		t.Fatal(e)
	}
	valid := intentBrief(f, req, task, true)
	baseline := Object{"planning": meta, "artifacts": []any{Object{"artifact": Object{"evidence_kind": "GENERATED", "media_type": "application/json"}, "bytes": Bytes(valid)}}}
	for _, key := range []string{"planning.provenance-v1", "planning.dag-capabilities-v1", "planning.open-questions-v1"} {
		if status, actual := verifyPlanning(baseline, key); status != "PASS" {
			t.Fatalf("baseline invalid: %s", actual)
		}
	}
	cases := []struct {
		name   string
		mutate func(Object)
	}{
		{"forged-USER_STATED", func(b Object) { Arr(b, "facts")[0].(map[string]any)["text"] = "用户要求利润增长 80%" }},
		{"promoted-OBSERVED", func(b Object) { Arr(b, "facts")[0].(map[string]any)["basis"] = "OBSERVED" }},
		{"cross-project", func(b Object) { b["project_id"] = ID() }},
		{"stale-raw", func(b Object) { b["raw_intent_hash"] = Digest([]byte("other")) }},
		{"stale-context", func(b Object) { b["context_ref"].(map[string]any)["revision"] = 77 }},
		{"expanded-budget", func(b Object) { b["budget_policy_ref"].(map[string]any)["id"] = ID() }},
		{"arbitrary-shell", func(b Object) { Arr(b, "nodes")[0].(map[string]any)["action"] = "powershell -c arbitrary" }},
		{"unknown-check", func(b Object) {
			Arr(Arr(b, "nodes")[0].(map[string]any), "checks")[0].(map[string]any)["command_key"] = "unknown.verifier"
		}},
		{"invented-business-threshold", func(b Object) {
			Arr(Arr(b, "nodes")[0].(map[string]any), "checks")[0].(map[string]any)["expected"] = `{"profit_improved":true}`
		}},
		{"cycle", func(b Object) { Arr(b, "nodes")[0].(map[string]any)["depends_on"] = []any{"second"} }},
		{"cross-goal-dependency", func(b Object) { Arr(b, "nodes")[0].(map[string]any)["depends_on"] = []any{ID()} }},
		{"missing-output", func(b Object) { Arr(b, "nodes")[0].(map[string]any)["outputs"] = Empty() }},
		{"deleted-failure-exits", func(b Object) { b["failure_exits"] = Empty() }},
		{"unbounded-wall-time", func(b Object) { Arr(b, "nodes")[0].(map[string]any)["wall_time_seconds"] = 999999 }},
		{"ignored-question", func(b Object) {
			b["open_questions"] = []any{Object{"question_id": "unknown", "question": "业务阈值？", "options": Empty(), "blocking": true}}
		}},
		{"model-revision-replay", func(b Object) { b["revision"] = 2 }},
		{"unknown-privilege-field", func(b Object) { b["grant_owner"] = true }},
	}
	for _, test := range cases {
		t.Run(test.name, func(t *testing.T) {
			body, _ := Decode(Bytes(valid))
			test.mutate(body)
			snap := Object{"planning": meta, "artifacts": []any{Object{"artifact": Object{"evidence_kind": "GENERATED", "media_type": "application/json"}, "bytes": Bytes(body)}}}
			failed := false
			for _, key := range []string{"planning.provenance-v1", "planning.dag-capabilities-v1", "planning.open-questions-v1"} {
				status, _ := verifyPlanning(snap, key)
				failed = failed || status == "FAIL"
			}
			if !failed {
				t.Fatal("untrusted proposal passed all gates")
			}
		})
	}
}

func TestIntentMentionAndNegationAreNotDeliveryAuthority(t *testing.T) {
	for _, text := range []string{`不要生成 {"result":"verified"}。`, `请研究论文，其中举了 {"result":"verified"} 的例子。`, `请先后生成两份 {"result":"verified"} JSON 报告。但不要执行。`} {
		meta := Object{"sources": []any{Object{"status": "ACCEPTED", "basis": "USER_STATED", "text": text}}}
		if _, count, _ := planningJSONAuthorization(meta); count != 0 {
			t.Fatalf("mention authorized output: %s", text)
		}
	}
}

func TestIntentOwnerBindingRejectsOtherActorAndDuplicateSubmission(t *testing.T) {
	f := contextFixture(t)
	body := Object{"requirement_key": "INTENT-" + ID(), "text": "原话不改", "basis": "USER_STATED", "source_refs": Empty(), "rationale": "Owner statement", "supersedes_id": nil, "acceptance_check_ids": Empty()}
	req := f.expect(201, "POST", f.path("/requirements"), ID(), f.stateTag(), body)
	f.expect(409, "POST", f.path("/requirements"), ID(), f.stateTag(), body)
	f.switchPrincipal("another-owner", []string{"OWNER"})
	f.expect(403, "POST", f.path("/requirements/"+Str(req, "id")+"/actions"), ID(), testTag(req), Object{"action": "ACCEPT", "reason": "not submitting actor", "source_validation_refs": Empty()})
	var count int
	f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='Requirement'").Scan(&count)
	if count != 1 {
		t.Fatal("duplicate conflict persisted a second requirement")
	}
}

func TestIntentStaleAuthorityCannotAcceptOrCompile(t *testing.T) {
	o, r, _, b := intentReport(t, true)
	f := o.f
	if e := f.s.RevokePrincipal(context.Background(), f.owner); e != nil {
		t.Fatal(e)
	}
	g := f.read("goals", Str(o.goal, "id"))
	task := f.read("tasks", Str(r.task, "id"))
	body, _ := Decode(Bytes(b))
	body["subject_ref"] = Ref(g, "Goal")
	body["run_id"] = nil
	body["input_refs"] = []any{Ref(o.req, "Requirement"), Ref(task, "Task")}
	f.expect(403, "POST", f.path("/acceptances"), ID(), testTag(g), body)
	var count int
	f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='Goal'").Scan(&count)
	if count != 1 {
		t.Fatal("revoked Owner plan compiled")
	}
}
