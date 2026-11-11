//go:build windows

package domain

import (
    "context"
    "os"
    "path/filepath"
    "sort"
    "strings"
    "testing"
    "time"
)

// Snapshot all logical tables in the disposable fixture, after fault injection
// and before the rejected operation. Only hashes leave this helper.
func preparedDatabaseSnapshot(t *testing.T, r *runtimeFixture) string {
    t.Helper()
    names, err := r.f.db.Query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    if err != nil { t.Fatal(err) }
    tables := []string{}
    for names.Next() {
        var name string
        if err = names.Scan(&name); err != nil { names.Close(); t.Fatal(err) }
        tables = append(tables,name)
    }
    err = names.Err()
    names.Close()
    if err != nil { t.Fatal(err) }
    snapshot := Object{}
    for _, name := range tables {
        rows, err := r.f.db.Query("SELECT * FROM \""+strings.ReplaceAll(name,"\"","\"\"")+"\"")
        if err != nil { t.Fatal(err) }
        columns, err := rows.Columns()
        if err != nil { rows.Close(); t.Fatal(err) }
        records := []string{}
        for rows.Next() {
            values := make([]any,len(columns))
            targets := make([]any,len(columns))
            for i:=range values { targets[i]=&values[i] }
            if err = rows.Scan(targets...); err != nil { rows.Close(); t.Fatal(err) }
            records=append(records,string(Bytes(values)))
        }
        err=rows.Err()
        rows.Close()
        if err != nil { t.Fatal(err) }
        sort.Strings(records)
        snapshot[name]=records
    }
    return Hash(snapshot)
}

func preparedAssertFault(t *testing.T, err error, status int, code, message string) {
    t.Helper()
    fault,ok:=err.(*Fault)
    if !ok || fault.Status!=status || fault.Code!=code || !strings.Contains(fault.Message,message) {
        t.Fatalf("wanted %d %s containing %q, got %v",status,code,message,err)
    }
}


// These five cases exercise the real profile checker with typed in-memory
// copies of a persisted manifest. They are checker coverage, not top-level
// AbandonPreparedQualification coverage: the production manifest trigger is
// intentionally left enabled and no persisted immutable JSON is changed.
func TestPreparedRunAbandonmentProfileCheckerRejectsMemoryManifestPins(t *testing.T) {
    cases:=[]struct{name string; change func(Object)}{
        {"profile_ref_mismatch",func(m Object){m["admission"].(map[string]any)["profile_ref"].(map[string]any)["id"]="different-profile"}},
        {"profile_hash_mismatch",func(m Object){m["admission"].(map[string]any)["profile_hash"]=Digest([]byte("different-profile-pin"))}},
        {"plan_pin_mismatch",func(m Object){m["admission"].(map[string]any)["permission"].(map[string]any)["plan_hash"]=Digest([]byte("different-plan-pin"))}},
        {"profile_body_mismatch",func(m Object){m["admission"].(map[string]any)["profile"].(map[string]any)["model"]="different-model"}},
        {"input_pin_mismatch",func(m Object){m["input_refs"]=Empty()}},
    }
    for _,case_:=range cases {
        t.Run(case_.name,func(t *testing.T){
            _,_,r,e:=preparedFixture(t)
            expectedKey:=preparedAssertCleanProfile(t,r,e)
            before:=preparedDatabaseSnapshot(t,r)
            tx,err:=r.f.db.Begin()
            if err!=nil{t.Fatal(err)}
            defer tx.Rollback()
            run,err:=load(tx,e.ProjectID,"Run",e.RunID)
            if err!=nil{t.Fatal(err)}
            task,err:=load(tx,e.ProjectID,"Task",e.TaskID)
            if err!=nil{t.Fatal(err)}
            dispatch,err:=runtimeDispatch(tx,e.ProjectID,e.RunID,e.Epoch)
            if err!=nil{t.Fatal(err)}
            persisted,ok:=dispatch["manifest"].(map[string]any)
            if !ok{t.Fatal("persisted manifest is not a typed object")}
            persistedHash:=Hash(persisted)
            // The same real checker must accept the persisted clean baseline.
            key,err:=r.f.s.preparedRunAbandonmentProfileUpload(tx,e,run,task,persisted)
            if err!=nil || key!=expectedKey{t.Fatalf("clean checker baseline failed: %s %v",key,err)}
            mutated,err:=Decode(Bytes(persisted))
            if err!=nil{t.Fatal(err)}
            case_.change(mutated)
            if Hash(persisted)!=persistedHash || Hash(mutated)==persistedHash{t.Fatal("fault injection did not isolate a changed in-memory copy")}
            _,err=r.f.s.preparedRunAbandonmentProfileUpload(tx,e,run,task,mutated)
            preparedAssertFault(t,err,409,"STATE_CONFLICT","preparation profile immutable binding differs")
            if err=tx.Rollback();err!=nil{t.Fatal(err)}
            if after:=preparedDatabaseSnapshot(t,r);after!=before{t.Fatal("read-only checker case changed fixture database")}
        })
    }
}

