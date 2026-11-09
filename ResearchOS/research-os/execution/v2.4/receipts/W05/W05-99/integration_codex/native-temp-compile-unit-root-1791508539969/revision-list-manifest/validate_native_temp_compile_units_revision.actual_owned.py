import sys
sys.dont_write_bytecode=True
import hashlib,json,types
from pathlib import Path
R=Path(r"D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
T=R/".local/worktrees/codex-w0599-native-temp-1791506570123"
P=R/".local/worktrees/codex-w0599-native-ttl-c54ba9df088e45ea94adb56457af2979"
A=B/"integration_codex/native-ttl-compile-root-458f017f3c294bb6"
V=B/"native_migration_broker_temp_revision_codex/9beca53ced874c93a6101f451eb33491"
Z=B/"native_temp_independent_review_codex/20261009-01a11e22"
ISO=B/"integration_codex/native-temp-isolation-root-1791506570123"
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(ref):
 a=pin(ref["path"]);assert a["sha256"]==ref["sha256"].removeprefix("sha256:") and a["bytes"]==ref["bytes"];return a
def save(n,v):
 with (O/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
 return pin(O/n)
def module(p,raw):
 p=Path(p).resolve();m=types.ModuleType("root_native_ttl_"+p.stem);m.__file__=str(p);sys.modules[m.__name__]=m
 exec(compile(raw,str(p),"exec"),m.__dict__);return m
assert pin(V/"HDF.json")["sha256"]=="e9dab1b8ca436384733a256501aa21ca2a1b3429859a80368810cc65b741ed2b"
assert pin(V/"MF.json")["sha256"]=="c3f3e98bee9a3f2879b1cf07ca49927f9c894bed4534aaa38f2775d514bec301"
assert pin(Z/"HDF.json")["sha256"]=="7ed8bc9380c2ef4a7acbd74c402213a43b072be6d2e810fad1d03cf865be6c0f"
assert pin(Z/"MF.json")["sha256"]=="5cf3fa351a1ce624d22e85440ced5d3b319a44caf44ba91a734dac86cbd36c98"
assert json.loads((Z/"HDF.json").read_bytes())["decision"]=="SOURCE_ACCEPTED_WITH_ROOT_EXECUTION_PREREQUISITES"
assert pin(ISO/"isolation.ready.json")["sha256"]==sys.argv[1] and pin(ISO/"isolation.ready.json")["bytes"]==int(sys.argv[2])
assert pin(A/"formatted.source-members.json")["sha256"]=="37f8fce8fd17225d60147f4b753b2dc946252cc87762ad1141dd8d89bd156bcc"
parent=json.loads((A/"formatted.source-members.json").read_bytes());assert len(parent)==43
sources={}
for ref in parent:
 path=Path(ref["path"]).resolve();assert path.is_relative_to(P);sources[path.relative_to(P).as_posix()]=verify(ref)
mf=json.loads((V/"MF.json").read_bytes());manifest_members=mf["members"]
entries=list(manifest_members.items()) if isinstance(manifest_members,dict) else [(ref["relative_path"],ref) for ref in manifest_members]
refs=[verify(ref) for _,ref in entries]
changes={}
for n,ref in entries:
 if n.startswith("candidate-root/"):
  key=n.removeprefix("candidate-root/");assert key=="internal/domain/native_migration_authority_harness_windows_test.go" and key in sources
  changes[key]=dict(previous_ref=sources[key],replacement_ref=verify(ref))
  old_bytes=Path(sources[key]["path"]).read_bytes();new_bytes=Path(ref["path"]).read_bytes()
  assert hashlib.sha256(old_bytes).hexdigest()=="e696dccc00a24e1a0eb0872327e351a6b92ac14ab7bea8692780f9f70aa8ef4d" and len(old_bytes)==29516
  assert hashlib.sha256(new_bytes).hexdigest()=="eaa745bb2ea461a875bda13bef2495e7a8fb3375446a687e15108021b883ae90" and len(new_bytes)==35845
  sources[key]=verify(ref)
assert len(sources)==43 and len(changes)==1
for n in sources:
 path=T/n
 if path.exists():assert (R/n).exists() and path.read_bytes()==(R/n).read_bytes()
canonical=[R/"execution/v2.4"/(n+".json") for n in ("checkpoint","path_ownership","step_state","commands")]
before={p:p.read_bytes() for p in canonical};assert json.loads(before[canonical[0]])["revision"]==361
assert pin(canonical[0])["sha256"]=="27b6680899a8ba49b0f76fa6c7c917a80edecd0bcf68059de4dfc8da91088845"
pre_run_ref=save("canonical.pre-run.exact.json",dict(refs=[pin(p) for p in canonical],checkpoint_revision=361,formal_acceptance=False))
main_names=("go.mod","go.sum","apps/control/main.go","internal/domain/store.go","internal/domain/runtime_coordinator_windows.go","internal/domain/backup_migration.go","internal/domain/backup.go","internal/domain/backup_upgrade.go","internal/domain/backup_host_configuration.go","internal/domain/backup_configuration_upgrade_test.go","internal/domain/backup_upgrade_test.go","internal/domain/backup_command_queue_test.go","internal/domain/backup_host_configuration_test.go","internal/domain/client_configuration_test.go")
main_before={R/n:(R/n).read_bytes() for n in main_names}
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
hp=B/"integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"
go=R/".local/tools/go1.27.1/go/bin/go.exe";fmt=go.with_name("gofmt.exe");python=Path(sys.executable)
t2j=R/".local/official-test2json-resource-8a1fba36028c4c0b9ed30c0a7aca54cc/programs/test2json.exe"
assert pin(t2j)["sha256"]=="dead8050fd4e0e0471407380898fe9642b9107048e0ad119cb652821dfe58f7c" and pin(t2j)["bytes"]==4932608
assert pin(python)["sha256"]=="cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b"
assert pin(gp)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
assert pin(hp)["sha256"]=="6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad"
assert pin(go)["sha256"]=="d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490"
refs += list(sources.values())+[pin(p) for p in main_before]+[pin(gp),pin(hp),pin(go),pin(fmt),pin(python),pin(Path(__file__).resolve()),pin(T/"go.mod"),pin(T/"go.sum"),pin(ISO/"isolation.ready.json"),pin(A/"validation.closed.json"),pin(A/"formatted.source-members.json")]
for d,mname in ((Z,"MF.json"),(V,"MF.json")):
 refs += [pin(d/"HDF.json"),pin(d/mname)]
 members=json.loads((d/mname).read_bytes())["members"];members=members.values() if isinstance(members,dict) else members
 refs += [verify(ref) for ref in members]
refs += [pin(go.parent.parent/"VERSION"),pin(go.parent.parent/"src/go.mod"),pin(t2j)]
refs += [pin(p) for p in canonical]+[pin(R/"execution/project_identity.json")]
gm=module(gp,gp.read_bytes());helper=module(hp,hp.read_bytes())
for mod in list(sys.modules.values()):
 for field in ("__file__","__cached__"):
  path=getattr(mod,field,None)
  if path and Path(path).is_file():refs.append(pin(path))
refs=list({r["path"]:r for r in refs}.values())
guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=768*1024*1024);guard.acquire(refs)
helper=module(hp,guard.get_buffer(str(hp)));candidate=None;compiled=None;binary_guard=runtime_guard=None
scratch=R/".local/native-temp-compile-env-1791508539969-revision1";scratch.mkdir(parents=True,exist_ok=False)
for n in ("profile","temp","programs"):(scratch/n).mkdir()
env={"SystemRoot":"C:/Windows","WINDIR":"C:/Windows","ComSpec":"C:/Windows/System32/cmd.exe","PATH":str(go.parent)+";C:/Windows/System32;C:/Program Files/Git/cmd","PATHEXT":".COM;.EXE;.BAT;.CMD","USERPROFILE":str(scratch/"profile"),"LOCALAPPDATA":str(scratch/"profile"),"APPDATA":str(scratch/"profile"),"TEMP":str(scratch/"temp"),"TMP":str(scratch/"temp"),"GOROOT":str(go.parent.parent),"GOPATH":str(R/".local/gopath"),"GOCACHE":str(R/".local/gocache"),"GOENV":"off","GOTOOLCHAIN":"local","GOPROXY":"off","GOSUMDB":"off","GOWORK":"off","CGO_ENABLED":"0","GOFLAGS":"-mod=readonly -p=1","GOMAXPROCS":"2"}
invocations=[];binaries={};actions={};inventory_ref=None;formatted_ref=None;overlay_ref=None
unit_detail_ref=None
env["RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT"]=str((scratch/"temp").resolve())
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
 ref=save("validation.closed.json",dict(status=status,error=error,invocation_refs=invocations,current_source_root=str(T),source_count=43,source_overlay_ref=overlay_ref,formatted_source_ref=formatted_ref,compiler_input_inventory_ref=inventory_ref,binary_refs=binaries,unit_actions=actions,unit_detail_ref=unit_detail_ref,official_test2json_ref=pin(t2j),unit_pass_count=sum(v=="pass" for v in actions.values()),unit_fail_count=sum(v=="fail" for v in actions.values()),unit_skip_count=sum(v=="skip" for v in actions.values()),all_owned_jobs_closed=True,main_canonical_unchanged=True,source_delta_review_ref=pin(Z/"HDF.json"),base43_formatted_ref=pin(A/"formatted.source-members.json"),canonical_pre_run_ref=pre_run_ref,broker_temp_source_change=changes,unchanged_exact_error_units_not_rerun=True,native_migration_cases_executed=0,real_owner_private_input_used=False,issuer_signatures_created=0,production_db_writes=0,external_model_provider_requests=0,original_trial_provider_requests=None,Main_adopted=False,formal_acceptance=False))
 print(json.dumps(dict(closed_ref=ref,status=status)),flush=True)
try:
 runtime_refs=[pin(p) for p in helper.runtime_resource_paths()]
 runtime_guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);runtime_guard.acquire(runtime_refs)
 for n,ref in sources.items():
  target=T/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(guard.get_buffer(str(Path(ref["path"]))))
 overlay_ref=save("source-overlay.json",dict(sources=sources,source_count=43,parent43_formatted_ref=pin(A/"formatted.source-members.json"),native_revision_manifest_ref=pin(V/"MF.json"),Main_adopted=False))
 success("format",[str(fmt),"-w",*[str(T/n) for n in sources if n.endswith(".go")]],45)
 targets=[pin(T/n) for n in sources];formatted_ref=save("formatted.source-members.json",targets)
 for n,ref in sources.items():
  if n not in changes:assert pin(T/n)["sha256"]==ref["sha256"] and pin(T/n)["bytes"]==ref["bytes"]
 save("owned-gofmt-output-scope.json",dict(owned_format_invocation_ref=invocations[0],unmodified_42_byte_equal=True,changed_source_refs={n:{"reviewed_ref":sources[n],"formatted_ref":pin(T/n),"different_bytes":pin(T/n)["sha256"]!=sources[n]["sha256"]} for n in changes},transformation="OFFICIAL_OWNED_GOFMT_ONLY",authority="NONE",formal_acceptance=False))
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
 compiled_refs=list({r["path"]:r for r in [*inputs.values(),*product.values(),*tools,inventory_ref,pin(go),pin(go.parent.parent/"VERSION")]}.values())
 compiled=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=1024*1024*1024);compiled.acquire(compiled_refs)
 for label,target in (("control-build","./apps/control"),("maintenance-root-build","./ops/supervisor/recovery_root"),("enrollment-build","./ops/supervisor/recovery_enrollment"),("backup-build","./ops/backup")):
  binary=scratch/"programs"/(label+".exe");success(label,[str(go),"build","-trimpath","-buildvcs=false","-o",str(binary),target],240);binaries[label]=pin(binary)
 binary=scratch/"programs/native-migration-harness.test.exe"
 success("tagged-test-binary-compile",[str(go),"test","-c","-tags=researchos_native_recovery_harness","-trimpath","-buildvcs=false","-o",str(binary),"./internal/domain"],240);binaries["tagged-test-harness"]=pin(binary)
 binary_guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=256*1024*1024);binary_guard.acquire(list(binaries.values())+[pin(t2j)])
 unit_parents=("TestNativeHarnessBrokerIsolatedTempEnvironment","TestNativeHarnessBrokerTempBoundaryComparison")
 selector="^("+"|".join(unit_parents)+")$"
 success("broker-temp-units",[str(t2j),"-t","-p","researchos/internal/domain",str(binary),"-test.v=test2json","-test.count=1","-test.run="+selector],60)
 events=[json.loads(line) for line in (O/"broker-temp-units.stdout.raw").read_text(encoding="utf-8").splitlines() if line.strip()]
 for event in events:
  if event.get("Test") and event.get("Action") in ("pass","fail","skip"):
   name=event["Test"];assert name not in actions,"duplicate test terminal";actions[name]=event["Action"]
 assert set(n for n in actions if "/" not in n)==set(unit_parents)
 assert len(actions)==30 and sum("/" in n for n in actions)==28 and all(a=="pass" for a in actions.values())
 assert all(n.split("/",1)[0] in unit_parents for n in actions)
 unit_detail_ref=save("broker-temp-unit-results.json",dict(selector=selector,parents=unit_parents,parent_count=2,leaf_count=28,actions=actions,actual_exit=0,original_jsonl_ref=pin(O/"broker-temp-units.stdout.raw"),official_test2json_ref=pin(t2j),pure_resolved_alias_comparison_is_not_actual_junction_execution=True,native_migration_cases_executed=0,formal_acceptance=False))
 closed("NATIVE_TEMP43_FOUR_PROGRAMS_TAGGED_TEST_AND_28_TEMP_UNITS_PASS_COMPONENT_ONLY_NATIVE_ACTUAL_PENDING")
except BaseException as e:
 if not (O/"validation.closed.json").exists():closed("FAILED_NATIVE43_COMPILE_OR_UNIT_NATIVE_CLOSED",repr(e))
 raise
finally:
 for g,n in ((runtime_guard,"runtime"),(binary_guard,"binary"),(compiled,"compiler"),(candidate,"candidate"),(guard,"input")):
  if g is not None:
   c=g.close();save(n+"-source-guard.cleanup.actual.json",c);assert c["closed"] and not c["errors"] and c["retained_handles_count"]==0
