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
