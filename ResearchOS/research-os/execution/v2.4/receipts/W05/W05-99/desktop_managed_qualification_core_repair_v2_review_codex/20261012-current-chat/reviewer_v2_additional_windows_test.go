//go:build windows
package domain
import("context";"testing")
func TestReviewerV2TerminalRunUnknownRetainsAdmissionFence(t *testing.T){
 for _,hold:=range []bool{false,true}{name:="durable_unknown_only";if hold{name="durable_unknown_and_managed_hold"};t.Run(name,func(t *testing.T){
  f,c,r,executor:=confirmationFixture(t);ctx:=context.Background()
  run,_,err:=c.beginManagedLocalQualification(ctx,f.token,r,executor);if err!=nil{t.Fatal(err)}
  // Isolated fault fixture: terminal Run with independently unresolved original MODEL effect.
  if _,err=f.db.Exec(`UPDATE domain_objects SET body=json_set(body,'$.status','SETTLED') WHERE project=? AND kind='Run' AND id=?`,f.project,run["id"]);err!=nil{t.Fatal(err)}
  if _,err=f.db.Exec(`INSERT INTO resource_effects(project,run,effect_key,sequence,body) VALUES(?,?,?,1,?)`,f.project,run["id"],"reviewer-original-model",Bytes(Object{"state":"UNKNOWN"}));err!=nil{t.Fatal(err)}
  config:=qualificationFenceConfig(t,f,c);config.ManagedStartupHold=hold
  restarted,err:=f.s.NewRuntimeCoordinator(ctx,config);if err!=nil{t.Fatal(err)};defer restarted.Close()
  before:=localSetupCensus(t,f)
  requireQualificationSessionFence(t,f,restarted,r)
  restarted.startupComplete=true
  if _,err=restarted.QuiesceForRelease(ctx);err==nil{t.Fatal("UNKNOWN effect permitted shutdown")}
  requireQualificationSessionFence(t,f,restarted,r)
  restarted.ResumeAfterReleaseAbort();requireQualificationSessionFence(t,f,restarted,r)
  if err=restarted.Scan(ctx);err!=nil{t.Fatal(err)};requireQualificationSessionFence(t,f,restarted,r)
  if before!=localSetupCensus(t,f){t.Fatal("original evidence modified")}
 })}
}
func TestReviewerV2ConstructorFailureReleasesOwnedLease(t *testing.T){
 f,c,_,_:=confirmationFixture(t);config:=qualificationFenceConfig(t,f,c)
 if _,err:=f.db.Exec(`ALTER TABLE idempotency RENAME TO reviewer_unreadable_idempotency`);err!=nil{t.Fatal(err)}
 got,err:=f.s.NewRuntimeCoordinator(context.Background(),config);if err==nil||got!=nil{t.Fatal("observation failure exposed coordinator")}
 if _,err=f.db.Exec(`ALTER TABLE reviewer_unreadable_idempotency RENAME TO idempotency`);err!=nil{t.Fatal(err)}
 restored,err:=f.s.NewRuntimeCoordinator(context.Background(),config);if err!=nil{t.Fatalf("constructor leaked owned lease: %v",err)}
 if !restored.ClientIntakeOpen(){t.Fatal("normal recovered constructor closed")}
 if err=restored.Close();err!=nil{t.Fatal(err)}
 second,err:=f.s.NewRuntimeCoordinator(context.Background(),config);if err!=nil{t.Fatalf("Close leaked owned lease: %v",err)};defer second.Close()
}
