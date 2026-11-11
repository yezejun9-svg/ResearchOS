package domain

import (
	"context"
	"researchos.local/research-os/internal/store"
	"testing"
	"time"
)

func TestW12ProgressAndLimits(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	resourceHTTP(f)
	qualifiedRun, qualifiedArtifact, qualifiedReceipt := retentionAccept(o, "persistent-candidate", []byte(`{"result":"verified"}`))
	task := o.task("persistent-candidate", Empty(), Empty())
	original := task
	statuses := Empty()
	var last *runtimeFixture
	policy := f.expect(200, "GET", f.path("/run-policy"), "", "", nil)
	if policy["max_concurrency"] != float64(2) || policy["max_queue"] != float64(100) || policy["same_failure_retry_limit"] != float64(2) || policy["no_progress_iteration_limit"] != float64(3) {
		t.Fatal("defaults changed")
	}
	var index int
	var name, dbPath string
	f.db.QueryRow("PRAGMA database_list").Scan(&index, &name, &dbPath)
	for i := 0; i < 3; i++ {
		last = o.claim(task)
		obs := last.observation("FAILED", false)
		obs["artifacts"] = Empty()
		last.observe(obs)
		last.call("/report", last.report(Empty(), 0), 200)
		f.token = o.owner
		task = f.read("tasks", Str(task, "id"))
		statuses = append(statuses, task["status"])
		if i < 2 {
			resourceSnapshot(f, "iteration-before-session-end-"+string(rune('1'+i))+".json")
			if e := f.db.Close(); e != nil {
				t.Fatal(e)
			}
			var e error
			f.db, e = store.Open(dbPath)
			if e != nil {
				t.Fatal(e)
			}
			f.s, e = New(f.db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
			if e != nil {
				t.Fatal(e)
			}
			f.h = f.s.Handler()
			resourceHTTP(f)
			o.owner, e = f.s.IssueCredential(context.Background(), f.owner, 15*time.Minute)
			if e != nil {
				t.Fatal(e)
			}
			f.token = o.owner
			task = f.expect(200, "POST", f.path("/tasks/"+Str(task, "id")+"/actions"), ID(), testTag(task), Object{"action": "RESUME", "reason": "new host session retains same bounded attempt history"})
		}
	}
	t.Cleanup(func() { f.db.Close() })
	n := f.read("no-progress-records", Str(task, "no_progress_record_id"))
	code, _, _ := f.request("POST", f.path("/tasks/"+Str(task, "id")+"/actions"), ID(), testTag(task), Object{"action": "RESUME", "reason": "fourth automatic attempt must stop"})
	resourcesAssert(t, "C16-01", []any{[]any{"FAILED", "FAILED", "DEFERRED_NO_PROGRESS"}, 409}, []any{statuses, code}, n)
	var retainedBytes []byte
	if e := f.db.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", f.project, qualifiedArtifact["storage_key"]).Scan(&retainedBytes); e != nil {
		t.Fatal(e)
	}
	tx, e := f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	qualifiedTask, e := load(tx, f.project, "Task", Str(qualifiedRun.task, "id"))
	if e == nil {
		e = f.s.acceptedTaskBinding(tx, f.project, qualifiedTask)
	}
	tx.Rollback()
	if e != nil {
		t.Fatal(e)
	}
	visible := f.expect(200, "GET", f.path("/artifacts/"+Str(qualifiedArtifact, "id")+"/content"), "", "", nil)
	resourcesAssert(t, "C16-02", []any{3, 3, "DEFERRED_NO_PROGRESS", nil, Ref(qualifiedArtifact, "Artifact"), qualifiedArtifact["content_hash"], true, "verified"}, []any{n["same_failure_count"], n["no_progress_iterations"], n["status"], task["acceptance_id"], n["best_accepted_artifact_ref"], Digest(retainedBytes), len(Arr(n, "resume_conditions")) > 0, visible["result"]}, Object{"progress": n, "deferred_task": task, "retained_accepted_task": qualifiedTask, "independent_receipt": qualifiedReceipt, "retained_bytes_hash": Digest(retainedBytes), "retained_bytes_size": len(retainedBytes)})
	child := f.expect(201, "POST", f.path("/goals"), ID(), f.stateTag(), Object{"title": "child attempt of persistent origin", "original_intent": "same candidate cannot reset accounting", "scope": "PROJECT", "requirement_refs": []any{Ref(o.req, "Requirement")}, "problem_ids": []any{"orchestration-problem"}, "deliverables": []any{"verified JSON"}, "acceptance_contract": orchestrationContract()})
	child = f.expect(200, "POST", f.path("/goals/"+Str(child, "id")+"/actions"), ID(), testTag(child), Object{"action": "ACTIVATE", "reason": "child scope test"})
	b := Object{}
	for _, k := range []string{"task_type", "stage", "dependency_task_ids", "requirement_refs", "input_refs", "acceptance_contract", "stop_policy"} {
		b[k] = original[k]
	}
	Merge(b, Object{"goal_id": child["id"], "title": "same inputs new session", "origin_problem_id": n["origin_problem_id"], "candidate_id": n["candidate_id"]})
	next := f.expect(201, "POST", f.path("/tasks"), ID(), testTag(child), b)
	f.bundle(next)
	next = f.read("tasks", Str(next, "id"))
	code, _, _ = f.request("POST", f.path("/tasks/"+Str(next, "id")+"/actions"), ID(), testTag(next), Object{"action": "SUBMIT", "reason": "child cannot reset"})
	newEvidence := f.artifact(Object{"experiment": "new independently inspectable input", "revision": 2}, Empty())
	f.token = o.owner
	resume := Object{"run_id": last.run["id"], "failure_signature": nil, "new_evidence_refs": []any{Ref(newEvidence, "Artifact")}, "metric_results": Empty(), "resume_reason": "new versioned evidence changes inputs; original failures remain"}
	n = f.expect(200, "POST", f.path("/no-progress-records/"+Str(n, "id")+"/advance"), ID(), testTag(n), resume)
	b["input_refs"] = []any{Ref(newEvidence, "Artifact")}
	b["title"] = "changed evidence candidate"
	child = f.read("goals", Str(child, "id"))
	changed := f.expect(201, "POST", f.path("/tasks"), ID(), testTag(child), b)
	f.bundle(changed)
	changed = f.read("tasks", Str(changed, "id"))
	changed = f.expect(200, "POST", f.path("/tasks/"+Str(changed, "id")+"/actions"), ID(), testTag(changed), Object{"action": "SUBMIT", "reason": "explicit new input version"})
	var reasons int
	f.db.QueryRow("SELECT count(*) FROM resource_progress_resumes WHERE record=?", n["id"]).Scan(&reasons)
	resourcesAssert(t, "C16-03", []any{true, 409, 3, true, 1, "READY"}, []any{next["no_progress_record_id"] == n["id"], code, n["no_progress_iterations"], changed["no_progress_record_id"] != n["id"], reasons, changed["status"]}, Object{"old": n, "child_same": next, "new_inputs": changed, "explicit_resume": resume})
	childProgress := f.read("no-progress-records", Str(next, "no_progress_record_id"))
	resourcesAssert(t, "W12-RETENTION-CHILD-KEY", Ref(qualifiedArtifact, "Artifact"), childProgress["best_accepted_artifact_ref"], Object{"child_task": next, "inherited_record": childProgress, "original_receipt_hash": qualifiedReceipt["receipt_hash"]})
	resourceSnapshot(f, "after-progress.json")
}

