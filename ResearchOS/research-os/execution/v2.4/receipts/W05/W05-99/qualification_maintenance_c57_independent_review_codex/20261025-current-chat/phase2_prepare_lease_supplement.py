import pathlib,json,hashlib
B=pathlib.Path(__file__).parent;S=pathlib.Path(json.loads((B/'PHASE2-exact-snapshot-verification.json').read_text(encoding='utf-8'))['snapshot'])
source='''//go:build windows
package runtime
import("os";"path/filepath";"testing";"time")
func TestIndependentC57ConcurrentMaintenanceBorrow(t *testing.T){
 root:=t.TempDir();db:=filepath.Join(root,"researchos.sqlite");if e:=os.WriteFile(db,[]byte("fixture"),0600);e!=nil{t.Fatal(e)}
 lease,e:=AcquireDataRootLease(root);if e!=nil{t.Fatal(e)};defer lease.Close();copyParent:=*lease
 start:=make(chan struct{});out:=make(chan *DataRootSourceBorrow,32)
 for i:=0;i<32;i++{go func(){<-start;b,e:=copyParent.BorrowMaintenanceSource(db);if e!=nil{out<-nil;return};out<-b}()};close(start)
 winners:=[]*DataRootSourceBorrow{}
 for i:=0;i<32;i++{select{case b:=<-out:if b!=nil{winners=append(winners,b)};case <-time.After(5*time.Second):t.Fatal("concurrent borrow deadlock")}}
 defer func(){for _,b:=range winners{b.Release()}}()
 if len(winners)!=1{t.Fatalf("concurrent successful borrowers=%d",len(winners))};b:=winners[0]
 if e=lease.Close();e==nil{t.Fatal("original parent closed while borrowed")};if e=copyParent.Close();e==nil{t.Fatal("copied parent closed while borrowed")}
 if !lease.Held()||!copyParent.Held(){t.Fatal("native lease lost")}
 competitor,err:=AcquireDataRootLease(root);if err==nil{competitor.Close();t.Fatal("independent native lease admitted while borrowed")}
 if e=b.Release();e!=nil{t.Fatal(e)};if e=lease.Close();e!=nil{t.Fatal(e)}
 if copyParent.Held(){t.Fatal("copy remained held after close")}
 competitor,e=AcquireDataRootLease(root);if e!=nil{t.Fatalf("independent native lease after release: %v",e)};if e=competitor.Close();e!=nil{t.Fatal(e)}
 t.Log("CONCURRENT_BORROW contenders=32 winners=1 parent_copies_close_denied=true independent_native_lease_blocked=true after_release_native_reacquire=true")
}
'''
dest=S/'adapters/runtime/independent_c57_concurrent_windows_test.go';assert not dest.exists();dest.write_text(source,encoding='utf-8')
job=json.loads((B/'PHASE2-jobs/120-independent-journal-prefixes.json').read_text(encoding='utf-8'));job['tag']='128-independent-concurrent-borrow';job['argv'][-3]='./adapters/runtime';job['argv'][-1]='^TestIndependentC57ConcurrentMaintenanceBorrow$'
job['supplementary_files'].append({'path':str(dest.relative_to(S)).replace('\\','/'),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
(B/'PHASE2-jobs/128-independent-concurrent-borrow.json').write_text(json.dumps(job,indent=2),encoding='utf-8');print(json.dumps(job['supplementary_files'][-1]))
