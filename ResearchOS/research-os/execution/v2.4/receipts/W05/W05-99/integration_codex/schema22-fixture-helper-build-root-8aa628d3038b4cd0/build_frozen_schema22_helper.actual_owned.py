import sys
sys.dont_write_bytecode=True
import hashlib,json,types
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
S=B/"schema22_public_fixture_bridge_source_codex/3d7d237d23244950a6d9008753e3fde9";F=B/"host_configuration_upgrade_executor_codex/old22-build-40e94f3f6e53442fa07068089c0de64a/frozen_source";T=R/".local/worktrees/codex-w0599-schema22-helper-8cabf8e8572a4b03";P=R/".local/trusted-schema22-helper-build-6b6c2c0114fa4409"
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(ref):
 actual=pin(ref["path"]);assert actual["sha256"]==ref["sha256"] and actual["bytes"]==ref["bytes"];return actual
def save(n,v):
 p=O/n
 with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
def mod(p,raw):
 m=types.ModuleType("root_historical22_"+p.stem);m.__file__=str(p);exec(compile(raw,str(p),"exec"),m.__dict__);return m
assert pin(S/"HDF.json")["sha256"]=="7d5d39f04557592c54bbf9ff877d787542f8c34549e4cd284ae26a85a71ad037" and pin(S/"MF.json")["sha256"]=="177d8f3c3199a258b83b4acc7c29b7be67323966f9c023642a6ddd4ebc089819"
mf=json.loads((S/"MF.json").read_bytes());assert len(mf["members"])==20 and len(mf["base_refs"])==506
refs=[verify(ref) for ref in mf["members"].values()]+[verify(ref) for ref in mf["base_refs"]]+[pin(S/n) for n in ("HDF.json","MF.json")]
originals={str(Path(ref["path"]).relative_to(F)):ref for ref in mf["base_refs"] if Path(ref["path"]).is_relative_to(F)};assert len(originals)==502 and sum(ref["bytes"] for ref in originals.values())==5621542
assert set(originals)=={str(p.relative_to(F)) for p in F.rglob("*") if p.is_file()}
overlays={n.removeprefix("historical22-overlay/"):ref for n,ref in mf["historical22_overlay_refs"].items()};assert len(overlays)==2 and not (set(overlays)&set(originals))
canonical=[R/"execution/v2.4"/(n+".json") for n in ("checkpoint","path_ownership","step_state","commands")];before={p:p.read_bytes() for p in canonical};assert json.loads(before[canonical[0]])["revision"]==353
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py";hp=B/"integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py";go=R/".local/tools/go1.27.1/go/bin/go.exe";fmt=go.with_name("gofmt.exe")
assert pin(gp)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85" and pin(hp)["sha256"]=="6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad" and pin(go)["sha256"]=="d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490"
refs+=[pin(p) for p in (gp,hp,go,fmt,Path(__file__).resolve())];refs=list({r["path"]:r for r in refs}.values())
gm=mod(gp,gp.read_bytes());guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024);guard.acquire(refs);helper=mod(hp,guard.get_buffer(str(hp)));candidate=None
T.mkdir(parents=True,exist_ok=False);P.mkdir(parents=True,exist_ok=False);(P/"profile").mkdir();(P/"temp").mkdir()
env={"SystemRoot":"C:/Windows","WINDIR":"C:/Windows","ComSpec":"C:/Windows/System32/cmd.exe","PATH":str(go.parent)+";C:/Windows/System32;C:/Program Files/Git/cmd","PATHEXT":".COM;.EXE;.BAT;.CMD","USERPROFILE":str(P/"profile"),"LOCALAPPDATA":str(P/"profile"),"APPDATA":str(P/"profile"),"TEMP":str(P/"temp"),"TMP":str(P/"temp"),"GOROOT":str(go.parent.parent),"GOPATH":str(R/".local/gopath"),"GOCACHE":str(R/".local/gocache"),"GOTOOLCHAIN":"local","GOPROXY":"off","GOSUMDB":"off","GOWORK":"off","CGO_ENABLED":"0","GOFLAGS":"-mod=readonly -p=1","GOMAXPROCS":"2"}
invocations=[]
def invoke(label,argv,wall):
 out=O/(label+".stdout.raw");err=O/(label+".stderr.raw");result=None;exception=None
 try:
  with out.open("xb") as stdout,err.open("xb") as stderr:result=helper.run_owned(argv,str(T),env,stdout,stderr,wall,creation_flags=0x08000000)
 except BaseException as e:exception=repr(e)
 receipt=save(label+".invocation.json",dict(argv=argv,cwd=str(T),public_environment=env,result=result,exception=exception,actual_native_exit=result.get("actual_exit") if result else None,stdout_ref=pin(out),stderr_ref=pin(err),provider_requests=0,production_db_writes=0));invocations.append(receipt)
 assert exception is None and result and not result["timed_out"] and result["error"] is None
 c=result["job_cleanup"];assert not c["errors"] and c["active_processes_last_observed"]==0 and all(c[k] for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"))
 print(json.dumps(dict(progress=label,actual_native_exit=result["actual_exit"],receipt_ref=receipt)),flush=True);return result
def closed(status,failed=None,binary=None):
 assert all(p.read_bytes()==raw for p,raw in before.items())
 ref=save("validation.closed.json",dict(status=status,failed_step=failed,source_handoff_ref=pin(S/"HDF.json"),source_manifest_ref=pin(S/"MF.json"),source_overlay_ref=overlay,formatted_source_ref=formatted_ref if "formatted_ref" in globals() else None,original502_preserved=True,staged_source_root=str(T),source_file_count=504,binary_ref=binary,invocation_refs=invocations,all_owned_jobs_closed=True,canonical_unchanged=True,helper_executed=False,model_executed=False,provider_requests=0,production_db_writes=0,formal_acceptance=False));print(json.dumps(dict(closed_ref=ref,status=status)),flush=True)
try:
 for n,ref in {**originals,**overlays}.items():
  dst=T/n;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(guard.get_buffer(str(Path(ref["path"]))))
 assert len([p for p in T.rglob("*") if p.is_file()])==504
 overlay=save("source-overlay.json",dict(original_source_root=str(F),originals=originals,overlays=overlays,source_count=504,original_frozen_source_changed=False,current_domain_overlay_applied=False))
 new_go=[str(T/n) for n in overlays if n.endswith(".go")];assert len(new_go)==1
 result=invoke("format-only-new-test-helper",[str(fmt),"-w",*new_go],30)
 if result["actual_exit"]!=0:closed("FAILED_FORMAT_NATIVE_CLOSED","format-only-new-test-helper");raise AssertionError("schema22 helper gofmt failed")
 targets=[pin(p) for p in T.rglob("*") if p.is_file()]
 for n,ref in originals.items():assert pin(T/n)["sha256"]==ref["sha256"] and pin(T/n)["bytes"]==ref["bytes"]
 formatted_ref=save("formatted.source-members.json",targets);candidate=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024);candidate.acquire(targets+[formatted_ref])
 binary=P/"schema22-fixture-helper.exe";result=invoke("compile-historical-domain-test-helper",[str(go),"test","-c","-trimpath","-buildvcs=false","-o",str(binary),"./internal/domain"],300)
 if result["actual_exit"]!=0:closed("FAILED_SCHEMA22_HELPER_COMPILE_NATIVE_CLOSED","compile-historical-domain-test-helper");raise AssertionError("schema22 fixture helper compilation failed")
 assert len([p for p in T.rglob("*") if p.is_file()])==504
 closed("FROZEN_SCHEMA22_HELPER_TEST_PACKAGE_COMPILED_COMPONENT_ONLY",binary=pin(binary))
finally:
 if candidate is not None:
  c=candidate.close();save("candidate-source-guard.cleanup.actual.json",c);assert c["closed"] and not c["errors"] and c["retained_handles_count"]==0
 c=guard.close();save("input-source-guard.cleanup.actual.json",c);assert c["closed"] and not c["errors"] and c["retained_handles_count"]==0
