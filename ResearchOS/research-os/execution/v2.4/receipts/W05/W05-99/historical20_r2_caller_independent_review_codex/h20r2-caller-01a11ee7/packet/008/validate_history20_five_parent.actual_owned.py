import sys
sys.dont_write_bytecode=True
import hashlib,json,types,re
from pathlib import Path
R=Path(r"D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/history20-r2-five-parent-target-root-1791521480000')
T=Path(r"D:/作品集/ResearchOS/research-os/.local/worktrees/h20r2s-1791521480000")
P=R/".local/worktrees/codex-w0599-typed-q3-83b95f35e9bd4f81ad0c6682895a6ac1"
A=B/"integration_codex/typed-q3-epoch-targeted-root-0c4318e1c10443f2"
ISO=Path(r"D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/history20-r2-five-parent-isolation-root-1791521480000")
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes()
 return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(ref):
 expected={"path":ref["path"],"sha256":ref["sha256"].removeprefix("sha256:"),"bytes":ref["bytes"]}
 actual=pin(ref["path"]);expected["path"]=str(Path(expected["path"]).resolve())
 assert actual==expected,"exact Source reference mismatch"
 return actual
def save(name,value):
 with (O/name).open("xb") as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
 return pin(O/name)
def module(path,raw):
 path=Path(path).resolve();m=types.ModuleType("root_typed_"+path.stem);m.__file__=str(path);sys.modules[m.__name__]=m
 exec(compile(raw,str(path),"exec"),m.__dict__);return m
def members(ref):
 manifest=json.loads(Path(ref["path"]).read_bytes())
 values=manifest["members"];return list(values.values()) if isinstance(values,dict) else values
def unique(refs):
 result={}
 for ref in refs:
  ref=verify(ref);key=ref["path"].casefold()
  assert key not in result or result[key]==ref
  result[key]=ref
 return list(result.values())
assert len(sys.argv)==8, "usage: validate.py CHOICE_SHA256 CHOICE_BYTES CHECKPOINT_SHA256 CHECKPOINT_BYTES CHECKPOINT_REVISION ISOLATION_READY_SHA256 ISOLATION_READY_BYTES"
choice_path=Path(__file__).resolve().parent/"source.integration.choice.json"
choice_ref={"path":str(choice_path),"sha256":sys.argv[1],"bytes":int(sys.argv[2])}
verify(choice_ref);choice=json.loads(choice_path.read_bytes())
assert choice["schema"]=="researchos.root-history20-five-parent-integration-choice.v1" and choice["Root_source_adoption_only"] is True
isolation_ref=verify({"path":str(ISO/"isolation.ready.json"),"sha256":sys.argv[6],"bytes":int(sys.argv[7])})
isolation=json.loads(Path(isolation_ref["path"]).read_bytes())
assert isolation["status"]=="DETACHED_CANDIDATE_WORKTREE_READY_NO_SOURCE_OVERLAY"
assert Path(isolation["worktree_root"]).resolve()==T and Path(isolation["repository_root"]).resolve()==R
assert isolation["head"]=="adc460c2138528f163f7fdab5e8d81dde157b7fb" and isolation["all_owned_jobs_closed"] is True
assert isolation["source_overlay"] is False and isolation["main_canonical_unchanged"] is True
sources={};input_refs=[verify(choice_ref),pin(__file__),isolation_ref]+[verify(ref) for ref in choice["base_driver_refs"]]
assert pin(A/"validation.closed.json")["sha256"]=="d2fd6c15fcdb727fff91aa7bd3c53275230ebc42bd2017a544ff8f17becfb113"
old_actual=json.loads((A/"validation.closed.json").read_bytes());assert old_actual["source_count"]==49
assert old_actual["pass_count"]==61 and old_actual["fail_count"]==6 and old_actual["skip_count"]==0
parent_ref=verify(old_actual["formatted_source_ref"]);input_refs += [parent_ref,pin(A/"validation.closed.json")]
for ref in json.loads(Path(parent_ref["path"]).read_bytes()):
 path=Path(ref["path"]).resolve();assert path.is_relative_to(P);sources[path.relative_to(P).as_posix()]=verify(ref)
assert len(sources)==49
new_tests=set(old_actual["exact_25_parent_names"]);review_refs=[];changes={}
for item in choice["source_components"]:
 for ref in (item["source_handoff"],item["source_manifest"],item["independent_handoff"],item["independent_manifest"]):input_refs.append(verify(ref))
 input_refs.extend(verify(ref) for ref in members(item["source_manifest"]))
 input_refs.extend(verify(ref) for ref in members(item["independent_manifest"]))
 candidate=(B/item["candidate_namespace"]/"candidate-root").resolve()
 if item["component"]=="H20R2":
  actual_T11=json.loads(Path(choice["actual_T11_overlay_ref"]["path"]).read_bytes())
  assert sources=={key:verify(ref) for key,ref in actual_T11["sources"].items()} and len(sources)==58
  assert {Path(ref["path"]).resolve().relative_to(candidate).as_posix() for ref in members(item["source_manifest"]) if Path(ref["path"]).resolve().is_relative_to(candidate)}==set(choice["h20_candidate_paths"])
 for ref in members(item["source_manifest"]):
  path=Path(ref["path"]).resolve()
  if path.is_relative_to(candidate):
   relative=path.relative_to(candidate).as_posix();assert (relative.startswith("internal/domain/") and (relative.endswith(".go") or relative.startswith("internal/domain/testdata/"))) or (item["component"]=="H20R2" and relative=="ops/backup/main.go")
   changes[relative]={"component":item["component"],"previous_ref":sources.get(relative),"replacement_ref":verify(ref)}
   sources[relative]=verify(ref)
   if relative.endswith("_test.go"):new_tests.update(re.findall(r"^func (Test[A-Za-z0-9_]+)\(",path.read_text(encoding="utf-8"),re.MULTILINE))
 review_refs.append(item["independent_handoff"])
assert len(sources)==61 and choice["expected_source_count"]==61
assert new_tests and set(old_actual["exact_25_parent_names"]).issubset(new_tests)
preserved_parent_sources=set(new_tests)
assert preserved_parent_sources==set(choice["source_preserved_parent_names"])
new_tests=set(choice["exact_parent_names"])
assert new_tests=={'TestHistory20RejectsReleaseAndSourceDrift', 'TestHistory20RestoreFailureRetainsEncryptedBackupAndSource', 'TestHistory20PublicUpgradePreservesSourceAndRevokesRestoredCredentials', 'TestHistory20MigrationRollsBackDDLWhenLedgerInsertFails', 'TestHistory20ImplicitStartupStillRejectsPopulatedSource'}
assert new_tests.issubset(preserved_parent_sources)
canonical=[R/"execution/v2.4"/(n+".json") for n in ("checkpoint","path_ownership","step_state","commands")]
before={p:p.read_bytes() for p in canonical}
checkpoint_sha,checkpoint_bytes,checkpoint_revision=sys.argv[3],int(sys.argv[4]),int(sys.argv[5])
assert pin(canonical[0])["sha256"]==checkpoint_sha and pin(canonical[0])["bytes"]==checkpoint_bytes
assert json.loads(before[canonical[0]])["revision"]==checkpoint_revision
assert not O.exists();O.mkdir()
canonical_pre_run_ref=save("canonical.pre-run.exact.json",dict(refs=[pin(p) for p in canonical],revision=checkpoint_revision,formal_acceptance=False))
main_before={R/n:(R/n).read_bytes() for n in ("go.mod","go.sum","internal/domain/client_workspace_test.go","internal/domain/client_protocol_goal_test.go","internal/domain/runtime_permission_windows_test.go","internal/domain/runtime_tool_integration_windows_test.go","internal/domain/runtime_session_events_windows_test.go","internal/domain/store.go")}
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py";hp=B/"integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"
go=R/".local/tools/go1.27.1/go/bin/go.exe";fmt=go.with_name("gofmt.exe")
node=Path(r"C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node.exe")
mu=B/"sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d/actual-go-validation-v4-mu-cancel/mu-worker.frozen.mjs"
test2json=R/".local/official-test2json-resource-8a1fba36028c4c0b9ed30c0a7aca54cc/programs/test2json.exe"
for path,digest in ((Path(sys.executable),"cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b"),(gp,"e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"),(hp,"6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad"),(go,"d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490"),(node,"5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6"),(mu,"2a8e70132a914affc6122c1f1db29cfa315b655c93d4200145852ebbc853d441"),(test2json,"dead8050fd4e0e0471407380898fe9642b9107048e0ad119cb652821dfe58f7c")):
 assert pin(path)["sha256"]==digest
input_refs.extend(list(sources.values())+[pin(p) for p in main_before]+[pin(p) for p in (gp,hp,go,fmt,node,mu,test2json,Path(sys.executable),go.parent.parent/"VERSION",go.parent.parent/"src/go.mod")])
gm=module(gp,gp.read_bytes());helper=module(hp,hp.read_bytes())
input_refs += [pin(p) for p in canonical]+[pin(R/"execution/project_identity.json")]
for mod in list(sys.modules.values()):
 for field in ("__file__","__cached__"):
  path=getattr(mod,field,None)
  if path and Path(path).is_file():input_refs.append(pin(path))
guard_raw=gp.read_bytes();assert hashlib.sha256(guard_raw).hexdigest()=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
input_guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
input_refs=unique(input_refs);input_guard.acquire(input_refs)
helper=module(hp,input_guard.get_buffer(str(hp)))
runtime_guard=candidate_guard=compiler_guard=binary_guard=None
scratch=Path('D:/作品集/ResearchOS/research-os/.local/history20-r2-five-parent-env-1791521480000');scratch.mkdir()
for name in ("profile","temp","programs"):(scratch/name).mkdir()
evidence=scratch/"typed-child-evidence";assert not evidence.exists()
env={"SystemRoot":"C:/Windows","WINDIR":"C:/Windows","ComSpec":"C:/Windows/System32/cmd.exe","PATH":str(go.parent)+";C:/Windows/System32","PATHEXT":".COM;.EXE;.BAT;.CMD","USERPROFILE":str(scratch/"profile"),"LOCALAPPDATA":str(scratch/"profile"),"APPDATA":str(scratch/"profile"),"TEMP":str(scratch/"temp"),"TMP":str(scratch/"temp"),"GOROOT":str(go.parent.parent),"GOPATH":str(R/".local/gopath"),"GOCACHE":str(R/".local/gocache"),"GOENV":"off","GOTOOLCHAIN":"local","GOPROXY":"off","GOSUMDB":"off","GOWORK":"off","CGO_ENABLED":"0","GOFLAGS":"-mod=readonly -p=1","GOMAXPROCS":"2","RESEARCHOS_GO":str(go),"RESEARCHOS_NODE":str(node),"RESEARCHOS_MU_BUNDLE":str(mu),"RESEARCHOS_TEST2JSON":str(test2json),"RESEARCHOS_TEST2JSON_SHA256":pin(test2json)["sha256"],"RESEARCHOS_TYPED_RUNTIME_EVIDENCE_DIR":str(evidence)}
invocations=[];closed_jobs=[];actions={};starts=set();formatted_ref=inventory_ref=overlay_ref=None;binary=None
def invoke(label,argv,wall,cwd=None):
 cwd=str(cwd or T);out=O/(label+".stdout.raw");err=O/(label+".stderr.raw")
 with out.open("xb") as stdout,err.open("xb") as stderr:result=helper.run_owned(argv,cwd,env,stdout,stderr,wall,creation_flags=0x08000000)
 receipt=save(label+".invocation.json",dict(argv=argv,cwd=cwd,public_environment=env,result=result,actual_native_exit=result["actual_exit"],stdout_ref=pin(out),stderr_ref=pin(err),external_model_provider_requests=0,original_trial_provider_requests=None,production_DB_writes=0))
 invocations.append(receipt);cleanup=result["job_cleanup"]
 is_closed=not cleanup["errors"] and cleanup["active_processes_last_observed"]==0 and all(cleanup[key] for key in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"));closed_jobs.append(is_closed)
 print(json.dumps({"progress":label,"actual_native_exit":result["actual_exit"],"receipt_ref":receipt}),flush=True)
 assert is_closed and not result["timed_out"] and result["error"] is None
 return result
def success(label,argv,wall):
 result=invoke(label,argv,wall);assert result["actual_exit"]==0,label+" actual failed";return result
def closed(status,error=None):
 assert all(path.read_bytes()==raw for path,raw in before.items()) and all(path.read_bytes()==raw for path,raw in main_before.items())
 ref=save("validation.closed.json",dict(status=status,error=error,source_count=len(sources),source_overlay_ref=overlay_ref,formatted_source_ref=formatted_ref,compiler_inventory_ref=inventory_ref,compiled_test_ref=pin(binary) if binary and binary.is_file() else None,exact_parent_names=sorted(new_tests),base25_parent_sources_preserved_not_execution_claim=True,preserved_parent_source_names=sorted(preserved_parent_sources),nonselected_parent_sources=sorted(preserved_parent_sources-new_tests),nonselected_parents_executed_or_newly_accepted=False,ordinary_history20_full_release_program_rehearsal_authority="OPEN_NOT_EXECUTED",history20_scope="PUBLIC_FIXTURE_A20_TO_PLAIN21_ONLY",expected_terminal_names=choice["expected_terminal_names"],legacyB_release_program_ProductOwner_flow="OPEN_NOT_EXECUTED",canonical_pre_run_ref=canonical_pre_run_ref,source_delta=changes,actions=actions,started_names=sorted(starts),pass_count=sum(v=="pass" for v in actions.values()),fail_count=sum(v=="fail" for v in actions.values()),skip_count=sum(v=="skip" for v in actions.values()),invocation_refs=invocations,all_owned_jobs_closed=all(closed_jobs),independent_Source_review_refs=review_refs,Main_canonical_unchanged=True,Main_adopted=False,typed_native_evidence_directory=str(evidence),original_trial_DB_touched=False,external_model_provider_requests=0,original_trial_provider_requests=None,formal_acceptance=False))
 print(json.dumps({"closed_ref":ref,"status":status}),flush=True)
try:
 runtime_refs=unique([pin(p) for p in helper.runtime_resource_paths()])
 runtime_guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);runtime_guard.acquire(runtime_refs)
 for relative,ref in sources.items():
  path=T/relative
  if path.is_file():assert path.read_bytes()==(R/relative).read_bytes()
  path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(input_guard.get_buffer(ref["path"]))
 overlay_ref=save("source-overlay.json",{"sources":sources,"Source_count":len(sources),"independent_source_reviews":review_refs,"Main_adopted":False})
 success("format",[str(fmt),"-w",*[str(T/name) for name in sources if name.endswith(".go")]],45)
 formatted=[pin(T/name) for name in sources];formatted_ref=save("formatted.source-members.json",formatted)
 candidate_guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);candidate_guard.acquire(formatted+[formatted_ref])
 success("tagged-compiler-input-list",[str(go),"list","-test","-deps","-compiled","-tags=researchos_native_recovery_harness","-json","./internal/domain"],240)
 text=(O/"tagged-compiler-input-list.stdout.raw").read_text(encoding="utf-8")
 decoder=json.JSONDecoder();pos=0;packages=[];inputs={};embeds=[]
 fields=("GoFiles","CgoFiles","CFiles","CXXFiles","MFiles","HFiles","FFiles","SFiles","SwigFiles","SwigCXXFiles","SysoFiles","CompiledGoFiles","TestGoFiles","XTestGoFiles","EmbedFiles","TestEmbedFiles","XTestEmbedFiles")
 while pos<len(text):
  while pos<len(text) and text[pos].isspace():pos+=1
  if pos==len(text):break
  pkg,pos=decoder.raw_decode(text,pos);assert not pkg.get("Error") and not pkg.get("DepsErrors");packages.append(pkg.get("ImportPath"))
  if not pkg.get("Dir"):continue
  directory=Path(pkg["Dir"])
  for field in fields:
   for name in pkg.get(field,[]):
    path=Path(name);path=path if path.is_absolute() else directory/path;ref=pin(path);inputs[ref["path"]]=ref
    if field.endswith("EmbedFiles"):embeds.append({"package":pkg["ImportPath"],"field":field,"ref":ref})
 product={}
 for relative in ("apps/control","internal","adapters","evaluation","ops","migrations/sqlite","spec/v2.0/contracts"):
  directory=T/relative
  for path in directory.rglob("*"):
   assert not path.is_symlink()
   if path.is_file():ref=pin(path);product[ref["path"]]=ref
 for relative in ("go.mod","go.sum","execution/toolchains/locked.json"):ref=pin(T/relative);product[ref["path"]]=ref
 tools=[pin(p) for p in (go.parent.parent/"pkg/tool/windows_amd64").iterdir() if p.is_file()]
 inventory_ref=save("actual-tagged-compiler-input-inventory.json",{"package_count":len(packages),"packages":packages,"build_inputs":list(inputs.values()),"product_inventory":list(product.values()),"compiler_tool_refs":tools,"GoRef":pin(go),"actual_embed_files":embeds,"includes_actual_test_and_embed_inputs":True,"build_tag":"researchos_native_recovery_harness","test2json_executable_ref":pin(test2json),"Root_SOURCE_COMPONENT_only":True})
 compiler_refs=unique(list(inputs.values())+list(product.values())+tools+[pin(go),inventory_ref])
 compiler_guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);compiler_guard.acquire(compiler_refs)
 binary=scratch/"programs/history20-five-parent.test.exe"
 success("tagged-test-binary-compile",[str(go),"test","-c","-tags=researchos_native_recovery_harness","-trimpath","-buildvcs=false","-o",str(binary),"./internal/domain"],240)
 binary_guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);binary_guard.acquire([pin(binary),pin(test2json)])
 selector="^("+("|".join(sorted(new_tests)))+")$"
 result=invoke("history20-five-parent-jsonl",[str(test2json),"-p","researchos.local/research-os/internal/domain","-t",str(binary),"-test.v=test2json","-test.run="+selector,"-test.count=1","-test.timeout=14m"],900,T/"internal/domain")
 events=[json.loads(line) for line in (O/"history20-five-parent-jsonl.stdout.raw").read_text(encoding="utf-8").splitlines()]
 for event in events:
  assert event["Package"]=="researchos.local/research-os/internal/domain"
  name=event.get("Test")
  if not name:continue
  assert name.split("/",1)[0] in new_tests
  if event["Action"]=="run":assert name not in starts;starts.add(name)
  elif event["Action"] in ("pass","fail","skip"):assert name in starts and name not in actions;actions[name]=event["Action"]
 assert result["actual_exit"]==0 and starts==set(actions)==set(choice["expected_terminal_names"]) and new_tests.issubset(starts) and len(actions)==9 and all(action=="pass" for action in actions.values()) and events[-1]["Action"]=="pass" and "Test" not in events[-1]
 closed("HISTORY20_FIVE_PARENT_A20_TO21_SCOPE_PASSED_FULL20_TO24_OPEN")
except BaseException as error:
 if not (O/"validation.closed.json").exists():closed("FAILED_HISTORY20_FIVE_PARENT_COMPILE_OR_TARGET_EXECUTION_CLOSED",repr(error))
 raise
finally:
 for guard,name in ((binary_guard,"binary"),(compiler_guard,"compiler"),(candidate_guard,"candidate"),(runtime_guard,"runtime"),(input_guard,"input")):
  if guard is not None:
   cleanup=guard.close();save(name+"-source-guard.cleanup.actual.json",cleanup)
   assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0
