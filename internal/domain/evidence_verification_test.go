package domain

import (
	"context"
	"database/sql"
	"os"
	"path/filepath"
	"testing"
)

// The fixture proves API binding only; its simulated source is not provider truth.
func evidenceVerificationFixture(t *testing.T, status string) (*orchestrationFixture, Object, Object, Object, Object) {
	return evidenceVerificationFixtureSource(t, status, false)
}

func evidenceVerificationFixtureSource(t *testing.T, status string, observed bool) (*orchestrationFixture, Object, Object, Object, Object) {
	t.Helper()
	o := orchestrationSetup(t)
	f := o.f
	f.token = o.owner
	kind, mode, sourceKind := "SIMULATED", "FIXTURE", "SIMULATION"
	raw := []byte("synthetic source snapshot")
	claim := "fixture claim"
	if observed {
		kind, mode, sourceKind = "OBSERVED", "LIVE", "LOCAL"
		claim = "source states that 2 + 2 = 5"
		path := filepath.Join(t.TempDir(), "source.txt")
		if e := os.WriteFile(path, []byte("local source states that 2 + 2 = 4"), 0600); e != nil {
			t.Fatal(e)
		}
		var e error
		raw, e = os.ReadFile(path)
		if e != nil {
			t.Fatal(e)
		}
	}
	u := f.expect(201, "POST", f.path("/content"), ID(), "", raw)
	snapshot := f.expect(201, "POST", f.path("/artifacts"), ID(), f.stateTag(), Object{"run_id": nil, "kind": "SOURCE_SNAPSHOT", "evidence_kind": kind, "measurement_mode": mode, "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "text/plain", "byte_size": len(raw), "input_refs": Empty(), "source_refs": Empty(), "produced_by": f.owner, "access_class": "PROJECT"})
	ev := f.expect(201, "POST", f.path("/evidence"), ID(), f.stateTag(), Object{"claim": claim, "stance": "CONTEXT", "evidence_kind": kind, "source_kind": sourceKind, "canonical_url": nil, "publisher": nil, "upstream_revision": nil, "published_at": nil, "modified_at": nil, "retrieved_at": Now(), "time_status": "UNKNOWN", "snapshot_artifact_ref": Ref(snapshot, "Artifact"), "locator": "fixture", "independence_key": Hash("fixture source"), "origin_evidence_id": nil, "discovery_urls": Empty(), "license_status": "UNKNOWN", "license_expression": nil})
	judgement := Object{"type": "researchos.evidence-verification.v1", "evidence_ref": Ref(ev, "Evidence"), "snapshot_artifact_ref": Ref(snapshot, "Artifact"), "status": status, "reason": "synthetic review result"}
	c := orchestrationContract()
	c["checks"].([]any)[0].(map[string]any)["expected"] = string(Bytes(judgement))
	c["contract_hash"] = contractDigest(c)
	taskBody := Object{"goal_id": o.goal["id"], "title": "fixture evidence verification", "task_type": "evidence_verification", "stage": "verification", "dependency_task_ids": Empty(), "requirement_refs": []any{Ref(o.req, "Requirement")}, "input_refs": []any{Ref(ev, "Evidence"), Ref(snapshot, "Artifact")}, "acceptance_contract": c, "origin_problem_id": "orchestration-problem", "candidate_id": "fixture-evidence-judgement", "stop_policy": Object{"wall_time_seconds": 60, "max_attempts": 3, "max_parallel_runs": 1, "stop_conditions": []any{"no progress"}}}
	if e := f.s.Contracts.Validate("CreateTaskRequest", taskBody); e != nil {
		t.Fatal(e)
	}
	task := f.expect(201, "POST", f.path("/tasks"), ID(), testTag(o.goal), taskBody)
	f.bundle(task)
	task = f.read("tasks", Str(task, "id"))
	task = f.expect(200, "POST", f.path("/tasks/"+Str(task, "id")+"/actions"), ID(), testTag(task), Object{"action": "SUBMIT", "reason": "fixture frozen review"})
	r := o.claim(task)
	result := o.report(r, Bytes(judgement))
	b := o.acceptance(r, result)
	b["subject_ref"] = Ref(r.task, "Task")
	receipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(r.task), b)
	return o, ev, snapshot, r.run, receipt
}

func TestW07VerifyEvidenceAcceptedBinding(t *testing.T) {
	for _, status := range []string{"VERIFIED", "CONTRADICTED", "UNAVAILABLE"} {
		t.Run(status, func(t *testing.T) {
			o, ev, snapshot, run, receipt := evidenceVerificationFixture(t, status)
			f := o.f
			path := f.path("/evidence/" + Str(ev, "id") + "/verify")
			request := Object{"status": status, "verification_run_id": run["id"], "check_results": receipt["checks"]}
			bad := Merge(Object{}, request)
			bad["status"] = "VERIFIED"
			if status == "VERIFIED" {
				bad["status"] = "CONTRADICTED"
			}
			if code, _, _ := f.request("POST", path, ID(), testTag(ev), bad); code != 422 {
				t.Fatalf("mismatched status %d", code)
			}
			bad = Merge(Object{}, request)
			altered, _ := Decode(Bytes(Object{"checks": receipt["checks"]}))
			altered["checks"].([]any)[0].(map[string]any)["actual"] = "caller PASS"
			bad["check_results"] = altered["checks"]
			if code, _, _ := f.request("POST", path, ID(), testTag(ev), bad); code != 422 {
				t.Fatalf("caller checks %d", code)
			}
			bad = Merge(Object{}, request)
			bad["verification_run_id"] = ID()
			if code, _, _ := f.request("POST", path, ID(), testTag(ev), bad); code == 200 {
				t.Fatal("wrong run accepted")
			}
			if _, e := f.db.Exec("UPDATE auth_principals SET roles=? WHERE id=?", string(Bytes([]string{"OWNER", "PLANNER", "EXECUTOR", "SCHEDULER", "VERIFIER"})), f.owner); e != nil {
				t.Fatal(e)
			}
			f.switchPrincipal(o.f.owner, []string{"OWNER", "PLANNER", "EXECUTOR", "SCHEDULER"})
			if code, body, _ := f.request("POST", path, ID(), testTag(ev), request); code != 403 || body["message"] != "evidence reviewer must be independent of source and execution" {
				t.Fatalf("source self-review %d %s", code, Bytes(body))
			}
			f.switchPrincipal("orchestration-independent-verifier", []string{"VERIFIER"})
			key := ID()
			got := f.expect(200, "POST", path, key, testTag(ev), request)
			if got["verification_status"] != status || got["verified_by_run_id"] != run["id"] || got["revision"] == ev["revision"] {
				t.Fatalf("bad verified result %s", Bytes(got))
			}
			f.expect(200, "POST", path, key, testTag(ev), request)
			if code, _, _ := f.request("POST", path, ID(), testTag(got), request); code == 200 {
				t.Fatal("historical run replay accepted")
			}
			_ = snapshot
		})
	}
}

func TestW07VerifyEvidenceRejectsRevokedAcceptance(t *testing.T) {
	o, ev, _, run, receipt := evidenceVerificationFixture(t, "VERIFIED")
	f := o.f
	if e := f.s.RevokePrincipal(context.Background(), Str(receipt, "verifier_principal_id")); e != nil {
		t.Fatal(e)
	}
	f.switchPrincipal("second-independent-verifier", []string{"VERIFIER"})
	request := Object{"status": "VERIFIED", "verification_run_id": run["id"], "check_results": receipt["checks"]}
	if code, _, _ := f.request("POST", f.path("/evidence/"+Str(ev, "id")+"/verify"), ID(), testTag(ev), request); code != 403 {
		t.Fatalf("revoked receipt verifier %d", code)
	}
}

func TestW07VerifyEvidenceRejectsChangedSnapshotAndWrongEvidence(t *testing.T) {
	o, ev, snapshot, run, receipt := evidenceVerificationFixture(t, "VERIFIED")
	f := o.f
	request := Object{"status": "VERIFIED", "verification_run_id": run["id"], "check_results": receipt["checks"]}
	f.token = o.owner
	other := f.expect(201, "POST", f.path("/evidence"), ID(), f.stateTag(), Object{"claim": "different fixture claim", "stance": "CONTEXT", "evidence_kind": "SIMULATED", "source_kind": "SIMULATION", "canonical_url": nil, "publisher": nil, "upstream_revision": nil, "published_at": nil, "modified_at": nil, "retrieved_at": Now(), "time_status": "UNKNOWN", "snapshot_artifact_ref": Ref(snapshot, "Artifact"), "locator": "other fixture", "independence_key": Hash("other source"), "origin_evidence_id": nil, "discovery_urls": Empty(), "license_status": "UNKNOWN", "license_expression": nil})
	f.switchPrincipal("orchestration-independent-verifier", []string{"VERIFIER"})
	if code, _, _ := f.request("POST", f.path("/evidence/"+Str(other, "id")+"/verify"), ID(), testTag(other), request); code == 200 {
		t.Fatal("wrong evidence accepted")
	}
	if _, e := f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.snapshot_artifact_ref.content_hash',?) WHERE project=? AND kind='Evidence' AND id=?", Hash("tampered fixture snapshot"), f.project, ev["id"]); e != nil {
		t.Fatal(e)
	}
	if code, _, _ := f.request("POST", f.path("/evidence/"+Str(ev, "id")+"/verify"), ID(), testTag(ev), request); code == 200 {
		t.Fatal("tampered snapshot accepted")
	}
}

