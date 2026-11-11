package domain

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"testing"
)

func workbenchAssert(t *testing.T, id string, want, got, evidence any) {
	t.Helper()
	status := "PASS"
	if Hash(want) != Hash(got) {
		status = "FAIL"
	}
	fmt.Println("W13_ASSERTION " + string(Bytes(Object{"assertion_id": id, "expected": want, "actual": got, "status": status, "evidence": evidence})))
	if status != "PASS" {
		t.Fatalf("%s mismatch", id)
	}
}

func workbenchFixture(t *testing.T) *orchestrationFixture {
	t.Helper()
	t.Setenv("W12_EVIDENCE_DIR", os.Getenv("W13_EVIDENCE_DIR"))
	o := orchestrationSetup(t)
	resourceHTTP(o.f)
	return o
}

func workbenchAccept(o *orchestrationFixture, name string) (Object, Object, Object) {
	r := o.claim(o.task(name, Empty(), Empty()))
	a := o.report(r, []byte(`{"result":"verified"}`))
	b := o.acceptance(r, a)
	receipt := o.f.expect(201, "POST", o.f.path("/acceptances"), ID(), testTag(r.task), b)
	o.f.token = o.owner
	return o.f.read("tasks", Str(r.task, "id")), a, receipt
}

func workbenchReleaseBody(f *fixture, a, receipt Object) Object {
	return Object{"scope": "PROJECT", "software_version": nil, "summary": "Independent verified result", "changes": []any{"Deliverable independently accepted"}, "decision_ids": Empty(), "artifact_refs": []any{Ref(a, "Artifact")}, "acceptance_ids": []any{receipt["id"]}, "open_issues": []any{"Development fixture; no live qualification"}, "next_steps": []any{"Independent development review"}, "policy_revision": f.state()["policy_revision"], "supersedes_id": nil}
}

func workbenchCounts(p Object) []any {
	sums := []int64{0, 0, 0, 0, 0}
	for _, v := range Arr(p, "stages") {
		c := v.(map[string]any)
		for i, field := range []string{"planned", "accepted", "pending_review", "blocked", "active"} {
			n, _ := Num(c, field)
			sums[i] += n
		}
	}
	return []any{sums[0], sums[1], sums[2], sums[3], sums[4]}
}

