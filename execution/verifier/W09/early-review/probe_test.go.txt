package domain

import (
 "context"
 "net/http/httptest"
 "os"
 "os/exec"
 "path/filepath"
 "runtime"
 "strings"
 "testing"
)

func verifierW09Base(t *testing.T) string {
 t.Helper()
 base:=os.Getenv("VERIFIER_W09_DATA")
 if base==""||!filepath.IsAbs(base){t.Fatal("explicit verifier-owned absolute synthetic data directory required")}
 if e:=os.MkdirAll(base,0700);e!=nil{t.Fatal(e)}
 dir,e:=os.MkdirTemp(base,"synthetic-");if e!=nil{t.Fatal(e)}
 // Retained as evidence; no recursive removal of junction-bearing directories.
 return dir
}
func verifierW09Content(f *fixture,id string)(int,string){
 q:=httptest.NewRequest("GET",f.path("/artifacts/"+id+"/content"),nil)
 q.Header.Set("Authorization","Bearer "+f.token)
 w:=httptest.NewRecorder();f.s.Handler().ServeHTTP(w,q)
 return w.Code,w.Body.String()
}
func verifierW09Junction(t *testing.T,base,link,target string){
 t.Helper()
 for _,p:=range []string{link,target}{ rel,e:=filepath.Rel(base,p);if e!=nil||!filepath.IsLocal(rel){t.Fatal("junction outside synthetic evidence directory")}}
 out,e:=exec.Command("cmd.exe","/c","mklink","/J",link,target).CombinedOutput()
 t.Logf("junction link=%s target=%s exit_error=%v output=%s",link,target,e,string(out))
 if e!=nil{t.Fatal(e)}
}
func TestVerifierW09RegisteredRootReplacement(t *testing.T){
 if runtime.GOOS!="windows"{t.Fatal("this probe requires actual Windows junction behavior")}
 f:=contextFixture(t);base:=verifierW09Base(t);a:=filepath.Join(base,"A");b:=filepath.Join(base,"B");moved:=filepath.Join(base,"A-original")
 for _,dir:=range []string{a,b}{if e:=os.Mkdir(dir,0700);e!=nil{t.Fatal(e)}}
 for file,text:=range map[string]string{filepath.Join(a,"same.txt"):"ALLOWED-A-SYNTHETIC",filepath.Join(b,"same.txt"):"UNAUTHORIZED-B-SYNTHETIC"}{if e:=os.WriteFile(file,[]byte(text),0600);e!=nil{t.Fatal(e)}}
 root,e:=f.s.RegisterLocalRoot(context.Background(),f.token,f.project,a);if e!=nil{t.Fatal(e)}
 before,e:=f.s.CaptureLocalSnapshot(context.Background(),f.token,f.project,root,"same.txt");if e!=nil{t.Fatal(e)}
 code,body:=verifierW09Content(f,Str(before,"id"));t.Logf("positive capture_http=%d allowed_marker=%v",code,strings.Contains(body,"ALLOWED-A-SYNTHETIC"));if code!=200||!strings.Contains(body,"ALLOWED-A-SYNTHETIC"){t.Fatal("positive root failed")}
 verifierW09Junction(t,base,filepath.Join(a,"escape"),b)
 _,escapeErr:=f.s.CaptureLocalSnapshot(context.Background(),f.token,f.project,root,"escape/same.txt")
 t.Logf("child_junction_denied=%v error=%v",escapeErr!=nil,escapeErr);if escapeErr==nil{t.Fatal("child junction unexpectedly allowed")}
 // Both exact rename endpoints checked before moving this self-created directory.
 for _,p:=range []string{a,moved}{rel,e:=filepath.Rel(base,p);if e!=nil||!filepath.IsLocal(rel){t.Fatal("rename outside synthetic scope")}}
 if e=os.Rename(a,moved);e!=nil{t.Fatal(e)}
 verifierW09Junction(t,base,a,b)
 after,captureErr:=f.s.CaptureLocalSnapshot(context.Background(),f.token,f.project,root,"same.txt")
 leaked:=false;status:=0;hits:=0
 if captureErr==nil{
  status,body=verifierW09Content(f,Str(after,"id"));leaked=strings.Contains(body,"UNAUTHORIZED-B-SYNTHETIC")
  q:=Object{"query":"UNAUTHORIZED-B-SYNTHETIC","snapshot_ids":[]any{after["id"]},"limit":10,"expected_state_revision":f.state()["revision"]}
  response:=f.expect(200,"POST",f.path("/search"),ID(),"",q);hits=len(Arr(response,"hits"))
 }
 t.Logf("registered_root_unchanged=%v capture_error=%v body_http=%d B_marker_read=%v search_hits=%d",root!="",captureErr,status,leaked,hits)
 if captureErr==nil&&leaked{t.Fatal("registered root path replacement read unregistered B")}
}

