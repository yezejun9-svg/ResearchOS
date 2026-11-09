//go:build windows

package domain

import (
 "context"
 "database/sql"
 "testing"
 "time"
)

// Mutation occurs in the review's isolated fixture while the real confirmation
// is between its first binding read and its final installation transaction.
func TestReviewerCodingFreezeTOCTOU(t *testing.T) {
 for _, mode := range []string{"writer_epoch", "workspace_revision", "owner_revoked", "real_expiry"} {
  t.Run(mode,func(t *testing.T){
   f,c,candidate,in,freeze:=codingFixture(t);ctx:=context.Background()
   prepared,err:=c.PrepareRuntimeCoding(ctx,f.token,"parent",candidate,in,freeze);if err!=nil{t.Fatal(err)}
   id,digest:=Str(prepared,"request_id"),Str(prepared,"request_hash")
   if mode=="real_expiry" {
    tx,err:=f.db.BeginTx(ctx,nil);if err!=nil{t.Fatal(err)}
    r,err:=c.loadCodingConfirmation(ctx,tx,f.token,f.project,id,digest);tx.Rollback();if err!=nil{t.Fatal(err)}
    now:=time.Now().UTC();r.IssuedAt=now.Add(-59800*time.Millisecond).Format(time.RFC3339Nano);r.ExpiresAt=now.Add(200*time.Millisecond).Format(time.RFC3339Nano);r.RequestID=ID();id=r.RequestID;digest=Hash(r)
    if _,err=f.db.Exec(`INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at) VALUES(?,?,'host:coding-confirmation',?,?,200,?,'{}',?)`,f.owner,f.project,id,digest,Bytes(r),Now());err!=nil{t.Fatal(err)}
   }
   entered:=false
   during:=func(ctx context.Context,b WorkspaceBinding,i RuntimeCodingIntent)(Object,error){
    entered=true;v,err:=freeze(ctx,b,i);if err!=nil{return nil,err}
    switch mode {
    case "writer_epoch":_,err=f.db.Exec(`UPDATE client_sessions SET writer_epoch=writer_epoch+1 WHERE id=?`,candidate.SessionID)
    case "workspace_revision":
     sourceTx(t,f.db,func(tx *sql.Tx)error{w,e:=f.s.binding(ctx,tx,in.WorkspaceRef);if e!=nil{return e};w.Revision++;return f.s.putOpaque(ctx,tx,"",KindWorkspaceBinding,w.AuthorizedRef,w.record())})
    case "owner_revoked":err=f.s.RevokePrincipal(ctx,f.owner)
    case "real_expiry":time.Sleep(250*time.Millisecond)
    }
    return v,err
   }
   if _,err=c.ConfirmRuntimeCoding(ctx,f.token,"parent",f.project,id,digest,during);err==nil{t.Fatal("changed confirmation installed")}
   if !entered{t.Fatal("fixture missed target freeze boundary")}
   var count int;var ref string
   if err=f.db.QueryRow(`SELECT count(*) FROM idempotency WHERE operation IN ('host:coding-installation','host:coding-authorization')`).Scan(&count);err!=nil||count!=0{t.Fatalf("authority leaked %d %v",count,err)}
   if err=f.db.QueryRow(`SELECT model_config_ref FROM client_sessions WHERE id=?`,candidate.SessionID).Scan(&ref);err!=nil||ref!=candidate.ModelRef{t.Fatal("session config advanced")}
   t.Logf("freeze boundary %s refused with zero installations and original model reference",mode)
  })
 }
}

func TestReviewerCodingDesktopExitAdditionalProofGaps(t *testing.T) {
 for _,mode:=range []string{"streams_not_drained","cleanup_incomplete","missing_started_stage","foreign_receipt_epoch","foreign_context","frozen_version_store_unavailable"}{
  t.Run(mode,func(t *testing.T){
   f,c,runID,key:=reviewerDesktopExitFixture(t,mode);ctx:=context.Background()
   sourceTx(t,f.db,func(tx *sql.Tx)error{
    switch mode{
    case "frozen_version_store_unavailable":
     _,e:=tx.Exec(`ALTER TABLE domain_versions RENAME TO reviewer_unavailable_versions`);return e
    case "streams_not_drained","cleanup_incomplete","missing_started_stage":
     return nil // Injected before the fixture's immutable evidence is sealed.
    default:
     effect,e:=latestEffect(tx,f.project,runID,key);if e!=nil{return e}
     if mode=="foreign_receipt_epoch"{effect["receipt"].(map[string]any)["epoch"]=2}else{effect["context_bundle_id"]="other-context"}
     return effectAppend(tx,f.project,runID,key,effect)
    }
   })
   var before,after string
   if err:=f.db.QueryRow(`SELECT group_concat(body) FROM domain_objects WHERE kind='BudgetLedgerEntry'`).Scan(&before);err!=nil{t.Fatal(err)}
   c.intakeClosed.Store(true)
   if _,err:=c.QuiesceForDesktopExit(ctx);err==nil{t.Fatal("missing or foreign proof allowed exit")}
   if c.ClientIntakeOpen(){t.Fatal("failed exit removed prior admission closure")}
   if err:=f.db.QueryRow(`SELECT group_concat(body) FROM domain_objects WHERE kind='BudgetLedgerEntry'`).Scan(&after);err!=nil||before!=after{t.Fatal("ledger mutated")}
   t.Logf("%s retained shutdown barrier and immutable UNKNOWN ledger",mode)
  })
 }
}

