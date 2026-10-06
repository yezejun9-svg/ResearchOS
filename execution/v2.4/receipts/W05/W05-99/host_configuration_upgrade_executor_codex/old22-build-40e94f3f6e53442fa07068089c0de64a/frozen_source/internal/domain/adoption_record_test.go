package domain

// W08-01: the reuse decision has to be sealed against artifacts that actually exist, and only then may it promote the
// REUSE_DECISION stage. A decision that cites a plausible but absent artifact must leave the stage untouched, because a
// completed stage is the claim the CLI and the Desktop both show the user.

import (
	"context"
	"database/sql"
	"strings"
	"testing"
)

func sealTestArtifact(t *testing.T, f *fixture, project, body string) Object {
	t.Helper()
	ctx := context.Background()
	tx, e := f.db.BeginTx(ctx, nil)
	if e != nil {
		t.Fatal(e)
	}
	p, e := authenticate(tx, f.token)
	if e != nil {
		tx.Rollback()
		t.Fatal(e)
	}
	b := []byte(body)
	u, e := f.s.upload(tx, p, project, b)
	if e != nil {
		tx.Rollback()
		t.Fatal(e)
	}
	sealed, e := f.s.seal(tx, p, project, Object{"run_id": nil, "kind": "MANIFEST", "evidence_kind": "GENERATED",
		"measurement_mode": "FIXTURE", "content_hash": u["content_hash"], "storage_key": u["storage_key"],
		"media_type": "application/json", "byte_size": len(b), "input_refs": []any{}, "source_refs": Empty(),
		"produced_by": p.ID, "access_class": "PROJECT"})
	if e != nil {
		tx.Rollback()
		t.Fatal(e)
	}
	// The seal only counts once the transaction is committed; a rolled-back seal would leave every later citation of
	// this id failing for a reason that has nothing to do with the guard under test.
	if e := tx.Commit(); e != nil {
		t.Fatal(e)
	}
	var raw string
	if e := f.db.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind=? AND id=?", project,
		"Artifact", Str(sealed, "id")).Scan(&raw); e != nil {
		t.Fatalf("the sealed artifact %s is not readable after committing: %v", Str(sealed, "id"), e)
	}
	return sealed
}

func reuseDecisionFor(project string, inventory, research, evidence, adoption Object) Object {
	return Object{
		"project_id": project, "capability_id": "cap-1", "input_revision": float64(1),
		"local_inventory_artifact_id": Str(inventory, "id"),
		"research_artifact_ids":       []any{Str(research, "id")},
		"decision":                    "ADOPT_UPSTREAM",
		"chosen_source":               "https://github.com/paperclipai/paperclip",
		"source_revision":             "commit-abc",
		"license_ref":                 Str(evidence, "id"),
		"patch_scope":                 []any{"README.md"},
		"rejected_alternatives":       []any{Str(research, "id")},
		"remaining_gap":               "",
		"evidence_artifact_ids":       []any{Str(evidence, "id")},
		"adoption_decision_ref":       Ref(adoption, "Artifact"),
	}
}

func readStageRow(t *testing.T, f *fixture, project, stage string) (Object, bool) {
	t.Helper()
	var raw string
	err := f.db.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind=? AND id=?", project,
		KindBootstrapStage, "stage-"+project+"-"+strings.ToLower(stage)).Scan(&raw)
	if err == sql.ErrNoRows {
		return nil, false
	}
	if err != nil {
		t.Fatal(err)
	}
	o, e := Decode([]byte(raw))
	if e != nil {
		t.Fatal(e)
	}
	return o, true
}

func writeBootstrapStage(t *testing.T, f *fixture, project, stage, status string) Object {
	t.Helper()
	ctx := context.Background()
	tx, e := f.db.BeginTx(ctx, nil)
	if e != nil {
		t.Fatal(e)
	}
	id := "stage-" + project + "-" + strings.ToLower(stage)
	rev, e := f.s.nextRevision(ctx, tx, project, KindBootstrapStage, id)
	if e != nil {
		tx.Rollback()
		t.Fatal(e)
	}
	row := Object{"id": id, "project_id": project, "stage": stage, "status": status,
		"inventory_artifact_ref": nil, "file_failures": Empty(), "observed_at": Now(), "revision": rev}
	if e := f.s.putOpaque(ctx, tx, project, KindBootstrapStage, id, row); e != nil {
		tx.Rollback()
		t.Fatal(e)
	}
	if e := tx.Commit(); e != nil {
		t.Fatal(e)
	}
	return row
}

