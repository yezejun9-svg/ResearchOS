//go:build windows

package domain

import (
    "context"
    "testing"
    "time"
)

// This test-only capability cannot be installed by an HTTP caller. Production
// deliberately has no Root witness integration in this Source candidate.
type preparedTestAuthority struct{}
func (preparedTestAuthority) verifyPreparedRunAbandonment(_ context.Context, e PreparedRunAbandonmentEvidence) error {
    if e.RootWitnessSignature != "fixture-signed-root-witness" {
        return Fail(403, "FORBIDDEN", "unverified Root witness")
    }
    return nil
}

func preparedFixture(t *testing.T) (*RuntimeCoordinator, RuntimeCoordinatorRoute, *runtimeFixture, PreparedRunAbandonmentEvidence) {
    t.Helper()
    coordinator, route, r := coordinatorFixture(t) // prepares a Run; never starts a native child here.
    tx, err := r.f.db.Begin()
    if err != nil { t.Fatal(err) }
    run, err := load(tx, r.f.project, "Run", Str(r.run, "id"))
    if err != nil { tx.Rollback(); t.Fatal(err) }
    run["lease_expires_at"] = time.Now().UTC().Add(-time.Minute).Format(time.RFC3339Nano)
    if err = bump(run); err != nil { tx.Rollback(); t.Fatal(err) }
    if err = r.f.s.put(tx, "Run", run); err != nil { tx.Rollback(); t.Fatal(err) }
    if err = tx.Commit(); err != nil { t.Fatal(err) }
    task := r.f.read("tasks", Str(r.task, "id"))
    var key, digest string
    if err = r.f.db.QueryRow("SELECT dispatch_key,manifest_hash FROM runtime_dispatches WHERE project=? AND run=? AND epoch=?", r.f.project, run["id"], run["lease_epoch"]).Scan(&key, &digest); err != nil { t.Fatal(err) }
    epoch, _ := Num(run, "lease_epoch")
    runRevision, _ := Num(run, "revision")
    taskRevision, _ := Num(task, "revision")
    started := time.Now().UTC().Add(-11*time.Minute)
    evidence := PreparedRunAbandonmentEvidence{
        Schema: "researchos.prepared-run-abandonment.v1", Outcome: preparedAbandonmentOutcome,
        ProjectID: r.f.project, TaskID: Str(task,"id"), RunID: Str(run,"id"), RuntimeID: Str(r.registration,"id"), OwnerRoot: r.f.owner,
        Epoch: epoch, RunRevision: runRevision, TaskRevision: taskRevision, DispatchKey: key, ManifestHash: digest,
        RootStartedUTC: started.Format(time.RFC3339Nano), RootClockExpiredUTC: started.Add(300*time.Second).Format(time.RFC3339Nano),
        ParentJobID: "fixture-closed-root-job", ParentJobClosedUTC: time.Now().UTC().Add(-time.Minute).Format(time.RFC3339Nano), ParentJobTerminal: true,
        HostJobContractSHA256: Digest([]byte("contract")), HostJobProbeSHA256: Digest([]byte("probe")), GOAuthoritySHA256: Digest([]byte("go")),
        RootWitnessSHA256: Digest([]byte("root-witness")), RootWitnessSignature: "fixture-signed-root-witness",
        ProviderRequests: nil, ActualCost: nil, FinancialClosed: false,
    }
    return coordinator, route, r, evidence
}

