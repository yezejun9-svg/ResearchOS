package domain

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"testing"
	"time"

	"researchos.local/research-os/adapters/protectedstore"
	holdout "researchos.local/research-os/evaluation/holdout/jev"
)

// These tests inject unexported preparedQualification only inside package tests.
// LIVE below exercises the admission branch; all test data and statistics are
// PUBLIC_FIXTURE_ONLY. There is no SCM query, real key, provider or formal dataset.
const qualificationPrivateCanary = "PUBLIC_FIXTURE_PRIVATE_BODY_MUST_NOT_ENTER_SQLITE_20260930"

type qualificationFixture struct {
	f                  *fixture
	q, dev, private    Object
	proof              *preparedQualification
	acceptance, result Object
}

func qualificationIntegrationAssert(t *testing.T, id string, want, got any) {
	t.Helper()
	status := "PASS"
	if Hash(want) != Hash(got) {
		status = "FAIL"
	}
	fmt.Println("W11_QUALIFICATION_ASSERTION " + string(Bytes(Object{"assertion_id": id, "expected": want, "actual": got, "status": status, "scope": "PUBLIC_FIXTURE_ONLY", "formal_holdout_accessed": false, "real_provider_called": false, "service_queried": false})))
	if status != "PASS" {
		t.Fatalf("%s: expected %v got %v", id, want, got)
	}
}
func qualificationSummary(t *testing.T) protectedstore.SafeSummary {
	t.Helper()
	raw, e := os.ReadFile("../../adapters/protectedstore/frozen_development.json")
	if e != nil {
		t.Fatal(e)
	}
	var verified struct {
		Keys []struct {
			Metrics protectedstore.FrozenDevelopmentCounts `json:"metrics"`
		} `json:"keys"`
	}
	if e = json.Unmarshal(raw, &verified); e != nil {
		t.Fatal(e)
	}
	hash := Digest([]byte(qualificationPrivateCanary))
	f := &protectedstore.FrozenRunSummary{DevelopmentHash: Digest(raw), Dataset: &protectedstore.Blob{Ticket: "ps1:" + hash[7:39], Project: "aede0678-7308-43dc-b9f2-cfe3d90cfdfb", Hash: hash, Size: int64(len(qualificationPrivateCanary)), MediaType: "application/json", MeasurementMode: "LIVE"}, FrozenAt: time.Now().Add(-time.Minute).UTC().Format(time.RFC3339Nano), ProjectID: "aede0678-7308-43dc-b9f2-cfe3d90cfdfb", RunState: "COMPLETED", GeneratorRevision: holdout.GeneratorRevision, RubricHash: holdout.RubricHash(), Threshold: holdout.Threshold, RequestBudget: 30, Qualification: "FAILED", AutomaticAuthority: "NONE", CostStatus: "UNKNOWN", BinaryHash: Digest([]byte("PUBLIC_FIXTURE_BINARY_NOT_ATTESTED"))}
	summary := protectedstore.SafeSummary{Schema: "researchos.protected-summary.v1", Status: "EXECUTION_REPORTED", Total: 30, Correct: 24, FalseAccept: 2, FalseReject: 2, Abstain: 2, CriticalFalseAccept: 2, MaximumMode: "ADVISORY", Frozen: f}
	batch, e := holdout.GeneratePublicFixture()
	if e != nil {
		t.Fatal(e)
	}
	for i, language := range []string{"zh", "zh-en"} {
		var positive, negative int64
		for _, c := range batch.Cases {
			if c.Scope.Language == language {
				if c.Expected == "ACCEPT" {
					positive++
				} else {
					negative++
				}
			}
		}
		f.Keys = append(f.Keys, protectedstore.FrozenKeyCounts{Scope: holdout.ScopeFor(language), DevelopmentCount: 30, Development: verified.Keys[i].Metrics, Planned: 15, StartedRequests: 15, RecordedInvocations: 15, HTTP200: 15, Correct: 12, FalseAccept: 1, FalseReject: 1, Abstain: 1, CriticalFalseAccept: 1, PositiveLabelCount: positive, NegativeLabelCount: negative, NonAbstainedAcceptCount: positive, NonAbstainedRejectCount: negative - 1, Baseline: protectedstore.FrozenBaselineCounts{Rule: "ALWAYS_REJECT", Correct: negative, FalseReject: positive}})
	}
	if e = summary.Validate(); e != nil {
		t.Fatal("public simulated summary invalid", e)
	}
	return summary
}
func newQualificationFixture(t *testing.T) *qualificationFixture {
	t.Helper()
	f := contextFixture(t)
	summary := qualificationSummary(t)
	tx, e := f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	defer tx.Rollback()
	author, e := authenticate(tx, f.token)
	if e != nil {
		t.Fatal(e)
	}
	raw, e := os.ReadFile("../../evaluation/development/jev-v2/dataset.json")
	if e != nil {
		t.Fatal(e)
	}
	if Digest(raw) != frozenDevelopmentDatasetHash {
		t.Fatal("frozen public development fixture hash drift")
	}
	u, e := f.s.upload(tx, author, f.project, raw)
	if e != nil {
		t.Fatal(e)
	}
	dev, e := f.s.seal(tx, author, f.project, Object{"run_id": nil, "kind": "REPORT", "evidence_kind": "OBSERVED", "measurement_mode": "LIVE", "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "application/json", "byte_size": len(raw), "input_refs": Empty(), "source_refs": Empty(), "produced_by": author.ID, "access_class": "PROJECT"})
	if e != nil {
		t.Fatal(e)
	}
	d := summary.Frozen.Dataset
	private := Merge(Base(f.project), Object{"run_id": nil, "kind": "REPORT", "evidence_kind": "OBSERVED", "measurement_mode": "LIVE", "content_hash": d.Hash, "storage_key": d.Ticket, "media_type": d.MediaType, "byte_size": d.Size, "input_refs": Empty(), "source_refs": Empty(), "produced_by": author.ID, "access_class": "VERIFIER_ONLY", "validity": "CURRENT", "sealed_at": Now()})
	if e = f.s.put(tx, "Artifact", private); e != nil {
		t.Fatal(e)
	}
	if e = tx.Commit(); e != nil {
		t.Fatal(e)
	}
	p := Principal{ID: "qualification-independent-verifier", Roles: []string{"VERIFIER"}, Grants: []Grant{{ProjectID: f.project, Restricted: true}}}
	if e = f.s.ProvisionPrincipal(context.Background(), p); e != nil {
		t.Fatal(e)
	}
	f.token, e = f.s.IssueCredential(context.Background(), p.ID, time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	tx, e = f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	defer tx.Rollback()
	p, e = authenticate(tx, f.token)
	if e != nil {
		t.Fatal(e)
	}
	scope, e := Decode(Bytes(holdout.ScopeFor("zh")))
	if e != nil {
		t.Fatal(e)
	}
	q, e := f.s.createQualification(tx, p, f.project, Object{"scope": scope, "dataset_artifact_ref": Ref(dev, "Artifact"), "holdout_artifact_ref": Ref(private, "Artifact"), "thresholds_hash": QualificationThresholdsHash(), "thresholds_frozen_at": summary.Frozen.FrozenAt, "total_case_count": 45, "holdout_case_count": 15, "label_basis": "OBJECTIVE", "measurement_mode": "LIVE", "expires_at": nil})
	if e != nil {
		t.Fatal(e)
	}
	state, e := singleton(tx, f.project, "ProjectState")
	if e != nil {
		t.Fatal(e)
	}
	if e = tx.Commit(); e != nil {
		t.Fatal(e)
	}
	return &qualificationFixture{f: f, q: q, dev: dev, private: private, proof: &preparedQualification{SubjectHash: Hash(q), PrincipalID: p.ID, Summary: summary}, acceptance: Object{"subject_ref": Ref(q, "Qualification"), "contract_hash": qualificationContract(q), "policy_revision": state["policy_revision"], "measurement_mode": "LIVE", "run_id": nil}}
}
func (q *qualificationFixture) accept(t *testing.T) (Object, error) {
	t.Helper()
	tx, e := q.f.db.Begin()
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	p, e := authenticate(tx, q.f.token)
	if e != nil {
		return nil, e
	}
	receipt, e := q.f.s.acceptQualification(tx, p, q.f.project, q.acceptance, q.proof)
	if e != nil {
		return nil, e
	}
	if e = tx.Commit(); e != nil {
		return nil, e
	}
	k := q.proof.Summary.Frozen.Keys[0]
	q.result = Object{"requested_maximum_mode": "BOUNDED_AUTO", "acceptance_id": receipt["id"], "test_receipt_refs": receipt["artifact_refs"], "critical_false_accept_count": k.CriticalFalseAccept, "false_accept_rate": float64(k.FalseAccept) / float64(k.Planned), "false_reject_rate": float64(k.FalseReject) / float64(k.PositiveLabelCount), "abstain_rate": float64(k.Abstain) / float64(k.Planned)}
	return receipt, nil
}
func (q *qualificationFixture) record() (Object, error) {
	tx, e := q.f.db.Begin()
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	p, e := authenticate(tx, q.f.token)
	if e != nil {
		return nil, e
	}
	result, e := q.f.s.recordQualificationResult(tx, p, q.f.project, Str(q.q, "id"), q.result, q.proof)
	if e != nil {
		return nil, e
	}
	return result, tx.Commit()
}
func qualificationStored(t *testing.T, q *qualificationFixture) (Object, int, int) {
	t.Helper()
	tx, e := q.f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	defer tx.Rollback()
	value, e := load(tx, q.f.project, "Qualification", Str(q.q, "id"))
	if e != nil {
		t.Fatal(e)
	}
	var receipts, leaks int
	if e = tx.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='AcceptanceReceipt'", q.f.project).Scan(&receipts); e != nil {
		t.Fatal(e)
	}
	if e = tx.QueryRow("SELECT count(*) FROM uploaded_content WHERE project=? AND (storage_key=? OR instr(CAST(bytes AS TEXT),?)>0)", q.f.project, q.proof.Summary.Frozen.Dataset.Ticket, qualificationPrivateCanary).Scan(&leaks); e != nil {
		t.Fatal(e)
	}
	return value, receipts, leaks
}
func TestW11QualificationTrustedAdmission(t *testing.T) {
	q := newQualificationFixture(t)
	receipt, e := q.accept(t)
	if e != nil {
		t.Fatal(e)
	}
	if e = q.f.s.Contracts.Validate("AcceptanceReceipt", receipt); e != nil {
		t.Fatal(e)
	}
	result, e := q.record()
	if e != nil {
		t.Fatal(e)
	}
	if e = q.f.s.Contracts.Validate("Qualification", result); e != nil {
		t.Fatal(e)
	}
	stored, n, leaks := qualificationStored(t, q)
	qualificationIntegrationAssert(t, "QUALIFICATION-SQLITE-FAILED-ADVISORY", []any{"FAILED", "ADVISORY", true, int64(2), 1, 0}, []any{stored["status"], stored["maximum_mode"], stored["jev_called"], mustQualificationRevision(t, stored), n, leaks})
	tx, e := q.f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	defer tx.Rollback()
	aggregate, e := q.f.s.artifactJSON(tx, q.f.project, Arr(receipt, "artifact_refs")[0].(map[string]any))
	if e != nil {
		t.Fatal(e)
	}
	qualificationIntegrationAssert(t, "QUALIFICATION-EXACT-SEALED-AGGREGATE", []bool{true, false}, []bool{Hash(aggregate) == Hash(q.proof.Summary), bytes.Contains(Bytes(aggregate), []byte(qualificationPrivateCanary))})
}
func mustQualificationRevision(t *testing.T, o Object) int64 {
	t.Helper()
	n, e := Num(o, "revision")
	if e != nil {
		t.Fatal(e)
	}
	return n
}
func TestW11QualificationRejectsDrift(t *testing.T) {
	for _, scenario := range []string{"client-stats", "scope", "threshold", "old-revision", "expired", "registrar", "grant-revoked", "credential-revoked", "dataset-bytes", "private-descriptor", "sealed-aggregate", "input-stale", "proof-principal", "summary-auto"} {
		t.Run(scenario, func(t *testing.T) {
			q := newQualificationFixture(t)
			post := scenario == "client-stats" || scenario == "sealed-aggregate"
			var receipt Object
			if post {
				var e error
				receipt, e = q.accept(t)
				if e != nil {
					t.Fatal(e)
				}
			}
			exec := func(query string, args ...any) {
				t.Helper()
				if _, e := q.f.db.Exec(query, args...); e != nil {
					t.Fatal(e)
				}
			}
			updateQ := func(field string, value any) {
				q.q[field] = value
				exec("UPDATE domain_objects SET body=? WHERE project=? AND kind='Qualification' AND id=?", string(Bytes(q.q)), q.f.project, q.q["id"])
				q.proof.SubjectHash = Hash(q.q)
				q.acceptance["contract_hash"] = qualificationContract(q.q)
			}
			var mutationErr error
			switch scenario {
			case "client-stats":
				q.result["false_accept_rate"] = 0
			case "scope":
				scope := copyObject(q.q["scope"].(map[string]any))
				scope["rubric_revision"] = "old-rubric"
				updateQ("scope", scope)
			case "threshold":
				updateQ("thresholds_hash", Digest([]byte("lowered-threshold")))
			case "old-revision":
				updateQ("revision", 2) // Deliberately retain the pre-update internal proof and VersionRef.
				q.proof.SubjectHash = Hash(Merge(copyObject(q.q), Object{"revision": 1}))
			case "expired":
				updateQ("expires_at", time.Now().Add(-time.Minute).UTC().Format(time.RFC3339Nano))
			case "registrar":
				exec("UPDATE auth_principals SET roles=? WHERE id=?", `["VERIFIER"]`, q.f.owner)
				exec("UPDATE auth_grants SET restricted=1 WHERE principal=? AND project=?", q.f.owner, q.f.project)
				var e error
				q.f.token, e = q.f.s.IssueCredential(context.Background(), q.f.owner, time.Minute)
				if e != nil {
					t.Fatal(e)
				}
				q.proof.PrincipalID = q.f.owner
			case "grant-revoked":
				exec("DELETE FROM auth_grants WHERE principal=? AND project=?", q.proof.PrincipalID, q.f.project)
			case "credential-revoked":
				if e := q.f.s.RevokePrincipal(context.Background(), q.proof.PrincipalID); e != nil {
					t.Fatal(e)
				}
			case "dataset-bytes":
				_, mutationErr = q.f.db.Exec("UPDATE uploaded_content SET bytes=? WHERE project=? AND storage_key=?", []byte(`{"tampered":true}`), q.f.project, q.dev["storage_key"])
			case "private-descriptor":
				_, mutationErr = q.f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.storage_key',?) WHERE project=? AND kind='Artifact' AND id=?", "ps1:00000000000000000000000000000000", q.f.project, q.private["id"])
			case "sealed-aggregate":
				ref := Arr(receipt, "artifact_refs")[0].(map[string]any)
				var key string
				if e := q.f.db.QueryRow("SELECT json_extract(body,'$.storage_key') FROM domain_objects WHERE project=? AND id=?", q.f.project, ref["id"]).Scan(&key); e != nil {
					t.Fatal(e)
				}
				_, mutationErr = q.f.db.Exec("UPDATE uploaded_content SET bytes=? WHERE project=? AND storage_key=?", []byte(`{"forged_safe_summary":true}`), q.f.project, key)
			case "input-stale":
				exec("UPDATE domain_objects SET body=json_set(body,'$.validity','STALE') WHERE project=? AND kind='Artifact' AND id=?", q.f.project, q.private["id"])
			case "proof-principal":
				q.proof.PrincipalID = "other-verifier"
			case "summary-auto":
				q.proof.Summary.MaximumMode = "BOUNDED_AUTO"
			}
			var e error
			if scenario == "dataset-bytes" || scenario == "private-descriptor" || scenario == "sealed-aggregate" {
				e = mutationErr
			} else if post {
				_, e = q.record()
			} else {
				_, e = q.accept(t)
			}
			if e != nil {
				t.Logf("rejected at admission or immutable storage: %v", e)
			}
			stored, count, leaks := qualificationStored(t, q)
			wantReceipts := 0
			if post {
				wantReceipts = 1
			}
			qualificationIntegrationAssert(t, "QUALIFICATION-REJECT-"+scenario, []any{true, "DRAFT", "ADVISORY", wantReceipts, 0}, []any{e != nil, stored["status"], stored["maximum_mode"], count, leaks})
		})
	}
}
