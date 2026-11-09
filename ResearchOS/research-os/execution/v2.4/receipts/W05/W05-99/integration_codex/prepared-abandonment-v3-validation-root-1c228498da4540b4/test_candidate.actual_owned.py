import sys
sys.dont_write_bytecode=True
import hashlib,json,types
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
T=R/".local/worktrees/codex-w0599-prepared-abandonment-v3-7f8246f12ecb4281";S=B/"prepared_run_abandonment_source_v3_codex/6e97da15b65146e5a6ef73a4804c9d12"
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(ref):
 actual=pin(ref["path"]);assert actual["sha256"]==ref["sha256"] and actual["bytes"]==ref["bytes"];return actual
def save(n,v):
 p=O/n
 with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
def module(p,raw):
 m=types.ModuleType("root_abandon_"+p.stem);m.__file__=str(p);exec(compile(raw,str(p),"exec"),m.__dict__);return m
assert T.exists() and T.resolve().is_relative_to((R/".local/worktrees").resolve()) and S.resolve().is_relative_to(B.resolve())
assert pin(S/"HDF.json")["sha256"]=="1e9d2bd0f67ef4a12906181efaa780fe2889f7fb335b30576147f40f62eae138" and pin(S/"MF.json")["sha256"]=="cb9c9e0d8d1a30b35b5b22e6f3eb8b4ac949933e55f2e0798f8c9c8e8d1f9c28"
mf=json.loads((S/"MF.json").read_bytes());hdf=json.loads((S/"HDF.json").read_bytes())
assert mf["productionAuthority"]=="UNSATISFIED" and mf["productionMigration"]=="UNAUTHORIZED" and hdf["total_file_count_in_revision"]==16
actual_files=[p for p in S.rglob("*") if p.is_file()]
assert len(actual_files)==16 and len(mf["members"])==14 and hdf["source_file_count"]==6 and mf["member_count"]==14
members=[verify(ref) for ref in mf["members"].values()]
extra_input_refs=[verify(ref) for key in ("input_refs","main_base_refs","supporting_source_refs") for ref in mf[key]]
for n,ref in mf["members"].items():
 if n.startswith("candidate-root/") and ref.get("previous_ref"):extra_input_refs.append(verify(ref["previous_ref"]))
assert {str(p.resolve()) for p in actual_files}=={str(Path(ref["path"]).resolve()) for ref in members+[pin(S/"HDF.json"),pin(S/"MF.json")]}
sources={n.removeprefix("candidate-root/"):ref for n,ref in mf["members"].items() if n.startswith("candidate-root/")}
assert len(sources)==6
main_before={R/n:(R/n).read_bytes() for n,ref in sources.items() if ref.get("base_sha256")}
for n,ref in sources.items():
 target=T/n
 if ref.get("base_sha256"):assert pin(R/n)["sha256"]==ref["base_sha256"] and pin(target)["sha256"]==ref["base_sha256"]
 else:assert not target.exists()
