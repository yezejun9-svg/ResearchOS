import sys
sys.dont_write_bytecode=True
import hashlib,json,types
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
T=Path("D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2")
P=R/".local/worktrees/codex-w0599-schema24-fixture-748db574d1db4c6b"
A=B/"integration_codex/schema24-fixture-targeted-root-405c90d2040c4c41"
V=B/"native_migration_harness_error_revision_codex/e57c696eaf418862f0eb721ec8c8"
Y=B/"schema24_fixture_actual_independent_review_codex/3e1e9204c6804e119c289c06a07d953d"
Z=B/"native_migration_error_revision_independent_review_codex/68fe97d536664f35b445543a7a835a25"
ISO=B/"integration_codex/native-harness43-isolation-root-1b43ec8438c3470e"
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(ref):
 a=pin(ref["path"]);assert a["sha256"]==ref["sha256"] and a["bytes"]==ref["bytes"];return a
def save(n,v):
 p=O/n
 with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
 return pin(p)
def module(p,raw):
 m=types.ModuleType("root_native43_"+p.stem);m.__file__=str(p);exec(compile(raw,str(p),"exec"),m.__dict__);return m
assert pin(V/"HDF.json")["sha256"]=="e8886cf85b95a84bade493e12691f995a631c179460726d29beba8e5c2a9b92e"
assert pin(V/"MF.json")["sha256"]=="89c0e2fcef8a3674f0a6513484fbfa22079c7fb4920dcc279ecc54778222dc63"
assert pin(Y/"HDF.json")["sha256"]=="ed484a92555ad3cbfcd6cabe3aa72a12835ebb96e8d2675217d650fedfd070c5"
assert pin(Z/"HDF.json")["sha256"]=="24938d80ded0e0ef79c82a4e7df1a51b22ed0a04a84c3ffb66303c9875d782f1"
assert json.loads((Z/"HDF.json").read_bytes())["decision"]=="EXACT_REJECTION_SOURCE_ACCEPTED_FOR_ROOT_GUARDED_NARROW_TESTS_ONLY_STOP"
assert pin(ISO/"isolation.ready.json")["sha256"]=="c31c74e9e55e6bbcdca678a044787c2bfe280bed7d5aa5fbc11548fce54ab94b"
assert pin(A/"formatted.source-members.json")["sha256"]=="c7db2cf39229b2e8ff48796de660b99f7000181f693778f43a5f56b0c6ecc0ef"
parent=json.loads((A/"formatted.source-members.json").read_bytes());assert len(parent)==41
sources={}
for ref in parent:
 path=Path(ref["path"]);assert path.is_relative_to(P);sources[path.relative_to(P).as_posix()]=verify(ref)
mf=json.loads((V/"MF.json").read_bytes());refs=[verify(ref) for ref in mf["members"].values()]
for n,ref in mf["members"].items():
 if n.startswith("candidate-root/"):
  key=n.removeprefix("candidate-root/");assert key not in sources;sources[key]=verify(ref)
assert len(sources)==43
for n in sources:
 p=T/n
 if p.exists():assert (R/n).exists() and p.read_bytes()==(R/n).read_bytes()
canonical=[R/"execution/v2.4"/(n+".json") for n in ("checkpoint","path_ownership","step_state","commands")]
before={p:p.read_bytes() for p in canonical};assert json.loads(before[canonical[0]])["revision"]==355
main_names=("go.mod","go.sum","apps/control/main.go","internal/domain/store.go","internal/domain/runtime_coordinator_windows.go","internal/domain/backup_migration.go","internal/domain/backup.go","internal/domain/backup_upgrade.go","internal/domain/backup_host_configuration.go","internal/domain/backup_configuration_upgrade_test.go","internal/domain/backup_upgrade_test.go","internal/domain/backup_command_queue_test.go","internal/domain/backup_host_configuration_test.go","internal/domain/client_configuration_test.go")
main_before={R/n:(R/n).read_bytes() for n in main_names}
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
hp=B/"integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"
go=R/".local/tools/go1.27.1/go/bin/go.exe";fmt=go.with_name("gofmt.exe");python=Path(sys.executable)
assert pin(python)["sha256"]=="cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b"
assert pin(gp)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
assert pin(hp)["sha256"]=="6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad"
assert pin(go)["sha256"]=="d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490"
refs += list(sources.values())+[pin(p) for p in main_before]+[pin(gp),pin(hp),pin(go),pin(fmt),pin(python),pin(Path(__file__).resolve()),pin(T/"go.mod"),pin(T/"go.sum"),pin(ISO/"isolation.ready.json"),pin(A/"validation.closed.json"),pin(A/"formatted.source-members.json")]
for d,mname in ((Y,"manifest.json"),(Z,"MF.json"),(V,"MF.json")):
 refs += [pin(d/"HDF.json"),pin(d/mname)]
 members=json.loads((d/mname).read_bytes())["members"];members=members.values() if isinstance(members,dict) else members
 refs += [verify(ref) for ref in members]
