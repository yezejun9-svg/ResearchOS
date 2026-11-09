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
    now:=time.Now().UTC();r.IssuedAt=now.Add(-59800*time.Millisecond).Format(time.RFC3339Nano);r.ExpiresAt=now.Add(200*time.Millisecond).Format(time.RFC3339Nano);digest=Hash(r)
    if _,err=f.db.Exec(`UPDATE idempotency SET request_hash=?,body=? WHERE operation='host:coding-confirmation' AND key=?`,digest,Bytes(r),id);err!=nil{t.Fatal(err)}
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
 for _,mode:=range []string{"streams_not_drained","cleanup_incomplete","missing_started_stage","foreign_receipt_epoch","foreign_context","missing_frozen_profile"}{
  t.Run(mode,func(t *testing.T){
   f,c,runID,key:=desktopExitFixture(t);ctx:=context.Background()
   sourceTx(t,f.db,func(tx *sql.Tx)error{
    switch mode{
    case "streams_not_drained","cleanup_incomplete":
     run,e:=load(tx,f.project,"Run",runID);if e!=nil{return e};o,e:=runtimeObservation(tx,f.project,run);if e!=nil{return e}
     field:="streams_drained";if mode=="cleanup_incomplete"{field="cleanup_complete"};o[field]=false
     if _,e=tx.Exec(`UPDATE runtime_observations SET body=?,receipt_hash=? WHERE project=? AND run=?`,Bytes(o),Hash(o),f.project,runID);e!=nil{return e}
     _,e=tx.Exec(`UPDATE runtime_dispatches SET observation_hash=? WHERE project=? AND run=?`,Hash(o),f.project,runID);return e
    case "missing_started_stage":_,e:=tx.Exec(`DELETE FROM resource_effects WHERE project=? AND run=? AND effect_key=? AND sequence=2`,f.project,runID,key);return e
    case "missing_frozen_profile":
     run,e:=load(tx,f.project,"Run",runID);if e!=nil{return e};d,e:=runtimeDispatch(tx,f.project,runID,run["lease_epoch"]);if e!=nil{return e}
     a:=d["manifest"].(map[string]any)["admission"].(map[string]any);ref:=a["profile_ref"].(map[string]any)
     _,e=tx.Exec(`DELETE FROM domain_objects WHERE project=? AND kind='Artifact' AND id=?`,f.project,ref["id"]);return e
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
 _,profile,err:=c.sessionModel(tx,f.project,Str(result,"model_config_ref"));if err!=nil{t.Fatal(err)}
 delete(profile,"coding_authorization")
 if err=c.validateCodingWorkspace(ctx,tx,f.owner,f.project,candidate.SessionID,in.WorkspaceRef,profile);err==nil{t.Fatal("coding reference downgraded to legacy model-only")}
}
