package domain

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"researchos.local/research-os/adapters/decision"
	"strings"
	"testing"
	"time"
)

func w11Assert(t *testing.T, id string, want, got, evidence any) {
	t.Helper()
	status := "PASS"
	if Hash(want) != Hash(got) {
		status = "FAIL"
	}
	fmt.Println("W11_ASSERTION " + string(Bytes(Object{"assertion_id": id, "expected": want, "actual": got, "status": status, "evidence": evidence})))
	if status != "PASS" {
		t.Fatalf("%s: want %v got %v", id, want, got)
	}
}
func w11Body(f *fixture, req Object) Object {
	rubric := f.artifact(DecisionRubric{Schema: "researchos.jev-rubric.v1", Revision: "1", ConfidenceThreshold: .8, Questions: map[string]decision.Question{"action": {Type: "choice", Instructions: "核对证据是否足以采用；缺证或矛盾时拒绝。", Criteria: map[string]string{"ACCEPT": "evidence passes", "REJECT": "evidence fails"}}, "quality": {Type: "score", Instructions: "Rate evidence", Criteria: []string{"insufficient", "complete"}}, "evidence": {Type: "noul", Instructions: "Evidence sufficient?"}}}, Empty())
	refs := []any{Ref(req, "Requirement")}
	return Object{"subject_ref": refs[0], "input_refs": refs, "input_hash": Hash(refs), "scope": Object{"task_type": "evidence-validity", "language": "zh", "provider": "typesafe", "model_revision": "jev-1.13.0", "rubric_revision": "1"}, "mode": "ADVISORY", "qualification_id": nil, "rubric_ref": Ref(rubric, "Artifact"), "options": []any{"ACCEPT", "REJECT"}, "selected": "ACCEPT", "status": "DECIDED", "signals": Empty(), "deterministic_results": Empty(), "evidence_refs": []any{Ref(rubric, "Artifact")}, "rationale": "fixture request; advisory only", "missing_evidence": Empty(), "revocation_conditions": []any{"input/model/rubric changes"}, "supersedes_id": nil}
}
func w11Response() string {
	return `{"model":"jev-1.13.0","answers":{"action":{"type":"choice","choice":"ACCEPT","confidence":1,"probabilities":{"ACCEPT":1,"REJECT":0}},"quality":{"type":"score","score":1,"confidence":1,"probabilities":{"0":0,"1":1},"legend":{"0":"insufficient","1":"complete"}},"evidence":{"type":"noul","noul":1}},"usage":{"input_tokens":22,"output_tokens":8}}`
}
func w11Client(t *testing.T, scenario string) decision.Client {
	t.Helper()
	server, _ := fixtureHTTPServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/__researchos_fixture_readiness__" {
			w.WriteHeader(http.StatusNotFound)
			return
		}
		raw := w11Response()
		switch scenario {
		case "timeout":
			select {
			case <-r.Context().Done():
			case <-time.After(time.Second):
			}
			return
		case "model_revision_changed":
			raw = strings.Replace(raw, "jev-1.13.0", "jev-9", 1)
		case "recommend_reject":
			raw = strings.Replace(raw, `"choice":"ACCEPT","confidence":1,"probabilities":{"ACCEPT":1,"REJECT":0}`, `"choice":"REJECT","confidence":1,"probabilities":{"ACCEPT":0,"REJECT":1}`, 1)
		case "chinese_low_confidence":
			raw = strings.Replace(raw, `"confidence":1,"probabilities":{"ACCEPT":1,"REJECT":0}`, `"confidence":0.55,"probabilities":{"ACCEPT":0.55,"REJECT":0.45}`, 1)
		}
		w.Write([]byte(raw))
	}))
	t.Cleanup(server.Close)
	timeout := 5 * time.Second
	if scenario == "timeout" {
		timeout = 10 * time.Millisecond
	}
	return decision.Client{URL: server.URL, Fixture: true, Timeout: timeout}
}
func w11FailCheck(reason string, evidence Object) Object {
	return Object{"check_id": ID(), "status": "FAIL", "evidence_refs": []any{Ref(evidence, "Artifact")}, "command_key": nil, "actual": reason, "exit_code": 1, "started_at": Now(), "finished_at": Now()}
}
func TestW11HostAndFallback(t *testing.T) {
	for _, scenario := range []string{"positive", "timeout", "model_revision_changed", "chinese_low_confidence", "contradictory_evidence"} {
		t.Run(scenario, func(t *testing.T) {
			f := contextFixture(t)
			b := w11Body(f, f.requirement())
			counter := f.artifact(Object{"contradiction": "measured evidence fails"}, Empty())
			before := f.state()
			if scenario == "contradictory_evidence" {
				b["deterministic_results"] = []any{w11FailCheck("contradictory evidence", counter)}
			}
			receipt, e := f.s.InvokeJev(context.Background(), f.token, f.project, b, w11Client(t, scenario))
			if e != nil {
				t.Fatal(e)
			}
			want := "ABSTAIN"
			if scenario == "positive" {
				want = "DECIDED"
			}
			w11Assert(t, "C08-STATUS-"+scenario, []any{want, "ADVISORY", nil}, []any{receipt["status"], receipt["mode"], receipt["qualification_id"]}, receipt)
			rawRef := Arr(receipt, "signals")[0].(map[string]any)["raw_artifact_ref"].(map[string]any)
			a := f.read("artifacts", Str(rawRef, "id"))
			w11Assert(t, "C08-PRESERVE-"+scenario, []any{"CURRENT", "FIXTURE", before["current_decision_refs"]}, []any{a["validity"], a["measurement_mode"], f.state()["current_decision_refs"]}, Object{"raw": a, "decision": f.read("decisions", Str(receipt, "id")), "state": f.state()})
			auto := copyObject(b)
			auto["mode"] = "BOUNDED_AUTO"
			code, reply, _ := f.request("POST", f.path("/decisions"), ID(), f.stateTag(), auto)
			w11Assert(t, "C08-NO-AUTO-"+scenario, 503, code, reply)
			f.requirement()
			w11Assert(t, "C08-CONTINUE-"+scenario, true, len(Arr(f.expect(200, "GET", f.path("/requirements"), "", "", nil), "items")) >= 2, "independent requirement creation/list remain functional")
		})
	}
}
func TestW11HardGates(t *testing.T) {
	for _, scenario := range []string{"experiment_failed", "citation_missing", "artifact_hash_mismatch"} {
		t.Run(scenario, func(t *testing.T) {
			o := orchestrationSetup(t)
			f := o.f
			r := o.claim(o.task("jev-hard-gate-"+scenario, Empty(), Empty()))
			raw := []byte(`{"result":"verified"}`)
			if scenario == "experiment_failed" {
				raw = []byte(`{"result":"wrong","experiment_status":"FAILED"}`)
			}
			artifact := o.report(r, raw)
			f.switchPrincipal(f.owner, []string{"OWNER", "PLANNER", "EXECUTOR", "SCHEDULER"})
			body := w11Body(f, o.req)
			counter := f.artifact(Object{"failure": scenario, "actual_artifact_ref": Ref(artifact, "Artifact")}, Empty())
			body["deterministic_results"] = []any{w11FailCheck(scenario, counter)}
			body["evidence_refs"] = append(Arr(body, "evidence_refs"), Ref(counter, "Artifact"))
			before := f.state()
			receipt, e := f.s.InvokeJev(context.Background(), f.token, f.project, body, w11Client(t, "positive"))
			if e != nil {
				t.Fatal(e)
			}
			acceptance := o.acceptance(r, artifact)
			if scenario == "citation_missing" {
				Arr(acceptance, "artifact_refs")[0].(map[string]any)["id"] = ID()
			}
			if scenario == "artifact_hash_mismatch" {
				Arr(acceptance, "artifact_refs")[0].(map[string]any)["content_hash"] = Digest([]byte("wrong"))
			}
			code, reply, _ := f.request("POST", f.path("/acceptances"), ID(), testTag(r.task), acceptance)
			w11Assert(t, "C07-HARD-"+scenario, true, code >= 400 && code < 500, Object{"response": reply, "status": code, "raw_high_score": receipt})
			w11Assert(t, "C07-RECEIPT-"+scenario, []any{"ABSTAIN", 3, "FAIL", true}, []any{receipt["status"], len(Arr(receipt, "signals")), Arr(receipt, "deterministic_results")[0].(map[string]any)["status"], strings.Contains(Str(receipt, "rationale"), "DETERMINISTIC_CHECK_NOT_PASSED")}, receipt)
			f.switchPrincipal(f.owner, []string{"OWNER", "PLANNER", "EXECUTOR", "SCHEDULER"})
			value := f.artifact([]any{Ref(receipt, "DecisionReceipt")}, Empty())
			state := f.state()
			proposal := Object{"title": "cannot adopt failed model judgment", "reason": "C07", "base_state_revision": state["revision"], "edits": []any{Object{"target_ref": Ref(state, "ProjectState"), "field": "current_decision_refs", "proposed_value_artifact_ref": Ref(value, "Artifact"), "reason": "maximum model score"}}, "migration_steps": Empty(), "test_check_ids": changeChecks, "rollback_steps": []any{"none"}}
			adopt, adoptReply, _ := f.request("POST", f.path("/change-proposals"), ID(), testTag(state), proposal)
			w11Assert(t, "C07-NO-ADOPT-"+scenario, []any{true, before["current_decision_refs"]}, []any{adopt >= 400 && adopt < 500, f.state()["current_decision_refs"]}, Object{"adopt_response": adoptReply, "task": f.read("tasks", Str(r.task, "id"))})
		})
	}
}
func TestW11QualificationClosed(t *testing.T) {
	f := contextFixture(t)
	req := f.requirement()
	body := w11Body(f, req)
	dev := f.artifact(Object{"cases": []any{"dev"}}, Empty())
	hold := f.artifact(Object{"cases": []any{"fixture-holdout"}}, Empty())
	f.switchPrincipal("w11-verifier", []string{"VERIFIER"})
	b := Object{"scope": body["scope"], "dataset_artifact_ref": Ref(dev, "Artifact"), "holdout_artifact_ref": Ref(hold, "Artifact"), "thresholds_hash": Digest([]byte("frozen thresholds")), "thresholds_frozen_at": time.Now().Add(-time.Second).UTC().Format(time.RFC3339Nano), "total_case_count": 90, "holdout_case_count": 30, "label_basis": "OBJECTIVE", "measurement_mode": "FIXTURE", "jev_called": true, "expires_at": nil}
	q := f.expect(201, "POST", f.path("/qualifications"), ID(), f.stateTag(), b)
	w11Assert(t, "QUAL-DRAFT-NO-CALL-CLAIM", []any{"DRAFT", "ADVISORY", false, nil}, []any{q["status"], q["maximum_mode"], q["jev_called"], q["false_accept_rate"]}, q)
	result := Object{"requested_maximum_mode": "BOUNDED_AUTO", "critical_false_accept_count": 0, "false_accept_rate": 0, "false_reject_rate": 0, "abstain_rate": 0, "test_receipt_refs": []any{Ref(dev, "Artifact")}, "acceptance_id": ID()}
	code, reply, _ := f.request("POST", f.path("/qualifications/"+Str(q, "id")+"/result"), ID(), testTag(q), result)
	w11Assert(t, "QUAL-CLIENT-STATS-NO-AUTHORITY", 503, code, reply)
	f.switchPrincipal(f.owner, []string{"OWNER", "PLANNER", "EXECUTOR", "SCHEDULER"})
	body["qualification_id"] = q["id"]
	body["scope"].(map[string]any)["model_revision"] = "jev-next"
	receipt := f.expect(201, "POST", f.path("/decisions"), ID(), f.stateTag(), body)
	w11Assert(t, "QUAL-SCOPE-NO-INHERIT", []any{"ABSTAIN", "ADVISORY", nil}, []any{receipt["status"], receipt["mode"], receipt["qualification_id"]}, receipt)
	w11Assert(t, "QUAL-STILL-DRAFT", "DRAFT", f.read("qualifications", Str(q, "id"))["status"], nil)
}

