package domain

import (
	"bufio"
	"context"
	"database/sql"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func TestW13MilestoneGates(t *testing.T) {
	for _, mode := range []string{"stale", "authority"} {
		t.Run(mode, func(t *testing.T) {
			o := workbenchFixture(t)
			f := o.f
			task, a, receipt := workbenchAccept(o, "qualified")
			pending := o.claim(o.task("not-accepted", Empty(), Empty()))
			unaccepted := o.report(pending, []byte(`{ "result" : "verified" }`))
			body := workbenchReleaseBody(f, unaccepted, receipt)
			code, _, _ := f.request("POST", f.path("/releases"), ID(), f.stateTag(), body)
			if code != 422 {
				t.Fatalf("unaccepted replacement: %d", code)
			}
			body = workbenchReleaseBody(f, a, receipt)
			if mode == "stale" {
				sourceTx(t, f.db, func(tx *sql.Tx) error {
					current, e := load(tx, f.project, "Artifact", Str(a, "id"))
					if e != nil {
						return e
					}
					current["validity"] = "STALE"
					if e = bump(current); e != nil {
						return e
					}
					return f.s.put(tx, "Artifact", current)
				})
			} else {
				// Trusted identity reassignment invalidates previously independent
				// authority; a historical PASS cannot survive this current check.
				if e := f.s.RegisterExecutionIdentity(context.Background(), Str(receipt, "verifier_principal_id"), Str(task, "assigned_principal_id")); e != nil {
					t.Fatal(e)
				}
			}
			before := f.state()
			code, response, _ := f.request("POST", f.path("/releases"), ID(), testTag(before), body)
			workbenchAssert(t, "W13-RELEASE-GATE-"+strings.ToUpper(mode), []any{true, 0, before}, []any{code != 201, countKind(t, f.db, "MilestoneRelease"), f.state()}, Object{"http_status": code, "response": response, "unaccepted_replacement_rejected": true, "independent_receipt": receipt})
		})
	}
}

func TestW13GoalMilestone(t *testing.T) {
	o := workbenchFixture(t)
	f := o.f
	r := o.claim(o.task("goal-result", Empty(), Empty()))
	a := o.report(r, []byte(`{"result":"verified"}`))
	b := o.acceptance(r, a)
	f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(r.task), b)
	task := f.read("tasks", Str(r.task, "id"))
	goal := f.read("goals", Str(o.goal, "id"))
	b["subject_ref"], b["run_id"] = Ref(goal, "Goal"), nil
	b["contract_hash"] = goal["acceptance_contract"].(map[string]any)["contract_hash"]
	b["input_refs"] = append(append(Empty(), Arr(goal, "requirement_refs")...), Ref(task, "Task"))
	acceptance := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(goal), b)
	f.token = o.owner
	release := f.expect(201, "POST", f.path("/releases"), ID(), f.stateTag(), workbenchReleaseBody(f, a, acceptance))
	workbenchAssert(t, "W13-RELEASE-GOAL", []any{acceptance["id"]}, release["acceptance_ids"], Object{"goal_acceptance": acceptance, "release": release})
}

func TestW13PreviewAndFiltering(t *testing.T) {
	o := workbenchFixture(t)
	f := o.f
	server := httptest.NewServer(f.s.Handler())
	t.Cleanup(server.Close)
	data := []byte(`<script>window.fixtureAttack=true</script><img src="https://invalid.test/private"><h1>Untrusted HTML</h1>`)
	u := f.expect(201, "POST", f.path("/content"), ID(), "", data)
	body := Object{"run_id": nil, "kind": "REPORT", "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE", "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "text/html", "byte_size": len(data), "input_refs": Empty(), "source_refs": Empty(), "produced_by": f.owner, "access_class": "PROJECT"}
	a := f.expect(201, "POST", f.path("/artifacts"), ID(), f.stateTag(), body)
	request, _ := http.NewRequest("GET", server.URL+f.path("/artifacts/"+Str(a, "id")+"/content"), nil)
	request.Header.Set("Authorization", "Bearer "+f.token)
	response, e := server.Client().Do(request)
	if e != nil {
		t.Fatal(e)
	}
	bytes, _ := io.ReadAll(response.Body)
	response.Body.Close()
	workbenchAssert(t, "W13-PREVIEW-HEADERS", []any{200, "sandbox; default-src 'none'", "attachment", "nosniff", a["content_hash"]}, []any{response.StatusCode, response.Header.Get("Content-Security-Policy"), response.Header.Get("Content-Disposition"), response.Header.Get("X-Content-Type-Options"), Digest(bytes)}, Object{"artifact_ref": Ref(a, "Artifact"), "headers": response.Header, "browser_script_execution": "NOT_RUN"})
	// Synthetic classification metadata only. No formal protected bytes or
	// holdout labels are installed; the actual protected store remains W17.
	private := Merge(Base(f.project), Object{"run_id": nil, "kind": "TEST_RESULT", "evidence_kind": "SIMULATED", "validity": "CURRENT", "measurement_mode": "FIXTURE", "content_hash": Digest(nil), "storage_key": "unbound-w13-protected-metadata", "media_type": "application/json", "byte_size": 0, "input_refs": Empty(), "source_refs": Empty(), "produced_by": f.owner, "sealed_at": Now(), "access_class": "VERIFIER_ONLY"})
	before := f.state()
	watermark, _ := Num(before, "event_sequence")
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		if e := f.s.put(tx, "Artifact", private); e != nil {
			return e
		}
		return f.s.event(tx, f.project, "Artifact", private, f.owner, ID(), "PROJECT_UPDATED")
	})
	f.requirement()
	stream, closeStream := workbenchStream(t, server, f.path("/events/stream"), f.token, fmt.Sprint(watermark))
	r := bufio.NewReader(stream.Body)
	workbenchFrame(t, r)
	frame := workbenchFrame(t, r)
	ev := workbenchEventFrame(t, frame)
	closeStream()
	stream.Body.Close()
	seq, _ := Num(ev, "sequence")
	code, _, _ := f.request("GET", f.path("/artifacts/"+Str(private, "id")), "", "", nil)
	workbenchAssert(t, "W13-SSE-ITEM-FILTER", []any{404, true, true}, []any{code, seq > watermark+1, !strings.Contains(frame, Str(private, "id")) && !strings.Contains(frame, Str(private, "content_hash"))}, Object{"public_frame": frame, "filtered_event_sequence": watermark + 1, "gap_is_permission_filter": true})
	privileged := Principal{ID: "w13-protected-reviewer", Roles: []string{"VERIFIER"}, Grants: []Grant{{ProjectID: f.project, Restricted: true}}}
	if e = f.s.ProvisionPrincipal(context.Background(), privileged); e != nil {
		t.Fatal(e)
	}
	f.token, e = f.s.IssueCredential(context.Background(), privileged.ID, time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	protectedCode, protectedReply, _ := f.request("GET", f.path("/artifacts/"+Str(private, "id")+"/content"), "", "", nil)
	workbenchAssert(t, "W13-PREVIEW-PROTECTED-UNAVAILABLE", 503, protectedCode, Object{"response": protectedReply, "classification_only_fixture": true, "protected_store": "W17_NOT_QUALIFIED"})
	resourceEvidence(t, "preview-headers.json", Object{"artifact_ref": Ref(a, "Artifact"), "headers": response.Header, "body_sha256": Digest(bytes), "public_sse_frame": frame})
}