func TestPreparedRunAbandonmentRejectsPreparationUploadAndPins(t *testing.T) {
    cases:=[]struct{
        name string
        expected string
        inject func(*testing.T,*runtimeFixture,*PreparedRunAbandonmentEvidence,string)
    }{
        {"additional_executor_upload","pre-dispatch abandonment refuses",func(t *testing.T,r *runtimeFixture,e *PreparedRunAbandonmentEvidence,key string){
            // Same bytes and digest at another storage key are still unbound.
            _,err:=r.f.db.Exec("INSERT INTO uploaded_content(storage_key,project,principal,bytes,content_hash,expires_at,sealed) SELECT ?,project,principal,bytes,content_hash,expires_at,1 FROM uploaded_content WHERE storage_key=?",ID(),key)
            if err!=nil{t.Fatal(err)}
        }},
        {"run_scoped_upload","pre-dispatch abandonment refuses",func(t *testing.T,r *runtimeFixture,e *PreparedRunAbandonmentEvidence,key string){
            // Even the permitted preparation storage key is forbidden as a Run contribution.
            _,err:=r.f.db.Exec("INSERT INTO runtime_uploads(storage_key,project,run,epoch) VALUES(?,?,?,?)",key,e.ProjectID,e.RunID,e.Epoch)
            if err!=nil{t.Fatal(err)}
        }},
        {"storage_key_mismatch","sealed runtime profile unavailable",func(t *testing.T,r *runtimeFixture,e *PreparedRunAbandonmentEvidence,key string){
            _,err:=r.f.db.Exec("UPDATE uploaded_content SET storage_key=? WHERE storage_key=?",ID(),key)
            if err!=nil{t.Fatal(err)}
        }},
        {"upload_sha_mismatch","preparation profile upload integrity differs",func(t *testing.T,r *runtimeFixture,e *PreparedRunAbandonmentEvidence,key string){
            // Isolated corruption injection; never weaken or remove production triggers.
            tx,err:=r.f.db.Begin();if err!=nil{t.Fatal(err)};defer tx.Rollback()
            if _,err=tx.Exec("UPDATE uploaded_content SET sealed=0 WHERE storage_key=?",key);err!=nil{t.Fatal(err)}
            if _,err=tx.Exec("UPDATE uploaded_content SET content_hash=?,sealed=1 WHERE storage_key=?",Digest([]byte("wrong-digest")),key);err!=nil{t.Fatal(err)}
            if err=tx.Commit();err!=nil{t.Fatal(err)}
        }},
        {"upload_principal_mismatch","preparation profile upload integrity differs",func(t *testing.T,r *runtimeFixture,e *PreparedRunAbandonmentEvidence,key string){
            _,err:=r.f.db.Exec("UPDATE uploaded_content SET principal=? WHERE storage_key=?",r.f.owner,key)
            if err!=nil{t.Fatal(err)}
        }},
        {"upload_unsealed","sealed runtime profile unavailable",func(t *testing.T,r *runtimeFixture,e *PreparedRunAbandonmentEvidence,key string){
            _,err:=r.f.db.Exec("UPDATE uploaded_content SET sealed=0 WHERE storage_key=?",key)
            if err!=nil{t.Fatal(err)}
        }},
        {"marker_profile_pin_mismatch","preparation profile immutable binding differs",func(t *testing.T,r *runtimeFixture,e *PreparedRunAbandonmentEvidence,key string){
            // Replace one marker in this disposable fixture using its real schema.
            // Its immutable UPDATE trigger remains installed; production never does this.
            tx,err:=r.f.db.Begin();if err!=nil{t.Fatal(err)};defer tx.Rollback()
            var plan,profile,contract,inputs,bundle,root string
            if err=tx.QueryRow("SELECT plan_hash,profile_hash,contract_hash,input_hash,context_bundle,owner_root FROM runtime_qualification_runs WHERE project=? AND task=?",e.ProjectID,e.TaskID).Scan(&plan,&profile,&contract,&inputs,&bundle,&root);err!=nil{t.Fatal(err)}
            if _,err=tx.Exec("DELETE FROM runtime_qualification_runs WHERE project=? AND task=?",e.ProjectID,e.TaskID);err!=nil{t.Fatal(err)}
            if _,err=tx.Exec("INSERT INTO runtime_qualification_runs(project,task,run,runtime,epoch,plan_hash,profile_hash,contract_hash,input_hash,context_bundle,owner_root) VALUES(?,?,?,?,?,?,?,?,?,?,?)",e.ProjectID,e.TaskID,e.RunID,e.RuntimeID,e.Epoch,plan,Digest([]byte("different-marker-profile")),contract,inputs,bundle,root);err!=nil{t.Fatal(err)}
            if err=tx.Commit();err!=nil{t.Fatal(err)}
        }},
    }
    for _,case_:=range cases{
        t.Run(case_.name,func(t *testing.T){
            _,_,r,e:=preparedFixture(t)
            key:=preparedAssertCleanProfile(t,r,e)
            r.f.s.preparedAbandonmentAuthority=preparedTestAuthority{}
            case_.inject(t,r,&e,key)
            before:=preparedDatabaseSnapshot(t,r)
            _,err:=r.f.s.AbandonPreparedQualification(context.Background(),r.ownerToken,e)
            status,code:=409,"STATE_CONFLICT"
            if case_.expected=="sealed runtime profile unavailable" {status,code=422,"GATE_FAILED"}
            preparedAssertFault(t,err,status,code,case_.expected)
            if after:=preparedDatabaseSnapshot(t,r);after!=before{t.Fatal("profile rejection changed fixture database")}
            var count int
            if err:=r.f.db.QueryRow("SELECT count(*) FROM runtime_prepared_abandonments WHERE project=? AND run=?",e.ProjectID,e.RunID).Scan(&count);err!=nil || count!=0 {t.Fatalf("rejection wrote proof: %d %v",count,err)}
            if r.f.read("runs",e.RunID)["status"]!="QUEUED" || r.f.read("tasks",e.TaskID)["status"]!="RUNNING" {t.Fatal("profile rejection changed business state")}
        })
    }
}


