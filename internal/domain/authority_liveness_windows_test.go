//go:build windows

package domain

import (
	"context"
	"database/sql"
	"testing"
)

func TestCurrentAuthorityRootDirectAndDelegated(t *testing.T) {
	f, _, _, _ := localSetupFixture(t)
	ctx := context.Background()
	for _, p := range []Principal{{ID: "direct-verifier", Roles: []string{"VERIFIER"}, Grants: []Grant{{ProjectID: f.project}}}, {ID: "service-root", Roles: []string{"VERIFIER"}}, {ID: "service-middle", Roles: []string{"VERIFIER"}}, {ID: "service-child", Roles: []string{"VERIFIER"}, Grants: []Grant{{ProjectID: f.project}}}} {
		if e := f.s.ProvisionPrincipal(ctx, p); e != nil {
			t.Fatal(e)
		}
	}
	if e := f.s.RegisterExecutionIdentity(ctx, "service-middle", "service-root"); e != nil {
		t.Fatal(e)
	}
	if e := f.s.RegisterExecutionIdentity(ctx, "service-child", "service-middle"); e != nil {
		t.Fatal(e)
	}
	for principal, want := range map[string]string{"direct-verifier": "direct-verifier", "service-child": "service-root", "service-middle": "service-root", "service-root": "service-root"} {
		tx, e := f.db.Begin()
		if e != nil {
			t.Fatal(e)
		}
		got, e := currentAuthorityRoot(tx, principal)
		tx.Rollback()
		if e != nil || got != want {
			t.Fatalf("valid direct/delegated identity denied: %s %s %v", principal, got, e)
		}
	}
	if e := f.s.RevokePrincipal(ctx, "service-middle"); e != nil {
		t.Fatal(e)
	}
	tx, e := f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	defer tx.Rollback()
	if _, e = currentAuthorityRoot(tx, "service-child"); e == nil {
		t.Fatal("revoked intermediate retained child authority")
	}
}

func TestManagedVerifierAnchoredLineageFailsClosed(t *testing.T) {
	cases := map[string]func(*fixture) error{
		"root revoked":  func(f *fixture) error { return f.s.RevokePrincipal(context.Background(), "managed-root") },
		"child revoked": func(f *fixture) error { return f.s.RevokePrincipal(context.Background(), "managed-child") },
		"root identity missing": func(f *fixture) error {
			_, e := f.db.Exec(`DELETE FROM orchestration_identity WHERE principal='managed-root'`)
			return e
		},
		"child identity missing": func(f *fixture) error {
			_, e := f.db.Exec(`DELETE FROM orchestration_identity WHERE principal='managed-child'`)
			return e
		},
		"missing root principal": func(f *fixture) error {
			_, e := f.db.Exec(`UPDATE orchestration_identity SET root='unprovisioned',parent='unprovisioned' WHERE principal='managed-child'`)
			return e
		},
		"active root replacement": func(f *fixture) error {
			if e := f.s.ProvisionPrincipal(context.Background(), Principal{ID: "replacement-root", Roles: []string{"VERIFIER"}}); e != nil {
				return e
			}
			if _, e := f.db.Exec(`INSERT INTO orchestration_identity(principal,root,parent) VALUES('replacement-root','replacement-root',NULL)`); e != nil {
				return e
			}
			_, e := f.db.Exec(`UPDATE orchestration_identity SET root='replacement-root',parent='replacement-root' WHERE principal='managed-child'`)
			return e
		},
		"root parent cycle": func(f *fixture) error {
			_, e := f.db.Exec(`UPDATE orchestration_identity SET parent='managed-child' WHERE principal='managed-root'`)
			return e
		},
	}
	for name, mutate := range cases {
		t.Run(name, func(t *testing.T) {
			f, _, _, _ := localSetupFixture(t)
			ctx := context.Background()
			if e := f.s.ProvisionPrincipal(ctx, Principal{ID: "managed-root", Roles: []string{"VERIFIER"}}); e != nil {
				t.Fatal(e)
			}
			if e := f.s.ProvisionPrincipal(ctx, Principal{ID: "managed-child", Roles: []string{"VERIFIER"}, Grants: []Grant{{ProjectID: f.project}}}); e != nil {
				t.Fatal(e)
			}
			if e := f.s.RegisterExecutionIdentity(ctx, "managed-child", "managed-root"); e != nil {
				t.Fatal(e)
			}
			if _, e := f.s.RecordLocalRuntimeAdministration(ctx, f.token, f.project, Object{"schema": "researchos.local-runtime-administration.v1", "action": "EXPLICIT_QUALIFICATION_REQUEST", "service_root": "managed-root", "verifier_principal": "managed-child"}); e != nil {
				t.Fatal(e)
			}
			var anchor string
			if e := f.db.QueryRow(`SELECT body FROM idempotency WHERE operation='host:managed-verifier-lineage' AND principal='managed-child'`).Scan(&anchor); e != nil {
				t.Fatal(e)
			}
			// The production immutable/durable identity triggers already prevent
			// these edits. Only this disposable fixture disables those storage
			// guards to exercise fail-closed reads of missing/corrupt lineage.
			// Root/child revocation cases still use the real RevokePrincipal API.
			if name != "root revoked" && name != "child revoked" {
				for _, statement := range []string{`DROP TRIGGER orchestration_identity_immutable`, `DROP TRIGGER orchestration_identity_durable`, `PRAGMA foreign_keys=OFF`} {
					if _, e := f.db.Exec(statement); e != nil {
						t.Fatal(e)
					}
				}
			}
			if e := mutate(f); e != nil {
				t.Fatal(e)
			}
			tx, e := f.db.Begin()
			if e != nil {
				t.Fatal(e)
			}
			if _, e = currentAuthorityRoot(tx, "managed-child"); e == nil {
				tx.Rollback()
				t.Fatal("managed lineage defect accepted or silently treated as direct identity")
			}
			tx.Rollback()
			var retained string
			if e = f.db.QueryRow(`SELECT body FROM idempotency WHERE operation='host:managed-verifier-lineage' AND principal='managed-child'`).Scan(&retained); e != nil || retained != anchor {
				t.Fatal("original immutable lineage anchor changed")
			}
		})
	}
}

