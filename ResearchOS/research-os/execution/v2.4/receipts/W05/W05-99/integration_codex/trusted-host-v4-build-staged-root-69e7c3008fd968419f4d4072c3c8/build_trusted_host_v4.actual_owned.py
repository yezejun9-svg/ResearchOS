SOURCE_NAMESPACE="D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_trusted_qualification_host_source_v4_codex/staged-root-69e7c3008fd968419f4d4072c3c8"
import sys
sys.dont_write_bytecode=True
import hashlib,json,types,uuid,difflib
from pathlib import Path
ROOT=Path("D:/作品集/ResearchOS/research-os");B=ROOT/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
SRC=Path(SOURCE_NAMESPACE);OLD=B/"mu_sdk_trusted_qualification_host_source_v3_codex/c8b22080210c4a398acd8ad294ce31fc"
SNAP=B/"mu_sdk_trusted_qualification_host_v3_interrupted_handoff_codex/cbf8ba710ee64480961ddc7befc394b5/source_snapshot"
names=("main.go","hostapi.go","prepare.go","execute.go","prepare_runtime.go","seed.template.json","profile.template.json","go.authority.template.json")
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
 p=O/name
 with p.open("xb") as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
def module(path,raw):
 m=types.ModuleType("root_staged_"+path.stem);m.__file__=str(path);exec(compile(raw,str(path),"exec"),m.__dict__);return m
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
hp=B/"integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"
go=ROOT/".local/tools/go1.27.1/go/bin/go.exe";fmt=go.with_name("gofmt.exe")
assert pin(gp)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
assert pin(hp)["sha256"]=="6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad"
assert pin(go)["sha256"]=="d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490"
frozen=[pin(OLD/n) for n in names]+[pin(SNAP/n) for n in names]+[pin(gp),pin(hp),pin(go),pin(fmt),pin(Path(__file__).resolve()),pin(ROOT/"execution/toolchains/locked.json")]
mainnames=("internal/host/vault.go","internal/host/host.go","apps/control/main.go","internal/domain/runtime_qualification.go","apps/cli/cli_stream.go")
frozen += [pin(ROOT/n) for n in mainnames]
canonical=[ROOT/"execution/v2.4"/(x+".json") for x in ("checkpoint","path_ownership","step_state","commands")]
canonbefore={p:p.read_bytes() for p in canonical}
assert json.loads(canonbefore[canonical[0]])["revision"]==347
gm=module(gp,gp.read_bytes());guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024);guard.acquire(frozen)
helper=module(hp,guard.get_buffer(str(hp)));new_guard=None
temp=ROOT/".local"/("trusted-host-build-staged-"+uuid.uuid4().hex);temp.mkdir();(temp/"profile").mkdir();(temp/"temp").mkdir()
env={"SystemRoot":"C:/Windows","WINDIR":"C:/Windows","ComSpec":"C:/Windows/System32/cmd.exe","PATH":str(go.parent)+";C:/Windows/System32;C:/Program Files/Git/cmd","PATHEXT":".COM;.EXE;.BAT;.CMD","USERPROFILE":str(temp/"profile"),"LOCALAPPDATA":str(temp/"profile"),"APPDATA":str(temp/"profile"),"TEMP":str(temp/"temp"),"TMP":str(temp/"temp"),"GOROOT":str(go.parent.parent),"GOPATH":str(ROOT/".local/gopath"),"GOCACHE":str(ROOT/".local/gocache"),"GOTOOLCHAIN":"local","GOPROXY":"off","GOSUMDB":"off","GOWORK":"off","CGO_ENABLED":"0","GOFLAGS":"-mod=readonly -p=1","GOMAXPROCS":"2"}
invocations=[]
def invoke(label,argv,timeout):
 out=O/(label+".stdout.raw");err=O/(label+".stderr.raw");result=None;exception=None
 save(label+".intent.json",dict(argv=argv,cwd=str(ROOT),public_environment=env,wall_seconds=timeout,target_host_executions=0,provider_requests=0))
 try:
  with out.open("xb") as stdout,err.open("xb") as stderr:result=helper.run_owned(argv,str(ROOT),env,stdout,stderr,timeout,creation_flags=0x08000000)
 except BaseException as e:exception=repr(e)
 finally:
  receipt=save(label+".invocation.json",dict(argv=argv,cwd=str(ROOT),result=result,exception=exception,actual_native_exit=result.get("actual_exit") if result else None,stdout_ref=pin(out),stderr_ref=pin(err),target_host_executions=0,provider_requests=0))
  invocations.append(receipt)
 assert exception is None and result is not None and result["actual_exit"]==0 and result["error"] is None and not result["timed_out"],label+" native failed"
 c=result["job_cleanup"];assert not c["errors"] and c["active_processes_last_observed"]==0 and all(c[k] is True for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"))
 return receipt
try:
 SRC.mkdir(parents=True,exist_ok=False)
 for n in names:
  original=guard.get_buffer(str(OLD/n));assert original==guard.get_buffer(str(SNAP/n))
  with (SRC/n).open("xb") as f:f.write(original)
 p=SRC/"prepare_runtime.go";raw=p.read_text(encoding="utf-8")
 start=raw.index("func verifyCLIGoalCreation(")
 fixed=r'''func verifyCLIGoalCreation(ctx context.Context,e *environment,s seed,v state,goalID string)error{
 rows,err:=e.db.QueryContext(ctx,"SELECT body FROM idempotency WHERE principal=? AND project=? AND operation='v2:goal.start'",e.ownerID,s.ProjectID);if err!=nil{return err}
 var matchedSnapshot map[string]any
 matches:=0
 for rows.Next(){
  var body string
  if err=rows.Scan(&body);err!=nil{rows.Close();return err}
  var response domain.Object
  if err=json.Unmarshal([]byte(body),&response);err!=nil{rows.Close();return err}
  result,_:=response["result"].(map[string]any)
  if result["goal_id"]!=goalID{continue}
  snapshot,_:=result["snapshot"].(map[string]any)
  if response["status"]!="COMPLETED" || response["method"]!="goal.start" || response["session_id"]!=nil || snapshot["workspace_ref"]!=s.WorkspaceRef || snapshot["model_config_ref"]!=v.ModelRef{rows.Close();return errors.New("CLI goal.start identity or workspace/model snapshot differs")}
  matchedSnapshot=snapshot;matches++
 }
 iterationErr:=rows.Err()
 closeErr:=rows.Close()
 if iterationErr!=nil{return iterationErr}
 if closeErr!=nil{return closeErr}
 if matches!=1{return errors.New("expected one actual completed CLI goal.start")}
 sid:=domain.Str(matchedSnapshot,"session_id");if sid==""{return errors.New("CLI draft did not create a session")}
 // SQLite's production pool has one connection. No query runs until the
 // idempotency cursor releases that connection, including every error path.
 var workspace,model,storedGoal,task,run string
 if err=e.db.QueryRowContext(ctx,"SELECT workspace_ref,model_config_ref,coalesce(goal_id,''),coalesce(task_id,''),coalesce(run_id,'') FROM client_sessions WHERE project_id=? AND id=?",s.ProjectID,sid).Scan(&workspace,&model,&storedGoal,&task,&run);err!=nil{return err}
 if workspace!=s.WorkspaceRef || model!=v.ModelRef || storedGoal!=goalID || task!="" || run!=""{return errors.New("CLI draft session has wrong Goal/workspace/model or started Task/Run")}
 var ordinaryTasks int
 if err=e.db.QueryRowContext(ctx,"SELECT count(*) FROM domain_objects WHERE project=? AND kind='Task' AND json_extract(body,'$.goal_id')=?",s.ProjectID,goalID).Scan(&ordinaryTasks);err!=nil{return err}
 if ordinaryTasks!=0{return errors.New("ordinary CLI draft unexpectedly has a Task")}
 return nil
}
'''
 p.write_text(raw[:start]+fixed,encoding="utf-8",newline="\n")
 with (O/"prepare_runtime.fix.forward.diff").open("xb") as f:f.write("".join(difflib.unified_diff(raw.splitlines(True),(raw[:start]+fixed).splitlines(True),fromfile="v3/prepare_runtime.go",tofile="v4/prepare_runtime.go")).encode())
 invoke("format",[str(fmt),"-w",*[str(SRC/n) for n in names if n.endswith(".go")]],30)
 source_refs=[pin(SRC/n) for n in names]
 source_manifest=save("formatted.source-members.json",source_refs)
 new_guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024);new_guard.acquire(source_refs+[source_manifest])
 binary=temp/"trusted-qualification-host.exe"
 invoke("compile",[str(go),"build","-trimpath","-o",str(binary),*[str(SRC/n) for n in names if n.endswith(".go")]],180)
 assert all(p.read_bytes()==body for p,body in canonbefore.items())
 assert all(pin(ref["path"])==ref for ref in frozen+source_refs)
 closed=save("compile.closed.json",dict(status="COMPILED_SOURCE_ONLY",source_namespace=str(SRC),source_members_ref=source_manifest,binary_ref=pin(binary),invocation_refs=invocations,all_owned_jobs_closed=True,canonical_unchanged=True,old_source_unchanged=True,target_host_executions=0,provider_requests=0,formal_acceptance=False,runtime_qualification=False))
 print(json.dumps(dict(closed_ref=closed,binary_ref=pin(binary),source_namespace=str(SRC),owned_native_jobs=2,provider_requests=0)),flush=True)
finally:
 if new_guard is not None:save("formatted-source-guard.cleanup.actual.json",new_guard.close())
 save("input-source-guard.cleanup.actual.json",guard.close())

