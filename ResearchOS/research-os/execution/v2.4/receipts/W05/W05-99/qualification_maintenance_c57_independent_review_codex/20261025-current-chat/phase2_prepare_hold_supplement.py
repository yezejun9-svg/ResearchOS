import pathlib,json,hashlib
B=pathlib.Path(__file__).parent
S=pathlib.Path(json.loads((B/'PHASE2-exact-snapshot-verification.json').read_text(encoding='utf-8'))['snapshot'])
p=S/'internal/domain/qualification_failure_maintenance_windows_test.go'
raw=p.read_text(encoding='utf-8');start=raw.index('func TestHistoricalQualificationNativeThreeFrameHold(');end=raw.index('\nfunc TestHistoricalQualificationPrivateNativeHoldThroughSQLReturn(',start)
body=raw[start:end].replace('TestHistoricalQualificationNativeThreeFrameHold','TestIndependentC57NativeAllEvidenceHeldThroughSQL')
body=body.replace('[]string{"exact", "tool_changed", "suffix", "raw_missing"}', '[]string{"exact_commit", "exact_rollback"}')
a=body.index('\t\t\tif mode == "exact" {');z=body.index('\n\t\t\t} else {',a)
replacement='''\t\t\tif strings.HasPrefix(mode,"exact_") {
    if err != nil {t.Fatal(err)}
    defer hold.Close()
    db,e:=sql.Open("sqlite",filepath.Join(root,"held-sql.sqlite"));if e!=nil{t.Fatal(e)};defer db.Close()
    if _,e=db.Exec(`CREATE TABLE marker(id INTEGER PRIMARY KEY)`);e!=nil{t.Fatal(e)}
    tx,e:=db.BeginTx(context.Background(),nil);if e!=nil{t.Fatal(e)};defer tx.Rollback()
    if _,e=tx.Exec(`INSERT INTO marker(id) VALUES(1)`);e!=nil{t.Fatal(e)}
    subject:=HistoricalQualificationSubject{ProjectID:"p",RunID:"r",Epoch:1}
    model:=Object{"fact":"fixture"}
    plan:=HistoricalQualificationPlan{Subject:subject,AuthorID:"owner",OwnerRoot:"owner",Source:source,Core:Object{"fixture":true},BeforeRun:Object{},BeforeState:Object{},BeforeDispatch:Object{}}
    plan.Proof=Object{"kind":historicalMaintenanceProofKind,"claim":"HOST_TOOL_EFFECT_NOT_DISPATCHED","native_class":historicalMaintenanceNativeClass,"plan_hash":plan.coreHash(),"owner_root":"owner","author":"owner","model_binding":model}
    verified:=verifiedHistoricalQualification{subject:subject,author:Principal{ID:"owner"},ownerRoot:"owner",run:Object{},state:Object{},dispatch:Object{},modelBinding:model,native:facts}
    closure,e:=(&Service{}).validatedHistoricalQualificationFailureTx(tx,plan,verified,hold);if e!=nil{t.Fatal(e)}
    copied:=closure
    files:=[]string{"bridge.json","stdout.raw","stderr.raw",modelName,filepath.Join("input","worker.exe"),filepath.Join("input","mu-worker.mjs"),filepath.Join("input","worker.json"),filepath.Join("input","request.json")}
    paths:=[]string{}
    for _,name:=range files{paths=append(paths,filepath.Join(directory,name))}
    guards:=[]string{filepath.Join(directory,"input"),directory,filepath.Dir(directory),root}
    check:=func(phase string){
      runtime.GC();runtime.GC()
      if e:=copied.Check();e!=nil{t.Fatalf("%s closure.Check %v",phase,e)}
      for _,path:=range paths{
        if e:=os.WriteFile(path,[]byte("tamper"),0600);e==nil{t.Fatalf("%s write admitted %s",phase,path)}
        if e:=os.Rename(path,path+".moved");e==nil{t.Fatalf("%s rename admitted %s",phase,path)}
        if e:=os.Remove(path);e==nil{t.Fatalf("%s delete admitted %s",phase,path)}
      }
      for _,path:=range guards{if e:=os.Rename(path,path+".moved");e==nil{t.Fatalf("%s ancestor rename admitted %s",phase,path)}}
      t.Logf("NATIVE_HOLD phase=%s files=%d denied_write_rename_delete=%d owned_ancestor_rename_denied=%d copied_closure_live=true forced_GC=2",phase,len(paths),len(paths)*3,len(guards))
    }
    check("before_sql_return")
    if mode=="exact_commit"{e=tx.Commit()}else{e=tx.Rollback()};if e!=nil{t.Fatal(e)}
    t.Logf("SQL_RETURN outcome=%s native_return_observed=true",mode)
    check("after_sql_return_before_close")
    if e=closure.Close();e!=nil{t.Fatal(e)}
    if e=copied.Check();e==nil{t.Fatal("copied closure live after Close")}
    for _,path:=range paths{if e=os.WriteFile(path,[]byte("after-close"),0600);e!=nil{t.Fatalf("write after close %s: %v",path,e)}}
    t.Logf("NATIVE_HOLD phase=after_close files=%d writes_succeed=true copied_closure_live=false",len(paths))
'''
body=body[:a]+replacement+body[z:]
header='''//go:build windows
package domain
import (
 "context"
 "database/sql"
 "encoding/json"
 "os"
 "path/filepath"
 "runtime"
 "strings"
 "testing"
 "golang.org/x/sys/windows"
 rt "researchos.local/research-os/adapters/runtime"
)
'''
dest=S/'internal/domain/independent_c57_hold_windows_test.go';assert not dest.exists();dest.write_text(header+body,encoding='utf-8')
job=json.loads((B/'PHASE2-jobs/103-independent-domain-census.json').read_text(encoding='utf-8'))
job['tag']='114-independent-native-hold';job['argv'][-1]='^TestIndependentC57NativeAllEvidenceHeldThroughSQL$'
job['supplementary_files'].append({'path':str(dest.relative_to(S)).replace('\\','/'),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
(B/'PHASE2-jobs/114-independent-native-hold.json').write_text(json.dumps(job,indent=2),encoding='utf-8')
print(json.dumps(job['supplementary_files'],indent=2))