func TestReviewerCodingAuthorizationCannotDisappear(t *testing.T){
 f,c,candidate,in,freeze:=codingFixture(t);ctx:=context.Background()
 prepared,err:=c.PrepareRuntimeCoding(ctx,f.token,"parent",candidate,in,freeze);if err!=nil{t.Fatal(err)}
 result,err:=c.ConfirmRuntimeCoding(ctx,f.token,"parent",f.project,Str(prepared,"request_id"),Str(prepared,"request_hash"),freeze);if err!=nil{t.Fatal(err)}
 tx,err:=f.db.BeginTx(ctx,nil);if err!=nil{t.Fatal(err)};defer tx.Rollback()
 runtime,err:=load(tx,f.project,"RuntimeRegistration",Str(result,"runtime_id"));if err!=nil{t.Fatal(err)}
 _,artifact,err:=c.service.currentRuntimeBinding(tx,f.project,runtime);if err!=nil{t.Fatal(err)}
 profile,err:=runtimeProfileBody(tx,f.project,artifact);if err!=nil{t.Fatal(err)}
 delete(profile,"coding_authorization")
 if err=c.validateCodingWorkspace(ctx,tx,f.owner,f.project,candidate.SessionID,in.WorkspaceRef,profile);err==nil{t.Fatal("coding reference downgraded to legacy model-only")}
}

func reviewerDesktopExitFixture(t *testing.T, mode string) (*fixture, *RuntimeCoordinator, string, string) {
	t.Helper()
	f, c, r, executor := confirmationFixture(t)
	ctx := context.Background()
	run, _, e := c.beginManagedLocalQualification(ctx, f.token, r, executor)
	if e != nil {
		t.Fatal(e)
	}
	runID := Str(run, "id")
	key := r.TaskID + ":" + runID + ":1:model:1"
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		task, e := load(tx, f.project, "Task", r.TaskID)
		if e != nil {
			return e
		}
		dispatch, e := runtimeDispatch(tx, f.project, runID, 1)
		if e != nil {
			return e
		}
		manifest := dispatch["manifest"].(map[string]any)
		admission := manifest["admission"].(map[string]any)
		profile := admission["profile"].(map[string]any)
		config := profile["model_config"].(map[string]any)
		goal, e := load(tx, f.project, "Goal", Str(task, "goal_id"))
		if e != nil {
			return e
		}
		request := Object{"route": config["route"], "capability": "MODEL", "credential_revision": "none", "payload": Object{"body": Object{"model": config["model"], "stream": true, "max_tokens": 32, "messages": []any{Object{"role": "user", "content": "fixture"}}}}}
		cost := Object{"policy_id": goal["budget_policy_id"], "run_id": runID, "operation": "UNKNOWN", "money": nil, "provider_request_id": key, "provider_event_id": "prepare/" + key, "reservation_id": nil, "cost_basis": "UNKNOWN", "occurred_at": run["created_at"]}
		effect, e := c.service.prepareEffectTx(tx, c.schedulerCredential(f.project), f.project, runID, key, request, cost)
		if e != nil {
			return e
		}
		if mode != "missing_started_stage" { effect, e = c.service.beginEffectTx(tx, c.schedulerCredential(f.project), f.project, runID, key) }
		if e != nil {
			return e
		}
		raw := []byte("data: {\"choices\":[{\"index\":0,\"delta\":{\"content\":\"fixture\"},\"finish_reason\":\"stop\"}]}\n\ndata: [DONE]\n\n")
		receipt := Object{"key": key, "epoch": 1, "run_id": runID, "receipt_id": Digest(raw), "state": "CONFIRMED", "model_transport": true, "actual_cost": nil, "payload": Object{"status": 200, "content_type": "text/event-stream", "body": string(raw)}}
		effect["state"], effect["receipt"] = "CONFIRMED", receipt
		if e = effectAppend(tx, f.project, runID, key, effect); e != nil {
			return e
		}
		identity := Object{"pid": 12345, "created": 123, "image": "fixture"}
		observation := Object{"state": "SETTLED", "children_stopped": true, "queue_empty": true, "streams_drained": true, "cleanup_complete": true, "ended": Now(), "dispatch_key": dispatch["dispatch_key"], "manifest_hash": dispatch["manifest_hash"], "worker": "fixture-worker", "identity": identity, "observation_sequence": 1, "spec": Object{"profile_hash": admission["profile_hash"], "run_id": runID, "task_id": task["id"], "epoch": 1}}
        if mode == "streams_not_drained" { observation["streams_drained"] = false }
        if mode == "cleanup_incomplete" { observation["cleanup_complete"] = false }

		if _, e = tx.Exec(`UPDATE runtime_dispatches SET state='OBSERVED',worker='fixture-worker',journal_locator=dispatch_key,identity=?,observation_sequence=1,observation_hash=? WHERE project=? AND run=?`, Bytes(identity), Hash(observation), f.project, runID); e != nil {
			return e
		}
		if _, e = tx.Exec(`INSERT INTO runtime_observations(project,run,epoch,receipt_hash,body,observed_at) VALUES(?,?,1,?,?,?)`, f.project, runID, Hash(observation), Bytes(observation), Now()); e != nil {
			return e
		}
		run["status"], run["children_stopped"], run["queue_empty"], run["ended_at"], run["runtime_settled_at"] = "SETTLED", true, true, Now(), Now()
		if e = bump(run); e != nil {
			return e
		}
		if e = f.s.put(tx, "Run", run); e != nil {
			return e
		}
		return f.s.releaseQualificationReservation(tx, f.project, run)
	})
	return f, c, runID, key
}
