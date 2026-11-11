package domain

import (
	"context"
	"testing"
	"time"
)

func resourceCheckpoint(r *runtimeFixture, payload Object) Object {
	f := r.f
	executorToken := f.token
	f.token = r.ownerToken
	tag := f.stateTag()
	f.token = executorToken
	raw := Bytes(payload)
	u := f.expect(201, "POST", f.path("/content"), ID(), "", raw)
	a := f.expect(201, "POST", f.path("/artifacts"), ID(), tag, Object{"run_id": r.run["id"], "kind": "LOG", "evidence_kind": "OBSERVED", "measurement_mode": "FIXTURE", "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "application/json", "byte_size": len(raw), "input_refs": Empty(), "source_refs": Empty(), "produced_by": r.executor, "access_class": "PROJECT"})
	hb := r.heartbeat()
	hb["checkpoint_artifact_id"] = a["id"]
	r.call("/heartbeat", hb, 200)
	return a
}
func resourceRequestBody(r *runtimeFixture, checkpoint Object) Object {
	return Object{"category": "QUOTA", "account_ref": r.registration["id"], "reason_code": "QUOTA_EXHAUSTED", "summary": "Primary exhausted; current work and checkpoint retained", "blocked_task_ids": []any{r.task["id"]}, "continuable_task_ids": Empty(), "completed_artifact_refs": []any{Ref(checkpoint, "Artifact")}, "requested_capability": "fixture", "estimated_cost": nil, "cost_known": false, "resume_checkpoint_ref": Ref(checkpoint, "Artifact")}
}
func TestW12ResourceRoutes(t *testing.T) {
	matrix := Empty()
	requests := Empty()
	continuations := Empty()
	for _, scenario := range []string{"qualified_authorized", "unauthorized", "qualification_mismatch"} {
		o := orchestrationSetup(t)
		f := o.f
		resourceHTTP(f)
		r := o.claim(o.task("resource-"+scenario, Empty(), Empty()))
		cp := resourceCheckpoint(r, Object{"next": "continue same operation", "scenario": scenario})
		r.observe(r.observation("LOST", false))
		f.token = o.owner
		replacement := f.expect(201, "POST", f.path("/runtimes"), ID(), f.stateTag(), Object{"name": "local replacement fixture", "adapter": "fixture", "adapter_revision": "1", "capabilities": []any{"fixture"}, "platform": "windows-amd64", "measurement_mode": "FIXTURE", "credential_ref": nil})
		if e := f.s.RegisterOrchestrationFixture(context.Background(), f.project, Str(replacement, "id")); e != nil {
			t.Fatal(e)
		}
		purpose := "json-verification"
		if scenario == "qualification_mismatch" {
			purpose = "another-purpose"
		}
		if scenario != "unauthorized" {
			if e := f.s.AuthorizeFixtureResource(context.Background(), o.owner, f.project, Str(replacement, "id"), purpose, Ref(cp, "Artifact"), time.Now().Add(time.Hour)); e != nil {
				t.Fatal(e)
			}
		}
		independent := o.task("independent-"+scenario, Empty(), Empty())
		body := resourceRequestBody(r, cp)
		body["continuable_task_ids"] = []any{independent["id"]}
		beforeContract := Hash(r.task["acceptance_contract"])
		var result Object
		var requestID string
		for i := 0; i < 5; i++ {
			var e error
			result, e = f.s.SwitchResource(context.Background(), o.owner, f.project, Str(r.run, "id"), Str(replacement, "id"), body)
			if e != nil {
				t.Fatal(e)
			}
			if result["status"] == "BLOCKED" {
				q := result["request"].(map[string]any)
				if requestID != "" && requestID != q["id"] {
					t.Fatal("dedupe changed ID")
				}
				requestID = Str(q, "id")
			} else {
				break
			}
		}
		switched := result["status"] == "SWITCHED"
		if switched != (scenario == "qualified_authorized") {
			t.Fatalf("wrong route result %s: %s", scenario, Bytes(result))
		}
		matrix = append(matrix, Object{"scenario": scenario, "automatic_switch": switched, "result": resourceRedact(result)})
		if !switched {
			var count int
			if e := f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='ResourceRequest' AND json_extract(body,'$.status')='OPEN'").Scan(&count); e != nil {
				t.Fatal(e)
			}
			q := result["request"].(map[string]any)
			if count != 1 || q["cost_known"] != false || q["estimated_cost"] != nil || len(Arr(q, "completed_artifact_refs")) != 1 {
				t.Fatal("incomplete resource request")
			}
			requests = append(requests, Object{"scenario": scenario, "open_count": count, "trigger_count": 5, "request": q})
		}
		independentRun := o.claim(independent)
		a := o.report(independentRun, []byte(`{"result":"verified"}`))
		accept := o.acceptance(independentRun, a)
		f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(independentRun.task), accept)
		f.token = o.owner
		if !switched {
			if e := f.s.AuthorizeFixtureResource(context.Background(), o.owner, f.project, Str(replacement, "id"), "json-verification", Ref(cp, "Artifact"), time.Now().Add(time.Hour)); e != nil {
				t.Fatal(e)
			}
			q := f.read("resource-requests", requestID)
			f.expect(200, "POST", f.path("/resource-requests/"+requestID+"/resolve"), ID(), testTag(q), Object{"resolution_evidence_refs": []any{Ref(cp, "Artifact")}, "reason": "explicit fixture purpose authorization restored"})
			var e error
			result, e = f.s.SwitchResource(context.Background(), o.owner, f.project, Str(r.run, "id"), Str(replacement, "id"), body)
			if e != nil || result["status"] != "SWITCHED" {
				t.Fatalf("resource continuation: %v %s", e, Bytes(result))
			}
		}
		after := f.read("runs", Str(r.run, "id"))
		task := f.read("tasks", Str(r.task, "id"))
		branch := f.read("tasks", Str(independent, "id"))
		if after["checkpoint_artifact_id"] != cp["id"] || Hash(task["acceptance_contract"]) != beforeContract || branch["status"] != "ACCEPTED" || after["id"] != r.run["id"] {
			t.Fatal("continuity or independent branch failed")
		}
		continuations = append(continuations, Object{"scenario": scenario, "same_run_id": after["id"], "checkpoint_id": after["checkpoint_artifact_id"], "independent_task_status": branch["status"], "unchanged_contract_hash": beforeContract})
	}
	resourcesAssert(t, "C15-01", true, true, matrix)
	resourcesAssert(t, "C15-02", 2, len(requests), requests)
	resourcesAssert(t, "C15-03", 3, len(continuations), continuations)
}