func TestW13Progress(t *testing.T) {
	o := workbenchFixture(t)
	f := o.f
	var accepted, artifact Object
	for i := 0; i < 4; i++ {
		accepted, artifact, _ = workbenchAccept(o, fmt.Sprintf("accepted-%d", i))
	}
	for i := 0; i < 2; i++ {
		r := o.claim(o.task(fmt.Sprintf("pending-%d", i), Empty(), Empty()))
		o.report(r, []byte(`{"result":"verified"}`))
		// The public report is real. VERIFYING is a trusted fixture of the
		// transient verification phase; no accepted receipt is fabricated.
		sourceTx(t, f.db, func(tx *sql.Tx) error {
			task, e := load(tx, f.project, "Task", Str(r.task, "id"))
			if e != nil {
				return e
			}
			task["status"] = "VERIFYING"
			if e = bump(task); e != nil {
				return e
			}
			// W06 currently has no public EXECUTION_REPORTED -> VERIFYING
			// transition. Install this schema-valid transient fixture explicitly,
			// preserving immutable version history; never install ACCEPTED here.
			if e = f.s.Contracts.Validate("Task", task); e != nil {
				return e
			}
			if _, e = tx.Exec("INSERT INTO domain_versions(project,kind,id,revision,body) VALUES(?,'Task',?,?,?)", f.project, task["id"], task["revision"], string(Bytes(task))); e != nil {
				return e
			}
			if _, e = tx.Exec("UPDATE domain_objects SET revision=?,body=? WHERE project=? AND kind='Task' AND id=?", task["revision"], string(Bytes(task)), f.project, task["id"]); e != nil {
				return e
			}
			rev, _ := Num(task, "revision")
			if e = f.s.refs(tx, f.project, "Task", Str(task, "id"), rev, "", task); e != nil {
				return e
			}
			return f.s.event(tx, f.project, "Task", task, f.owner, ID(), "TASK_CHANGED")
		})
	}
	f.token = o.owner
	first := f.expect(200, "GET", f.path("/progress"), "", "", nil)
	for i := 0; i < 3; i++ {
		o.task(fmt.Sprintf("new-ready-%d", i), Empty(), Empty())
	}
	second := f.expect(200, "GET", f.path("/progress"), "", "", nil)
	workbenchAssert(t, "W13-C18-COUNTS", []any{[]any{6, 4, 2, 0, 0}, []any{9, 4, 2, 0, 0}}, []any{workbenchCounts(first), workbenchCounts(second)}, Object{"before": first, "after": second})
	beforePlan, _ := Num(first, "plan_revision")
	afterPlan, _ := Num(second, "plan_revision")
	workbenchAssert(t, "W13-C18-PLAN", []any{6, true, true, 9}, []any{len(Arr(second, "stages")), afterPlan > beforePlan, second["plan_change_note"] != nil, len(o.f.expect(200, "GET", f.path("/tasks"), "", "", nil)["items"].([]any))}, Object{"plan_revision_before": beforePlan, "plan_revision_after": afterPlan, "rule": "one revision per task creation or planning-field change; runtime-only revisions excluded"})
	page := f.expect(200, "GET", f.path("/events?limit=100"), "", "", nil)
	items := Arr(page, "items")
	last := items[len(items)-1].(map[string]any)
	if _, e := f.s.ConsumeEvent(context.Background(), "w13-projection", f.project, Str(last, "id")); e != nil {
		t.Fatal(e)
	}
	for _, v := range items {
		if _, e := f.s.ConsumeEvent(context.Background(), "w13-projection", f.project, Str(v.(map[string]any), "id")); e != nil {
			t.Fatal(e)
		}
	}
	if _, e := f.s.ConsumeEvent(context.Background(), "w13-projection", f.project, Str(items[0].(map[string]any), "id")); e != nil {
		t.Fatal(e)
	}
	rebuilt := f.expect(200, "GET", f.path("/progress"), "", "", nil)
	var applied int64
	var projectedRaw string
	if e := f.db.QueryRow("SELECT sequence FROM consumer_positions WHERE consumer='w13-projection' AND project=?", f.project).Scan(&applied); e != nil {
		t.Fatal(e)
	}
	if e := f.db.QueryRow("SELECT body FROM context_projection WHERE consumer='w13-projection' AND project=? AND kind='Task' AND id=?", f.project, accepted["id"]).Scan(&projectedRaw); e != nil {
		t.Fatal(e)
	}
	projected, e := Decode([]byte(projectedRaw))
	if e != nil {
		t.Fatal(e)
	}
	workbenchAssert(t, "W13-C18-REBUILD", []any{second, second["as_of_event_sequence"], Ref(accepted, "Task")}, []any{rebuilt, applied, Ref(projected, "Task")}, Object{"replay_order": "last first, then sequence order, then duplicate oldest", "authority": "domain_objects/domain_versions; no projection writes"})
	// Current accepted graph, rather than an ACCEPTED string alone, controls the
	// count. Canonical invalidation is explicit trusted revision fault injection.
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		a, e := load(tx, f.project, "Artifact", Str(artifact, "id"))
		if e != nil {
			return e
		}
		a["validity"] = "STALE"
		if e = bump(a); e != nil {
			return e
		}
		if e = f.s.put(tx, "Artifact", a); e != nil {
			return e
		}
		return f.s.event(tx, f.project, "Artifact", a, f.owner, ID(), "PROJECT_UPDATED")
	})
	invalidated := f.expect(200, "GET", f.path("/progress"), "", "", nil)
	counts := workbenchCounts(invalidated)
	workbenchAssert(t, "W13-PROGRESS-CURRENT-ACCEPTANCE", []any{true, afterPlan}, []any{counts[1].(int64) < 4, invalidated["plan_revision"]}, Object{"invalidated_artifact": artifact["id"], "accepted_task": accepted["id"], "projection": invalidated})
	resourceSnapshot(f, "progress-authority.json")
}