func TestW07VerifyEvidenceRejectsAliasAndCrossProject(t *testing.T) {
	o, ev, _, run, receipt := evidenceVerificationFixture(t, "VERIFIED")
	f := o.f
	request := Object{"status": "VERIFIED", "verification_run_id": run["id"], "check_results": receipt["checks"]}
	alias := "fixture-source-alias"
	if e := f.s.ProvisionPrincipal(context.Background(), Principal{ID: alias, Roles: []string{"VERIFIER"}, Grants: []Grant{{ProjectID: f.project}}}); e != nil {
		t.Fatal(e)
	}
	if e := f.s.RegisterExecutionIdentity(context.Background(), alias, f.owner); e != nil {
		t.Fatal(e)
	}
	f.switchPrincipal(alias, []string{"VERIFIER"})
	if code, body, _ := f.request("POST", f.path("/evidence/"+Str(ev, "id")+"/verify"), ID(), testTag(ev), request); code != 403 || body["message"] != "evidence reviewer must be independent of source and execution" {
		t.Fatalf("source alias %d %s", code, Bytes(body))
	}
	f.switchPrincipal("orchestration-independent-verifier", []string{"VERIFIER"})
	if code, _, _ := f.request("POST", "/v1/projects/other-project/evidence/"+Str(ev, "id")+"/verify", ID(), testTag(ev), request); code != 404 {
		t.Fatalf("cross-project %d", code)
	}
}