refs=list({r["path"]:r for r in refs}.values())
gm=module(gp,gp.read_bytes());guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=768*1024*1024);guard.acquire(refs)
helper=module(hp,guard.get_buffer(str(hp)));candidate=None;compiled=None;binary_guard=None
scratch=R/".local/native-harness43-compile-env-678b98f8f3134dd7";scratch.mkdir(parents=True,exist_ok=False)
for n in ("profile","temp","programs"):(scratch/n).mkdir()
env={"SystemRoot":"C:/Windows","WINDIR":"C:/Windows","ComSpec":"C:/Windows/System32/cmd.exe","PATH":str(go.parent)+";C:/Windows/System32;C:/Program Files/Git/cmd","PATHEXT":".COM;.EXE;.BAT;.CMD","USERPROFILE":str(scratch/"profile"),"LOCALAPPDATA":str(scratch/"profile"),"APPDATA":str(scratch/"profile"),"TEMP":str(scratch/"temp"),"TMP":str(scratch/"temp"),"GOROOT":str(go.parent.parent),"GOPATH":str(R/".local/gopath"),"GOCACHE":str(R/".local/gocache"),"GOTOOLCHAIN":"local","GOPROXY":"off","GOSUMDB":"off","GOWORK":"off","CGO_ENABLED":"0","GOFLAGS":"-mod=readonly -p=1","GOMAXPROCS":"2"}
invocations=[];binaries={};actions={};inventory_ref=None;formatted_ref=None;overlay_ref=None
def invoke(label,argv,wall):
 out=O/(label+".stdout.raw");err=O/(label+".stderr.raw");result=None;exception=None
 try:
  with out.open("xb") as stdout,err.open("xb") as stderr:result=helper.run_owned(argv,str(T),env,stdout,stderr,wall,creation_flags=0x08000000)
 except BaseException as e:exception=repr(e)
 finally:
  receipt=save(label+".invocation.json",dict(argv=argv,cwd=str(T),public_environment=env,result=result,exception=exception,actual_native_exit=result.get("actual_exit") if result else None,stdout_ref=pin(out),stderr_ref=pin(err),external_model_provider_requests=0,production_db_writes=0));invocations.append(receipt)
 assert exception is None and result and not result["timed_out"] and result["error"] is None
 c=result["job_cleanup"];assert not c["errors"] and c["active_processes_last_observed"]==0 and all(c[k] for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"))
 print(json.dumps(dict(progress=label,actual_native_exit=result["actual_exit"],receipt_ref=receipt)),flush=True)
 return result
def success(label,argv,wall):
 result=invoke(label,argv,wall)
 if result["actual_exit"]!=0:raise AssertionError("native43 "+label+" failed actualExit="+str(result["actual_exit"]))
 return result
def closed(status,error=None):
 assert all(p.read_bytes()==raw for p,raw in before.items()) and all(p.read_bytes()==raw for p,raw in main_before.items())
 ref=save("validation.closed.json",dict(status=status,error=error,invocation_refs=invocations,current_source_root=str(T),source_count=43,source_overlay_ref=overlay_ref,formatted_source_ref=formatted_ref,compiler_input_inventory_ref=inventory_ref,binary_refs=binaries,unit_actions=actions,unit_pass_count=sum(v=="pass" for v in actions.values()),unit_fail_count=sum(v=="fail" for v in actions.values()),unit_skip_count=sum(v=="skip" for v in actions.values()),all_owned_jobs_closed=True,main_canonical_unchanged=True,source_delta_review_ref=pin(Z/"HDF.json"),parent267_actual_review_ref=pin(Y/"HDF.json"),native_migration_cases_executed=0,real_owner_private_input_used=False,issuer_signatures_created=0,production_db_writes=0,external_model_provider_requests=0,original_trial_provider_requests=None,Main_adopted=False,formal_acceptance=False))
 print(json.dumps(dict(closed_ref=ref,status=status)),flush=True)
try:
 for n,ref in sources.items():
  target=T/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(guard.get_buffer(str(Path(ref["path"]))))
 overlay_ref=save("source-overlay.json",dict(sources=sources,source_count=43,parent41_formatted_ref=pin(A/"formatted.source-members.json"),native_revision_manifest_ref=pin(V/"MF.json"),Main_adopted=False))
 success("format",[str(fmt),"-w",*[str(T/n) for n in sources if n.endswith(".go")]],45)
 targets=[pin(T/n) for n in sources];formatted_ref=save("formatted.source-members.json",targets)
 for n,ref in list(sources.items())[:41]:assert pin(T/n)["sha256"]==ref["sha256"] and pin(T/n)["bytes"]==ref["bytes"]
 candidate=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024);candidate.acquire(targets+[formatted_ref])
 success("tagged-compiler-input-list",[str(go),"list","-test","-deps","-compiled","-tags=researchos_native_recovery_harness","-json","./internal/domain","./internal/recoveryauthority","./apps/control","./ops/supervisor/recovery_root","./ops/supervisor/recovery_enrollment","./ops/backup"],240)
 raw=(O/"tagged-compiler-input-list.stdout.raw").read_text(encoding="utf-8");decoder=json.JSONDecoder();pos=0;packages=[];inputs={};embeds=[]
 fields=("GoFiles","CgoFiles","CFiles","CXXFiles","MFiles","HFiles","FFiles","SFiles","SwigFiles","SwigCXXFiles","SysoFiles","CompiledGoFiles","TestGoFiles","XTestGoFiles","EmbedFiles","TestEmbedFiles","XTestEmbedFiles")
 while pos<len(raw):
  while pos<len(raw) and raw[pos].isspace():pos+=1
  if pos==len(raw):break
  pkg,pos=decoder.raw_decode(raw,pos);assert not pkg.get("Error") and not pkg.get("DepsErrors");packages.append(pkg.get("ImportPath"))
  if not pkg.get("Dir"):continue
  directory=Path(pkg["Dir"])
  for field in fields:
   for name in pkg.get(field,[]):
    path=Path(name);path=path if path.is_absolute() else directory/path;ref=pin(path);inputs[str(path)]=ref
    if field.endswith("EmbedFiles"):embeds.append(dict(package=pkg["ImportPath"],ref=ref,field=field))
 product={}
 for relative in ("apps/control","internal","adapters","evaluation","ops","migrations/sqlite","spec/v2.0/contracts"):
  root=T/relative;assert root.is_dir() and not root.is_symlink()
  for path in root.rglob("*"):
   assert not path.is_symlink()
   if path.is_dir():continue
   assert path.is_file();product[str(path)]=pin(path)
 for relative in ("go.mod","go.sum","execution/toolchains/locked.json"):product[str(T/relative)]=pin(T/relative)
 tools=[pin(path) for path in (go.parent.parent/"pkg/tool/windows_amd64").iterdir() if path.is_file()]
 for e in embeds:
  path=Path(e["ref"]["path"])
  if path.is_relative_to(T):assert str(path) in product
 inventory_ref=save("actual-tagged-compiler-input-inventory.json",dict(package_count=len(packages),packages=packages,build_input_count=len(inputs),build_inputs=list(inputs.values()),actual_embed_files=embeds,product_inventory_count=len(product),product_inventory=list(product.values()),compiler_tool_refs=tools,GoRef=pin(go),selected_module_files_pinned=True,includes_actual_test_and_embed_inputs=True,build_tag="researchos_native_recovery_harness",GOWORK="off",CGO_ENABLED="0",Main_adopted=False,formal_acceptance=False))
 compiled_refs=list({r["path"]:r for r in [*inputs.values(),*product.values(),*tools,inventory_ref]}.values())
 compiled=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=1024*1024*1024);compiled.acquire(compiled_refs)
 test=invoke("exact-error-unit",[str(go),"test","-tags=researchos_native_recovery_harness","-count=1","-json","-timeout=115s","-run","^TestNativeHarnessExpectedError$","./internal/domain"],130)
 events=[json.loads(l) for l in (O/"exact-error-unit.stdout.raw").read_text(encoding="utf-8").splitlines() if l.startswith("{")]
 actions={e["Test"]:e["Action"] for e in events if "Test" in e and e["Action"] in ("pass","fail","skip")}
 started={e["Test"] for e in events if "Test" in e and e["Action"]=="run"}
 assert test["actual_exit"]==0 and len(actions)==25 and started==set(actions) and all(v=="pass" for v in actions.values())
 for label,target in (("control-build","./apps/control"),("maintenance-root-build","./ops/supervisor/recovery_root"),("enrollment-build","./ops/supervisor/recovery_enrollment"),("backup-build","./ops/backup")):
  binary=scratch/"programs"/(label+".exe");success(label,[str(go),"build","-trimpath","-buildvcs=false","-o",str(binary),target],240);binaries[label]=pin(binary)
 binary=scratch/"programs/native-migration-harness.test.exe"
 success("tagged-test-binary-compile",[str(go),"test","-c","-tags=researchos_native_recovery_harness","-trimpath","-buildvcs=false","-o",str(binary),"./internal/domain"],240);binaries["tagged-test-harness"]=pin(binary)
 binary_guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=256*1024*1024);binary_guard.acquire(list(binaries.values()))
 closed("NATIVE43_EXACT_ERROR24_UNITS_PASSED_FOUR_PROGRAMS_AND_TAGGED_TEST_COMPILED_COMPONENT_ONLY")
except BaseException as e:
 if not (O/"validation.closed.json").exists():closed("FAILED_NATIVE43_COMPILE_OR_UNIT_NATIVE_CLOSED",repr(e))
 raise
finally:
 for g,n in ((binary_guard,"binary"),(compiled,"compiler"),(candidate,"candidate"),(guard,"input")):
  if g is not None:
   c=g.close();save(n+"-source-guard.cleanup.actual.json",c);assert c["closed"] and not c["errors"] and c["retained_handles_count"]==0
