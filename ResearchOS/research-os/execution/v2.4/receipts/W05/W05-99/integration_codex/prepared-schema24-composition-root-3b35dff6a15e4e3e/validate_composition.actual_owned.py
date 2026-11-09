import sys
sys.dont_write_bytecode=True
import hashlib,json,types
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
T=R/".local/worktrees/codex-w0599-prepared-maintenance-native-52c5a209cfd34eca";S=B/"prepared_abandonment_native_authority_source_codex/f6373acf36474d869fa8a64f3c490864";C=B/"prepared_run_abandonment_source_v4_codex/f1cd47ca0f9544bfbe94b51a80d7c492";M=B/"prepared_abandonment_schema_upgrade_source_codex/e841e7fcddaa45ecb115f84df9827af2"
P=B/"integration_codex/native-authority-unprovisioned-component-root-cb0935d7bf444f4f"
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(ref):
 actual=pin(ref["path"]);assert actual["sha256"]==ref["sha256"] and actual["bytes"]==ref["bytes"];return actual
def save(n,v):
 p=O/n
 with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
def module(p,raw):
 m=types.ModuleType("root_composition_"+p.stem);m.__file__=str(p);exec(compile(raw,str(p),"exec"),m.__dict__);return m
expected={S:("2f33da54d8e91dad1651da92ecbbc6506d0520a541b730176129fafd2db0a3d2","349aa6b33bd8a2616aa619607b25bea10f502e60292f734abcfc3e21a311215c"),C:("16034d64a0e95c9697a1afda1fa1babcdaa79652c3e9e3847503fc5b87896565","fc99c790329ebf190adb04e6b7243c3c3c375f9bb361a3173c910b55b0a45733"),M:("a6e03021860808f09d7e36622a6aff9206a3e2aa18008afd94c62ff00f177a99","b1585d636212dfe6592bf51aff78257decff13a14d4efc148f6c0f66de94d42c")}
for d,(h,m) in expected.items():assert pin(d/"HDF.json")["sha256"]==h and pin(d/"MF.json")["sha256"]==m
manifests=[json.loads((d/"MF.json").read_bytes()) for d in (C,S,M)]
refs=[verify(ref) for mf in manifests for ref in mf["members"].values()]+[verify(ref) for mf in manifests for ref in mf.get("input_refs",[])]
sources={};overlap={}
for d,mf in zip((C,S,M),manifests):
 for n,ref in mf["members"].items():
  if not n.startswith("candidate-root/"):continue
  target=n.removeprefix("candidate-root/")
  if target in sources:overlap[target]=dict(previous_ref=sources[target],superseding_ref=ref)
  sources[target]=ref
assert len(sources)==35 and list(overlap)==["internal/domain/prepared_run_abandonment.go"]
previous=json.loads((P/"formatted.source-members.json").read_bytes());previous_by_path={str(Path(ref["path"])):ref for ref in previous}
assert len(previous)==25 and json.loads((P/"validation.closed.json").read_bytes())["status"]=="UNPROVISIONED_AUTHORITY_LEAF_TESTS_AND_ENROLLMENT_BUILD_PASSED_SOURCE_ONLY"
main_files=["go.mod","go.sum","apps/control/main.go","internal/domain/store.go","internal/domain/runtime_coordinator_windows.go","internal/domain/backup_migration.go","internal/domain/backup.go","internal/domain/backup_upgrade.go","internal/domain/backup_host_configuration.go","internal/domain/backup_configuration_upgrade_test.go"];main_before={R/n:(R/n).read_bytes() for n in main_files}
for n in sources:
 target=T/n
 if str(target) in previous_by_path:verify(previous_by_path[str(target)])
 elif n in main_files:assert target.read_bytes()==main_before[R/n]
 else:assert not target.exists()