func TestPreparedRunAbandonmentSuccessAndIdempotency(t *testing.T) {
    coordinator, route, r, evidence := preparedFixture(t)
    if _, err := r.f.s.AbandonPreparedQualification(context.Background(), r.ownerToken, evidence); err == nil {
        t.Fatal("unbound Root witness capability accepted")
    }
    r.f.s.preparedAbandonmentAuthority = preparedTestAuthority{}
    run, err := r.f.s.AbandonPreparedQualification(context.Background(), r.ownerToken, evidence)
    if err != nil { t.Fatal(err) }
    task := r.f.read("tasks", evidence.TaskID)
    if run["status"] != "FAILED" || task["status"] != "FAILED" || task["active_run_id"] != evidence.RunID || run["runtime_settled_at"] != nil || run["children_stopped"] != nil || run["queue_empty"] != nil {
        t.Fatalf("failure projected as settled runtime or lost Task history: %s %s", Bytes(run), Bytes(task))
    }
    var state, worker, locator string
    if err = r.f.db.QueryRow("SELECT state,worker,journal_locator FROM runtime_dispatches WHERE project=? AND run=? AND epoch=?", evidence.ProjectID,evidence.RunID,evidence.Epoch).Scan(&state,&worker,&locator); err != nil || state != "PREPARED" || worker != "" || locator != "" {
        t.Fatalf("dispatch history changed: %s %s %s %v",state,worker,locator,err)
    }
    var financial int
    var proof string
    if err = r.f.db.QueryRow("SELECT financial_closed,proof_json FROM runtime_prepared_abandonments WHERE project=? AND run=? AND epoch=?",evidence.ProjectID,evidence.RunID,evidence.Epoch).Scan(&financial,&proof); err != nil || financial != 0 {
        t.Fatalf("missing open-accounting proof: %d %v",financial,err)
    }
    stored, err := Decode([]byte(proof))
    if err != nil || stored["provider_requests"] != nil || stored["actual_cost"] != nil || stored["outcome"] != preparedAbandonmentOutcome {
        t.Fatalf("unknown accounting changed: %s %v",proof,err)
    }
    var markers, ledger, observations int
    if err = r.f.db.QueryRow("SELECT count(*) FROM runtime_qualification_runs WHERE project=? AND task=? AND run=?",evidence.ProjectID,evidence.TaskID,evidence.RunID).Scan(&markers); err != nil { t.Fatal(err) }
    if err = r.f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='BudgetLedgerEntry' AND project=? AND json_extract(body,'$.run_id')=?",evidence.ProjectID,evidence.RunID).Scan(&ledger); err != nil { t.Fatal(err) }
    if err = r.f.db.QueryRow("SELECT count(*) FROM runtime_observations WHERE project=? AND run=?",evidence.ProjectID,evidence.RunID).Scan(&observations); err != nil { t.Fatal(err) }
    if markers != 1 || ledger != 0 || observations != 0 { t.Fatalf("marker/accounting/observation changed: %d %d %d",markers,ledger,observations) }
    again, err := r.f.s.AbandonPreparedQualification(context.Background(),r.ownerToken,evidence)
    if err != nil || Hash(again) != Hash(run) { t.Fatalf("identical proof not idempotent: %v",err) }
    other := evidence
    other.HostJobProbeSHA256 = Digest([]byte("different-probe"))
    if _,err = r.f.s.AbandonPreparedQualification(context.Background(),r.ownerToken,other); err == nil { t.Fatal("different proof accepted") }
    if _,err = r.f.db.Exec("UPDATE runtime_dispatches SET state='STARTED',worker='forged',journal_locator='forged' WHERE project=? AND run=? AND epoch=?",evidence.ProjectID,evidence.RunID,evidence.Epoch); err == nil { t.Fatal("tombstoned dispatch was writable") }
    if _,err = r.f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.status','QUEUED') WHERE project=? AND kind='Run' AND id=?",evidence.ProjectID,evidence.RunID); err == nil { t.Fatal("tombstoned Run was writable") }
    status, _, _ := r.f.request("POST",r.f.path("/tasks/"+evidence.TaskID+"/actions"),ID(),testTag(task),Object{"action":"RESUME","reason":"must not reuse old qualification"})
    if status < 400 { t.Fatal("abandoned qualification Task resumed") }
    if err = coordinator.RunAdmitted(context.Background(),route,r.run,r.lease); err == nil { t.Fatal("terminal Run launched after tombstone") }
    config := coordinator.config
    if err = coordinator.Close(); err != nil { t.Fatal(err) }
    restarted, err := r.f.s.NewRuntimeCoordinator(context.Background(), config)
    if err != nil { t.Fatal(err) }
    defer restarted.Close()
    if err = restarted.Recover(context.Background()); err != nil { t.Fatal(err) }
    if err = r.f.db.QueryRow("SELECT state FROM runtime_dispatches WHERE project=? AND run=? AND epoch=?",evidence.ProjectID,evidence.RunID,evidence.Epoch).Scan(&state); err != nil || state != "PREPARED" { t.Fatalf("restart recovery rewrote tombstone: %s %v",state,err) }
}

