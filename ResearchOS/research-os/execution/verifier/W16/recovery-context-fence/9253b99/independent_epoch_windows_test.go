//go:build windows

package supervisor

import (
 "context"
 "errors"
 "strings"
 "testing"
 rt "researchos.local/research-os/adapters/runtime"
)

// Public journal callback only; no process is started or native restoration invoked.
func TestIndependentRecoveryEpochRefresh(t *testing.T) {
 for _,fails:=range []bool{false,true} {
  name:="success";if fails {name="error"}
  t.Run(name,func(t *testing.T){
   j,s:=recoveryJournalFixture(t)
   driver:=&ControlFixtureDriver{Journal:j,Restore:func(context.Context,ReleaseState,*rt.DataRootLease)(string,error){
    changed:=j.State();changed.Epoch++
    changed.AdmissionBundle.ExpectedEpoch++;changed.Admission=releaseHash(*changed.AdmissionBundle);changed.Cutover.Epoch=changed.Epoch
    if e:=j.Append(changed);e!=nil {t.Fatal(e)}
    if fails {return "",errors.New("synthetic interrupted restore")};return s.Data,nil
   }}
   engine,e:=NewReleaseEngine(j,driver,driver,func(ReleaseAdmission)error{return nil});if e!=nil {t.Fatal(e)}
   got,e:=engine.RollbackFixture(context.Background(),s.Operation)
   if e==nil||!strings.Contains(e.Error(),"restore changed journal operation or epoch")||got.Epoch!=s.Epoch+1||j.State().Epoch!=got.Epoch||got.Operation!=s.Operation {t.Fatal("stale same-operation epoch overwritten",e)}
  })
 }
}
