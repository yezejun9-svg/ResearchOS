package domain

import (
	"database/sql"
	"testing"
)

func retentionAccept(o *orchestrationFixture, title string, raw []byte) (*runtimeFixture, Object, Object) {
	f := o.f
	r := o.claim(o.task(title, Empty(), Empty()))
	a := o.report(r, raw)
	b := o.acceptance(r, a)
	receipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(r.task), b)
	f.token = o.owner
	return r, a, receipt
}

func TestW12RetentionGates(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	resourceHTTP(f)
	first, artifact, receipt := retentionAccept(o, "retained-candidate", []byte(`{"result":"verified"}`))
	initial := f.read("no-progress-records", Str(first.task, "no_progress_record_id"))
	resourcesAssert(t, "W12-RETENTION-ACCEPTED", Ref(artifact, "Artifact"), initial["best_accepted_artifact_ref"], Object{"progress": initial, "acceptance": receipt, "producer": first.executor})
	second, other, otherReceipt := retentionAccept(o, "retained-candidate", []byte(`{ "result" : "verified" }`))
	current := f.read("no-progress-records", Str(second.task, "no_progress_record_id"))
	resourcesAssert(t, "W12-RETENTION-NO-INVENTED-RANKING", []any{true, Ref(artifact, "Artifact"), initial["last_effective_progress_at"], 0, 0}, []any{artifact["content_hash"] != other["content_hash"], current["best_accepted_artifact_ref"], current["last_effective_progress_at"], current["same_failure_count"], current["no_progress_iterations"]}, Object{"first": receipt, "later": otherReceipt, "selection_rule": "retain existing qualified result; no comparable metric registered"})

	pending := o.claim(o.task("retained-candidate", Empty(), Empty()))
	unaccepted := o.report(pending, []byte(`{"result": "verified"}`))
	tx, e := f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	notAcceptedErr := f.s.retainAcceptedResult(tx, f.project, pending.task)
	tx.Rollback()
	f.token = o.owner
	after := f.read("no-progress-records", Str(pending.task, "no_progress_record_id"))
	resourcesAssert(t, "W12-RETENTION-UNACCEPTED", []any{true, Ref(artifact, "Artifact")}, []any{notAcceptedErr != nil, after["best_accepted_artifact_ref"]}, Object{"candidate_artifact": unaccepted, "task_status": pending.task["status"], "error": notAcceptedErr.Error()})

	request := o.acceptance(pending, unaccepted)
	verifierToken := f.token
	// Existing acceptance identity barrier must reject even an executor granted
	// the VERIFIER role; retaining is never a separate self-approval route.
	if _, e = f.db.Exec("UPDATE auth_principals SET roles='[\"EXECUTOR\",\"VERIFIER\"]' WHERE id=?", pending.executor); e != nil {
		t.Fatal(e)
	}
	if _, e = f.db.Exec("INSERT INTO auth_grants(principal,project) VALUES(?,?)", pending.executor, f.project); e != nil {
		t.Fatal(e)
	}
	f.switchPrincipal(pending.executor, []string{"VERIFIER"})
	code, denial, _ := f.request("POST", f.path("/acceptances"), ID(), testTag(pending.task), request)
	f.token = o.owner
	after = f.read("no-progress-records", Str(pending.task, "no_progress_record_id"))
	resourcesAssert(t, "W12-RETENTION-SELF-APPROVAL", []any{403, Ref(artifact, "Artifact")}, []any{code, after["best_accepted_artifact_ref"]}, Object{"response": denial, "progress": after})

	// Model the same trusted validity revision change that invalidation produces;
	// a sealed old body remains for history, but cannot pass current acceptance.
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		a, e := load(tx, f.project, "Artifact", Str(unaccepted, "id"))
		if e != nil {
			return e
		}
		a["validity"] = "STALE"
		if e = bump(a); e != nil {
			return e
		}
		return f.s.put(tx, "Artifact", a)
	})
	f.token = verifierToken
	code, denial, _ = f.request("POST", f.path("/acceptances"), ID(), testTag(pending.task), request)
	f.token = o.owner
	after = f.read("no-progress-records", Str(pending.task, "no_progress_record_id"))
	resourcesAssert(t, "W12-RETENTION-STALE-CANDIDATE", []any{true, Ref(artifact, "Artifact")}, []any{code != 201, after["best_accepted_artifact_ref"]}, Object{"status": code, "response": denial, "invalidation": "trusted artifact validity revision fault injection"})
	resourceSnapshot(f, "retention-gates.json")
}

func TestW12RetentionInvalidation(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	resourceHTTP(f)
	accepted, artifact, receipt := retentionAccept(o, "invalidate-retained", []byte(`{"result":"verified"}`))
	pending := o.claim(o.task("invalidate-retained", Empty(), Empty()))
	executorToken := f.token
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		a, e := load(tx, f.project, "Artifact", Str(artifact, "id"))
		if e != nil {
			return e
		}
		a["validity"] = "STALE"
		if e = bump(a); e != nil {
			return e
		}
		return f.s.put(tx, "Artifact", a)
	})
	f.token = executorToken
	obs := pending.observation("FAILED", false)
	obs["artifacts"] = Empty()
	pending.observe(obs)
	pending.call("/report", pending.report(Empty(), 0), 200)
	f.token = o.owner
	n := f.read("no-progress-records", Str(accepted.task, "no_progress_record_id"))
	task := f.read("tasks", Str(pending.task, "id"))
	var history int
	var raw []byte
	if e := f.db.QueryRow("SELECT count(*) FROM domain_versions WHERE project=? AND kind='NoProgressRecord' AND id=? AND json_extract(body,'$.best_accepted_artifact_ref.id')=?", f.project, n["id"], artifact["id"]).Scan(&history); e != nil {
		t.Fatal(e)
	}
	if e := f.db.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", f.project, artifact["storage_key"]).Scan(&raw); e != nil {
		t.Fatal(e)
	}
	resourcesAssert(t, "W12-RETENTION-INVALIDATED-HISTORY", []any{nil, 1, "FAILED", true, artifact["content_hash"], true}, []any{n["best_accepted_artifact_ref"], n["no_progress_iterations"], task["status"], history > 0, Digest(raw), len(Arr(n, "resume_conditions")) > 0}, Object{"progress": n, "old_receipt_hash": receipt["receipt_hash"], "historical_versions": history, "bytes_retained": len(raw), "rule": "stale result detached from current pointer; history retained; no failed-run rollback"})
	resourceSnapshot(f, "retention-invalidated.json")
}