func TestPreparedRunAbandonmentRejectsBindingsAndAuthority(t *testing.T) {
    _,route,r,evidence := preparedFixture(t)
    r.f.s.preparedAbandonmentAuthority = preparedTestAuthority{}
    bad := []struct{name string; change func(*PreparedRunAbandonmentEvidence)}{
        {"run_revision",func(x *PreparedRunAbandonmentEvidence){x.RunRevision++}},
        {"task_revision",func(x *PreparedRunAbandonmentEvidence){x.TaskRevision++}},
        {"epoch",func(x *PreparedRunAbandonmentEvidence){x.Epoch++}},
        {"runtime",func(x *PreparedRunAbandonmentEvidence){x.RuntimeID="wrong-runtime"}},
        {"dispatch_key",func(x *PreparedRunAbandonmentEvidence){x.DispatchKey="wrong-key"}},
        {"manifest_hash",func(x *PreparedRunAbandonmentEvidence){x.ManifestHash=Digest([]byte("wrong-manifest"))}},
        {"owner_root",func(x *PreparedRunAbandonmentEvidence){x.OwnerRoot="wrong-root"}},
        {"root_signature",func(x *PreparedRunAbandonmentEvidence){x.RootWitnessSignature="forged"}},
        {"parent_job",func(x *PreparedRunAbandonmentEvidence){x.ParentJobTerminal=false}},
        {"clock",func(x *PreparedRunAbandonmentEvidence){x.RootClockExpiredUTC=time.Now().UTC().Add(time.Hour).Format(time.RFC3339Nano)}},
        {"cost_zero",func(x *PreparedRunAbandonmentEvidence){v:="0";x.ActualCost=&v}},
        {"provider_zero",func(x *PreparedRunAbandonmentEvidence){v:=int64(0);x.ProviderRequests=&v}},
        {"financial_closed",func(x *PreparedRunAbandonmentEvidence){x.FinancialClosed=true}},
    }
    for _,case_ := range bad {
        t.Run(case_.name,func(t *testing.T){x:=evidence;case_.change(&x);if _,err:=r.f.s.AbandonPreparedQualification(context.Background(),r.ownerToken,x);err==nil{t.Fatal("bad binding accepted")}})
    }
    if _,err:=r.f.s.AbandonPreparedQualification(context.Background(),route.ExecutorToken,evidence);err==nil{t.Fatal("Executor credential accepted")}
    var count int
    if err:=r.f.db.QueryRow("SELECT count(*) FROM runtime_prepared_abandonments WHERE project=? AND run=?",evidence.ProjectID,evidence.RunID).Scan(&count);err!=nil||count!=0{t.Fatalf("rejected request mutated state: %d %v",count,err)}
}

