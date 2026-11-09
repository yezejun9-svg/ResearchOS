package domain

import (
	"context"
	"testing"
)

func qualificationFixBody(receipt, log Object) Object {
	return Object{"qualification_ids": []any{receipt["id"]}, "supports_resume": false, "resume_evidence_ref": nil, "receipt_artifact_ref": Ref(log, "Artifact")}
}

func qualificationFixAdmission(r *runtimeFixture, runtime Object, capabilities []any) error {
	tx, err := r.f.db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	_, err = r.f.s.currentRuntimeAdmission(tx, r.f.project, nil, runtime, capabilities, "claim")
	return err
}

func TestRuntimeQualificationFixCallerRoot(t *testing.T) {
	for _, related := range []string{"owner", "executor"} {
		t.Run(related, func(t *testing.T) {
			r, receipt, log := acceptedRuntimeQualification(t)
			f := r.f
			f.switchPrincipal("qualification-caller", []string{"VERIFIER"})
			root := f.owner
			if related == "executor" {
				root = r.executor
			}
			if err := f.s.RegisterExecutionIdentity(context.Background(), "qualification-caller", root); err != nil {
				t.Fatal(err)
			}
			status, _, _ := f.request("POST", f.path("/runtimes/"+Str(r.registration, "id")+"/qualify"), ID(), testTag(r.registration), qualificationFixBody(receipt, log))
			if status != 403 {
				t.Fatalf("caller shares %s root: HTTP %d, want 403", related, status)
			}
		})
	}
}

func TestRuntimeQualificationFixCurrentAuthorRoot(t *testing.T) {
	for _, phase := range []string{"qualify", "use"} {
		t.Run(phase, func(t *testing.T) {
			r, receipt, log := acceptedRuntimeQualification(t)
			f := r.f
			path := f.path("/runtimes/" + Str(r.registration, "id") + "/qualify")
			var qualified Object
			if phase == "use" {
				qualified = f.expect(200, "POST", path, ID(), testTag(r.registration), qualificationFixBody(receipt, log))
			}
			if err := f.s.RegisterExecutionIdentity(context.Background(), f.owner, Str(receipt, "verifier_principal_id")); err != nil {
				t.Fatal(err)
			}
			if phase == "qualify" {
				status, _, _ := f.request("POST", path, ID(), testTag(r.registration), qualificationFixBody(receipt, log))
				if status != 403 {
					t.Fatalf("current author root changed: HTTP %d, want 403", status)
				}
			} else if err := qualificationFixAdmission(r, qualified, []any{"start"}); err == nil {
				t.Fatal("current author root changed but admission passed")
			}
		})
	}
}

func TestRuntimeQualificationFixCapabilityScope(t *testing.T) {
	r, receipt, log := acceptedRuntimeQualification(t)
	f := r.f
	qualified := f.expect(200, "POST", f.path("/runtimes/"+Str(r.registration, "id")+"/qualify"), ID(), testTag(r.registration), qualificationFixBody(receipt, log))
	if err := qualificationFixAdmission(r, qualified, []any{"start"}); err != nil {
		t.Fatalf("observed start was denied: %v", err)
	}
	if err := qualificationFixAdmission(r, qualified, []any{"cancel_job_tree"}); err == nil {
		t.Fatal("unproven cancel_job_tree was admitted")
	}
}

func TestRuntimeQualificationFixCurrentRegistration(t *testing.T) {
	r, receipt, log := acceptedRuntimeQualification(t)
	f := r.f
	qualified := f.expect(200, "POST", f.path("/runtimes/"+Str(r.registration, "id")+"/qualify"), ID(), testTag(r.registration), qualificationFixBody(receipt, log))
	if err := qualificationFixAdmission(r, qualified, []any{"start"}); err != nil {
		t.Fatalf("current registration was denied: %v", err)
	}
	if _, err := f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.status','REVOKED') WHERE project=? AND kind='RuntimeRegistration' AND id=?", f.project, qualified["id"]); err != nil {
		t.Fatal(err)
	}
	if err := qualificationFixAdmission(r, qualified, []any{"start"}); err == nil {
		t.Fatal("stale AVAILABLE snapshot bypassed revoked registration")
	}
}