// This test-only capability cannot be installed by an HTTP caller. Production
// deliberately has no Root witness integration in this Source candidate.
type preparedTestAuthority struct{}
func (preparedTestAuthority) verifyPreparedRunAbandonment(_ context.Context, e PreparedRunAbandonmentEvidence) error {
    if e.RootWitnessSignature != "fixture-signed-root-witness" {
        return Fail(403, "FORBIDDEN", "unverified Root witness")
    }
    return nil
}

// Build the same pre-Run preparation sequence as the trusted Host: executor
// upload -> sealed Artifact -> Task input -> immutable plan -> qualification Run.
// LIVE here selects the production unknown-cost admission branch only. This
// fixture never calls a model, broker, worker, or native process.
func preparedCoordinatorFixture(t *testing.T) (*RuntimeCoordinator, RuntimeCoordinatorRoute, *runtimeFixture) {
    t.Helper()
    f := contextFixture(t)
    req := f.requirement()
    exe, err := os.Executable()
    if err != nil { t.Fatal(err) }
    binary, err := os.ReadFile(exe)
    if err != nil { t.Fatal(err) }
    registration := f.expect(201, "POST", f.path("/runtimes"), ID(), f.stateTag(), Object{"name":"prepared abandonment admission only", "adapter":"codex-cli", "adapter_revision":runtimeBridgeRevision, "capabilities":[]any{"start","context_rebuild"}, "platform":"windows-amd64", "measurement_mode":"LIVE", "credential_ref":nil})
    executor, scheduler := ID(), ID()
    for _, p := range []Principal{
        {ID:executor, Roles:[]string{"EXECUTOR"}, Grants:[]Grant{{ProjectID:f.project}}},
        {ID:scheduler, Roles:[]string{"SCHEDULER"}, Grants:[]Grant{{ProjectID:f.project}}},
    } {
        if err = f.s.ProvisionPrincipal(context.Background(), p); err != nil { t.Fatal(err) }
    }
    executorToken, err := f.s.IssueCredential(context.Background(), executor, 15*time.Minute)
    if err != nil { t.Fatal(err) }
    schedulerToken, err := f.s.IssueCredential(context.Background(), scheduler, 15*time.Minute)
    if err != nil { t.Fatal(err) }
    ownerToken := f.token
    profileBody := Object{"runtime_id":registration["id"], "technical_hash":runtimeTechnicalHash(registration), "adapter":registration["adapter"], "adapter_revision":runtimeBridgeRevision, "platform":"windows-amd64", "build_hash":Digest(binary), "sandbox":runtimeSandboxProfile, "credential_revision":"none", "backend":"native-offline", "model":"none", "command_id":"native-fixture", "argv":[]any{"-test.run=^TestRuntimeCoordinatorChild$","--","--coordinator-child","{manifest}"}, "effect_routes":Empty(), "permissions":Object{"network":"none","environment":"staging-only","capabilities":Empty(),"process_limit":1,"memory_mib":256}, "timeout_seconds":15, "outputs":[]any{"result.json"}, "max_cost":nil}
    raw := Bytes(profileBody)
    f.token = executorToken
    upload := f.expect(201, "POST", f.path("/content"), ID(), "", raw)
    profile := f.expect(201, "POST", f.path("/artifacts"), ID(), f.stateTag(), Object{"run_id":nil, "kind":"REPORT", "evidence_kind":"GENERATED", "measurement_mode":"LIVE", "content_hash":upload["content_hash"], "storage_key":upload["storage_key"], "media_type":"application/json", "byte_size":len(raw), "input_refs":Empty(), "source_refs":Empty(), "produced_by":executor, "access_class":"PROJECT"})
    f.token = ownerToken
    contract := orchestrationContract()
    goal := f.expect(201, "POST", f.path("/goals"), ID(), f.stateTag(), Object{"title":"prepared qualification", "original_intent":"test exact pre-dispatch abandonment", "scope":"PROJECT", "requirement_refs":[]any{Ref(req,"Requirement")}, "problem_ids":[]any{"runtime"}, "deliverables":[]any{"receipt"}, "acceptance_contract":contract})
    goal = f.expect(200, "POST", f.path("/goals/"+Str(goal,"id")+"/actions"), ID(), testTag(goal), Object{"action":"ACTIVATE","reason":"isolated admission fixture"})
    task := f.expect(201, "POST", f.path("/tasks"), ID(), testTag(goal), Object{"goal_id":goal["id"], "title":"prepared qualification", "task_type":"runtime_qualification", "stage":"verification", "dependency_task_ids":Empty(), "requirement_refs":[]any{Ref(req,"Requirement")}, "input_refs":[]any{Ref(profile,"Artifact")}, "acceptance_contract":contract, "origin_problem_id":"runtime", "candidate_id":"runtime", "stop_policy":Object{"wall_time_seconds":60,"max_attempts":1,"max_parallel_runs":1,"stop_conditions":[]any{"no progress"}}})
    f.bundle(task)
    task = f.read("tasks", Str(task,"id"))
    if err = f.s.RegisterRuntimeQualificationPlan(context.Background(), ownerToken, f.project, Str(task,"id"), Str(registration,"id"), Ref(profile,"Artifact"), []any{"start","context_rebuild"}, time.Hour, ""); err != nil { t.Fatal(err) }
    run, lease, err := f.s.BeginRuntimeQualification(context.Background(), ownerToken, f.project, Str(task,"id"), Str(registration,"id"), executor)
    if err != nil { t.Fatal(err) }
    server, _ := fixtureHTTPServer(t, f.h)
    t.Cleanup(server.Close)
    var seq int
    var name, dbPath string
    if err = f.db.QueryRow("PRAGMA database_list").Scan(&seq,&name,&dbPath); err != nil { t.Fatal(err) }
    route := RuntimeCoordinatorRoute{ProjectID:f.project, RuntimeID:Str(registration,"id"), ExecutorID:executor, ExecutorToken:executorToken, CommandID:Str(profileBody,"command_id"), Executable:exe}
    coordinator, err := f.s.NewRuntimeCoordinator(context.Background(), RuntimeCoordinatorConfig{DataRoot:filepath.Dir(dbPath),APIURL:server.URL,SchedulerToken:schedulerToken,Routes:[]RuntimeCoordinatorRoute{route}})
    if err != nil { t.Fatal(err) }
    t.Cleanup(func(){ coordinator.Close() })
    return coordinator, route, &runtimeFixture{f:f,ownerToken:ownerToken,executor:executor,lease:lease,run:run,task:task,registration:registration}
}

