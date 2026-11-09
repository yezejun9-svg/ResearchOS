//go:build windows

package domain

import (
    "context"
    "database/sql"
    "strings"
    "sync/atomic"
    "testing"
    rt "researchos.local/research-os/adapters/runtime"
)

type independentHarnessCountingDriver struct { rt.CodexDriver; starts atomic.Int32 }
func (d *independentHarnessCountingDriver) Start(ctx context.Context, in rt.CodexLaunch, cb rt.CodexCallbacks) (rt.CodexHandle,error) {
    d.starts.Add(1)
    return d.CodexDriver.Start(ctx,in,cb)
}
func independentHarnessSubmit(t *testing.T,f *fixture,c *RuntimeCoordinator,b *WorkspaceBinding,key,prompt string)(HarnessSubmit,Object,string){
    t.Helper()
    in:=HarnessSubmit{RequestID:key,ProjectID:f.project,WorkspaceRef:b.AuthorizedRef,HarnessID:"codex",Scope:"workspace-read",Prompt:prompt}
    ack,err:=c.HarnessV1().Submit(context.Background(),f.token,in)
    if err!=nil { t.Fatal(err) }
    data:=ack["data"].(map[string]any)
    if data["run"]!=nil || data["status"]!="QUEUED" { t.Fatal("ACK fabricated run/completion",ack) }
    id:=Str(data["task_ref"].(map[string]any),"task_id")
    if id=="" { t.Fatal("missing immutable task locator") }
    return in,ack,id
}
func independentHarnessCount(t *testing.T,db *sql.DB,query string,args ...any)int{
    t.Helper();var n int
    if err:=db.QueryRow(query,args...).Scan(&n);err!=nil { t.Fatal(err) }
    return n
}
func TestIndependentHarnessLostACKNeverRedispatch(t *testing.T){
    f,c,b:=harnessFixture(t,harnessExecutable(t))
    counting:=&independentHarnessCountingDriver{CodexDriver:c.config.HarnessDriver}
    c.config.HarnessDriver=counting
    port:=c.HarnessV1()
    in,original,id:=independentHarnessSubmit(t,f,c,b,"independent-lost-ack","UNKNOWN")
    // The renderer lost the ACK; recover by original request locator, never a new mutation.
    lookup,err:=port.List(context.Background(),f.token,HarnessList{ProjectID:f.project,RequestID:in.RequestID,Cursor:"0",Limit:1})
    if err!=nil { t.Fatal(err) }
    data:=lookup["data"].(map[string]any)
    items:=Arr(data,"items")
    if Str(data["lookup"].(map[string]any),"state")!="FOUND" || len(items)!=1 || Str(items[0].(map[string]any)["task_ref"].(map[string]any),"task_id")!=id { t.Fatal("lost ACK lookup did not recover original task",lookup) }
    if counting.starts.Load()!=0 { t.Fatal("submission/lookup launched before sole Scan") }
    if err=c.Scan(context.Background());err!=nil { t.Fatal(err) };c.workers.Wait()
    if view:=harnessViewFixture(t,f,c,id);view["status"]!="UNKNOWN" { t.Fatal("missing terminal protocol was not UNKNOWN",view) }
    for i:=0;i<2;i++{
        replay,e:=port.Submit(context.Background(),f.token,in)
        if e!=nil || Hash(replay)!=Hash(original) { t.Fatal("replay replaced original ACK",e,replay) }
        if e=c.Recover(context.Background());e!=nil { t.Fatal(e) }
        if e=c.Scan(context.Background());e!=nil { t.Fatal(e) };c.workers.Wait()
    }
    if counting.starts.Load()!=1 { t.Fatal("UNKNOWN replay/recovery redispatched",counting.starts.Load()) }
    if n:=independentHarnessCount(t,f.db,`SELECT count(*) FROM domain_objects WHERE project=? AND kind='Run' AND json_extract(body,'$.task_id')=?`,f.project,id);n!=1 { t.Fatal("duplicate authoritative Run",n) }
}

func TestIndependentHarnessQueuedCancelCASAndACK(t *testing.T){
    f,c,b:=harnessFixture(t,harnessExecutable(t));port:=c.HarnessV1()
    _,_,id:=independentHarnessSubmit(t,f,c,b,"independent-cancel-task","COMPLETE")
    view:=harnessViewFixture(t,f,c,id)
    stale:=HarnessCancel{RequestID:"independent-stale-cancel",ExpectedTaskRevision:"9223372036854775807"}
    if _,err:=port.Cancel(context.Background(),f.token,f.project,id,stale);err==nil { t.Fatal("stale queued revision accepted") }
    in:=HarnessCancel{RequestID:"independent-exact-cancel",ExpectedTaskRevision:Str(view,"task_revision")}
    ack,err:=port.Cancel(context.Background(),f.token,f.project,id,in)
    if err!=nil { t.Fatal(err) }
    if ack["data"].(map[string]any)["disposition"]!="CANCELLED_BEFORE_LAUNCH" { t.Fatal(ack) }
    before:=independentHarnessCount(t,f.db,`SELECT count(*) FROM outbox WHERE project=? AND json_extract(body,'$.aggregate_ref.id')=?`,f.project,id)
    replay,err:=port.Cancel(context.Background(),f.token,f.project,id,in)
    if err!=nil || Hash(replay)!=Hash(ack) { t.Fatal("cancel ACK replay changed",err,replay) }
    if after:=independentHarnessCount(t,f.db,`SELECT count(*) FROM outbox WHERE project=? AND json_extract(body,'$.aggregate_ref.id')=?`,f.project,id);before!=after { t.Fatal("cancel replay emitted another event",before,after) }
    in.ExpectedTaskRevision="9223372036854775807"
    if _,err=port.Cancel(context.Background(),f.token,f.project,id,in);err==nil { t.Fatal("same cancel key changed body was accepted") }
    if err=c.Scan(context.Background());err!=nil { t.Fatal(err) };c.workers.Wait()
    if n:=independentHarnessCount(t,f.db,`SELECT count(*) FROM domain_objects WHERE project=? AND kind='Run' AND json_extract(body,'$.task_id')=?`,f.project,id);n!=0 { t.Fatal("queued cancelled task launched",n) }
}