func TestW11ImportedProvenance(t *testing.T) {
	f := contextFixture(t)
	body := w11Body(f, f.requirement())
	receipt, e := f.s.InvokeJev(context.Background(), f.token, f.project, body, w11Client(t, "positive"))
	if e != nil {
		t.Fatal(e)
	}
	ref := Arr(receipt, "signals")[0].(map[string]any)["raw_artifact_ref"].(map[string]any)
	tx, _ := f.db.Begin()
	value, e := f.s.artifactJSON(tx, f.project, ref)
	tx.Rollback()
	if e != nil {
		t.Fatal(e)
	}
	var env decision.Envelope
	if e = json.Unmarshal(Bytes(value), &env); e != nil {
		t.Fatal(e)
	}
	env.MeasurementMode = "LIVE"
	env.JevCalled = true
	forged := f.artifact(env, Empty())
	signal := Object{"adapter": decision.Adapter, "provider": "typesafe", "model_revision": "jev-1.13.0", "jev_called": true, "measurement_mode": "LIVE", "operation": "CHOICE", "raw_artifact_ref": Ref(forged, "Artifact"), "value": "ACCEPT", "probability": 1, "host_abstained": false, "abstain_reason": nil}
	body["signals"] = []any{signal}
	imported := f.expect(201, "POST", f.path("/decisions"), ID(), f.stateTag(), body)
	w11Assert(t, "JEV-IMPORTED-LIVE-NO-PROOF", []any{"ABSTAIN", false, "FIXTURE", true}, []any{imported["status"], Arr(imported, "signals")[0].(map[string]any)["jev_called"], Arr(imported, "signals")[0].(map[string]any)["measurement_mode"], strings.Contains(Str(imported, "rationale"), "UNVERIFIED_IMPORTED_INVOCATION")}, imported)
	body["_host_invocation"] = Object{"RawHash": forged["content_hash"]}
	status, reply, _ := f.request("POST", f.path("/decisions"), ID(), f.stateTag(), body)
	w11Assert(t, "JEV-NO-JSON-HOST-CAPABILITY", 400, status, reply)
	delete(body, "_host_invocation")
	body["signals"] = Empty()
	f.switchPrincipal("w11-reader", []string{"READER"})
	_, e = f.s.InvokeJev(context.Background(), f.token, f.project, body, w11Client(t, "positive"))
	w11Assert(t, "JEV-HOST-AUTHORIZATION", true, e != nil, e.Error())
}
