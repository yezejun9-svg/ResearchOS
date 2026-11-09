package domain

import (
	"testing"
)

// W06-01 part G: the two faces the round-4 review left open.
// G1 reaches acceptance.go:14 for real, on the recipe the reviewer built: a VERIFIER_ONLY reference and a
// project-wide verifier that satisfies the role/grant clause at :11.
// G2 measures the side-effects face rather than asserting about it: whether the acceptance path consults
// effects reconciliation for an ordinary task at all.
func TestW06Step4NegativesPartG(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f

	// G1: visibility, decided by :14 rather than by an earlier clause.
	g1 := o.task("visibility-verifier-only-ref", Empty(), Empty())
	g1r := o.claim(g1)
	g1a := o.report(g1r, []byte(`{"result":"verified"}`))
	g1b := o.acceptance(g1r, g1a)
	raw := []byte(`{"sealed":"verifier only side record"}`)
	u := f.expect(201, "POST", f.path("/content"), ID(), "", raw)
	sealedID := ID()
	// HTTP refuses to create a VERIFIER_ONLY artifact for any principal here (403 restricted reference
	// unavailable), so the sealed record is seeded as a row the way an internal service path would write it.
	if _, e := f.db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body,content_hash,immutable)
		SELECT ?, 'Artifact', ?, revision, json_set(body,'$.id',?,'$.access_class','VERIFIER_ONLY','$.storage_key',?,'$.content_hash',?), ?, 0
		FROM domain_objects WHERE project=? AND kind='Artifact' AND id=?`,
		f.project, sealedID, sealedID, u["storage_key"], u["content_hash"], u["content_hash"], f.project, Str(g1a, "id")); e != nil {
		t.Fatal(e)
	}
	var sealedAccess string
	if e := f.db.QueryRow("SELECT json_extract(body,'$.access_class') FROM domain_objects WHERE project=? AND kind='Artifact' AND id=?", f.project, sealedID).Scan(&sealedAccess); e != nil {
		t.Fatal(e)
	}
	f.switchPrincipal("orchestration-independent-verifier", []string{"VERIFIER"})
	verifierToken := f.token
	withSealed, _ := Decode(Bytes(g1b))
	withSealed["artifact_refs"] = append(Arr(withSealed, "artifact_refs"), Object{"entity_type": "Artifact", "id": sealedID, "revision": 1, "content_hash": nil})
	tx, e := f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	p, e := authenticate(tx, verifierToken)
	if e != nil {
		t.Fatal(e)
	}
	_, visErr := f.s.acceptanceSnapshot(tx, p, f.project, withSealed)
	tx.Rollback()
	fault, isFault := visErr.(*Fault)
	visStatus, visMessage := 0, ""
	if isFault {
		visStatus, visMessage = fault.Status, fault.Message
	}
	orchestrationAssert(t, "W06-01-NEG-VISIBILITY-VERIFIER-ONLY-REF-REFUSED-BY-VISIBLE", []any{403, "acceptance references are not visible to current verifier"},
		[]any{visStatus, visMessage},
		Object{"guard": "acceptance.go:14", "verifier_passes_grant_clause": true, "sealed_artifact": sealedID,
			"seeded_access_class": sealedAccess, "rejection": visErr})

	// Control: the same snapshot without the verifier-only reference still resolves, so the refusal is
	// about that reference and not about the run, the contract or the grant.
	tx2, e := f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	p2, e := authenticate(tx2, verifierToken)
	if e == nil {
		_, e = f.s.acceptanceSnapshot(tx2, p2, f.project, g1b)
	}
	tx2.Rollback()
	orchestrationAssert(t, "W06-01-NEG-VISIBILITY-CONTROL-WITHOUT-SEALED-REF-RESOLVES", true, e == nil,
		Object{"error_if_any": e, "artifact_refs_in_control": Arr(g1b, "artifact_refs")})

	// G2: measure whether an ordinary acceptance consults the effects-reconciliation branch at all.
	// The branch sits behind a qualification marker; count markers for a task that accepted cleanly.
	var markers int
	if e = f.db.QueryRow("SELECT count(*) FROM runtime_qualification_runs WHERE project=? AND task=?", f.project, Str(g1r.task, "id")).Scan(&markers); e != nil {
		t.Fatal(e)
	}
	var receipts int
	if e = f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='AcceptanceReceipt'").Scan(&receipts); e != nil {
		t.Fatal(e)
	}
	before := countAcceptanceReceipts(t, f)
	eff := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(g1r.task), g1b)
	after := countAcceptanceReceipts(t, f)
	orchestrationAssert(t, "W06-01-OUTPUT-SIDE-EFFECT-BRANCH-IS-QUALIFICATION-GATED", []any{0, "PASS", 1},
		[]any{markers, eff["verdict"], after - before},
		Object{"effect_of_dropping_the_reconciliation_call_at_acceptance.go:108_on_this_path": "unmeasurable because the branch sits behind the qualification marker, which is why no id can falsify it here", "receipts_before": before})
}

func countAcceptanceReceipts(t *testing.T, f *fixture) int {
	t.Helper()
	var n int
	if e := f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='AcceptanceReceipt'").Scan(&n); e != nil {
		t.Fatal(e)
	}
	return n
}