func TestVerifierW09ChangedSourceReadPaths(t *testing.T){
 for _,scenario:=range []string{"modify","delete","revoke","move_outside_root"}{t.Run(scenario,func(t *testing.T){
  f:=contextFixture(t);base:=verifierW09Base(t);rootPath:=filepath.Join(base,"A");if e:=os.Mkdir(rootPath,0700);e!=nil{t.Fatal(e)}
  file:=filepath.Join(rootPath,"source.txt");const marker="OLD-V1-SYNTHETIC-MARKER"
  if e:=os.WriteFile(file,[]byte(marker),0600);e!=nil{t.Fatal(e)}
  root,e:=f.s.RegisterLocalRoot(context.Background(),f.token,f.project,rootPath);if e!=nil{t.Fatal(e)}
  artifact,e:=f.s.CaptureLocalSnapshot(context.Background(),f.token,f.project,root,"source.txt");if e!=nil{t.Fatal(e)}
  req:=f.requirement();task:=f.task(req,[]any{Ref(artifact,"Artifact")},"local-snapshot-input");f.bundle(task)
  if _,e=f.s.MaterializeTaskContext(context.Background(),f.token,f.project,Str(task,"id"),filepath.Join(base,"before"));e!=nil{t.Fatal(e)}
  q:=Object{"query":marker,"snapshot_ids":[]any{artifact["id"]},"limit":10,"expected_state_revision":f.state()["revision"]};key:=ID()
  warm:=f.expect(200,"POST",f.path("/search"),key,"",q);if len(Arr(warm,"hits"))!=1{t.Fatal("positive search failed")}
  code,raw:=verifierW09Content(f,Str(artifact,"id"));if code!=200||raw!=marker{t.Fatal("positive content failed")}
  switch scenario{
  case "modify":e=os.WriteFile(file,[]byte("NEW-V2-SYNTHETIC-MARKER"),0600)
  case "delete":e=os.Remove(file) // Single self-created text file only, no recursive deletion.
  case "revoke":e=f.s.RevokeLocalRoot(context.Background(),f.token,f.project,root)
  case "move_outside_root":e=os.Rename(file,filepath.Join(base,"outside.txt"))
  };if e!=nil{t.Fatal(e)}
  searchCode,result,_:=f.request("POST",f.path("/search"),key,"",q)
  _,oldMaterializeErr:=f.s.MaterializeTaskContext(context.Background(),f.token,f.project,Str(task,"id"),filepath.Join(base,"after-old-bundle"))
  code,raw=verifierW09Content(f,Str(artifact,"id"));oldBodyLeaked:=strings.Contains(raw,marker)
  t.Logf("scenario=%s same_key_http=%d hits=%d old_bundle_rejected=%v direct_content_http=%d old_body_returned=%v",scenario,searchCode,len(Arr(result,"hits")),oldMaterializeErr!=nil,code,oldBodyLeaked)
  if strings.Contains(string(Bytes(result)),marker){t.Error("same-key search replayed old body")}
  if oldMaterializeErr==nil{t.Error("old bundle materialized changed source")}
  if oldBodyLeaked{t.Error("direct content still returns deleted/changed/revoked source body")}
  if scenario!="revoke"{
   // Before maintenance refresh, new bundle excludes the snapshot ID, but still has a task input VersionRef.
   task=f.read("tasks",Str(task,"id"));bundle:=f.bundle(task)
   dest:=filepath.Join(base,"after-new-bundle");_,newErr:=f.s.MaterializeTaskContext(context.Background(),f.token,f.project,Str(task,"id"),dest)
   bytes,_:=os.ReadFile(filepath.Join(dest,"inputs",Str(artifact,"id")+".content"));leaked:=strings.Contains(string(bytes),marker)
   t.Logf("fresh_bundle_authorized_snapshot_count=%d materialize_error=%v old_body_written=%v",len(Arr(bundle,"authorized_snapshot_ids")),newErr,leaked)
   if leaked{t.Error("fresh bundle with old input VersionRef materialized invalidated local bytes")}
  }
  refreshed,refreshErr:=f.s.RefreshLocalSnapshots(context.Background(),f.token,f.project);if refreshErr!=nil{t.Fatal(refreshErr)}
  metadata:=f.read("artifacts",Str(artifact,"id"));code,raw=verifierW09Content(f,Str(artifact,"id"))
  t.Logf("after_refresh changed=%d validity=%v content_http=%d old_body_returned=%v",refreshed,metadata["validity"],code,strings.Contains(raw,marker))
 })}
}
