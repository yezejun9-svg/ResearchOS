package domain

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sync"
	"testing"
	"time"
)

func contextFixture(t *testing.T) *fixture {
	return contextFixtureFrom(setup(t))
}

func contextFixtureFrom(f *fixture) *fixture {
	f.createProject()
	f.owner = "fixture-author"
	f.switchPrincipal(f.owner, []string{"OWNER", "PLANNER", "EXECUTOR", "SCHEDULER"})
	return f
}
func (f *fixture) switchPrincipal(id string, roles []string) {
	f.t.Helper()
	var exists int
	f.db.QueryRow("SELECT count(*) FROM auth_principals WHERE id=?", id).Scan(&exists)
	if exists == 0 {
		if e := f.s.ProvisionPrincipal(context.Background(), Principal{ID: id, Roles: roles, CanCreateProject: id == f.owner, Grants: []Grant{{ProjectID: f.project}}}); e != nil {
			f.t.Fatal(e)
		}
	}
	token, e := f.s.IssueCredential(context.Background(), id, time.Minute)
	if e != nil {
		f.t.Fatal(e)
	}
	f.token = token
}
func (f *fixture) read(kind, id string) Object {
	return f.expect(200, "GET", f.path("/"+kind+"/"+id), "", "", nil)
}
func (f *fixture) state() Object { return f.expect(200, "GET", f.path("/state"), "", "", nil) }
func (f *fixture) artifact(value any, refs []any) Object {
	f.t.Helper()
	raw := Bytes(value)
	u := f.expect(201, "POST", f.path("/content"), ID(), "", raw)
	return f.expect(201, "POST", f.path("/artifacts"), ID(), f.stateTag(), Object{"run_id": nil, "kind": "REPORT", "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE", "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "application/json", "byte_size": len(raw), "input_refs": refs, "source_refs": Empty(), "produced_by": f.owner, "access_class": "PROJECT"})
}
func (f *fixture) decision(subject, rubric Object, prior any, selected string) Object {
	refs := []any{Ref(subject, "Requirement")}
	return f.expect(201, "POST", f.path("/decisions"), ID(), f.stateTag(), Object{"subject_ref": refs[0], "input_refs": refs, "input_hash": Hash(refs), "scope": Object{"task_type": "fixture", "language": "en", "provider": "deterministic-fixture", "model_revision": "none", "rubric_revision": "1"}, "mode": "ADVISORY", "qualification_id": nil, "rubric_ref": Ref(rubric, "Artifact"), "options": []any{"A", "B"}, "selected": selected, "status": "DECIDED", "signals": Empty(), "deterministic_results": Empty(), "evidence_refs": []any{Ref(rubric, "Artifact")}, "rationale": "explicit deterministic fixture decision", "missing_evidence": Empty(), "revocation_conditions": []any{"input changes"}, "supersedes_id": prior})
}
func (f *fixture) proposal(decisions []any, inputs ...any) Object {
	refs := inputs
	if refs == nil {
		refs = Empty()
	}
	a := f.artifact(decisions, refs)
	state := f.state()
	return f.expect(201, "POST", f.path("/change-proposals"), ID(), testTag(state), Object{"title": "adopt explicit decision lineage", "reason": "fixture change", "base_state_revision": state["revision"], "edits": []any{Object{"target_ref": Ref(state, "ProjectState"), "field": "current_decision_refs", "proposed_value_artifact_ref": Ref(a, "Artifact"), "reason": "replace by checked successor"}}, "migration_steps": Empty(), "test_check_ids": changeChecks, "rollback_steps": []any{"submit a new independently accepted reversal"}})
}
func (f *fixture) accept(proposal Object) Object {
	f.t.Helper()
	frozen, e := f.s.ChangeContractHash(context.Background(), f.project, Str(proposal, "id"))
	if e != nil {
		f.t.Fatal(e)
	}
	f.switchPrincipal("fixture-independent-verifier", []string{"VERIFIER"})
	b := Object{"subject_ref": Ref(proposal, "ChangeProposal"), "run_id": nil, "contract_hash": frozen, "input_refs": []any{Ref(proposal, "ChangeProposal")}, "artifact_refs": Empty(), "checks": []any{Object{"check_id": "client-not-authoritative", "status": "NOT_RUN", "evidence_refs": Empty(), "command_key": nil, "actual": "server must recompute", "exit_code": nil, "started_at": nil, "finished_at": nil}}, "verdict": "BLOCKED", "executor_principal_ids": Empty(), "independence_basis": "DETERMINISTIC_SERVICE", "blocking_conflict_ids": Empty(), "qualification_ids": Empty(), "policy_revision": 1, "measurement_mode": "FIXTURE", "reason": "request server independent verification"}
	receipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(proposal), b)
	f.switchPrincipal(f.owner, []string{"OWNER", "PLANNER", "EXECUTOR", "SCHEDULER"})
	return receipt
}
func (f *fixture) apply(p Object) Object {
	r := f.accept(p)
	return f.expect(200, "POST", f.path("/change-proposals/"+Str(p, "id")+"/apply"), ID(), testTag(p), Object{"acceptance_id": r["id"], "expected_project_state_revision": f.state()["revision"]})
}
func (f *fixture) task(req Object, inputs []any, title string) Object {
	contract := Object{"contract_hash": Digest([]byte(title)), "contract_revision": 1, "checks": []any{Object{"check_id": "fixture-check", "kind": "DETERMINISTIC", "required": true, "expected": "actual artifact", "command_key": "test.context", "rubric_ref": nil, "qualification_id": nil, "not_applicable_reason": nil}}, "require_independent_verifier": true, "version_policy": "EXACT", "frozen_at": Now()}
	goal := f.expect(201, "POST", f.path("/goals"), ID(), f.stateTag(), Object{"title": title, "original_intent": "fixture intent", "scope": "PROJECT", "requirement_refs": []any{Ref(req, "Requirement")}, "problem_ids": []any{"fixture-problem"}, "deliverables": []any{"report"}, "acceptance_contract": contract})
	return f.expect(201, "POST", f.path("/tasks"), ID(), testTag(goal), Object{"goal_id": goal["id"], "title": title, "task_type": title, "stage": "verification", "dependency_task_ids": Empty(), "requirement_refs": []any{Ref(req, "Requirement")}, "input_refs": inputs, "acceptance_contract": contract, "origin_problem_id": "fixture-problem", "candidate_id": title, "stop_policy": Object{"wall_time_seconds": 60, "max_attempts": 3, "max_parallel_runs": 1, "stop_conditions": []any{"no progress"}}})
}
func (f *fixture) bundle(task Object) Object {
	state := f.state()
	return f.expect(201, "POST", f.path("/context-bundles"), ID(), testTag(state), Object{"task_id": task["id"], "expected_project_state_revision": state["revision"]})
}
func (f *fixture) link(from, to Object) {
	f.expect(201, "POST", f.path("/impact-links"), ID(), f.stateTag(), Object{"from_ref": from, "to_ref": to, "relation": "DEPENDS_ON", "basis": "DETERMINISTIC", "evidence_refs": Empty()})
}
func assertion(t *testing.T, id string, expected, actual, evidence any) {
	t.Helper()
	status := "PASS"
	if Hash(expected) != Hash(actual) {
		status = "FAIL"
	}
	b, _ := json.Marshal(Object{"assertion_id": id, "status": status, "expected": expected, "actual": actual, "evidence": evidence})
	fmt.Println("W04_ASSERTION " + string(b))
	if status != "PASS" {
		t.Fatalf("assertion %s mismatch: %s", id, b)
	}
}
func TestW04C03(t *testing.T) {
	runW04C03(t, contextFixture(t))
}

func runW04C03(t *testing.T, f *fixture) {
	req := f.requirement()
	rubric := f.artifact(Object{"rubric": "deterministic fixture"}, Empty())
	d1 := f.decision(req, rubric, nil, "A")
	f.apply(f.proposal([]any{Ref(d1, "DecisionReceipt")}))
	t1 := f.task(req, []any{Ref(d1, "DecisionReceipt")}, "affected-task")
	t2 := f.task(req, Empty(), "unrelated-task")
	f.bundle(t1)
	b2 := f.bundle(t2)
	t1 = f.read("tasks", Str(t1, "id"))
	t2 = f.read("tasks", Str(t2, "id"))
	a1 := f.artifact(Object{"result": "old result"}, []any{Ref(d1, "DecisionReceipt")})
	f.link(Ref(t1, "Task"), Ref(d1, "DecisionReceipt"))
	f.link(Ref(a1, "Artifact"), Ref(d1, "DecisionReceipt"))
	oldTag := testTag(t1)
	d2 := f.decision(req, rubric, d1["id"], "B")
	proposal := f.proposal([]any{Ref(d2, "DecisionReceipt")})
	applied := f.apply(proposal)
	newT1 := f.read("tasks", Str(t1, "id"))
	newA1 := f.read("artifacts", Str(a1, "id"))
	newT2 := f.read("tasks", Str(t2, "id"))
	impacted := map[string]bool{}
	for _, raw := range Arr(proposal, "impacted_refs") {
		ref := raw.(map[string]any)
		impacted[Str(ref, "entity_type")+":"+Str(ref, "id")] = true
	}
	if len(impacted) != 2 || !impacted["Task:"+Str(t1, "id")] || !impacted["Artifact:"+Str(a1, "id")] {
		t.Fatal("impact set differs from exactly T1 and A1", proposal["impacted_refs"])
	}
	assertion(t, "C03-01", []any{"NEEDS_REVALIDATION", "STALE", 2}, []any{newT1["status"], newA1["validity"], len(Arr(proposal, "impacted_refs"))}, Object{"proposal": applied, "D1": Ref(d1, "DecisionReceipt"), "D2": Ref(d2, "DecisionReceipt"), "logical_generation": 2, "impact_links": f.expect(200, "GET", f.path("/impact-links"), "", "", nil), "events": f.expect(200, "GET", f.path("/events"), "", "", nil)})
	msg := Object{"task_id": t2["id"], "run_id": nil, "correlation_id": ID(), "recipient_id": f.owner, "message_type": "EVIDENCE_READY", "body": "unrelated task continues with frozen context", "refs": []any{Ref(b2, "ContextBundle")}}
	receipt := f.expect(201, "POST", f.path("/messages"), ID(), f.stateTag(), msg)
	assertion(t, "C03-02", []any{t2["revision"], "DRAFT"}, []any{newT2["revision"], newT2["status"]}, Object{"bundle": b2, "message_receipt": receipt})
	stateNow := f.state()
	staleValue := Object{"title": "stale value cannot be reused", "reason": "negative fixture", "base_state_revision": stateNow["revision"], "edits": []any{Object{"target_ref": Ref(stateNow, "ProjectState"), "field": "current_decision_refs", "proposed_value_artifact_ref": Ref(a1, "Artifact"), "reason": "must refuse historical CURRENT"}}, "migration_steps": Empty(), "test_check_ids": changeChecks, "rollback_steps": []any{"none"}}
	f.expect(412, "POST", f.path("/change-proposals"), ID(), testTag(stateNow), staleValue)
	oldOutput := f.artifact(Object{"result": "late old executor"}, []any{Ref(d1, "DecisionReceipt")})
	stale, staleResponse, _ := f.request("POST", f.path("/tasks/"+Str(t1, "id")+"/actions"), ID(), oldTag, Object{"action": "SUBMIT", "reason": "old executor"})
	conflict, conflictResponse, _ := f.request("POST", f.path("/tasks/"+Str(t1, "id")+"/actions"), ID(), testTag(newT1), Object{"action": "SUBMIT", "reason": "old executor"})
	assertion(t, "C03-03", []any{"STALE", 412, 409}, []any{oldOutput["validity"], stale, conflict}, Object{"historical_output": oldOutput, "stale_rejection": staleResponse, "conflict_rejection": conflictResponse})
}
func TestW04C04(t *testing.T) {
	runW04C04(t, contextFixture(t))
}

func runW04C04(t *testing.T, f *fixture) {
	req := f.requirement()
	rubric := f.artifact(Object{"rubric": "explicit integration"}, Empty())
	d1 := f.decision(req, rubric, nil, "A")
	f.apply(f.proposal([]any{Ref(d1, "DecisionReceipt")}))
	body := copyObject(d1)
	for _, k := range []string{"id", "revision", "project_id", "receipt_hash", "created_at", "recorded_by"} {
		delete(body, k)
	}
	body["supersedes_id"] = d1["id"]
	tag := f.stateTag()
	key := ID()
	firstToken := f.token
	f.switchPrincipal("concurrent-second-planner", []string{"PLANNER"})
	second := *f
	f.token = firstToken
	var results [2]Object
	var statuses [2]int
	var wg sync.WaitGroup
	for i := 0; i < 2; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			b := copyObject(body)
			b["selected"] = []string{"A", "B"}[i]
			k := key
			if i == 1 {
				k = ID()
			}
			caller := f
			if i == 1 {
				caller = &second
			}
			statuses[i], results[i], _ = caller.request("POST", f.path("/decisions"), k, tag, b)
		}(i)
	}
	wg.Wait()
	winner, loser := 0, 1
	if statuses[0] != 201 {
		winner, loser = 1, 0
	}
	if statuses[winner] != 201 || statuses[loser] != 412 {
		t.Fatal(statuses, results)
	}
	b := copyObject(body)
	b["selected"] = []string{"A", "B"}[loser]
	other := f.expect(201, "POST", f.path("/decisions"), ID(), f.stateTag(), b)
	chosen := results[winner]
	conflict := f.expect(201, "POST", f.path("/conflicts"), ID(), f.stateTag(), Object{"kind": "REVISION", "subject_refs": []any{Ref(chosen, "DecisionReceipt"), Ref(other, "DecisionReceipt")}, "description": "incompatible candidate decisions", "blocks_refs": Empty()})
	task := f.task(req, Empty(), "integration")
	f.bundle(task)
	task = f.read("tasks", Str(task, "id"))
	applied := f.apply(f.proposal([]any{Ref(chosen, "DecisionReceipt")}, Ref(task, "Task")))
	state := f.state()
	resolved := f.read("conflicts", Str(conflict, "id"))
	assertion(t, "C04-01", []any{201, 412, 1, "RESOLVED"}, []any{statuses[winner], statuses[loser], len(Arr(state, "current_decision_refs")), resolved["status"]}, Object{"integration_task": task, "applied": applied, "current_decision": state["current_decision_refs"]})
	events, e := f.s.PendingEvents(context.Background(), f.project)
	if e != nil {
		t.Fatal(e)
	}
	last := events[len(events)-1]
	wait, e := f.s.ConsumeEvent(context.Background(), "fixture-projection", f.project, Str(last, "id"))
	if e != nil {
		t.Fatal(e)
	}
	for i := len(events) - 2; i >= 0; i-- {
		if _, e = f.s.ConsumeEvent(context.Background(), "fixture-projection", f.project, Str(events[i], "id")); e != nil {
			t.Fatal(e)
		}
	}
	for i := 0; i < 3; i++ {
		if _, e = f.s.ConsumeEvent(context.Background(), "fixture-projection", f.project, Str(last, "id")); e != nil {
			t.Fatal(e)
		}
	}
	var position, count int
	f.db.QueryRow("SELECT sequence FROM consumer_positions WHERE consumer='fixture-projection' AND project=?", f.project).Scan(&position)
	f.db.QueryRow("SELECT count(*) FROM consumer_inbox WHERE consumer='fixture-projection' AND applied=1").Scan(&count)
	var projectionRaw string
	if e = f.db.QueryRow("SELECT body FROM context_projection WHERE consumer='fixture-projection' AND project=? AND kind='ProjectState'", f.project).Scan(&projectionRaw); e != nil {
		t.Fatal(e)
	}
	projection, e := Decode([]byte(projectionRaw))
	if e != nil {
		t.Fatal(e)
	}
	if Hash(projection["current_decision_refs"]) != Hash(state["current_decision_refs"]) || Hash(projection["revision"]) != Hash(state["revision"]) {
		t.Fatal("projection rolled back or omitted final state", projection, state)
	}
	assertion(t, "C04-02", []any{"WAITING_FOR_PREDECESSOR", len(events), len(events)}, []any{wait["status"], position, count}, Object{"wait": wait, "events": events, "applied_once": count})
	tag = f.stateTag()
	key = ID()
	body["selected"] = "A"
	first := f.expect(201, "POST", f.path("/decisions"), key, tag, body)
	status, replay, h := f.request("POST", f.path("/decisions"), key, tag, body)
	body["selected"] = "B"
	different, _, _ := f.request("POST", f.path("/decisions"), key, tag, body)
	assertion(t, "C04-03", []any{201, first["id"], "true", 409}, []any{status, replay["id"], h.Get("Idempotency-Replayed"), different}, replay)
}
func TestW04A01(t *testing.T) {
	f := setup(t)
	source := filepath.Join(t.TempDir(), "package")
	if e := os.CopyFS(source, os.DirFS("../../spec/v2.0")); e != nil {
		t.Fatal(e)
	}
	manifestPath := filepath.Join(source, "PACKAGE_MANIFEST.json")
	raw, e := os.ReadFile(manifestPath)
	if e != nil {
		t.Fatal(e)
	}
	pinned := Digest(raw)
	report, e := f.s.ImportSpecification(context.Background(), f.token, source, pinned, Object{"assumptions": []any{"Synthetic fixture assumption: development remains local."}})
	if e != nil {
		t.Fatal(e)
	}
	profile := report["profile"].(map[string]any)
	basis := map[string]bool{}
	for _, v := range Arr(profile, "facts") {
		basis[Str(v.(map[string]any), "basis")] = true
	}
	var foreignGrants int
	f.db.QueryRow("SELECT count(*) FROM auth_grants WHERE project<>?", report["project_id"]).Scan(&foreignGrants)
	assertion(t, "A01-01", []any{true, 4, 0, "DRAFT"}, []any{Str(profile, "id") != Str(report["goal"].(map[string]any), "id"), len(basis), foreignGrants, report["goal"].(map[string]any)["status"]}, report)
	before := databaseCounts(t, f)
	file := filepath.Join(source, "01_PRD.md")
	original, e := os.ReadFile(file)
	if e != nil {
		t.Fatal(e)
	}
	if e = os.WriteFile(file, append(original, []byte("tampered")...), 0600); e != nil {
		t.Fatal(e)
	}
	_, tamper := f.s.ImportSpecification(context.Background(), f.token, source, pinned, Object{})
	if e = os.WriteFile(file, original, 0600); e != nil {
		t.Fatal(e)
	}
	manifest, e := Decode(raw)
	if e != nil {
		t.Fatal(e)
	}
	Arr(manifest, "files")[0].(map[string]any)["path"] = "../outside.txt"
	attack := Bytes(manifest)
	if e = os.WriteFile(manifestPath, attack, 0600); e != nil {
		t.Fatal(e)
	}
	_, traversal := f.s.ImportSpecification(context.Background(), f.token, source, Digest(attack), Object{})
	if e = os.WriteFile(manifestPath, raw, 0600); e != nil {
		t.Fatal(e)
	}
	_, authority := f.s.ImportSpecification(context.Background(), f.token, source, pinned, Object{"historical_authorization": Object{"project": "quillclub_or_xiaoshuo", "read": true}})
	injectedPath := filepath.Join(source, "injected-fixture.txt")
	if e = os.WriteFile(injectedPath, []byte("not listed in manifest"), 0600); e != nil {
		t.Fatal(e)
	}
	_, injected := f.s.ImportSpecification(context.Background(), f.token, source, pinned, Object{})
	if e = os.Remove(injectedPath); e != nil {
		t.Fatal(e)
	}
	_, hashMismatch := f.s.ImportSpecification(context.Background(), f.token, source, Digest([]byte("wrong")), Object{})
	assertion(t, "A01-02", []any{true, true, true, true, true, before}, []any{tamper != nil, traversal != nil, authority != nil, hashMismatch != nil, injected != nil, databaseCounts(t, f)}, Object{"tamper": fmt.Sprint(tamper), "traversal": fmt.Sprint(traversal), "forged_authority": fmt.Sprint(authority), "manifest": fmt.Sprint(hashMismatch), "injected_fixture_file": fmt.Sprint(injected)})
	cmd := exec.Command("python", filepath.Join(source, "tools", "validate_package.py"))
	out, e := cmd.CombinedOutput()
	if e != nil {
		t.Fatalf("package validator: %v %s", e, out)
	}
	validation, e := Decode(out)
	if e != nil {
		t.Fatal(e)
	}
	assertion(t, "A01-03", []any{"PASS", "SPECIFICATION_PACKAGE_ONLY", "NOT_RUN"}, []any{validation["status"], validation["scope"], validation["product_tests"]}, validation)
	after, _ := os.ReadFile(manifestPath)
	if string(after) != string(raw) {
		t.Fatal("readonly manifest changed")
	}
}
func databaseCounts(t *testing.T, f *fixture) Object {
	t.Helper()
	o := Object{}
	for _, table := range []string{"domain_objects", "domain_versions", "domain_refs", "auth_grants", "outbox", "context_imports", "uploaded_content", "idempotency"} {
		var count int
		if e := f.db.QueryRow("SELECT count(*) FROM " + table).Scan(&count); e != nil {
			t.Fatal(e)
		}
		o[table] = count
	}
	return o
}
func TestW04CanonicalNumbers(t *testing.T) {
	runW04CanonicalNumbers(t, contextFixture(t))
}
func runW04CanonicalNumbers(t *testing.T, f *fixture) {
	req := f.requirement()
	task := f.task(req, Empty(), "numeric")
	goal := f.read("goals", Str(task, "goal_id"))
	body := Object{"goal_id": goal["id"], "title": "number-boundary", "task_type": "fixture", "stage": "verification", "dependency_task_ids": Empty(), "requirement_refs": []any{Ref(req, "Requirement")}, "input_refs": Empty(), "acceptance_contract": task["acceptance_contract"], "origin_problem_id": "fixture-problem", "candidate_id": "candidate-number", "stop_policy": Object{"wall_time_seconds": json.Number("9007199254740992"), "max_attempts": 3, "max_parallel_runs": 1, "stop_conditions": []any{"fixture"}}}
	key := ID()
	tag := testTag(goal)
	first, firstResponse, _ := f.request("POST", f.path("/tasks"), key, tag, body)
	body["stop_policy"].(map[string]any)["wall_time_seconds"] = json.Number("9007199254740993")
	second, secondResponse, h := f.request("POST", f.path("/tasks"), key, tag, body)
	valid := 0
	for _, raw := range []string{`{"n":1e3}`, `{"n":1.0}`, `{"n":0.1}`} {
		if _, e := Decode([]byte(raw)); e != nil {
			t.Fatal(e)
		}
		valid++
	}
	assertion(t, "W04-G01-NUMBERS", []any{201, 400, "", 3}, []any{first, second, h.Get("Idempotency-Replayed"), valid}, Object{"first_response": firstResponse, "second_response": secondResponse})
}
func TestW04ContextRecovery(t *testing.T) {
	runW04ContextRecovery(t, contextFixture(t), New)
}
func runW04ContextRecovery(t *testing.T, f *fixture, construct func(*sql.DB, string, string) (*Service, error)) {
	req := f.requirement()
	source := f.artifact(Object{"source": "read-only fixture evidence"}, Empty())
	task := f.task(req, []any{Ref(source, "Artifact")}, "resume-fixture")
	bundle := f.bundle(task)
	newService, e := construct(f.db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if e != nil {
		t.Fatal(e)
	}
	recovered, e := newService.GetTaskContext(context.Background(), f.token, f.project, Str(task, "id"))
	if e != nil {
		t.Fatal(e)
	}
	destination := filepath.Join(t.TempDir(), "task-context")
	t.Cleanup(func() {
		filepath.WalkDir(destination, func(path string, entry os.DirEntry, err error) error {
			if err == nil && !entry.IsDir() {
				os.Chmod(path, 0600)
			}
			return err
		})
	})
	manifest, e := newService.MaterializeTaskContext(context.Background(), f.token, f.project, Str(task, "id"), destination)
	if e != nil {
		t.Fatal(e)
	}
	raw, e := os.ReadFile(filepath.Join(destination, "inputs", Str(source, "id")+".content"))
	if e != nil {
		t.Fatal(e)
	}
	if e = os.WriteFile(filepath.Join(destination, "candidates", "result.json"), []byte(`{"candidate":true}`), 0600); e != nil {
		t.Fatal(e)
	}
	profile := f.expect(200, "GET", f.path("/profile"), "", "", nil)
	hasProfile := false
	for _, r := range Arr(bundle, "version_vector") {
		hasProfile = hasProfile || r.(map[string]any)["entity_type"] == "ProjectProfile"
	}
	assertion(t, "W04-G03-RECOVERY", []any{bundle["id"], source["content_hash"], true, "candidates"}, []any{recovered["id"], Digest(raw), hasProfile, manifest["candidate_directory"]}, Object{"bundle": bundle, "manifest": manifest})
	value := f.artifact([]any{Object{"text": "new observed fact", "basis": "OBSERVED", "source_refs": []any{Ref(source, "Artifact")}, "validity": "CURRENT"}}, Empty())
	state := f.state()
	proposal := f.expect(201, "POST", f.path("/change-proposals"), ID(), testTag(state), Object{"title": "update copied context facts", "reason": "facts changed", "base_state_revision": state["revision"], "edits": []any{Object{"target_ref": Ref(profile, "ProjectProfile"), "field": "facts", "proposed_value_artifact_ref": Ref(value, "Artifact"), "reason": "replace observed fact"}}, "migration_steps": Empty(), "test_check_ids": changeChecks, "rollback_steps": []any{"independent reversal"}})
	f.apply(proposal)
	changed := f.read("tasks", Str(task, "id"))
	_, stale := newService.GetTaskContext(context.Background(), f.token, f.project, Str(task, "id"))
	assertion(t, "W04-G03-PROFILE", []any{"NEEDS_REVALIDATION", true}, []any{changed["status"], stale != nil}, Object{"changed_task": changed, "old_bundle": bundle, "error": fmt.Sprint(stale)})
	revalidated := f.expect(200, "POST", f.path("/tasks/"+Str(task, "id")+"/actions"), ID(), testTag(changed), Object{"action": "REVALIDATE", "reason": "explicitly refresh after independently accepted new profile facts"})
	newBundle := f.bundle(revalidated)
	restored, e := newService.GetTaskContext(context.Background(), f.token, f.project, Str(task, "id"))
	if e != nil {
		t.Fatal(e)
	}
	historical := f.read("context-bundles", Str(bundle, "id"))
	assertion(t, "W04-G03-REBUILT", []any{true, "new observed fact", bundle["receipt_hash"]}, []any{restored["id"] != bundle["id"], Arr(newBundle, "facts")[0].(map[string]any)["text"], historical["receipt_hash"]}, Object{"old": Ref(bundle, "ContextBundle"), "new": Ref(newBundle, "ContextBundle")})
	if e = f.s.RevokePrincipal(context.Background(), f.owner); e != nil {
		t.Fatal(e)
	}
	_, revoked := newService.GetTaskContext(context.Background(), f.token, f.project, Str(task, "id"))
	assertion(t, "W04-G03-REVOKED", "UNAUTHENTICATED", revoked.(*Fault).Code, Object{"current_grant_checked": true})
	os.Chmod(filepath.Join(destination, "bundle.json"), 0600)
	os.Chmod(filepath.Join(destination, "manifest.json"), 0600)
	os.Chmod(filepath.Join(destination, "inputs", Str(source, "id")+".content"), 0600)
}
func TestW04RestrictedContext(t *testing.T) {
	runW04RestrictedContext(t, contextFixture(t))
}
func runW04RestrictedContext(t *testing.T, f *fixture) {
	req := f.requirement()
	p := Principal{ID: "privileged-context-owner", Roles: []string{"OWNER", "PLANNER", "EXECUTOR", "SCHEDULER"}, Grants: []Grant{{ProjectID: f.project, Restricted: true}}}
	if e := f.s.ProvisionPrincipal(context.Background(), p); e != nil {
		t.Fatal(e)
	}
	token, e := f.s.IssueCredential(context.Background(), p.ID, time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	a := Merge(Base(f.project), Object{"run_id": nil, "kind": "TEST_RESULT", "evidence_kind": "SIMULATED", "validity": "CURRENT", "measurement_mode": "FIXTURE", "content_hash": Digest(nil), "storage_key": "synthetic-no-protected-bytes", "media_type": "application/json", "byte_size": 0, "input_refs": Empty(), "source_refs": Empty(), "produced_by": p.ID, "sealed_at": Now(), "access_class": "VERIFIER_ONLY"})
	tx, e := f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	if e = f.s.put(tx, "Artifact", a); e != nil {
		t.Fatal(e)
	}
	if e = tx.Commit(); e != nil {
		t.Fatal(e)
	}
	f.token = token
	task := f.task(req, []any{Ref(a, "Artifact")}, "restricted-task")
	bundle := f.bundle(task)
	stateTag := f.stateTag()
	f.switchPrincipal("ordinary-context-planner", []string{"PLANNER", "READER"})
	f.expect(404, "GET", f.path("/context-bundles/"+Str(bundle, "id")), "", "", nil)
	list := f.expect(200, "GET", f.path("/context-bundles"), "", "", nil)
	state := f.state()
	before := databaseCounts(t, f)
	f.expect(403, "POST", f.path("/context-bundles"), ID(), stateTag, Object{"task_id": task["id"], "expected_project_state_revision": state["revision"]})
	after := databaseCounts(t, f)
	f.token = token
	positive := f.expect(200, "GET", f.path("/context-bundles/"+Str(bundle, "id")), "", "", nil)
	_, protected := f.s.MaterializeTaskContext(context.Background(), token, f.project, Str(task, "id"), filepath.Join(t.TempDir(), "blocked"))
	decision := f.decision(req, a, nil, "A")
	tx, e = f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	restrictedState, e := singleton(tx, f.project, "ProjectState")
	if e != nil {
		t.Fatal(e)
	}
	restrictedState["current_decision_refs"] = []any{Ref(decision, "DecisionReceipt")}
	if e = bump(restrictedState); e != nil {
		t.Fatal(e)
	}
	if e = f.s.put(tx, "ProjectState", restrictedState); e != nil {
		t.Fatal(e)
	}
	if e = tx.Commit(); e != nil {
		t.Fatal(e)
	}
	f.switchPrincipal("ordinary-context-planner", []string{"PLANNER", "READER"})
	f.expect(403, "GET", f.path("/state"), "", "", nil)
	f.expect(404, "GET", f.path("/decisions/"+Str(decision, "id")), "", "", nil)
	f.token = token
	f.expect(200, "GET", f.path("/state"), "", "", nil)
	assertion(t, "W04-G03-RESTRICTED", []any{0, before, bundle["id"], 503}, []any{len(Arr(list, "items")), after, positive["id"], protected.(*Fault).Status}, Object{"positive_control": Ref(bundle, "ContextBundle"), "ordinary_read": "404", "ordinary_construction": "403 rolled back", "protected_bytes": "unbound 503"})
}
