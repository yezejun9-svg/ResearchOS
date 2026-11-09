//go:build windows

package qualificationmaintenancejournal

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func qualificationJournalFixture(t *testing.T) (string, JournalPlan, []byte) {
	t.Helper()
	root := t.TempDir()
	if err := createPrivateDirectory(filepath.Join(root, "host")); err != nil {
		t.Fatal(err)
	}
	plan := JournalPlan{Schema: qualificationPlanSchema, OperationID: "00112233445566778899aabbccddeeff",
		DataRoot: root, Database: filepath.Join(root, "researchos.sqlite")}
	core := map[string]any{"schema": "fixture"}
	subject := map[string]any{"project_id": "fixture"}
	source := map[string]any{"source": "fixture"}
	proof := map[string]any{"native": map[string]any{"kind": "fixture"}, "model_binding": map[string]any{"kind": "fixture"}}
	full := map[string]any{
		"schema":       "researchos.qualification-failure-maintenance-full-plan.v1",
		"operation_id": plan.OperationID, "data_root": plan.DataRoot, "database": plan.Database,
		"core": core, "subject": subject, "source": source, "proof": proof,
		"before_census": map[string]any{"rows": 0}, "before_run": map[string]any{}, "before_state": map[string]any{},
		"before_dispatch": map[string]any{}, "before_protected_sha256": "p", "before_residual_sha256": "r",
		"artifact": map[string]any{}, "impact_link": map[string]any{}, "run": map[string]any{},
		"project_state": map[string]any{}, "event": map[string]any{}, "observation": map[string]any{},
		"dispatch_sequence": int64(1), "proof_bytes": []byte("fixture"), "outcome_hash": digest([]byte("outcome")),
	}
	mustHash := func(v any) string {
		h, e := hash(v)
		if e != nil {
			t.Fatal(e)
		}
		return h
	}
	plan.PlanHash = mustHash(core)
	plan.SubjectHash = mustHash(subject)
	plan.EvidenceHash = mustHash(map[string]any{"source": source, "native": proof["native"], "model": proof["model_binding"]})
	plan.BeforeHash = mustHash(map[string]any{"census": full["before_census"], "run": full["before_run"], "state": full["before_state"],
		"dispatch": full["before_dispatch"], "protected": full["before_protected_sha256"], "residual": full["before_residual_sha256"]})
	plan.AfterHash = mustHash(map[string]any{"artifact": full["artifact"], "impact_link": full["impact_link"], "run": full["run"],
		"state": full["project_state"], "event": full["event"], "observation": full["observation"],
		"dispatch_sequence": full["dispatch_sequence"], "upload_hash": digest([]byte("fixture")), "outcome_hash": full["outcome_hash"]})
	plan.FullPlan, _ = json.Marshal(full)
	raw, err := json.Marshal(plan)
	if err != nil {
		t.Fatal(err)
	}
	return root, plan, raw
}

func TestQualificationJournalPendingAndAbort(t *testing.T) {
	root, plan, raw := qualificationJournalFixture(t)
	planDigest, err := StartQualification(root, raw)
	if err != nil {
		t.Fatal(err)
	}
	if err := CheckOrdinary(root); err == nil {
		t.Fatal("BEGIN must block ordinary acquisition")
	}
	permit, status, err := OpenOwnInspection(root, QualificationNamespace, plan.OperationID, planDigest)
	if err != nil || status.State != "BEGIN" || status.Terminal || status.Applied {
		t.Fatalf("own BEGIN: %#v %v", status, err)
	}
	if _, err := permit.Check(root); err != nil {
		t.Fatal(err)
	}
	if _, _, err := OpenOwnInspection(root, ReplacementNamespace, plan.OperationID, planDigest); err == nil {
		t.Fatal("replacement own permit exempted pending qualification operation")
	}
	if err := AppendQualification(root, plan.OperationID, planDigest, "CLASSIFIED_NOT_APPLIED", ""); err != nil {
		t.Fatal(err)
	}
	if err := AppendQualification(root, plan.OperationID, planDigest, "ABORTED", ""); err != nil {
		t.Fatal(err)
	}
	if err := CheckOrdinary(root); err != nil {
		t.Fatal(err)
	}
	if _, err := StartQualification(root, raw); err == nil {
		t.Fatal("existing operation must never be overwritten")
	}
}

func TestQualificationJournalUnknownInventoryBlocks(t *testing.T) {
	root, plan, raw := qualificationJournalFixture(t)
	planDigest, err := StartQualification(root, raw)
	if err != nil {
		t.Fatal(err)
	}
	dir := filepath.Join(root, "host", QualificationNamespace, plan.OperationID)
	if err := createPrivateFile(filepath.Join(dir, "unexpected.json"), []byte(`{}`)); err != nil {
		t.Fatal(err)
	}
	if err := CheckOrdinary(root); err == nil {
		t.Fatal("unknown event must block ordinary acquisition")
	}
	if _, _, err := OpenOwnInspection(root, QualificationNamespace, plan.OperationID, planDigest); err == nil {
		t.Fatal("own permit must not exempt unknown event")
	}
	if _, err := os.Lstat(filepath.Join(dir, "unexpected.json")); err != nil {
		t.Fatal(err)
	}
}

func TestQualificationJournalFullPlanHashesFailClosed(t *testing.T) {
	root, plan, _ := qualificationJournalFixture(t)
	for _, change := range []func(map[string]any){
		func(full map[string]any) { full["operation_id"] = "ffeeddccbbaa99887766554433221100" },
		func(full map[string]any) { full["core"] = map[string]any{"schema": "changed"} },
		func(full map[string]any) { full["before_protected_sha256"] = "changed" },
		func(full map[string]any) { full["proof_bytes"] = []byte("different") },
		func(full map[string]any) { full["source"] = map[string]any{"source": "changed"} },
	} {
		var full map[string]any
		if err := json.Unmarshal(plan.FullPlan, &full); err != nil {
			t.Fatal(err)
		}
		change(full)
		tampered := plan
		tampered.FullPlan, _ = json.Marshal(full)
		raw, _ := json.Marshal(tampered)
		if _, err := StartQualification(root, raw); err == nil {
			t.Fatal("mismatched full plan accepted")
		}
	}
}

func TestQualificationJournalRejectsWrongAppliedOutcome(t *testing.T) {
	root, plan, raw := qualificationJournalFixture(t)
	planDigest, err := StartQualification(root, raw)
	if err != nil {
		t.Fatal(err)
	}
	if err = AppendQualification(root, plan.OperationID, planDigest, "DB_COMMITTED_OBSERVED", digest([]byte("wrong"))); err == nil {
		t.Fatal("wrong applied outcome appended")
	}
	_, status, err := OpenOwnInspection(root, QualificationNamespace, plan.OperationID, planDigest)
	if err != nil || status.State != "BEGIN" {
		t.Fatalf("wrong outcome changed journal: %#v %v", status, err)
	}
}
