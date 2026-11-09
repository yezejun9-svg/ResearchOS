package domain

import (
 "context"
 "database/sql"
 "testing"
 "time"
)

func TestIndependentAttachBoundaryRefusals(t *testing.T) {
 for _, scenario := range []string{"duplicate-creation", "invalid-lease-same", "invalid-lease-other", "sealed", "archived", "future-cursor-same", "stale-revision", "invalid-host-ttl"} {
  t.Run(scenario,func(t *testing.T){
   f:=contextFixture(t);svc,sid,_:=handlerTypedSession(t,f,"first");svc.Host.LeaseTTL=time.Minute
   client,code:="second","WRITER_BUSY";rev,cursor:=int64(1),int64(0)
   exec:=func(q string,args ...any){t.Helper();if _,e:=f.db.Exec(q,args...);e!=nil{t.Fatal(e)}}
   exec("UPDATE client_sessions SET lease_expires_at=? WHERE id=?",time.Now().Add(-time.Minute).UTC().Format(time.RFC3339Nano),sid)
   switch scenario {
   case "duplicate-creation":
    code="FORBIDDEN";exec(`INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at) SELECT principal,project,operation,?,request_hash,status,body,headers,created_at FROM idempotency WHERE operation='v2:session.create'`,ID())
   case "invalid-lease-same": client="first";exec("UPDATE client_sessions SET lease_expires_at='not-time' WHERE id=?",sid)
   case "invalid-lease-other": exec("UPDATE client_sessions SET lease_expires_at='not-time' WHERE id=?",sid)
   case "sealed": code="SESSION_ARCHIVED";exec("UPDATE client_sessions SET sealed_at=? WHERE id=?",Now(),sid)
   case "archived": code="SESSION_ARCHIVED";exec("UPDATE client_sessions SET archived_at=? WHERE id=?",Now(),sid)
   case "future-cursor-same": client="first";cursor=1;code="CURSOR_INVALID"
   case "stale-revision": rev=1;code="VERSION_CONFLICT";exec("UPDATE client_sessions SET revision=2 WHERE id=?",sid)
   case "invalid-host-ttl": svc.Host.LeaseTTL=16*time.Minute
   }
   var before string
   if e:=f.db.QueryRow(`SELECT json_array(writer_client_id,writer_epoch,revision,event_watermark,lease_expires_at,updated_at) FROM client_sessions WHERE id=?`,sid).Scan(&before);e!=nil{t.Fatal(e)}
   env:=handlerDecode(t,&Envelope{ProtocolVersion:strptr(ProtocolV2),CommandID:strptr(ID()),ClientID:&client,ProjectID:&f.project,SessionID:&sid,ExpectedRevision:&rev,Method:strptr("session.attach"),Payload:Bytes(Object{"request_write_owner":true,"after_sequence":cursor})})
   tx,e:=f.db.Begin();if e!=nil{t.Fatal(e)}
   res,replay,e:=svc.Execute(context.Background(),tx,env,f.owner)
   if scenario=="invalid-host-ttl" {if e==nil || res!=nil || replay{t.Fatalf("invalid TTL accepted %s %v",Bytes(res),e)};if e=tx.Rollback();e!=nil{t.Fatal(e)}} else {
    if e!=nil{tx.Rollback();t.Fatal(e)}
    if deref(res.Status)!="REJECTED" || deref(res.ErrorCode)!=code {tx.Rollback();t.Fatalf("expected %s got %s",code,Bytes(res))}
    if e=tx.Commit();e!=nil{t.Fatal(e)}
   }
   var after string
   if e=f.db.QueryRow(`SELECT json_array(writer_client_id,writer_epoch,revision,event_watermark,lease_expires_at,updated_at) FROM client_sessions WHERE id=?`,sid).Scan(&after);e!=nil || before!=after{t.Fatalf("refusal mutated session before=%s after=%s err=%v",before,after,e)}
  })
 }
}

func TestIndependentAttachCanonicalRunBoundaries(t *testing.T){
 for _,scenario:=range []string{"active-same-renewal","active-task-no-head-run","historical-run-no-head-run"}{
  t.Run(scenario,func(t *testing.T){
   o:=orchestrationSetup(t);f:=o.f;svc,sid,_:=handlerTypedSession(t,f,"first");svc.Host.LeaseTTL=time.Minute
   task:=o.task("independent-"+scenario,Empty(),Empty());r:=o.claim(task)
   runID:=r.run["id"];client:="second";code:="SESSION_BUSY"
   if scenario=="active-same-renewal"{client="first";code=""}
   head:=runID;if scenario!="active-same-renewal"{head=nil}
   if _,e:=f.db.Exec(`UPDATE client_sessions SET task_id=?,run_id=?,lease_expires_at=? WHERE id=?`,task["id"],head,time.Now().Add(-time.Minute).UTC().Format(time.RFC3339Nano),sid);e!=nil{t.Fatal(e)}
   if scenario=="historical-run-no-head-run" {if _,e:=f.db.Exec(`UPDATE domain_objects SET body=json_set(body,'$.active_run_id',NULL,'$.status','ACCEPTED') WHERE project=? AND kind='Task' AND id=?`,f.project,task["id"]);e!=nil{t.Fatal(e)}}
   var beforeRun string;if e:=f.db.QueryRow(`SELECT body FROM domain_objects WHERE project=? AND kind='Run' AND id=?`,f.project,runID).Scan(&beforeRun);e!=nil{t.Fatal(e)}
   env:=handlerDecode(t,&Envelope{ProtocolVersion:strptr(ProtocolV2),CommandID:strptr(ID()),ClientID:&client,ProjectID:&f.project,SessionID:&sid,ExpectedRevision:revPtr(1),Method:strptr("session.attach"),Payload:Bytes(Object{"request_write_owner":true,"after_sequence":0})})
   sourceTx(t,f.db,func(tx *sql.Tx)error{res,_,e:=svc.Execute(context.Background(),tx,env,f.owner);if e!=nil{return e};if code=="" {if deref(res.Status)!="COMPLETED"{t.Fatalf("renewal blocked %s",Bytes(res))}} else if deref(res.Status)!="REJECTED" || deref(res.ErrorCode)!=code{t.Fatalf("unsafe grant %s",Bytes(res))};return nil})
   var epoch,revision,watermark int64;var writer,afterRun string
   if e:=f.db.QueryRow(`SELECT writer_epoch,revision,event_watermark,writer_client_id FROM client_sessions WHERE id=?`,sid).Scan(&epoch,&revision,&watermark,&writer);e!=nil{t.Fatal(e)}
   if epoch!=1 || revision!=1 || watermark!=0 || writer!="first"{t.Fatalf("unexpected generation mutation %d %d %d %s",epoch,revision,watermark,writer)}
   if e:=f.db.QueryRow(`SELECT body FROM domain_objects WHERE project=? AND kind='Run' AND id=?`,f.project,runID).Scan(&afterRun);e!=nil || beforeRun!=afterRun{t.Fatalf("run mutated %v",e)}
  })
 }
}