func TestPreparedRunAbandonmentRejectsStartedUnknownAndFootprints(t *testing.T) {
    cases:=[]struct{name string; inject func(*testing.T,*runtimeFixture,PreparedRunAbandonmentEvidence)}{
        {"started",func(t *testing.T,r *runtimeFixture,e PreparedRunAbandonmentEvidence){_,err:=r.f.db.Exec("UPDATE runtime_dispatches SET state='STARTED',worker='worker',journal_locator=? WHERE project=? AND run=? AND epoch=?",e.DispatchKey,e.ProjectID,e.RunID,e.Epoch);if err!=nil{t.Fatal(err)}}},
        {"unknown",func(t *testing.T,r *runtimeFixture,e PreparedRunAbandonmentEvidence){_,err:=r.f.db.Exec("UPDATE runtime_dispatches SET state='UNKNOWN',reason='missing journal' WHERE project=? AND run=? AND epoch=?",e.ProjectID,e.RunID,e.Epoch);if err!=nil{t.Fatal(err)}}},
        {"observation",func(t *testing.T,r *runtimeFixture,e PreparedRunAbandonmentEvidence){_,err:=r.f.db.Exec("INSERT INTO runtime_observations(project,run,epoch,receipt_hash,body,observed_at) VALUES(?,?,?,?,?,?)",e.ProjectID,e.RunID,e.Epoch,Digest([]byte("obs")),`{}`,Now());if err!=nil{t.Fatal(err)}}},
        {"effect",func(t *testing.T,r *runtimeFixture,e PreparedRunAbandonmentEvidence){_,err:=r.f.db.Exec("INSERT INTO resource_effects(project,run,effect_key,sequence,body) VALUES(?,?,?,?,?)",e.ProjectID,e.RunID,"effect",1,`{"state":"UNKNOWN"}`);if err!=nil{t.Fatal(err)}}},
        {"ledger",func(t *testing.T,r *runtimeFixture,e PreparedRunAbandonmentEvidence){_,err:=r.f.db.Exec("INSERT INTO domain_objects(project,kind,id,revision,body) VALUES(?,?,?,?,?)",e.ProjectID,"BudgetLedgerEntry",ID(),1,string(Bytes(Object{"run_id":e.RunID,"provider_request_id":"qualification-dispatch/"+e.RunID})));if err!=nil{t.Fatal(err)}}},
        {"queue",func(t *testing.T,r *runtimeFixture,e PreparedRunAbandonmentEvidence){_,err:=r.f.db.Exec("INSERT INTO client_queue_fences(project,task_id,session_id,generation,state) VALUES(?,?,?,?,?)",e.ProjectID,e.TaskID,"session",ID(),"OPEN");if err!=nil{t.Fatal(err)}}},
        {"upload",func(t *testing.T,r *runtimeFixture,e PreparedRunAbandonmentEvidence){_,err:=r.f.db.Exec("INSERT INTO uploaded_content(storage_key,project,principal,bytes,content_hash,expires_at) VALUES(?,?,?,?,?,?)",ID(),e.ProjectID,r.executor,[]byte("x"),Digest([]byte("x")),Now());if err!=nil{t.Fatal(err)}}},
        {"marker_missing",func(t *testing.T,r *runtimeFixture,e PreparedRunAbandonmentEvidence){_,err:=r.f.db.Exec("DELETE FROM runtime_qualification_runs WHERE project=? AND task=?",e.ProjectID,e.TaskID);if err!=nil{t.Fatal(err)}}},
        {"lease_unexpired",func(t *testing.T,r *runtimeFixture,e PreparedRunAbandonmentEvidence){_,err:=r.f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.lease_expires_at',?) WHERE project=? AND kind='Run' AND id=?",time.Now().UTC().Add(time.Hour).Format(time.RFC3339Nano),e.ProjectID,e.RunID);if err!=nil{t.Fatal(err)}}},
        {"task_not_running",func(t *testing.T,r *runtimeFixture,e PreparedRunAbandonmentEvidence){_,err:=r.f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.status','BLOCKED') WHERE project=? AND kind='Task' AND id=?",e.ProjectID,e.TaskID);if err!=nil{t.Fatal(err)}}},
    }
    for _,case_:=range cases{
        t.Run(case_.name,func(t *testing.T){_,_,r,e:=preparedFixture(t);r.f.s.preparedAbandonmentAuthority=preparedTestAuthority{};case_.inject(t,r,e);if _,err:=r.f.s.AbandonPreparedQualification(context.Background(),r.ownerToken,e);err==nil{t.Fatal("started/unknown/footprint accepted")}})
    }
}
