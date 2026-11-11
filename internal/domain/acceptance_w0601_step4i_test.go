package domain

import (
	"context"
	"testing"
	"time"
)

// Part I replaces part F's structurally-frozen rStatus/aStatus zeros (which could only ever be 0) with
// unconditional attempts: each route is called whatever happened before it, and each records its own refusal.
// The measured mechanism is not "output isolation at the acceptance level": a verifier cannot create a
// VERIFIER_ONLY artifact on another principal's run at all (:11/:14 grant-and-visibility), and an acceptance
// body that names a foreign artifact fails as a vector mismatch at :222 before the isolation clause at :208
// is ever consulted. See precision_notes_round6_findings.json.
func TestW06Step4NegativesPartI(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	countReceipts := func() int {
		var n int
		if e := f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='AcceptanceReceipt'").Scan(&n); e != nil {
			t.Fatal(e)
		}
		return n
	}
	p := o.task("isolation-routes-answer-for-themselves", Empty(), Empty())
	r := o.claim(p)
	good := o.report(r, []byte(`{"result":"verified"}`))
	raw := []byte(`{"verifier_only":"part-i"}`)
	f.token = o.owner
	tag := f.stateTag()
	f.switchPrincipal("part-i-project-wide-verifier", []string{"VERIFIER"})
	verifierToken := f.token
	u := f.expect(201, "POST", f.path("/content"), ID(), "", raw)
	artifactBody := func(class string) Object {
		return Object{"run_id": r.run["id"], "kind": "REPORT", "evidence_kind": "GENERATED",
			"measurement_mode": "FIXTURE", "content_hash": u["content_hash"], "storage_key": u["storage_key"],
			"media_type": "application/json", "byte_size": len(raw), "input_refs": r.task["input_refs"],
			"source_refs": Empty(), "produced_by": "part-i-project-wide-verifier", "access_class": class}
	}
	before := countReceipts()
	cStatus, created, _ := f.request("POST", f.path("/artifacts"), ID(), tag, artifactBody("VERIFIER_ONLY"))
	orchestrationAssert(t, "W06-01-NEG-ISOLATION-CREATION-REFUSAL-IS-GRANT-VISIBILITY",
		[]any{403, "FORBIDDEN", "restricted reference unavailable", 0},
		[]any{cStatus, created["code"], created["message"], countReceipts() - before},
		Object{"access_class": "VERIFIER_ONLY", "actor": "project-wide VERIFIER, not the executor",
			"rejection": created, "route": "POST /artifacts"})
	rStatus, restricted, _ := f.request("POST", f.path("/artifacts"), ID(), tag, artifactBody("RESTRICTED"))
	orchestrationAssert(t, "W06-01-NEG-ISOLATION-RESTRICTED-CLASS-REFUSED-BY-SCHEMA",
		[]any{400, "INVALID_REQUEST", "request violates CreateArtifactRequest schema", 0},
		[]any{rStatus, restricted["code"], restricted["message"], countReceipts() - before},
		Object{"access_class": "RESTRICTED", "rejection": restricted,
			"meaning": "this value never reaches any isolation guard, so it cannot evidence one"})

	// The executor's report route is attempted unconditionally even though the run is already terminal: it
	// answers with its own state refusal rather than an isolation one.
	ghost := ID()
	etok, ee := f.s.IssueCredential(context.Background(), r.executor, 15*time.Minute)
	if ee != nil {
		t.Fatal(ee)
	}
	f.token = etok
	r.refresh()
	reportBody := r.report([]any{good["id"], ghost}, 0)
	tStatus, terminal, _ := f.request("POST", f.path("/runs/"+Str(r.run, "id")+"/report"), ID(), testTag(r.run), reportBody)
	orchestrationAssert(t, "W06-01-NEG-ISOLATION-REPORT-ROUTE-CLOSED-AFTER-TERMINAL-RUN",
		[]any{409, "STATE_CONFLICT", "run already terminal", 0},
		[]any{tStatus, terminal["code"], terminal["message"], countReceipts() - before},
		Object{"declared_artifact_ids": reportBody["result_artifact_ids"], "rejection": terminal,
			"meaning": "the second report attempt is refused by run state, so the isolation clause is not what kept it"})

	// An acceptance body that names the never-created artifact fails as a vector mismatch before :208 is read.
	f.token = verifierToken
	task := f.read("tasks", Str(p, "id"))
	refs := append(Arr(task, "output_artifact_ids"), ghost)
	artifactRefs := Empty()
	for _, id := range refs {
		artifactRefs = append(artifactRefs, Object{"entity_type": "Artifact", "id": id, "revision": 1, "content_hash": nil})
	}
	b := o.acceptance(r, good)
	b["artifact_refs"] = artifactRefs
	b["input_refs"] = task["input_refs"]
	aStatus, foreign, _ := f.request("POST", f.path("/acceptances"), ID(), testTag(task), b)
	orchestrationAssert(t, "W06-01-NEG-ISOLATION-FOREIGN-REF-FAILS-AS-VECTOR-BEFORE-ISOLATION",
		[]any{422, "GATE_FAILED", "exact output artifact vector required", 0},
		[]any{aStatus, foreign["code"], foreign["message"], countReceipts() - before},
		Object{"refs": len(artifactRefs), "rejection": foreign,
			"clause_order": "the vector comparison answers, the isolation clause at :208 is never consulted"})

	// Control: the same verifier, the same task, a vector that matches - accepted. Without this the four rows
	// above would only prove the fixture is broken.
	c := o.acceptance(r, good)
	cStatus2, accepted, _ := f.request("POST", f.path("/acceptances"), ID(), testTag(task), c)
	orchestrationAssert(t, "W06-01-NEG-ISOLATION-PLAIN-VECTOR-CONTROL-ACCEPTED",
		[]any{201, "PASS", "ACCEPTED", 1},
		[]any{cStatus2, accepted["verdict"], Str(f.read("tasks", Str(p, "id")), "status"), countReceipts() - before},
		Object{"receipt_id": accepted["id"], "artifact_refs": c["artifact_refs"]})
}
