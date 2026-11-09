//go:build windows
package host
import("context";"encoding/json";"fmt";"os";"path/filepath";"strings";"testing";"time";"researchos.local/research-os/internal/domain")
func reviewRewriteEventTimes(t *testing.T, f replacementFixture, times []string) {
 t.Helper();dir:=filepath.Join(f.Root,"host",replacementJournal,f.Input.OperationID);previous:=""
 for i,state:=range []string{"prepared","publishing","committed"} {path:=filepath.Join(dir,fmt.Sprintf("%04d-%s.json",i+1,state));raw,e:=os.ReadFile(path);if e!=nil{t.Fatal(e)};var ev replacementEvent;if e=json.Unmarshal(raw,&ev);e!=nil{t.Fatal(e)};ev.At=times[i];ev.Previous=previous;ev.Hash="";ev.Hash=domain.Hash(ev);previous=ev.Hash;replacementTestWrite(t,path,ev)}
}
func TestIndependentReviewIncreasingRFC3339Nano(t *testing.T) {
 f:=newReplacementFixture(t);in:=f.preflight(t);if out,e:=RuntimeVerifierReplacement(context.Background(),in);e!=nil{t.Fatalf("setup commit %+v %v",out,e)}
 times:=[]string{"2026-10-14T02:00:00.1Z","2026-10-14T02:00:00.11Z","2026-10-14T02:00:00.12Z"}
 for i:=1;i<len(times);i++ {a,_:=time.Parse(time.RFC3339Nano,times[i-1]);b,_:=time.Parse(time.RFC3339Nano,times[i]);if !b.After(a){t.Fatal("invalid probe setup")}}
 reviewRewriteEventTimes(t,f,times)
 if e:=replacementTestGate(f.Root);e!=nil{t.Errorf("chronologically increasing valid timestamp chain rejected: %v",e)}
 in.Action="recover";in.OperationID=f.Input.OperationID;in.RecoveryAction="inspect"
 if out,e:=RuntimeVerifierReplacement(context.Background(),in);e!=nil{t.Errorf("terminal inspect rejected valid timestamp chain: state=%s outcome=%s error=%v",out.State,out.Outcome,e)}
}
func TestIndependentReviewClockRegressionBetweenOperations(t *testing.T) {
 f:=newReplacementFixture(t);in:=f.preflight(t);result,e:=RuntimeVerifierReplacement(context.Background(),in);if e!=nil{t.Fatal(e)}
 future:=time.Now().UTC().Add(time.Hour).Truncate(time.Second);times:=[]string{future.Format(time.RFC3339Nano),future.Add(time.Second).Format(time.RFC3339Nano),future.Add(2*time.Second).Format(time.RFC3339Nano)};reviewRewriteEventTimes(t,f,times)
 if e=replacementTestGate(f.Root);e!=nil{t.Fatal("first valid operation",e)}
 rollback:=f.Input;rollback.OperationID=strings.Repeat("b",32);rollback.Out=filepath.Join(f.Base,"reverse.json");rollback.Manifest=f.OldManifest;raw,_:=os.ReadFile(f.OldManifest);rollback.ExpectManifestSHA256=domain.Digest(raw);rollback.ExpectRecordSHA256=result.NewRecordSHA256;rollback.RollbackOf=f.Input.OperationID
 planned,e:=RuntimeVerifierReplacement(context.Background(),rollback);if e!=nil{t.Fatal("reverse plan",e)}
 result,e=RuntimeVerifierReplacement(context.Background(),RuntimeVerifierReplacementInput{Action:"commit",DataRoot:f.Root,Plan:rollback.Out,ExpectPlanSHA256:planned.PlanSHA256});if e!=nil{t.Fatalf("valid reverse commit %+v %v",result,e)}
 t.Logf("reverse result before gate: %+v",result)
 if e=replacementTestGate(f.Root);e!=nil{t.Errorf("two committed causal transitions became unstartable after wall-clock correction: %v",e)}
}
func TestIndependentReviewDetachedGrantlessChild(t *testing.T) {
 f:=newReplacementFixture(t);f.exec(t,`UPDATE orchestration_identity SET root='foreign',parent='foreign' WHERE principal IN (SELECT principal FROM auth_grants WHERE project='project-b'); DELETE FROM auth_grants WHERE project='project-b'`)
 out,e:=RuntimeVerifierReplacement(context.Background(),f.Input)
 if e==nil{t.Errorf("detached grantless existing verifier child omitted from claimed all-child census: %+v",out)}else{t.Logf("rejected: %v",e)}
}