func TestIndependentHarnessTaskCursorAndInt64(t *testing.T){
    f,c,b:=harnessFixture(t,harnessExecutable(t));port:=c.HarnessV1().(*harnessV1)
    _,_,one:=independentHarnessSubmit(t,f,c,b,"independent-cursor-one","COMPLETE")
    _,_,two:=independentHarnessSubmit(t,f,c,b,"independent-cursor-two","COMPLETE")
    other,err:=port.Events(context.Background(),f.token,HarnessEvents{ProjectID:f.project,TaskID:two,Cursor:"0",Limit:10})
    if err!=nil { t.Fatal(err) }
    otherCursor:=Str(other["data"].(map[string]any),"next_cursor")
    sourceTx(t,f.db,func(tx *sql.Tx)error{
        // Seed only the outbox allocator in this fresh fixture. The placeholder is not
        // a Task event and is never presented as a real canonical observation.
        if _,e:=tx.Exec(`INSERT INTO outbox(project,sequence,id,body) VALUES(?,?,?,?)`,f.project,int64(9007199254740990),ID(),`{}`);e!=nil{return e}
        task,e:=load(tx,f.project,"Task",one);if e!=nil{return e}
        _,e=port.emit(tx,f.owner,f.project,task,nil,"LOG",Object{"text":"independent high sequence"});return e
    })
    reset,err:=port.Events(context.Background(),f.token,HarnessEvents{ProjectID:f.project,TaskID:one,Cursor:otherCursor,Limit:10})
    if err!=nil { t.Fatal(err) }
    rd:=reset["data"].(map[string]any)
    if rd["reset"]!=true || len(Arr(rd,"events"))!=0 || Str(rd,"next_cursor")!="9007199254740991" || Str(rd["snapshot"].(map[string]any)["task_ref"].(map[string]any),"task_id")!=one { t.Fatal("foreign task cursor mixed state or rounded tail",reset) }
    first,err:=port.Events(context.Background(),f.token,HarnessEvents{ProjectID:f.project,TaskID:one,Cursor:"0",Limit:1})
    if err!=nil { t.Fatal(err) };fd:=first["data"].(map[string]any)
    if fd["has_more"]!=true || fd["end"]!=false || fd["snapshot"]!=nil { t.Fatal("first incremental page state",first) }
    second,err:=port.Events(context.Background(),f.token,HarnessEvents{ProjectID:f.project,TaskID:one,Cursor:Str(fd,"next_cursor"),Limit:10})
    if err!=nil { t.Fatal(err) };sd:=second["data"].(map[string]any);events:=Arr(sd,"events")
    if len(events)!=1 || Str(events[0].(map[string]any),"sequence")!="9007199254740991" || Str(sd,"next_cursor")!="9007199254740991" { t.Fatal("safe canonical producer cursor was rounded or another task leaked",second) }
    for _,future:=range []string{"9007199254740993","9223372036854775807"}{
        n,e:=HarnessDecimal(future,true);if e!=nil || n<=9007199254740991 { t.Fatal("int64 string rounded/rejected",future,n,e) }
        value,e:=port.Events(context.Background(),f.token,HarnessEvents{ProjectID:f.project,TaskID:one,Cursor:future,Limit:10})
        if e!=nil { t.Fatal(e) };data:=value["data"].(map[string]any)
        if data["reset"]!=true || len(Arr(data,"events"))!=0 || Str(data,"next_cursor")!="9007199254740991" { t.Fatal("future int64 cursor was not read-only reset",future,value) }
    }
    for _,bad:=range []string{"01","-1","1e3","9223372036854775808"}{
        if _,e:=port.Events(context.Background(),f.token,HarnessEvents{ProjectID:f.project,TaskID:one,Cursor:bad,Limit:1});e==nil { t.Fatal("invalid cursor accepted",bad) }
    }
    caps,err:=port.Capabilities(context.Background(),f.token);if err!=nil { t.Fatal(err) }
    cd:=caps["data"].(map[string]any)
    if Str(cd["security_scope"].(map[string]any),"hooks")!="PLATFORM_POLICY" || Str(cd["verification"].(map[string]any),"execution")!="UNVERIFIED" { t.Fatal("fixture claimed qualification/disabled policy",caps) }
    if strings.Contains(string(Bytes(caps)),f.token) { t.Fatal("Host credential leaked") }
}
