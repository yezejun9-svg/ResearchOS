import sys
sys.dont_write_bytecode=True
import hashlib,json,types,uuid
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
T=R/".local/worktrees/codex-w0599-prepared-abandonment-5480a340ab04468a";expected="adc460c2138528f163f7fdab5e8d81dde157b7fb"
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(n,v):
 p=O/n
 with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
def module(p,raw):
 m=types.ModuleType("root_worktree_"+p.stem);m.__file__=str(p);exec(compile(raw,str(p),"exec"),m.__dict__);return m
assert not T.exists() and T.resolve().is_relative_to((R/".local/worktrees").resolve())
canonical=[R/"execution/v2.4"/(x+".json") for x in ("checkpoint","path_ownership","step_state","commands")];before={p:p.read_bytes() for p in canonical};assert json.loads(before[canonical[0]])["revision"]==350
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py";hp=B/"integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py";git=Path("C:/Program Files/Git/cmd/git.exe")
assert pin(gp)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85" and pin(hp)["sha256"]=="6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad"
frozen=[pin(gp),pin(hp),pin(git),pin(Path(__file__).resolve())]+[pin(R/x) for x in ("go.mod","go.sum","internal/domain/store.go","internal/domain/runtime_coordinator_windows.go","internal/domain/backup_migration.go")]
gm=module(gp,gp.read_bytes());guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024);guard.acquire(frozen);helper=module(hp,guard.get_buffer(str(hp)))
scratch=R/".local"/("prepared-abandonment-toolenv-"+uuid.uuid4().hex);scratch.mkdir();(scratch/"profile").mkdir();(scratch/"temp").mkdir();(scratch/"empty-hooks").mkdir()
env={"SystemRoot":"C:/Windows","WINDIR":"C:/Windows","ComSpec":"C:/Windows/System32/cmd.exe","PATH":str(git.parent)+";C:/Windows/System32","PATHEXT":".COM;.EXE;.BAT;.CMD","USERPROFILE":str(scratch/"profile"),"LOCALAPPDATA":str(scratch/"profile"),"APPDATA":str(scratch/"profile"),"TEMP":str(scratch/"temp"),"TMP":str(scratch/"temp"),"GIT_CONFIG_NOSYSTEM":"1","GIT_CONFIG_GLOBAL":"NUL","GIT_TERMINAL_PROMPT":"0"}
def invoke(label,argv,wall):
 out=O/(label+".stdout.raw");err=O/(label+".stderr.raw");result=None;exception=None
 try:
  with out.open("xb") as stdout,err.open("xb") as stderr:result=helper.run_owned(argv,str(R),env,stdout,stderr,wall,creation_flags=0x08000000)
 except BaseException as e:exception=repr(e)
 finally:
  receipt=save(label+".invocation.json",dict(argv=argv,cwd=str(R),public_environment=env,result=result,exception=exception,actual_native_exit=result.get("actual_exit") if result else None,stdout_ref=pin(out),stderr_ref=pin(err),provider_requests=0));print(json.dumps(dict(progress=label,receipt_ref=receipt)),flush=True)
 assert exception is None and result and result["actual_exit"]==0 and not result["timed_out"] and result["error"] is None
 c=result["job_cleanup"];assert not c["errors"] and c["active_processes_last_observed"]==0 and all(c[k] for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"))
 return receipt
try:
 verify=invoke("head-before",[str(git),"rev-parse","HEAD"],30);assert (O/"head-before.stdout.raw").read_text().strip()==expected
 create=invoke("create-worktree",[str(git),"-c","core.hooksPath="+str(scratch/"empty-hooks"),"worktree","add","--detach",str(T),expected],180)
 verify_after=invoke("head-after",[str(git),"rev-parse","HEAD"],30);assert (O/"head-after.stdout.raw").read_text().strip()==expected
 for x in ("go.mod","go.sum","internal/domain/store.go","internal/domain/runtime_coordinator_windows.go","internal/domain/backup_migration.go"):assert (T/x).read_bytes()==(R/x).read_bytes()
 assert all(p.read_bytes()==raw for p,raw in before.items()) and all(pin(ref["path"])==ref for ref in frozen)
 ready=save("isolation.ready.json",dict(status="DETACHED_CANDIDATE_WORKTREE_READY_NO_SOURCE_OVERLAY",repository_root=str(R),worktree_root=str(T),head=expected,invocation_refs=[verify,create,verify_after],main_canonical_unchanged=True,source_overlay=False,all_owned_jobs_closed=True,provider_requests=0,formal_acceptance=False))
 print(json.dumps(dict(ready_ref=ready,worktree_root=str(T),owned_jobs=3,provider_requests=0)),flush=True)
finally:
 cleanup=guard.close();assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0;save("source-guard.cleanup.actual.json",cleanup)

