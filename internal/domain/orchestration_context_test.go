package domain

import (
	"context"
	"os"
	"path/filepath"
	"testing"
)

func TestW06ContextContinuation(t *testing.T) {
	if os.Getenv("RESEARCHOS_C01_MODEL") != "1" {
		t.Skip("C01/G02 runner explicitly enables the real model")
	}
	o := orchestrationSetup(t)
	f := o.f
	rubric := f.artifact(Object{"rubric": "explicit fixture decision"}, Empty())
	d1 := f.decision(o.req, rubric, nil, "A")
	f.apply(f.proposal([]any{Ref(d1, "DecisionReceipt")}))
	o.owner = f.token
	source := f.artifact(Object{"name": "continuation-arithmetic", "operands": []any{17, 25}, "operations": Object{"A": "ADD", "B": "MULTIPLY"}}, []any{Ref(o.req, "Requirement")})
	first := o.task("accepted-predecessor", Empty(), []any{Ref(source, "Artifact")})
	r := o.claim(first)
	a := o.report(r, []byte(`{"result":"verified"}`))
	b := o.acceptance(r, a)
	f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(r.task), b)
	f.token = o.owner
	beforeTask := o.task("continue-current-decision", []any{first["id"]}, []any{Ref(d1, "DecisionReceipt"), Ref(source, "Artifact")})
	before, e := f.s.GetTaskContext(context.Background(), f.token, f.project, Str(beforeTask, "id"))
	if e != nil {
		t.Fatal(e)
	}
	d2 := f.decision(o.req, rubric, d1["id"], "B")
	f.apply(f.proposal([]any{Ref(d2, "DecisionReceipt")}))
	o.owner = f.token
	// Revalidation uses the existing W04 replacement of explicitly superseded refs.
	current := f.read("tasks", Str(beforeTask, "id"))
	current = f.expect(200, "POST", f.path("/tasks/"+Str(current, "id")+"/actions"), ID(), testTag(current), Object{"action": "REVALIDATE", "reason": "resume with current accepted decision"})
	f.bundle(current)
	current = f.read("tasks", Str(current, "id"))
	current = f.expect(200, "POST", f.path("/tasks/"+Str(current, "id")+"/actions"), ID(), testTag(current), Object{"action": "SUBMIT", "reason": "new context snapshot"})
	next := o.claim(current)
	bundle, e := f.s.GetTaskContext(context.Background(), f.token, f.project, Str(current, "id"))
	if e != nil {
		t.Fatal(e)
	}
	var questionsBefore int
	if e = f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='AgentMessage' AND json_extract(body,'$.message_type')='QUESTION'", f.project).Scan(&questionsBefore); e != nil {
		t.Fatal(e)
	}
	receipt, command := c01FreshAgent(t, next, bundle, Object{"ref": Ref(d1, "DecisionReceipt"), "record": d1})
	questions, ok := receipt["questions"].([]any)
	if !ok {
		t.Fatal("missing actual question channel")
	}
	questionEvents := Empty()
	for _, value := range questions {
		text, ok := value.(string)
		if !ok || text == "" {
			t.Fatal("invalid QUESTION")
		}
		executorToken := f.token
		f.token = o.owner
		tag := f.stateTag()
		f.token = executorToken
		questionEvents = append(questionEvents, f.expect(201, "POST", f.path("/messages"), ID(), tag, Object{"task_id": current["id"], "run_id": next.run["id"], "correlation_id": ID(), "recipient_id": f.owner, "message_type": "QUESTION", "body": text, "refs": []any{Ref(bundle, "ContextBundle")}}))
	}
	var questionsAfter int
	if e = f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='AgentMessage' AND json_extract(body,'$.message_type')='QUESTION'", f.project).Scan(&questionsAfter); e != nil {
		t.Fatal(e)
	}
	if out := os.Getenv("W06_EVIDENCE_DIR"); out != "" {
		if e = os.WriteFile(filepath.Join(out, "C01-question-events.json"), Bytes(Object{"model_requests": questions, "events": questionEvents, "before": questionsBefore, "after": questionsAfter}), 0600); e != nil {
			t.Fatal(e)
		}
	}
	orchestrationAssert(t, "C01-01-CONTINUATION", []any{o.goal["id"], o.goal["original_intent"], current["id"], d2["id"], d2["revision"], "MULTIPLY", []any{17, 25}, 425}, []any{receipt["goal_id"], receipt["goal_intent"], receipt["next_task_id"], receipt["current_decision_id"], receipt["current_decision_revision"], receipt["operation"], receipt["operands"], receipt["total"]}, Object{"before": before, "after": bundle, "fresh_agent": receipt, "command": command, "host_computation": "17 * 25 = 425; current B, superseded A would give 42"})
	orchestrationAssert(t, "C01-02-HISTORY-NO-ASK", []any{d1["id"], 0, 0}, []any{receipt["historical_decision_id"], len(questions), questionsAfter - questionsBefore}, Object{"question_events": questionEvents, "question_events_before": questionsBefore, "question_events_after": questionsAfter})
	found := false
	for _, v := range Arr(bundle, "version_vector") {
		ref := v.(map[string]any)
		if ref["id"] == receipt["source_id"] && ref["content_hash"] == receipt["source_hash"] && receipt["source_id"] == source["id"] {
			found = true
		}
	}
	tx, e := f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	traced := 0
	for _, v := range Arr(bundle, "version_vector") {
		ref := v.(map[string]any)
		object, err := version(tx, f.project, ref)
		if err != nil {
			t.Fatal(err)
		}
		if ref["entity_type"] == "Artifact" {
			var data []byte
			if err = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE storage_key=? AND sealed=1", object["storage_key"]).Scan(&data); err != nil || Digest(data) != object["content_hash"] {
				t.Fatal("source hash verification failed", err)
			}
		}
		traced++
	}
	tx.Rollback()
	orchestrationAssert(t, "C01-03-PROVENANCE", []any{true, bundle["source_manifest_hash"], true, len(Arr(bundle, "version_vector"))}, []any{found, bundle["source_manifest_hash"], bundle["receipt_hash"] == Receipt(bundle) && command["bundle_hash"] == Hash(bundle), traced}, Object{"source_ref": Ref(source, "Artifact"), "authorized_snapshot_ids": bundle["authorized_snapshot_ids"], "bundle_ref": Ref(bundle, "ContextBundle")})
	// Adapter seals the fresh process's actual structured candidate through scoped
	// upload/report; executor still cannot accept it.
	candidate, ok := receipt["candidate"].(map[string]any)
	if !ok || len(candidate) == 0 {
		t.Fatal("empty candidate")
	}
	computationLog := next.sealKind(Bytes(Object{"model_output": receipt, "command": command, "source_ref": Ref(source, "Artifact"), "decision_ref": Ref(d2, "DecisionReceipt"), "bundle_ref": Ref(bundle, "ContextBundle"), "host_computation_passed": true}), "LOG")
	result := o.report(next, Bytes(candidate))
	request := o.acceptance(next, result)
	acceptance := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(next.task), request)
	if out := os.Getenv("W06_EVIDENCE_DIR"); out != "" {
		if e = os.WriteFile(filepath.Join(out, "C01-sealed-artifacts.json"), Bytes(Object{"computation_log": computationLog, "result": result, "acceptance": acceptance, "model_output": receipt}), 0600); e != nil {
			t.Fatal(e)
		}
	}
	orchestrationAssert(t, "W06-G02-SUCCESSOR-ACCEPTED", "PASS", acceptance["verdict"], Object{"run_id": next.run["id"], "result_ref": Ref(result, "Artifact"), "acceptance": Ref(acceptance, "AcceptanceReceipt"), "side_effect": "sealed local fixture artifact only", "computation_log": Ref(computationLog, "Artifact"), "host_computation_passed": true, "model_provider_revision": nil})
}
