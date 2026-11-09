import sys
sys.dont_write_bytecode=True
import hashlib,json,types
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
T=R/".local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409";A=B/"integration_codex/prepared-historical-regression-v3-root-0a452eccf5be423b"
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(ref):
 actual=pin(ref["path"]);assert actual["sha256"]==ref["sha256"] and actual["bytes"]==ref["bytes"];return actual
def save(n,v):
 p=O/n
 with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
def module(p,raw):
 m=types.ModuleType("root_full_domain_"+p.stem);m.__file__=str(p);exec(compile(raw,str(p),"exec"),m.__dict__);return m
assert pin(A/"validation.closed.json")["sha256"]=="36df9a817c132fa4a32920e478c5fbbd011d93282aedf4916ce71a2eb07ef3c3"
parent=json.loads((A/"validation.closed.json").read_bytes());assert parent["status"]=="PREPARED_AND_HISTORICAL_BACKUP_REGRESSION_PASSED_CURRENT_TESTS_COMPILED_COMPONENT_ONLY" and (parent["test_actions"]["pass_count"],parent["test_actions"]["fail_count"],parent["test_actions"]["skip_count"])==(199,0,0)
targets=json.loads((A/"formatted.source-members.json").read_bytes());assert len(targets)==38 and all(Path(r["path"]).is_relative_to(T) for r in targets)
frozen=[verify(ref) for ref in targets]+[pin(A/n) for n in ("validation.closed.json","formatted.source-members.json","source-overlay.json","original-tool-io.json","prepared-and-historical-backup-regression.invocation.json")]
canonical=[R/"execution/v2.4"/(n+".json") for n in ("checkpoint","path_ownership","step_state","commands")];before={p:p.read_bytes() for p in canonical};assert json.loads(before[canonical[0]])["revision"]==354
main_names=("go.mod","go.sum","apps/control/main.go","internal/domain/store.go","internal/domain/runtime_coordinator_windows.go","internal/domain/backup_migration.go","internal/domain/backup.go","internal/domain/backup_upgrade.go","internal/domain/backup_host_configuration.go","internal/domain/backup_configuration_upgrade_test.go","internal/domain/backup_upgrade_test.go");main_before={R/n:(R/n).read_bytes() for n in main_names}
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py";hp=B/"integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py";go=R/".local/tools/go1.27.1/go/bin/go.exe"
node=Path("C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node.exe");bundle=B/"sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d/actual-go-validation-v4-mu-cancel/mu-worker.frozen.mjs"
for p,sha in ((gp,"e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"),(hp,"6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad"),(go,"d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490"),(node,"5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6"),(bundle,"2a8e70132a914affc6122c1f1db29cfa315b655c93d4200145852ebbc853d441")):assert pin(p)["sha256"]==sha;frozen.append(pin(p))
env=dict(json.loads((A/"prepared-and-historical-backup-regression.invocation.json").read_bytes())["public_environment"])
for key in ("RESEARCHOS_CONFIGURATION_OLD_CONTROL","RESEARCHOS_CONFIGURATION_TARGET_PROGRAM","RESEARCHOS_HISTORICAL_SCHEMA14_CONTROL","RESEARCHOS_CONFIGURATION_SCHEMA22_HELPER"):frozen.append(pin(env[key]))
helper_namespace=B/"integration_codex/schema22-fixture-helper-build-root-8aa628d3038b4cd0";frozen+=[verify(ref) for ref in json.loads((helper_namespace/"formatted.source-members.json").read_bytes())]
old_manifest=B/"schema22_public_fixture_bridge_revision_codex/378a514e11f9417fab091937a9d2421c/MF.json";oldroot=Path(env["RESEARCHOS_CONFIGURATION_OLD_ROOT"]);frozen+=[verify(ref) for ref in json.loads(old_manifest.read_bytes())["base_refs"] if Path(ref["path"]).is_relative_to(oldroot)]
scratch=R/".local/full-domain-component-env-64b6627df5a847c7";scratch.mkdir(parents=True,exist_ok=False);(scratch/"profile").mkdir();(scratch/"temp").mkdir();(scratch/"programs").mkdir()
env.update(USERPROFILE=str(scratch/"profile"),LOCALAPPDATA=str(scratch/"profile"),APPDATA=str(scratch/"profile"),TEMP=str(scratch/"temp"),TMP=str(scratch/"temp"),RESEARCHOS_NODE=str(node),RESEARCHOS_MU_BUNDLE=str(bundle),PATH=str(node.parent)+";"+env["PATH"])
assert not any(env.get(k) for k in ("RESEARCHOS_RUNTIME_LIVE","RESEARCHOS_C01_MODEL","W16_CURRENT_NATIVE"))
frozen+=[pin(p) for p in main_before]+[pin(Path(__file__).resolve())];frozen=list({r["path"]:r for r in frozen}.values())
gm=module(gp,gp.read_bytes());guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024);guard.acquire(frozen);helper=module(hp,guard.get_buffer(str(hp)));compiled_guard=None;binary_guard=None
invocations=[];binaries={};inventory_ref=None;tests=None
def invoke(label,argv,wall):
 out=O/(label+".stdout.raw");err=O/(label+".stderr.raw");result=None;exception=None
 try:
  with out.open("xb") as stdout,err.open("xb") as stderr:result=helper.run_owned(argv,str(T),env,stdout,stderr,wall,creation_flags=0x08000000)
 except BaseException as e:exception=repr(e)
 finally:
  ref=save(label+".invocation.json",dict(argv=argv,cwd=str(T),public_environment=dict(env),result=result,exception=exception,actual_native_exit=result.get("actual_exit") if result else None,stdout_ref=pin(out),stderr_ref=pin(err),external_model_provider_requests=0,local_fixture_network_used=True,production_db_writes=0));invocations.append(ref)
 assert exception is None and result and not result["timed_out"] and result["error"] is None
 c=result["job_cleanup"];assert not c["errors"] and c["active_processes_last_observed"]==0 and all(c[k] for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"))
 print(json.dumps(dict(progress=label,actual_native_exit=result["actual_exit"],receipt_ref=ref)),flush=True)
 return result
def closed(status,failed=None):
 assert all(p.read_bytes()==raw for p,raw in before.items()) and all(p.read_bytes()==raw for p,raw in main_before.items()) and all(verify(r)==r for r in targets)
 ref=save("validation.closed.json",dict(status=status,failed_step=failed,invocation_refs=invocations,parent_targeted_ref=pin(A/"validation.closed.json"),compiled_input_inventory_ref=inventory_ref,binary_refs=binaries,test_actions=tests,current_source_root=str(T),source_count=38,Main_adopted=False,main_canonical_unchanged=True,all_owned_jobs_closed=True,native_authority_positive=False,external_model_provider_requests=0,local_fixture_network_used=True,production_db_writes=0,formal_acceptance=False))
 print(json.dumps(dict(closed_ref=ref,status=status,formal_acceptance=False)),flush=True)
try:
 listed=invoke("full-test-compiled-input-list",[str(go),"list","-test","-deps","-compiled","-json","./internal/domain","./internal/recoveryauthority","./apps/control","./ops/supervisor/recovery_root","./ops/supervisor/recovery_enrollment","./ops/backup"],240)
 if listed["actual_exit"]!=0:closed("FAILED_FULL_DOMAIN_COMPILER_LIST_NATIVE_CLOSED","full-test-compiled-input-list");raise AssertionError("current full test compiler input list failed")
 raw=(O/"full-test-compiled-input-list.stdout.raw").read_text(encoding="utf-8");decoder=json.JSONDecoder();pos=0;packages=[];inputs={};embeds=[]
 fields=("GoFiles","CgoFiles","CFiles","CXXFiles","MFiles","HFiles","FFiles","SFiles","SwigFiles","SwigCXXFiles","SysoFiles","CompiledGoFiles","EmbedFiles")
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
 for e in embeds:
  path=Path(e["ref"]["path"])
  if path.is_relative_to(T):assert str(path) in product
 inventory_ref=save("actual-full-test-compiler-input-inventory.json",dict(package_count=len(packages),packages=packages,build_input_count=len(inputs),build_inputs=list(inputs.values()),actual_embed_files=embeds,product_inventory_count=len(product),product_inventory=list(product.values()),GoRef=pin(go),selected_module_files_pinned=True,GOWORK="off",CGO_ENABLED="0",Main_adopted=False,formal_acceptance=False))
 compiled_refs=list({r["path"]:r for r in [*inputs.values(),*product.values(),inventory_ref]}.values());compiled_guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=768*1024*1024);compiled_guard.acquire(compiled_refs)
 for label,target in (("control-build","./apps/control"),("maintenance-root-build","./ops/supervisor/recovery_root"),("enrollment-build","./ops/supervisor/recovery_enrollment"),("backup-build","./ops/backup")):
  binary=scratch/"programs"/(label+".exe");result=invoke(label,[str(go),"build","-trimpath","-buildvcs=false","-o",str(binary),target],240)
  if result["actual_exit"]!=0:closed("FAILED_CURRENT_COMPOSITION_BUILD_NATIVE_CLOSED",label);raise AssertionError("current Source composition binary build failed")
  binaries[label]=pin(binary)
 binary_guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=256*1024*1024);binary_guard.acquire(list(binaries.values()))
 env["RUNTIME_CONTROL_BINARY"]=binaries["control-build"]["path"]
 tested=invoke("full-domain-and-native-authority-offline",[str(go),"test","-count=1","-json","-timeout=1185s","./internal/domain","./internal/recoveryauthority"],1200)
 events=[json.loads(l) for l in (O/"full-domain-and-native-authority-offline.stdout.raw").read_text(encoding="utf-8").splitlines() if l.startswith("{")];actions={(e["Package"],e["Test"]):e["Action"] for e in events if "Test" in e and e["Action"] in ("pass","fail","skip")};started={(e["Package"],e["Test"]) for e in events if "Test" in e and e["Action"]=="run"}
 tests=dict(actions=[dict(package=k[0],test=k[1],action=v) for k,v in actions.items()],pass_count=sum(v=="pass" for v in actions.values()),fail_count=sum(v=="fail" for v in actions.values()),skip_count=sum(v=="skip" for v in actions.values()),started_nodes=len(started),all_started_have_terminal=started==set(actions),skipped_tests=[dict(package=k[0],test=k[1]) for k,v in actions.items() if v=="skip"],external_live_model_enabled=False,formal_acceptance=False)
 if tested["actual_exit"]!=0 or not actions or tests["fail_count"] or started!=set(actions):closed("FAILED_CURRENT_COMPOSITION_FULL_DOMAIN_NATIVE_CLOSED","full-domain-and-native-authority-offline");raise AssertionError("full Domain/current native authority offline regression failed")
 closed("CURRENT_COMPOSITION_COMPILER_CLOSURE_FOUR_BUILDS_AND_FULL_OFFLINE_DOMAIN_PASSED_COMPONENT_ONLY")
finally:
 for name,g in (("binary",binary_guard),("compiled-input",compiled_guard),("input",guard)):
  if g is not None:
   c=g.close();save(name+"-source-guard.cleanup.actual.json",c);assert c["closed"] and not c["errors"] and c["retained_handles_count"]==0
