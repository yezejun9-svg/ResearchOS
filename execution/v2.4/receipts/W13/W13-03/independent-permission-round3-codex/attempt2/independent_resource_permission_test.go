//go:build windows
package domain
import (
 "context"
 "database/sql"
 "testing"
 "time"
)
type independentResourcePermissionPort struct { *clientPermissionPort }
func (p *independentResourcePermissionPort) CheckPermission(ctx context.Context, tx *sql.Tx, project, session string, intent, record, scope Object) (bool, bool, error) {
 blocked, err := otherBlockingPermissionResources(tx, project, Str(intent,"run_id"), Str(record,"request_id"))
 return p.waiting, !blocked, err
}
func TestIndependentPermissionAllowWithOtherResourcePending(t *testing.T) {
 p := newPermissionFixture(t,"USER_DECIDABLE",time.Now().Add(time.Minute))
 f := p.o.f
 p.svc.SessionRuntime = &independentResourcePermissionPort{p.port}
 sourceTx(t,f.db,func(tx *sql.Tx) error {
  principal, err := clientPrincipal(context.Background(),tx,f.owner,f.project,true)
  if err != nil { return err }
  _,err = f.s.createResourceRequest(tx,principal,f.project,Object{"category":"PERMISSION","account_ref":nil,"reason_code":"INDEPENDENT_OTHER_RESOURCE","summary":"Another required resource remains pending","blocked_task_ids":[]any{p.r.task["id"]},"continuable_task_ids":Empty(),"completed_artifact_refs":Empty(),"requested_capability":"another resource","estimated_cost":nil,"cost_known":false,"resume_checkpoint_ref":nil})
  if err != nil {return err}
  blocked, err := otherBlockingPermissionResources(tx,f.project,Str(p.r.run,"id"),Str(p.request,"id"))
  if err != nil {return err}
  if !blocked {t.Fatal("independent setup did not produce another blocking ResourceRequest")}
  return nil
 })
 response,_ := executeWorkspaceTest(t,f,p.svc,p.envelope(t,"ALLOW_ONCE"))
 t.Logf("observed response: %s",Bytes(response))
 if deref(response.Status)!="COMPLETED" || response.Result["resumption_scheduled"]!=false {
  t.Fatalf("section 7 requires recording an otherwise valid original decision with resumption_scheduled=false while another resource is pending")
 }
}


type independentPermissionTranscriptFootprint struct {
 TaskID, RunID, Digest, ScopeHash, ArgumentsHash string
 TaskCount, RunCount, ToolEffects int
}
func independentPermissionTranscriptCheck(t *testing.T, f *fixture, doc *SchemaDoc, sessionID, runID, requestID string, reseal, expectAssistant bool) independentPermissionTranscriptFootprint {
 t.Helper()
 var footprint independentPermissionTranscriptFootprint
 sourceTx(t, f.db, func(tx *sql.Tx) error {
  snapshot, err := BuildSessionSnapshot(context.Background(), tx, doc, f.project, sessionID)
  if err != nil { return err }
  reference, ok := snapshot["transcript_artifact_ref"].(map[string]any)
  if !ok || reference["id"] == "" { t.Fatal("production USER send did not leave a sealed transcript reference") }
  _, body, err := permissionArtifact(tx,f.project,reference)
  if err != nil { return err }
  if body["schema"] != "researchos.session-transcript.v1" || body["session_id"] != sessionID || len(Arr(body,"messages")) == 0 { t.Fatal("transcript artifact does not contain the original journal") }
  if expectAssistant {
   assistant := false
   for _, value := range Arr(body,"messages") { m:=value.(map[string]any); assistant=assistant || m["role"]=="ASSISTANT" && m["complete"]==true }
   if !assistant { t.Fatal("settled allowed tool lacks newly sealed complete ASSISTANT transcript") }
  }
  intent, record, scope, _, err := loadClientPermission(tx,f.project,sessionID,requestID)
  if err != nil { return err }
  footprint.Digest=Str(record,"action_digest"); footprint.ScopeHash=Hash(record["scope_ref"]); footprint.ArgumentsHash=Hash(scope["arguments_artifact_ref"])
  if err=tx.QueryRow("SELECT task_id,run_id FROM client_sessions WHERE id=?",sessionID).Scan(&footprint.TaskID,&footprint.RunID); err!=nil {return err}
  if footprint.RunID != runID || footprint.TaskID != scope["task_id"] || runID != scope["run_id"] || Hash(scope) != footprint.Digest { t.Fatal("original permission binding changed") }
  if err=tx.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Task'",f.project).Scan(&footprint.TaskCount); err!=nil {return err}
  if err=tx.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Run'",f.project).Scan(&footprint.RunCount); err!=nil {return err}
  if err=tx.QueryRow("SELECT count(DISTINCT effect_key) FROM resource_effects WHERE project=? AND run=? AND json_extract(body,'$.payload.capability')='TOOL'",f.project,runID).Scan(&footprint.ToolEffects); err!=nil {return err}
  if footprint.ToolEffects!=1 {t.Fatalf("expected one original tool effect, got %d",footprint.ToolEffects)}
  if reseal {
   if intent["state"]!="STARTED" || record["decision"]!=nil || len(Arr(snapshot,"pending_permissions"))!=1 { t.Fatal("reseal setup is not the original undecided permission waiter") }
   taskBefore,err:=load(tx,f.project,"Task",footprint.TaskID); if err!=nil{return err}
   runBefore,err:=load(tx,f.project,"Run",runID); if err!=nil{return err}
   if err=transcriptAppend(context.Background(),tx,doc,f.project,sessionID,ID(),"Permission wait observation: new journal bytes", "SYSTEM"); err!=nil{return err}
   if err=f.s.sealSessionTranscript(context.Background(),tx,doc,f.project,sessionID,f.owner); err!=nil{return err}
   after,err:=BuildSessionSnapshot(context.Background(),tx,doc,f.project,sessionID); if err!=nil{return err}
   nextRef,ok:=after["transcript_artifact_ref"].(map[string]any)
   if !ok || nextRef["id"]==reference["id"] { t.Fatal("independent reseal did not create a new sealed transcript artifact") }
   _,nextBody,err:=permissionArtifact(tx,f.project,nextRef); if err!=nil{return err}
   oldMessages, newMessages := Arr(body,"messages"), Arr(nextBody,"messages")
   if len(newMessages)!=len(oldMessages)+1 || Hash(newMessages[:len(oldMessages)])!=Hash(oldMessages) || newMessages[len(oldMessages)].(map[string]any)["role"]!="SYSTEM" || Hash(after["pending_permissions"])!=Hash(snapshot["pending_permissions"]) { t.Fatal("new transcript artifact lost earlier bytes, omitted the new SYSTEM observation, or changed pending frozen action") }
   taskAfter,err:=load(tx,f.project,"Task",footprint.TaskID); if err!=nil{return err}
   runAfter,err:=load(tx,f.project,"Run",runID); if err!=nil{return err}
   if Hash(taskBefore)!=Hash(taskAfter) || Hash(runBefore)!=Hash(runAfter) {t.Fatal("transcript reseal mutated original Task or Run")}
  } else if len(Arr(snapshot,"pending_permissions"))!=0 { t.Fatal("resolved/expired permission remained pending after transcript integration") }
  return nil
 })
 return footprint
}