func TestW07VerifyEvidenceRejectsStaleEvidenceAndChangedOutput(t *testing.T) {
	t.Run("evidence revision", func(t *testing.T) {
		o, ev, _, run, receipt := evidenceVerificationFixture(t, "VERIFIED")
		f := o.f
		sourceTx(t, f.db, func(tx *sql.Tx) error {
			current, e := load(tx, f.project, "Evidence", Str(ev, "id"))
			if e != nil {
				return e
			}
			if e = bump(current); e != nil {
				return e
			}
			return f.s.put(tx, "Evidence", current)
		})
		f.switchPrincipal("orchestration-independent-verifier", []string{"VERIFIER"})
		current := f.read("evidence", Str(ev, "id"))
		request := Object{"status": "VERIFIED", "verification_run_id": run["id"], "check_results": receipt["checks"]}
		if code, _, _ := f.request("POST", f.path("/evidence/"+Str(ev, "id")+"/verify"), ID(), testTag(current), request); code == 200 {
			t.Fatal("stale task input accepted")
		}
	})
	t.Run("output artifact", func(t *testing.T) {
		o, ev, _, run, receipt := evidenceVerificationFixture(t, "VERIFIED")
		f := o.f
		ref := Arr(receipt, "artifact_refs")[0].(map[string]any)
		if _, e := f.db.Exec("UPDATE artifact_uses SET body=json_set(body,'$.content_hash',?) WHERE project=? AND artifact=?", Hash("changed fixture report"), f.project, ref["id"]); e == nil {
			t.Fatal("sealed output use was mutable")
		}
		f.switchPrincipal("orchestration-independent-verifier", []string{"VERIFIER"})
		request := Object{"status": "VERIFIED", "verification_run_id": run["id"], "check_results": receipt["checks"]}
		f.expect(200, "POST", f.path("/evidence/"+Str(ev, "id")+"/verify"), ID(), testTag(ev), request)
	})
}

func TestW07VerifyEvidenceObservedLiveFailClosed(t *testing.T) {
	for _, status := range []string{"VERIFIED", "CONTRADICTED", "UNAVAILABLE"} {
		t.Run(status, func(t *testing.T) {
			o, ev, snapshot, run, receipt := evidenceVerificationFixtureSource(t, status, true)
			f := o.f
			if ev["evidence_kind"] != "OBSERVED" || snapshot["measurement_mode"] != "LIVE" || receipt["measurement_mode"] != "FIXTURE" {
				t.Fatal("test did not construct the cross-mode boundary")
			}
			request := Object{"status": status, "verification_run_id": run["id"], "check_results": receipt["checks"]}
			code, body, _ := f.request("POST", f.path("/evidence/"+Str(ev, "id")+"/verify"), ID(), testTag(ev), request)
			if code != 422 || body["message"] != "fixture verification requires simulated evidence and fixture snapshot" {
				t.Fatalf("OBSERVED/LIVE fixture review %d %s", code, Bytes(body))
			}
			current := f.read("evidence", Str(ev, "id"))
			if current["verification_status"] != "UNVERIFIED" || current["revision"] != ev["revision"] {
				t.Fatalf("OBSERVED/LIVE evidence changed %s", Bytes(current))
			}
			t.Logf("fixture %s denied for OBSERVED/LIVE evidence: HTTP %d", status, code)
		})
	}
}
