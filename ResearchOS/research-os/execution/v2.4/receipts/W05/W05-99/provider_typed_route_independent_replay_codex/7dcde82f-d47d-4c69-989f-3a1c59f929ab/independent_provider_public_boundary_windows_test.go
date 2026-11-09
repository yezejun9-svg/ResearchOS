package domain
import (
 "context"
 "database/sql"
 "encoding/json"
 "fmt"
 "os"
 "path/filepath"
 "strings"
 "testing"
 "researchos.local/research-os/internal/store"
)
type independentWorkspace struct { expected WorkspaceBinding; calls int; records []any; restored bool; root string }
func (s *independentWorkspace) SnapshotWorkspace(_ context.Context,b WorkspaceBinding, principal string,_ BackupWorkspaceLimits)(BackupWorkspaceSnapshot,error){
 if Hash(b)!=Hash(s.expected)||principal!="fixture-author"||b.AuthorizedRef!="tool-workspace"||b.Access!="READ_ONLY"||b.ProjectID==nil||*b.ProjectID!="00172b0dce9cbf45a78a9625552efd10" {return BackupWorkspaceSnapshot{},fmt.Errorf("SYNTHETIC_WORKSPACE_IDENTITY_MISMATCH")}
 witness:=[]byte("workspace-file-observation-7719")
 if s.restored { if filepath.Clean(b.RealPath)!=filepath.Clean(s.root){return BackupWorkspaceSnapshot{},fmt.Errorf("restored pin mismatch")}; raw,e:=os.ReadFile(filepath.Join(s.root,"evidence.txt"));if e!=nil||Digest(raw)!=Digest(witness){return BackupWorkspaceSnapshot{},fmt.Errorf("restored witness mismatch")}}
 s.calls++;s.records=append(s.records,Object{"binding":b,"principal":principal,"synthetic":true,"original_filesystem_read":false,"witness_hash":Digest(witness),"witness_bytes":len(witness)})
 return BackupWorkspaceSnapshot{Directories:[]string{},Files:[]BackupWorkspaceFile{{Path:"evidence.txt",Data:witness}}},nil
}
func independentWrite(t *testing.T,path string,v any){t.Helper();f,e:=os.OpenFile(path,os.O_WRONLY|os.O_CREATE|os.O_EXCL,0600);if e!=nil{t.Fatal(e)};_,e=f.Write(Bytes(v));ce:=f.Close();if e!=nil||ce!=nil{t.Fatal(e,ce)}}
func independentInventory(t *testing.T,db *sql.DB) Object {t.Helper();tx,e:=db.Begin();if e!=nil{t.Fatal(e)};v,e:=validateProviderInventory(tx,"","");tx.Rollback();if e!=nil{t.Fatal("inventory",e)};r:=Object{};for k,v:=range v{r[k]=v};return r}
func independentTable(v Object,name string) Object {return v["tables"].(Object)[name].(Object)}
func independentRows(v Object,name string) []string{return independentTable(v,name)["rows"].(Object)["typed_row_multiset"].([]string)}
func independentSubset(t *testing.T,a,b []string,label string){t.Helper();m:=map[string]int{};for _,r:=range b{m[r]++};for _,r:=range a{m[r]--;if m[r]<0{t.Fatal("original immutable row changed",label)}}}
func independentCellRows(v Object,name string) []Object {
 tab:=independentTable(v,name)["rows"].(Object);cols:=tab["columns"].([]string);out:=[]Object{}
 for _,r:=range tab["typed_row_multiset"].([]string){var cells [][]any;if json.Unmarshal([]byte(r),&cells)!=nil{panic("typed row decode")};o:=Object{};for i,c:=range cells{if len(c)>1{o[cols[i]]=c[1]}else{o[cols[i]]=nil}};out=append(out,o)};return out
}
func independentRestoreDelta(t *testing.T,before,after Object) Object {
 t.Helper();allowed:=map[string]bool{"domain_objects":true,"domain_versions":true,"domain_refs":true,"events":true,"outbox":true,"resource_effects":true,"auth_credentials":true,"backup_restore_barriers":true,"client_command_queue":true,"client_control_receipts":true,"client_queue_fences":true,"client_control_requests":true,"client_sessions":true,"retrieval_roots":true}
 delta:=Object{};old:=before["tables"].(Object);cur:=after["tables"].(Object)
 for n,b:=range old{a,ok:=cur[n];if !ok{t.Fatal("restore removed table",n)};if Hash(b)!=Hash(a){if !allowed[n]{t.Fatal("unexpected restored table change",n)};delta[n]=Object{"before":Hash(b),"after":Hash(a)}}
 for n:=range cur{if _,ok:=old[n];!ok&&n!="backup_restore_barriers"{t.Fatal("unexpected new restore table",n)}}
 for _,n:=range []string{"resource_effects","domain_versions","events","outbox","client_control_receipts"}{if _,ok:=old[n];ok{independentSubset(t,independentRows(before,n),independentRows(after,n),n)}}
 // Every original historical body remains. Current Run and WorkspaceBinding alone
 // may change through backupFence and the declared portable workspace remap.
 oldobj:=independentCellRows(before,"domain_objects");newobj:=independentCellRows(after,"domain_objects");index:=map[string]Object{};for _,r:=range newobj{index[fmt.Sprint(r["project"],"|",r["kind"],"|",r["id"])]=r}
 for _,r:=range oldobj{a:=index[fmt.Sprint(r["project"],"|",r["kind"],"|",r["id"])];if a==nil{t.Fatal("missing original object")};if Hash(r)==Hash(a){continue};kind:=r["kind"];if kind!="Run"&&kind!="WorkspaceBinding"{t.Fatal("unexpected object restore delta",kind)};if kind=="Run"{o,e:=Decode([]byte(Str(a,"body")));if e!=nil||(o["status"]!="RECONCILING"&&o["status"]!="CANCEL_REQUESTED")||o["lease_expires_at"]!="1970-01-01T00:00:00Z"{t.Fatal("bad restored Run fence")}}}
 // The original MODEL/TOOL request and reservation history must be unchanged;
 // appended resource rows can only be restore UNKNOWN observations.
 known:=map[string]bool{};for _,r:=range independentRows(before,"resource_effects"){known[r]=true};afterrows:=independentRows(after,"resource_effects");decoded:=independentCellRows(after,"resource_effects");for i,r:=range afterrows{if known[r]{continue};body,e:=Decode([]byte(Str(decoded[i],"body")));if e!=nil||body["state"]!="UNKNOWN"||body["restore_reason"]!="SNAPSHOT_MAY_PREDATE_EXTERNAL_DISPATCH"{t.Fatal("non-restore effect appended")}}
 delta["schema_before"]=Hash(before["schema"]);delta["schema_after"]=Hash(after["schema"]);return delta
}
func independentDecodedArchive(t *testing.T,path string,key []byte,out string,wantWorkspace bool) Object {
 t.Helper();m,files,e:=readBackup(path,key);if e!=nil{t.Fatal(e)};refs:=Object{};dir:=filepath.Join(out,"decoded");if e=os.Mkdir(dir,0700);e!=nil{t.Fatal(e)}
 for n,b:=range files{if filepath.Base(n)!=n{t.Fatal("decoded filename")};if e=os.WriteFile(filepath.Join(dir,n),b,0600);e!=nil{t.Fatal(e)};refs[n]=Object{"sha256":Digest(b),"bytes":len(b)}}
 var idx backupWorkspaceIndex;if e=json.Unmarshal(files["workspace-index.json"],&idx);e!=nil{t.Fatal("workspace index",e)}
 if wantWorkspace{if len(idx.Roots)!=1||idx.Roots[0].Ref!="tool-workspace"||len(idx.Roots[0].Files)!=1||len(idx.Roots[0].Directories)!=0{t.Fatal("workspace root/file bound")};f:=idx.Roots[0].Files[0];if f.Path!="evidence.txt"||f.Size!=31||f.Hash!=Digest([]byte("workspace-file-observation-7719"))||Digest(files[f.Blob])!=f.Hash{t.Fatal("decoded witness mismatch")}}else if len(idx.Roots)!=0{t.Fatal("unexpected workspace")}
 if _,e=providerSemanticVector(filepath.Join(dir,"state.sqlite"),filepath.Join(out,"decoded-semantic.json.gz"));e!=nil{t.Fatal(e)}
 r:=Object{"manifest":m,"files":refs,"workspace_index":idx};independentWrite(t,filepath.Join(out,"decoded-chain.json"),r);return r
}
func TestIndependentProviderPublicArchiveBoundary(t *testing.T){
 raw,e:=os.ReadFile(os.Getenv("RESEARCHOS_INDEPENDENT_PUBLIC_SPEC"));if e!=nil{t.Fatal(e)};spec,e:=Decode(raw);if e!=nil{t.Fatal(e)};input,e:=os.ReadFile(Str(spec,"input"));if e!=nil||Digest(input)!=spec["input_sha256"]{t.Fatal("input hash",e)}
 dir:=Str(spec,"output");if e=os.Mkdir(dir,0700);e!=nil{t.Fatal(e)};path:=filepath.Join(dir,"case.sqlite");if e=os.WriteFile(path,input,0600);e!=nil{t.Fatal(e)}
 before,e:=providerSemanticVector(path,filepath.Join(dir,"semantic-before.json.gz"));if e!=nil{t.Fatal(e)};pre,e:=os.ReadFile(path);if e!=nil||Digest(pre)!=Digest(input){t.Fatal("before Open copy differs")}
 db,e:=store.Open(path);if e!=nil{t.Fatal(e)};result:=Object{"label":"INDEPENDENT_ZERO_MODEL_PUBLIC_BOUNDARY","input_sha256":Digest(input),"pre_open_sha256":Digest(pre),"mode":spec["mode"],"model_calls":0,"HTTP":0,"worker_starts":0,"synthetic_workspace":spec["id"]=="0"}
 t.Cleanup(func(){_,ce:=db.Exec("PRAGMA wal_checkpoint(TRUNCATE)");if ce!=nil{t.Error(ce)};if ce=db.Close();ce!=nil{t.Error(ce)};b,ce:=os.ReadFile(path);if ce!=nil{t.Error(ce)};result["closed_sha256"]=Digest(b);after,ce:=providerSemanticVector(path,filepath.Join(dir,"semantic-after.json.gz"));if ce!=nil{t.Error(ce)}else{allowed:=map[string]bool{};if spec["mode"]!="positive"{allowed["resource_effects"]=true;allowed["runtime_dispatches"]=true};if Hash(before["schema"])!=Hash(after["schema"]){t.Error("original copied schema changed")};changes:=[]string{};for n,v:=range before["tables"].(Object){if Hash(v)!=Hash(after["tables"].(Object)[n]){changes=append(changes,n);if !allowed[n]{t.Error("undeclared source mutation",n)}}};result["changed_tables"]=changes};original,ce:=os.ReadFile(Str(spec,"input"));if ce!=nil||Digest(original)!=spec["input_sha256"]{t.Error("immutable source drift",ce)};result["test_failed"]=t.Failed();independentWrite(t,filepath.Join(dir,"actual.json"),result)})
 contracts,e:=LoadContracts("../../spec/v2.0/contracts");if e!=nil{t.Fatal(e)};svc:=&Service{DB:db,Contracts:contracts};bindings,e:=workspaceBackupBindings(db);if e!=nil{t.Fatal(e)};hasWorkspace:=spec["id"]=="0";var ws *independentWorkspace
 if hasWorkspace {if len(bindings)!=1{t.Fatal("workspace count")};b:=bindings[0];if b.HostPrincipalRef!="fixture-local-user"||b.Revision!=1||b.Status!="ACTIVE"||b.ClientID!="mu-client"{t.Fatal("original fixed workspace metadata")};ws=&independentWorkspace{expected:b}}else if len(bindings)!=0{t.Fatal("unexpected workspace")}
 if spec["mode"]!="positive"{
  rows,er:=db.Query("SELECT name,sql FROM sqlite_schema WHERE type='trigger' ORDER BY name");if er!=nil{t.Fatal(er)};tr:=[][2]string{};for rows.Next(){var n,s string;if er=rows.Scan(&n,&s);er!=nil{t.Fatal(er)};tr=append(tr,[2]string{n,s})};rows.Close();tx,er:=db.Begin();if er!=nil{t.Fatal(er)};defer tx.Rollback();for _,x:=range tr{if _,er=tx.Exec(`DROP TRIGGER "`+strings.ReplaceAll(x[0],`"`,`""`)+`"`);er!=nil{t.Fatal(er)}}
  statements:=[]string{`DELETE FROM runtime_dispatches`,`UPDATE resource_effects SET body=json_remove(body,'$.payload.provider_transport') WHERE json_extract(body,'$.payload.capability')='MODEL'`};mutations:=[]any{};for _,s:=range statements{r,er:=tx.Exec(s);if er!=nil{t.Fatal(er)};n,er:=r.RowsAffected();if er!=nil{t.Fatal(er)};mutations=append(mutations,Object{"sql":s,"rows":n})};for _,x:=range tr{if _,er=tx.Exec(x[1]);er!=nil{t.Fatal(er)}};if er=tx.Commit();er!=nil{t.Fatal(er)};result["mutations"]=mutations;result["triggers_restored"]=tr
 }
 key:=backupTestKey(t);archive:=filepath.Join(dir,"archive");var manifest BackupManifest;if hasWorkspace{manifest,e=svc.CreateBackupWithWorkspaces(context.Background(),archive,key,ws)}else{manifest,e=svc.CreateBackup(context.Background(),archive,key)}
 result["backup_manifest"]=manifest;if e!=nil{result["backup_error"]=e.Error()}
 if spec["mode"]!="positive"{if e==nil{t.Fatal("PUBLIC_CREATEBACKUP_UNEXPECTED_ACCEPT")};if _,er:=os.Stat(archive);!os.IsNotExist(er){t.Fatal("refusal published destination",er)};result["public_refusal_proven"]=true;return}
 if e!=nil{t.Fatal("public backup prerequisite/refusal",e)}
 firstDir:=filepath.Join(dir,"archive-proof");if e=os.Mkdir(firstDir,0700);e!=nil{t.Fatal(e)};result["archive_chain"]=independentDecodedArchive(t,archive,key,firstDir,hasWorkspace)
 inv:=independentInventory(t,db);if len(inv)!=int(Num(spec["expected_inventory"])){t.Fatal("nonempty original inventory")};for k:=range inv{if !strings.Contains(k,":model:"){t.Fatal("TOOL classified MODEL")}};result["original_inventory"]=inv
 destination:=filepath.Join(dir,"restored");opt:=backupOpt(t,svc,key);pins:=[]any{}
 opt.WorkspaceTarget=func(_ context.Context,d string,req []WorkspaceRestoreRequest)([]WorkspaceRestorePin,error){if !hasWorkspace||d!=destination||len(req)!=1{return nil,fmt.Errorf("unexpected pin request")};r:=req[0];expected:=BackupWorkspaceDestination(destination,"tool-workspace");if r.AuthorizedRef!="tool-workspace"||r.PrincipalID!="fixture-author"||r.Access!="READ_ONLY"||filepath.Clean(r.RealPath)!=filepath.Clean(expected){return nil,fmt.Errorf("pin scope")};b,er:=os.ReadFile(filepath.Join(expected,"evidence.txt"));if er!=nil||Digest(b)!=Digest([]byte("workspace-file-observation-7719")){return nil,fmt.Errorf("pin witness")};pin:=WorkspaceRestorePin{AuthorizedRef:r.AuthorizedRef,RealPath:expected,HostPrincipalRef:"SYNTHETIC_INDEPENDENT_RESTORE"};pins=append(pins,Object{"request":r,"returned":pin,"sha256":Digest(b)});return []WorkspaceRestorePin{pin},nil}
 report,e:=RestoreBackup(context.Background(),archive,destination,opt);result["restore_report"]=report;result["restore_pins"]=pins;if e!=nil{result["restore_error"]=e.Error();t.Fatal("public restore",e)}
 rp:=filepath.Join(destination,"state.sqlite");restoredBefore,e:=providerSemanticVector(rp,filepath.Join(dir,"restored-before-open.json.gz"));if e!=nil{t.Fatal(e)};result["restore_delta"]=independentRestoreDelta(t,before,restoredBefore)
 rdb,e:=store.Open(rp);if e!=nil{t.Fatal(e)};defer rdb.Close();if e=validateModelStreamBackup(rdb);e!=nil{t.Fatal("restored stream validation",e)};restInv:=independentInventory(t,rdb);if len(restInv)!=len(inv){t.Fatal("inventory membership lost")};for k:=range inv{if _,ok:=restInv[k];!ok{t.Fatal("original inventory key lost")}}
 again:=filepath.Join(dir,"rebackup");rsvc:=&Service{DB:rdb,Contracts:contracts};var rews *independentWorkspace
 if hasWorkspace{bs,er:=workspaceBackupBindings(rdb);if er!=nil||len(bs)!=1{t.Fatal(er)};rews=&independentWorkspace{expected:bs[0],restored:true,root:BackupWorkspaceDestination(destination,"tool-workspace")};_,e=rsvc.CreateBackupWithWorkspaces(context.Background(),again,key,rews)}else{_,e=rsvc.CreateBackup(context.Background(),again,key)};if e!=nil{t.Fatal("public rebackup",e)}
 reDir:=filepath.Join(dir,"rebackup-proof");if e=os.Mkdir(reDir,0700);e!=nil{t.Fatal(e)};result["rebackup_chain"]=independentDecodedArchive(t,again,key,reDir,hasWorkspace)
 if _,e=rdb.Exec("PRAGMA wal_checkpoint(TRUNCATE)");e!=nil{t.Fatal(e)};if e=rdb.Close();e!=nil{t.Fatal(e)};after,e:=providerSemanticVector(rp,filepath.Join(dir,"restored-closed.json.gz"));if e!=nil{t.Fatal(e)};if Hash(after)!=Hash(restoredBefore){t.Fatal("rebackup mutated restored DB")};rb,e:=os.ReadFile(rp);if e!=nil{t.Fatal(e)};result["restored_closed_sha256"]=Digest(rb);result["restored_inventory"]=restInv
 if ws!=nil{result["synthetic_backup_callbacks"]=ws.records;result["synthetic_rebackup_callbacks"]=rews.records;if ws.calls!=1||rews.calls!=1||len(pins)!=1{t.Fatal("workspace callback count")}};result["public_roundtrip_proven"]=true
}
