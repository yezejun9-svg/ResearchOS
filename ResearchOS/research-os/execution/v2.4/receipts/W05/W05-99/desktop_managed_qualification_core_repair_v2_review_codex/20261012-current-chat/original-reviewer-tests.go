//go:build windows
package domain
import ("context";"testing";"path/filepath")
func TestReviewerRefusedShutdownPreservesManagedIntakeFence(t *testing.T) {
 f,c,r,executor:=confirmationFixture(t);ctx:=context.Background()
 if e:=c.BeginLocalQualificationWindow(ctx,r.RequestID);e!=nil{t.Fatal(e)}
 run,_,e:=c.beginManagedLocalQualification(ctx,f.token,r,executor);if e!=nil{t.Fatal(e)}
 if e=c.EndLocalQualificationWindow(ctx);e==nil{t.Fatal("unsettled qualification unexpectedly finished")}
 if c.ClientIntakeOpen(){t.Fatal("baseline intake not fenced")}
 before:=localSetupCensus(t,f)
 snap,e:=c.QuiesceForRelease(ctx)
 if e==nil{t.Fatal("outstanding qualification incorrectly accepted shutdown")}
 if localSetupCensus(t,f)!=before{t.Fatal("refused shutdown changed original Run/effect counters")}
 t.Logf("original Run=%s status=%s refusedShutdown=%v activeRuns=%d qualificationActive=%v intakeOpen=%v",Str(run,"id"),Str(run,"status"),e,snap.ActiveRuns,c.qualificationActive,c.ClientIntakeOpen())
 if e=c.Scan(ctx);e!=nil{t.Fatal(e)}
 if c.ClientIntakeOpen(){t.Fatal("P1: refused SHUTDOWN permanently reopened session intake while original managed qualification remains unresolved")}
}

func TestReviewerRestartRestoresIntakeFenceBeforeScan(t *testing.T) {
 f,c,r,executor:=confirmationFixture(t);ctx:=context.Background()
 if _,_,e:=c.beginManagedLocalQualification(ctx,f.token,r,executor);e!=nil{t.Fatal(e)}
 var seq int;var name,path string
 if e:=f.db.QueryRow("PRAGMA database_list").Scan(&seq,&name,&path);e!=nil{t.Fatal(e)}
 config:=c.config;config.APIURL="http://127.0.0.1:1";config.DataRoot=filepath.Dir(path)
 restarted,e:=f.s.NewRuntimeCoordinator(ctx,config);if e!=nil{t.Fatal(e)};defer restarted.Close()
 if restarted.ClientIntakeOpen(){t.Fatal("P1: actual coordinator constructor exposed open session intake before first Scan despite durable unresolved managed Run")}
}
func TestReviewerManagedStartupHoldClosesIntakeBeforeScan(t *testing.T) {
 f,c,_,_:=confirmationFixture(t);ctx:=context.Background()
 var seq int;var name,path string
 if e:=f.db.QueryRow("PRAGMA database_list").Scan(&seq,&name,&path);e!=nil{t.Fatal(e)}
 config:=c.config;config.APIURL="http://127.0.0.1:1";config.DataRoot=filepath.Dir(path);config.ManagedStartupHold=true
 restarted,e:=f.s.NewRuntimeCoordinator(ctx,config);if e!=nil{t.Fatal(e)};defer restarted.Close()
 if e=restarted.Scan(ctx);e!=nil{t.Fatal(e)}
 if restarted.ClientIntakeOpen(){t.Fatal("P1: ManagedStartupHold blocks Scan but leaves session intake open")}
}
