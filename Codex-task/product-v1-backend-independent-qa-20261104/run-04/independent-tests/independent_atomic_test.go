//go:build windows

package domain

import (
    "context"
    "database/sql"
    "sync/atomic"
    "testing"
    rt "researchos.local/research-os/adapters/runtime"
)

type independentHarnessTerminalFaultDriver struct {
    rt.CodexDriver
    db *sql.DB
    injected atomic.Bool
    starts atomic.Int32
}
type independentHarnessTerminalFaultHandle struct {
    rt.CodexHandle
    owner *independentHarnessTerminalFaultDriver
}
func (d *independentHarnessTerminalFaultDriver) Start(ctx context.Context,in rt.CodexLaunch,cb rt.CodexCallbacks)(rt.CodexHandle,error){
    d.starts.Add(1)
    handle,err:=d.CodexDriver.Start(ctx,in,cb)
    if err!=nil{return nil,err}
    return &independentHarnessTerminalFaultHandle{CodexHandle:handle,owner:d},nil
}
func (h *independentHarnessTerminalFaultHandle) Wait(ctx context.Context)(rt.CodexResult,error){
    result,err:=h.CodexHandle.Wait(ctx)
    if err!=nil{return result,err}
    // The owned fake process has already stopped and its earlier events committed.
    // Fault only the final EventEnvelope persistence window in this fresh DB.
    _,err=h.owner.db.Exec(`CREATE TRIGGER independent_terminal_event_failure BEFORE INSERT ON domain_objects WHEN NEW.kind='EventEnvelope' BEGIN SELECT RAISE(ABORT,'independent terminal event fault'); END;`)
    if err==nil{h.owner.injected.Store(true)}
    return result,err
}
func TestIndependentHarnessUnknownTerminalAtomic(t *testing.T){
    f,c,b:=harnessFixture(t,harnessExecutable(t))
    driver:=&independentHarnessTerminalFaultDriver{CodexDriver:c.config.HarnessDriver,db:f.db}
    c.config.HarnessDriver=driver
    _,_,id:=independentHarnessSubmit(t,f,c,b,"independent-unknown-atomic","UNKNOWN")
    if err:=c.Scan(context.Background());err!=nil{t.Fatal(err)}
    c.workers.Wait()
    if !driver.injected.Load(){t.Fatal("terminal persistence fault was not installed")}
    view:=harnessViewFixture(t,f,c,id)
    page,err:=c.HarnessV1().Events(context.Background(),f.token,HarnessEvents{ProjectID:f.project,TaskID:id,Cursor:"0",Limit:500})
    if err!=nil{t.Fatal(err)}
    data:=page["data"].(map[string]any)
    terminal:=0
    for _,value:=range Arr(data,"events"){
        if value.(map[string]any)["kind"]=="TASK_TERMINAL"{terminal++}
    }
    if view["terminal"]==true && terminal==0{
        t.Fatalf("terminal state committed without terminal event: status=%v terminal=%v end=%v",view["status"],view["terminal"],data["end"])
    }
    // Failure of event persistence must not turn the owned uncertain execution
    // into another launch opportunity. A later read-only reconciliation may
    // commit UNKNOWN and its event together once persistence recovers.
    if err=c.Scan(context.Background());err!=nil{t.Fatal(err)}
    c.workers.Wait()
    if driver.starts.Load()!=1{t.Fatal("terminal write fault allowed redispatch",driver.starts.Load())}
    if _,err=f.db.Exec(`DROP TRIGGER independent_terminal_event_failure`);err!=nil{t.Fatal(err)}
    if err=c.Recover(context.Background());err!=nil{t.Fatal(err)}
    if err=c.Scan(context.Background());err!=nil{t.Fatal(err)}
    c.workers.Wait()
    if driver.starts.Load()!=1{t.Fatal("read-only reconciliation relaunched",driver.starts.Load())}
    view=harnessViewFixture(t,f,c,id)
    page,err=c.HarnessV1().Events(context.Background(),f.token,HarnessEvents{ProjectID:f.project,TaskID:id,Cursor:"0",Limit:500})
    if err!=nil{t.Fatal(err)}
    data=page["data"].(map[string]any);terminal=0
    for _,value:=range Arr(data,"events"){if value.(map[string]any)["kind"]=="TASK_TERMINAL"{terminal++}}
    if view["status"]!="UNKNOWN" || view["terminal"]!=true || terminal!=1 || data["end"]!=true{t.Fatal("UNKNOWN reconciliation/event did not settle atomically",view,page)}
}
