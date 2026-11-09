//go:build windows

package host

import (
 "bytes"
 "context"
 "encoding/binary"
 "errors"
 "os"
 "path/filepath"
 "strings"
 "testing"

 "golang.org/x/sys/windows"
 "researchos.local/research-os/internal/domain"
 sandbox "researchos.local/research-os/ops/experiment_sandbox"
)

const captureFixtureSource="package candidate\nfunc Clamp(value, lower, upper int32) int32 { if value < lower { return lower }; if value > upper { return upper }; return value }\n"
const captureFixtureMod="module fixture.invalid/MOD_SENTINEL\n"
const captureFixtureTest="package candidate\n// FIXED_TEST_SENTINEL_NEVER_SERIALIZE\n"
type candidateFixture struct{view domain.RuntimeCodingCaptureView;check frozenRuntimeCheck;id sandbox.Identity;manifest []any;source string}
func newCandidateFixture(t *testing.T)candidateFixture{
 t.Helper();stage:=filepath.Join(t.TempDir(),"stage");source:=filepath.Join(stage,"input","source")
 if err:=os.MkdirAll(filepath.Join(source,"pkg"),0700);err!=nil{t.Fatal(err)}
 for p,s:=range map[string]string{"go.mod":captureFixtureMod,"pkg/solution.go":captureFixtureSource,"pkg/solution_test.go":captureFixtureTest}{captureWrite(t,filepath.Join(source,filepath.FromSlash(p)),s)}
 h:=func(s string)string{return domain.Digest([]byte(s))}
 v:=domain.RuntimeCodingCaptureView{Schema:"researchos.coding-private-capture-context.v1",ProjectID:"synthetic-project",TaskID:"synthetic-task",RunID:"synthetic-run",LeaseEpoch:"7",CheckID:"synthetic-check",SuiteRef:"coding.pure-scalar-bundle-v1",SuiteHash:h("suite"),BindingHash:h("binding"),TaskContractHash:h("task"),GoalContractHash:h("goal"),PolicyHash:h("policy"),ToolchainHash:h("toolchain"),GoModHash:h(captureFixtureMod),TestHash:h(captureFixtureTest)}
 f:=candidateFixture{view:v,source:source,id:sandbox.Identity{PID:17,Created:23,Job:"synthetic-job",SID:"synthetic-sid",Profile:"synthetic-profile",StagingDirectory:stage},
 check:frozenRuntimeCheck{id:v.CheckID,toolchainHash:v.ToolchainHash,argv:[]string{"-C","${SOURCE}","test","-p=2","-count=1","-run","^TestFixture$","./pkg"},sources:[]runtimeCheckSource{{"go.mod",v.GoModHash},{"pkg/solution.go",""},{"pkg/solution_test.go",v.TestHash}}}}
 f.snapshot(t);return f
}
func captureWrite(t *testing.T,p,s string){t.Helper();if err:=os.WriteFile(p,[]byte(s),0600);err!=nil{t.Fatal(err)}}
func(f *candidateFixture)snapshot(t *testing.T){
 t.Helper();root,err:=os.OpenRoot(f.source);if err!=nil{t.Fatal(err)};defer root.Close()
 f.manifest,err=runtimeCheckSnapshot(context.Background(),root,f.check.sources,"");if err!=nil{t.Fatal(err)}
}
func(f candidateFixture)capture(ctx context.Context)(*runtimeCandidateCapture,error){return captureRuntimeCandidate(ctx,f.view,f.check,f.view.PolicyHash,f.manifest,f.id)}
func(f candidateFixture)receipt()sandbox.Receipt{
 argv:=append([]string(nil),f.check.argv...);argv[1]=f.source
 return sandbox.Receipt{PID:f.id.PID,Created:f.id.Created,Job:f.id.Job,SID:f.id.SID,Profile:f.id.Profile,Directory:filepath.Join(f.id.StagingDirectory,"output"),Executable:filepath.Join(f.id.StagingDirectory,"input","go","bin","go.exe"),Args:argv,Stopped:true,StreamsDrained:true,CleanupComplete:true,OutputCopied:true}
}
func captureRejected(t *testing.T,f candidateFixture){t.Helper();if c,err:=f.capture(context.Background());err==nil || c!=nil{t.Fatal("invalid snapshot accepted")}}
func TestRuntimeCandidateCaptureCurrentBytesAndDefensiveSeal(t *testing.T){
 f:=newCandidateFixture(t)
 // Authorized edit A -> B precedes this check's staging snapshot.
 b:=strings.Replace(captureFixtureSource,"return value","return  value",1)
 captureWrite(t,filepath.Join(f.source,"pkg","solution.go"),b);f.snapshot(t)
 hash:=domain.Hash(f.manifest);c,err:=f.capture(context.Background());if err!=nil{t.Fatal(err)}
 f.view.BindingHash="consumer change";f.manifest[1].(domain.Object)["sha256"]="consumer change"
 e,err:=c.evidence(f.receipt());if err!=nil{t.Fatal(err)}
 candidate:=e["candidate"].(domain.Object)
 if e["source_manifest_hash"]!=hash || !bytes.Equal(candidate["bytes"].([]byte),[]byte(b)) || candidate["sha256"]!=domain.Digest([]byte(b)){t.Fatal("not exact B")}
 for _,sentinel:=range []string{"MOD_SENTINEL","FIXED_TEST_SENTINEL_NEVER_SERIALIZE"}{if bytes.Contains(domain.Bytes(e),[]byte(sentinel)){t.Fatal("fixed source leaked")}}
 candidate["bytes"].([]byte)[0]='X';e["inventory"].([]any)[0].(domain.Object)["path"]="mutation"
 e2,err:=c.evidence(f.receipt());if err!=nil || !bytes.Equal(e2["candidate"].(domain.Object)["bytes"].([]byte),[]byte(b)) || e2["inventory"].([]any)[0].(domain.Object)["path"]!="go.mod"{t.Fatal("aliases capture",err)}
 captureWrite(t,filepath.Join(f.source,"pkg","solution.go"),"after capture")
 e3,err:=c.evidence(f.receipt());if err!=nil || domain.Hash(e3)!=domain.Hash(e2){t.Fatal("seal reread mutable path",err)}
}
func TestRuntimeCandidateCaptureRejectsInventoryAndBytes(t *testing.T){
 cases:=map[string]func(*testing.T,*candidateFixture){
  "B_to_C":func(t *testing.T,f *candidateFixture){captureWrite(t,filepath.Join(f.source,"pkg","solution.go"),captureFixtureSource+"\n")},
  "fixed_mod":func(t *testing.T,f *candidateFixture){captureWrite(t,filepath.Join(f.source,"go.mod"),"wrong fixed")},
  "fixed_test":func(t *testing.T,f *candidateFixture){captureWrite(t,filepath.Join(f.source,"pkg","solution_test.go"),"wrong fixed")},
  "extra_file":func(t *testing.T,f *candidateFixture){captureWrite(t,filepath.Join(f.source,"extra.go"),"x")},
  "extra_pkg":func(t *testing.T,f *candidateFixture){captureWrite(t,filepath.Join(f.source,"pkg","extra.go"),"x")},
  "empty_dir":func(t *testing.T,f *candidateFixture){if err:=os.Mkdir(filepath.Join(f.source,"empty"),0700);err!=nil{t.Fatal(err)}},
  "vendor":func(t *testing.T,f *candidateFixture){if err:=os.Mkdir(filepath.Join(f.source,"vendor"),0700);err!=nil{t.Fatal(err)}},
  "missing":func(t *testing.T,f *candidateFixture){if err:=os.Remove(filepath.Join(f.source,"pkg","solution_test.go"));err!=nil{t.Fatal(err)}},
  "case_file":func(t *testing.T,f *candidateFixture){if err:=os.Rename(filepath.Join(f.source,"go.mod"),filepath.Join(f.source,"GO.MOD"));err!=nil{t.Fatal(err)}},
  "case_pkg":func(t *testing.T,f *candidateFixture){if err:=os.Rename(filepath.Join(f.source,"pkg"),filepath.Join(f.source,"PKG"));err!=nil{t.Fatal(err)}},
  "case_source":func(t *testing.T,f *candidateFixture){if err:=os.Rename(f.source,filepath.Join(filepath.Dir(f.source),"SOURCE"));err!=nil{t.Fatal(err)}},
  "case_input":func(t *testing.T,f *candidateFixture){if err:=os.Rename(filepath.Dir(f.source),filepath.Join(f.id.StagingDirectory,"INPUT"));err!=nil{t.Fatal(err)}},
  "invalid_ast":func(t *testing.T,f *candidateFixture){captureWrite(t,filepath.Join(f.source,"pkg","solution.go"),"package candidate\nfunc init(){}");f.snapshot(t)},
  "invalid_utf8":func(t *testing.T,f *candidateFixture){captureWrite(t,filepath.Join(f.source,"pkg","solution.go"),string([]byte{255}));f.snapshot(t)},
  "oversize":func(t *testing.T,f *candidateFixture){captureWrite(t,filepath.Join(f.source,"pkg","solution.go"),strings.Repeat("x",16385));f.snapshot(t)},
  "hardlink":func(t *testing.T,f *candidateFixture){if err:=os.Link(filepath.Join(f.source,"pkg","solution.go"),filepath.Join(f.id.StagingDirectory,"alias"));err!=nil{t.Fatal(err)}},
 }
 for name,change:=range cases{t.Run(name,func(t *testing.T){f:=newCandidateFixture(t);change(t,&f);captureRejected(t,f)})}
}
// Windows junction fixture: filesystem operations only, no shell/process and no
// symlink privilege assumption. Both junction and target remain under TempDir.
func captureJunction(t *testing.T,p,target string){
 t.Helper();if err:=os.Mkdir(p,0700);err!=nil{t.Fatal(err)}
 sub,_:=windows.UTF16FromString("\\??\\"+target);printName,_:=windows.UTF16FromString(target)
 paths:=append(append([]uint16(nil),sub...),printName...);data:=make([]byte,16+len(paths)*2)
 binary.LittleEndian.PutUint32(data,0xa0000003);binary.LittleEndian.PutUint16(data[4:],uint16(len(data)-8))
 binary.LittleEndian.PutUint16(data[10:],uint16((len(sub)-1)*2));binary.LittleEndian.PutUint16(data[12:],uint16(len(sub)*2));binary.LittleEndian.PutUint16(data[14:],uint16((len(printName)-1)*2))
 for i,v:=range paths{binary.LittleEndian.PutUint16(data[16+i*2:],v)}
 wide,_:=windows.UTF16PtrFromString(p);h,err:=windows.CreateFile(wide,windows.GENERIC_WRITE,windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE|windows.FILE_SHARE_DELETE,nil,windows.OPEN_EXISTING,windows.FILE_FLAG_OPEN_REPARSE_POINT|windows.FILE_FLAG_BACKUP_SEMANTICS,0)
 if err!=nil{t.Fatal(err)};defer windows.CloseHandle(h);var returned uint32
 if err=windows.DeviceIoControl(h,0x000900a4,&data[0],uint32(len(data)),nil,0,&returned,nil);err!=nil{t.Fatal(err)}
}
func TestRuntimeCandidateCaptureRejectsReparse(t *testing.T){
 for _,where:=range []string{"stage","input","source","pkg"}{t.Run(where,func(t *testing.T){
  f:=newCandidateFixture(t);p:=f.id.StagingDirectory
  switch where{case "input":p=filepath.Dir(f.source);case "source":p=f.source;case "pkg":p=filepath.Join(f.source,"pkg")}
  target:=p+"-original";if err:=os.Rename(p,target);err!=nil{t.Fatal(err)}
  captureJunction(t,p,target);captureRejected(t,f)
 })}
}
func TestRuntimeCandidateCaptureContextAndManifestRefusals(t *testing.T){
 cases:=map[string]func(*candidateFixture){
  "schema":func(f *candidateFixture){f.view.Schema="unknown"},
  "suite":func(f *candidateFixture){f.view.SuiteRef="unknown"},
  "check":func(f *candidateFixture){f.view.CheckID="other"},
  "policy":func(f *candidateFixture){f.view.PolicyHash=domain.Digest([]byte("other"))},
  "toolchain":func(f *candidateFixture){f.view.ToolchainHash=domain.Digest([]byte("other"))},
  "vendor":func(f *candidateFixture){f.check.vendorRoot="ignored-not-allowed"},
  "candidate_fixed":func(f *candidateFixture){f.check.sources[1].expected=domain.Digest([]byte(captureFixtureSource))},
  "fixed":func(f *candidateFixture){f.check.sources[0].expected=domain.Digest([]byte("other"))},
  "roster":func(f *candidateFixture){f.check.sources[0].path="GO.MOD"},
  "package":func(f *candidateFixture){f.check.argv[7]="../escape"},
  "manifest_extra":func(f *candidateFixture){f.manifest=append(f.manifest,f.manifest[0])},
  "manifest_escape":func(f *candidateFixture){f.manifest[1].(domain.Object)["path"]="../solution.go"},
  "manifest_ads":func(f *candidateFixture){f.manifest[1].(domain.Object)["path"]="pkg/solution.go:stream"},
  "manifest_mode":func(f *candidateFixture){f.manifest[1].(domain.Object)["mode"]="fixed"},
  "manifest_size":func(f *candidateFixture){f.manifest[1].(domain.Object)["size_bytes"]=-1},
  "pid":func(f *candidateFixture){f.id.PID=0},
  "created":func(f *candidateFixture){f.id.Created=0},
  "job":func(f *candidateFixture){f.id.Job=""},
  "sid":func(f *candidateFixture){f.id.SID=""},
  "profile":func(f *candidateFixture){f.id.Profile=""},
  "relative":func(f *candidateFixture){f.id.StagingDirectory="relative"},
  "alias":func(f *candidateFixture){f.id.StagingDirectory+=string(os.PathSeparator)+".."},
 }
 for name,change:=range cases{t.Run(name,func(t *testing.T){f:=newCandidateFixture(t);change(&f);captureRejected(t,f)})}
}
type captureCancelContext struct{context.Context;remaining int}
func(c *captureCancelContext)Err()error{c.remaining--;if c.remaining<=0{return context.Canceled};return nil}
func TestRuntimeCandidateCaptureCancellation(t *testing.T){
 f:=newCandidateFixture(t);ctx,cancel:=context.WithCancel(context.Background());cancel()
 if _,err:=f.capture(ctx);!errors.Is(err,context.Canceled){t.Fatal(err)}
 file,err:=os.Open(filepath.Join(f.source,"pkg","solution_test.go"));if err!=nil{t.Fatal(err)};defer file.Close()
 if _,_,_,err=runtimeCaptureRead(&captureCancelContext{Context:context.Background(),remaining:2},file,runtimeCaptureFixedLimit,false);!errors.Is(err,context.Canceled){t.Fatal("read cancellation",err)}
}
func TestRuntimeCandidateCaptureCompleteReceiptOnly(t *testing.T){
 f:=newCandidateFixture(t);c,err:=f.capture(context.Background());if err!=nil{t.Fatal(err)}
 cases:=map[string]func(*sandbox.Receipt){
  "pid":func(r *sandbox.Receipt){r.PID++},"created":func(r *sandbox.Receipt){r.Created++},"job":func(r *sandbox.Receipt){r.Job+="x"},
  "sid":func(r *sandbox.Receipt){r.SID+="x"},"profile":func(r *sandbox.Receipt){r.Profile+="x"},
  "capability":func(r *sandbox.Receipt){r.Capabilities=[]string{"network"}},"cwd":func(r *sandbox.Receipt){r.Directory=f.id.StagingDirectory},
  "exe":func(r *sandbox.Receipt){r.Executable="go.exe"},"args":func(r *sandbox.Receipt){r.Args[1]="old-source"},
  "arg_count":func(r *sandbox.Receipt){r.Args=append(r.Args,"extra")},"stopped":func(r *sandbox.Receipt){r.Stopped=false},
  "streams":func(r *sandbox.Receipt){r.StreamsDrained=false},"cleanup":func(r *sandbox.Receipt){r.CleanupComplete=false},"output":func(r *sandbox.Receipt){r.OutputCopied=false},
 }
 for name,change:=range cases{t.Run(name,func(t *testing.T){r:=f.receipt();change(&r);if _,err:=c.evidence(r);err==nil{t.Fatal("bad receipt accepted")}})}
 for _,timed:=range []bool{false,true}{r:=f.receipt();r.ExitCode=1;r.TimedOut=timed;e,err:=c.evidence(r)
  if err!=nil || e["structural_witness"].(domain.Object)["semantic_acceptance"]!=false || bytes.Contains(domain.Bytes(e),[]byte("PASS")){t.Fatal("capture became business PASS",err)}
 }
 if _,err:=(*runtimeCandidateCapture)(nil).evidence(f.receipt());err==nil{t.Fatal("missing callback")}
}
func TestRuntimeCandidateCaptureEvidenceBoundAndNilSelector(t *testing.T){
 f:=newCandidateFixture(t);c,err:=f.capture(context.Background());if err!=nil{t.Fatal(err)};e,err:=c.evidence(f.receipt());if err!=nil{t.Fatal(err)}
 full:=domain.Object{"padding":strings.Repeat("x",(4<<20)-64)}
 if err:=runtimeCheckEvidenceBound(full);err!=nil{t.Fatal("control must fit",err)}
 full["candidate_capture"]=e;if err:=runtimeCheckEvidenceBound(full);err==nil{t.Fatal("encoded overhead ignored")}
 r:=domain.RuntimeToolRequest{Name:"run_check",Arguments:domain.Object{"check_id":"coding.pure-scalar-bundle-v1"},Policy:domain.Object{"capture":true}}
 if v,err:=r.CodingCapture();v!=nil || err!=nil{t.Fatal("worker opted in")}
}

