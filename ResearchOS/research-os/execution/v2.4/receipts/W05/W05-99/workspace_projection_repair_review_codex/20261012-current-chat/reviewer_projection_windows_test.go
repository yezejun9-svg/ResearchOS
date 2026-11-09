//go:build windows

package domain

import (
 "context"
 "database/sql"
 "fmt"
 "reflect"
 "testing"
)

func TestIndependentProjectionMatrix(t *testing.T) {
 ctx:=context.Background()
 f:=contextFixture(t)
 doc:=clientHistoryDoc(t)
 svc:=&ClientService{Doc:doc,Domain:f.s,SessionRuntime:nextTurnFixturePort{}}
 run:=func(t *testing.T,fn func(*sql.Tx)) { t.Helper(); tx,e:=f.db.BeginTx(ctx,nil);if e!=nil{t.Fatal(e)};defer tx.Rollback();fn(tx) }
 put:=func(t *testing.T,tx *sql.Tx,b *WorkspaceBinding){t.Helper();if e:=f.s.putOpaque(ctx,tx,"",KindWorkspaceBinding,b.AuthorizedRef,b.record());e!=nil{t.Fatal(e)}}
 query:=func(t *testing.T,tx *sql.Tx,env *Envelope) []any { t.Helper();items,e:=svc.clientWorkspaceProjection(ctx,tx,env,f.owner);if e!=nil{t.Fatal(e)};return items }
 t.Run("empty_is_array",func(t *testing.T){run(t,func(tx *sql.Tx){if got:=query(t,tx,&Envelope{});got==nil||len(got)!=0{t.Fatal(got)}})})
 t.Run("two_project_filter_and_no_sensitive_fields",func(t *testing.T){run(t,func(tx *sql.Tx){
   project2:="review-project-two"
   if _,e:=tx.Exec("INSERT INTO auth_grants(principal,project,task,run,restricted) VALUES(?,?,'','',0)",f.owner,project2);e!=nil{t.Fatal(e)}
   put(t,tx,projectionBinding("z-two",f.owner,&project2,1));put(t,tx,projectionBinding("a-one",f.owner,&f.project,1));put(t,tx,projectionBinding("m-unbound",f.owner,nil,1))
   got:=query(t,tx,&Envelope{});if len(got)!=3 {t.Fatal(got)}
   for i,ref:=range []string{"a-one","m-unbound","z-two"}{o:=got[i].(Object);if o["authorized_workspace_ref"]!=ref||len(o)!=7{t.Fatal(got)}}
   filtered:=query(t,tx,&Envelope{ProjectID:&project2});if len(filtered)!=1||filtered[0].(Object)["authorized_workspace_ref"]!="z-two"{t.Fatal(filtered)}
 })})
 for _,tc:=range []struct{name,patch string}{
  {"id_mismatch","json_set(body,'$.authorized_workspace_ref','wrong')"},
  {"revision_mismatch","json_set(body,'$.revision',2)"},
  {"fractional_revision","json_set(body,'$.revision',1.5)"},
  {"missing_project","json_remove(body,'$.project_id')"},
  {"empty_project","json_set(body,'$.project_id','')"},
  {"bad_status","json_set(body,'$.status','BROKEN')"},
  {"bad_access","json_set(body,'$.access','OWNER')"},
  {"missing_path","json_remove(body,'$.display_path')"},
 } {t.Run(tc.name,func(t *testing.T){run(t,func(tx *sql.Tx){put(t,tx,projectionBinding("bad",f.owner,nil,1));if _,e:=tx.Exec("UPDATE domain_objects SET body="+tc.patch+" WHERE kind=? AND id='bad'",KindWorkspaceBinding);e!=nil{t.Fatal(e)};items,e:=svc.clientWorkspaceProjection(ctx,tx,&Envelope{},f.owner);fault,ok:=e.(*Fault);if !ok||fault.Code!="RESOURCE_BLOCKED"||items!=nil{t.Fatalf("bad state not blocked: %v %v",items,e)}})})}
 t.Run("revoked_binding_does_not_enable_session",func(t *testing.T){run(t,func(tx *sql.Tx){b:=projectionBinding("revoked-current",f.owner,&f.project,1);b.Status=WorkspaceRevoked;put(t,tx,b);got:=query(t,tx,&Envelope{});if len(got)!=1||got[0].(Object)["status"]!=WorkspaceRevoked{t.Fatal(got)};e:=svc.checkClientBinding(ctx,tx,f.owner,f.project,b.AuthorizedRef,"unused-model");fault,ok:=e.(*Fault);if !ok||fault.Code!="WORKSPACE_REVOKED"{t.Fatal(e)}})})
 t.Run("revoked_principal_and_credential",func(t *testing.T){run(t,func(tx *sql.Tx){
   if _,e:=tx.Exec("UPDATE auth_credentials SET revoked=1 WHERE principal=?",f.owner);e!=nil{t.Fatal(e)}
   if _,e:=authenticate(tx,f.token);e==nil{t.Fatal("revoked credential accepted")}
   if _,e:=tx.Exec("UPDATE auth_principals SET revoked=1 WHERE id=?",f.owner);e!=nil{t.Fatal(e)}
   if _,e:=svc.clientWorkspaceProjection(ctx,tx,&Envelope{},f.owner);e==nil{t.Fatal("revoked principal accepted")}
 })})
 t.Run("closed_transaction_does_not_return_empty_success",func(t *testing.T){tx,e:=f.db.BeginTx(ctx,nil);if e!=nil{t.Fatal(e)};tx.Rollback();if items,e:=svc.clientWorkspaceProjection(ctx,tx,&Envelope{},f.owner);e==nil||items!=nil{t.Fatalf("%v %v",items,e)}})
 t.Run("direct_execute_current_grants_and_original_replay",func(t *testing.T){run(t,func(tx *sql.Tx){
   put(t,tx,projectionBinding("fresh-binding",f.owner,&f.project,1))
   call:=func(id string,project any,payload Object)(*Response,bool){raw:=Bytes(Object{"protocol_version":ProtocolV2,"command_id":id,"client_id":"independent-review","project_id":project,"session_id":nil,"expected_revision":nil,"writer_epoch":nil,"method":"workspace.list","payload":payload});env,e:=decodeClientIdentityEnvelope(doc,raw);if e!=nil{t.Fatal(e)};r,replayed,e:=svc.Execute(ctx,tx,env,f.owner);if e!=nil{t.Fatal(e)};if e=ValidateResultAgainstMethod("workspace.list",r,doc);e!=nil{t.Fatal(e)};return r,replayed}
   first,replayed:=call("review-first",nil,Object{});if replayed||deref(first.Status)!="COMPLETED"||len(first.Result["items"].([]any))!=1{t.Fatal(first)}
   if _,e:=tx.Exec("DELETE FROM auth_grants WHERE principal=?",f.owner);e!=nil{t.Fatal(e)}
   fresh,_:=call("review-after-grant-loss",nil,Object{});if deref(fresh.Status)!="COMPLETED"||len(fresh.Result["items"].([]any))!=0{t.Fatal(fresh)}
   scoped,_:=call("review-unauthorized-project",f.project,Object{});if deref(scoped.Status)!="REJECTED"||deref(scoped.ErrorCode)!="FORBIDDEN"{t.Fatal(scoped)}
   old,replayed:=call("review-first",nil,Object{});if !replayed||!reflect.DeepEqual(Bytes(old),Bytes(first)){t.Fatalf("replay changed: %v",old)}
 })})
 t.Run("1000_foreign_rows_do_not_consume_limit",func(t *testing.T){run(t,func(tx *sql.Tx){for i:=0;i<1000;i++{put(t,tx,projectionBinding(fmt.Sprintf("foreign-%04d",i),"other-principal",nil,1))};put(t,tx,projectionBinding("own-only",f.owner,nil,1));if got:=query(t,tx,&Envelope{});len(got)!=1||got[0].(Object)["authorized_workspace_ref"]!="own-only"{t.Fatal(got)}})})
 t.Run("direct_schema_payload_protocol_and_native_rejections",func(t *testing.T){
   for _,patch:=range []Object{{"payload":Object{"unexpected":true}},{"protocol_version":"researchos-client/1"},{"method":"native.pickWorkspace"},{"payload":Object{"api_key":"fixture-only"}}}{raw:=Object{"protocol_version":ProtocolV2,"command_id":"bad-envelope","client_id":"review","project_id":nil,"session_id":nil,"expected_revision":nil,"writer_epoch":nil,"method":"workspace.list","payload":Object{}};for k,v:=range patch{raw[k]=v};if _,e:=decodeClientIdentityEnvelope(doc,Bytes(raw));e==nil{t.Fatalf("bad direct envelope accepted: %v",patch)}}
 })
}
