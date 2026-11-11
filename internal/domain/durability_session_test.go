package domain

import (
	"context"
	"testing"
	"time"
)

func TestW12SessionIdentity(t *testing.T) {
	results := Empty()
	for _, mode := range []string{"resume", "switch"} {
		o := orchestrationSetup(t)
		f := o.f
		resourceHTTP(f)
		r := o.claim(o.task("session-"+mode, Empty(), Empty()))
		executorToken := f.token
		checkpoint := resourceCheckpoint(r, Object{"step": "durable original session"})
		old := Merge(Object{}, r.run)
		oldHeartbeat := r.heartbeat()
		oldReport := r.report(Empty(), 0)
		oldObservation := r.observation("LOST", false)
		r.observe(oldObservation)
		f.token = o.owner
		policy := f.expect(200, "GET", f.path("/goals/"+Str(o.goal, "id")+"/budget-policy"), "", "", nil)
		providerKey := "original-provider-" + mode
		reservation := f.expect(201, "POST", f.path("/budget-ledger"), ID(), testTag(policy), budgetRequest(r, Str(policy, "id"), "UNKNOWN", providerKey, nil, "UNKNOWN", nil))
		var result Object
		var e error
		if mode == "resume" {
			revision, _ := Num(r.run, "revision")
			result, e = f.s.ResumeCheckpoint(context.Background(), o.owner, f.project, Str(r.run, "id"), "identity-resume-key", revision)
		} else {
			replacement := f.expect(201, "POST", f.path("/runtimes"), ID(), f.stateTag(), Object{"name": "new session fixture", "adapter": "fixture", "adapter_revision": "1", "capabilities": []any{"fixture"}, "platform": "windows-amd64", "measurement_mode": "FIXTURE", "credential_ref": nil})
			if e = f.s.RegisterOrchestrationFixture(context.Background(), f.project, Str(replacement, "id")); e != nil {
				t.Fatal(e)
			}
			if e = f.s.AuthorizeFixtureResource(context.Background(), o.owner, f.project, Str(replacement, "id"), "json-verification", Ref(checkpoint, "Artifact"), time.Now().Add(time.Hour)); e != nil {
				t.Fatal(e)
			}
			result, e = f.s.SwitchResource(context.Background(), o.owner, f.project, Str(r.run, "id"), Str(replacement, "id"), resourceRequestBody(r, checkpoint))
		}
		if e != nil {
			t.Fatal(e)
		}
		r.run = result["run"].(map[string]any)
		r.lease = Str(result, "lease_token")
		f.token = executorToken
		if result["native_resume"] != false || r.run["external_run_id"] != nil || r.run["lease_token_hash"] == old["lease_token_hash"] {
			t.Fatal("session reconstruction reused former binding")
		}
		oldEpoch, _ := Num(old, "lease_epoch")
		newEpoch, _ := Num(r.run, "lease_epoch")
		if newEpoch != oldEpoch+1 {
			t.Fatal("session epoch not advanced once")
		}
		path := f.path("/runs/" + Str(r.run, "id"))
		oldStatus, _, _ := f.request("POST", path+"/heartbeat", ID(), testTag(r.run), oldHeartbeat)
		reportStatus, _, _ := f.request("POST", path+"/report", ID(), testTag(r.run), oldReport)
		if oldStatus != 409 || reportStatus != 409 {
			t.Fatal("former callbacks escaped lease fence", oldStatus, reportStatus)
		}
		if e = f.s.ObserveRuntime(context.Background(), f.project, Str(r.run, "id"), oldEpoch, oldObservation); e != nil {
			t.Fatal(e)
		}
		f.expect(200, "GET", f.path("/artifacts/"+Str(checkpoint, "id")), "", "", nil)
		hb := r.heartbeat()
		hb["external_run_id"] = "replacement-session-" + mode
		r.call("/heartbeat", hb, 200)
		if r.run["checkpoint_artifact_id"] != checkpoint["id"] || r.run["id"] != old["id"] || r.run["external_run_id"] != hb["external_run_id"] {
			t.Fatal("new session did not retain recovery identity")
		}
		f.token = o.owner
		late := f.expect(201, "POST", f.path("/budget-ledger"), ID(), testTag(policy), budgetRequest(r, Str(policy, "id"), "RECONCILE", providerKey, dollars("1.25"), "ACTUAL", reservation["id"]))
		var carries, archived int
		if e = f.db.QueryRow("SELECT count(*) FROM resource_checkpoint_carries WHERE run=? AND epoch=?", r.run["id"], newEpoch).Scan(&carries); e != nil {
			t.Fatal(e)
		}
		if e = f.db.QueryRow("SELECT count(*) FROM resource_route_history WHERE run=? AND json_extract(body,'$.previous_external_run_id')=?", r.run["id"], old["external_run_id"]).Scan(&archived); e != nil {
			t.Fatal(e)
		}
		if carries != 1 || archived != 1 || late["run_id"] != old["id"] {
			t.Fatal("carry, former session audit or cost attribution lost")
		}
		results = append(results, Object{"mode": mode, "old": old, "current": r.run, "old_heartbeat_status": oldStatus, "old_report_status": reportStatus, "checkpoint_carries": carries, "archived_external_id": archived, "late_original_run_cost": late})
	}
	resourcesAssert(t, "W12-SESSION-IDENTITY-FENCE", 2, len(results), results)
}