func TestW13Milestones(t *testing.T) {
	o := workbenchFixture(t)
	f := o.f
	_, artifact, acceptance := workbenchAccept(o, "release-candidate")
	f.switchPrincipal("w13-reader", []string{"READER"})
	readerToken := f.token
	f.token = o.owner
	b := workbenchReleaseBody(f, artifact, acceptance)
	key, tag := ID(), f.stateTag()
	release := f.expect(201, "POST", f.path("/releases"), key, tag, b)
	for i := 0; i < 4; i++ {
		r := f.expect(201, "POST", f.path("/releases"), key, tag, b)
		if r["id"] != release["id"] {
			t.Fatal("release replay changed identity")
		}
	}
	var logical int
	if e := f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Notification' AND json_extract(body,'$.release_id')=? AND json_extract(body,'$.recipient_id')='w13-reader'", f.project, release["id"]).Scan(&logical); e != nil {
		t.Fatal(e)
	}
	workbenchAssert(t, "W13-C17-DEDUP", []any{1, 1}, []any{logical, countKind(t, f.db, "MilestoneRelease")}, Object{"release": release, "deliveries": 5})
	projection := f.expect(200, "GET", f.path("/progress"), "", "", nil)
	f.token = readerToken
	page := f.expect(200, "GET", f.path("/notifications"), "", "", nil)
	items := Arr(page, "items")
	if len(items) != 1 {
		t.Fatalf("reader received %d notifications", len(items))
	}
	n := items[0].(map[string]any)
	detail := f.read("releases", Str(n, "release_id"))
	workbenchAssert(t, "W13-C17-BINDING", []any{release["id"], []any{Ref(artifact, "Artifact")}, []any{acceptance["id"]}, release["id"]}, []any{n["release_id"], detail["artifact_refs"], detail["acceptance_ids"], projection["latest_release_id"]}, Object{"notification": n, "release": detail, "projection": projection})
	readBody := Object{"reason": "read locally"}
	read := f.expect(200, "POST", f.path("/notifications/"+Str(n, "id")+"/read"), ID(), testTag(n), readBody)
	watermark := f.state()["event_sequence"]
	again := f.expect(200, "POST", f.path("/notifications/"+Str(n, "id")+"/read"), ID(), testTag(read), readBody)
	workbenchAssert(t, "W13-C17-READ-IDEMPOTENT", []any{read, watermark}, []any{again, f.state()["event_sequence"]}, Object{"same_status_new_key": true})
	f.token = o.owner
	code, _, _ := f.request("GET", f.path("/notifications/"+Str(n, "id")), "", "", nil)
	codeWrite, _, _ := f.request("POST", f.path("/notifications/"+Str(n, "id")+"/read"), ID(), testTag(read), readBody)
	workbenchAssert(t, "W13-NOTIFICATION-RECIPIENT", []any{404, 404}, []any{code, codeWrite}, Object{"recipient": "w13-reader", "other": f.owner})
	// Replay durable outbox delivery, including an interrupted/unacknowledged
	// release. Consumers only rebuild projections; they never create releases.
	pending, e := f.s.PendingEvents(context.Background(), f.project)
	if e != nil {
		t.Fatal(e)
	}
	for replay := 0; replay < 5; replay++ {
		for _, event := range pending {
			if _, e = f.s.ConsumeEvent(context.Background(), "w13-offline", f.project, Str(event, "id")); e != nil {
				t.Fatal(e)
			}
		}
	}
	var restored int
	f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='Notification' AND json_extract(body,'$.recipient_id')='w13-reader'").Scan(&restored)
	workbenchAssert(t, "W13-C17-DURABLE-REPLAY", []any{true, 1, 1}, []any{len(pending) > 0, restored, countKind(t, f.db, "MilestoneRelease")}, Object{"outbox_count": len(pending), "replays": 5, "external_channels": Empty()})
	// A late notification storage failure rolls back release, project pointer,
	// sequence and all outbox entries in the same HTTP transaction.
	before := f.state()
	if _, e = f.db.Exec("CREATE TRIGGER w13_fail_notification BEFORE INSERT ON domain_objects WHEN NEW.kind='Notification' BEGIN SELECT RAISE(ABORT,'w13 injected notification failure'); END;"); e != nil {
		t.Fatal(e)
	}
	code, _, _ = f.request("POST", f.path("/releases"), ID(), testTag(before), b)
	f.db.Exec("DROP TRIGGER w13_fail_notification")
	workbenchAssert(t, "W13-RELEASE-ATOMIC", []any{true, before, 1}, []any{code != 201, f.state(), countKind(t, f.db, "MilestoneRelease")}, Object{"http_status": code, "fault": "notification insertion rejected after release event creation"})
	second := f.expect(201, "POST", f.path("/releases"), ID(), f.stateTag(), b)
	workbenchAssert(t, "W13-RELEASE-SEQUENCE", []any{2, release["id"], nil}, []any{second["sequence"], second["parent_release_id"], second["software_version"]}, second)
	resourceSnapshot(f, "milestones-notifications.json")
}
