//go:build windows

package domain

import (
	"context"
	"database/sql"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"
)

// Synthetic files exercise offline hash/provenance gates only. No fixture
// executable is started and these tests confer no LIVE runtime qualification.
func localSetupFixture(t *testing.T) (*fixture, *ClientService, RuntimeSetupCandidate, RuntimeSetupAssets) {
	t.Helper()
	f := contextFixture(t)
	client := "local-setup-client"
	s, sid, _ := handlerTypedSession(t, f, client)
	configure := &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: &client, ProjectID: &f.project, SessionID: &sid, ExpectedRevision: revPtr(1), WriterEpoch: revPtr(1), Method: strptr("host.configure"), Payload: Bytes(Object{"config_revision": 2, "provider_id": "ollama", "base_url": "http://127.0.0.1:1/v1", "model_id": "qwen3:4b-instruct", "credential_ref": nil})}
	r, _ := handlerCommand(t, f, s, configure)
	if deref(r.Status) != "COMPLETED" {
		t.Fatalf("configure: %s", Bytes(r))
	}
	root := t.TempDir()
	node, bundle := []byte("MZ-offline-fixture-never-executed"), []byte("offline fixture bundle; never executed")
	a := RuntimeSetupAssets{Executable: filepath.Join(root, "node.exe"), BundleFile: filepath.Join(root, "mu-worker.mjs"), BuildHash: Digest(node), BundleHash: Digest(bundle)}
	if err := os.WriteFile(a.Executable, node, 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(a.BundleFile, bundle, 0600); err != nil {
		t.Fatal(err)
	}
	return f, s, RuntimeSetupCandidate{ProjectID: f.project, SessionID: sid, PrincipalID: f.owner, ModelRef: Str(r.Result, "model_config_ref")}, a
}

func localSetupCensus(t *testing.T, f *fixture) string {
	t.Helper()
	var objects, plans, bindings, runs, effects, dispatches, ledger int
	for _, q := range []struct {
		sql    string
		target *int
	}{
		{"SELECT count(*) FROM domain_objects", &objects}, {"SELECT count(*) FROM runtime_qualification_plans", &plans}, {"SELECT count(*) FROM runtime_bindings", &bindings}, {"SELECT count(*) FROM domain_objects WHERE kind='Run'", &runs}, {"SELECT count(*) FROM resource_effects", &effects}, {"SELECT count(*) FROM runtime_dispatches", &dispatches}, {"SELECT count(*) FROM domain_objects WHERE kind='BudgetLedgerEntry'", &ledger},
	} {
		if err := f.db.QueryRow(q.sql).Scan(q.target); err != nil {
			t.Fatal(err)
		}
	}
	return string(Bytes([]any{objects, plans, bindings, runs, effects, dispatches, ledger}))
}

func TestLocalRuntimeSetupAtomicOfflineAndRecovery(t *testing.T) {
	f, client, candidate, assets := localSetupFixture(t)
	ctx := context.Background()
	candidates, err := f.s.RuntimeSetupCandidates(ctx, configurationFixtureOwner)
	if err != nil || len(candidates) != 1 || candidates[0] != candidate {
		t.Fatalf("committed candidate: %v %v", candidates, err)
	}
	prepared, err := f.s.PrepareClientRuntime(ctx, f.token, candidate, assets, client.Doc, client.ConfigurationAuthority)
	if err != nil {
		t.Fatal(err)
	}
	reg := f.read("runtimes", prepared.RuntimeID)
	task := f.read("tasks", prepared.TaskID)
	if reg["status"] != "REGISTERED" || reg["supports_resume"] != false || len(Arr(reg, "qualification_ids")) != 0 || reg["credential_ref"] != nil || task["status"] != "DRAFT" || task["active_run_id"] != nil {
		t.Fatalf("preparation granted execution: %s %s", Bytes(reg), Bytes(task))
	}
	var activity int
	if err = f.db.QueryRow(`SELECT (SELECT count(*) FROM runtime_dispatches)+(SELECT count(*) FROM resource_effects)+(SELECT count(*) FROM domain_objects WHERE kind IN ('Run','AcceptanceReceipt','BudgetLedgerEntry'))`).Scan(&activity); err != nil || activity != 0 {
		t.Fatalf("offline activity=%d err=%v", activity, err)
	}
	before := localSetupCensus(t, f)
	again, err := f.s.PrepareClientRuntime(ctx, f.token, candidate, assets, client.Doc, client.ConfigurationAuthority)
	if err != nil || again.RuntimeID != prepared.RuntimeID || again.TaskID != prepared.TaskID || localSetupCensus(t, f) != before {
		t.Fatalf("non-idempotent preparation: %v", err)
	}
	ids, tokens := map[string]string{}, map[string]string{}
	for _, role := range []string{"SCHEDULER", "EXECUTOR"} {
		ids[role], err = f.s.EnsureRuntimeSetupPrincipal(ctx, f.token, f.project, role)
		if err != nil {
			t.Fatal(err)
		}
		tokens[role], err = f.s.IssueCredential(ctx, ids[role], time.Minute)
		if err != nil {
			t.Fatal(err)
		}
		var root string
		if err = f.db.QueryRow(`SELECT root FROM orchestration_identity WHERE principal=?`, ids[role]).Scan(&root); err != nil || root != f.owner {
			t.Fatalf("independence fabricated: %s %v", root, err)
		}
	}
	makeCoordinator := func() *RuntimeCoordinator {
		return &RuntimeCoordinator{service: f.s, config: RuntimeCoordinatorConfig{ClientSchema: client.Doc, ConfigurationAuthority: client.ConfigurationAuthority}}
	}
	c := makeCoordinator()
	if err = c.InstallPreparedRuntime(ctx, prepared, ids["EXECUTOR"], tokens["EXECUTOR"], tokens["SCHEDULER"], assets); err != nil {
		t.Fatal(err)
	}
	if len(c.config.Routes) != 0 || len(c.runtimeRoutes()) != 1 || len(c.runtimeProviders()) != 2 {
		t.Fatal("route publication mutated static config")
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		runtime, profile, e := c.sessionModel(tx, f.project, candidate.ModelRef)
		if e != nil {
			return e
		}
		if profile["max_cost"] != nil || profile["credential_revision"] != "none" {
			t.Fatal("unknown cost or local credentials changed")
		}
		if _, e = f.s.currentRuntimeAdmission(tx, f.project, task, runtime, []any{"start"}, "session.send"); e == nil {
			t.Fatal("REGISTERED runtime admitted")
		}
		return nil
	})
	// A fresh coordinator restores the same persistent plan rather than creating
	// another runtime. Its empty in-memory route state does not imply permission.
	restored := makeCoordinator()
	if err = restored.InstallPreparedRuntime(ctx, again, ids["EXECUTOR"], tokens["EXECUTOR"], tokens["SCHEDULER"], assets); err != nil || len(restored.runtimeRoutes()) != 1 {
		t.Fatalf("restore route: %v", err)
	}
	var wg sync.WaitGroup
	for n := 0; n < 4; n++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for i := 0; i < 100; i++ {
				_ = c.runtimeRoutes()
				_ = c.runtimeProviders()
				_ = c.schedulerCredential(f.project)
			}
		}()
	}
	for n := 0; n < 5; n++ {
		if err = c.InstallPreparedRuntime(ctx, prepared, ids["EXECUTOR"], tokens["EXECUTOR"], tokens["SCHEDULER"], assets); err != nil {
			t.Fatal(err)
		}
	}
	wg.Wait()
	t.Log("offline registered=1 sealed_profile=1 plan=1 run=0 model_calls=0 acceptance=0 restored_exact_binding=true snapshot_readers=4")
}