func TestQualificationPurposeChecksRevokedVerifierRoot(t *testing.T) {
	r, receipt, log := acceptedRuntimeQualification(t)
	f := r.f
	ctx := context.Background()
	if e := f.s.ProvisionPrincipal(ctx, Principal{ID: "qualified-service-root", Roles: []string{"VERIFIER"}}); e != nil {
		t.Fatal(e)
	}
	if e := f.s.RegisterExecutionIdentity(ctx, Str(receipt, "verifier_principal_id"), "qualified-service-root"); e != nil {
		t.Fatal(e)
	}
	qualified := f.expect(200, "POST", f.path("/runtimes/"+Str(r.registration, "id")+"/qualify"), ID(), testTag(r.registration), qualificationFixBody(receipt, log))
	if e := f.s.RevokePrincipal(ctx, "qualified-service-root"); e != nil {
		t.Fatal(e)
	}
	if e := qualificationFixAdmission(r, qualified, []any{"start"}); e == nil {
		t.Fatal("AVAILABLE used revoked signing root")
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		original, e := load(tx, f.project, "AcceptanceReceipt", Str(receipt, "id"))
		if e != nil {
			return e
		}
		if Hash(original) != Hash(receipt) {
			t.Fatal("original receipt mutated")
		}
		return nil
	})
}

func TestAcceptanceFinalizeRechecksVerifierRootWithoutGrantInheritance(t *testing.T) {
	for _, phase := range []string{"root_revoked_after_prepare", "child_grant_removed_after_prepare"} {
		t.Run(phase, func(t *testing.T) {
			r := runtimeSetupMode(t, "FIXTURE")
			f := r.f
			ctx := context.Background()
			output := r.seal([]byte(`{"result":"verified"}`))
			observation := r.observation("SETTLED", true)
			observation["artifacts"] = []any{Object{"path": "result.json", "content_hash": output["content_hash"], "byte_size": output["byte_size"]}}
			r.observe(observation)
			r.call("/report", r.report([]any{output["id"]}, 0), 200)
			f.token = r.ownerToken
			r.task = f.read("tasks", Str(r.task, "id"))
			request := (&orchestrationFixture{f: f, owner: r.ownerToken}).acceptance(r, output)
			const child = "orchestration-independent-verifier"
			if e := f.s.ProvisionPrincipal(ctx, Principal{ID: "finalize-service-root", Roles: []string{"VERIFIER"}, Grants: []Grant{{ProjectID: f.project}}}); e != nil {
				t.Fatal(e)
			}
			if e := f.s.RegisterExecutionIdentity(ctx, child, "finalize-service-root"); e != nil {
				t.Fatal(e)
			}
			prepared, e := f.s.prepareTaskAcceptance(ctx, f.token, f.project, request)
			if e != nil || prepared.verdict != "PASS" {
				t.Fatalf("valid prepared acceptance: %v", e)
			}
			if phase == "root_revoked_after_prepare" {
				e = f.s.RevokePrincipal(ctx, "finalize-service-root")
			} else {
				_, e = f.db.Exec(`DELETE FROM auth_grants WHERE principal=?`, child)
			}
			if e != nil {
				t.Fatal(e)
			}
			tx, e := f.db.Begin()
			if e != nil {
				t.Fatal(e)
			}
			principal, e := authenticate(tx, f.token)
			if e != nil {
				tx.Rollback()
				t.Fatal(e)
			}
			_, e = f.s.acceptTask(tx, principal, f.project, request, prepared, ID())
			tx.Rollback()
			if e == nil {
				t.Fatal("cached computation bypassed current root or inherited root grant")
			}
			var count int
			if e = f.db.QueryRow(`SELECT count(*) FROM domain_objects WHERE kind='AcceptanceReceipt'`).Scan(&count); e != nil || count != 0 {
				t.Fatal("refused finalization wrote acceptance receipt")
			}
			t.Log("prepared deterministic PASS retained; final authority transaction denied; root grants did not substitute for child grants")
		})
	}
}