func TestW0801RecordReuseDecisionSealsAndPromotes(t *testing.T) {
	f, _, _ := sourceProject(t)
	ctx := context.Background()
	inventory := sealTestArtifact(t, f, f.project, "local inventory")
	research := sealTestArtifact(t, f, f.project, "research notes")
	evidence := sealTestArtifact(t, f, f.project, "upstream licence text")
	adoption := sealTestArtifact(t, f, f.project, "adoption decision document")

	out, e := f.s.RecordReuseDecision(ctx, f.token, f.project,
		reuseDecisionFor(f.project, inventory, research, evidence, adoption), "FIXTURE")
	if e != nil {
		t.Fatalf("a decision backed by real artifacts was refused: %v", e)
	}
	if Str(out, "decision") != "ADOPT_UPSTREAM" {
		t.Fatalf("the promoted decision changed: %+v", out)
	}
	row, present := readStageRow(t, f, f.project, StageReuseDecision)
	if !present {
		t.Fatal("no REUSE_DECISION stage row after a promoted decision")
	}
	if Str(row, "status") != StageCompleted {
		t.Fatalf("the stage was not promoted: %+v", row)
	}
	ref, isObject := out["adoption_artifact"].(Object)
	if !isObject {
		t.Fatalf("the writer did not return the sealed decision reference: %+v", out)
	}
	if Str(row, "inventory_artifact_ref") != Str(ref, "id") {
		t.Fatalf("the promoted stage points somewhere else: stage %+v vs reference %+v", row, ref)
	}
	// The reader needs the research stage too: a promotion is only presentable once the stage before it actually
	// produced a row. This writes it through the product's own stage writer rather than inventing a shape.
	writeBootstrapStage(t, f, f.project, StageResearch, StageCompleted)
	researchRow, researchPresent := readStageRow(t, f, f.project, StageResearch)
	if !researchPresent {
		t.Fatal("the research stage row was not written")
	}
	turns, e := ProjectStages([]Object{researchRow, row}, reuseDecisionFor(f.project, inventory, research, evidence, adoption))
	if e != nil {
		t.Fatalf("the projection rejected a decision the writer accepted: %v", e)
	}
	if got := statusOf(t, turns, StageReuseDecision); got.Status != StageCompleted || got.EvidenceRef == nil {
		t.Fatalf("projection disagrees with the stored promotion: %+v", got)
	}
}

func TestW0801ReaderRefusesThePromotionWhileResearchNeverRan(t *testing.T) {
	// 反例3 on stored rows: the writer validated the payload and its artifacts, but this project never ran
	// project.bootstrap, so there is no RESEARCH row at all. The projection the CLI and Desktop read from must refuse
	// to present the promotion rather than show a decision that skipped the reuse gate.
	f, _, _ := sourceProject(t)
	ctx := context.Background()
	inventory := sealTestArtifact(t, f, f.project, "local inventory")
	research := sealTestArtifact(t, f, f.project, "research notes")
	evidence := sealTestArtifact(t, f, f.project, "upstream licence text")
	adoption := sealTestArtifact(t, f, f.project, "adoption decision document")
	b := reuseDecisionFor(f.project, inventory, research, evidence, adoption)
	if _, e := f.s.RecordReuseDecision(ctx, f.token, f.project, b, "FIXTURE"); e != nil {
		t.Fatalf("a decision backed by real artifacts was refused: %v", e)
	}
	row, present := readStageRow(t, f, f.project, StageReuseDecision)
	if !present {
		t.Fatal("the writer did not record the promotion this test is about")
	}
	_, e := ProjectStages([]Object{row}, b)
	if e == nil {
		t.Fatal("a completed reuse decision was presented with no research stage at all")
	}
	if !strings.Contains(e.Error(), "while RESEARCH is ABSENT") {
		t.Fatalf("refusal does not name the missing stage: %v", e)
	}
}

func TestW0801RecordReuseDecisionRefusesACitedArtifactThatDoesNotExist(t *testing.T) {
	f, _, _ := sourceProject(t)
	ctx := context.Background()
	inventory := sealTestArtifact(t, f, f.project, "local inventory")
	research := sealTestArtifact(t, f, f.project, "research notes")
	evidence := sealTestArtifact(t, f, f.project, "upstream licence text")
	adoption := sealTestArtifact(t, f, f.project, "adoption decision document")

	b := reuseDecisionFor(f.project, inventory, research, evidence, adoption)
	b["research_artifact_ids"] = []any{"art-that-was-never-sealed"}
	if _, e := f.s.RecordReuseDecision(ctx, f.token, f.project, b, "FIXTURE"); e == nil {
		t.Fatal("a decision citing a non-existent research artifact was accepted")
	}
	if row, present := readStageRow(t, f, f.project, StageReuseDecision); present && Str(row, "status") == StageCompleted {
		t.Fatal("the stage was promoted even though the decision was refused")
	}
}

func TestW0801RecordReuseDecisionRejectsAnUnknownMeasurementMode(t *testing.T) {
	f, _, _ := sourceProject(t)
	b := reuseDecisionFor(f.project, sealTestArtifact(t, f, f.project, "i"), sealTestArtifact(t, f, f.project, "r"),
		sealTestArtifact(t, f, f.project, "e"), sealTestArtifact(t, f, f.project, "a"))
	if _, e := f.s.RecordReuseDecision(context.Background(), f.token, f.project, b, "LIVE_QUALIFIED"); e == nil {
		t.Fatal("an unrecognised measurement mode was accepted")
	}
	if _, e := f.s.RecordReuseDecision(context.Background(), f.token, "other-project", b, "FIXTURE"); e == nil {
		t.Fatal("a decision naming another project was accepted")
	}
}