func TestLocalRuntimeSetupRefusalsAndAtomicBudget(t *testing.T) {
	for _, name := range []string{"foreign-principal", "wrong-model", "missing-assets", "capped-budget"} {
		t.Run(name, func(t *testing.T) {
			f, client, candidate, assets := localSetupFixture(t)
			switch name {
			case "foreign-principal":
				candidate.PrincipalID = "foreign"
			case "wrong-model":
				candidate.ModelRef = "mc-" + strings.Repeat("f", 32)
			case "missing-assets":
				assets.BundleFile = filepath.Join(t.TempDir(), "missing.mjs")
			case "capped-budget":
				sourceTx(t, f.db, func(tx *sql.Tx) error {
					policy, e := singleton(tx, "", "BudgetPolicy")
					if e != nil {
						return e
					}
					if e = bump(policy); e != nil {
						return e
					}
					policy["mode"] = "CAPPED"
					policy["cap"] = dollars("1")
					policy["enforcement"] = "ESTIMATED"
					return f.s.put(tx, "BudgetPolicy", policy)
				})
			}
			before := localSetupCensus(t, f)
			_, err := f.s.PrepareClientRuntime(context.Background(), f.token, candidate, assets, client.Doc, client.ConfigurationAuthority)
			if err == nil || localSetupCensus(t, f) != before {
				t.Fatalf("refusal not atomic: %v", err)
			}
		})
	}
}

func TestLocalRuntimeSetupAssetDriftAndRevocation(t *testing.T) {
	f, client, candidate, assets := localSetupFixture(t)
	ctx := context.Background()
	if _, err := f.s.PrepareClientRuntime(ctx, f.token, candidate, assets, client.Doc, client.ConfigurationAuthority); err != nil {
		t.Fatal(err)
	}
	before := localSetupCensus(t, f)
	changed := []byte("different offline bundle")
	if err := os.WriteFile(assets.BundleFile, changed, 0600); err != nil {
		t.Fatal(err)
	}
	assets.BundleHash = Digest(changed)
	if _, err := f.s.PrepareClientRuntime(ctx, f.token, candidate, assets, client.Doc, client.ConfigurationAuthority); err == nil || localSetupCensus(t, f) != before {
		t.Fatalf("changed bundle reused qualification: %v", err)
	}
	id, err := f.s.EnsureRuntimeSetupPrincipal(ctx, f.token, f.project, "EXECUTOR")
	if err != nil {
		t.Fatal(err)
	}
	if _, err = f.s.EnsureRuntimeSetupPrincipal(ctx, f.token, f.project, "VERIFIER"); err == nil {
		t.Fatal("setup provisioned verifier")
	}
	if err = f.s.RevokePrincipal(ctx, id); err != nil {
		t.Fatal(err)
	}
	if _, err = f.s.EnsureRuntimeSetupPrincipal(ctx, f.token, f.project, "EXECUTOR"); err == nil {
		t.Fatal("setup revived revoked executor")
	}
}