for n in ("go.mod","go.sum"):assert (T/n).read_bytes()==main_before[R/n]
canonical=[R/"execution/v2.4"/(n+".json") for n in ("checkpoint","path_ownership","step_state","commands")];before={p:p.read_bytes() for p in canonical};assert json.loads(before[canonical[0]])["revision"]==352
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py";hp=B/"integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py";go=R/".local/tools/go1.27.1/go/bin/go.exe";fmt=go.with_name("gofmt.exe")
assert pin(gp)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85" and pin(hp)["sha256"]=="6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad" and pin(go)["sha256"]=="d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490"
refs+=[pin(p) for p in main_before]+[pin(T/"go.mod"),pin(T/"go.sum"),pin(gp),pin(hp),pin(go),pin(fmt),pin(Path(__file__).resolve())]+[pin(d/n) for d in (S,C,M) for n in ("HDF.json","MF.json")];refs=list({r["path"]:r for r in refs}.values())
gm=module(gp,gp.read_bytes());guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024);guard.acquire(refs);helper=module(hp,guard.get_buffer(str(hp)));candidate=None
scratch=T/".local/prepared-schema24-validation";scratch.mkdir(parents=True,exist_ok=False);(scratch/"profile").mkdir();(scratch/"temp").mkdir()
env={"SystemRoot":"C:/Windows","WINDIR":"C:/Windows","ComSpec":"C:/Windows/System32/cmd.exe","PATH":str(go.parent)+";C:/Windows/System32;C:/Program Files/Git/cmd","PATHEXT":".COM;.EXE;.BAT;.CMD","USERPROFILE":str(scratch/"profile"),"LOCALAPPDATA":str(scratch/"profile"),"APPDATA":str(scratch/"profile"),"TEMP":str(scratch/"temp"),"TMP":str(scratch/"temp"),"GOROOT":str(go.parent.parent),"GOPATH":str(R/".local/gopath"),"GOCACHE":str(R/".local/gocache"),"GOTOOLCHAIN":"local","GOPROXY":"off","GOSUMDB":"off","GOWORK":"off","CGO_ENABLED":"0","GOFLAGS":"-mod=readonly -p=1","GOMAXPROCS":"2"}
invocations=[]
def invoke(label,argv,wall):
 out=O/(label+".stdout.raw");err=O/(label+".stderr.raw");result=None;exception=None
 try:
  with out.open("xb") as stdout,err.open("xb") as stderr:result=helper.run_owned(argv,str(T),env,stdout,stderr,wall,creation_flags=0x08000000)
 except BaseException as e:exception=repr(e)
 finally:
  receipt=save(label+".invocation.json",dict(argv=argv,cwd=str(T),public_environment=env,result=result,exception=exception,actual_native_exit=result.get("actual_exit") if result else None,stdout_ref=pin(out),stderr_ref=pin(err),provider_requests=0,production_db_writes=0));invocations.append(receipt)
 assert exception is None and result and not result["timed_out"] and result["error"] is None
 c=result["job_cleanup"];assert not c["errors"] and c["active_processes_last_observed"]==0 and all(c[k] for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"))
 print(json.dumps(dict(progress=label,actual_native_exit=result["actual_exit"],receipt_ref=receipt)),flush=True)
 return result
def closed(status,failed=None,tests=None,binary=None):
 assert all(p.read_bytes()==raw for p,raw in before.items()) and all(p.read_bytes()==raw for p,raw in main_before.items())
 ref=save("validation.closed.json",dict(status=status,failed_step=failed,invocation_refs=invocations,source_overlay_ref=overlay,formatted_source_ref=formatted_ref if "formatted_ref" in globals() else None,test_actions=tests,binary_ref=binary,all_owned_jobs_closed=True,main_canonical_unchanged=True,issuer_anchor_provisioned=False,complete_control_built=binary is not None,migration_dependency_source_sealed=True,production_db_writes=0,provider_requests=0,formal_acceptance=False))
 print(json.dumps(dict(closed_ref=ref,status=status,provider_requests=0)),flush=True)
try:
 for n,ref in sources.items():
  target=T/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(guard.get_buffer(str(Path(ref["path"]))))
 overlay=save("source-overlay.json",dict(core_manifest_ref=pin(C/"MF.json"),native_manifest_ref=pin(S/"MF.json"),migration_manifest_ref=pin(M/"MF.json"),sources=sources,overlap=overlap,source_count=35,Main_adopted=False))
 result=invoke("format",[str(fmt),"-w",*[str(T/n) for n in sources if n.endswith(".go")]],45)
 if result["actual_exit"]!=0:closed("FAILED_FORMAT_NATIVE_CLOSED","format");raise AssertionError("schema composition gofmt failed")
 targets=[pin(T/n) for n in sources];formatted_ref=save("formatted.source-members.json",targets)
 candidate=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024);candidate.acquire(targets+[formatted_ref])
 tests={}
 for label,pattern,wall in (("new-migration-suite","^TestPreparedUpgrade",300),("historical-backup-regression","^Test(W17Upgrade|W18|ConfigurationUpgrade|PreparedRunAbandonment)",480)):
  test=invoke(label,[str(go),"test","-count=1","-json","-timeout="+str(wall-15)+"s","-run",pattern,"./internal/domain"],wall)
  events=[json.loads(l) for l in (O/(label+".stdout.raw")).read_text(encoding="utf-8").splitlines() if l.startswith("{")]
  actions={e["Test"]:e["Action"] for e in events if "Test" in e and e["Action"] in ("pass","fail","skip")}
  tests[label]=dict(actions=actions,pass_count=sum(v=="pass" for v in actions.values()),fail_count=sum(v=="fail" for v in actions.values()),skip_count=sum(v=="skip" for v in actions.values()))
  if test["actual_exit"]!=0 or not actions or any(v=="fail" for v in actions.values()):closed("FAILED_DOMAIN_TEST_NATIVE_CLOSED",label,tests);raise AssertionError("schema composition "+label+" failed")
 binaries={}
 for label,target in (("control-build","./apps/control"),("maintenance-root-build","./ops/supervisor/recovery_root")):
  binary=scratch/(label+".exe");result=invoke(label,[str(go),"build","-trimpath","-buildvcs=false","-o",str(binary),target],180)
  if result["actual_exit"]!=0:closed("FAILED_COMPOSITION_BUILD_NATIVE_CLOSED",label,tests);raise AssertionError("schema composition binary build failed")
  binaries[label]=pin(binary)
 closed("SCHEMA24_SOURCE_COMPOSITION_NEW_TESTS_AND_BACKUP_REGRESSION_AND_BINARIES_PASSED_UNPROVISIONED",tests=tests,binary=binaries)
finally:
 if candidate is not None:
  c=candidate.close();save("candidate-source-guard.cleanup.actual.json",c);assert c["closed"] and not c["errors"] and c["retained_handles_count"]==0
 c=guard.close();save("input-source-guard.cleanup.actual.json",c);assert c["closed"] and not c["errors"] and c["retained_handles_count"]==0