// Every positive and negative case must start from an actually eligible fixture.
// This prevents an existing billing/upload or wrong Task type from masking the
// guard that a negative case intends to exercise.
func preparedAssertCleanProfile(t *testing.T, r *runtimeFixture, e PreparedRunAbandonmentEvidence) string {
    t.Helper()
    tx, err := r.f.db.Begin()
    if err != nil { t.Fatal(err) }
    defer tx.Rollback()
    run, err := load(tx,e.ProjectID,"Run",e.RunID)
    if err != nil { t.Fatal(err) }
    task, err := load(tx,e.ProjectID,"Task",e.TaskID)
    if err != nil { t.Fatal(err) }
    if task["task_type"]!="runtime_qualification" || task["status"]!="RUNNING" || task["active_run_id"]!=e.RunID || run["status"]!="QUEUED" || r.registration["measurement_mode"]!="LIVE" { t.Fatal("fixture is not an admitted LIVE qualification") }
    var markers, frozen int
    if err = tx.QueryRow("SELECT count(*) FROM runtime_qualification_runs WHERE project=? AND task=? AND run=? AND runtime=? AND epoch=? AND owner_root=?",e.ProjectID,e.TaskID,e.RunID,e.RuntimeID,e.Epoch,e.OwnerRoot).Scan(&markers); err!=nil || markers!=1 { t.Fatalf("fixture lacks exact immutable marker: %d %v",markers,err) }
    if err = tx.QueryRow("SELECT count(*) FROM sqlite_master WHERE type='trigger' AND name='runtime_qualification_runs_frozen'").Scan(&frozen); err!=nil || frozen!=1 { t.Fatalf("fixture marker is not protected: %d %v",frozen,err) }
    dispatch, err := runtimeDispatch(tx,e.ProjectID,e.RunID,e.Epoch)
    if err != nil { t.Fatal(err) }
    if dispatch["state"]!="PREPARED" || dispatch["worker"]!="" || dispatch["journal_locator"]!="" || Hash(dispatch["identity"])!=Hash(Object{}) { t.Fatal("fixture already crossed launch fence") }
    manifest := dispatch["manifest"].(map[string]any)
    key, err := r.f.s.preparedRunAbandonmentProfileUpload(tx,e,run,task,manifest)
    if err != nil || key=="" { t.Fatalf("baseline preparation binding rejected: %v",err) }
    if err = preparedRunAbandonmentFootprint(tx,e,r.executor,key); err != nil { t.Fatalf("baseline has a forbidden footprint: %v",err) }
    var uploads int
    if err = tx.QueryRow("SELECT count(*) FROM uploaded_content WHERE project=? AND principal=? AND storage_key=? AND sealed=1",e.ProjectID,r.executor,key).Scan(&uploads); err!=nil || uploads!=1 { t.Fatalf("baseline lacks exact executor sealed profile upload: %d %v",uploads,err) }
    return key
}

