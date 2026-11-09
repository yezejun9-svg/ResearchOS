//go:build windows

package domain

import (
	"context"
	"database/sql"
	"strings"
	"testing"
	"time"
)

func TestLocalRuntimeExecutorNarrowClaimGrants(t *testing.T) {
	f, client, candidate, assets := localSetupFixture(t)
	ctx := context.Background()
	prepared, e := f.s.PrepareClientRuntime(ctx, f.token, candidate, assets, client.Doc, client.ConfigurationAuthority)
	if e != nil {
		t.Fatal(e)
	}
	executor, e := f.s.EnsureRuntimeSetupPrincipal(ctx, f.token, f.project, "EXECUTOR")
	if e != nil {
		t.Fatal(e)
	}
	run, _, e := f.s.BeginRuntimeQualification(ctx, f.token, f.project, prepared.TaskID, prepared.RuntimeID, executor)
	if e != nil {
		t.Fatal(e)
	}
	if got, e := f.s.EnsureRuntimeSetupPrincipal(ctx, f.token, f.project, "EXECUTOR"); e != nil || got != executor {
		t.Fatalf("legitimate current claim rejected: %v", e)
	}
	// The original claim/epoch marker remains the authority for historical grants.
	before := localSetupCensus(t, f)
	for _, g := range []Grant{{ProjectID: "unrelated-project"}, {ProjectID: f.project, TaskID: prepared.TaskID}, {ProjectID: f.project, TaskID: prepared.TaskID, RunID: "missing-run"}, {ProjectID: f.project, TaskID: "wrong-task", RunID: Str(run, "id")}} {
		_, e = f.db.Exec(`INSERT INTO auth_grants(principal,project,task,run,restricted) VALUES(?,?,?,?,?)`, executor, g.ProjectID, g.TaskID, g.RunID, g.Restricted)
		if e != nil {
			t.Fatal(e)
		}
		if _, e = f.s.EnsureRuntimeSetupPrincipal(ctx, f.token, f.project, "EXECUTOR"); e == nil {
			t.Fatalf("unrelated grant accepted: %+v", g)
		}
		if _, e = f.db.Exec(`DELETE FROM auth_grants WHERE principal=? AND project=? AND task=? AND run=? AND restricted=?`, executor, g.ProjectID, g.TaskID, g.RunID, g.Restricted); e != nil {
			t.Fatal(e)
		}
	}
	if _, e = f.db.Exec(`UPDATE auth_grants SET restricted=1 WHERE principal=? AND project=? AND task=? AND run=?`, executor, f.project, prepared.TaskID, run["id"]); e != nil {
		t.Fatal(e)
	}
	if _, e = f.s.EnsureRuntimeSetupPrincipal(ctx, f.token, f.project, "EXECUTOR"); e == nil {
		t.Fatal("altered restricted grant accepted")
	}
	if _, e = f.db.Exec(`UPDATE auth_grants SET restricted=0 WHERE principal=? AND project=? AND task=? AND run=?`, executor, f.project, prepared.TaskID, run["id"]); e != nil {
		t.Fatal(e)
	}
	if _, e = f.s.EnsureRuntimeSetupPrincipal(ctx, f.token, f.project, "EXECUTOR"); e != nil {
		t.Fatal(e)
	}
	if localSetupCensus(t, f) != before {
		t.Fatal("credential validation mutated business activity")
	}
	t.Log("qualification Begin only, original Run grant accepted; foreign/task-only/missing/wrong/restricted grants denied; provider/model execution=0")
}

func TestManagedLocalQualificationRequestConsumptionAndDrift(t *testing.T) {
	f, client, candidate, assets := localSetupFixture(t)
	ctx := context.Background()
	prepared, e := f.s.PrepareClientRuntime(ctx, f.token, candidate, assets, client.Doc, client.ConfigurationAuthority)
	if e != nil {
		t.Fatal(e)
	}
	executor, e := f.s.EnsureRuntimeSetupPrincipal(ctx, f.token, f.project, "EXECUTOR")
	if e != nil {
		t.Fatal(e)
	}
	scheduler, e := f.s.EnsureRuntimeSetupPrincipal(ctx, f.token, f.project, "SCHEDULER")
	if e != nil {
		t.Fatal(e)
	}
	executorToken, e := f.s.IssueCredential(ctx, executor, time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	schedulerToken, e := f.s.IssueCredential(ctx, scheduler, time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	c := &RuntimeCoordinator{service: f.s, config: RuntimeCoordinatorConfig{ClientSchema: client.Doc, ConfigurationAuthority: client.ConfigurationAuthority}}
	if e = c.InstallPreparedRuntime(ctx, prepared, executor, executorToken, schedulerToken, assets); e != nil {
		t.Fatal(e)
	}
	request, e := c.PreparedLocalQualification(ctx, f.token, candidate, 600)
	if e != nil {
		t.Fatal(e)
	}
	if e = c.ValidateLocalQualification(ctx, f.token, request); e != nil {
		t.Fatal(e)
	}
	changed := request
	changed.ProfileHash = Digest([]byte("changed"))
	if c.ValidateLocalQualification(ctx, f.token, changed) == nil {
		t.Fatal("changed profile admitted")
	}
	before := localSetupCensus(t, f)
	if c.ValidateLocalQualification(ctx, executorToken, request) == nil {
		t.Fatal("executor triggered trusted Owner qualification")
	}
	if localSetupCensus(t, f) != before {
		t.Fatal("read-only preflight mutated activity")
	}
	run, lease, e := c.beginManagedLocalQualification(ctx, f.token, request, executor)
	if e != nil {
		t.Fatal(e)
	}
	if _, _, e = c.beginManagedLocalQualification(ctx, f.token, request, executor); e == nil {
		t.Fatal("consumed managed request repeated")
	}
	var body string
	if e = f.db.QueryRow(`SELECT body FROM idempotency WHERE operation='host:managed-runtime-qualification' AND key=?`, request.RequestID).Scan(&body); e != nil {
		t.Fatal(e)
	}
	if len(body) == 0 || strings.Contains(body, lease) {
		t.Fatal("lease leaked into managed receipt")
	}
	if e = c.ValidateLocalQualification(ctx, f.token, request); e == nil {
		t.Fatal("consumed draft preflight accepted")
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		var count int
		if e := tx.QueryRow(`SELECT count(*) FROM resource_effects WHERE run=?`, run["id"]).Scan(&count); e != nil {
			return e
		}
		if count != 0 {
			t.Fatal("preparation performed effect")
		}
		return nil
	})
	t.Log("private managed request committed once with original qualification gates; no worker launch or model request")
}