func TestW12ConcurrencyAndQueue(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	resourceHTTP(f)
	first := o.claim(o.task("slot-one", Empty(), Empty()))
	second := o.claim(o.task("slot-two", Empty(), Empty()))
	f.token = o.owner
	queued := o.task("slot-three", Empty(), Empty())
	executor := ID()
	if e := f.s.ProvisionPrincipal(context.Background(), Principal{ID: executor, Roles: []string{"EXECUTOR"}}); e != nil {
		t.Fatal(e)
	}
	code, reply, _ := f.request("POST", f.path("/tasks/"+Str(queued, "id")+"/claim"), ID(), testTag(queued), Object{"runtime_id": o.rt["id"], "executor_principal_id": executor, "context_bundle_id": queued["context_bundle_id"]})
	if code != 409 {
		t.Fatal(code, reply)
	}
	// Exact initial queue capacity: 100 submitted pending tasks, plus two active.
	for i := 1; i < 100; i++ {
		o.task("pending-"+ID(), Empty(), Empty())
	}
	goal := f.read("goals", Str(o.goal, "id"))
	body := Object{"goal_id": goal["id"], "title": "queue overflow preserves input", "task_type": "json-verification", "stage": "verification", "dependency_task_ids": Empty(), "requirement_refs": []any{Ref(o.req, "Requirement")}, "input_refs": Empty(), "acceptance_contract": orchestrationContract(), "origin_problem_id": "orchestration-problem", "candidate_id": "overflow", "stop_policy": Object{"wall_time_seconds": 60, "max_attempts": 3, "max_parallel_runs": 1, "stop_conditions": []any{"no progress"}}}
	overflow := f.expect(201, "POST", f.path("/tasks"), ID(), testTag(goal), body)
	f.bundle(overflow)
	overflow = f.read("tasks", Str(overflow, "id"))
	full, _, _ := f.request("POST", f.path("/tasks/"+Str(overflow, "id")+"/actions"), ID(), testTag(overflow), Object{"action": "SUBMIT", "reason": "queue boundary"})
	var count int
	f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='Task' AND json_extract(body,'$.status')='READY'").Scan(&count)
	resourcesAssert(t, "C13-03", []any{409, 409, 100, "DRAFT"}, []any{code, full, count, f.read("tasks", Str(overflow, "id"))["status"]}, Object{"active_runs": []any{first.run["id"], second.run["id"]}, "run_policy": f.expect(200, "GET", f.path("/run-policy"), "", "", nil), "retry_and_no_progress": "C16 exact persisted checks"})
}