func preparedFixture(t *testing.T) (*RuntimeCoordinator, RuntimeCoordinatorRoute, *runtimeFixture, PreparedRunAbandonmentEvidence) {
    t.Helper()
    coordinator, route, r := preparedCoordinatorFixture(t)
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
    preparedAssertCleanProfile(t, r, evidence)
    return coordinator, route, r, evidence
}

func TestPreparedRunAbandonmentSuccessAndIdempotency(t *testing.T) {
    coordinator, route, r, evidence := preparedFixture(t)
    profileKey := preparedAssertCleanProfile(t, r, evidence)
    var originalProfile []byte
    if err := r.f.db.QueryRow("SELECT bytes FROM uploaded_content WHERE storage_key=?", profileKey).Scan(&originalProfile); err != nil { t.Fatal(err) }
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
    var retainedProfile []byte
    var retainedSealed, proofCount int
    if err = r.f.db.QueryRow("SELECT bytes,sealed FROM uploaded_content WHERE storage_key=? AND project=? AND principal=?",profileKey,evidence.ProjectID,r.executor).Scan(&retainedProfile,&retainedSealed); err!=nil || retainedSealed!=1 || Digest(retainedProfile)!=Digest(originalProfile) { t.Fatalf("legal preparation upload was changed or deleted: %v",err) }
    if err = r.f.db.QueryRow("SELECT count(*) FROM runtime_prepared_abandonments WHERE project=? AND run=? AND epoch=?",evidence.ProjectID,evidence.RunID,evidence.Epoch).Scan(&proofCount); err!=nil || proofCount!=1 { t.Fatalf("idempotent proof duplicated: %d %v",proofCount,err) }
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
        t.Run(case_.name,func(t *testing.T){
            preparedAssertCleanProfile(t,r,evidence)
            expected := map[string]string{"run_revision":"current pre-dispatch Run", "task_revision":"current pre-dispatch Run", "epoch":"current pre-dispatch Run", "runtime":"current pre-dispatch Run", "dispatch_key":"native dispatch launch fence", "manifest_hash":"native dispatch launch fence", "owner_root":"direct local Root Owner", "root_signature":"unverified Root witness", "parent_job":"exact pre-dispatch abandonment identity", "clock":"original Root clock", "cost_zero":"unknown provider accounting", "provider_zero":"unknown provider accounting", "financial_closed":"unknown provider accounting"}[case_.name]
            x:=evidence;case_.change(&x)
            before:=preparedDatabaseSnapshot(t,r)
            _,err:=r.f.s.AbandonPreparedQualification(context.Background(),r.ownerToken,x)
            status,code:=409,"STATE_CONFLICT"
            switch case_.name {
            case "owner_root","root_signature":status,code=403,"FORBIDDEN"
            case "parent_job","clock","cost_zero","provider_zero","financial_closed":status,code=422,"GATE_FAILED"
            }
            preparedAssertFault(t,err,status,code,expected)
            if after:=preparedDatabaseSnapshot(t,r);after!=before{t.Fatal("authority rejection changed fixture database")}
        })
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
        t.Run(case_.name,func(t *testing.T){
            _,_,r,e:=preparedFixture(t)
            r.f.s.preparedAbandonmentAuthority=preparedTestAuthority{}
            case_.inject(t,r,e)
            before:=preparedDatabaseSnapshot(t,r)
            expected := "pre-dispatch abandonment refuses"
            switch case_.name {
            case "started","unknown": expected="native dispatch launch fence"
            case "marker_missing": expected="immutable qualification marker"
            case "lease_unexpired","task_not_running": expected="current pre-dispatch Run"
            }
            _,err:=r.f.s.AbandonPreparedQualification(context.Background(),r.ownerToken,e)
            preparedAssertFault(t,err,409,"STATE_CONFLICT",expected)
            if after:=preparedDatabaseSnapshot(t,r);after!=before{t.Fatal("footprint rejection changed fixture database")}
            var proofCount int
            if err:=r.f.db.QueryRow("SELECT count(*) FROM runtime_prepared_abandonments WHERE project=? AND run=?",e.ProjectID,e.RunID).Scan(&proofCount);err!=nil || proofCount!=0 {t.Fatalf("rejected footprint wrote proof: %d %v",proofCount,err)}
        })
    }
}