canonical=[R/"execution/v2.4"/(x+".json") for x in ("checkpoint","path_ownership","step_state","commands")];canon_before={p:p.read_bytes() for p in canonical};assert json.loads(canon_before[canonical[0]])["revision"]==351
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py";hp=B/"integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py";go=R/".local/tools/go1.27.1/go/bin/go.exe";fmt=go.with_name("gofmt.exe")
assert pin(gp)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85" and pin(hp)["sha256"]=="6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad" and pin(go)["sha256"]=="d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490"
frozen=members+extra_input_refs+[pin(S/"HDF.json"),pin(S/"MF.json"),pin(gp),pin(hp),pin(go),pin(fmt),pin(Path(__file__).resolve()),pin(T/"go.mod"),pin(T/"go.sum")]+[pin(p) for p in main_before]
frozen=list({ref["path"]:ref for ref in frozen}.values())
gm=module(gp,gp.read_bytes());guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024);guard.acquire(frozen);helper=module(hp,guard.get_buffer(str(hp)));candidate_guard=None
scratch=T/".local/prepared-abandonment-validation";scratch.mkdir(parents=True,exist_ok=False);(scratch/"profile").mkdir();(scratch/"temp").mkdir()
env={"SystemRoot":"C:/Windows","WINDIR":"C:/Windows","ComSpec":"C:/Windows/System32/cmd.exe","PATH":str(go.parent)+";C:/Windows/System32;C:/Program Files/Git/cmd","PATHEXT":".COM;.EXE;.BAT;.CMD","USERPROFILE":str(scratch/"profile"),"LOCALAPPDATA":str(scratch/"profile"),"APPDATA":str(scratch/"profile"),"TEMP":str(scratch/"temp"),"TMP":str(scratch/"temp"),"GOROOT":str(go.parent.parent),"GOPATH":str(R/".local/gopath"),"GOCACHE":str(R/".local/gocache"),"GOTOOLCHAIN":"local","GOPROXY":"off","GOSUMDB":"off","GOWORK":"off","CGO_ENABLED":"0","GOFLAGS":"-mod=readonly -p=1","GOMAXPROCS":"2"}
refs=[]
def invoke(label,argv,wall):
 out=O/(label+".stdout.raw");err=O/(label+".stderr.raw");result=None;exception=None
 try:
  with out.open("xb") as stdout,err.open("xb") as stderr:result=helper.run_owned(argv,str(T),env,stdout,stderr,wall,creation_flags=0x08000000)
 except BaseException as e:exception=repr(e)
 finally:
  receipt=save(label+".invocation.json",dict(argv=argv,cwd=str(T),public_environment=env,result=result,exception=exception,actual_native_exit=result.get("actual_exit") if result else None,stdout_ref=pin(out),stderr_ref=pin(err),mode="FIXTURE_ISOLATED_SOURCE_VALIDATION",production_root_witness=False,production_db_writes=0,external_provider_requests=0));refs.append(receipt)
 assert exception is None and result and not result["timed_out"] and result["error"] is None
 c=result["job_cleanup"];assert not c["errors"] and c["active_processes_last_observed"]==0 and all(c[k] for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"))
 return result
try:
 for n,ref in sources.items():
  p=T/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(guard.get_buffer(str(Path(ref["path"]))))
 gofiles=[str(T/n) for n in sources if n.endswith(".go")]
 formatted=invoke("format",[str(fmt),"-w",*gofiles],30);assert formatted["actual_exit"]==0
 target_refs=[pin(T/n) for n in sources];target_manifest=save("formatted.source-members.json",target_refs)
 candidate_guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024);candidate_guard.acquire(target_refs+[target_manifest])
 result=invoke("test",[str(go),"test","-count=1","-json","./internal/domain","-run","^TestPreparedRunAbandonment"],180)
 events=[json.loads(x) for x in (O/"test.stdout.raw").read_text(encoding="utf-8").splitlines() if x.startswith("{")]
 tests={e["Test"]:e["Action"] for e in events if "Test" in e and e["Action"] in ("pass","fail","skip")}
 assert all(p.read_bytes()==raw for p,raw in main_before.items()) and all(p.read_bytes()==raw for p,raw in canon_before.items())
 closed=save("validation.closed.json",dict(status="PASSED_FIXTURE_ONLY" if result["actual_exit"]==0 else "FAILED_FIXTURE_NATIVE_CLOSED",actual_native_exit=result["actual_exit"],test_actions=tests,source_members_ref=target_manifest,invocation_refs=refs,all_owned_jobs_closed=True,main_canonical_unchanged=True,production_db_writes=0,production_root_witness=False,external_provider_requests=0,formal_acceptance=False))
 print(json.dumps(dict(closed_ref=closed,actual_native_exit=result["actual_exit"],test_actions=tests,all_owned_jobs_closed=True,external_provider_requests=0)),flush=True)
 assert result["actual_exit"]==0 and tests and all(a=="pass" for a in tests.values()),"candidate fixture tests failed; immutable diagnostic closed record saved"
finally:
 if candidate_guard is not None:
  c=candidate_guard.close();save("candidate-source-guard.cleanup.actual.json",c);assert c["closed"] and not c["errors"] and c["retained_handles_count"]==0
 cleanup=guard.close();assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0;save("input-source-guard.cleanup.actual.json",cleanup)
